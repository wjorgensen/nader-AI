import redis
import os
from dotenv import load_dotenv
from contextlib import contextmanager

load_dotenv()


class Red:
    def __init__(self, url: (str | None) = None):
        self.url = url or os.getenv("REDIS_URL") or "redis://localhost:6379"
        self.red = redis.Redis.from_url(self.url, decode_responses=True)

    def flushdb(self):
        return self.red.flushdb()

    def ping(self):
        return self.red.ping()

    def close(self):
        self.red.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


if __name__ == "__main__":
    with Red() as worker:
        if worker.ping():
            print("redis ok")
        else:
            print("redis failed")
