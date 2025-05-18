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

# Introduction to Dagster

- **Dagster** is an open-source data orchestrator designed for building, running, and observing data pipelines and workflows.

- **Features**:

  1. **Asset-Centric Approach**: Adopts an asset-centric model, where assets are first-class citizens. This allows you to define and track data assets directly, making it easier to manage and monitor the flow of data throughout your pipelines.
  2. **Scalability**: Dagster empowers users to scale their data workflows efficiently as their requirements evolve, making it a versatile choice for growing organizations needing to manage complex ML workflows.
  3. **Developer Productivity**: By focusing on enhancing developer productivity and debugging capabilities, Dagster streamlines the process of orchestrating complex data pipelines.
  4. **Observability and Monitoring**: Dagster provides built-in tools for observability, giving you detailed insights into the execution of your workflows. You can monitor pipeline runs, view logs, and track the status of individual components, ensuring greater transparency and control, especially for model training jobs.
  5. **Modular Architecture**: The highly modular design promotes reusability and flexibility. You can easily create reusable pipeline components, making it simpler to adapt and scale your workflows. While Prefect and Airflow support modular workflows, Dagster’s focus on modularity makes it particularly powerful for complex data engineering tasks.
  6. **Web UI**: It has Dagit, a web-based graphical interface that provides a real-time view of pipeline execution, configuration, and system health.
  7. **Error Handling**:
     - **Dagster** offers built-in support for error handling and retries within the pipeline definition. It provides mechanisms for specifying error boundaries and recovery strategies, enhancing pipeline robustness.
     - **Remark**: **Airflow** also supports **error handling** and retries, but it typically requires users to implement custom error handling logic within their Python code. While this provides flexibility, it may require more effort to implement and maintain.

- **Dagster vs. Airflow**

  1. **Abstraction Level**

     - **Dagster**: focuses on the concept of a **directed acyclic graph** (**DAG**) for defining data pipelines. **Dagster** emphasizes a more structured approach to pipeline development, with a strong emphasis on type safety and explicit dependencies between data assets.
     - **Airflow**, on the other hand, uses Python code to define workflows, giving users more flexibility and control over the execution logic. While it still uses **DAGs** to represent workflows, Airflow's approach is more code-centric.

  2. **Execution Model**:

     - **Dagster** separates the pipeline definition (the DAG) from the execution engine. It provides a unified framework for defining pipelines, managing dependencies, and executing tasks. Dagster also emphasizes data lineage and metadata management.
     - **Airflow** uses a distributed architecture with a scheduler, executor, and worker nodes. It supports parallel execution of tasks across multiple nodes, making it suitable for scaling out workflows. Airflow also provides built-in monitoring and alerting capabilities.

  3. **Error Handling**

     - **Dagster** offers built-in support for error handling and retries within the pipeline definition. It provides mechanisms for specifying error boundaries and recovery strategies, enhancing pipeline robustness.
     - **Airflow** also supports error handling and retries, but it typically requires users to implement custom error handling logic within their Python code. While this provides flexibility, it may require more effort to implement and maintain.

  4. **Community and Ecosystem**
     - **Dagster** is a newer entrant compared to **Airflow**, but it has been gaining traction, especially in organizations looking for a more structured approach to data engineering. It has a growing community and ecosystem of plugins and integrations.
     - **Airflow** has been around for longer and has a larger user base and ecosystem. It has extensive documentation, a rich set of integrations, and a vibrant community contributing plugins and extensions.

# Dagster Components

- **Dagster** has three main components that work together to schedule, execute, and monitor workflows:

  1. **Dagster Core**

     - This is the heart of **Dagster** that allows you to define and execute **DAGs** (**Directed Acyclic Graphs**), but with a more software engineering-friendly approach. Instead of defining tasks and dependencies manually (like in **Airflow**), **Dagster** uses solids (compute units) and graphs (workflow definitions).

  2. **Dagster Webserver** (`dagster-webserver`): This is the **UI** (**Dagit**) that provides:

     - A visualization of pipelines.
     - The ability to trigger runs.
     - Logs and monitoring.
     - Debugging tools.

  3. **Dagster Daemon** (`dagster-daemon`)
     - This is the **background worker** responsible for running schedules and sensors.
     - Unlike **Airflow**, where the **scheduler** is part of the main process, **Dagster** separates it.
     - It polls for scheduled runs and kicks off executions.

- **How they work together**:
  1. You define **pipelines** (**jobs**) in **Dagster**.
  2. The **webserver** (**Dagit**) lets you inspect and trigger jobs.
  3. The **daemon** handles scheduled jobs in the background.

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
