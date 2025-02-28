# Nader AI

## Project Overview


## System Architecture

## Development Workflow

Local development is facilitated using `uv` for Python package management:
```
~ nader-AI/engine $ uv sync
~ nader-AI/ $ uv run -m engine.main
~ nader-AI/ $ uv run -m engine.packages.telegram
~ nader-AI/ $ uv run -m engine.scripts.seed
```

For deployment, Docker Compose is used:
```
$ docker-compose up -d
```

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

## Folder Structure

```
nader-AI/
├── .env
├── .gitignore
├── .dockerignore
├── docker-compose.yml
├── Dockerfile
├── README.md
│
├── client/
│   ├── api/
│   ├── package.json
│   ├── next.config.ts
│   ├── tsconfig.json
│   ├── public/
│   └── src/
│       ├── pages/
│       │   ├── api/
│       │   ├── components/
│       │   ├── index.tsx
│       │   ├── _app.tsx
│       │   └── _document.tsx
│       └── styles/
│
└── engine/
    ├── main.py
    ├── pyproject.toml
    ├── uv.lock
    ├── __init__.py
    ├── .python-version
    │
    ├── agent/
    │   ├── __init__.py
    │   ├── index.py
    │   └── character/
    │
    ├── orchestrator/
    │   ├── __init__.py
    │   └── orchestrator.py
    │
    ├── server/
    │   ├── __init__.py
    │   ├── main.py
    │   └── models/
    │
    ├── packages/
    │   ├── mongo.py
    │   ├── red.py
    │   ├── log.py
    │   ├── telegram.py
    │   ├── github.py
    │   └── worker.py
    │
    ├── scripts/
    │
    └── logs/
```