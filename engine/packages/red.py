import redis.asyncio as redis
import os
from dotenv import load_dotenv
from contextlib import contextmanager

load_dotenv()


class Red:
    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.red = redis.from_url(redis_url, decode_responses=True)

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
