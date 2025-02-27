from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os
from engine.packages.log import Logger
from typing import Optional

load_dotenv()


class MDB:
    def __init__(self, uri: Optional[str] = None) -> None:
        self.uri: str = uri or os.getenv("MDB_URI") or "mongodb://localhost:27017"
        self.client: Optional[MongoClient] = None
        self.logger = Logger("MDB", persist=True)

    def connect(self) -> None:
        """
        Establishes a connection to the MongoDB server.
        """
        if self.client is None:
            try:
                self.client = MongoClient(self.uri, server_api=ServerApi("1"))
                self.client.admin.command("ping")
                self.logger.info("successfully connected to MongoDB")
            except Exception as e:
                self.logger.error("error connecting to MongoDB")
                raise e

    def close(self) -> None:
        """
        Closes the MongoDB connection.
        """
        if self.client is not None:
            self.client.close()
            self.logger.info("closed connection to MongoDB")
            self.client = None
