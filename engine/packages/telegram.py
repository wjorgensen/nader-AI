import asyncio
import os
from engine.packages.log import Logger
from engine.packages.red import Red
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import dotenv
dotenv.load_dotenv()

class TEL:
    def __init__(self):
        self.logger = Logger("TEL", persist=True)
        self.kv = Red()
        self.t = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN") or "").build()


if __name__ == "__main__":
    print(os.getcwd())
    
    async def main():
        worker = TEL()
    
    asyncio.run(main())
