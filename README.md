# Data Ops

## Table Of Contents

# Project Overview

- This is a comprehensive **data operations** (**DataOps**) platform that includes (**Architecture Components**):
  1.  **Databases**: PostgreSQL, MySQL, MongoDB, Redis
  2.  **APIs**: Express.js APIs for different databases
  3.  **Messaging**: Apache Kafka with Zookeeper, Schema Registry, Kafka Connect, Debezium
  4.  **Data Warehouse**: ClickHouse
  5.  **Orchestration**: Apache Airflow, Dagster, Prefect
  6.  **Data Pipelines**: NiFi, Spark, Airbyte, PeerDB, dbt
  7.  **Dashboards**: Grafana, Superset, Redash, Metabase, Streamlit, Taipy
  8.  **Monitoring**: Prometheus, Loki
  9.  **ML/AI**: MLflow, OCR pipeline, Open WebUI with Ollama
  10. **Metadata**: Open Metadata
  11. **Web Portals**: Next.js application with Prisma
  12. **Documentation**: Docusaurus site

# Prerequisites

- Before diving into the project, ensure you have the following prerequisites:
  1. Docker — Docker Compose
  2. Apache Kafka (Stream Processing)
  3. PostgreSQL
  4. Superset(Report/Dashboard)
  5. Kafka UI ( Kafka Monitoring)
  6. Grafana (System Monitoring)

# Project Structure

- data-ops/
  - `docker-compose.yml` # Root compose (orchestrates all services)
  - databases/
    - postgres/
      - `docker-compose-postgres.yml`
    - mysql/
      - `docker-compose-mysql.yml`
  - workflows/
    - dagster/
      - `Dockerfile`
      - `docker-compose-dagster.yml`

# Resources and Further Reading

1. [github.com/nyangweso-rodgers - Docker-Commands](https://github.com/nyangweso-rodgers/My-Journey-Into-Computer-Science/blob/master/04-VMs-vs-Containers/02-Containers/01-Docker/01-Docker-Commands/Readme.md)
2. [github.com/nyangweso-rodgers - Setting Express.js Development Environment](https://github.com/nyangweso-rodgers/Programming-with-JavaScript/blob/main/03-JavaScript-Frameworks/02-Express.js/01-Setting-Express-Development-Environment/Readme.md)
3. [github.com/nyangweso-rodgers - Docker Compose File](https://github.com/nyangweso-rodgers/My-Journey-Into-Computer-Science/blob/master/04-VMs-vs-Containers/02-Containers/01-Docker/02-Docker-Compose-File/Readme.md)
4. [mohamed-dhaoui.medium.com - data-streaming-journey-moving-from-postgresql-to-bigquery-with-kafka-connect-and-debezium-2679fdbbffd0](https://mohamed-dhaoui.medium.com/data-streaming-journey-moving-from-postgresql-to-bigquery-with-kafka-connect-and-debezium-2679fdbbffd0)
5. [Debezium Official Documentation](https://debezium.io/documentation/reference/stable/tutorial.html)
