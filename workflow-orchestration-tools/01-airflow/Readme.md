# Apache Airflow

## Table Of Contents

# Introduction to Apache Airflow

- **Apache Airflow** is an open-source tool for orchestrating complex computational workflows and pipelines. It is designed to help us programmatically author, schedule, and monitor workflows in a way that is scalable and maintainable.

- **Advantages**:

  1. It is flexible, allowing users to define workflows as code.
  2. Workflows are defined in Python.
  3. It allows scaling horizontally on multiple machines.
  4. It provides a web-based UI that makes it easy to visualize pipelines running in production, monitor progress, and troubleshoot issues
  5. It benefits from a strong community that contributes a wealth of plugins and integrations.

- **Use Cases of Apache Airflow**:

  1. Batch data processing (ETL workflows).
  2. Scheduling machine learning model training.
  3. Running scripts or jobs on a regular basis.
  4. Coordinating tasks across multiple systems.

- **Features**:

  1. **DAG** (**Directed Acyclic Graphs**):
     - Are the key features of **Apache Airflow**.
     - **Workflows** are defined as **DAGs**.
     - A **DAG** is a directed graph with no directed cycles. It represents a collection of all the tasks you want to run, organized in a way that reflects their relationships and dependencies.
       - Each edge in the graph has a direction, which indicates the order of task execution. This directionality ensures that a task that depends on another can only start once its prerequisite task has completed successfully.
       - The graph must have no cycles (**acyclic**). This means you cannot go back to a task that was already executed, ensuring no infinite loops and that there is a finite end to the workflow.
       - The tasks and their dependencies are modeled as a graph, where nodes represent tasks and edges represent dependencies between these tasks.

- **Airflow Architecture**
  - **Apache Airflow** features a modular architecture that is built around the concept of a **scheduler**, **executor**, and **workers** that execute tasks defined in **DAGs**.
  - **Web Server**: Provides the web-based UI built using **Flask**. It allows users to monitor and manage their workflows, view logs, and track the progress and history of **DAGs**.
  - **Scheduler**: The heart of Airflow, responsible for scheduling tasks. It continuously polls the state of tasks and DAGs, and triggers task instances whose dependencies have been met. The scheduler is designed to ensure that the right tasks run at the right time or in response to an external trigger.
  - **Metadata Database**: Airflow uses a backend database to store state and metadata about the workflows. Common databases used include PostgreSQL and MySQL. This database records credentials, connections, history, and job states.
  - **Executor**: Responsible for running the tasks that the scheduler pushes to it. There are different types of executors in Airflow:
    1. **LocalExecutor**: Executes tasks with parallelism on the same machine.
    2. **CeleryExecutor**: Uses Celery, a distributed task queue, to distribute tasks across multiple workers.
    3. **KubernetesExecutor**: Runs each task in a separate pod in a Kubernetes cluster, providing dynamic scaling and isolation.
    4. **SequentialExecutor**: A simpler executor that runs one task at a time. Useful for development and testing.
  - **Workers**: These are the processes that actually execute the logic of tasks once they are scheduled. Their nature depends on the type of executor used.

# Apache Airflow Concepts

## 1. Operators

- **Operators** are the building blocks of a **DAG**; they represent a single, ideally idempotent, unit of work. Each **operator** in **Airflow** is designed to do one specific thing, and they can be extended to handle virtually any type of job, whether it involves running a **Python function**, **executing a SQL query**, **managing a Docker container**, **sending an email**, or more.

- **Airflow** comes with many built-in **operators**, which can be categorized into different types such as:

  1. **Action Operators**

     - Perform a specific action, like the `PythonOperator` for executing Python code, `BashOperator` for running **Bash scripts**, or `EmailOperator` for sending emails.

  2. **Transfer Operators**

     - Move data from one system to another, such as `S3ToRedshiftOperator`, which copies data from **Amazon S3** to a **Redshift database**.

  3. **Sensor Operators**
     - Wait for a certain condition or event before proceeding, like the `HttpSensor` that waits for a specific **HTTP** endpoint to return a certain result before moving forward.

