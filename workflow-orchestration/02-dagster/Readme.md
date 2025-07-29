# Dagster

## Table Of Contents

# Project Overview

- Build a fullly operational dagster pipeline to:

  1. Move data from PostgreSQL Database to ClickHouse Server

- Setup:

  - Define **Services**: `dagster`, `dagster-daemon`, and `dagster-webserver`
  - Define a **pipeline**: `etl-pipeline.py` is pulling from **Postgres** and appending to **ClickHouse**.

- Design Plan:

  1. Postgres

     - Use `created_at` to identify new records.
     - Use `updated_at` to detect changes to existing records.

  2. ClickHouse

     - Switch to a `ReplacingMergeTree` table engine (replaces old rows by id on merge).
     - Track the last run’s timestamp to filter incremental data.

  3. Dagster
     - Store the last run’s timestamp in Dagster’s instance (persistent storage).
     - Split logic into **assets**: initial load, new records, and updates.

# Setting Up Dagster

## 1. Prerequisites

- Ensure you have the following:
  1. Python (version 3.7 or later)
  2. Pip (Python package manager)

## 2. Installation

- **Step 2.1**: **Installation**: Start by installing **Dagster** and the `dagster-docker` package. This can be done via pip:

  ```sh
      pip install dagster dagster-docker
  ```

- **Step 2.2**: **Configuration**: Configure `Dockerfile` to include both **Dagster** and your pipelines.

  - An example `Dockerfile` might look like this:

    ```Dockerfile
      FROM python:3.8-slim

      RUN pip install dagster dagster-docker

      COPY . /my_dagster_workspace
      WORKDIR /my_dagster_workspace

      CMD ["dagster", "api", "grpc", "--python-file", "my_pipeline.py", "--host", "0.0.0.0"]
    ```

- **Step 2.3**: **Running Dagster Pipelines**: With your Docker container set up, you can run your pipelines using the dagster CLI or programmatically via scripts. Containers ensure that your pipeline's environment is reproducible, making it easier to manage dependencies and test changes.

- Install Dagster and Dagit (Dagster’s web-based UI) using pip:
  ```sh
    pip install dagster dagit
  ```
- Using `docker-compose.yml` File

  ```yml
  version: "3.7"

  services:
  docker_example_postgresql:
    image: postgres:11
    container_name: docker_example_postgresql
    environment:
    POSTGRES_USER: "postgres_user"
    POSTGRES_PASSWORD: "postgres_password"
    POSTGRES_DB: "postgres_db"
    networks:
      - docker_example_network
    healthcheck:
    test: ["CMD-SHELL", "pg_isready -U postgres_user -d postgres_db"]
    interval: 10s
    timeout: 8s
    retries: 5

  docker_example_user_code:
    build:
    context: .
    dockerfile: ./Dockerfile_user_code
    container_name: docker_example_user_code
    image: docker_example_user_code_image
    restart: always
    environment:
    DAGSTER_POSTGRES_USER: "postgres_user"
    DAGSTER_POSTGRES_PASSWORD: "postgres_password"
    DAGSTER_POSTGRES_DB: "postgres_db"
    DAGSTER_CURRENT_IMAGE: "docker_example_user_code_image"
    networks:
      - docker_example_network

  docker_example_webserver:
    build:
    context: .
    dockerfile: ./Dockerfile_dagster
    entrypoint:
      - dagster-webserver
      - -h
      - "0.0.0.0"
      - -p
      - "3000"
      - -w
      - workspace.yaml
    container_name: docker_example_webserver
    expose:
      - "3000"
    ports:
      - "3000:3000"
    environment:
    DAGSTER_POSTGRES_USER: "postgres_user"
    DAGSTER_POSTGRES_PASSWORD: "postgres_password"
    DAGSTER_POSTGRES_DB: "postgres_db"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /tmp/io_manager_storage:/tmp/io_manager_storage
    networks:
      - docker_example_network
    depends_on:
    docker_example_postgresql:
      condition: service_healthy
    docker_example_user_code:
      condition: service_started

  docker_example_daemon:
    build:
    context: .
    dockerfile: ./Dockerfile_dagster
    entrypoint:
      - dagster-daemon
      - run
    container_name: docker_example_daemon
    restart: on-failure
    environment:
    DAGSTER_POSTGRES_USER: "postgres_user"
    DAGSTER_POSTGRES_PASSWORD: "postgres_password"
    DAGSTER_POSTGRES_DB: "postgres_db"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /tmp/io_manager_storage:/tmp/io_manager_storage
    networks:
      - docker_example_network
    depends_on:
    docker_example_postgresql:
      condition: service_healthy
    docker_example_user_code:
      condition: service_started

  networks:
  docker_example_network:
    driver: bridge
    name: docker_example_network
  ```

