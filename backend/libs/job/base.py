import asyncio
import time
from venv import logger

from model.process import Process


class JobBase:
    def __init__(self):
        self.tag = None
        self.inverval = 30

    def get_data(self):
        raise NotImplementedError

    def process(self, data: list[Process]):
        raise NotImplementedError

    def run(self):
        while True:
            start_time = time.time()
            data = self.get_data()
            if data:
                asyncio.run(self.process(data))
            end_time = time.time()
            if end_time - start_time < self.inverval:
                logger.info(f"Delay {self.inverval - (end_time - start_time)} seconds")
                time.sleep(self.inverval - (end_time - start_time))
            else:
                time.sleep(1)
