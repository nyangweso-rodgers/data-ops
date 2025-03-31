# Open Metadata

## Table Of Contents

# Overview Of Open Metadata

- It provides tools for **data discovery**, **lineage tracking**, **data quality monitoring**, **observability**, and **governance**, all built around a standardized metadata schema. The goal is to unlock the value of data by ensuring it is **well-documented**, **searchable**, and **accessible** to different personas like data scientists, analysts, and engineers.

- **Features of Open Metadata**:

  1. Centralized Metadata Store: A single place to store and manage metadata from diverse systems.
  2. Ingestion Framework: Connectors to pull metadata from 75+ sources (e.g., MySQL, Snowflake, Airflow, Tableau).
  3. Collaboration Tools: Features like task creation, conversations, and documentation within the platform.
  4. Data Lineage: Tracks how data flows and transforms across systems.
  5. Data Quality and Observability: Monitors data health with profiling and quality checks.

- **Use Cases of Open Metadata**
  1. Data Discovery: Helps users find relevant datasets by searching metadata, reducing time spent looking for data.
  2. Data Governance: Enforces policies, ownership, and security (e.g., integrating with SSO or role-based access control) to ensure compliance and proper data usage.
  3. Data Lineage Tracking: Provides visibility into data origins, transformations, and destinations, aiding in debugging and auditing.
  4. Data Quality Management: Allows profiling and setting up tests to ensure data reliability (e.g., checking for null values or anomalies).
  5. Collaboration: Enables teams to document, annotate, and discuss data assets, bridging gaps between technical and business users.
  6. Observability: Monitors data pipelines and assets for freshness, volume, and latency, with alerting capabilities.
  7. Integration with Tools: Connects to BI tools, databases, and orchestration systems to create a holistic view of the data ecosystem.

# Setup Open Metadata Using Docker

- **Key Components**:

  1. OpenMetadata Server: The core application handling APIs and UI.
  2. Database: MySQL or PostgreSQL for storing metadata (default in the compose file is MySQL).
  3. Elasticsearch: For indexing and searching metadata.
  4. Ingestion Service: Often powered by Apache Airflow to pull metadata from sources.

- **Step 1**:

- **Step 2**: Create `docker-compose.yml`
  - Connect to Postgres
    ```sh
      # create MySQL Database
    ```
  - Create Database and User:
    ```sh
      # create a MySQL Database for Open Metadata
      CREATE DATABASE open_metadata;
    ```
- Step : Build and Run

- **Step** : **Log in to OpenMetadata**

  - **OpenMetadata** provides a default admin account to login.
  - You can access **OpenMetadata** at `http://localhost:8585`. Use the following credentials to log in to **OpenMetadata**.
    - Username: `admin@open-metadata.org`
    - Password: `admin`
  - Once you log in, you can goto **Settings** -> **Users** to add another user and make them admin as well.

- **Step** : **Log in to Airflow**
  - **Apache Airflow** is utilized by **OpenMetadata** to orchestrate ingestion workflows.
  - **OpenMetadata** ships with an **Airflow container** to run the ingestion workflows that have been deployed via the UI.

# Resources and Further Reading

1. [Download the docker-compose.yml file from the release page](https://github.com/open-metadata/OpenMetadata/releases/tag/1.6.7-release)