## 2. Tasks

- **Tasks** are instances of **operators**; they represent the application of an operator’s logic to a specific set of input parameters or configurations. When you define a task in a **DAG**, you’re specifying what **operator** to use and configuring it to perform its function in a particular way, tailored to your workflow.

## 3. Connections

- **Connections** are **Airflow’s** way of storing and managing credentials and configuration details for external systems in a centralized, reusable manner. Instead of hardcoding things like **database hostnames**, **usernames**, or **passwords** in your **DAGs**, you define them once as a **Connection** and reference them by a unique identifier (`conn_id`). This keeps your code clean, secure, and easy to update.
- A **Connection** is a record with these key fields:

  1. **Conn ID**: Unique name (e.g., `postgres_default`).
  2. **Conn Type**: Type of system (e.g., `Postgres`, `HTTP`, `AWS`).
  3. **Host**: Server address (e.g., `postgres-db`).
  4. **Schema**: Database name (e.g., `apache_airflow`, `users`).
  5. **Login**: Username (e.g., `postgres`).
  6. **Password**: Password
  7. **Port**: Port number (e.g., `5432`).
  8. **Extra**: Optional JSON for additional settings (e.g., `{"sslmode": "require"}`).

- **Managing Connections**

  1. **Via UI**

     - Go to `http://localhost:8086` > **Admin** > **Connections**.
     - Click `+` to add or edit existing ones.

  2. **Via CLI**

     - Add a Connection:
       ```sh
        docker exec -it apache-airflow-webserver airflow connections add \
          --conn-id postgres_users_db \
          --conn-type postgres \
          --conn-host postgres-db \
          --conn-schema <database_name> \
          --conn-login <user> \
          --conn-password <password> \
          --conn-port 5432
       ```
     - List Connections:
       ```sh
         docker exec -it apache-airflow-webserver airflow connections list
       ```

  3. **Via Environment Variables**
     - Define a Connection as a JSON string in `.env`
     ```env
       AIRFLOW_CONN_POSTGRES_USERS_DB=postgresql://postgres:<password>@postgres-db:5432/<database_name>
     ```
     - **Airflow** loads it on startup. Useful for automation but less flexible than UI/CLI.

- **How Airflow Uses Connections**

  1. **Metadata Storage**: **Connections** are encrypted (using the `FERNET_KEY`) and stored in the `connection` table in `apache_airflow` db. Check it by:
     ```sh
      docker exec -it postgres-db psql -U postgres -d apache_airflow -c "SELECT * FROM connection;"
     ```
  2. **Hooks**: `PostgresHook` fetches the **Connection** by `conn_id`, decrypts it, and builds the connection string.
  3. **Operators**: Some operators (e.g., `PostgresOperator`) also use Connections directly.

- **Best Practices**

  1. **Naming**: Use descriptive `conn_ids` (e.g., `postgres_users_db` > `my_db`).
  2. **Separation**: Keep metadata (`postgres_default`) separate from app data (`postgres_users_db`).
  3. **Secrets**: For production, use Airflow’s Secrets Backend (e.g., **HashiCorp Vault**) instead of storing passwords in **Connections**.
  4. **Testing**: Always test Connections in the UI to catch typos early.

- **Example Connections**
  1. Adding MySQL RDS Connection
  2. Setting Up MySQL Connection in AirFlow
     - Step 1: Add MySQL Provider in Airflow
       - Install `apache-airflow-providers-mysql` in Docker container.
       - Verify in **Admin** > **Providers**.
     - Step 2: Configure MySQL RDS Connection in Airflow
       - Add a connection (mysql_rds_prod) via UI or CLI.
       - Secure credentials

## 4. Configurations

- The **Configurations** page in the Airflow UI (under **Admin** > **Configurations**) is meant to display the contents of `airflow.cfg` (Airflow’s main configuration file) and environment variables used by Airflow. It allows admins to view settings like database connections, scheduler options, or SMTP details
- `airflow.cfg` and environment variables may contain sensitive data, such as
  1. Database credentials.
  2. SMTP passwords
  3. API keys, tokens, or other secrets.
