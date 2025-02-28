# Nader AI
https://www.naderai.xyz/

## Local Development
We recommend using `uv` with python for local development.  
`~ nader-AI/engine $ uv sync`  
`~ nader-AI/ $ uv run -m engine.main`  
`~ nader-AI/ $ uv run -m engine.packages.telegram`  
`~ nader-AI/ $ uv run -m engine.scripts.seed`  
... etc

## Engine Deployment

`$ docker-compose up -d`

This will build the image and start the container in detached mode.

To stop the server:  
`docker-compose down`


## Environment Variables

The engine requires the following environment variables:

- `MDB_URI`: MongoDB connection URI
- `REDIS_URL`: Redis connection URL
- `TWITTER_USERNAME`: Twitter username
- `TWITTER_PASSWORD`: Twitter password
- `TWITTER_EMAIL`: Twitter email
- `HYPERBOLIC_API_KEY`: Hyperbolic API key
- `GAIA_API_KEY`: Gaia API key
- `TELEGRAM_TOKEN`: Telegram bot token
- `GITHUB_PAT`: Path to the GitHub repository

## Other Requirements

- Docker
- Docker Compose
- MongoDB
    - Ensure that your MongoDB instance is running and accessible
- Redis
- Python
- UV