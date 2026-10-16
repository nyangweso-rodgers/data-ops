# Workflow Orchestration Tools

## Table Of Contents

- [Overview](#overview)
- [Comparing Tools](#comparing-tools)
  - [Logging: Airflow vs Dagster](#logging-airflow-vs-dagster)

# Overview

- **Workflow orchestration** is a method of coordinating and managing complex processes across multiple automated tasks and systems. It ensures the logical flow of the tasks, and their efficient and seamless interaction with each other to complete broader business processes.

- **Key Features of Orchestration Tools**:
  1. Automated task scheduling and execution
  2. Error handling and retry capability
  3. Capability to do bulk backfilling
  4. Integration with multiple tools and platforms.
  5. Real-time workflow monitoring and error handling.
  6. Scalable architecture to handle growing business needs.
  7. Unified & central control plane
  8. UI view for managing workflows efficiently.

- Popular orchestration tools include:
  1. Airflow
     - The `01-apache-airflow/` directory contains a custom `Dockerfile` for setting up airflow and a `dags/` directory to create and schedule the tasks.
  2. Prefect
  3. Temporal
  4. Kestra
  5. Windmill
  6. Mage.ai
  7. Dagster
  8. DolphinScheduler
  9. Metaflow
  10. Cadence
  11. Kedro
  12. n8n

# Comparing Tools

## Logging: Airflow vs Dagster

|              | Dagster                                                                                            | Airflow                                                                                                                        |
| ------------ | -------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| **Database** | Event logs (step started/succeeded, materializations) in Postgres `event_logs` - what the UI shows | State only (DAG runs, task instances, XComs) - never log text                                                                  |
| **Files**    | Compute logs (raw stdout/stderr) via `LocalComputeLogManager`                                      | Task logs written by the worker, served by the webserver                                                                       |
| **Remote**   | Compute logs to S3 (and others) via a compute log manager                                          | Task logs to S3, GCS, Azure Blob, CloudWatch or Elasticsearch/OpenSearch when each task finishes; the UI reads them from there |

Both write logs to disk - Dagster just keeps the important run events in its DB. How each is set up here: `airflow/docs/architecture.md#logging`.

# Resources and Further Reading
