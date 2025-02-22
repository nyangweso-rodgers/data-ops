# Clickhouse

## Table Of Contents

# ClickHouse

- **ClickHouse** is an open-source column-oriented database management system developed by **Yandex** in 2009 to power **Yandex**. It is designed to provide high performance for analytical queries. Released as open-source software in 2016, it has rapidly become one of the fastest-growing and most celebrated databases, processing over 13 trillion records and handling more than 20 billion events daily.
- ClickHouse uses a SQL-like query language for querying data and supports different data types, including:

  1. integers,
  2. strings,
  3. dates,
  4. and floats.

- **ClickHouse Cloud**
  - The advantage of the hosted version, is that users won’t have to manage a complex database system themselves. The system will automatically handle sharding, replication and upgrading. Auto-scaling, too, is built into ClickHouse Cloud

# Architecture Of ClickHouse

1. **Columnar Storage Format**

   - Unlike traditional row-oriented databases, **ClickHouse** stores data by **columns** rather than **rows**. This approach offers several advantages:
     - Reduced I/O: Only the necessary columns for a query are read from storage, minimizing disk operations.
     - Improved Compression: Column-wise storage allows for better data compression, as similar data types are grouped together
     - Efficient Analytical Queries: Columnar format is optimized for aggregations and scans over large datasets.

2. **Vectorized Query Execution**

   - ClickHouse employs vectorized query execution, processing data in batches or chunks:
     - Multiple rows are processed simultaneously, leveraging modern CPU capabilities
     - This approach minimizes the overhead of handling individual values and maximizes CPU efficiency through SIMD (Single Instruction, Multiple Data) operations.

3. **Distributed Query Processing**

   - **ClickHouse’s** architecture supports distributed query execution:

     1. Query Analysis: The system analyzes the query structure and identifies relevant tables and sections.
     2. Query Parsing: The query is divided into optimal fragments.
     3. Query Optimization: The system selects the most efficient execution plan.
     4. Query Routing: Query fragments are routed to relevant nodes holding the required.
     5. Parallel Execution: Query fragments are processed in parallel across nodes
     6. Data Aggregation: Results from different nodes are merged to produce the final output.

   - Query Flow:

     1. Client submits a query through one of the entry points.
     2. The query is routed through the load balancer to an available ClickHouse node.
     3. The Query Parser interprets the SQL statement.
     4. The Query Optimizer creates an efficient execution plan.
     5. For distributed setups, the Distributed Query Planner splits the query across nodes.
     6. The Vectorized Execution Engine retrieves data from Columnar Storage via Storage Engines.
     7. Data Processors apply operations on the retrieved data.
     8. Results are aggregated in the Result Aggregator.
     9. The final result is sent back to the client.

   - Component details :
     1. Client Entry Points (HTTP/TCP/CLI): These are the interfaces through which clients can interact with ClickHouse. Supported protocols include HTTP, native TCP, and command-line interface (CLI).
     2. Load Balancer/Router: Distributes incoming queries across multiple ClickHouse nodes for better performance and high availability.
     3. Query Parser: Analyzes and interprets the incoming SQL queries.
     4. Query Optimizer: Creates an efficient execution plan for the parsed query.
     5. Distributed Query Planner: Determines how to split and execute the query across multiple nodes in a distributed setup.
     6. Columnar Storage: The underlying data storage format optimized for analytical workloads.
     7. Storage Engines: Manage how data is physically stored and retrieved (e.g., MergeTree family).
     8. Vectorized Execution Engine: Processes data in batches (vectors) for improved CPU efficiency.
     9. Data Processors: Handle operations like filtering, aggregation, and transformations on the data.
     10. Result Aggregator: Combines partial results from different nodes or processors into the final output.

# Key Features of ClickHouse

- **ClickHouse** stands out as a powerful columnar database management system designed for **online analytical processing** (OLAP) workloads.
  1. Columnar Storage and Compression
  2. Real-Time Analytics Capabilities
  3. Vectorized Query Execution
  4. Scalability and Distributed Architecture
  5. SQL Compatibility and Ecosystem Integration

