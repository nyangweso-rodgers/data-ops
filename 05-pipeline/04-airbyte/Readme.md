# Airbyte

## Table of Contents

# Airbyte

- **Airbyte** is an open-source data integration platform designed to help you consolidate data from various sources into your data warehouses, lakes, and databases.
- **Airbyte** is an open-source data integration platform that aims to standardize and simplify the process of Extraction and Loading. **Airbyte** operates on the principle of **ELT**, it simply extracts raw data and loads it to destinations, optionally it allows us to do transformation. Transformations are decoupled from the **EL** phase. It simplifies this process by building **connectors** between **data sources** and **destinations**. It is a plugin-based system where you can quickly your own customized connecter using the Airbyte CDK.

- **Features of Airbyte**:

  1. Open source
  2. 170+ connectors and 25+ Destinations
  3. Support custom connectors
  4. Built-in scheduler to allow for varied Sync frequency
  5. Integration with **airflow** and **dbt**
  6. Available on the K8s platform
  7. Octavia-cli with YAML template for deployments
  8. Support for near real-time CDC

- **Limitations**:
  1. Not any stable release, still in Alpha
  2. Lack of IAM Role-based auth on AWS services, currently it asks for KEYS
  3. Lack of native support for **Prometheus**, it has Open Telemetry recently added.
  4. Lack of support for User Access Management
  5. Not battle-tested in production can get slow after 2k concurrent jobs.
  6. No support for replaying a specific execution instance of a job

# Setup

## Requirements

1. Temporal Service
   - Temporal is a workflow orchestration engine used by Airbyte to manage data synchronization tasks.
   - The Temporal service is designed to support multiple database backends (e.g., **Cassandra**, **MySQL**, **PostgreSQL**) and other configurations (e.g., **Elasticsearch** for visibility)
2. Airbyte Worker
3. Airbyte Server
4. Airbyte Weapp

# Resources and Further Reading
