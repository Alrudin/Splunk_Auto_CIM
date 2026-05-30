FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if necessary
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .
