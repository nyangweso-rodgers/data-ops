# Clickhouse

## Table Of Contents

# ClickHouse

- **ClickHouse** is an open-source column-oriented database management system developed by **Yandex** in 2009 to power **Yandex**. It is designed to provide high performance for analytical queries. Released as open-source software in 2016, it has rapidly become one of the fastest-growing and most celebrated databases, processing over 13 trillion records and handling more than 20 billion events daily.

# Setup ClickHouse Docker Container

- **Requirements**

  - Docker (https://www.docker.com/)
  - Docker Compose (https://docs.docker.com/compose/)
  - **ClickHouse Keeper** (**clickhouse-keeper**)
    - **ClickHouse Keeper** provides the coordination system for **data replication** and **distributed DDL queries** execution. **ClickHouse Keeper** is compatible with **ZooKeeper**.
    - **ZooKeeper** is one of the first well-known open-source coordination systems. It's implemented in **Java**, and has quite a simple and powerful data model. ZooKeeper's coordination algorithm, **ZooKeeper Atomic Broadcast** (**ZAB**), doesn't provide linearizability guarantees for reads, because each ZooKeeper node serves reads locally. Unlike **ZooKeeper**, **ClickHouse Keeper** is written in **C++** and uses the **RAFT algorithm** implementation. This algorithm allows linearizability for reads and writes, and has several open-source implementations in different languages.
    - By default, **ClickHouse Keeper** provides the same guarantees as **ZooKeeper**: linearizable writes and non-linearizable reads. It has a compatible client-server protocol, so any standard ZooKeeper client can be used to interact with **ClickHouse Keeper**. Snapshots and logs have an incompatible format with **ZooKeeper**, but the `clickhouse-keeper-converter` tool enables the conversion of **ZooKeeper** data to **ClickHouse Keeper** snapshots. The interserver protocol in ClickHouse Keeper is also incompatible with ZooKeeper so a mixed ZooKeeper / ClickHouse Keeper cluster is impossible.
  - **Remarks**:
    - Starting with `ClickHouse 22.6`, **Keeper** is bundled into the server image, so you could run **Keeper** within the same container as the server instead of using a separate `clickhouse-keeper:<>` image. i.e., We don't need to run a standalone `clickhouse-keeper` service as we can integrate **ClickHouse Keeper** into the `clickhouse-server` container using the bundled **Keeper** functionality in version `24.8.7.41`

- **Step 1** : **Configure** `clickhouse-server` **Docker Container**

  - **Healthcheck Details**:

    - `curl -f http://localhost:8123/ping`: Checks if ClickHouse’s HTTP interface is up (returns “Ok” when healthy).
    - Retries 5 times every 10 seconds—gives ClickHouse up to 50 seconds to start, which is usually plenty.

- **Step 2**: **Configure** `config.xml` **File**

  - `config.xml`: Defines ClickHouse server settings, including ZooKeeper/Keeper integration pointing to `clickhouse-keeper:9181`.
    ```xml
     <!-- config.xml-->
    ```
  - where:
    1. `<level>debug</level>` : Sets logging verbosity to debug level
    2. `<log>`: Specifies main log file path at `/var/log/clickhouse-server/clickhouse-server.log`
    3. `<errorlog>`: Defines error log file location at `/var/log/clickhouse-server/clickhouse-server.err.log`
    4. `<size>1000M</size>`: Limits each log file to 1000 megabytes
    5. `<count>3</count>`: Keeps 3 rotated log files
    6. `<display_name>ch-1S_1K</display_name>`: Sets the server’s display name Network Settings
    7. `<listen_host>0.0.0.0</listen_host>`: Listens on all network interfaces
    8. `<http_port>8123</http_port>`: Port for HTTP interface
    9. `<tcp_port>9000</tcp_port>`: Port for native ClickHouse protocol
    10. `<user_directories>`: Specifies user configuration locations
    11. `users_xml`: Points to users.xml for user settings
    12. `local_directory`: Local path for access control files
    13. `<distributed_ddl>`: Configuration for distributed DDL operations
    14. `path`: ZooKeeper path for DDL task queue

- **Step 3**: **Configure** `users.xml` **File**

  - Clickhouse server configuration for users (`users.d/users.xml`)
    ```xml
      <!-- users.xml-->
    ```
  - where:

- **Step 4** : **Access** `clickhouse-server` **Docker Container**

  - Access `clickhouse-server` Docker Container by:
    ```sh
      docker exec -it clickhouse-server clickhouse-client
    ```
  - Create a sample database: Inside the `clickhouse-client`, create a new database by:
    ```sql
        CREATE DATABASE test_db;
    ```
  - Create a sample table: Within `test_db`, create a sample table:
    ```sql
        CREATE TABLE test_db.sample_table (
        id UInt32,
        name String,
        age UInt8
        ) ENGINE = MergeTree() ORDER BY id;
    ```
  - Add some sample data to the table:
    ```sql
        INSERT INTO test_db.sample_table VALUES (1, 'Alice', 25), (2, 'Bob', 30);
    ```
  - Query table data:
    ```sql
        SELECT * FROM test_db.sample_table;
    ```

- **Step 5**: **Access ClickHouse’s Web Interface** (**Optional**)

  - **ClickHouse** provides an **HTTP** interface on port `8123`. To access it, open a browser and navigate to: http://localhost:8123
  - This interface is minimal, but it allows you to execute queries directly from your browser.
  - **Tabix Connection Options**:

    1. **Direct CH** (**Direct ClickHouse Connection**)

       - This option allows **Tabix** to connect directly to your ClickHouse server’s HTTP interface (port `8123` by default).
       - You provide the ClickHouse server’s URL, username, and password directly in the Tabix UI.
         - URL: `http://127.0.0.1:8123` or `http://localhost:8123`
       - This is simpler and works well when Tabix and ClickHouse are on the same network or when ClickHouse is exposed to the host running your browser.

    2. **Tabix.Server**
       - This option uses an intermediary Tabix server (a backend proxy) that handles connections to ClickHouse.
       - You’d need to specify the URL of the Tabix server (not ClickHouse directly), and the Tabix server would then connect to ClickHouse on your behalf.
       - This requires a separate Tabix server setup 

# Resources and Further Reading

1. [clickhouse - Docker Image](https://hub.docker.com/_/clickhouse)
2. [Medium - Running a Clickhouse Distributed Multi Node Cluster Locally Using Docker Compose](https://archive.ph/9ptU6#selection-313.0-313.80)
3. [Medium - ClickHouse Basic Tutorial: Keys & Indexes](https://itnext.io/clickhouse-basic-tutorial-keys-indexes-ed72b0c0cc2f)
4. [Medium - ClickHouse: A Deep Dive into Modern Real-Time Analytics](https://towardsdev.com/clickhouse-a-deep-dive-into-modern-real-time-analytics-32442257a5b8)
