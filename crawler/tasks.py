from links_crawler.celery import app


@app.task
def build_links_tree(page_url: str) -> None:
    from .utils import LinksCrawler

    crawler = LinksCrawler(page_url)
    crawler._warm_up_cache()
    links_tree = {
        page_url: crawler._get_links_tree(crawler.root_url, 1, [crawler.root_url])
    }
    crawler._save_links_tree_in_redis(links_tree)
