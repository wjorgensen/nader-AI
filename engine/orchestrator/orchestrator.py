import asyncio
import schedule
import time
import os
import dotenv
import textwrap
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from engine.packages.github import GithubWorker
from engine.packages.worker import TWTW

dotenv.load_dotenv()

from engine.agent.index import AI
from engine.packages.log import Logger
from engine.packages.mongo import MDB
from engine.packages.red import Red
from engine.packages.telegram import TEL
from twikit.errors import Forbidden
from datetime import datetime

states = ["seed", "gathering", "testing", "pre_referral"]

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
        - You are talking to someone who was referred by {referrer} to join a builder network
        - Your job is to gather their information while having a natural conversation
        - FIRST respond directly to what they just said in a conversational way
        - THEN ask them for any missing information you still need

        So far, you have gathered: {gathered}
        You still need to collect: {needed}

        IMPORTANT:
        1. First acknowledge and respond to the user's last message in a conversational way
        2. Then naturally ask for the missing information
        3. Be friendly and professional
        4. Do not mention that you're an AI
        5. Don't be robotic or overly formal
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
    """),
    "success_gather": textwrap.dedent("""
        OVERVIEW:
        - User has successfully provided their GitHub and email
        - You want to transition them to the testing phase
        - Keep your tone technically sharp and authentic
        
        MAKE SURE TO:
        - Acknowledge getting their info
        - Hint at the upcoming technical evaluation
        - Keep it short and punchy
        - No corporate speak or formality
        
        ACTION INFO:
        - NO ACTIONS SHOULD BE GENERATED FOR THIS PROMPT
    """),
    "stalled_gather": textwrap.dedent("""
        OVERVIEW:
        - After multiple attempts, user hasn't provided GitHub/email
        - You're putting their application on hold
        - Keep door open for when they're ready
        
        MAKE SURE TO:
        - Be direct but not dismissive
        - Imply they can continue when ready
        - Keep your edge and authenticity
        
        ACTION INFO:
        - NO ACTIONS SHOULD BE GENERATED FOR THIS PROMPT
    """),
    "testing": textwrap.dedent("""
        OVERVIEW:
        - User has provided GitHub and email
        - You want to perform technical evaluation
        
        YOU WILL BE PROVIDED WITH:
        - Their GitHub username
        - Their github repositories
        - How many stars each repository has
        - What the readme of each repository contains
        
        YOUR GOAL:
        - Evaluate their technical skills based on a wholistic approach
        - Determine if they are a good fit for the network
        
        KEEP IN MIND:
        - not all repos may contain readme files
        - some great repos can have low stars
        - take a wholistic approach
        - look at project complexity, project goals, how cool the projects are, if they are innovative
        
        PROVIDE A FIT SCORE FROM 1-100:
        - 1 being a poor fit
        - 100 being a perfect fit
        
        YOU MUST FORMAT your response as a JSON object with these fields:
        {
            "fit_score": "a number from 1-100",
            "comments": "any additional comments on the evaluation
        }
    """)
}

class Orchestrator:
    def __init__(self):
        self.logger = Logger("orchestrator", persist=True)
        self.mdb = MDB()
        self.mdb.connect()
        self.kv = Red()
        self.twtw = TWTW()
        self.ai = AI()
        self.tel = TEL()
        self.git = GithubWorker()

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
            
    async def xgather(self):
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
    
    async def gather(self):
        """Process users in gathering state to collect GitHub and email info"""
        self.logger.info("gathering data")
        
        if not self.mdb.client: return
        
        # Use the xgather method which is already implemented
        await self.xgather()
        
    async def testing(self):
        if not self.mdb.client:
            self.logger.error("MongoDB client not available")
            return

        people = self.mdb.client["network"]["people"]
        
        for person in people.find({"state": "testing"}):
            telegram_id = person.get("telegram_id")
            github_username = person.get("github_username")
            
            self.logger.info(f"processing testing for {github_username}")
            
            repos = self.git.get_user_repositories(github_username)
            
            extra = textwrap.dedent(f"""
                GITHUB DETAILS ABOUT THE POTENTIAL CANDIDATE:
                - CANDIDATES GitHub Username: {github_username}
                - CANDIDATES GitHub Repositories: {repos}
                - CANDIDATES GitHub Repositories Stars: {
                    [repo["stars"] for repo in repos or []]
                }
                - CANDIDATES GitHub Repositories Descriptions: {
                    [repo["description"] for repo in repos or []]
                }
                - CANDIDATES GitHub Repositories Readmes: {
                    [self.git.get_repo_readme(github_username, repo["name"]) for repo in repos or []]
                }
            """)

            prompt = await self.prompt("testing", extra)
            
            try:
                response = await self.ai.act(prompt)
                # The response is already a dict, not a string, so we need to access the 'response' field
                # and then parse that as JSON
                response_text = response["response"]
                
                # Check if response_text is already a dict or if it needs to be parsed
                if isinstance(response_text, str): parsed_response = json.loads(response_text)
                else: parsed_response = response_text
                    
                fit_score = int(parsed_response["fit_score"])
                
                if fit_score >= 65:
                    people.update_one(
                        {"_id": person["_id"]},
                        {"$set": {
                            "state": "accepted",
                            "fit_score": fit_score,
                            "evaluation_comments": parsed_response["comments"]
                        }}
                    )
                else:
                    people.update_one(
                        {"_id": person["_id"]},
                        {"$set": {
                            "state": "rejected", 
                            "fit_score": fit_score,
                            "evaluation_comments": parsed_response["comments"]
                        }}
                    )
                
            except Exception as e:
                self.logger.error(f"Failed to process testing for {github_username}: {str(e)}")

if __name__ == "__main__":
    orchestrator = Orchestrator()
    
    # start the scheduler
    schedule.every(15).minutes.do(orchestrator.seeds)
    schedule.every(15).minutes.do(orchestrator.gather)
    schedule.every(15).minutes.do(orchestrator.testing)
    