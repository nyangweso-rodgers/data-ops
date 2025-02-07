# Data Ops

# Project Description

- This prject is split into several phases:

  1. Phase 1: Involves setting up the following databases using Docker
     1. Postgres
     2. MySQL
     3. MongoDB
  2. Phase 2: Involves designing APIs for storing data into the above databases.
  3. Phase 3: Involves setting up the following messaging platforms for storing data for analytics workloads:
     1. Apache Kafka
  4. Phase 4: Involves constructing a data pipeline utilizing Kafka for streaming, **Airflow** for orchestration, **Spark** for data transformation, and **PostgreSQL** for storage using Docker.

- The project focuses more on practical application rather than theoretical aspects of the end-to-end data architecture.

# Prerequisites

- Before diving into the project, ensure you have the following prerequisites:
  1. Docker — Docker Compose
  2. Apache Kafka (Stream Processing)
  3. PostgreSQL
  4. Superset(Report/Dashboard)
  5. Kafka UI ( Kafka Monitoring)
  6. Grafana (System Monitoring)

# Setup

- Here is the overall structure of the project:

  - Readme.md
  - 01-databases

    - 01-postgres
    - 02-mongodb-community-server
    - 03-mysql

  - 02-apis
  - 03-messaging

    - 01-apache-kafka

  - 04-data-warehouse

    - 01-clickhouse

  - 05-pipeline

    - 01-apache-airflow

  - 06-data-visualization

    - 01-apache-superset

  - 07-ml-model

# Resources and Further Reading

1. [github.com/nyangweso-rodgers - Docker-Commands](https://github.com/nyangweso-rodgers/My-Journey-Into-Computer-Science/blob/master/04-VMs-vs-Containers/02-Containers/01-Docker/01-Docker-Commands/Readme.md)

2. [github.com/nyangweso-rodgers - Setting Express.js Development Environment](https://github.com/nyangweso-rodgers/Programming-with-JavaScript/blob/main/03-JavaScript-Frameworks/02-Express.js/01-Setting-Express-Development-Environment/Readme.md)
3. [github.com/nyangweso-rodgers - Docker Compose File](https://github.com/nyangweso-rodgers/My-Journey-Into-Computer-Science/blob/master/04-VMs-vs-Containers/02-Containers/01-Docker/02-Docker-Compose-File/Readme.md)
4. [mohamed-dhaoui.medium.com - data-streaming-journey-moving-from-postgresql-to-bigquery-with-kafka-connect-and-debezium-2679fdbbffd0](https://mohamed-dhaoui.medium.com/data-streaming-journey-moving-from-postgresql-to-bigquery-with-kafka-connect-and-debezium-2679fdbbffd0)
5. [Debezium Official Documentation](https://debezium.io/documentation/reference/stable/tutorial.html)
