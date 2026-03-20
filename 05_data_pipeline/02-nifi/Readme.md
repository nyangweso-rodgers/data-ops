# Apache NiFi

## Table Of Contents

# What is Apache NIFI ?

- **Apache NiFi** is a robust platform designed to automate and manage the flow of data between systems.
- **Apache NiFi** is a real time data ingestion platform, which can transfer and manage data transfer between different sources and destination systems. It supports a wide variety of data formats like **logs**, **geo** **location data**, **social feeds**, etc. It also supports many protocols like **SFTP**, **HDFS**, and **KAFKA**, etc. This support to wide variety of data sources and protocols making this platform popular in many IT organizations.

# The core concepts of NiFi

# Set Up NiFi Using Docker

- Step 1:

  ```Dockerfile
    docker pull apache/nifi:latest
  ```

- Step : Access Apache NiFi
  - Access Apache NiFi UI from `http://localhost:8443` or `https://localhost:8443/nifi`
  - Finding the Default Credentials: When **NiFi** starts for the first time, it logs the generated username and password in the `nifi-app.log` or console output. Look in the logs for something like:
    ```sh
      Generated Username [some-username]
      Generated Password [some-password]
    ```

## 1. Setting Up a PostgreSQL-to-ClickHouse Flow in NiFi

- Overview

  - **Source**: Postgres table (queried via `QueryDatabaseTable`).
  - **Destination**: ClickHouse table (via `PutClickHouse`).

- Prerequisites

  1. **Postgres JDBC Driver**: Baked into NiFi image via the Dockerfile.
  2. ClickHouse driver in NiFi
  3. Connection pool
  4. Flow to move data

- **Step 1**: **Add ClickHouse JDBC Driver to NiFi**

  - **NiFi** needs the **ClickHouse JDBC driver** to communicate with **clickhouse-server**. Let’s update `Dockerfile` to include the ClickHouse driver.

    ```Dockerfile
      FROM apache/nifi:latest

      USER root
      RUN apt-get update && apt-get install -y wget && rm -rf /var/lib/apt/lists/*

      # Add Postgres JDBC driver
      RUN wget -O /opt/nifi/nifi-current/lib/postgresql-42.7.3.jar \
          https://jdbc.postgresql.org/download/postgresql-42.7.3.jar

      # Add ClickHouse JDBC driver
      RUN wget -O /opt/nifi/nifi-current/lib/clickhouse-jdbc-0.6.4.jar \
          https://repo1.maven.org/maven2/com/clickhouse/clickhouse-jdbc/0.6.4/clickhouse-jdbc-0.6.4.jar

      USER nifi
    ```

- **Step 2**: **Rebuild and Restart NiFi**

  ```sh
    docker-compose -f docker-compose.nifi.yml down
    docker-compose -f docker-compose.nifi.yml up -d --build
  ```

- **Step 3**: **Configure ClickHouse Connection Pool in NiFi**

  1. **Open Controller Services**: **NiFi UI** > **Hamburger menu** > **Controller Settings** > **Controller Services** > `+`.
  2. **Add DBCPConnectionPool**
     - Search `DBCPConnectionPool`, name it `ClickHouseDBConnectionPool`.
     - Configure:
       - **Database Connection URL**: `jdbc:clickhouse://clickhouse-server:8123/default` (replace `default` with your ClickHouse database name if different).
       - **Database Driver Class Name**: `com.clickhouse.jdbc.ClickHouseDriver`.
       - **Database Driver Location(s)**: `/opt/nifi/nifi-current/lib/clickhouse-jdbc-0.6.4.jar`.
       - **Database User**: Your ClickHouse username (`default` is default if unchanged in `users.xml`).
       - **Password**: Your ClickHouse password (`default` is empty unless set in `users.xml`).
     - Apply and enable it (lightning bolt).

- **Step 4**: **Create a ClickHouse Table**

  - Before syncing, ensure a target table exists in ClickHouse. Use your tabix UI (`http://localhost:8090`) or **clickhouse-client**:
    ```sh
      # bash
      docker exec -it clickhouse-server clickhouse-client
    ```
  - Run a query to create a table (adjust based on your Postgres table structure—share it if you want specifics!):
    ```sql
      -- sql
      CREATE TABLE default.customers (
        id Nullable(String),
        first_name Nullable(String),
        created_at Nullable(DateTime)
    ) ENGINE = MergeTree()
    ORDER BY (id);
    ```

- **Stpe 5**: **Build the NiFi Flow**

  - Assuming `PostgresDBConnectionPool` is now visible (enabled at root level), let’s set up the flow.

    1. **QueryDatabaseTable Processor**:

       - Add to **canvas** > **Configure**:
         - **Database Connection Pooling Service**: `PostgresDBConnectionPool`.
         - **Table Name**: Your Postgres table (e.g., `users`).
         - **Columns to Return**: Leave blank or specify (e.g., `id`, `first_name`, `created_at`).
         - **Maximum-value Columns**: `id` (for incremental sync).
       - Apply

    2. **PutClickHouse Processor**

       - Add to **canvas** > **Configure**
         - **ClickHouse Connection Pool**: `ClickHouseDBConnectionPool`.
         - **Table Name**: `my_table` (or your ClickHouse table name).
         - **Record Reader**: Add a `JsonRecordSetReader` (**Controller Services** > `+` > `Enable`).
       - Apply

    3. **Connect Processors**

       - Drag an arrow from `QueryDatabaseTable` (success) to `PutClickHouse`.

    4. **Start the Flow**
       - Right-click each processor > "Start".
       - NiFi will query Postgres and insert records into ClickHouse.

- **Step 6**: **Verify in ClickHouse**

  - Use **tabix** (`http://localhost:8090`) or `clickhouse-client`
    ```sql
      -- sql 
      SELECT * FROM default.my_table;
    ``` 

## 2. Setting Up a PostgreSQL-to-Kafka Flow in NiFi

# Resources and Further Reading

1.
