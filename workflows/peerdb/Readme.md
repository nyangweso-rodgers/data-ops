# peerDB

# Introduction to PeerDB

- Unlike many ETL tools that aim to support a wide variety of database connectors, **PeerDB** focuses exclusively on **PostgreSQL** as a data source. This specialisation has allowed the team to create one of the fastest and most scalable **CDC solutions for PostgreSQL**, with support for advanced features like complex data types and partitioned tables.
- In July 2024, **ClickHouse** acquired **PeerDB**. Since then, the integration between the two platforms has deepened, including the private preview of **PeerDB** integrated into **ClickHouse Cloud**. This strategic alignment makes PeerDB the natural choice when working with PostgreSQL and ClickHouse.

# Self Managed vs Fully Managed

- The first option is to use the [PeerDB open source distribution](https://www.peerdb.io/) and run it in a self hosted configuration on your own server. This can be used to send data from any Postgres database (including open source or AWS RDS) to either open source ClickHouse and ClickHouse Cloud.
- The second option is to use a fully managed version of PeerDB which is integrated and embedded into ClickHouse Cloud. In this instance, the solution is branded as PostgreSQL CDC for ClickPipes, though PeerDB is used behind the scenes.

# Core Concepts

## 1. CDC vs SQL Integration

- There are two primary options for extracting data from your source PostgreSQL database which are referred to as **CDC** and **Query Replication**.

  1. **CDC** (**Change Data Capture**) is a low level solution whereby **PeerDB** will source data by listening to a log of low level change events emitted from PostgreSQL.
  2. Query Replication:
     - The **Query Replication** route extracts data from the PostgreSQL source by periodically issuing a SQL query. This route allows you to do things like applying where clauses onto the query and carry out joins across multiple source tables. This route may also be necessary if your source table does not have a primary key.
     - The **Query Replication** route is much more flexible, but there are a few downsides.
       - Firstly, it will need to run as a periodic batch, whereas the CDC mechanism is streaming based and can be run at lower latency.
       - In addition, the Query Replication route would also add more load onto the source database than the CDC approach.

- **Remarks**:
  - With a fast analytical database like ClickHouse and the option of applying transformations within PeerDB, the go-to should be to stick to CDC to emit “low level” events, and do any transformation work within PeerDB or within ClickHouse away from your transactional application database.

# Resources and Further Reading

1. [Reliably Replicating Data Between PostgreSQL and ClickHouse Part 1 - PeerDB Open Source](https://benjaminwootton.com/insights/clickhouse-peerdb-cdc/?ref=dailydev)