- **Step** : **Setup Dagster Webserver** (`dagster`)

  - Serves the Dagit UI and GraphQL API.
  - Executes pipelines manually or when triggered externally.
  - Communicates with the daemon via the shared `DAGSTER_HOME` storage (e.g., SQLite or Postgres) to see scheduled runs and their status.

- **Step** : **Setup Dagster Daemon** (`dagster-daemon`)

  - **Dagster Daemon** is a seperate process that manages:
    - **Schedules**: Runs jobs at specified intervals (e.g., hourly).
    - **Sensors**: Triggers runs based on external events (e.g., new data in Postgres).
    - **Run Queue**: Coordinates execution if you have multiple runs or concurrency limits.
  - Add the `dagster-daemon` service to the root `docker-compose.yml`. It needs to share `DAGSTER_HOME` with the `webserver` for coordination and access your pipeline code.
    ```yml
    dagster-daemon:
      build:
        context: ./workflow-orchestration-tools/02-dagster/dagster-pipeline
        dockerfile: Dockerfile
      image: dagster
      container_name: dagster-daemon
      entrypoint: ["dagster-daemon", "run"]
      depends_on:
        - postgres-db
        - clickhouse-server
        - dagster
      environment:
        - DAGSTER_HOME=/app/dagster_home
      volumes:
        - ./workflow-orchestration-tools/02-dagster/dagster-home:/app/dagster_home
      networks:
        - data-ops-network
    ```
  - Where:
    - Set `entrypoint: ["dagster-daemon", "run"]` to start the daemon process instead of the webserver.
    - Shared the same `DAGSTER_HOME` volume so both services use the same storage (e.g., run history, schedules).
    - No ports exposed— the daemon doesn’t need a public interface; it communicates internally with the webserver.

- **Step** : **Access Dagit**

  - Open your browser and go to `http://localhost:3004` or `http://127.0.0.1:3004`
  - You should see the **Dagit** interface. Look under the **“Definitions”** or **“Assets”** tab for:
    - The `postgres_to_clickhouse` job.
    - The `postgres_data` and `clickhouse_table` assets.

- **Step** : **Run Your Pipeline**
  - Before running, confirm your tables are set up in `clickhouse-server`
  - Example:
    - Run this via **Tabix** (http://localhost:8090) or a **ClickHouse client**:
      ```sql
        CREATE TABLE customers (
          id Int32,
          created_by String,
          updated_by String,
          created_at DateTime,
          updated_at DateTime
      ) ENGINE = MergeTree()
      ORDER BY (created_at);
      ```

# Resources and Further Reading

1. [Dagster Documentation](https://docs.dagster.io/?_gl=1*1bd3xxt*_ga*Nzc4MzMwNDcxLjE3MTcxNDc3OTM.*_ga_84VRQZG7TV*MTcxNzE0Nzc5My4xLjAuMTcxNzE0Nzc5My42MC4wLjA.*_gcl_au*MTcxOTE5MzIyMS4xNzE3MTQ3Nzk0)
