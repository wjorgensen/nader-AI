/**
 * Actions available to the NaderAI agent
 * This file contains the implementation of actions that can be triggered by the agent
 */

// Define action metadata for documentation and prompt generation
export const actionDefinitions = {
  database_add: {
    description: "Add to database",
    format: {"type": "database_add", "collection": "developers", "data": {}},
    useWhen: "You identify a developer worth tracking or want to store information"
  },
  api_call: {
    description: "Make API call",
    format: {"type": "api_call", "endpoint": "github|twitter|etc", "method": "GET|POST", "params": {}},
    useWhen: "You need external data to answer a question or verify information"
  },
  schedule_followup: {
    description: "Schedule followup",
    format: {"type": "schedule_followup", "recipient": "userId", "message": "...", "delayHours": 48},
    useWhen: "You want to check in with a developer later about their progress"
  },
  connect_developers: {
    description: "Connect developers",
    format: {"type": "connect_developers", "developer1": "userId1", "developer2": "userId2", "reason": "...", "introMessage": "..."},
    useWhen: "You identify two developers who should collaborate based on complementary skills"
  }
};

/**
 * Generates a formatted list of available actions for the system prompt
 * @returns String containing numbered list of actions with descriptions
 */
export function generateActionsList(): string {
  return Object.entries(actionDefinitions)
    .map(([key, action], index) => {
      return `${index + 1}. ${action.description}: 
   ${JSON.stringify(action.format)}
   Use when: ${action.useWhen}`;
    })
    .join("\n\n");
}

/**
 * Adds a developer profile to the database
 * @param data Developer profile data
 * @returns Result of the database operation
 * 
 * Example usage by agent:
 * {
 *   "type": "database_add",
 *   "collection": "developers",
 *   "data": {
 *     "name": "Jane Doe",
 *     "github": "janedoe",
 *     "skills": ["Solidity", "Rust", "ZK proofs"],
 *     "rating": 92,
 *     "notes": "Impressive ZK work, potential for L2 projects"
 *   }
 * }
 */
export async function addToDatabase(actionData: {
  collection: string;
  data: Record<string, any>;
}) {
  try {
    console.log(`Adding to ${actionData.collection} database:`, actionData.data);
    // TODO: Implement actual database connection
    // const db = await connectToDatabase();
    // const result = await db.collection(actionData.collection).insertOne(actionData.data);
    // return { success: true, id: result.insertedId };
    
    return { success: true, id: "mock-id-" + Date.now() };
  } catch (error) {
    console.error("Database add error:", error);
    return { success: false, error: "Failed to add to database" };
  }
}

/**
 * Makes an API call to an external service
 * @param actionData API call parameters
 * @returns Result of the API call
 * 
 * Example usage by agent:
 * {
 *   "type": "api_call",
 *   "endpoint": "github",
 *   "method": "GET",
 *   "params": {
 *     "username": "janedoe",
 *     "repo": "zk-rollup-implementation"
 *   }
 * }
 */
export async function makeApiCall(actionData: {
  endpoint: string;
  method: string;
  params: Record<string, any>;
}) {
  try {
    console.log(`Making API call to ${actionData.endpoint}:`, actionData.params);
    // TODO: Implement actual API call
    // const response = await fetch(`https://api.example.com/${actionData.endpoint}`, {
    //   method: actionData.method,
    //   headers: { 'Content-Type': 'application/json' },
    //   body: actionData.method !== 'GET' ? JSON.stringify(actionData.params) : undefined
    // });
    // return await response.json();
    
    return { success: true, data: { result: "Mock API response for " + actionData.endpoint } };
  } catch (error) {
    console.error("API call error:", error);
    return { success: false, error: "Failed to make API call" };
  }
}

/**
 * Schedules a follow-up message to be sent later
 * @param actionData Schedule data
 * @returns Result of the scheduling operation
 * 
 * Example usage by agent:
 * {
 *   "type": "schedule_followup",
 *   "recipient": "user123",
 *   "message": "Just checking in on your progress with that ZK implementation. Any blockers?",
 *   "delayHours": 48
 * }
 */
export async function scheduleFollowup(actionData: {
  recipient: string;
  message: string;
  delayHours: number;
}) {
  try {
    const scheduledTime = new Date(Date.now() + actionData.delayHours * 60 * 60 * 1000);
    console.log(`Scheduling followup for ${actionData.recipient} at ${scheduledTime}:`, actionData.message);
    // TODO: Implement actual scheduling
    // const scheduler = getScheduler();
    // const jobId = await scheduler.schedule({
    //   recipient: actionData.recipient,
    //   message: actionData.message,
    //   sendAt: scheduledTime
    // });
    // return { success: true, jobId };
    
    return { success: true, jobId: "mock-job-" + Date.now() };
  } catch (error) {
    console.error("Schedule followup error:", error);
    return { success: false, error: "Failed to schedule followup" };
  }
}

/**
 * Connects two developers based on matching skills or interests
 * @param actionData Connection data
 * @returns Result of the connection operation
 * 
 * Example usage by agent:
 * {
 *   "type": "connect_developers",
 *   "developer1": "user123",
 *   "developer2": "user456",
 *   "reason": "Both working on ZK rollups with Rust, potential collaboration opportunity",
 *   "introMessage": "You both are doing amazing work on ZK rollups. I think you should connect."
 * }
 */
export async function connectDevelopers(actionData: {
  developer1: string;
  developer2: string;
  reason: string;
  introMessage: string;
}) {
  try {
    console.log(`Connecting developers ${actionData.developer1} and ${actionData.developer2}:`, actionData.reason);
    // TODO: Implement actual connection mechanism
    // const messaging = getMessagingService();
    // const connectionId = await messaging.createGroupChat([actionData.developer1, actionData.developer2], {
    //   initialMessage: actionData.introMessage
    // });
    // return { success: true, connectionId };
    
    return { success: true, connectionId: "mock-connection-" + Date.now() };
  } catch (error) {
    console.error("Connect developers error:", error);
    return { success: false, error: "Failed to connect developers" };
  }
}

/**
 * Processes all actions returned by the agent
 * @param actions Array of action objects from the agent
 * @returns Results of all processed actions
 */
export async function processActions(actions: any[]): Promise<Array<{type: string, result: any}>> {
  if (!actions || !Array.isArray(actions) || actions.length === 0) {
    return [];
  }

  const results: Array<{type: string, result: any}> = [];
  
  for (const action of actions) {
    let result;
    
    switch (action.type) {
      case 'database_add':
        result = await addToDatabase(action);
        break;
      case 'api_call':
        result = await makeApiCall(action);
        break;
      case 'schedule_followup':
        result = await scheduleFollowup(action);
        break;
      case 'connect_developers':
        result = await connectDevelopers(action);
        break;
      default:
        result = { success: false, error: `Unknown action type: ${action.type}` };
    }
    
    results.push({
      type: action.type,
      result
    });
  }
  
  return results;
}