- Exposing these in the UI could allow anyone with admin access to view them, posing a security risk, especially in multi-user or public-facing setups.

## 5. Providers

- The **Providers** page in the Airflow UI (**Admin** > **Providers**) lists all installed **Airflow provider packages**, which are modular extensions that add functionality like **hooks**, **operators**, and **connections** for external systems (e.g., PostgreSQL, ClickHouse). Unlike the **Configurations** page, which is restricted by `expose_config`, the **Providers** page is always accessible to admin users because it doesn’t expose sensitive data—just metadata about installed packages. It shows the following:

  1. **Package Name**

     - The name of the provider package, e.g., `apache-airflow-providers-postgres`, `apache-airflow-providers-http`.
     - Each package corresponds to a specific integration (e.g., `postgres` for your `postgres_users_db`, `http` for ClickHouse’s HTTP interface).

  2. **Version**

     - The installed version of the provider, e.g., `5.8.0` for `apache-airflow-providers-postgres`.
     - Matches the version installed in the Docker container (via `pip` or Airflow’s constraints).

  3. **Description**
     - A brief summary of the provider’s purpose, e.g., “PostgreSQL provider for Apache Airflow” or “HTTP provider for Apache Airflow”.
     - Helps identify what each package enables.

- Examples

  1. `apache-airflow-providers-postgres`: Enables `PostgresHook` for connecting to Postgres server
     ```py
      from airflow.providers.postgres.hooks.postgres import PostgresHook
     ```
  2. `apache-airflow-providers-http`

     - Listed as `apache-airflow-providers-http`

  3. `apache-airflow-providers-common-sql`
     - Provides base SQL functionality for `PostgresHook`.
     - Listed as `apache-airflow-providers-common-sql`.

## 6. Pools

- The **Pools** page in the Airflow UI (**Admin** > **Pools**) allows you to view and manage resource pools, which are used to limit the number of tasks that can run concurrently for specific resources or DAGs. **Pools** help control parallelism, preventing overloading of systems like databases or external services.
- When you click **Admin** > **Pools**, you typically see a table with columns:
  1. **Pool**: The name of the pool (e.g., `default_pool`).
  2. **Slots**: The total number of slots (task instances) allowed to run concurrently.
  3. **Used Slots**: How many slots are currently in use (running tasks).
  4. **Queued Slots**: How many tasks are waiting for a slot.
  5. **Open Slots**: Available slots (`Slots - Used Slots - Queued Slots`).
  6. **Description** (optional): A note about the pool’s purpose.

# Setup Apache Airflow With Docker

- **Key Components**:

  1. **Scheduler**: The brain of **Airflow**. It schedules tasks based on the **DAG** definitions and their schedules, ensuring dependencies are respected.
  2. **Web Server**: A user-friendly interface (built with **Flask**) to visualize **DAGs**, check task statuses, trigger runs, and view logs.
  3. **Executor**: Determines how tasks are executed. Examples include:
     1. **SequentialExecutor**: Runs tasks one at a time (good for testing).
     2. **LocalExecutor**: Runs tasks in parallel on a single machine.
     3. **CeleryExecutor**: Distributes tasks across multiple worker nodes using Celery.
  4. **Workers**: In distributed setups (e.g., with **CeleryExecutor**), workers execute the tasks assigned by the **scheduler**.
  5. **DAGs**: The workflows themselves, written as Python scripts, defining tasks and their dependencies.

- **Requirements**:

  1. **Metadata Database**

     - **Airflow** uses a **relational database** (referred to as the **metadata database**) to store information about:
       1. **DAGs** (**Directed Acyclic Graphs**): **Definitions**, **schedules**, and **configurations** of your workflows.
       2. **Task Instances**: Execution history, status (e.g., running, success, failed), and retry information for each task.
       3. **Variables and Connections**: Key-value pairs and connection credentials (e.g., to databases, APIs) used in your workflows.
       4. **Scheduler State**: Information about when tasks should run and their dependencies.
       5. **User Data**: Details about **users** and **roles** (e.g., your admin user) if authentication is enabled.

  2. **Dockerfile**

     - Custom Airflow image with additional dependencies and an initialization script.

  3. **Init Script** (`init-airflow.sh`)
     - Handles **database creation**, **schema initialization**, and **admin** user setup.

