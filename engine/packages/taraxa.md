# Telegram Data Processing for NaderAI

This directory contains examples for processing Telegram data to enhance the NaderAI agent's understanding of crypto conversations.

## Overview

The Taraxa processor is designed to analyze Telegram message data from crypto communities and extract insights that can be used to make the NaderAI agent more authentic in its interactions. By processing real Telegram conversations, the agent can:

1. Learn popular crypto terms and topics
2. Understand common crypto slang and expressions
3. Adopt natural conversation patterns from Telegram
4. Gain insights into engagement metrics and activity patterns

## CSV Data Format

The Telegram data should be provided in a CSV file with the following columns:

```
chat_id,id,date,user_id,sender_type,text,member_online_count,views,replies,forwards,reply_to_id
```

Where:
- `chat_id`: Identifier for the Telegram chat/group
- `id`: Message identifier
- `date`: Timestamp of the message
- `user_id`: Identifier for the message sender
- `sender_type`: Type of sender (user, bot, etc.)
- `text`: The actual message content
- `member_online_count`: Number of members online when the message was sent
- `views`: Number of views for the message
- `replies`: Number of replies to the message
- `forwards`: Number of times the message was forwarded
- `reply_to_id`: Identifier of the message being replied to (if applicable)

## Usage

### Processing Telegram Data

You can process Telegram data using the provided example script:

```bash
python examples/process_telegram_data.py --csv path/to/telegram_data.csv
```

### Options

- `--csv`: Path to the Telegram CSV file (required)
- `--network`: AI network to use (HYPERBOLIC, GAIA, or ORA, default: HYPERBOLIC)
- `--test`: Test the agent with a sample query after processing
- `--test-query`: Custom test query to send to the agent (default: "Tell me about the latest crypto trends")

### Example

```bash
# Process data and test the agent
python examples/process_telegram_data.py --csv data/telegram_crypto_messages.csv --test

# Process data with a custom test query
python examples/process_telegram_data.py --csv data/telegram_crypto_messages.csv --test --test-query "What's your take on ZK rollups?"

# Use a different AI network
python examples/process_telegram_data.py --csv data/telegram_crypto_messages.csv --network GAIA
```

## How It Works

1. The Taraxa processor reads the CSV file and extracts various insights:
   - Popular crypto terms and topics
   - Common slang and expressions
   - Conversation patterns and engagement metrics
   - Activity patterns (e.g., hourly activity)

2. These insights are stored in MongoDB for future reference.

3. The agent's character is enhanced with the extracted insights:
   - Popular crypto terms are added to the agent's topics
   - Common slang is incorporated into the agent's communication style

4. When the agent responds to queries, it uses these insights to make its responses more authentic and aligned with crypto Telegram culture.

## Integration with NaderAI

The Taraxa processor is integrated with the NaderAI agent through the `AI` class in `engine/agent/index.py`. The agent automatically incorporates Telegram insights into its system prompt when responding to queries.

## Programmatic Usage

You can also use the Taraxa processor programmatically in your own code:

```python
from engine.packages.taraxa import TaraxaProcessor
from engine.agent.index import AI

# Process Telegram data
processor = TaraxaProcessor()
result = processor.process_csv("path/to/telegram_data.csv")

# Enhance the agent's character
processor.enhance_character("engine/agent/character/character.json")

# Use the enhanced agent
agent = AI()
response = await agent.act("Tell me about ZK proofs")
``` 