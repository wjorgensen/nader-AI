# Nader AI

Nader AI is a closed network of the most savage builders in web3, and you don't get in by updating your LinkedIn. This is the talent hub you've never heard of—and won't, unless one of our nodes decides you're worth bringing into the fold. No resume spam, no recruiter cold calls, just pure, validated technical excellence connecting with opportunities that actually matter.

#### [naderai.xyz](https://naderai.xyz)

#### [DEMO VIDEO](https://www.loom.com/share/89a06f61d3cc4cffa0bfe517a6abfc87?sid=2e40f199-fc00-4107-bfd5-02c0cfc990af)


## What This Actually Does

This agent hunts for real talent in a sea of mediocrity. We've built a system that crawls GitHub commits, Twitter threads, and obscure hacker forums to identify devs who are shipping actual innovation—not just forking Uniswap V2 and calling it groundbreaking.

## The Vetting Engine

Our engine doesn't care about your resume or where you worked. It analyzes:

- Your commit history: Are you shipping meaningful code or just making cosmetic changes?
- Technical depth: Can you explain ZK rollups without mentioning "magic"?
- Build history: Have you deployed anything that wasn't abandoned after the seed round dried up?
- Network validation: Do other elite builders vouch for your work, or are you just collecting GitHub stars from bots?
- Knowledge graph: We map how your technical knowledge connects to what's actually pushing web3 forward
- Bullshit detector: Our agent can smell when you're pretending to understand consensus mechanisms or just parroting Bankless episodes

The elite builder network operates on pure technical merit. No LinkedIn endorsements, no hackathon participation trophies, no blue checkmarks necessary. If you're in the top 0.01%, our algorithms will find you before you've even updated your "open to work" status.

For companies: Skip the recruitment theater and access pre-vetted, technically validated builders who can actually ship. No more wasting six figures on recruiters who can't tell Solidity from JavaScript.

For devs: Get connected to projects worth your time, not glorified SQL databases cosplaying as "decentralized" tech. No more wasting months building something that's going to rug its users at the first sign of a bear market.

## Architecture
The app is split into two main parts, the company/project side and the developer side.  

The company side is a web app that allows entities looking for talent to post an opportunity by giving Nader-AI some spare change.

The developer side is a distributed systemsy engine that runs multiple workers and services to create a network of developers, and get to know them better.  
Most of the data is stored in unstructured NoSQL format in MongoDB. There is a caching layer to reduce load on Twitter workers. All context and information about a potential candidate or company is stored in our database and used as context when necessary. 

There are many phases that are processed by the orchestrator service and simultaneously processed as messages come in.

some phases: `"reffered", "welcome", "seeded", "gather", "testing", "ready", "job_match", "evaluated"`

These phases are determined by Nader AI as it talks to the user and gains more information and context about them.

as these phases progress different workers spawn that collect more info, help the agent make decisions, and grow the network.  

some workers: `twitter: expand network, twitter: scrape user tweets, github: scrape user repos, github: determine user project proficiecy, telegram: request information`

The engine is built to be modular and scalable, with the ability to add more workers and services as needed. 

We hope to continue to add more workers and services to give nader-ai better context on users, and it's network.


## Referral Network 

Think you can just waltz in here? Nah. This isn't some Web2 LinkedIn circle where everyone's a "blockchain expert". You need a referral from someone already in the network—and they're putting their reputation (and crypto) on the line for you. Every successful referral that makes it through our vetting pays out in ETH to whoever vouched for them. But here's the catch: if you refer someone who's all cap and no ship, you're taking a rep hit. No pressure. Quality over quantity, always. Real recognizes real, and in this game, your network is your net worth.

## Get Connected

- Builders: Hit up @nader_ai_agent_bot on Telegram
- Projects: Submit job requests at naderai.xyz

## Decentralized AI Inference

We run our AI on Hyperbolic and Gaia because centralized inference is for NPCs—our validators stake real value and can't be censored. Our talent identification engine stays based by distributing compute across specialized hardware nodes that actually get paid to maintain quality, because if you're not decentralized, you're just running a fancy SQL database.

## Local Development
We recommend using `uv` with python for local development.  
`~ nader-AI/engine $ uv sync`  
`~ nader-AI/ $ uv run -m engine.main`  
`~ nader-AI/ $ uv run -m engine.packages.telegram`  
`~ nader-AI/ $ uv run -m engine.scripts.seed`  
... etc

## Technical Setup

`$ docker-compose up -d`

This will build the image and start the container in detached mode.

To stop the server:  
`docker-compose down`


### Environment Variables

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
