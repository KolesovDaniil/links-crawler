from django.urls import reverse
from pytest import fixture

from crawler.utils import render_html_links_tree

LINKS_TREE = {
    "https://test.com/": {
        "https://test1.com/": {},
        "https://test2.com/": {"https://test3.com/": {}},
    }
}


@fixture
def mocked_crawler_class(mocker):
    return mocker.patch("crawler.views.LinksCrawler")


@fixture
def mocked_cached_miss(mocked_crawler_class):
    class FakeCrawler:
        def get_links(self):
            return False, None

    mocked_crawler_class.return_value = FakeCrawler()


@fixture
def mocked_cache_hit(mocked_crawler_class):
    class FakeCrawler:
        def get_links(self):
            return True, LINKS_TREE

    mocked_crawler_class.return_value = FakeCrawler()


class TestLinksOnPageView:
    @fixture(autouse=True)
    def setup(self):
        self.url = reverse("get_nested_links")

    def test_cache_does_not_exist(self, client, mocked_cached_miss):
        url_to_parse = "https://test.com/"
        data = {"url": url_to_parse}

        response = client.post(self.url, data=data, format="multipart")

        assert response.context["links_tree_exists"] is False
        assert response.context["links_tree"] is None

    def test_cache_exists(self, client, mocked_cache_hit):
        url_to_parse = "https://test.com/"
        data = {"url": url_to_parse}

        response = client.post(self.url, data=data, format="multipart")

        assert response.context["links_tree_exists"] is True
        assert response.context["links_tree"] == _get_html_links_tree()


class TestRenderHTMLLinksTree:
    def test_render_html_links_tree(self):
        html_links_tree = render_html_links_tree(LINKS_TREE)
        assert html_links_tree == _get_html_links_tree()


def _get_a_tag(url):
    return f'<a href="{url}">{url}</a>'


def _get_html_links_tree():
    return (
        f"<ul><li>{_get_a_tag('https://test.com/')}"
        f"<ul><li>{_get_a_tag('https://test1.com/')}</li>"
        f"<li>{_get_a_tag('https://test2.com/')}"
        f"<ul><li>{_get_a_tag('https://test3.com/')}</li></ul></li></ul>"
        f"</li></ul>"
    )
