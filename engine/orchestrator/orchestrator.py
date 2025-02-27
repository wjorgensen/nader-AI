import asyncio
import schedule
import time
import os
import dotenv

dotenv.load_dotenv()

from engine.agent.index import AI
from engine.packages.log import Logger
from engine.packages.mongo import MDB
from engine.packages.red import Red
from engine.packages.worker import TWTW

prompts = {
    "seed": """
        You are introducing yourself to a new potential candidate for your network.
        You currently only have their twitter/x username and would like to know more about them.
        You want to start a conversation with them to learn more about their interests and background.
        You want to eventually discern if they are a good fit for your network of great engineers, minds, creators, and innovators.
        Start off by introducing yourself briefly, and asking them a bit about themselves.
        """
}

class Orchestrator:
    def __init__(self):
        self.logger = Logger("orchestrator", persist=True)
        self.mdb = MDB()
        self.mdb.connect()
        self.kv = Red()
        self.ai = AI()
        self.twtw = TWTW()
        self.twtw.login(
            username=os.getenv("TWITTER_USERNAME"),
            email=os.getenv("TWITTER_EMAIL"),
            password=os.getenv("TWITTER_PASSWORD"),
        )

    async def seeds(self):
        self.logger.info("processing seeds")

        if not self.mdb.client: return

        people = self.mdb.client["network"]["people"]
        for person in people.find({"state": "seeded"}):
            x_username = person.get("x_username")
            self.logger.info(f"processing {x_username}")
            
            opener = await self.ai.act(prompts["seed"])
            msg = opener["response"]
            
            print(f"opening message: {msg}")
            # send the message to the person
            # after that update the state of this person

    async def start(self):
        self.logger.info("starting orchestrator")

        await self.seeds()

        schedule.every(5).minutes.do(self.seeds)

        while True:
            schedule.run_pending()
            time.sleep(10)


if __name__ == "__main__":
    orchestrator = Orchestrator()
    asyncio.run(orchestrator.start())
