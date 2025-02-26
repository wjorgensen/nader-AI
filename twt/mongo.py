
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os

load_dotenv()

uri = os.getenv('MDB_URI')
print(f"connecting to {uri}")

client = MongoClient(uri, server_api=ServerApi('1'))

try:
    client.admin.command('ping')
    print("-")
except Exception as e:
    print(e)