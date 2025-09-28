# Prefect

## Table Of Contents

#

# Setup

# Requirements

- Multi-server deployments require:
  1.  PostgreSQL database version 14.9 or higher (SQLite does not support multi-server synchronization)
  2.  Redis for event messaging
  3.  Load balancer for API traffic distribution

# Folder Structure

- prefect/
  - deployments/
    - deploy.py
  - flows/
    - test_flow.py
  - tasks/
  - docker-compose-prefect.yml
  - Dickerfile
  - Readme.md

# Services

## `prefect-server`

## `prefect-services`

## `prefect-worker`

# Setup Steps

- **Step 1** : **Create PostgreSQL DB**

  - Connect to Postgres Docker Container:
    ```sh
      docker exec -it postgres psql -U <username>
    ```
  - List existing databases:
    ```sh
      \l
    ```
  - Create Database:
    ```sh
      CREATE DATABASE prefect;
    ```

- Access the UI:
  - Open http://localhost:4200

# Flows

- Deploy Flows
  1. Option 1: Using Docker
     - Using
       ```sh
        docker exec -it prefect-server python /app/deployments/deploy.py
       ```
  2. Option 2:

# Resources and Further Reading

1. [docs.prefect.io - get-started](https://docs.prefect.io/v3/get-started)
