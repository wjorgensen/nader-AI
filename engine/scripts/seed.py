import asyncio
from engine.packages.mongo import MDB
from engine.packages.log import Logger
from engine.packages.worker import TWTW
from datetime import datetime
import json
import os
import dotenv

dotenv.load_dotenv()

async def seed_network():
    mdb = MDB()
    mdb.connect()
    logger = Logger("seed", persist=True)
    logger.info("seeding network")
    twtw = TWTW()
    await twtw.login(
            username=os.getenv("TWITTER_USERNAME"),
            email=os.getenv("TWITTER_EMAIL"),
            password=os.getenv("TWITTER_PASSWORD"),
        )
    print(twtw.ping())  
    if not mdb.client: return

    fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seed.json")

    f = open(fp, "r")
    seed = json.load(f)

    db = mdb.client["network"]
    people = db["people"]

    for usr in seed:
        if people.find_one({"x_username": usr.get("x_username")}):
            logger.info(f"user {usr.get('x_username')} already exists, skipping")
            continue
        
        logger.info(f"seeding {usr}")
        username = usr.get("x_username")
        xuid = str(await twtw.uid(username))
        userdump = await twtw.client.get_user_by_id(xuid)
        print(userdump)
        rawtweets = await twtw.client.get_user_tweets(user_id=xuid, tweet_type="Tweets")
        tweets = [tweet.full_text for tweet in rawtweets if not tweet.full_text.startswith("RT @")]
        people.insert_one(
            {
                "x_username": usr.get("x_username"),
                "x_name": userdump.name,
                "github_username": usr.get("github_username"),
                "tweets": tweets,
                "x_bio": userdump.description,
                "state": "seed",
                "created_at": datetime.now(),
                "refferal": False,
                "dm": [],
            }
        )
        logger.info(f"seeded {usr}")

    mdb.close()
    logger.info("done seeding network")


if __name__ == "__main__":
    asyncio.run(seed_network())
