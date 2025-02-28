import asyncio
import os
from engine.packages.log import Logger
from engine.packages.red import Red
from telegram import Update
from telegram.ext import ApplicationBuilder
import dotenv
import json
import time

dotenv.load_dotenv()

class TEL:
    def __init__(self):
        self.logger = Logger("TEL", persist=True)
        self.kv = Red()
        self.mdb = None  # Will be set by orchestrator
        
        token = os.getenv("TELEGRAM_TOKEN")
        if not token:
            self.logger.error("No TELEGRAM_TOKEN found in environment variables!")
            token = ""
        
        # Create application
        self.t = ApplicationBuilder().token(token).build()
        self.is_running = False
        
        # Command handlers
        self.start_command_handler = None
        self.refer_command_handler = None
        self.general_message_handler = None
    
    async def store_message(self, chat_id, username, text, message_id):
        """Store message in Redis"""
        key = f"telegram:chat:{chat_id}:history"
        
        # Get existing messages
        existing = await self.kv.red.get(key)
        if existing:
            messages = json.loads(existing)
        else:
            messages = []
        
        # Add new message
        message_data = {
            "id": message_id,
            "user": username,
            "text": text,
            "timestamp": int(time.time())
        }
        messages.append(message_data)
        
        # Store back in Redis
        await self.kv.red.set(key, json.dumps(messages))
        self.logger.info(f"New message from {username}: {text}")
    
    async def handle_message(self, update):
        """Process message based on content and user status"""
        if not update.message or not update.effective_user:
            return
            
        text = update.message.text
        user_id = update.effective_user.id
        
        # Handle commands
        if text.startswith('/start'):
            if self.start_command_handler:
                await self.start_command_handler(update, None)
            return
            
        if text.startswith('/refer'):
            if self.refer_command_handler:
                # Create context-like object with args
                args = text.split()[1:] if len(text.split()) > 1 else []
                context = type('obj', (object,), {'args': args})
                await self.refer_command_handler(update, context)
            return
        
        # For non-command messages, check user status in DB
        if self.mdb and self.mdb.client:
            person = self.mdb.client["network"]["people"].find_one({"telegram_id": user_id})
            
            if person:
                # User exists, process based on state
                state = person.get("state", "unknown")
                self.logger.info(f"Processing message from user in state: {state}")
                
                # Call general message handler with state info
                if self.general_message_handler:
                    await self.general_message_handler(update, person)
            else:
                # User not in DB, suggest using /start
                await update.message.reply_text("I don't recognize you. Use /start to begin or /refer if you have a referral code.")
    
    async def check_updates(self):
        """Check for updates and handle messages"""
        try:
            # Get the last update_id we processed
            last_update_id = await self.kv.red.get("telegram:last_update_id")
            offset = int(last_update_id) + 1 if last_update_id else None
            
            updates = await self.t.bot.get_updates(offset=offset, limit=10, timeout=1)
            if updates:
                for update in updates:
                    if hasattr(update, 'message') and update.message and hasattr(update.message, 'text'):
                        message = update.message
                        text = message.text
                        user = message.from_user.username if message.from_user else "Unknown"
                        message_id = message.message_id
                        chat_id = message.chat_id
                        
                        # Store message
                        await self.store_message(chat_id, user, text, message_id)
                        
                        # Process message based on content and user status
                        await self.handle_message(update)
                        
                    # Store the last update_id we processed
                    await self.kv.red.set("telegram:last_update_id", str(update.update_id))
                    
        except Exception as e:
            self.logger.error(f"Error checking updates: {e}")
    
    async def setup_handlers(self, handlers):
        """Set up command handlers from orchestrator"""
        for handler in handlers:
            if hasattr(handler, 'commands') and handler.commands:
                # Convert frozenset to list to access first element
                commands = list(handler.commands)
                if commands and "start" in commands:
                    self.start_command_handler = handler.callback
                elif commands and "refer" in commands:
                    self.refer_command_handler = handler.callback
    
    async def start_polling(self):
        """Start polling for updates"""
        self.is_running = True
        await self.t.initialize()
        bot_info = await self.t.bot.get_me()
        bot_username = bot_info.username
        self.logger.info(f"Bot @{bot_username} started in polling mode")
    
    async def stop(self):
        """Stop the bot"""
        self.is_running = False
        try:
            await self.t.shutdown()
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
        self.logger.info("Bot stopped")
    
    async def run_forever(self):
        """Run the bot continuously"""
        await self.start_polling()
        
        # Keep the bot running
        while self.is_running:
            try:
                await self.check_updates()
                await asyncio.sleep(1)  # Check every second
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in bot loop: {e}")
                await asyncio.sleep(5)
        
        await self.stop()


if __name__ == "__main__":
    async def main():
        worker = TEL()
        try:
            await worker.run_forever()
        except KeyboardInterrupt:
            await worker.stop()
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
