import redis
import os
from dotenv import load_dotenv
from contextlib import contextmanager

load_dotenv()

class KV:
    def __init__(self, url: str = None):
        self.url = url or os.getenv("REDIS_URL")
        self.pool = redis.ConnectionPool.from_url(self.url)
        self.conn = redis.Redis(connection_pool=self.pool)

    def get(self, key: str):
        return self.conn.get(key)

    def set(self, key: str, value, ex: int = None):
        return self.conn.set(key, value, ex=ex)

    def delete(self, key: str):
        return self.conn.delete(key)

    def keys(self, pattern: str = "*"):
        return self.conn.keys(pattern)

    def flushdb(self):
        return self.conn.flushdb()
        
    def ping(self):
        return self.conn.ping()
        
    def close(self):
        self.pool.disconnect()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

if __name__ == "__main__":
    with KV() as worker:
        if worker.ping():
            print("redis ok")
        else:
            print("redis failed")
