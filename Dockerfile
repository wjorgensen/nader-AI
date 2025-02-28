FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only the necessary files for installation first
COPY engine/pyproject.toml engine/uv.lock /app/engine/
COPY engine/__init__.py /app/engine/__init__.py

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -e /app/engine

# Copy the rest of the application
COPY engine/ /app/engine/
COPY .env /app/.env

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["python", "-m", "engine.main"] 