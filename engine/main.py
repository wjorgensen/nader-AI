import asyncio
import uvicorn
from engine.packages.log import Logger

logger = Logger("main", persist=True)

def run_server():
    """Run the FastAPI server with the Telegram bot"""
    logger.info("Starting FastAPI server with Telegram bot integration")
    uvicorn.run("engine.server.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    run_server()
