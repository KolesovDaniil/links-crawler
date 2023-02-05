import gc
import json
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from typing import Generator, Optional

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django_redis import get_redis_connection
from funcy import joining
from furl import furl
from redis import StrictRedis

from .tasks import build_links_tree

redis: StrictRedis = get_redis_connection()


class LinksCrawler:
    def __init__(
        self, page_url: str, nesting_level: Optional[int] = settings.NESTING_LEVEL
    ):
        self.nesting_level = nesting_level
        self.root_url = self._remove_query_params_and_anchors(page_url)
        self.pages_to_parse = deque()
        self.threads_pool = ThreadPoolExecutor(max_workers=8)

    def get_links(self) -> tuple[bool, Optional[dict]]:
        """Return all links on the page including nested ones"""
        links_tree = self._get_links_tree_from_redis()

        if links_tree:
            return True, links_tree

        build_links_tree.delay(self.root_url)

        return False, None

    def _warm_up_cache(self):
        future = self.threads_pool.submit(self._get_links_on_page, self.root_url)
        # We define the level of links that will be found
        self.pages_to_parse.append((future, 1, [self.root_url]))

        while self.pages_to_parse:
            future, link_level, parents = self.pages_to_parse.popleft()

            if not future.done():
                self.pages_to_parse.append((future, link_level, parents))
                continue

            if link_level > settings.NESTING_LEVEL:
                continue

            links_on_page = future.result()
            self._submit_tasks_to_pool(links_on_page, link_level + 1, parents)

    def _get_links_tree(self, page_url: str, link_level: int, parents: list) -> dict:
        redis_key = f"{settings.CACHED_LINKS_KEY_PREFIX}{page_url}"
        page_links = redis.smembers(redis_key)
        page_links = map(lambda l: l.decode("ascii"), page_links)
        last_level = link_level + 1 > settings.NESTING_LEVEL

        if last_level:
            node_factory = lambda _: {}
        else:
            node_factory = (
                lambda link: self._get_links_tree(
                    link, link_level + 1, [link, *parents]
                )
                if link not in parents
                else {}
            )

        return {link: node_factory(link) for link in page_links}

    def _submit_tasks_to_pool(
        self, links_on_page: list[str], link_level: int, parents: list
    ) -> None:
        for link in links_on_page:
            if link in [*parents, self.root_url]:
                continue

            future = self.threads_pool.submit(self._get_links_on_page, link)
            self.pages_to_parse.append((future, link_level + 1, [link, *parents]))

        gc.collect()

    def _get_links_on_page(self, page_url: str) -> list[str]:
        redis_key = f"{settings.CACHED_LINKS_KEY_PREFIX}{page_url}"
        cached_links = redis.smembers(redis_key)

        if cached_links:
            links_on_page = list(map(lambda l: l.decode("ascii"), cached_links))
        else:
            links_on_page = self._retrieve_links_from_page(page_url)

        if not links_on_page:
            return []

        redis.sadd(redis_key, *links_on_page)
        redis.expire(redis_key, settings.DAY * 7)

        return links_on_page

    def _retrieve_links_from_page(self, page_url: str) -> list[str]:
        html = self._get_page_html(page_url)

        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        link_tags_on_page = soup.find_all("a")
        links_on_page = []

        for link_tag in link_tags_on_page:
            link = link_tag.get("href")
            normalized_link = self._normalize_url_to_absolute_path(page_url, link)
            cleaned_link = self._remove_query_params_and_anchors(normalized_link)
            links_on_page.append(cleaned_link)

        unique_links = list(set(links_on_page))

        return unique_links

    @staticmethod
    def _normalize_url_to_absolute_path(page_url: str, url: str) -> str:
        return requests.compat.urljoin(page_url, url)

    @staticmethod
    def _remove_query_params_and_anchors(url: str) -> str:
        try:
            return furl(url).remove(args=True, fragment=True).url
        # We can get link from XML document which can contain forbidden characters
        except Exception:
            return ""

    @staticmethod
    def _get_page_html(page_url: str) -> Optional[str]:
        try:
            response = requests.get(page_url, verify=False, timeout=0.5)
            return response.text
        except requests.RequestException:
            return

    def _save_links_tree_in_redis(self, links_tree: dict) -> None:
        redis_key = f"{settings.CACHED_LINKS_TREE_KEY_PREFIX}{self.root_url}"
        redis.set(redis_key, json.dumps(links_tree))
        redis.expire(redis_key, settings.DAY * 7)

    def _get_links_tree_from_redis(self) -> Optional[dict]:
        redis_key = f"{settings.CACHED_LINKS_TREE_KEY_PREFIX}{self.root_url}"
        links_tree = redis.get(redis_key)

        return links_tree and json.loads(links_tree)


@joining("")
def render_html_links_tree(links_tree: dict) -> Generator:
    if not links_tree:
        return ""

    yield "<ul>"

    for url in links_tree.keys():
        a_tag = f'<a href="{url}">{url}</a>'
        yield f"<li>{a_tag}{render_html_links_tree(links_tree[url])}</li>"

    yield "</ul>"
