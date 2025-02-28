import asyncio
import schedule
import time
import os
import dotenv
import textwrap
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

dotenv.load_dotenv()

from engine.agent.index import AI
from engine.packages.log import Logger
from engine.packages.mongo import MDB
from engine.packages.red import Red
from engine.packages.worker import TWTW
from twikit.errors import Forbidden
from datetime import datetime
from engine.packages.referral import ReferralSystem

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
        - You are talking to someone who was referred to your network by {referrer}
        - Your goal is to naturally collect their GitHub username and email address
        - Be conversational, friendly, and genuine while gathering this information
        
        APPROACH:
        - First, ask about their background and what they're building
        - Ask about their GitHub to see their work
        - Later, get their email for network communications
        - Keep the tone conversational and authentic
        
        MAKE SURE TO:
        - Keep responses short and punchy
        - Don't act like an assistant
        - No fluff, no corporate speak
        - Be funny but technically sharp
        
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
    """)
}

# New welcome message
WELCOME_MESSAGE = textwrap.dedent("""
    Yo. I'm NaderAI, and I'm building a private network of the most cracked blockchain builders in the world.

    This isn't some VC-backed social club—it's an invite-only network of elite engineers, protocol devs, and builders who are actually shipping, not just posting takes.

    To get in, you need a referral from someone already in the network. Each verified builder gets three referral codes to share with other cracked devs they vouch for.

    If someone sent you here, drop their details:
    /refer @their_username their_code

    If you're good, welcome to the future. If not, there's always web2.
