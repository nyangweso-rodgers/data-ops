# Dagster

## Table Of Contents

# Project Overview

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

# Resources and Further Reading

1. [Dagster Documentation](https://docs.dagster.io/?_gl=1*1bd3xxt*_ga*Nzc4MzMwNDcxLjE3MTcxNDc3OTM.*_ga_84VRQZG7TV*MTcxNzE0Nzc5My4xLjAuMTcxNzE0Nzc5My42MC4wLjA.*_gcl_au*MTcxOTE5MzIyMS4xNzE3MTQ3Nzk0)
