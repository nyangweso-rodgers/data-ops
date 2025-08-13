# Use an official Python runtime
FROM python:3.11-slim

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY server.py requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Command to run the MCP server
CMD ["python", "server.py"]