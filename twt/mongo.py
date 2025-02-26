from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os

from twt.log import NaderLogger

class MW:
    def __init__(self, uri=None):
        load_dotenv()
        self.uri = uri or os.getenv('MDB_URI')
        self.client = None
        self.logger = NaderLogger()

    def connect(self):
        if self.client: return
        
        self.logger.info(f"connecting to {self.uri}")
        self.client = MongoClient(self.uri, server_api=ServerApi('1'))
        
        try:
            self.client.admin.command('ping')
            self.logger.info("connected to MongoDB")
        except Exception as e:
            self.logger.error(f"connection to MongoDB failed: {e}")
            raise

    def close(self):
        if self.client:
            self.client.close()
            self.client = None
            self.logger.info("closed connection to MongoDB")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()