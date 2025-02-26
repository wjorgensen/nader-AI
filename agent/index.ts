import 'dotenv/config';
import OpenAI from 'openai';
import naderCharacter from './character/naderCharacter.json';
import { processActions, generateActionsList } from './actions';

// Use a type assertion to ensure TypeScript recognizes the environment variable
const apiKey = process.env.HYPERBOLIC_API_KEY as string;

const client = new OpenAI({
  apiKey: apiKey,
  baseURL: 'https://api.hyperbolic.xyz/v1',
});

/**
 * Sends a message to the NaderAI agent and returns a structured response
 * @param userContent - The user's message content
 * @param processActionsAutomatically - Whether to automatically process actions (default: true)
 * @returns Promise containing the agent's response and action results
 */
export async function sendToAgent(userContent: string, processActionsAutomatically = true) {
  // Create a system prompt that incorporates the character's personality
  const characterBio = naderCharacter.bio.join(' ');
  const characterStyle = naderCharacter.style.all.join(' ') + ' ' + naderCharacter.style.chat.join(' ');
  
  const systemPrompt = `You are ${naderCharacter.name}, ${characterBio}
  
Your personality traits: ${naderCharacter.adjectives.join(', ')}

You know about: ${naderCharacter.topics.join(', ')}

Communication style: ${characterStyle}

IMPORTANT: You MUST respond in valid JSON format with the following structure:
{
  "response": "Your message text here",
  "actions": [] // Array of action objects if needed
}

Available actions:
${generateActionsList()}

Keep your responses authentic to your character. Never break character.`;

  const response = await client.chat.completions.create({
    messages: [
      {
        role: 'system',
        content: systemPrompt,
      },
      {
        role: 'user',
        content: userContent,
      },
    ],
    model: 'meta-llama/Meta-Llama-3.1-70B-Instruct',
  });

  const output = response.choices[0].message.content || '';
  
  try {
    // Parse the response to ensure it's valid JSON
    const parsedOutput = JSON.parse(output);
    
    // Process actions if requested
    let actionResults: Array<{type: string, result: any}> = [];
    if (processActionsAutomatically && parsedOutput.actions && parsedOutput.actions.length > 0) {
      actionResults = await processActions(parsedOutput.actions);
    }
    
    return {
      ...parsedOutput,
      actionResults
    };
  } catch (error) {
    // If parsing fails, return a formatted error
    console.error("Failed to parse LLM response as JSON:", error);
    return {
      response: "Sorry, I encountered an error processing your request.",
      actions: [],
      actionResults: []
    };
  }
}
