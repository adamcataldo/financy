from datetime import datetime
from datetime import timedelta
from queue import Queue
from time import sleep
import logging

class Executor:
    def __init__(self, queries_per_minute):
        self.times_called = Queue(queries_per_minute)
        
    def execute(self, query):
        now = datetime.now()
        if self.times_called.full():
            first = self.times_called.get()
            while now - first <= timedelta(minutes=1):
                wait_delta = first + timedelta(seconds=1, minutes=1) - now
                sleep(wait_delta.total_seconds())
                now = datetime.now()
            logging.debug("Sleeping")
        self.times_called.put(now)
        return query()
    
class RetryingExecutor():
    def __init__(self, queries_per_minute, retries=3, retry_on=None):
        self.executor = Executor(queries_per_minute)
        self.retries = retries
        self.retry_on = None
    
    def execute(self, query):
        value = self.executor.execute(query)
        retries = 0
        while value == self.retry_on and retries < self.retries:
            logging.debug("Retrying")
            sleep(2**retries)
            value = self.executor.execute(query)
        return value