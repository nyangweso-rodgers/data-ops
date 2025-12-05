# Dagster

## Table Of Contents

# Project Overview

# Project Structure

- data-ops/
  - workflows/
    - dagster/
      - `dagster_home/`
        - `dagster.yaml` # Configures the Dagster instance (e.g., storage, executors).
        - `workspace.yaml` # Points to the code repository (`dagster_pipeline/`).
        - `.logs_queue/` # Temporary queue files for the `QueuedRunCoordinator` (if you have it enabled).
      - `dagster_pipeline/`
        - `assets/`
          - `etl/`
            - `mysql_to_clickhouse/`
              - `amtdb/`
                - `__init__.py`
                - `accounts/`
                  - `__init__.py`
                  - `v1/`
                    - `accounts_asset.py`
                - `customers/`
                  - `__init__.py`
                  - `v1/`
                    - `customers_asset.py`
            - `postgres_to_clickhouse/`
              - `fma/`
        - `config/`
          - `schemas/`
            - `mysql/`
              - `amtdb/`
                - `accounts/v1/accounts.yml`
            - postgres/
        - `jobs/`
          - `__init__.py`
          - mysql_amtdb_accounts_job.py
        - `resources/`
          - `databases/v1/database.py`
          - `__init__.py`
          - `database.py `# Database connection resources
          - schema_loader.py # Schema configuration loader
        - `utils/`
          - `__init__.py`
          - `clickhouse_utils/`
            - `__init__.py`
            - `v1/`
              - `clickhouse_utils.py`
          - `etl_utils/`
            - `__init__.py`
            - `v1/`
              - `etl_utils.py`
          - `mysql_utils/`
            - `__init__.py`
            - `v1/`
              - `mysql_utils.py`
          - `postgres_utils/`
            - `__init__.py`
            - `v1/`
              - `postgres_utils.py`
        - `definitions.py`
      - `docker-compose-dagster.yml`
      - `Dockerfile`
- Notes:
- dagster/
  - dagster_home/
    - dagster.yaml
    - workspace.yaml
  - dagster_pipeline/
    - assets/
      - etl/
        - mysql_to_clickhouse.py
        - mysql_to_postgres.py
        - postgres_to_clickhouse/py
    - config/
    - resources/
    - utils/
  - Dockerfile
  - docker-compose-dagster.yml

# Setting Up Dagster on Docker

## Requirements

1. `dagster` (gRPC Server)

   - **Purpose**: Executes your pipeline code and handles job runs
   - **Why needed**: This is where your actual data pipelines run
   - **Command**: `dagster api grpc` - serves your pipeline definitions
   - **Remarks**:
     - Communicates with the daemon via the shared `DAGSTER_HOME` storage (e.g., SQLite or Postgres) to see scheduled runs and their status.

2. `dagster_webserver` (Web UI)

   - **Purpose**: Provides the web interface for monitoring, triggering jobs, viewing logs
   - **Why needed**: Without this, you'd have no UI to interact with Dagster
   - **Command**: `dagster-webserver` - serves the web interface on port 3004

3. `dagster_daemon` (Background Services)
   - **Purpose**: Handles **scheduling**, **sensors**, **backfills**, and other background tasks
   - **Why needed**: Without this, scheduled jobs won't run automatically
   - **Command**: `dagster-daemon run` - manages background processes
   - **Remarks**:
     - Add the `dagster-daemon` service to the root `docker-compose.yml`. It needs to share `DAGSTER_HOME` with the `webserver` for coordination and access your pipeline code.

## Step : Setup PostgreSQL DB For Dagster

- Connect to PostgreSQL as superuser

  ```sh
    # If using Docker container
    docker exec -it <postgres_container_name> psql -U postgres
  ```

- Create the database and user

  ```sql
    -- Create the database
    CREATE DATABASE dagster;

    -- Create user with password (if user doesn't exist)
    CREATE USER <user_name> WITH PASSWORD '<password>';

    -- Grant all privileges on the database to the user
    GRANT ALL PRIVILEGES ON DATABASE dagster TO <user_name>;

    -- Connect to the dagster database
    \c dagster

    -- Grant schema privileges
    GRANT ALL ON SCHEMA public TO postgres;
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

    -- Exit
    \q
  ```

## Step : Access Dagit

