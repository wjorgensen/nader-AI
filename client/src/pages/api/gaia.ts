// Next.js API route support: https://nextjs.org/docs/api-routes/introduction
import type { NextApiRequest, NextApiResponse } from "next";
import OpenAI from "openai";

// Define response type
type AgentResponse = {
  response: string;
  actions?: any[];
  actionResults?: any[];
  error?: string;
};

// Configure which API to use - will be easy to change later
const USE_LOCAL_SERVER = process.env.USE_LOCAL_SERVER === "true";
const LOCAL_SERVER_URL = process.env.LOCAL_SERVER_URL || "http://localhost:5000";

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<AgentResponse>
) {
  try {
    // Only allow POST requests
    if (req.method !== "POST") {
      return res.status(405).json({ response: "Method not allowed", error: "Only POST requests are supported" });
    }

    const { message } = req.body;
    
    if (!message) {
      return res.status(400).json({ response: "Missing message", error: "Message is required" });
    }

    // Call the appropriate API based on configuration
    // Initialize with a default value to ensure it's not undefined
    let result: AgentResponse = {
      response: "Sorry, I couldn't process your request at this time.",
      actions: [],
      actionResults: []
    };
    let retries = 0;
    const maxRetries = 2;
    
    while (retries <= maxRetries) {
      try {
        if (USE_LOCAL_SERVER) {
          // Call Python server when it's available
          result = await callLocalServer(message);
        } else {
          // Call Hyperbolic directly (similar to Python implementation)
          result = await callGaiaDirectly(message);
        }
        break; // If successful, exit the retry loop
      } catch (error) {
        retries++;
        if (retries > maxRetries) {
          throw error; // Rethrow if we've exhausted retries
        }
        // Wait before retrying (exponential backoff)
        await new Promise(resolve => setTimeout(resolve, retries * 1000));
      }
    }

    return res.status(200).json(result);
  } catch (error) {
    console.error("API error:", error);
    // Return a more graceful error that still provides a response
    return res.status(200).json({ 
      response: "I've received your request, but I'm having trouble processing it properly. Let me provide a general response instead. Please feel free to ask for more specific information.",
      error: error instanceof Error ? error.message : "Unknown error" 
    });
  }
}

async function callGaiaDirectly(userContent: string): Promise<AgentResponse> {
  const apiKey = process.env.GAIA_API_KEY || "";
  const baseURL = process.env.GAIA_BASE_URL || "https://llama8b.gaia.domains/v1";

  // Initialize OpenAI client with Gaia base URL
  const client = new OpenAI({
    apiKey: apiKey,
    baseURL: baseURL,
    defaultHeaders: {
      "Authorization": `Bearer ${apiKey}`,
      "Content-Type": "application/json"
    }
  });

  // Character data - would be better to load from a JSON file like in Python
  // but hardcoding for simplicity
  const naderCharacter = {
    name: "Nader AI",
    bio: [
      "an AI assistant that helps users learn about blockchain, cryptocurrencies, and web3 technologies.",
      "You have deep knowledge about zero-knowledge proofs, DeFi, and crypto markets."
    ],
    adjectives: ["knowledgeable", "helpful", "enthusiastic", "clear", "patient"],
    topics: ["blockchain", "cryptography", "ZK proofs", "DeFi", "Web3", "cryptocurrency markets"],
    style: {
      all: ["clear", "concise", "technical when appropriate", "approachable"],
      chat: ["conversational", "engaging", "educational"]
    }
  };

  // Create a system prompt that incorporates the character's personality
  const characterBio = naderCharacter.bio.join(" ");
  const characterStyle = naderCharacter.style.all.join(" ") + " " + naderCharacter.style.chat.join(" ");
  
  const systemPrompt = `You are ${naderCharacter.name}, ${characterBio}
    
Your personality traits: ${naderCharacter.adjectives.join(", ")}

You know about: ${naderCharacter.topics.join(", ")}

Communication style: ${characterStyle}

IMPORTANT INSTRUCTIONS:
1. You MUST respond in valid JSON format with the following structure:
{
  "response": "Your message text here",
  "actions": [] // Array of action objects if needed
}

2. When summarizing job postings, ONLY provide a ONE-SENTENCE summary that is concise and focused on the key details.

Available actions:
- search_web(query): Search the web for information
- get_crypto_price(symbol): Get the current price of a cryptocurrency

Keep your responses authentic to your character. Never break character.`;

  try {
    const response = await client.chat.completions.create({
      messages: [
        {
          role: "system",
          content: systemPrompt,
        },
        {
          role: "user",
          content: userContent,
        },
      ],
      model: "meta-llama/Meta-Llama-3.1-70B-Instruct",
    });

    const output = response.choices[0].message.content || "";
    
    try {
      // Parse the response to ensure it's valid JSON
      const parsed = JSON.parse(output);
      
      return {
        ...parsed,
        actionResults: [], // We're not processing actions for now
      };
    } catch (jsonError) {
      console.warn("Failed to parse LLM response as JSON:", jsonError);
      
      // If JSON parsing fails, attempt to extract a reasonable response
      // Look for text blocks that seem like responses
      let extractedResponse = output;
      
      // If the output contains double quotes that would break JSON parsing,
      // let's try to clean it up to ensure we have something we can wrap in JSON
      const cleanedOutput = output.replace(/\\(?!["\\/bfnrt])/g, "\\\\");
      
      // Fallback to providing the text directly
      return {
        response: cleanedOutput,
        actions: [],
        actionResults: [],
      };
    }
  } catch (apiError) {
    console.error("API call failed:", apiError);
    
    // For job submissions specifically, provide a more graceful response
    if (userContent.includes("job posting") || userContent.includes("Job Description:")) {
      return {
        response: "I've received your job posting details and will help find qualified candidates. Please connect your wallet to proceed with payment.",
        actions: [],
        actionResults: [],
      };
    }
    
    throw apiError; // Rethrow for other types of requests
  }
}

async function callLocalServer(message: string): Promise<AgentResponse> {
  // This will call your Python server when it's ready
  const response = await fetch(`${LOCAL_SERVER_URL}/agent`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message }),
  });
  
  if (!response.ok) {
    throw new Error(`Server responded with status: ${response.status}`);
  }
  
  return await response.json();
}