"""
Entry point for running the NaderAI agent
"""

import asyncio
import argparse
from agent.index import send_to_agent

async def main():
    parser = argparse.ArgumentParser(description="NaderAI Agent")
    parser.add_argument("message", type=str, help="Message to send to the agent")
    args = parser.parse_args()
    
    result = await send_to_agent(args.message)
    print("Response:", result["response"])
    
    if result.get("actionResults") and len(result["actionResults"]) > 0:
        print("\nActions performed:")
        for action in result["actionResults"]:
            print(f"- {action['type']}: {'Success' if action['result']['success'] else 'Failed'}")

if __name__ == "__main__":
    asyncio.run(main()) 