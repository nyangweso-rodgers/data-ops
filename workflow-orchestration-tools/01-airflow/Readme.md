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

# Installing Apache Airflow on Linux

1. **Step 1**: Setup Python Virtual Environment on **Linux**/**WSL**

2. **Step 2**: Install Apache Airflow
   ```sh
    pip install apache-airflow
   ```

- **Remarks**:
  - Installing **Apache Airflow** on a **Windows Virtual Environment** is Problematic because **Apache Airflow** isn't officially supported on **Windows**. Here's why:
    - Compatibility Issues
      - **Airflow** relies heavily on certain **POSIX-compliant** tools and libraries, which are native to Unix-like OS (Linux, macOS). Windows lacks some of these tools out of the box.
      - Examples:
        - Airflow uses `fork()` in its process management, which doesn’t work natively on Windows.
        - Some of its dependencies (like `pycparser` or `cgroups`) are hard to compile or are incompatible with Windows.
    - Dependency Management: Airflow has many dependencies that rely on native **C extensions**. On **Linux**, these are compiled using tools like **gcc** (**GNU Compiler Collection**), which are readily available. Windows, however, needs something like **Microsoft Build Tools**, which can be challenging to set up correctly.
    - Subprocess Management: Airflow's scheduler and worker processes rely on Unix-like behavior for managing subprocesses and inter-process communication. These mechanisms are either non-existent or work differently on Windows.
    - Windows-Specific Challenges: Even if you manage to install Airflow using workarounds (e.g., Docker for Windows), running it natively is not ideal because of potential performance and stability issues.

# Creating DAGs Uisng Python

- Step 1: Create `dags/` directory inside the `project-folder/`

  - Create a `test.py` file with the following:

- **Components of DAG File**:

  1. **Imports** (**The Building Blocks**)

     - `DAG` is the core class that defines a workflow.
     - `PythonOperator`: Executes Python functions as tasks.
     - `LoggingMixin`: For proper Airflow logging (better than `print()`).

  2. **Task Functions** (**The Workers**)

     - Example:
       ```py
        def print_greeting():
        print("Hello, Airflow enthusiasts!")
       ```
     - Each function represents a discrete unit of work.

  3. **DAG Definition** (**The Blueprint**)

     - Example:
       ```py
        dag = DAG(
          'dummy_dag', # Unique DAG ID
          default_args={'start_date': days_ago(1)},
          schedule_interval='*/5 * * * *',
          catchup=False
       )
       ```

  4. **Tasks** (**The Steps**)
     - Example:
       ```py
        print_greeting_task = PythonOperator(
        task_id='print_greeting',
        python_callable=print_greeting,
        dag=dag
       )
       ```

# Operators & Tasks

- **Operators** are the building blocks of a **DAG**; they represent a single, ideally idempotent, unit of work. Each **operator** in **Airflow** is designed to do one specific thing, and they can be extended to handle virtually any type of job, whether it involves running a Python function, executing a SQL query, managing a Docker container, sending an email, or more.
- **Tasks** are instances of **operators**; they represent the application of an operator’s logic to a specific set of input parameters or configurations. When you define a task in a **DAG**, you’re specifying what **operator** to use and configuring it to perform its function in a particular way, tailored to your workflow.
- **Airflow** comes with many built-in **operators**, which can be categorized into different types such as:

  1. **Action Operators**: Perform a specific action, like the `PythonOperator` for executing Python code, `BashOperator` for running **Bash scripts**, or `EmailOperator` for sending emails.

  2. **Transfer Operators**: Move data from one system to another, such as:

     1. `S3ToRedshiftOperator`, which copies data from **Amazon S3** to a **Redshift database**.

  3. **Sensor Operators**: Wait for a certain condition or event before proceeding, like the `HttpSensor` that waits for a specific HTTP endpoint to return a certain result before moving forward.

# Resources and Further Reading

1. [Medium - How to easily install Apache Airflow on Windows?](https://vivekjadhavr.medium.com/how-to-easily-install-apache-airflow-on-windows-6f041c9c80d2)
2. [Medium - Getting started with Apache AirFlow for Data Workflows](https://archive.ph/uqajQ#selection-1527.0-1531.90)
