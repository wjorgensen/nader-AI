"""
Actions available to the NaderAI agent
This file contains the implementation of actions that can be triggered by the agent
"""

import json
from datetime import datetime, timedelta

# Define action metadata for documentation and prompt generation
action_definitions = {
    "database_add": {
        "description": "Add to database",
        "format": {"type": "database_add", "collection": "developers", "data": {}},
        "useWhen": "You identify a developer worth tracking or want to store information"
    },
    "api_call": {
        "description": "Make API call",
        "format": {"type": "api_call", "endpoint": "github|twitter|etc", "method": "GET|POST", "params": {}},
        "useWhen": "You need external data to answer a question or verify information"
    },
    "schedule_followup": {
        "description": "Schedule followup",
        "format": {"type": "schedule_followup", "recipient": "userId", "message": "...", "delayHours": 48},
        "useWhen": "You want to check in with a developer later about their progress"
    },
    "connect_developers": {
        "description": "Connect developers",
        "format": {"type": "connect_developers", "developer1": "userId1", "developer2": "userId2", "reason": "...", "introMessage": "..."},
        "useWhen": "You identify two developers who should collaborate based on complementary skills"
    }
}


def generate_actions_list():
    """
    Generates a formatted list of available actions for the system prompt
    :return: String containing numbered list of actions with descriptions
    """
    actions_list = []
    for i, (key, action) in enumerate(action_definitions.items(), 1):
        actions_list.append(
            f"{i}. {action['description']}: \n"
            f"   {json.dumps(action['format'])}\n"
            f"   Use when: {action['useWhen']}"
        )
    return "\n\n".join(actions_list)


async def add_to_database(action_data):
    """
    Adds a developer profile to the database
    :param action_data: Developer profile data
    :return: Result of the database operation
    
    Example usage by agent:
    {
      "type": "database_add",
      "collection": "developers",
      "data": {
        "name": "Jane Doe",
        "github": "janedoe",
        "skills": ["Solidity", "Rust", "ZK proofs"],
        "rating": 92,
        "notes": "Impressive ZK work, potential for L2 projects"
      }
    }
    """
    try:
        print(f"Adding to {action_data['collection']} database:", action_data['data'])
        # TODO: Implement actual database connection
        # db = await connect_to_database()
        # result = await db.collection(action_data['collection']).insert_one(action_data['data'])
        # return {"success": True, "id": str(result.inserted_id)}
        
        return {"success": True, "id": f"mock-id-{int(datetime.now().timestamp())}"}
    except Exception as error:
        print("Database add error:", error)
        return {"success": False, "error": "Failed to add to database"}


async def make_api_call(action_data):
    """
    Makes an API call to an external service
    :param action_data: API call parameters
    :return: Result of the API call
    
    Example usage by agent:
    {
      "type": "api_call",
      "endpoint": "github",
      "method": "GET",
      "params": {
        "username": "janedoe",
        "repo": "zk-rollup-implementation"
      }
    }
    """
    try:
        print(f"Making API call to {action_data['endpoint']}:", action_data['params'])
        # TODO: Implement actual API call
        # import aiohttp
        # async with aiohttp.ClientSession() as session:
        #     if action_data['method'] == 'GET':
        #         async with session.get(f"https://api.example.com/{action_data['endpoint']}", 
        #                               params=action_data['params']) as response:
        #             return await response.json()
        #     else:
        #         async with session.post(f"https://api.example.com/{action_data['endpoint']}", 
        #                               json=action_data['params']) as response:
        #             return await response.json()
        
        return {"success": True, "data": {"result": f"Mock API response for {action_data['endpoint']}"}}
    except Exception as error:
        print("API call error:", error)
        return {"success": False, "error": "Failed to make API call"}


async def schedule_followup(action_data):
    """
    Schedules a follow-up message to be sent later
    :param action_data: Schedule data
    :return: Result of the scheduling operation
    
    Example usage by agent:
    {
      "type": "schedule_followup",
      "recipient": "user123",
      "message": "Just checking in on your progress with that ZK implementation. Any blockers?",
      "delayHours": 48
    }
    """
    try:
        scheduled_time = datetime.now() + timedelta(hours=action_data['delayHours'])
        print(f"Scheduling followup for {action_data['recipient']} at {scheduled_time}:", action_data['message'])
        # TODO: Implement actual scheduling
        # scheduler = get_scheduler()
        # job_id = await scheduler.schedule({
        #     "recipient": action_data['recipient'],
        #     "message": action_data['message'],
        #     "send_at": scheduled_time
        # })
        # return {"success": True, "jobId": job_id}
        
        return {"success": True, "jobId": f"mock-job-{int(datetime.now().timestamp())}"}
    except Exception as error:
        print("Schedule followup error:", error)
        return {"success": False, "error": "Failed to schedule followup"}


async def connect_developers(action_data):
    """
    Connects two developers based on matching skills or interests
    :param action_data: Connection data
    :return: Result of the connection operation
    
    Example usage by agent:
    {
      "type": "connect_developers",
      "developer1": "user123",
      "developer2": "user456",
      "reason": "Both working on ZK rollups with Rust, potential collaboration opportunity",
      "introMessage": "You both are doing amazing work on ZK rollups. I think you should connect."
    }
    """
    try:
        print(f"Connecting developers {action_data['developer1']} and {action_data['developer2']}:", action_data['reason'])
        # TODO: Implement actual connection mechanism
        # messaging = get_messaging_service()
        # connection_id = await messaging.create_group_chat(
        #     [action_data['developer1'], action_data['developer2']], 
        #     initial_message=action_data['introMessage']
        # )
        # return {"success": True, "connectionId": connection_id}
        
        return {"success": True, "connectionId": f"mock-connection-{int(datetime.now().timestamp())}"}
    except Exception as error:
        print("Connect developers error:", error)
        return {"success": False, "error": "Failed to connect developers"}


async def process_actions(actions):
    """
    Processes all actions returned by the agent
    :param actions: Array of action objects from the agent
    :return: Results of all processed actions
    """
    if not actions or not isinstance(actions, list) or len(actions) == 0:
        return []

    results = []
    
    for action in actions:
        result = None
        
        if action['type'] == 'database_add':
            result = await add_to_database(action)
        elif action['type'] == 'api_call':
            result = await make_api_call(action)
        elif action['type'] == 'schedule_followup':
            result = await schedule_followup(action)
        elif action['type'] == 'connect_developers':
            result = await connect_developers(action)
        else:
            result = {"success": False, "error": f"Unknown action type: {action['type']}"}
        
        results.append({
            "type": action['type'],
            "result": result
        })
    
    return results 