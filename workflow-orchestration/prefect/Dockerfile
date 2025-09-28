# Use the official Prefect 3 image as base
FROM prefecthq/prefect:3-latest

# Set working directory
WORKDIR /app

# Install system dependencies (if needed, e.g., for compiling packages)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \ 
    && rm -rf /var/lib/apt/lists/*

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Optional: Copy custom scripts or configs
# COPY ./my_scripts /app/my_scripts

# Copy flows directory into the image
COPY flows/ /app/flows/
COPY tasks /app/tasks/
COPY deployments /app/deployments/

# Set environment variables (optional, can override in docker-compose.yml)
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app