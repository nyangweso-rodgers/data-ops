# n8n (nodemation)

# About n8n

- **n8n** (pronounced "n-eight-n", short for "nodemation") is a workflow automation platform that combines visual building with custom code. It's designed for technical teams who want the speed of no-code tools but need the flexibility to write actual code when required.

- **Common Use Cases**:
  1. Data Pipeline Automation
     - Trigger workflows from Dagster/Airflow
     - Process data from PostgreSQL/MySQL
     - Push results to Elasticsearch
  2. Notification Systems
     - Send alerts to Slack/Email
     - Monitor service health
     - Alert on pipeline failures
  3. API Integration
     - Connect external APIs
     - Transform and route data
     - Sync between systems
  4. AI Workflows
     - Use LangChain nodes
     - Connect to Ollama/OpenAI
     - Build AI agents

- **Available Integrations (400+)**
  1. Databases
     - PostgreSQL ✓ (already configured)
     - MySQL ✓ (available in monorepo)
     - Redis ✓ (available in monorepo)
     - Elasticsearch ✓ (available in monorepo)
  2. Workflow Tools
     - Slack
     - Email (SMTP)
     - Webhooks
     - HTTP Request
  3. Cloud Services
     - AWS (S3, Lambda, SQL)
     - Google Cloud
     - Azure
  4. Development
     - GitHub
     - Docker
     - SSH

# Prerequisites

- Docker installed on your system
- Docker Compose installed
- Port 5678 available (or change it in docker-compose.yml)

# Setup

- Important: Generate secure values:

  ```sh
    # Encryption key
    openssl rand -hex 32

    # Secure password
    openssl rand -base64 32
  ```

- Create Docker Volume

  ```sh
    docker volume create n8n-data
  ```

- Initialize Database: From monorepo root:

  ```sh
    mae postgres-up
    make n8n-init-db
  ```

- Start n8n
  ```sh
   make n8n-up-build
  ```

# Accessing n8n

- Web Interface: http://localhost:5678
- API: http://localhost:5678/api/v1/
- Webhooks: http://localhost:5678/webhook/ or http://localhost:5678/webhook-test/

# Troubleshooting

- Container won't start

  ```sh
    make logs
    # Check database connection
    docker exec -it postgres psql -U postgres -c "\l"
  ```

- Database connection issues

  ```sh
    # Verify postgres is running
    docker ps | grep postgres

    # Check network
    docker network inspect data-ops-network

    # Test connection
    docker exec -it n8n ping postgres
  ```

- Port conflicts

  ```sh
    # Check what's using port 5678
    lsof -i :5678

    # Or change port in docker-compose-n8n.yml
    ports:
    - "5679:5678"
  ```

# Resources

1. Official Docs: https://docs.n8n.io/
2. Community Forum: https://community.n8n.io/
3. GitHub: https://github.com/n8n-io/n8n
4. Workflow Templates: https://n8n.io/workflows/
