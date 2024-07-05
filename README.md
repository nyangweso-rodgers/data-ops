# Data Ops

# Project Description

- This prject is for:
  - **Data Pipeline** Service with **Apache Kafka**, **Postgres**, and **MongoDB**.
  - API service, and a
  - Next.js Application.

# Prerequisites

- Before diving into the project, ensure you have the following prerequisites:
  1. Docker — Docker Compose
  2. Apache Kafka (Stream Processing)
  3. PostgreSQL
  4.
  5. Superset(Report/Dashboard)
  6. Kafka UI ( Kafka Monitoring)
  7. Grafana (System Monitoring)

# Setup

- The project has the following services running as Docker containers

  1. mongo
  2. postgres
  3. pgadmin
     - [dpage/pgadmin4](https://hub.docker.com/r/dpage/pgadmin4) is a web based administration tool for the PostgreSQL database.
  4. kafka
  5. kafka-ui
  6. zookeeper
  7. schema-registry
  8. sale-order-api
  9. customer-api
  10. nextjs.app

# 1. Databases

# 1.1 PostgreSQL Docker Container

- Check my [github.com/nyangweso-rodgers - Running PostgreSQL Docker Container](https://github.com/nyangweso-rodgers/My-Databases/tree/main/02-Transactional-Databases/01-postgresql/01-setup-postgresql/01-postgres-docker-container), GitHub repo on how to configure and run postgresql docker container using **docker-compose**.
  ```yml
  services:
  ```

## Connect to a Postgres Docker Container

- To connect to a **PostgreSQL** instance running within a **Docker container**, you can use the `docker exec` command combined with the `psql` command:
- Example:
  ```bash
    #accessing postgres docker container
    docker exec -it postgres psql -U admin -d test_db
  ```
- Remarks:
  - Check my [GitHub Repo](https://github.com/nyangweso-rodgers/My-Databases/blob/main/02-Transactional-Databases/01-postgresql/02-connect-to-postgresql/01-psql-commands/Readme.md) for a list of `psql` commands

# 1.2 MongoDB Docker Container

- Check [github.com/nyangweso-rodgers - Run MongoDB Docker Container](https://github.com/nyangweso-rodgers/My-Databases/blob/main/03-Working-with-MongoDB/02-Setup-MongoDB/01-Run-MongoDB-Docker-Container/Readme.md) repo on how to run a mongo docker container using docker-compose.
- Check [github.com/nyangweso-rodgers - mongoDB replica set](https://github.com/nyangweso-rodgers/My-Databases/blob/main/03-Working-with-MongoDB/01-Fundamentals-of-MongoDB/mongoDB-replica-set/Readme.md) repo, to successfully set up a **MongoDB** **replica set** with **Docker Compose**. This ensures that you have a highly available and resilient MongoDB deployment.
  ```yml
  services:
  ```

# 2. Messaging Broker Services

# 2.1 Zookeeper

```yml
services:
```

# 2.2 Kafka

```yml
services:
```

## Access Kafka Shell of the Kafka Container

- Access the shell of the **Kafka container** by running the following command:

  ```sh
    #access kafka shell
    docker exec -it kafka bash
  ```

## List Available Kafka Topics

- Use the `kafka-topics` command to list the topics in the **Kafka cluster**:
  ```sh
    #list available kafka topics
    kafka-topics --list --bootstrap-server kafka:29092
  ```
- If no **topics** exists, the following will be returned:
  ```sh
    __consumer_offsets
    _schemas
  ```

## Delete Kafka Topic

- To delete a topic use the `kafka-topics` command with the `--delete` option.
  - Syntax:
    ```sh
      kafka-topics --bootstrap-server localhost:29092 --delete --topic <topic_name>
    ```
- Example:
  ```sh
    kafka-topics --bootstrap-server localhost:29092 --delete --topic  test-kafka-topic
  ```

# 2.3 Schema Registry

```yml
services:
```

# 2.4 Debezium

```yml
services:
```

## Configure Debezum Connector

```json
{
  "name": "customer-postgresdb-connector",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "tasks.max": "1",
    "plugin.name": "pgoutput",
    "database.hostname": "postgres",
    "database.port": "5432",
    "database.user": "admin",
    "database.password": "<password>",
    "database.dbname": "test_db",
    "database.server.name": "postgres",
    "table.include.list": "public.customer",
    "heartbeat.interval.ms": "5000",
    "key.converter": "org.apache.kafka.connect.json.JsonConverter",
    "value.converter": "org.apache.kafka.connect.json.JsonConverter",
    "value.converter.schemas.enable": false,
    "topic.prefix": "test_db",
    "topic.creation.enable": "true",
    "topic.creation.default.replication.factor": "1",
    "topic.creation.default.partitions": "1",
    "topic.creation.default.cleanup.policy": "delete",
    "topic.creation.default.retention.ms": "604800000"
  }
}
```

## Properties

- Other **properties** include:

  1. `publication.autocreate.mode`
     - Example: `"publication.autocreate": "filtered"`
     - Setting `publication.autocreate.mode` property to `"filtered"` instructs **Debezium** to automatically create a **publication** that includes only the tables listed in `table.include.list`. It doesn't specify the exact tables or schema you want to include. However, if you'll be defining your own **publication** explicitly (using `CREATE PUBLICATION` command ), this property is not necessary. Removing it from both connector configurations will streamline your setup.

## Step : Create Publications in PostgreSQL

- Create **publications** for the respective tables in **PostgreSQL**.

  ```sql
    -- Connect to your PostgreSQL database
    psql -h localhost -U admin -d test_db

    -- Create a publication for the customer table
    CREATE PUBLICATION debezium_customer_publication FOR TABLE public.customer;

    -- Create a publication for the delegates_survey table
    CREATE PUBLICATION debezium_delegates_survey_publication FOR TABLE public.delegates_survey;
  ```

## Step : Verifying the Setup

1. **Check Replication Slot Status**: Ensure both replication slots are correctly configured and active.
   ```sql
    SELECT * FROM pg_replication_slots;
   ```
2. **Check Publications**: Verify that the publications include the correct tables.
   ```sql
    -- Check the publications
    SELECT * FROM pg_publication;
    -- Check the tables associated with each publication
    SELECT * FROM pg_publication_tables;
   ```
3. **Check Kafka Topics**: Ensure that Kafka topics are created and data is being streamed correctly.

## Step : Remove the Unused debezium Slot

1. Drop the Unused Slot:
   ```sql
    SELECT pg_drop_replication_slot('debezium');
   ```
2. Verify Slots After Dropping:
   ```sql
    SELECT * FROM pg_replication_slots;
   ```

## Step : Register Debezium Connector(s) using `curl` Commands

- To **register** debezium **connector**, run the below `curl` commands:

  ```sh
    curl -X POST --location "http://localhost:8083/connectors" -H "Content-Type: application/json" -H "Accept: application/json" -d @register-customer-postgresdb-connector.json
  ```

- and
  ```sh
    curl -X POST --location "http://localhost:8083/connectors" -H "Content-Type: application/json" -H "Accept: application/json" -d @register-delegates-survey-postgresdb-connector.json
  ```

## Step : Delete Debezium Connector(s) using `curl` Commands

- Remove the **connectors** by:
  ```sh
    curl -X DELETE http://localhost:8083/connectors/customer-postgresdb-connector
  ```
- And:
  ```sh
    curl -X DELETE http://localhost:8083/connectors/delegates-surveys-postgresdb-connector
  ```

# 3. GUI Servces

## 3.1 Kafka UI

```yml
services:
```

## 3.2 Debezium UI

```yml
services:
```

# 4. Dashboards

- We can build the dashboards using the following tools:
  1. Metabase
  2. Superset
  3. Redash
  4. Tableau
  5. Power BI

## 4.1 Metabase Docker Container

```yml
services:
```

## Access Metabase

- Once the **Docker Compose** is up and running, you can access Metabase at http://localhost:3000 in your web browser.

## Connect Metabase to PostgreSQL

- When you first open **Metabase**, it will ask you to setup a connection to your database. Here are the settings you need to use:
  1. Database type: PostgreSQL
  2. Host: postgres
  3. Port: 5432
  4. Database name: <provide database name>
  5. Username: <username>
  6. Password: <password>
- Now, you should be able to explore your **PostgreSQL** data using **Metabase**!

# Resources and Further Reading

1. [github.com/nyangweso-rodgers - Docker-Commands](https://github.com/nyangweso-rodgers/My-Journey-Into-Computer-Science/blob/master/04-VMs-vs-Containers/02-Containers/01-Docker/01-Docker-Commands/Readme.md)

2. [github.com/nyangweso-rodgers - Setting Express.js Development Environment](https://github.com/nyangweso-rodgers/Programming-with-JavaScript/blob/main/03-JavaScript-Frameworks/02-Express.js/01-Setting-Express-Development-Environment/Readme.md)
3. [github.com/nyangweso-rodgers - Docker Compose File](https://github.com/nyangweso-rodgers/My-Journey-Into-Computer-Science/blob/master/04-VMs-vs-Containers/02-Containers/01-Docker/02-Docker-Compose-File/Readme.md)
