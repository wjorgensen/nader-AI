# Nader AI

## server deployment

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