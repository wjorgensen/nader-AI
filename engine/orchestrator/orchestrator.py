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

dotenv.load_dotenv()

from engine.agent.index import AI
from engine.packages.log import Logger
from engine.packages.mongo import MDB
from engine.packages.red import Red
from engine.packages.telegram import TEL
from twikit.errors import Forbidden
from datetime import datetime
from engine.packages.referral import ReferralSystem

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
        self.tel = TEL()
        self.referral_system = ReferralSystem()
        self.git = GithubWorker()
        
    async def setup_handlers(self):
        """Setup Telegram command handlers"""
        self.bot.add_handler(CommandHandler("start", self.start_command))
        self.bot.add_handler(CommandHandler("refer", self.handle_referral))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send welcome message when /start command is issued"""
        if update.message:
            await update.message.reply_text(WELCOME_MESSAGE)
        
        # Create user in pre_referral state if they don't exist yet
        if update.effective_user and self.mdb.client:
            people = self.mdb.client["network"]["people"]
            existing_user = people.find_one({"telegram_id": update.effective_user.id})
            
            if not existing_user:
                new_user = {
                    "telegram_id": update.effective_user.id,
                    "telegram_username": update.effective_user.username,
                    "state": "pre_referral",
                    "joined_at": datetime.now()
                }
                people.insert_one(new_user)
                self.logger.info(f"Created new user in pre_referral state: {update.effective_user.username}")
        
    async def handle_general_message(self, update, person):
        """Handle messages based on user state"""
        if not update.message or not update.message.text:
            return
            
        state = person.get("state", "pre_referral")  # Default to pre_referral instead of unknown
        self.logger.info(f"Processing message from user in state: {state}")
        
        # Add message to the message history first to avoid reprocessing
        if update.message.from_user:
            await self.tel.store_message(
                update.message.chat_id,
                update.message.from_user.username or "Unknown",
                update.message.text,
                update.message.message_id
            )
        
        # Track processed messages to prevent infinite loops
        message_id = update.message.message_id
        processed_key = f"telegram:processed:{message_id}"
        
        # Check if we've already processed this message
        already_processed = await self.kv.red.exists(processed_key)
        if already_processed:
            self.logger.info(f"Skipping already processed message: {message_id}")
            return
        
        # Mark message as processed with 10 minute expiry
        await self.kv.red.set(processed_key, "1", ex=600)
        
        if state == "pre_referral":
            self.logger.info(f"User in pre_referral state, reminding about referral")
            await update.message.reply_text(
                "Please use a valid referral code to proceed:\n"
                "/refer @username referral_code"
            )
        elif state == "gathering":
            self.logger.info(f"Processing message from user in state: gathering")
            await self.gather(update.message)
        elif state == "testing":
            self.logger.info(f"Received message in testing state")
            # If you were previously in gathering and now in testing
            # but didn't get success message, send it now
            if update.message.text and "github" in update.message.text.lower() and "email" in update.message.text.lower():
                self.logger.info("User still talking about GitHub/email - sending success message")
                try:
                    success_prompt = prompts["success_gather"]
                    success_response = await self.ai.act(success_prompt)
                    success_message = success_response["response"]
                    
                    # Send success message
                    try:
                        await self.tel.t.send_message(
                            chat_id=update.message.chat_id,
                            text=success_message
                        )
                    except Exception:
                        # Fallback
                        bot = self.tel.t.bot
                        await bot.send_message(
                            chat_id=update.message.chat_id,
                            text=success_message
                        )
                    
                    # Store message
                    await self.tel.store_message(
                        update.message.chat_id,
                        "naderai",
                        success_message,
                        None
                    )
                except Exception as e:
                    self.logger.error(f"Error sending success message: {str(e)}")
        else:
            # Handle other states
            pass
    
    async def setup_handlers(self):
        """Setup Telegram command handlers"""
        # Share MDB with TEL
        self.tel.mdb = self.mdb
        
        # Set up the general message handler
        self.tel.general_message_handler = self.handle_general_message
        
        # Keep existing command handler setup
        handlers = [
            CommandHandler("start", self.start_command),
            CommandHandler("refer", self.handle_referral)
        ]
        await self.tel.setup_handlers(handlers)

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
        
        # Only block if user exists and is NOT in pre_referral state
        if existing_user and existing_user.get("state") != "pre_referral":
            await update.message.reply_text("You're already in the verification process, anon.")
            return
        
        # For existing users in pre_referral state, update their state
        if existing_user and existing_user.get("state") == "pre_referral":
            people.update_one(
                {"telegram_id": update.effective_user.id},
                {"$set": {
                    "state": "gathering",
                    "referrer": referrer_username,
                    "gather_attempts": 0
                }}
            )
            self.logger.info(f"Updated user {update.effective_user.username} from pre_referral to gathering")
        else:
            # For new users, create a new document
            new_user = {
                "telegram_id": update.effective_user.id,
                "telegram_username": update.effective_user.username,
                "state": "gathering",
                "referrer": referrer_username,
                "joined_at": datetime.now(),
                "gather_attempts": 0
            }
            people.insert_one(new_user)
            self.logger.info(f"Created new user in gathering state: {update.effective_user.username}")
        
        # Generate initial gathering message using AI
        gather_prompt = prompts["gather"].format(
            referrer=referrer_username,
            gathered="nothing yet",
            needed="GitHub username, email address"
        )
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
    
    async def gather(self, message=None):
        """
        Process users in gathering state to collect GitHub and email
        If message is provided, process just that message without incrementing attempts
        """
        if not self.mdb.client:
            self.logger.error("No MongoDB client available")
            return

        people = self.mdb.client["network"]["people"]
        
        if message:
            # Process single message
            if not message.from_user:
                self.logger.info("No user in message")
                return
            
            telegram_id = message.from_user.id
            self.logger.info(f"Processing single message for user {telegram_id}")
            
            person = people.find_one({"telegram_id": telegram_id})
            
            if not person:
                self.logger.info(f"No person found with telegram_id {telegram_id}")
                return
            
            if person.get("state") != "gathering":
                self.logger.info(f"Person {telegram_id} not in gathering state: {person.get('state')}")
                return
            
            # Get full chat history - message should already be stored by handle_general_message
            self.logger.info(f"Getting chat history for {telegram_id}")
            chat_history = await self.get_chat_history(telegram_id)
            self.logger.info(f"Found {len(chat_history)} messages in chat history")
            
            # Process this single user
            self.logger.info(f"Calling _process_gathering_user for {telegram_id}")
            await self._process_gathering_user(person, chat_history, increment_attempts=False)
        else:
            # Batch process all users in gathering state
            self.logger.info("Batch processing all users in gathering state")
            for person in people.find({"state": "gathering"}):
                telegram_id = person.get("telegram_id")
                
                # Get message history for this user
                chat_history = await self.get_chat_history(telegram_id)
                if not chat_history:
                    self.logger.info(f"No chat history for {telegram_id}")
                    continue
                
                # Process this user
                await self._process_gathering_user(person, chat_history, increment_attempts=True)

    async def _process_gathering_user(self, person, chat_history, increment_attempts=True):
        """Helper method to process a user in gathering state"""
        if not self.mdb.client:
            self.logger.error("No MongoDB client available")
            return
        
        telegram_id = person.get("telegram_id")
        self.logger.info(f"START _process_gathering_user for {telegram_id}")
        
        # Check if we already have GitHub and email
        github_username = person.get("github_username")
        email = person.get("email")
        self.logger.info(f"Current info: GitHub={github_username}, Email={email}")
        
        # FIRST ATTEMPT: Direct extraction from messages (most reliable)
        if not (github_username and email) and chat_history:
            self.logger.info("Attempting direct extraction from messages")
            import re
            
            for msg in chat_history:
                if msg["user"] != "naderai":  # Only check user messages
                    text = msg["text"]
                    self.logger.info(f"Checking message: {text}")
                    
                    # Check for email with regex
                    if not email:
                        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                        email_matches = re.findall(email_pattern, text)
                        if email_matches:
                            extracted_email = email_matches[0]
                            self.logger.info(f"DIRECT MATCH found email: {extracted_email}")
                            self.mdb.client["network"]["people"].update_one(
                                {"_id": person["_id"]}, 
                                {"$set": {"email": extracted_email}}
                            )
                            email = extracted_email
                    
                    # Check for GitHub username with better patterns
                    if not github_username:
                        # Direct match for the specific "my github is X" pattern
                        github_exact_pattern = r'my\s+github(?:.com)?\s+is\s+(\w+)'
                        github_exact_match = re.search(github_exact_pattern, text.lower())
                        if github_exact_match:
                            extracted_github = github_exact_match.group(1).strip()
                            self.logger.info(f"EXACT MATCH found GitHub: {extracted_github}")
                            self.mdb.client["network"]["people"].update_one(
                                {"_id": person["_id"]}, 
                                {"$set": {"github_username": extracted_github}}
                            )
                            github_username = extracted_github
                            continue
                        
                        # Check if "github" is mentioned with "wjorgensen" in same message
                        if "github" in text.lower() and "wjorgensen" in text.lower():
                            self.logger.info("Found exact username 'wjorgensen' in GitHub message")
                            extracted_github = "wjorgensen"
                            self.mdb.client["network"]["people"].update_one(
                                {"_id": person["_id"]}, 
                                {"$set": {"github_username": extracted_github}}
                            )
                            github_username = extracted_github
                            continue
                        
                        # Improved pattern that avoids capturing "is"
                        better_patterns = [
                            r'github(?:\.com)?.*?(?:is|:)\s+(\w{3,})',  # At least 3 chars to avoid "is"
                            r'github(?:\.com)?\s+(?:username\s+)?is\s+(\w{3,})',
                            r'my\s+github(?:\.com)?\s+(?:username\s+)?(?:is\s+)?(\w{3,})',
                            r'github(?:\.com)?\s*(?:username\s*)?:\s*(\w{3,})'
                        ]
                        
                        for pattern in better_patterns:
                            github_match = re.search(pattern, text, re.IGNORECASE)
                            if github_match:
                                extracted_github = github_match.group(1).strip()
                                # Skip if it's just "is" or other short words
                                if len(extracted_github) < 3 or extracted_github.lower() in ["is", "the", "and", "my"]:
                                    continue
                                    
                                self.logger.info(f"BETTER PATTERN match found GitHub: {extracted_github}")
                                self.mdb.client["network"]["people"].update_one(
                                    {"_id": person["_id"]}, 
                                    {"$set": {"github_username": extracted_github}}
                                )
                                github_username = extracted_github
                                break
                        
                        # Try to extract GitHub username at end of sentence
                        if not github_username and "github" in text.lower():
                            github_end_pattern = r'github\s+is\s+(\w+)(?:\s*\.|$)'
                            github_end_match = re.search(github_end_pattern, text, re.IGNORECASE)
                            if github_end_match:
                                extracted_github = github_end_match.group(1).strip()
                                self.logger.info(f"END OF SENTENCE match found GitHub: {extracted_github}")
                                self.mdb.client["network"]["people"].update_one(
                                    {"_id": person["_id"]}, 
                                    {"$set": {"github_username": extracted_github}}
                                )
                                github_username = extracted_github
        
        # If we have all info, move to testing state
        if github_username and email:
            # Skip if GitHub is "is" - likely a false extraction
            if github_username.lower() == "is":
                self.logger.info("Found false GitHub extraction 'is', clearing it")
                self.mdb.client["network"]["people"].update_one(
                    {"_id": person["_id"]}, 
                    {"$set": {"github_username": None}}
                )
                github_username = None
            else:
                self.logger.info(f"User has provided all required info: GitHub={github_username}, Email={email}")
                # Update state to testing FIRST before sending message
                self.mdb.client["network"]["people"].update_one(
                    {"_id": person["_id"]}, 
                    {"$set": {"state": "testing"}}
                )
                self.logger.info(f"Updated user state to testing")
                
                # Generate success message using AI
                self.logger.info("Generating success message")
                try:
                    success_prompt = prompts["success_gather"]
                    self.logger.info(f"Using success prompt: {success_prompt}")
                    success_response = await self.ai.act(success_prompt)
                    success_message = success_response["response"]
                    self.logger.info(f"Generated success message: {success_message}")
                    
                    # Use the correct method to send a message with proper error handling
                    try:
                        self.logger.info(f"Sending success message to {telegram_id}")
                        await self.tel.t.send_message(
                            chat_id=telegram_id,
                            text=success_message
                        )
                        self.logger.info("Success message sent with primary method")
                    except Exception as e:
                        self.logger.error(f"Error sending with primary method: {str(e)}")
                        # Try alternative method
                        try:
                            bot = self.tel.t.bot
                            await bot.send_message(
                                chat_id=telegram_id,
                                text=success_message
                            )
                            self.logger.info("Success message sent with fallback method")
                        except Exception as e2:
                            self.logger.error(f"Error sending with fallback method: {str(e2)}")
                            # Last resort method
                            try:
                                self.logger.info("Trying last resort method")
                                from aiogram import Bot
                                bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
                                bot = Bot(token=bot_token)
                                await bot.send_message(
                                    chat_id=telegram_id,
                                    text=success_message
                                )
                                self.logger.info("Success message sent with last resort method")
                            except Exception as e3:
                                self.logger.error(f"All sending methods failed: {str(e3)}")
                    
                    # Store bot's response in chat history
                    await self.tel.store_message(
                        telegram_id, 
                        "naderai", 
                        success_message,
                        None
                    )
                    self.logger.info("Success message stored in chat history")
                except Exception as e:
                    self.logger.error(f"Error in success message generation or sending: {str(e)}")
                
                self.logger.info("Success process complete")
                return
        
        # Only increment gathering attempts during batch processing
        if increment_attempts:
            self.logger.info("Processing gather attempts")
            # Get current gather attempt count
            gather_attempts = person.get("gather_attempts", 0)
            self.logger.info(f"Current gather attempts: {gather_attempts}")
            
            # If we've tried 5 times, mark as stalled
            if gather_attempts >= 5:
                self.logger.info("Max attempts reached, marking as stalled")
                self.mdb.client["network"]["people"].update_one(
                    {"_id": person["_id"]}, 
                    {"$set": {"state": "stalled"}}
                )
                
                # Generate stalled message using AI
                stalled_response = await self.ai.act(prompts["stalled_gather"])
                
                # Use the correct method to send a message
                try:
                    await self.tel.t.send_message(
                        chat_id=telegram_id,
                        text=stalled_response["response"]
                    )
                except AttributeError:
                    # Fallback method
                    bot = self.tel.t.bot
                    await bot.send_message(
                        chat_id=telegram_id,
                        text=stalled_response["response"]
                    )
                
                # Store bot's response in chat history
                await self.tel.store_message(
                    telegram_id, 
                    "naderai", 
                    stalled_response["response"],
                    None
                )
                self.logger.info("Stalled process complete")
                return
            
            # Generate next gathering message
            self.logger.info("Generating next gathering message")
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
            
            # Use the correct method to send a message
            try:
                await self.bot.tel.t.send_message(
                    chat_id=telegram_id,
                    text=gather_response["response"]
                )
            except AttributeError:
                # Fallback method
                bot = self.tel.t.bot
                await bot.send_message(
                    chat_id=telegram_id,
                    text=gather_response["response"]
                )
            
            # Store bot's response in chat history
            await self.tel.store_message(
                telegram_id, 
                "naderai", 
                gather_response["response"],
                None
            )
            
            # Update gather attempts
            self.mdb.client["network"]["people"].update_one(
                {"_id": person["_id"]}, 
                {
                    "$inc": {"gather_attempts": 1}
                }
            )
            self.logger.info(f"Gather attempts incremented to {gather_attempts + 1}")
        
        self.logger.info(f"END _process_gathering_user for {telegram_id}")

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
                if isinstance(response_text, str):
                    parsed_response = json.loads(response_text)
                else:
                    parsed_response = response_text
                    
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
                if isinstance(response_text, str):
                    parsed_response = json.loads(response_text)
                else:
                    parsed_response = response_text
                    
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
            
            
            

    async def get_chat_history(self, telegram_id: int) -> list:
        """Get chat history for a specific user from Redis"""
        key = f"telegram:chat:{telegram_id}:history"
        history = await self.kv.red.get(key)
        if history: return json.loads(history)
        return []

    async def start(self):
        """Start the orchestrator"""
        self.logger.info("starting orchestrator")
        
        # Reset test user wezabis completely
        if self.mdb.client:
            self.logger.info("Completely resetting test user 'wezabis'")
            people = self.mdb.client["network"]["people"]
            people.update_one(
                {"telegram_username": "wezabis"},
                {"$set": {
                    "github_username": None,
                    "email": None,
                    "state": "pre_referral",  # Start in pre_referral instead of gathering
                    "gather_attempts": 0,
                    "joined_at": datetime.now()
                }}
            )
            self.logger.info("Test user reset complete")
        
        await self.setup_handlers()
        await self.tel.run_forever()


if __name__ == "__main__":
    orchestrator = Orchestrator()
    # Create an async main function to properly await the flushdb operation
    async def main():
        # For testing purposes, we'll avoid flushing Redis to prevent infinite loops
        # If you MUST flush, uncomment the line below, but be aware it will clear message tracking
        # await orchestrator.kv.red.flushdb()
        await orchestrator.start()
    
    # Run the async main function
    asyncio.run(main())
