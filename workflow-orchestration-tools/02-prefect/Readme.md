# Prefect

- **Prefect** offers a **data orchestration** platform to set up, deploy, and manage pipelines at scale. We can build tasks on **Prefect** using Python scripts.
- **Features**
  1. **Cloud-Native Workflows**: **Prefect** is designed to seamlessly integrate with cloud platforms like **AWS** and **Google Cloud**, offering scalability and performance optimization tailored for modern cloud environments, especially for deploying models in production.
  2. **Dynamic Workflow Management**: **Prefect** excels in handling dynamic workflows with changing requirements, providing users with a lightweight yet powerful solution for orchestrating their data processes.
  3. **Powerful API and Programmatic Control**: **Prefect** offers a robust API that lets you programmatically control executions, interact with the scheduler, and manage workflows, providing greater automation and control over your data pipelines.
  4. **Flexible Scheduling**: Prefect allows you to schedule workflows with ease, supporting both time-based schedules and event-driven triggers. This flexibility ensures that your workflows can run exactly when needed, whether on a fixed schedule or in response to specific events.

# Installation

```yml
version: "3.8"

services:
postgres:
  image: postgres:14
  restart: unless-stopped
  volumes:
    - db_data:/var/lib/postgresql/data
  expose:
    - 5432
  environment:
  POSTGRES_PASSWORD: changeme
  POSTGRES_DB: prefect
  healthcheck:
  test: ["CMD-SHELL", "pg_isready -U postgres"]
  interval: 10s
  timeout: 5s
  retries: 5

prefect-server:
  image: prefecthq/prefect:2-latest
  command:
    - prefect
    - server
    - start
  ports:
    - 4200:4200
  depends_on:
  postgres:
    condition: service_started
  volumes:
    - ${PWD}/prefect:/root/.prefect
    - ${PWD}/flows:/flows
  environment:
  PREFECT_API_DATABASE_CONNECTION_URL: postgresql+asyncpg://postgres:changeme@postgres:5432/prefect
  PREFECT_LOGGING_SERVER_LEVEL: INFO
  PREFECT_API_URL: http://localhost:4200/api
volumes:
db_data: null
```
