
definitions = {
    "seed": {
        "description": "starts a connection with a user",
        "format": {
            "type": "seed",
            "data": {
                "x_username": "x_username",
                "name": "name",
            },
        },
        "usecase": "starting a new conversation & connection with a user",
    },
}


def generate_actions_list():
    """
    Generates a formatted list of available actions for the system prompt
    
    Returns:
        str: Formatted list of actions with descriptions and use cases
    """
    acts = []
    for i, (key, action) in enumerate(definitions.items(), 1):
        acts.append(
            f"{i}. {key}: {action['description']} - {action['usecase']}"
        )
    return "\n\n".join(acts)