- Open your browser and go to `http://localhost:3004` or `http://127.0.0.1:3004`
- **Remarks**:

  - Why `127.0.0.1` Works But `localhost` Might Not:

    1.  **DNS Resolution Issues**

        - `localhost` requires **DNS resolution** (looking up the hostname)
        - `127.0.0.1` is a direct IP address (no DNS lookup needed)
        - Your system's DNS might be misconfigured or slow

    2.  **IPv6 vs IPv4 Conflicts**

        - `localhost` might resolve to `IPv6 ::1` instead of `IPv4 127.0.0.1`
        - Docker typically binds to **IPv4** by default
        - Your browser might be trying IPv6 first

    3.  **Hosts File Issues**
        - Your `/etc/hosts` (Linux/Mac) or `C:\Windows\System32\drivers\etc\hosts` (Windows) file might have incorrect entries
        - Should contain: `127.0.0.1 localhost`

# Troubleshooting

- **Check Specific Container Health**
  ```sh
    docker inspect dagster-webserver | grep -A 5 Health
  ```

# Key Concepts

## 1. Asset

- **Why Assets are preferred**:
  1. **Automatic Dependencies**: Dagster tracks what depends on what
  2. **Data Lineage**: Visual graph of the workflow
  3. **Incremental Updates**: Only rebuild what changed
  4. **Self-Documenting**: Clear what each piece produces
  5. **Easy Testing**: Test individaul assets independenly

## 2. Job

- **When to Use Jobs**:
  1. Complex control flow (if/else logic)
  2. Dynamic pipelines (different steps based on daat)
  3. Legacy system integrations
  4. Operational workflows (not data products)

## 3. Resources

- **Resources** in **Dagster** are external services, connections, or tools required by your pipeline to execute, such as databases, cloud storage, APIs, or compute environments. They encapsulate configuration and lifecycle management for these external dependencies.

# Development Workflow

1. Define **Resources** (database connections, APIs, etc.)
2. Create **Assets** (data products you want) OR Ops/Jobs (workflows)
3. Set up Dependencies (assets automatically, jobs manually)
4. Add Schedules/Sensors (when to run)
5. Test in development
6. Deploy to production with different resource configs

## Laoding Data into Memory

## Streaming

- The streaming version is a generator that yields batches instead of accumulating everything in memory before returning. This matters because:
  1.  Memory efficiency - You process one batch at a time, so your memory footprint stays constant regardless of how many rows you're loading.
  2.  Real-time processing - You can start pushing data to ClickHouse as soon as the first batch is ready, rather than waiting for all data to be fetched and concatenated. This is huge for ETL pipelines—reduces end-to-end latency.
  3.  Failure resilience - If something breaks midway, you've already committed batches 1-10 to ClickHouse. With the second approach, you'd have wasted time fetching everything only to fail at the concatenation step.
  4.  Predictable performance - No garbage collection spikes or memory thrashing when dealing with large result sets.

# Persisting `last

# Dagster CLI

- You can run the Dagster CLI commands e.g., `dagster asset materialize ...` from the local terminal (not inside a Dagster Docker container or "Dagster terminal"—Dagster doesn't have a dedicated one). It's designed to be executed from the host machine where your project code lives (e.g., the directory containing `definitions.py`). This works even if Dagster UI (`dagit`) is running in Docker.
- **Setup**

  - Install **Dagster CLI Locally**: If not already, install Dagster in your project env (or globally)
    ```sh
      pip install dagster dagster-webserver dagster-mysql  # Add dagster-postgres if using Postgres
    ```
    - This gives the `dagster` command without needing Docker for CLI.
  - Project Directory: Navigate to your project root (e.g., `/path/to/dagster_pipeline/` where `definitions.py` is).

- How to Run the Command
  - Open local terminal (e.g., VS Code integrated, or bash/cmd), cd to project root, and run:
    ```sh
      dagster asset materialize -a migrate_staging_leads_to_production --config '{"limit": 100, "skip_validation": false}'
    ```

# Resources and Further Reading

1. [docs.dagster.io](https://docs.dagster.io/?_gl=1*1bd3xxt*_ga*Nzc4MzMwNDcxLjE3MTcxNDc3OTM.*_ga_84VRQZG7TV*MTcxNzE0Nzc5My4xLjAuMTcxNzE0Nzc5My42MC4wLjA.*_gcl_au*MTcxOTE5MzIyMS4xNzE3MTQ3Nzk0)
