# Dagster

## Table Of Contents

# Project Overview

# Project Structure

- `02-dagster/`

  - `dagster-home/`
    - `dagster.yaml` # Configures the Dagster instance (e.g., storage, executors).
    - `workspace.yaml` # Points to the code repository (dagster-pipeline/).
  - `dagster-pipeline/`
    - `assets/`
      - `__init__.py` # Exports assets for Dagster to load.
      - `customers_sync.py` # Defines the customers asset for syncing the customers table.
    - `config/`
      - `local.yaml` # Defines resources and pipeline configs (with pipeline_configs needing mapping to assets).
      - `prod.yaml` # For production settings
    - `jobs/`
      - `__init__.py` # Exports jobs
      - `customers_sync_job.py` # Defines the sc_amt_replica_to_reporting_service Job.
    - `resources/`
      - `__init__.py` # Dynamically creates resources from config/local.yaml.
      - `clickhouse.py` # ClickHouse syncs.
      - `mysql.py` # Implements MySQLResource (using mysql.connector, with pooling and incremental sync support).
      - `postgres.py` # Implements PostgresResource (robust, with pooling and bulk inserts).
  - `docker-compose-dagster.yml`
  - `Dockerfile`
  - `Readme.md`

- Breakdown of directories in `dagster_home/`

  1. `.logs_queue/`

     - Temporary queue files for the `QueuedRunCoordinator` (if you had it enabled).

  2. `nux/`

     - "New User Experience" data.
     - Stores metadata Dagster uses to know if you’ve already seen the getting-started tips / intro flows in the UI.
     - Harmless, safe to delete, Dagster will recreate if needed.

  3. `.telemetry/`

     - Stores telemetry events (anonymous usage statistics Dagster sends to Elementl by default).
     - If you disable telemetry (`telemetry: enabled: false`), this directory will stop being populated.

  4. `history/`

     - Keeps a record of CLI command history and some instance event history.
     - Similar to a “shell history” file.
     - Can be deleted, but you’ll lose local history references.

  5. `logs/`

     - Compute logs from pipeline/asset runs (stdout/stderr per step).
     - This is where your tasks’ print/log output goes if you use the `LocalComputeLogManager`.
     - Very useful for debugging.
     - Safe to delete, but you’ll lose run logs in Dagit UI for past runs.

  6. `schedules/`

     - Local storage for schedule definitions and ticks when you’re not using Postgres-backed schedule storage.
     - If you switch to Postgres schedule storage, this becomes unused.
     - Safe to delte after switching

  7. `storage/`
     - Default metadata storage when Postgres is not configured (includes run storage, event logs, schedules, etc. as SQLite files).
     - With Postgres configured, Dagster won’t use this anymore.
     - Safe to delete once you’re sure everything is migrated.

# Setting Up Dagster on Docker

## Step 1: Setup Dagster Webserver(`dagster`)

- Serves the Dagit UI and GraphQL API.
- Executes pipelines manually or when triggered externally.
- Communicates with the daemon via the shared `DAGSTER_HOME` storage (e.g., SQLite or Postgres) to see scheduled runs and their status.

## Step 2: Setup Dagster Daemon (`dagster-daemon`)

- **Dagster Daemon** is a seperate process that manages:
  - **Schedules**: Runs jobs at specified intervals (e.g., hourly).
  - **Sensors**: Triggers runs based on external events (e.g., new data in Postgres).
  - **Run Queue**: Coordinates execution if you have multiple runs or concurrency limits.
- Add the `dagster-daemon` service to the root `docker-compose.yml`. It needs to share `DAGSTER_HOME` with the `webserver` for coordination and access your pipeline code.
- **Note**:
  - Set `entrypoint: ["dagster-daemon", "run"]` to start the daemon process instead of the webserver.
  - Shared the same `DAGSTER_HOME` volume so both services use the same storage (e.g., run history, schedules).
  - No ports exposed— the daemon doesn’t need a public interface; it communicates internally with the webserver.

## Step 3: Setup Dagster Daemon

## Step : Access Dagit

- Open your browser and go to `http://localhost:3004` or `http://127.0.0.1:3004`
- You should see the **Dagit** interface. Look under the **“Definitions”** or **“Assets”** tab for:
  - The `postgres_to_clickhouse` job.
  - The `postgres_data` and `clickhouse_table` assets.
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

# Resources and Further Reading

1. [Dagster Documentation](https://docs.dagster.io/?_gl=1*1bd3xxt*_ga*Nzc4MzMwNDcxLjE3MTcxNDc3OTM.*_ga_84VRQZG7TV*MTcxNzE0Nzc5My4xLjAuMTcxNzE0Nzc5My42MC4wLjA.*_gcl_au*MTcxOTE5MzIyMS4xNzE3MTQ3Nzk0)