# Technical Setup

## 1. Prerequisites

1. Docker (https://www.docker.com/)
2. Docker Compose (https://docs.docker.com/compose/)
3. **ZooKeeper**: **Zookeeper** is the preliminary service that **Clickhouse** uses for storing replicas’ meta information. This is needed for the replication mechanism that **Clickhouse** cluster offers.

4. **ClickHouse Keeper** (**clickhouse-keeper**)
   - **ClickHouse Keeper** provides the coordination system for **data replication** and **distributed DDL queries** execution. **ClickHouse Keeper** is compatible with **ZooKeeper**.
   - **ZooKeeper** is one of the first well-known open-source coordination systems. It's implemented in **Java**, and has quite a simple and powerful data model. ZooKeeper's coordination algorithm, **ZooKeeper Atomic Broadcast** (**ZAB**), doesn't provide linearizability guarantees for reads, because each ZooKeeper node serves reads locally. Unlike **ZooKeeper**, **ClickHouse Keeper** is written in **C++** and uses the **RAFT algorithm** implementation. This algorithm allows linearizability for reads and writes, and has several open-source implementations in different languages.
   - By default, **ClickHouse Keeper** provides the same guarantees as **ZooKeeper**: linearizable writes and non-linearizable reads. It has a compatible client-server protocol, so any standard ZooKeeper client can be used to interact with **ClickHouse Keeper**. Snapshots and logs have an incompatible format with **ZooKeeper**, but the `clickhouse-keeper-converter` tool enables the conversion of **ZooKeeper** data to **ClickHouse Keeper** snapshots. The interserver protocol in ClickHouse Keeper is also incompatible with ZooKeeper so a mixed ZooKeeper / ClickHouse Keeper cluster is impossible.
   - Configuration:
     - **ClickHouse Keeper** can be used as a standalone replacement for **ZooKeeper** or as an internal part of the ClickHouse server. In both cases the configuration is almost the same `.xml` file.

## 2. File configuration for Clickhouse

1.  **Clickhouse server configuration** (`config.d/config.xml`):

    - `config.xml`: Defines ClickHouse server settings, including ZooKeeper/Keeper integration pointing to `clickhouse-keeper:9181`.

    ```xml
      <clickhouse replace="true">
      <!-- Logger Configuration -->
      <logger>
          <level>debug</level> <!-- Sets logging verbosity to debug level -->
          <log>/var/log/clickhouse-server/clickhouse-server.log</log>  <!-- Specifies main log file path at /var/log/clickhouse-server/clickhouse-server.log -->
          <errorlog>/var/log/clickhouse-server/clickhouse-server.err.log</errorlog>  <!-- Defines error log file location at /var/log/clickhouse-server/clickhouse-server.err.log -->
          <size>1000M</size> <!-- Limits each log file to 1000 megabytes -->
          <count>3</count> <!-- Keeps 3 rotated log files -->
      </logger>

      <display_name>ch-1S_1K</display_name> <!-- Sets the server’s display name -->

      <!-- Network Configuration -->
      <listen_host>0.0.0.0</listen_host> <!-- Listens on all network interfaces -->
      <http_port>8123</http_port> <!-- HTTP interface port -->
      <tcp_port>9000</tcp_port> <!-- Native protocol port -->
      <mysql_port>9004</mysql_port> <!-- MySQL protocol port-->

      <!-- Specifies user configuration locations -->
      <user_directories>
          <users_xml>
              <path>users.xml</path>
          </users_xml>
          <local_directory>
              <path>/var/lib/clickhouse/access/</path>
          </local_directory>
      </user_directories>
      <distributed_ddl> <!--Configuration for distributed DDL operations-->
          <path>/clickhouse/task_queue/ddl</path>
      </distributed_ddl>

      <!--ZooKeeper Integration-->
      <zookeeper>
          <node>
              <host>clickhouse-keeper</host> <!--Points to clickhouse-keeper service-->
              <port>9181</port> <!--Uses port 9181 for keeper communication-->
          </node>
      </zookeeper>
    </clickhouse>
    ```

    - Where:

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

2.  **Clickhouse server configuration for users** (`users.d/users.xml`) :

    - `users.d/users.xml`

    ```xml
      <?xml version="1.0"?>
      <clickhouse replace="true">
          <profiles>
              <default>
                  <max_memory_usage>10000000000</max_memory_usage> <!--max_memory_usage: 10GB (10000000000 bytes) maximum memory usage per query-->
                  <use_uncompressed_cache>0</use_uncompressed_cache>
                  <load_balancing>in_order</load_balancing> <!--load_balancing: Set to “in_order” for distributed queries-->
                  <log_queries>1</log_queries><!--log_queries: Enabled (1) to log all queries-->
              </default>
          </profiles>
          <users>
              <default>
                  <access_management>1</access_management> <!-- allowing the user to manage access rights -->
                  <profile>default</profile><!--Set to use the “default” profile defined above-->
                  <networks>
                      <ip>::/0</ip><!--Allows connections from any IP (::/0)-->
                  </networks>
                  <quota>default</quota><!--Uses the “default” quota below-->
                  <access_management>1</access_management>
                  <named_collection_control>1</named_collection_control>
                  <show_named_collections>1</show_named_collections>
                  <show_named_collections_secrets>1</show_named_collections_secrets>
              </default>
              <!-- Transaction service user -->
              <transaction_user>
                  <password>secure_password</password>
                  <profile>default</profile>
                  <networks>
                      <ip>::/0</ip>
                  </networks>
                  <quota>default</quota>
                  <access_management>1</access_management>
              </transaction_user>
          </users>
          <quotas>
              <default>
                  <interval><!-- default quota is defined with an interval of 1 hour (3600 seconds)-->
                      <duration>3600</duration>
                      <!--All quota limits (queries, errors, result_rows, read_rows, execution_time) are set to 0, which means no limits are imposed-->
                      <queries>0</queries>
                      <errors>0</errors>
                      <result_rows>0</result_rows>
                      <read_rows>0</read_rows>
                      <execution_time>0</execution_time>
                  </interval>
              </default>
          </quotas>
      </clickhouse>
    ```

    - Where:

          1. Profiles

             - Maximum memory usage per query: 10GB
             - Uncompressed cache usage: Disabled
             - Load balancing for distributed queries: Set to “in_order”
             - Query logging: Enabled

          2. Users
             - Two users are defined: `“default”` and `“transaction_user”`
             - Both users have:
               - Access management enabled
               - Use the default profile
               - Can connect from any IP address
               - Use the default quota
               - The default user has additional permissions for named collections
               - The `transaction_user` has a specific password set

          3. Quotas
             - An interval duration of 1 hour (3600 seconds)
             - No limits set for queries, errors, result rows, read rows, or execution time (all set to 0)

## 3. Install Clickhouse Client

- Install clickhouse-client (https://clickhouse.com/docs/en/install)

  ```sh
    curl https://clickhouse.com/ | sh
  ```

- Connect to clickhouse:

  ```sh
    ./clickhouse client --user transaction_user --password secure_password
  ```

- Execute the following DDL in the CLI :

  ```sh
    CREATE DATABASE IF NOT EXISTS transactions;
    USE transactions;
  ```

- Execute the following DDL in the CLI to create the table :
  ```sh
    CREATE TABLE IF NOT EXISTS transactions (
        id String ,
        amount Decimal(18, 2),
        currency String,
        status Enum('pending' = 1, 'completed' = 2, 'failed' = 3),
        user_id String,
        merchant_id String,
        payment_method String,
        created_at DateTime DEFAULT now()
    ) ENGINE = MergeTree()
    ORDER BY user_id
    SETTINGS index_granularity=8192;
  ```
- **Remarks**:
  1. Starting with `ClickHouse 22.6`, **Keeper** is bundled into the server image, so you could run **Keeper** within the same container as the server instead of using a separate `clickhouse-keeper:<>` image. This might simplify your setup
  2. We don't need to run a standalone `clickhouse-keeper` service as we can integrate **ClickHouse Keeper** into the `clickhouse-server` container using the bundled **Keeper** functionality in version `24.8.7.41`

## 5. Running and Testing

1. Start the Services

   - `docker-compose up -d`
   - Check logs: `docker logs clickhouse-server` (look for Keeper starting on `9181` and no errors).

2. Test ClickHouse

   - `docker exec -it clickhouse-server clickhouse-client`
   - Run: `SELECT * FROM system.zookeeper WHERE path = '/'` (will be empty until you create replicated tables).

3. Test Keeper:

   - `docker exec -it clickhouse-server clickhouse-keeper-client --host localhost --port 9181`
   - Run: `ls` (should return an empty response if no data yet).

4. Test Tabix

   - Open http://localhost:8090 in your browser.
   - Enter `http://localhost:8123` in a single `http://host:port` field if that’s how your Tabix UI is structured.
   - Use the `default` user (no password) or `transaction_user` with `secure_password` to connect to clickhouse-server:8123.

5. Create a Replicated Table (to verify Keeper):

   - In `clickhouse-client`

     ```sql
      CREATE TABLE test_replicated
        (
            id UInt32,
            value String
        )
        ENGINE = ReplicatedMergeTree('/clickhouse/tables/{shard}/test_replicated', '{replica}')
        ORDER BY id;
     ```

   - Insert data: `INSERT INTO test_replicated VALUES (1, 'test');`
   - Check `system.zookeeper` again to see replication metadata.

# Connect to clickhouse

## 2. ClickHouse Server

- Some of the interesting **properties** include:

  - port-mappings (e.g. port `9000` for Clickhouse’s native TCP/IP protocol endpoint and port `8123` for Clickhouse’s HTTP interface) and volumes (for the persistence of your data)

- **Step 4**: Access ClickHouse’s Web Interface (Optional)

  - **ClickHouse** provides an **HTTP** interface on port `8123`. To access it, open a browser and navigate to: http://localhost:8123
  - This interface is minimal, but it allows you to execute queries directly from your browser.

- **Step** : **Interacting with ClickHouse: Example Commands**

  1. Create a Sample Database

     - Inside the clickhouse-client, create a new database:
       ```sql
        CREATE DATABASE test_db;
       ```

  2. Create a Sample Table

     - Within `test_db`, create a sample table:
       ```sql
        CREATE TABLE test_db.sample_table (
        id UInt32,
        name String,
        age UInt8
        ) ENGINE = MergeTree() ORDER BY id;
       ```

  3. Insert Data

     - Add some sample data to the table:
       ```sql
        INSERT INTO test_db.sample_table VALUES (1, 'Alice', 25), (2, 'Bob', 30);
       ```

  4. Query Data
     - Retrieve data from the table:
       ```sql
        SELECT * FROM test_db.sample_table;
       ```

# How to deploy ClickHouse

# ETL Tools for ClickHouse

1. Airbyte
2. Apache NiFi
3. Debezium
4. dbt (Data Build Tool)
5. Custom Python Scripts
6. Kafka Connect with ClickHouse Sink
7. pg2ch
8. Flink
9. ClickHouse’s Built-in MySQL and PostgreSQL Engines
10. Logstash
11. Metabase (for Ad-hoc ETL)
12. Custom Shell Scripts
    - You can use shell scripts with tools like `mysqldump`, `pg_dump`, and `curl` to extract data and load it into ClickHouse.

# ClickHouse Concepts

## 1. Primary Key

- **ClickHouse** indexes are based on **Sparse Indexing**, an alternative to the **B-Tree index** utilized by traditional **DBMSs**. In **B-tree**, every row is indexed, which is suitable for locating and updating a single row, also known as **pointy-queries** common in OLTP tasks. This comes with the cost of poor performance on high-volume insert speed and high memory and storage consumption. On the contrary, the **sparse index** splits data into multiple parts, each group by a fixed portion called **granules**. **ClickHouse** considers an index for every **granule** (**group of data**) instead of every row, and that’s where the **sparse index** term comes from. Having a query filtered on the primary keys, **ClickHouse** looks for those **granules** and loads the matched **granules** in parallel to the memory. That brings a notable performance on range queries common in OLAP tasks. Additionally, as data is stored in **columns** in multiple files, it can be compressed, resulting in much less storage consumption.
- The nature of the **spars-index** is based on **LSM trees** allowing you to insert high-volume data per second. All these come with the cost of not being suitable for pointy queries, which is not the purpose of the **ClickHouse**.

# System Tables

- **ClickHouse** has a lot of tables with internal information or meta data.
- Show all **system tables** by:
  ```sql
    SHOW TABLES FROM system
  ```

## 2. Partition Key

- Create a table by specifying **partition key**:

  ```sql
    CREATE TABLE default.projects_partitioned
    (

        `project_id` UInt32,

        `name` String,

        `created_date` Date
    )
    ENGINE = MergeTree
    PARTITION BY toYYYYMM(created_date)
    PRIMARY KEY (created_date, project_id)
    ORDER BY (created_date, project_id, name)
  ```

  - Here, **ClickHouse** partitions data based on the **month** of the `created_date`:

## 3. Materialized View in Clickhouse

- **Definitions and purpose**:

  - **Materialized views** in **ClickHouse** are a powerful feature that can significantly enhance query performance and data processing efficiency.
  - A **materialized view** in **ClickHouse** is essentially a trigger that runs a query on blocks of data as they are inserted into a source table.
  - The results of this query are then stored in a separate “target” table.
  - This allows for precomputation of aggregations, transformations, or complex calculations, shifting the computational burden from query time to insert time.

- **Features**:

  - Unlike traditional **materialized views** in some databases, **ClickHouse materialized views** are updated in real-time as data flows into the source table.
  - By querying **materialized views** instead of raw data, resource-intensive calculations are offloaded to the initial view creation process.
  - This can drastically reduce query execution time, especially for complex analytical queries.

- **Use Cases**:

  1. Materialized views are particularly useful for real-time analytics dashboards, where instant insights from large volumes of data are required.
  2. They can precompute aggregations, perform data transformations, or filter data for specific use cases.

- **Considerations**:

  - While **materialized views** offer significant performance benefits, they do consume additional CPU, memory, and disk resources as data is processed and written into the new form.

- **Types of Materialized Views in ClickHouse**: ClickHouse offers several types of materialized views based on different storage engines:

  1. **AggregatingMergeTree**

     - Best for aggregation operations
     - Maintains running totals and counts
     - Example:
       ```sql
        CREATE MATERIALIZED VIEW view_name
        ENGINE = AggregatingMergeTree()
        ORDER BY key_column
        AS SELECT
            key_column,
            aggregateFunction(value_column)
        FROM source_table
        GROUP BY key_column;
       ```

  2. **SummingMergeTree**:

     - Optimized for summing operations
     - Automatically combines rows with the same primary key
     - Example:
       ```sql
        CREATE MATERIALIZED VIEW view_name
        ENGINE = SummingMergeTree()
        ORDER BY key_column
        AS SELECT
            key_column,
            sum(value_column) as total
        FROM source_table
        GROUP BY key_column;
       ```

  3. **ReplacingMergeTree**
     - Keeps only the latest version of each row
     - Useful for deduplication
     - Example:
       ```sql
        CREATE MATERIALIZED VIEW view_name
        ENGINE = ReplacingMergeTree(version_column)
        ORDER BY key_column
        AS SELECT * FROM source_table;
       ```

# Resources and Further Reading

1. [clickhouse - Docker Image](https://hub.docker.com/_/clickhouse)
2. [Medium - Running a Clickhouse Distributed Multi Node Cluster Locally Using Docker Compose](https://archive.ph/9ptU6#selection-313.0-313.80)
3. [Medium - ClickHouse Basic Tutorial: Keys & Indexes](https://itnext.io/clickhouse-basic-tutorial-keys-indexes-ed72b0c0cc2f)
4. [Medium - ClickHouse: A Deep Dive into Modern Real-Time Analytics](https://towardsdev.com/clickhouse-a-deep-dive-into-modern-real-time-analytics-32442257a5b8)
