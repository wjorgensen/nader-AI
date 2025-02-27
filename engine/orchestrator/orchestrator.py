import asyncio
import schedule
import time
import os
import dotenv
import textwrap

dotenv.load_dotenv()

from engine.agent.index import AI
from engine.packages.log import Logger
from engine.packages.mongo import MDB
from engine.packages.red import Red
from engine.packages.worker import TWTW

prompts = {
    "seed": textwrap.dedent("""
        OVERVIEW:
        - You are introducing yourself to a new potential candidate for your network.
        - You currently only have their twitter/x username and would like to know more about them.
        - You want to start a conversation with them to learn more about their interests and background.
        - You want to eventually discern if they are a good fit for your network of great engineers, minds, creators, and innovators.
        - In the details section, there might be some insight and context about the potential candidate.
        - Start off by introducing yourself briefly, and asking them briefly a bit about themselves, using the context provided.
        
        MAKE SURE TO:
        - Briefly introduce yourself
        - Ask them a question about themselves
        
        ACTION INFO:
        - NO ACTIONS SHOULD BE GENERATED FOR THIS PROMPT
        """)
}

class Orchestrator:
    def __init__(self):
        self.logger = Logger("orchestrator", persist=True)
        self.mdb = MDB()
        self.mdb.connect()
        self.kv = Red()
        self.ai = AI()
        self.twtw = TWTW()
        
    async def prompt(self, key, details):
        base = prompts[key]
        return f"{base}\n{details}"

    async def seeds(self):
        self.logger.info("processing seeds")

        if not self.mdb.client: return

        people = self.mdb.client["network"]["people"]
        for person in people.find({"state": "seeded"}):
            self.logger.info(f"processing {person.get('x_username')}")
            
            extra = textwrap.dedent(f"""
                DETAILS ABOUT THE POTENTIAL CANDIDATE:
                - CANDIDATES Twitter / X Username: {person.get("x_username")}
                - CANDIDATES Twitter / X Name: {person.get("x_name")}
                - CANDIDATES Twitter / X Bio: {person.get("x_bio")}
                - CANDIDATES Last Couple Of Tweets List: {person.get("tweets")}
            """)
            
            full = await self.prompt("seed", extra)
            opener = await self.ai.act(full)
            msg = opener["response"]
            self.logger.info(f"opening message: {msg}")
            
            xusrid = str(await self.twtw.uid(person.get("x_username")))
            print(xusrid)
            await self.twtw.client.send_dm(user_id=xusrid, text=msg)
            self.logger.info(f"sent opening message to {person.get('x_username')}")
            
            people.update_one({"_id": person["_id"]}, {"$set": {"state": "opened"}})
            self.logger.info(f"updated state for {person.get('x_username')} to opened")
            
    async def start(self):
        self.logger.info("starting orchestrator")
        await self.twtw.login(
            username=os.getenv("TWITTER_USERNAME"),
            email=os.getenv("TWITTER_EMAIL"),
            password=os.getenv("TWITTER_PASSWORD"),
        )

        await self.seeds()

        schedule.every(5).minutes.do(self.seeds)

        while True:
            schedule.run_pending()
            time.sleep(10)


if __name__ == "__main__":
    orchestrator = Orchestrator()
    asyncio.run(orchestrator.start())
