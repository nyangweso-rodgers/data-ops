# Airflow Architecture

## Table of Contents

- [Logging](#logging)

## Logging

### How Airflow logs

- **Metadata DB** holds state only (DAG runs, task instances, XComs) - never log text. Airflow has no handler that writes logs to a database.
- **Task logs** are written as files by the worker and served by the webserver.
- **Remote logging** ships each task's log to S3, GCS, Azure Blob, CloudWatch or Elasticsearch/OpenSearch when the task finishes; the UI then reads it back from there.
- **Scheduler / DAG-processor logs** are always local files.

### In this repo

- **Dev:** local `logs/`, kept bounded by the hourly `airflow_log_cleanup` DAG - files older than 14 days are deleted, then oldest-first down to 80% of a 1 GB cap (`AIRFLOW_LOG_MAX_SIZE_MB`, `AIRFLOW_LOG_RETENTION_DAYS`). See `dags/maintenance/log_cleanup.py`.
- **Prod:** task logs go to S3 (`AIRFLOW_REMOTE_LOG_FOLDER`, local copies deleted after upload); scheduler logs stay local under the same cleanup DAG (2 GB / 7 days). TODOs in `docker-compose-airflow.prod.yml`.
