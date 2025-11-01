from threading import Thread

from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import time
from urllib.parse import urlparse
import datetime


def base_for(url):
    for end in [
        "ics.uci.edu",
        "cs.uci.edu",
        "informatics.uci.edu",
        "stat.uci.edu",
    ]:
        if url.hostname is not None and url.hostname.lower().endswith(end):
            return end

    return ""

class Worker(Thread):
    def __init__(self, worker_id, config, shared_state):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.shared_state = shared_state
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)

    def run(self):
        while True:
            # pop is threadsafe
            tbd_url = self.shared_state.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                scraper.crawler_end()
                break

            parse = urlparse(tbd_url)
            base = base_for(parse)
            now = datetime.datetime.now(datetime.timezone.utc)

            how_long = None

            try:
                how_long = self.config.time_delay - (now - self.shared_state.cooldowns[base]).total_seconds()
            except KeyError:
                pass

            if how_long is not None and how_long > 0:
                time.sleep(how_long)

            self.shared_state.cooldowns[base] = datetime.datetime.now(datetime.timezone.utc) 

            resp = download(tbd_url, self.config, self.logger)
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                    f"using cache {self.config.cache_server}.")
            scraped_urls = scraper.scraper(tbd_url, resp)

            with self.shared_state.lock:
                self.shared_state.frontier.add_urls(scraped_urls)
                self.shared_state.frontier.mark_url_complete(tbd_url)

