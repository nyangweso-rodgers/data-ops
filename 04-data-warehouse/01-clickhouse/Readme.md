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

1. Columnar Storage Format

   - Unlike traditional row-oriented databases, **ClickHouse** stores data by **columns** rather than **rows**. This approach offers several advantages:
     - Reduced I/O: Only the necessary columns for a query are read from storage, minimizing disk operations.
     - Improved Compression: Column-wise storage allows for better data compression, as similar data types are grouped together
     - Efficient Analytical Queries: Columnar format is optimized for aggregations and scans over large datasets.

2. Vectorized Query Execution

   - ClickHouse employs vectorized query execution, processing data in batches or chunks:
     - Multiple rows are processed simultaneously, leveraging modern CPU capabilities
     - This approach minimizes the overhead of handling individual values and maximizes CPU efficiency through SIMD (Single Instruction, Multiple Data) operations.

3. Distributed Query Processing

   - ClickHouse’s architecture supports distributed query execution:

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

- **Prerequisites**

  1. Docker (https://www.docker.com/)
  2. Docker Compose (https://docs.docker.com/compose/)
  3. **ZooKeeper**: **Zookeeper** is the preliminary service that **Clickhouse** uses for storing replicas’ meta information. This is needed for the replication mechanism that **Clickhouse** cluster offers.

- **Step 1**: Create `docker-compose.yml` to define ClickHouse service:

- **Step 2**: **Create Directories and Files**

  - Create a directory structure and add the above configuration files:
    ```sh
      mkdir -p clickhouse_cluster/config
      cd clickhouse_cluster/config
      touch zookeeper.xml cluster.xml macros1.xml macros2.xml config.xml config2.xml default-password.xml
    ```
  - Add the corresponding configurations to these files.

  - 1. `config.xml`: This file defines the core ClickHouse configuration. It includes paths for storing data and logs and general settings for the ClickHouse server.

    ```xml
      <yandex>
        <listen_host>127.0.0.1</listen_host>
        <listen_host>clickhouse-node-1</listen_host>
    </yandex>
    ```

  - 2. `zookeeper.xml`: This file contains the ZooKeeper configuration for distributed coordination.

    ```xml
      <clickhouse>
        <zookeeper>
          <node index="1">
            <host>zookeeper</host>
            <port>2181</port>
          </node>
        </zookeeper>
      </clickhouse>
    ```

  - 3. `cluster.xml`: Defines the cluster configuration, detailing the nodes and shards in the cluster. Each node should have an identical `cluster.xml`.

    ```xml
      <yandex>
        <remote_servers>
            <local_cluster>
                <secret>local</secret>
                <shard>
                    <internal_replication>true</internal_replication>
                    <replica>
                        <host>clickhouse-node-1</host>
                        <port>9000</port>
                    </replica>
                    <replica>
                        <host>clickhouse-node-2</host>
                        <port>9000</port>
                    </replica>
                </shard>
            </local_cluster>
        </remote_servers>
    </yandex>
    ```

  - 4. `default-password.xml`: We need this file to set the password for default user(the value of hex is `password`)

    ```xml
      <yandex>
        <users>
            <default>
                <password remove='1' />
                <password_sha256_hex>5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8</password_sha256_hex>
            </default>
        </users>
    </yandex>
    ```

  - 5. `acess_management.xml`

    ```xml
      <yandex>
        <users>
            <default>
                <!-- access management -->
                <access_management>1</access_management>
            </default>
        </users>
    </yandex>
    ```

  - 6. `macros.xml`: Specifies macros for each node to identify its **shard** and **replica**.
    ```xml
      <yandex>
        <!--
            That macros are defined per server,
            and they can be used in DDL, to make the DB schema cluster/server neutral
        -->
        <macros>
            <cluster>local</cluster>
            <shard>01</shard>
            <replica>clickhouse-node-1</replica> <!-- better - use the same as hostname  -->
        </macros>
    </yandex>
    ```

- **Step 3**: Start the Cluster

  - Run the following command:
    ```sh
      docker-compose up -d
    ```

- **Step 4**: **Verify the Setup**

  - Access the ClickHouse web interface on http://localhost:8123 for Node 1
  - login to clickhouse any one docker pod. It will show image name as clickhouse/clickhouse-server:24.8.7.41, use any one container ID to login
    ```sh
      docker exec -it <CONTAINER_ID> sh
    ```
  - login to clickhouse using below command (login to clickhouse container in docker for running this)
    ```sh
      clickhouse-client --password password
    ```
  - Run a query to check cluster status:
    ```sh
      SELECT * FROM system.clusters;
    ```

- **Step** : **Install ClickHouse Client**
  - Install clickhouse-client (https://clickhouse.com/docs/en/install)
    ```sh
      curl https://clickhouse.com/ | sh
    ```
  - Connect to clickhouse :
    ```sh
      ./clickhouse client --user transaction_user --password password
    ```

# docker-compose.yml File

- Here, we defined the services that we need to run our **Clickhouse** cluster.

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

# Resources and Further Reading

1. [clickhouse - Docker Image](https://hub.docker.com/_/clickhouse)
2. [Medium - Running a Clickhouse Distributed Multi Node Cluster Locally Using Docker Compose](https://archive.ph/9ptU6#selection-313.0-313.80)
