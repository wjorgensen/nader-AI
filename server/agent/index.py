"""
Main module for the NaderAI agent
Handles communication with the AI model and processes responses
"""

import os
import json
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI

from .actions import generate_actions_list, process_actions

# Load environment variables
load_dotenv()

# Get API key from environment
api_key = os.getenv("HYPERBOLIC_API_KEY")

# Initialize OpenAI client
client = AsyncOpenAI(
    api_key=api_key,
    base_url="https://api.hyperbolic.xyz/v1"
)

# Load character data
with open("agent/character/naderCharacter.json", "r") as f:
    nader_character = json.load(f)


async def send_to_agent(user_content, process_actions_automatically=True):
    """
    Sends a message to the NaderAI agent and returns a structured response
    :param user_content: The user's message content
    :param process_actions_automatically: Whether to automatically process actions (default: True)
    :return: Promise containing the agent's response and action results
    """
    # Create a system prompt that incorporates the character's personality
    character_bio = " ".join(nader_character["bio"])
    character_style = " ".join(nader_character["style"]["all"]) + " " + " ".join(nader_character["style"]["chat"])
    
    system_prompt = f"""You are {nader_character["name"]}, {character_bio}
    
Your personality traits: {", ".join(nader_character["adjectives"])}

You know about: {", ".join(nader_character["topics"])}

Communication style: {character_style}

IMPORTANT: You MUST respond in valid JSON format with the following structure:
{{
  "response": "Your message text here",
  "actions": [] // Array of action objects if needed
}}

Available actions:
{generate_actions_list()}

Keep your responses authentic to your character. Never break character."""

    # Call the API
    response = await client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_content,
            },
        ],
        model="meta-llama/Meta-Llama-3.1-70B-Instruct",
    )

    output = response.choices[0].message.content or ""
    
    try:
        # Parse the response to ensure it's valid JSON
        parsed_output = json.loads(output)
        
        # Process actions if requested
        action_results = []
        if process_actions_automatically and parsed_output.get("actions") and len(parsed_output["actions"]) > 0:
            action_results = await process_actions(parsed_output["actions"])
        
        return {
            **parsed_output,
            "actionResults": action_results
        }
    except Exception as error:
        # If parsing fails, return a formatted error
        print("Failed to parse LLM response as JSON:", error)
        return {
            "response": "Sorry, I encountered an error processing your request.",
            "actions": [],
            "actionResults": []
        }


# Example usage in an async context
if __name__ == "__main__":
    async def main():
        result = await send_to_agent("Tell me about ZK proofs")
        print(result["response"])
        
    asyncio.run(main()) 