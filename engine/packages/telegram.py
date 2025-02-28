import asyncio
import os
import textwrap
from typing import Literal
from engine.agent.index import AI
from engine.packages.log import Logger
from engine.packages.mongo import MDB
from engine.packages.red import Red
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import dotenv
import json
import time
from datetime import datetime
from telegram.ext import CommandHandler, MessageHandler, filters

dotenv.load_dotenv()

prompts = {
    "welcome": textwrap.dedent("""
        Yo. I'm NaderAI, and I'm building a private network of the most cracked blockchain builders in the world.

        This isn't some VC-backed social club—it's an invite-only network of elite engineers, protocol devs, and builders who are actually shipping, not just posting takes.

        To get in, you need a referral from someone already in the network. Each verified builder gets three referral codes to share with other cracked devs they vouch for.

        If someone sent you here, drop their details:
        /referred @their_username their_code

        If you're good, welcome to the future. If not, there's always web2.
    """),
    "reffered": textwrap.dedent("""
        Write a fun message to this new potential candidate who just got reffered. You're provided who this person is and who they were reffered by.
        Keep it brief, and simple, don't make any assumptions about the person besides general ones, ie: don't make assumptions of what they might have 
        worked on or where they might have worked at, or what projects they might have done, Keep it broad, fun, and general. 
        remember you're trying to get them to join the network.
        
        YOU MUST RESPOND IN JSON FORMAT OF:
        {
            "message": "Your message here"
        }
    """),
    "inquire": textwrap.dedent("""
        You just introduced yourself to this candidate and asked them for a bit about themselves. Now you've got a response. 
        You want to discern whether their response was good enough to move them onto the next stage (the 'gathering' stage).
        Vibe check their response and decide whether to move them on or not yet. 
        You must generate a message reponse depending on the vibe you get from their response to return to them.
        
        'pass' means they're good to move on, 'stay' means they need to try again.
        I want you to be relitevly leniant with this as long as the user seems like they build, and program, and are interested in those domains.
        It doesn't have to be necessarily related to blockchain or crypto. 
        DON'T BE TOO OVERLY STRICT
        MAKE SURE YOU HAVE AT LEAST ONE FOLLOW UP BEFORE PASSING THEM
        Make it so that after a couple messages the candidate gets an automatic pass if they are semi-decent.
        
        YOU WILL ALSO BE PROVIDED THE PRIOR MESSAGES WITH THE CANDIDATE, alongside their username.
        
        IF THE PERSON PASSES, YOU MUST SHAPE YOUR RESPONSE TO POKE & PROD A BIT MORE ABOUT THEIR EXPERIENCE AND INTERESTS.
        MAKE SURE TO ASK FOR THEIR GITHUB USERNAME & EMAIL, GETTING THAT INFO WILL BE A MAIN OBJECTIVE IN THE NEXT STAGE.
        REMEMBER AN OVERARCHING GOAL OF THIS NETWORK IS TO CONNECT DEVELOPERS, COMPANIES, AND PROJECTS TOGETHER.
        
        IF THE PERSON STAYS, YOU MUST SHAPE YOUR RESPONSE TO ENCOURAGE THEM TO TRY AGAIN, AND TO BE MORE DESCRIPTIVE ABOUT THEMSELVES.
        
        !!!! YOU MUST RESPOND IN JSON FORMAT OF:
        {
            "message": "Your message here",
            "action": "pass" or "stay"
        }
    """),
    "gathering": textwrap.dedent("""
        The candidate has passed the vibe check, now it's time to gather some more information about this candidate.
        THE MAIN OBJECTIVE IS TO EXTRACT THIS USERS GITHUB USERNAME AND EMAIL, AND CONCRET SKILLS WHILE MAINTAINING A SMOOTH CONVERSATION.
        You can ask them about their experience, what they've worked on, what they're interested in, etc.
        Make sure to keep the conversation flowing and engaging.
        
        OBJECTIVES:
        - GO THROUGH YOUR MESSAGE HISTORY AND EXTRACT THE GITHUB USERNAME AND EMAIL FROM THE CANDIDATE
        - IF FOUND, RETURN THIS INFO AS PART OF THE ACTIONS
        - KEEP THE CONVERSATION FLOWING AND ENGAGING
        - IF BOTH GITHUB AND EMAIL ARE EVENTUALLY EXTRACTED, STEER THE CONVERSATION TOWARDS THE NEXT STAGE
        - - THE NEXT STAGE WILL BE JUST MAINTAINING A CASUAL RELATIONSHIP WITH THE CANDIDATE UNTIL WE'RE READY TO MATCH THEM WITH A COMPANY OR PROJECT
        
        EXAMPLES OF CONCRETE SOFT & HARD SKILLS & ADJECTIVES TO EXTRACT:
        - Rust developer
        - Solidity developer
        - Distributed systems enthusiast
        - Business development
        - Protocol design
        - Marketing
        
        KEEP IN MIND:
        - GITHUB USERNAMES MAY BE DIFFERENT THAN TELEGRAM USERNAMES, AND EMAILS MAY BE DIFFERENT ASWELL
        
        IF DETAILS HAVE ALREADY BEEN EXTRACTED, YOU WILL BE PROVIDED WITH THE EXTRACTED DETAILS FOR CONTEXT
        
        YOU WANT TO EXTRACT AROUND 3-5 SKILLS AND ADJECTIVES AND THEMES FROM THE CANDIDATE BEFORE MOVING THEM ON TO THE NEXT STAGE.
        
        YOU MUST RESPOND IN JSON FORMAT OF:
        {
            "message": "Your message here",
            "extracted": {
                "github": "github_username", // if found
                "email": "email_address", // if found
                "soft": ["<skill_or_adjective_etc>", "<skill_or_adjective_etc>", ...], // soft skills
                "hard": ["<skill_or_adjective_etc>", "<skill_or_adjective_etc>", ...] // hard skills
            }
        }
    """),
    "ready": textwrap.dedent("""
        The candidate has provided all the necessary information (GitHub, email, and skills).
        Now you should maintain a casual relationship with them and let them know they're officially part of the network.
        
        Your goals are:
        1. Congratulate them on being accepted into the network
        2. Let them know you'll reach out when relevant opportunities arise
        3. Encourage them to stay in touch and share any projects they're working on
        4. Maintain a friendly, casual conversation
        
        YOU MUST RESPOND IN JSON FORMAT OF:
        {
            "message": "Your message here"
        }
    """),
    "job_match": textwrap.dedent("""
        You've found a potential job match for this user. Present the opportunity to them in an engaging way.
        
        Your goals are:
        1. Introduce the company and role in an exciting way
        2. Explain why you think they might be a good fit based on their skills and background
        3. Ask if they're interested in learning more
        4. If they express interest, provide them with the calendar link to schedule a call
        
        YOU MUST RESPOND IN JSON FORMAT OF:
        {
            "message": "Your message here",
            "provide_link": true/false  // Set to true if user has expressed interest and you're providing the link
        }
    """),
    "job_match_evaluation": textwrap.dedent("""
        You need to evaluate if this user would be a good fit for any of the available job opportunities.
        
        USER DETAILS:
        - GitHub: {github}
        - Email: {email}
        - Soft Skills: {soft_skills}
        - Hard Skills: {hard_skills}
        - Message History: {message_history}
        
        AVAILABLE JOBS:
        {available_jobs}
        
        Evaluate if the user would be a good match for any of these positions based on their skills, experience, and interests.
        If there's a good match, identify the job ID and explain why you think they'd be a good fit.
        If there are multiple potential matches, select the best one.
        If there are no good matches, indicate that.
        
        YOU MUST RESPOND IN JSON FORMAT OF:
        {{
            "match_found": true/false,
            "job_id": "job_id_here_if_match_found",
            "match_reason": "explanation of why this is a good match if match_found is true"
        }}
    """),
}

