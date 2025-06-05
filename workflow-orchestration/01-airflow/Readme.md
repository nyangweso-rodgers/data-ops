# Apache Airflow

## Table Of Contents

# Setup

# Integrating dbt with Airflow

- **dbt** allows you to define SQL models (e.g., tables, views) in `.sql` files, which it compiles and executes against databases like PostgreSQL. **Airflow** can trigger dbt commands (e.g., `dbt run`) using operators like `DbtRunOperator` from the `astronomer-cosmos` package or `BashOperator` for simpler setups. The `dbt/` folder will contain `dbt` project, including **models**, **configurations**, and **profiles**.

# Creating DAGs Using Python

- **Components of DAG File**:

  1. **Imports** (**The Building Blocks**)

     - `DAG` is the core class that defines a workflow.
     - `PythonOperator`: Executes Python functions as tasks.
     - `LoggingMixin`: For proper Airflow logging (better than `print()`).
     - `PostgresHook`
     - `days_ago`

  2. **Default Arguments**

     - Defines task-level defaults:
       ```py
        default_args = {
          'owner': 'airflow',
          'depends_on_past': False,
          'email_on_failure': False,
          'email_on_retry': False,
          'retries': 1,
       }
       ```
     - `owner`: Labels tasks as owned by `airflow`.
     - `depends_on_past`: Tasks don’t wait for prior runs to succeed.
     - `email_on_failure/retry`: No emails (requires SMTP setup anyway).
     - `retries`: Tasks retry once if they fail.

  3. **Task Functions** (**The Workers**)

     - Example:
       ```py
        def print_greeting():
        print("Hello, Airflow enthusiasts!")
       ```
     - Each function represents a discrete unit of work.

  4. **DAG Definition** (**The Blueprint**)

     - Example:
       ```py
        dag = DAG(
          'dummy_dag', # Unique DAG ID
          default_args={'start_date': days_ago(1)},
          schedule_interval='*/5 * * * *',
          catchup=False
       )
       ```

  5. **Tasks** (**The Steps**)
     - Example:
       ```py
        print_greeting_task = PythonOperator(
        task_id='print_greeting',
        python_callable=print_greeting,
        dag=dag
       )
       ```

- **Examples DAGs For this Project**:

  1. `dummy_dag`
  2. `fetch-quote-and-sync-to-postgres-db`

     - **Purpose**: The **DAG** checks for a quotes table in the `users` database (via `postgres_default`), creates it if missing, fetches a random quote from `api.quotable.io`, and inserts it into the table.
     - **Schedule**: Runs daily (@daily).
     - **Tasks**: Two sequential tasks:
       1. `check_and_create_table`: Ensures the `quotes` table exists.
       2. `fetch_and_insert_quote`: Fetches and stores a quote.

## 3. Fetch and Sync Data From Postgres to ClickHouse

- **Dependecies**:
  1. `clickhouse_connect`
     - Install to Airflow Comtainer by:
       ```sh
        docker exec -it apache-airflow-webserver pip install clickhouse-connect
       ```
     - Or, Update `Dockerfile`
       ```Dockerfile
        RUN pip install clickhouse-connect
       ```
- Create a ClickHouse Connection in Apache Airflow UI
  - Access the Airflow Web UI on `http://localhost:8080`
  - Navigate to **Admin** > **Connections** and Create a New Connection by clicking the `+` button
  - Fill the connection details:
    - **Connection Id**: `clickhouse_default`
    - **Connection Type**: `HTTP` (Port `8123` is a ClickHouse’s HTTP interface. Airflow’s HTTP connection type aligns with this.Note that if we use the native TCP protocol, port `9000`, you could use `Generic` or a custom type)
    - **Host**: `clickhouse-server`
    - **Schema**: `default`
    - **Login**: `<clickhouse-username>`
    - **Password**: `<clickhouse-password>`
    - **Port**: `8123`
    - **Extra**: Leave blank (or optionally add `{"secure": false}`)
    - Save the Connection

# Schema-Driven Configuration

- YAML schema file (e.g., `accounts.yml`) defines source-to-target column mappings
- Dynamic schema validation ensures data compatibility
- Column aliasing (e.g., `parentAccountId` → `parent_account_id`)
- **Type conversion** handled automatically

# Creating Custom Hooks

1. `MySqlHook`: Wrapper around Airflow's MySQL hook with enhanced features
2. `PostgresHook`: Custom PostgreSQL hook with advanced upsert capabilities

# Example Custom Hooks

## 1. `postgres-hook.py`

