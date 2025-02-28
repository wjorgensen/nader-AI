import os
import json
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI
from .actions import generate_actions_list, definitions

from engine.packages.log import Logger
from engine.packages.mongo import MDB
from engine.packages.red import Red

load_dotenv()


class AI:
    def __init__(self):
        self.api_key = os.getenv("HYPERBOLIC_API_KEY")
        self.base_url = "https://api.hyperbolic.xyz/v1"
        self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        
        self.logger = Logger("agent", persist=True)
        self.mdb = MDB()
        self.kv = Red()
        
        with open("engine/agent/character/character.json") as f:
            self.character = json.load(f)
    
    def _system(self):
        """
        Builds the system prompt for the AI model based on character data.
        
        Returns:
            str: The formatted system prompt
        """

        prompt = f"""
                YOU ARE {self.character["name"]},
                YOUR BIO: {" ".join(self.character["bio"])}
                YOUR PERSONALITY TRAITS: {", ".join(self.character["adjectives"])}
                YOU KNOW ABOUT: {", ".join(self.character["topics"])}
                COMMUNICATION STYLE: {(
                    " ".join(self.character["style"]["all"])
                    + " "
                    + " ".join(self.character["style"]["chat"])
                )}
                
                IMPORTANT: You MUST respond IN THE PROPER FORMAT GIVEN TO YOU.
                
                Keep your responses authentic to your character. Never break character.
                """

        return prompt
    
    async def act(self, content: str):
        """
        Sends a message to the NaderAI agent and returns a structured response
        
        Args:
            content (str): The user's message content
            
        Returns:
            dict: The agent's response and action results
        """
        self.logger.info(f"processing agent action with content: {content[:50]}...")
        
        try:
            response = await self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": self._system(),
                    },
                    {
                        "role": "user",
                        "content": content,
                    },
                ],
                model="meta-llama/Meta-Llama-3.1-70B-Instruct",
            )
            output = response.choices[0].message.content
            if not output: raise Exception("failed response from agent")
            parsed = json.loads(output)
            return {
                "status": "success",
                "response": parsed
            }
        except Exception as error:
            self.logger.error(f"error processing agent action: {str(error)}")
            return {
                "status": "error",
                "response": "sorry, I encountered an error processing your request.",
            }
    
if __name__ == "__main__":
    async def main():
        agent = AI()
        result = await agent.act("Tell me about ZK proofs")
    asyncio.run(main())