""")

class Orchestrator:
    def __init__(self):
        self.logger = Logger("orchestrator", persist=True)
        self.mdb = MDB()
        self.mdb.connect()
        self.kv = Red()
        self.ai = AI()
        self.bot = Application.builder().token(os.getenv("TELEGRAM_TOKEN") or "").build()
        self.referral_system = ReferralSystem()
        
    async def setup_handlers(self):
        """Setup Telegram command handlers"""
        self.bot.add_handler(CommandHandler("start", self.start_command))
        self.bot.add_handler(CommandHandler("refer", self.handle_referral))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send welcome message when /start command is issued"""
        if update.message: await update.message.reply_text(WELCOME_MESSAGE)
        
    async def handle_referral(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle referral code submission"""
        if not update.message:
            return
        if not context.args or len(context.args) != 2:
            await update.message.reply_text("Please use the format: /refer @username referral_code")
            return
            
        referrer_username = context.args[0]
        referral_code = context.args[1]
        
        # Verify referral using new system
        referrer = await self.referral_system.verify_referral(referrer_username, referral_code)
        
        if not referrer:
            await update.message.reply_text("Invalid referral code or username. Please check and try again.")
            return
            
        if not update.effective_user:
            await update.message.reply_text("Error: Unable to identify user. Please try again.")
            return
            
        if not self.mdb.client:
            return
        
        people = self.mdb.client["network"]["people"]
        
        # Check if user already exists
        existing_user = people.find_one({"telegram_id": update.effective_user.id})
        if existing_user:
            await update.message.reply_text("You're already in the verification process, anon.")
            return
            
        # Add new user to network (in gathering state)
        new_user = {
            "telegram_id": update.effective_user.id,
            "telegram_username": update.effective_user.username,
            "state": "gathering",
            "referrer": referrer_username,
            "joined_at": datetime.now()
        }
        
        # Insert new user
        people.insert_one(new_user)
        
        # Generate initial gathering message using AI
        gather_prompt = prompts["gather"].format(referrer=referrer_username)
        gather_response = await self.ai.act(gather_prompt)
        
        welcome_msg = textwrap.dedent(f"""
            Referral verified. Let's see if you're based enough for the network.
        """)
        
        await update.message.reply_text(welcome_msg)
        await update.message.reply_text(gather_response["response"])

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
    
            
    # async def gather_twitter(self):
    #     self.logger.info("gathering data")

    #     if not self.mdb.client: return

    #     people = self.mdb.client["network"]["people"]
        
    #     # Process people in "gathering" states
    #     for person in people.find({"state": {"$in": ["gathering"]}}):
    #         x_username = person.get("x_username")
    #         self.logger.info(f"gathering info for {x_username}")
            
    #         try:
    #             # Get user ID from username
    #             user_id = str(await self.twtw.uid(x_username))
                
    #             # Get previous messages from DM history
    #             message_history = await self.twtw.client.get_dm_history(user_id)
    #             previous_messages = []
                
    #             # Format previous messages for the prompt
    #             for message in message_history:
    #                 sender = "them" if message.sender_id == user_id else "you"
    #                 previous_messages.append(f"{sender}: {message.text}")
                
    #             # Join the messages with newlines
    #             formatted_messages = "\n".join(previous_messages)
                
    #             # Check if we already have GitHub and email - first from DB
    #             github_username = person.get("github_username")
    #             email = person.get("email")
                
    #             # If we don't have complete info, try to extract from previous messages
    #             if not (github_username and email) and previous_messages:
    #                 extract_prompt = prompts["extract_info"].format(
    #                     previous_messages=formatted_messages
    #                 )
                    
    #                 extraction_response = await self.ai.act(extract_prompt)
    #                 try:
    #                     extracted_info = json.loads(extraction_response["response"])
                        
    #                     # Update github_username if we found it
    #                     if not github_username and extracted_info.get("github_username"):
    #                         github_username = extracted_info["github_username"]
    #                         if github_username.lower() != "null":
    #                             people.update_one(
    #                                 {"_id": person["_id"]}, 
    #                                 {"$set": {"github_username": github_username}}
    #                             )
    #                             self.logger.info(f"Extracted GitHub for {x_username}: {github_username}")
                        
    #                     # Update email if we found it
    #                     if not email and extracted_info.get("email"):
    #                         email = extracted_info["email"]
    #                         if email.lower() != "null":
    #                             people.update_one(
    #                                 {"_id": person["_id"]}, 
    #                                 {"$set": {"email": email}}
    #                             )
    #                             self.logger.info(f"Extracted email for {x_username}: {email}")
    #                 except json.JSONDecodeError:
    #                     self.logger.error(f"Failed to parse extraction response: {extraction_response['response']}")
                
    #             # Check if we now have all the info we need
    #             if github_username and email:
    #                 people.update_one(
    #                     {"_id": person["_id"]}, 
    #                     {"$set": {"state": "testing"}}
    #                 )
    #                 self.logger.info(f"Updated state for {x_username} to completed - all info gathered")
    #                 continue  # Skip to next person
                
    #             # Get current gather attempt count
    #             gather_attempts = person.get("gather_attempts", 0)
                
    #             # If we've already tried 3 times, mark as stalled
    #             if gather_attempts >= 3:
    #                 people.update_one(
    #                     {"_id": person["_id"]}, 
    #                     {"$set": {"state": "stalled"}}
    #                 )
    #                 self.logger.info(f"Marked {x_username} as stalled after {gather_attempts} attempts")
    #                 continue  # Skip to next person
                
    #             # Determine what info we have and what we still need
    #             gathered_info = []
    #             needed_info = []
                
    #             if github_username:
    #                 gathered_info.append(f"GitHub username: {github_username}")
    #             else:
    #                 needed_info.append("GitHub username")
                
    #             if email:
    #                 gathered_info.append(f"email: {email}")
    #             else:
    #                 needed_info.append("email address")
                
    #             currently_gathered = "nothing yet" if not gathered_info else ", ".join(gathered_info)
    #             remaining_info = ", ".join(needed_info) if needed_info else "all required information"
                
    #             # Format the gather prompt with the variables
    #             base_prompt = prompts["gather"].format(
    #                 currently_gathered=currently_gathered,
    #                 remaining_info=remaining_info,
    #                 previous_messages=formatted_messages
    #             )
                
    #             gather_response = await self.ai.act(base_prompt)
    #             msg = gather_response["response"]
    #             self.logger.info(f"gathering message: {msg}")
                
    #             # Send the message
    #             await self.twtw.client.send_dm(user_id=user_id, text=msg)
    #             self.logger.info(f"sent gathering message to {x_username}")
                
    #             # Update gather attempts and state
    #             people.update_one(
    #                 {"_id": person["_id"]}, 
    #                 {
    #                     "$set": {"state": "gathering"},
    #                     "$inc": {"gather_attempts": 1}
    #                 }
    #             )
    #             self.logger.info(f"Updated gather attempts for {x_username} to {gather_attempts + 1}")
                
    #         except Exception as e:
    #             self.logger.error(f"Failed to process gathering for {x_username}: {str(e)}")
    
    async def gather(self):
        """Process users in gathering state to collect GitHub and email"""
        if not self.mdb.client:
            return

        people = self.mdb.client["network"]["people"]
        
        # Process people in "gathering" state
        for person in people.find({"state": "gathering"}):
            telegram_id = person.get("telegram_id")
            
            # Get message history for this user
            chat_history = await self.get_chat_history(telegram_id)
            if not chat_history:
                continue
                
            # Format messages for the extraction prompt
            formatted_messages = []
            for msg in chat_history:
                sender = "them" if msg["user"] != "naderai" else "you"
                formatted_messages.append(f"{sender}: {msg['text']}")
            
            messages_text = "\n".join(formatted_messages)
            
            # Check if we already have GitHub and email
            github_username = person.get("github_username")
            email = person.get("email")
            
            # If we don't have complete info, try to extract from messages
            if not (github_username and email) and formatted_messages:
                extract_prompt = prompts["extract_info"].format(
                    previous_messages=messages_text
                )
                
                extraction_response = await self.ai.act(extract_prompt)
                try:
                    extracted_info = json.loads(extraction_response["response"])
                    
                    # Update github_username if found
                    if not github_username and extracted_info.get("github_username"):
                        github_username = extracted_info["github_username"]
                        if github_username.lower() != "null":
                            people.update_one(
                                {"_id": person["_id"]}, 
                                {"$set": {"github_username": github_username}}
                            )
                    
                    # Update email if found
                    if not email and extracted_info.get("email"):
                        email = extracted_info["email"]
                        if email.lower() != "null":
                            people.update_one(
                                {"_id": person["_id"]}, 
                                {"$set": {"email": email}}
                            )
                except json.JSONDecodeError:
                    continue
            
            # If we have all info, move to testing state
            if github_username and email:
                people.update_one(
                    {"_id": person["_id"]}, 
                    {"$set": {"state": "testing"}}
                )
                
                # Generate success message using AI
                success_response = await self.ai.act(prompts["success_gather"])
                await self.bot.send_message(
                    chat_id=telegram_id,
                    text=success_response["response"]
                )
                continue
            
            # Get current gather attempt count
            gather_attempts = person.get("gather_attempts", 0)
            
            # If we've tried 3 times, mark as stalled
            if gather_attempts >= 3:
                people.update_one(
                    {"_id": person["_id"]}, 
                    {"$set": {"state": "stalled"}}
                )
                
                # Generate stalled message using AI
                stalled_response = await self.ai.act(prompts["stalled_gather"])
                await self.bot.send_message(
                    chat_id=telegram_id,
                    text=stalled_response["response"]
                )
                continue
            
            # Generate next gathering message
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
            
            gather_prompt = prompts["gather"].format(
                referrer=person.get("referrer", "someone"),
                gathered=", ".join(gathered_info) if gathered_info else "nothing yet",
                needed=", ".join(needed_info)
            )
            
            gather_response = await self.ai.act(gather_prompt)
            
            # Send the gathering message
            await self.bot.send_message(
                chat_id=telegram_id,
                text=gather_response["response"]
            )
            
            # Update gather attempts
            people.update_one(
                {"_id": person["_id"]}, 
                {
                    "$inc": {"gather_attempts": 1}
                }
            )

    async def get_chat_history(self, telegram_id: int) -> list:
        """Get chat history for a specific user from Redis"""
        key = f"telegram:chat:{telegram_id}:history"
        history = await self.kv.red.get(key)
        if history:
            return json.loads(history)
        return []

    async def start(self):
        self.logger.info("starting orchestrator")
        await self.setup_handlers()
        await self.bot.initialize()
        await self.bot.start()
        self.bot.run_polling()


if __name__ == "__main__":
    orchestrator = Orchestrator()
    asyncio.run(orchestrator.start())
