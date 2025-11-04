from utils import get_logger
from crawler.frontier import Frontier
from crawler.worker import Worker

import datetime
import threading

class SharedState:
    def __init__(self, frontier_factory):
        self.lock = threading.Lock()
        self.frontier = frontier_factory()

        self.cooldowns = {
            "ics.uci.edu": datetime.datetime.now(datetime.timezone.utc),
            "cs.uci.edu": datetime.datetime.now(datetime.timezone.utc),
            "informatics.uci.edu": datetime.datetime.now(datetime.timezone.utc),
            "stat.uci.edu": datetime.datetime.now(datetime.timezone.utc),
        }
        self.crawler_ended = False

class Crawler(object):
    def __init__(self, config, restart, frontier_factory=Frontier, worker_factory=Worker):
        self.config = config
        self.logger = get_logger("CRAWLER")
        self.shared_state = SharedState(lambda: frontier_factory(config, restart))
        self.workers = list()
        self.worker_factory = worker_factory

    def start_async(self):
        self.workers = [
            self.worker_factory(worker_id, self.config, self.shared_state)
            for worker_id in range(self.config.threads_count)]
        for worker in self.workers:
            worker.start()

    def start(self):
        self.start_async()
        self.join()

    def join(self):
        for worker in self.workers:
            worker.join()
