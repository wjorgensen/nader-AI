import asyncio
import schedule
import time
import os
import dotenv
import textwrap
import json

dotenv.load_dotenv()

from engine.agent.index import AI
from engine.packages.log import Logger
from engine.packages.mongo import MDB
from engine.packages.red import Red
from engine.packages.worker import TWTW
from twikit.errors import Forbidden
from datetime import datetime

states = ["seed", "gathering"]

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
        """),
    "gather": textwrap.dedent("""
        OVERVIEW:
        - You are continuing a conversation with a potential candidate for your network of engineers, innovators, and creators.
        - Your goal is to naturally collect their GitHub username and email address for future collaboration.
        - Be conversational, friendly, and genuine while gathering this information.
        - Respond to their messages in a way that shows you're listening and interested in their work.
        
        CURRENT STATUS:
        - Already gathered: {currently_gathered}
        - Still needed: {remaining_info}
        
        PREVIOUS CONVERSATION:
        {previous_messages}
        
        APPROACH:
        - If you still need their GitHub username: Ask about their projects, what they're working on, or if they have open-source work you could check out on GitHub.
        - If you still need their email: Mention collaboration opportunities, sharing resources, or keeping in touch as reasons for collecting their email.
        - If they seem hesitant: Respect their privacy and don't push too hard. Instead, explain why you're asking and how it will benefit them.
        - If you've collected all needed information: Thank them, express interest in their work, and let them know you'll be in touch.
        
        MAKE SURE TO:
        - Keep the tone conversational and authentic
        - Respond directly to what they've said in their messages
        - Ask for only ONE piece of missing information at a time
        - Don't rush or force the conversation
        
        ACTION INFO:
        - NO ACTIONS SHOULD BE GENERATED FOR THIS PROMPT
        """),
    "extract_info": textwrap.dedent("""
        TASK: Extract GitHub username and email from the conversation, if present.
        
        PREVIOUS CONVERSATION:
        {previous_messages}
        
        Based on the conversation above, extract the following information if available:
        1. GitHub username
        2. Email address
        
        YOU MUST FORMAT your response as a JSON object with these fields:
        {
            "github_username": "extracted username or null if not found",
            "email": "extracted email or null if not found",
            "confidence": "high/medium/low for each extraction"
        }
        
        Only extract information that is clearly provided by the user. Do not guess or assume information.
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
        for person in people.find({"state": "seed"}):
            self.logger.info(f"processing {person.get('x_username')}")
            
            extra = textwrap.dedent(f"""
                DETAILS ABOUT THE POTENTIAL CANDIDATE:
                - CANDIDATES Twitter / X Username: {person.get("x_username")}
                - CANDIDATES Twitter / X Name: {person.get("x_name")}
                - CANDIDATES Twitter / X Bio: {person.get("x_bio")}
                - CANDIDATES Last Couple Of Tweets List: {person.get("tweets")}
            """)
            
            try:
                full = await self.prompt("seed", extra)
                opener = await self.ai.act(full)
                msg = opener["response"]
                self.logger.info(f"opening message: {msg}")
                
                # xusrid = str(await self.twtw.uid(person.get("x_username")))
                # print(xusrid)
                # dm = await self.twtw.client.send_dm(user_id=xusrid, text=msg)
                # self.logger.info(f"sent opening message to {person.get('x_username')}")
                # people.update_one({"_id": person["_id"]}, {"$set": {"state": "gathering"}})
                # self.logger.info(f"updated state for {person.get('x_username')} to gathering")
                # people.update_one(
                #     {"_id": person["_id"]},
                #     {
                #         "$push": {
                #             "dm": {
                #                 "timestamp": datetime.now(),
                #                 "content": dm.text,
                #                 "id": dm.id,
                #                 "sender": "naderai",
                #             }
                #         }
                #     }
                # )
                # self.logger.info(f"updated dm [] for {person.get('x_username')}")
                
            except Forbidden as fe:
                self.logger.error(f"Twitter API Forbidden error: {fe}")
                people.update_one({"_id": person["_id"]}, {"$set": {"issue": "twitter_forbidden", "error": str(fe)}})
                self.logger.info(f"updated issue & error for {person.get('x_username')} to twitter_forbidden")
                
            except Exception as e:
                self.logger.error(f"error processing {person.get('x_username')}: {e}")
                people.update_one({"_id": person["_id"]}, {"$set": {"issue": "error", "error": str(e)}})
                self.logger.info(f"updated issue & error for {person.get('x_username')} to error")
            
    async def refferals(self):
        ...
    
            
    async def gather(self):
        self.logger.info("gathering data")

        if not self.mdb.client: return

        people = self.mdb.client["network"]["people"]
        
        # Process people in "gathering" states
        for person in people.find({"state": {"$in": ["gathering"]}}):
            x_username = person.get("x_username")
            self.logger.info(f"gathering info for {x_username}")
            
            try:
                # Get user ID from username
                user_id = str(await self.twtw.uid(x_username))
                
                # Get previous messages from DM history
                message_history = await self.twtw.client.get_dm_history(user_id)
                previous_messages = []
                
                # Format previous messages for the prompt
                for message in message_history:
                    sender = "them" if message.sender_id == user_id else "you"
                    previous_messages.append(f"{sender}: {message.text}")
                
                # Join the messages with newlines
                formatted_messages = "\n".join(previous_messages)
                
                # Check if we already have GitHub and email - first from DB
                github_username = person.get("github_username")
                email = person.get("email")
                
                # If we don't have complete info, try to extract from previous messages
                if not (github_username and email) and previous_messages:
                    extract_prompt = prompts["extract_info"].format(
                        previous_messages=formatted_messages
                    )
                    
                    extraction_response = await self.ai.act(extract_prompt)
                    try:
                        extracted_info = json.loads(extraction_response["response"])
                        
                        # Update github_username if we found it
                        if not github_username and extracted_info.get("github_username"):
                            github_username = extracted_info["github_username"]
                            if github_username.lower() != "null":
                                people.update_one(
                                    {"_id": person["_id"]}, 
                                    {"$set": {"github_username": github_username}}
                                )
                                self.logger.info(f"Extracted GitHub for {x_username}: {github_username}")
                        
                        # Update email if we found it
                        if not email and extracted_info.get("email"):
                            email = extracted_info["email"]
                            if email.lower() != "null":
                                people.update_one(
                                    {"_id": person["_id"]}, 
                                    {"$set": {"email": email}}
                                )
                                self.logger.info(f"Extracted email for {x_username}: {email}")
                    except json.JSONDecodeError:
                        self.logger.error(f"Failed to parse extraction response: {extraction_response['response']}")
                
                # Check if we now have all the info we need
                if github_username and email:
                    people.update_one(
                        {"_id": person["_id"]}, 
                        {"$set": {"state": "testing"}}
                    )
                    self.logger.info(f"Updated state for {x_username} to completed - all info gathered")
                    continue  # Skip to next person
                
                # Get current gather attempt count
                gather_attempts = person.get("gather_attempts", 0)
                
                # If we've already tried 3 times, mark as stalled
                if gather_attempts >= 3:
                    people.update_one(
                        {"_id": person["_id"]}, 
                        {"$set": {"state": "stalled"}}
                    )
                    self.logger.info(f"Marked {x_username} as stalled after {gather_attempts} attempts")
                    continue  # Skip to next person
                
                # Determine what info we have and what we still need
                gathered_info = []
                needed_info = []
                
                if github_username:
                    gathered_info.append(f"GitHub username: {github_username}")
                else:
                    needed_info.append("GitHub username")
                
                if email:
                    gathered_info.append(f"email: {email}")
                else:
                    needed_info.append("email address")
                
                currently_gathered = "nothing yet" if not gathered_info else ", ".join(gathered_info)
                remaining_info = ", ".join(needed_info) if needed_info else "all required information"
                
                # Format the gather prompt with the variables
                base_prompt = prompts["gather"].format(
                    currently_gathered=currently_gathered,
                    remaining_info=remaining_info,
                    previous_messages=formatted_messages
                )
                
                gather_response = await self.ai.act(base_prompt)
                msg = gather_response["response"]
                self.logger.info(f"gathering message: {msg}")
                
                # Send the message
                await self.twtw.client.send_dm(user_id=user_id, text=msg)
                self.logger.info(f"sent gathering message to {x_username}")
                
                # Update gather attempts and state
                people.update_one(
                    {"_id": person["_id"]}, 
                    {
                        "$set": {"state": "gathering"},
                        "$inc": {"gather_attempts": 1}
                    }
                )
                self.logger.info(f"Updated gather attempts for {x_username} to {gather_attempts + 1}")
                
            except Exception as e:
                self.logger.error(f"Failed to process gathering for {x_username}: {str(e)}")
    
    async def start(self):
        self.logger.info("starting orchestrator")
        await self.twtw.login(
            username=os.getenv("TWITTER_USERNAME"),
            email=os.getenv("TWITTER_EMAIL"),
            password=os.getenv("TWITTER_PASSWORD"),
        )

        await self.seeds()
        #await self.gather()

        schedule.every(15).minutes.do(self.seeds)
        schedule.every(15).minutes.do(self.gather)

        while True:
            schedule.run_pending()
            time.sleep(10)


if __name__ == "__main__":
    orchestrator = Orchestrator()
    asyncio.run(orchestrator.start())
