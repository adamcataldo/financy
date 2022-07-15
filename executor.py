from datetime import datetime
from datetime import timedelta
from queue import Queue
from time import sleep

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
        self.times_called.put(now)
        return query()