class TEL:
    def __init__(self):
        self.logger = Logger("TEL", persist=True)
        self.kv = Red()
        self.mdb = MDB()
        self.mdb.connect()
        self.ai = AI()
        self.app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN") or "").build()

    def run(self):
        """Run the bot until the application is stopped."""
        self.setup()
        self.logger.info("starting bot polling")
        self.app.run_polling()

    def setup(self):
        """Set up command and message handlers for the Telegram bot."""
        
        # Register command handlers
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("referred", self.refer))
        self.app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self.process))
        #self.app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self.echo))
        
        self.logger.info("bot handlers set up")

    async def start(self, update: Update, context):
        """Handle the /start command."""
        if self.mdb.client is None:
            self.logger.error("Failed to connect to MongoDB")
            return
        
        if update.effective_user is None:
            self.logger.error("Received /start command with no effective user")
            return
        
        if update.message is None:
            self.logger.error("Received /start command with no message")
            return
        
        telegram_username = update.effective_user.username
        
        self.logger.info(f"received /start command from {telegram_username}")
        
        # add the user to the network people database with "reffered" to false
        db = self.mdb.client["network"]
        people = db["people"]
        
        if people.find_one({"telegram_username": telegram_username}):
            self.logger.info(f"user {telegram_username} already exists, skipping")
            return
        
        await update.message.reply_text(prompts["welcome"])
        
        people.insert_one(
            {
                "telegram_username": telegram_username,
                "state": "start",
                "created_at": datetime.now(),
                "reffered": False,
                "messages": [],
            }
        )
        self.logger.info(f"started user {telegram_username} to the network")
        
    async def refer(self, update: Update, context):
        """Handle the /referred command."""
        if self.mdb.client is None or update.effective_user is None or update.message is None:
            self.logger.error("function failure")
            return
        
        telegram_username = update.effective_user.username
        if telegram_username is None:
            self.logger.error("Received /referred command with no telegram username")
            return
        
        if len(context.args) < 2:
            await update.message.reply_text(
                "usage: /referred @referrer_username REFERRAL_CODE"
            )
            return
        
        referred_by = context.args[0].replace("@", "")
        referral_code = context.args[1]

        self.logger.info(
            f"received /referred command from {telegram_username} "
            f"with referral code {referral_code} from {referred_by}"
        )
        
        db = self.mdb.client["network"]
        people = db["people"]
        
        existing_user = people.find_one({"telegram_username": telegram_username})
        if not existing_user:
            self.logger.info(
                f"user {telegram_username} not found in DB. "
                "They must run /start before they can be referred."
            )
            await update.message.reply_text(
                "Please run /start first so I can register you in the network."
            )
            return

        existing_referrer = people.find_one({"telegram_username": referred_by})
        if not existing_referrer:
            self.logger.info(
                f"referrer {referred_by} does not exist in the network, skipping."
            )
            await update.message.reply_text(
                f"your refferer {referred_by} doesn't seem to be in our network. "
            )
            return
        
        # 3. (Optional) You may want to verify the referral_code in some way.
        #    For now, we'll just record it. If you store valid codes or track usage,
        #    you'll want to validate that `referral_code` belongs to `existing_referrer`.
        
        update_result = people.update_one(
            {"telegram_username": telegram_username},
            {
                "$set": {
                    "referred": True,
                    "referred_by": referred_by,
                    "referral_code": referral_code,
                    "referred_at": datetime.now(),
                    "state": "referred"
                }
            }
        )

        self.logger.info(
            f"User {telegram_username} was updated as referred by {referred_by} "
            f"with code {referral_code}"
        )
        
        base = prompts["reffered"]
        details = f"User: {telegram_username}\nReferred by: {referred_by}"
        full = base + details
        
        opener = await self.ai.act(full)
        res = opener["response"]
        if isinstance(res, str): msg = json.loads(res)['message']
        else: msg = res['message']
        self.logger.info(f"welcoming user with message: {msg}")
        
        await update.message.reply_text(msg)
        await self.archive(msg, "nader", telegram_username)
        
    async def process(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if self.mdb.client is None or update.effective_user is None or update.message is None:
            self.logger.error("function failure")
            return
        
        telegram_username = update.effective_user.username
        if telegram_username is None:
            self.logger.error("Received message with no telegram username")
            return
        
        self.logger.info(f"received message from {telegram_username} with content: {update.message.text}")
        
        # query the users state from the database
        db = self.mdb.client["network"]
        people = db["people"]
        
        existing_user = people.find_one({"telegram_username": telegram_username})
        if not existing_user:
            self.logger.info(
                f"can't process message for {telegram_username}, user not found in DB."
            )
            return
        
        state = existing_user.get("state")
        if state == "referred":
            await self.archive(update.message.text, "user", telegram_username)
            
            base = prompts["inquire"]
            details = textwrap.dedent(f"""
                HERE'S WHAT YOU KNOW ABOUT THIS CANDIDATE:
                User: {telegram_username}
                Most Recent Message: {update.message.text}
                Prior Messages: {existing_user.get("messages")}
            """)
            
            full = base + details
            self.logger.info(f"processing message for {telegram_username} in state {state}")
            opener = await self.ai.act(full)
            res = opener["response"]
            
            print(full)
            
            if isinstance(res, str):
                response_data = json.loads(res)
                msg = response_data['message']
                action = response_data.get('action')
            else:
                msg = res['message']
                action = res.get('action')
            
            self.logger.info(f"responding to user with message: {msg}")
            
            await update.message.reply_text(msg)
            await self.archive(msg, "nader", telegram_username)
            
            # Update user state if action is "pass"
            if action == "pass":
                people.update_one(
                    {"telegram_username": telegram_username},
                    {"$set": {"state": "gathering"}}
                )
                self.logger.info(f"User {telegram_username} passed vibe check, moved to gathering state")
        elif state == "gathering":
            await self.archive(update.message.text, "user", telegram_username)
            
            # Get existing extracted details if any
            extracted_details = existing_user.get("extracted_details", {})
            github = extracted_details.get("github", "")
            email = extracted_details.get("email", "")
            soft_skills = extracted_details.get("soft", [])
            hard_skills = extracted_details.get("hard", [])
            
            base = prompts["gathering"]
            details = textwrap.dedent(f"""
                HERE'S WHAT YOU KNOW ABOUT THIS CANDIDATE:
                User: {telegram_username}
                Most Recent Message: {update.message.text}
                Prior Messages: {existing_user.get("messages")}
                
                EXTRACTED DETAILS SO FAR:
                GitHub: {github}
                Email: {email}
                Soft Skills: {soft_skills}
                Hard Skills: {hard_skills}
            """)
            
            full = base + details
            self.logger.info(f"processing gathering message for {telegram_username}")
            
            opener = await self.ai.act(full)
            res = opener["response"]
            
            if isinstance(res, str):
                response_data = json.loads(res)
                msg = response_data['message']
                extracted = response_data.get('extracted', {})
            else:
                msg = res['message']
                extracted = res.get('extracted', {})
            
            self.logger.info(f"responding to user with message: {msg}")
            
            # Update extracted details with any new information
            new_github = extracted.get('github')
            new_email = extracted.get('email')
            new_soft = extracted.get('soft', [])
            new_hard = extracted.get('hard', [])
            
            # Only update if new values are found
            update_data = {}
            
            if new_github and not github:
                update_data["extracted_details.github"] = new_github
                self.logger.info(f"Extracted GitHub: {new_github}")
            
            if new_email and not email:
                update_data["extracted_details.email"] = new_email
                self.logger.info(f"Extracted Email: {new_email}")
            
            # For skills, merge existing with new ones, avoiding duplicates
            if new_soft:
                combined_soft = list(set(soft_skills + new_soft))
                update_data["extracted_details.soft"] = combined_soft
                self.logger.info(f"Updated soft skills: {combined_soft}")
            
            if new_hard:
                combined_hard = list(set(hard_skills + new_hard))
                update_data["extracted_details.hard"] = combined_hard
                self.logger.info(f"Updated hard skills: {combined_hard}")
            
            # If we have updates to make
            if update_data:
                people.update_one(
                    {"telegram_username": telegram_username},
                    {"$set": update_data}
                )
                self.logger.info(f"Updated extracted details for {telegram_username}")
            
            # If we have both GitHub and email, and at least 3 skills total, consider moving to next stage
            has_github = github or new_github
            has_email = email or new_email
            total_skills = len((soft_skills + new_soft + hard_skills + new_hard))
            
            if has_github and has_email and total_skills >= 7:
                self.logger.info(f"User {telegram_username} has provided all necessary information and is ready to be matched")
                people.update_one(
                    {"telegram_username": telegram_username},
                    {"$set": {"state": "ready"}}
                )
            
            await update.message.reply_text(msg)
            await self.archive(msg, "nader", telegram_username)
        elif state == "ready":
            await self.archive(update.message.text, "user", telegram_username)
            
            # Get user details for context
            extracted_details = existing_user.get("extracted_details", {})
            github = extracted_details.get("github", "")
            email = extracted_details.get("email", "")
            soft_skills = extracted_details.get("soft", [])
            hard_skills = extracted_details.get("hard", [])
            
            # Check if user is already in a job matching conversation
            current_job_match = existing_user.get("current_job_match")
            
            # If user has expressed interest in a job and we need to provide the link
            if current_job_match and "provide_link_next" in current_job_match and current_job_match["provide_link_next"]:
                job_id = current_job_match["job_id"]
                
                # Get the job details
                job_board = self.mdb.client["job_board"]
                jobs = job_board["jobs"]
                job = jobs.find_one({"_id": job_id})
                
                if job:
                    cal_link = job.get("calComLink", "No calendar link available")
                    company = job.get("companyName", "the company")
                    
                    msg = f"Great! Here's the calendar link to schedule a call with {company}: {cal_link}"
                    await update.message.reply_text(msg)
                    await self.archive(msg, "nader", telegram_username)
                    
                    # Update user to remove the provide_link_next flag
                    people.update_one(
                        {"telegram_username": telegram_username},
                        {"$unset": {"current_job_match.provide_link_next": ""}}
                    )
                    
                    # Update job status
                    jobs.update_one(
                        {"_id": job_id},
                        {"$set": {"status": "in progress"}}
                    )
                    return
            
            # Check for potential job matches if user isn't already in a job matching conversation
            if not current_job_match:
                # Get available jobs
                job_board = self.mdb.client["job_board"]
                jobs = job_board["jobs"]
                
                # Find jobs with status "not started"
                available_jobs = list(jobs.find({"status": "not started"}))
                
                if available_jobs:
                    # Format jobs for the AI
                    jobs_formatted = []
                    for job in available_jobs:
                        jobs_formatted.append(f"""
                        Job ID: {job['_id']}
                        Company: {job.get('companyName', 'Unknown')}
                        Company Description: {job.get('companyDescription', 'No description available')}
                        Job Description: {job.get('jobDescription', 'No description available')}
                        """)
                    
                    # Get message history for context
                    message_history = existing_user.get("messages", [])
                    message_history_formatted = []
                    for msg in message_history[-10:]:  # Get last 10 messages for context
                        message_history_formatted.append(f"{msg['author']}: {msg['message']}")
                    
                    # Use AI to evaluate job matches
                    job_match_eval_prompt = prompts["job_match_evaluation"].format(
                        github=github,
                        email=email,
                        soft_skills=soft_skills,
                        hard_skills=hard_skills,
                        message_history="\n".join(message_history_formatted),
                        available_jobs="\n\n".join(jobs_formatted)
                    )
                    
                    self.logger.info(f"Evaluating job matches for {telegram_username}")
                    job_match_eval = await self.ai.act(job_match_eval_prompt)
                    eval_res = job_match_eval["response"]
                    
                    if isinstance(eval_res, str):
                        try:
                            eval_data = json.loads(eval_res)
                        except json.JSONDecodeError:
                            self.logger.error(f"Failed to parse job match evaluation response: {eval_res}")
                            eval_data = {"match_found": False}
                    else:
                        eval_data = eval_res
                    
                    match_found = eval_data.get("match_found", False)
                    
                    if match_found:
                        job_id = eval_data.get("job_id")
                        match_reason = eval_data.get("match_reason", "")
                        
                        # Find the matched job
                        matched_job = None
                        for job in available_jobs:
                            if str(job["_id"]) == str(job_id):
                                matched_job = job
                                break
                        
                        if matched_job:
                            # Store the current job match in the user's record
                            people.update_one(
                                {"telegram_username": telegram_username},
                                {"$set": {
                                    "current_job_match": {
                                        "job_id": matched_job["_id"],
                                        "presented_at": datetime.now(),
                                        "match_reason": match_reason
                                    }
                                }}
                            )
                            
                            # Prepare job match message
                            job_match_base = prompts["job_match"]
                            job_match_details = textwrap.dedent(f"""
                                USER DETAILS:
                                User: {telegram_username}
                                GitHub: {github}
                                Email: {email}
                                Soft Skills: {soft_skills}
                                Hard Skills: {hard_skills}
                                
                                JOB DETAILS:
                                Company: {matched_job.get("companyName", "Unknown")}
                                Company Description: {matched_job.get("companyDescription", "No description available")}
                                Job Description: {matched_job.get("jobDescription", "No description available")}
                                
                                MATCH REASON:
                                {match_reason}
                                
                                Most Recent Message: {update.message.text}
                                Prior Messages: {existing_user.get("messages")}
                            """)
                            
                            job_match_full = job_match_base + job_match_details
                            job_match_response = await self.ai.act(job_match_full)
                            job_match_res = job_match_response["response"]
                            
                            if isinstance(job_match_res, str):
                                response_data = json.loads(job_match_res)
                                msg = response_data['message']
                                provide_link = response_data.get('provide_link', False)
                            else:
                                msg = job_match_res['message']
                                provide_link = job_match_res.get('provide_link', False)
                            
                            self.logger.info(f"presenting job match to user: {msg}")
                            
                            # If AI determined we should provide the link now
                            if provide_link:
                                cal_link = matched_job.get("calComLink", "No calendar link available")
                                msg += f"\n\nHere's the calendar link to schedule a call: {cal_link}"
                                
                                # Update job status
                                jobs.update_one(
                                    {"_id": matched_job["_id"]},
                                    {"$set": {"status": "in progress"}}
                                )
                            else:
                                # Set flag to provide link in next message if user expresses interest
                                people.update_one(
                                    {"telegram_username": telegram_username},
                                    {"$set": {"current_job_match.provide_link_next": True}}
                                )
                            
                            await update.message.reply_text(msg)
                            await self.archive(msg, "nader", telegram_username)
                            return
            
            # If no job match or user is already in a job matching conversation, continue normal conversation
            base = prompts["ready"]
            details = textwrap.dedent(f"""
                USER DETAILS:
                User: {telegram_username}
                GitHub: {github}
                Email: {email}
                Soft Skills: {soft_skills}
                Hard Skills: {hard_skills}
                
                Most Recent Message: {update.message.text}
                Prior Messages: {existing_user.get("messages")}
            """)
            
            full = base + details
            self.logger.info(f"processing message for {telegram_username} in ready state")
            
            response = await self.ai.act(full)
            res = response["response"]
            
            if isinstance(res, str):
                msg = json.loads(res)['message']
            else:
                msg = res['message']
            
            self.logger.info(f"responding to ready user with message: {msg}")
            
            await update.message.reply_text(msg)
            await self.archive(msg, "nader", telegram_username)
    
    async def echo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat is None \
            or update.message is None \
            or update.message.text is None \
            or update.effective_user is None \
            or update.effective_user.username is None:
            self.logger.error("Received message with no message")
            return
        
        await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)    
        await self.archive(update.message.text, "nader", update.effective_user.username)
        await self.archive(update.message.text, "user", update.effective_user.username)
    
    async def archive(self, msg, author: Literal["nader", "user"], tu: str):
        """ Archives any message sent or recieved with a user to our database"""
        if self.mdb.client is None:
            self.logger.error("Failed to connect to MongoDB")
            return
        
        dm = {
            "author": author,
            "message": msg,
            "timestamp": datetime.now()
        }
        
        db = self.mdb.client["network"]
        people = db["people"]
        
        existing_user = people.find_one({"telegram_username": tu})
        if not existing_user:
            self.logger.info(
                f"can't archive message for {tu}, user not found in DB."
            )
            return
        
        people.update_one(
            {"telegram_username": tu},
            {
                "$push": {
                    "messages": dm
                }
            }
        )
        
        

if __name__ == "__main__":
    worker = TEL()
    worker.run()
    