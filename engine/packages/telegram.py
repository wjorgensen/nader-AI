import asyncio
import os
from engine.packages.log import Logger
from engine.packages.red import Red
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import dotenv
import json
import time

dotenv.load_dotenv()

class TEL:
    def __init__(self):
        self.logger = Logger("TEL", persist=True)
        self.kv = Red()
        
        token = os.getenv("TELEGRAM_TOKEN")
        if not token:
            self.logger.error("No TELEGRAM_TOKEN found in environment variables!")
            token = ""
        
        # Create application
        self.t = ApplicationBuilder().token(token).build()
        self.is_running = False
    
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
        self.kv.red.set(key, json.dumps(messages))
        self.logger.info(f"New message from {username}: {text}")
    
    async def start_polling(self):
        """Start polling for updates"""
        self.is_running = True
        await self.t.initialize()
        bot_info = await self.t.bot.get_me()
        bot_username = bot_info.username
        self.logger.info(f"Bot @{bot_username} started in polling mode")
    
    async def check_updates(self):
        """Check for updates"""
        try:
            # Get the last update_id we processed
            last_update_id = await self.kv.red.get("telegram:last_update_id")
            offset = int(last_update_id) + 1 if last_update_id else None
            
            updates = await self.t.bot.get_updates(offset=offset, limit=10, timeout=1)
            if updates:
                for update in updates:
                    if hasattr(update, 'message') and update.message:
                        message = update.message
                        if hasattr(message, 'text') and message.text:
                            text = message.text
                            user = message.from_user.username if message.from_user else "Unknown"
                            message_id = message.message_id
                            chat_id = message.chat_id
                            
                            await self.store_message(chat_id, user, text, message_id)
                            
                            # Store the last update_id we processed
                            self.kv.red.set("telegram:last_update_id", str(update.update_id))
        except Exception as e:
            self.logger.error(f"Error checking updates: {e}")
    
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
