# Open Metadata

## Table Of Contents

# Overview Of Open Metadata

- It provides tools for **data discovery**, **lineage tracking**, **data quality monitoring**, **observability**, and **governance**, all built around a standardized metadata schema. The goal is to unlock the value of data by ensuring it is **well-documented**, **searchable**, and **accessible** to different personas like data scientists, analysts, and engineers.

- **Features of Open Metadata**:

  1. Centralized Metadata Store: A single place to store and manage metadata from diverse systems.
  2. **Add descriptions**: You can define the owner and add descriptions to the data which will help you identify the authenticity and thr owner details whenever needed.
  3. Ingestion Framework: Connectors to pull metadata from 75+ sources (e.g., MySQL, Snowflake, Airflow, Tableau).
  4. Collaboration Tools: Features like task creation, conversations, and documentation within the platform.
  5. Data Lineage: Tracks how data flows and transforms across systems i.e., You can look for the data lineage and the source from where its been generated and all the way to where it is consumed.
  6. **Data Quality and Observability**: Monitors data health with **profiling** and **quality checks**.
  7. **Profiling the data**:
     - You can view the details for each of the columns and the check null or non null value counts which can help you build your trust with the data.

- **Use Cases of Open Metadata**
  1. **Data Discovery**: Helps users find relevant datasets by searching metadata, reducing time spent looking for data.
  2. **Data Governance**: Enforces policies, ownership, and security (e.g., integrating with SSO or role-based access control) to ensure compliance and proper data usage.
  3. **Data Lineage Tracking**: Provides visibility into data origins, transformations, and destinations, aiding in debugging and auditing.
  4. **Data Quality Management**: Allows profiling and setting up tests to ensure data reliability (e.g., checking for null values or anomalies).
  5. **Collaboration**: Enables teams to document, annotate, and discuss data assets, bridging gaps between technical and business users.
  6. **Observability**: Monitors data pipelines and assets for freshness, volume, and latency, with alerting capabilities.
  7. **Integration with Tools**: Connects to BI tools, databases, and orchestration systems to create a holistic view of the data ecosystem.

# Setup Open Metadata Using Docker

- **Key Components**:

  1. OpenMetadata Server: The core application handling APIs and UI.
  2. Database: MySQL or PostgreSQL for storing metadata (default in the compose file is MySQL).
  3. Elasticsearch: For indexing and searching metadata.

  4. **Ingestion Service**
     - The `open-metadata-ingestion` service is essentially an Airflow instance pre-configured with the `openmetadata-managed-apis` plugin, designed to handle ingestion workflows (e.g., metadata extraction, lineage, and test connections) triggered from the OpenMetadata UI.
     - **Features** include:
       - **Metadata Collection**: Automatically pulls metadata from data sources
       - **Scheduled Pipelines**: Regular metadata updates without manual intervention
       - **UI-Driven Configuration**: Set up connectors through the web interface
       - **Workflow Management**: Handles dependencies between metadata jobs
     - Without Ingestion Service
       - You'd need to manually create and maintain **Airflow DAGs**
       - No UI for configuring data source connections
       - Limited automation capabilities

- **Step 1**:

- **Step 2**: Create `docker-compose.yml`
  - Access the Container: Run the following command from your host machine (where mysql-db is the container name from your docker-compose.yml):
    ```sh
      docker exec -it mysql-db mysql -u root -p
    ```
  - Create Database and User:
    ```sh
      # create a MySQL Database for Open Metadata
      CREATE DATABASE open_metadata;
    ```
- Step : Build and Run

- **Step 3** : **Log in to OpenMetadata**

  - **OpenMetadata** provides a default admin account to login.
  - You can access **OpenMetadata** at `http://localhost:8585`. Use the following credentials to log in to **OpenMetadata**.
    - Username: `admin@open-metadata.org`
    - Password: `admin`
  - Once you log in, you can goto **Settings** -> **Users** to add another user and make them admin as well.

- **Step 4** : **Adding the Database Service**
  - Open the OpenMetadata UI: `http://localhost:8585`
  - Login with `admin`:`admin`
  - Go to **Settings** > **Services** > **Databases** > **Add New Service**.
  - Configure:
    - Service Name: `PostgresDB`
    - Service Type: `Postgres`
    - Host and Port: `postgres-db:5432`
    - Username: `postgres`
    - Password: `password`
    - SSL Mode: `disable`
  - Click **Test Connection**
  - **Remarks**:
    - The `open-metadata-ingestion` service (an Airflow instance with `openmetadata-managed-apis`):
      1. **Received the Test Request**: When you clicked "**Test Connection**" in the UI, `open-metadata-server` sent a request to `open-metadata-ingestion` via `http://open-metadata-ingestion:8080`.
      2. **Generated a DAG**: It created a temporary DAG (e.g., `test-connection-Postgres-<random-id>`) to verify connectivity to `postgres-db:5432`.
      3. **Executed the DAG**: The Airflow scheduler ran the **DAG**, and the result was sent back to the UI, confirming success.