## Step 1: Created `Dockerfile`

- Create a Dockerfile with the following configuration:

  ```Dockerfile
    # Use the official Airflow image as a base
    FROM apache/airflow:2.8.1

    # Switch to airflow user (default in the image)
    USER airflow

    # Install additional Python dependencies (if needed)
    RUN pip install --no-cache-dir \
        pandas \
        sqlalchemy

    # Copy your DAGs or custom files (optional)
    COPY ./dags /opt/airflow/dags
  ```

- **Remarks**:
  - **Base Image**: `apache/airflow:2.8.1` is the latest stable version as of now (March 29, 2025).
  - **Dependencies**: Add any Python packages your **DAGs** need (e.g., `pandas`, `sqlalchemy`).
    - `sqlalchemy` is a python library (an ORM and SQL toolkit) that **Airflow** uses to interact with its **metadata database**. It abstracts database operations, allowing **Airflow** to work with various database backends (**PostgreSQL**, **MySQL**, **SQLite**, etc.) without changing its core code.
  - **DAGs**: Optionally copy your **DAG** files into the container.

## Step 2: Create a `docker-compose.yaml`

- Create the `docker-compose.yaml` file with the following configurations:

  ```yml
  version: "3"

  services:
  ```

- **Environment Variables**:

  1. `AIRFLOW__DATABASE__SQL_ALCHEMY_CONN`: defines the connection string for Apache Airflow’s **metadata database**. This database stores all the essential data **Airflow** needs to manage workflows, **track task execution**, and **maintain its state**. This database is accessed via **SQLAlchemy**, a Python ORM (Object-Relational Mapping) library that **Airflow** uses to interact with the database in a database-agnostic way. The connection string tells **Airflow** how to connect to this database. Example:
     ```sh
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres-db:5432/apache_airflow
     ```

- **Remarks**:
  - `airflow` is the database name **Airflow** will use — create this in your Postgres instance if it doesn’t exist yet.
    - Connect to Postgres
      ```sh
        docker exec -it postgres-db psql -U ${POSTGRES_USER}
      ```
    - Create Database and User:
      ```sh
        CREATE DATABASE apache_airflow;
      ```

## Step 3: Start Docker Containers

- **Remarks**:

  - When you start **Airflow** containers, you will nptice that `__pycache__/01-dummy-dag.cpython-38.pyc` file is automatically created because Python compiles your **DAG** file (e.g., `01-dummy-dag.py`) into bytecode for faster execution.

    - When Python imports a module (like your `DAG` file), it compiles the `.py` file into bytecode (`.pyc`) and caches it in `__pycache__/`.
    - This makes subsequent imports faster since Python doesn't need to re-parse the source code.
    - Add `__pycache__/ `to your `.gitignore`

  - **Airflow's Behavior**
    - **Airflow** scans and imports your DAG files every few seconds (default: 30s).
    - Each scan triggers Python's import system, generating the .pyc file.

## Step : Testing

- List DAGS:
  ```sh
    docker exec apache-airflow-webserver airflow dags list
  ```

# Integrating dbt with Airflow

- **dbt** allows you to define SQL models (e.g., tables, views) in `.sql` files, which it compiles and executes against databases like PostgreSQL. **Airflow** can trigger dbt commands (e.g., `dbt run`) using operators like `DbtRunOperator` from the `astronomer-cosmos` package or `BashOperator` for simpler setups. The `dbt/` folder will contain `dbt` project, including **models**, **configurations**, and **profiles**.

# Creating DAGs Uisng Python

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

# Resources and Further Reading

1. [Medium - How to easily install Apache Airflow on Windows?](https://vivekjadhavr.medium.com/how-to-easily-install-apache-airflow-on-windows-6f041c9c80d2)
2. [Medium - Getting started with Apache AirFlow for Data Workflows](https://archive.ph/uqajQ#selection-1527.0-1531.90)