- Functionality:

  1. **Connection Management**: Uses `psycopg2` with Airflow’s connection store (`_get_conn_params`, `get_conn`, `get_cursor`).
  2. **Table Management**: Supports `table_exists` and `create_table_if_not_exists`.
  3. **Query Execution**: Handles queries (`execute_query`) and bulk inserts (`insert_rows`).
  4. **Logging**: Robust logging with configurable levels via `LOG_LEVELS`.

- Available **Methods**:

  1. `test_connection() -> Tuple[bool, str]`:

     - **Use Case**: Verify that the database connection is working before performing operations.
     - **When to Use**: At the start of a DAG or task to ensure connectivity, especially for critical workflows.
     - **Example**: Check if the database is reachable before proceeding with data processing.

  2. `table_exists(table_name: str, schema: str = "public") -> bool`:

     - **Use Case**: Check if a table exists in the database.
     - **When to Use**: Before creating a table or inserting data to avoid errors or redundant operations.
     - **Example**: Ensure a target table exists before loading data.

  3. `create_table_if_not_exists(table_name: str, columns: List[str], schema: str = "public") -> bool`:

     - **Use Case**: Create a table with specified columns if it doesn’t already exist.
     - **When to Use**: To set up a table for data storage in an ETL pipeline.
     - **Example**: Create a table for storing user data if it’s not already present.

  4. `execute_query(query: str, params: Optional[Union[tuple, dict]] = None) -> Union[List[Any], int]`:

     - **Use Case**: Run arbitrary SQL queries, such as SELECT, UPDATE, DELETE, or custom operations.
     - **When to Use**: For fetching data, updating records, or performing operations not covered by other methods.
     - **Example**: Retrieve data for processing or update records based on a condition.

  5. `insert_rows(table_name: str, rows: List[Dict[str, Any]], schema: str = "public") -> int`:
     - **Use Case**: Perform bulk insertion of multiple rows into a table.
     - **When to Use**: To load large datasets efficiently into a table.
     - **Example**: Insert a batch of user records from an external source.

## 2. `mysql_hook.py`

## 3. `clickhouse_cloud_hook.py`

## 4. `jira_api_hook.py`

## 5. `ccs_api_hook.py`

# Architectures

## 1. Sync Customers from MySQL Database to ClickHouse

- The pipeline is schedule to do the following:

  1. Schema definition (YAML configuration)
  2. Source connectivity (MySQL hook)
  3. Target connectivity (ClickHouse hook)
  4. Schema validation and transformation (SchemaLoader)
  5. Orchestration (Airflow DAG)

- DAG Implementation:
  1. Schema validation
  2. Connection testing for both source and target
  3. Source table validation
  4. Data fetching with incremental logic
  5. Target table creation/validation
  6. Data insertion
  7. Task Dependecies

# DAGs

# Sync Jira Projects, Issues & Sprints to Postgres

- **Step 1**: Create `JiraApiHook` API Hook
  - Uses **Airflow Variables**: `jira_url`, `jira_email`, `jira_api_token`, `jira_project_keys`.
  - `fetch_sprints` retrieves sprints for all boards associated with `project_keys`, deduplicating by sprint ID.

## Creating the Sprint Sync DAG

- **Objective**: The DAG will:

  - Fetch all sprints (active, closed, future) for projects specified in `jira_project_keys` (e.g., `BSS`,`SD`,`EE`) using `JiraApiHook.fetch_sprints`.
  - Sync the data to the `jira.sprints` table in the `postgres_reporting_service` database, as defined in `SYNC_CONFIGS['jira_sprints_to_postgres']`.
  - Ensure the target table exists, creating it if necessary, based on `sprints.yml`.
  - Use bulk insertion via `PostgresHook.insert_rows` for efficiency.
  - Handle incremental syncs using `last_sync_timestamp` and the `complete_date` field.
  - Incorporate type checking/conversion from `JiraApiHook` (e.g., id as 123 → "123").

- **Schema**: Use the provided `sprints.yml` (path: `schemas/jira/jira/sprints.yml`).
- **Hook**: Use `JiraApiHook` from `plugins/hooks/jira/v2.py`
- **Sync Config**: Define `jira_sprints_to_postgres` in `SYNC_CONFIGS` with source (`Jira`) and target (`PostgreSQL`) details.
- **Incremental Sync**: Filter sprints by `complete_date` using a stored `last_sync_timestamp`.
- **Table Management**: Create or update the PostgreSQL table based on the schema’s targets.postgres.
- **Utilities**:

  1. `SchemaLoader.load_schema` to load `sprints.yml`
  2. `add_sync_time` to add `sync_time` to records (assumed to append `datetime.now()`).
  3. `PostgresHook` for database operations.

- **Constants**: Use `DEFAULT_ARGS`, `CONNECTION_IDS`, and `LOG_LEVELS` from `constants.py`.

# Resources and Further Reading

1.