# Ingestion

- Two common alternatives for **ingestion**:

  1. Run a dedicated `ingestion` container

     - This acts as a background worker, picking up ingestion workflows triggered from the UI.
     - Enables a low-code/no-code ingestion experience directly from **OpenMetadata**.

  2. Use **Apache Airflow**
     - You can write DAGs that call OpenMetadata’s ingestion scripts via Python or CLI.
     - Great for version-controlled, scheduled, reproducible ingestion.
     - Ideal if you want to integrate ingestion into a broader data pipeline or orchestration layer.

- Remarks:
  - The `open-metadata-ingestion` service is essentially an **Airflow** instance managed by **OpenMetadata** for running ingestion workflows

## Step : Run the Ingestion from Airflow

- **OpenMetadata** integrates with **Airflow** to orchestrate ingestion workflows. You can use **Airflow** to extract metadata and [deploy workflows] (/deployment/ingestion/openmetadata) directly.
- **Dependecies**

  - **OpenMetadata** requires specific **Airflow** providers and Python packages to enable ingestion workflows.
  - Update `Dockerfile` to include the **OpenMetadata Airflow APIs** package:

    ```Dockerfile
      FROM apache/airflow:2.9.0

      # Switch to root for installing system dependencies
      USER root

      RUN apt-get update && apt-get install -y \
          default-libmysqlclient-dev \
          build-essential \
          && apt-get clean

      # Switch back to airflow user for installing Python packages and runtime
      USER airflow
      RUN pip install --no-cache-dir \
          apache-airflow-providers-mysql==5.6.0 \
          mysqlclient==2.2.4 \
          psycopg2-binary==2.9.9 \
          connexion[swagger-ui] \
          requests==2.31.0 \
          clickhouse-connect==0.7.0 \
          openmetadata-managed-apis==1.6.7

      # Back to root to copy and chmod the script
      USER root
      COPY ./scripts/init-airflow.sh /opt/airflow/init-apache-airflow.sh
      RUN chmod +x /opt/airflow/init-apache-airflow.sh

      # Back to airflow user and set entrypoint
      USER airflow
      ENTRYPOINT ["/opt/airflow/init-apache-airflow.sh"]
    ```

  - **Access Airflow UI**

    - Open `http://localhost:8080` (or the port defined in `APACHE_AIRFLOW_PORT`) and log in with the credentials from `APACHE_AIRFLOW_ADMIN_USERNAME` and `APACHE_AIRFLOW_ADMIN_PASSWORD`.

  - **Access OpenMetadata UI**
    - Open `http://localhost:8585` and log in (default credentials are typically admin/admin unless customized).

- We have different classes for different types of workflows.
- For example, for the `Metadata` workflow we'll use:

  ```py
    import yaml

    from metadata.workflow.metadata import MetadataWorkflow

    def run():
        workflow_config = yaml.safe_load(CONFIG)
        workflow = MetadataWorkflow.create(workflow_config)
        workflow.execute()
        workflow.raise_from_status()
        workflow.print_status()
        workflow.stop()
  ```

  - The classes for each workflow type are:
    1. `Metadata`: `from metadata.workflow.metadata import MetadataWorkflow`
    2. `Lineage`: `from metadata.workflow.metadata import MetadataWorkflow` (same as **metadata**)
    3. `Usage`: `from metadata.workflow.usage import UsageWorkflow`
    4. `dbt`: `from metadata.workflow.metadata import MetadataWorkflow`
    5. `Profiler`: `from metadata.workflow.profiler import ProfilerWorkflow`
    6. `Data Quality`: `from metadata.workflow.data_quality import TestSuiteWorkflow`
    7. `Data Insights`: `from metadata.workflow.data_insight import DataInsightWorkflow`
    8. `Elasticsearch Reindex`: `from metadata.workflow.metadata import MetadataWorkflow` (same as **metadata**)

# Resources and Further Reading

1. [Download the docker-compose.yml file from the release page](https://github.com/open-metadata/OpenMetadata/releases/tag/1.6.7-release)
2. [github.com - openmetadata-retention](https://github.com/open-metadata/openmetadata-retention)
