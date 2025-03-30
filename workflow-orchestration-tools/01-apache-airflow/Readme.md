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

# Installation Using Docker

- **Key Components**:
  1. **Scheduler**: The brain of **Airflow**. It schedules tasks based on the **DAG** definitions and their schedules, ensuring dependencies are respected.
  2. **Web Server**: A user-friendly interface (built with **Flask**) to visualize **DAGs**, check task statuses, trigger runs, and view logs.
  3. **Metadata Database**: Stores the state of tasks, DAGs, and configurations. Commonly uses **PostgreSQL**, **MySQL**, or **SQLite** (for testing).
  4. **Executor**: Determines how tasks are executed. Examples include:
     1. **SequentialExecutor**: Runs tasks one at a time (good for testing).
     2. **LocalExecutor**: Runs tasks in parallel on a single machine.
     3. **CeleryExecutor**: Distributes tasks across multiple worker nodes using Celery.
  5. **Workers**: In distributed setups (e.g., with **CeleryExecutor**), workers execute the tasks assigned by the **scheduler**.
  6. **DAGs**: The workflows themselves, written as Python scripts, defining tasks and their dependencies.

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
  - **Dependencies**: Add any Python packages your DAGs need (e.g., `pandas`, `sqlalchemy`).
    - `sqlalchemy` is a python library (an ORM and SQL toolkit) that **Airflow** uses to interact with its **metadata database**. It abstracts database operations, allowing **Airflow** to work with various database backends (PostgreSQL, MySQL, SQLite, etc.) without changing its core code.
  - **DAGs**: Optionally copy your DAG files into the container.

## Step 2: Create a `docker-compose.yaml`

- Create the `docker-compose.yaml` file with the following configurations:

  ```yml
  version: "3"

  services:
  ```

- **Remarks**:
  - `airflow` is the database name **Airflow** will use—create this in your Postgres instance if it doesn’t exist yet.
    - Connect to Postgres
      ```sh
        docker exec -it postgres-db psql -U ${POSTGRES_USER}
      ```
    - Create Database and User:
      ```sh
        CREATE DATABASE apache-airflow;
        CREATE USER airflow WITH PASSWORD 'airflow';
        GRANT ALL PRIVILEGES ON DATABASE airflow TO airflow;
      ```
- Note:
  - The `./airflow` directory from the host (the directory where the docker-compose file is located, specifically the airflow subfolder) is mounted to `/opt/airflow` inside the container. This is typically done to ensure that data can persist even after the container stops, or to provide additional data to the container at runtime.
  - Apache Airflow’s web interface, by default, runs on port `8080`, so this mapping allows you to access the Airflow web interface through the host machine’s IP address on port 8080.
- Compose up the YAML file (right click, select the compose up command).
- Check the status of the container in the Docker Desktop to see if it is running.
- Go to http://localhost:8080/
- On the first login; the username is `admin` and the password can be found in the `standalone_admin_password.txt` file.

# Installing Apache Airflow with Pip

- **Requirements**:

  1. Python 3.8 or higher: You can download it from [Python’s official website](https://www.python.org/downloads/windows/).
  2. **Pip**: Make sure you have pip, the Python package manager, installed.
  3. Windows 10 or higher
  4. **Windows Subsystem for Linux** (**WSL2**):
     - Allows you to run Linux commands and programs on a Windows OS.
     - It provides a Linux-compatible environment that runs natively on Windows, enabling users to use Linux command-line tools and utilities on a Windows machine.

- **Remarks**:

  - Why Installing **Apache Airflow** on a Windows Virtual Environment is Problematic: Apache Airflow isn't officially supported on Windows. Here's why:
    1. **Compatibility Issues**:
       - **Airflow** relies heavily on certain **POSIX-compliant** tools and libraries, which are native to Unix-like operating systems (Linux, macOS). Windows lacks some of these tools out of the box.
       - Examples:
         1. Airflow uses `fork()` in its process management, which doesn’t work natively on Windows.
         2. Some of its dependencies (like `pycparser` or `cgroups`) are hard to compile or are incompatible with Windows.
    2. **Dependency Management**:
       - Airflow has many dependencies that rely on native **C extensions**.
       - On Linux, these are compiled using tools like `gcc` (**GNU Compiler Collection**), which are readily available. Windows, however, needs something like **Microsoft Build Tools**, which can be challenging to set up correctly.
    3. **Subprocess Management**: Airflow's scheduler and worker processes rely on Unix-like behavior for managing subprocesses and inter-process communication. These mechanisms are either non-existent or work differently on Windows.
    4. **Windows-Specific Challenges**: Even if you manage to install **Airflow** using workarounds (e.g., Docker for Windows), running it natively is not ideal because of potential performance and stability issues.

- **Installing Apache Airflow on Windows with WSL**:

  1. **Step 1**: Activate Ubuntu or Other Linux System

     - If you haven’t already, make sure you’ve enabled **WSL** and installed a Linux distribution such as **Ubuntu** from the Microsoft Store.
     - Launch the Linux terminal to proceed.

  2. **Step 2**: Create a Virtual Environment and Activate It

     - To create a virtual environment, you can use Python’s built-in `venv` module. Navigate to your desired project directory and execute these commands:

       ```sh
         #Create virtual environment
         python3 -m venv airflow-env

         #Activate the virtual environment
         source airflow-env/bin/activate
       ```

  3. **Step 3**: Set the `$AIRFLOW_HOME` Parameter (Environment Variable)

     - Set the `$AIRFLOW_HOME` environment variable to specify where **Airflow** will store its configuration and metadata files. Add this line to your shell profile file (e.g., `.bashrc` or `.zshrc`)

       ```sh

       ```

     - Add it to your shell profile to make it persistent (e.g., `~/.bashrc`):

       ```bash
        echo "export AIRFLOW_HOME=/mnt/c/Users/hp/Downloads/working-env/data-ops/05-pipeline/01-apache-airflow/airflow_home" >> ~/.bashrc
        source ~/.bashrc
       ```

     - Here:
       - The first command appends the line that sets the `AIRFLOW_HOME` environment variable to your `~/.bashrc` file:
       - The second command reloads the `~/.bashrc` file so that the new environment variable is available in your current session:
     - Verify `$AIRFLOW_HOME`:
       ```sh
        echo $AIRFLOW_HOME
       ```

  4. **Step 4**: **Install Apache Airflow**

     - Use `pip` to install Apache Airflow

       ```sh
         pip install apache-airflow
       ```

  5. **Step 5**: **Initialize the Database**

     - Initialize the Airflow database, which is essential for storing metadata about your workflows:
       ```sh
        airflow db init
        # or, for future improvements
        airflow db migrate
       ```
     - This creates necessary files:
       1. `airflow.cfg` (configuration file)
       2. `airflow.db` (metadata database)
       3. `logs/` (Airflow logs folder)
       4. Other necessary directories (like `dags/` if you start adding **DAGs**).

  6. **Step 6**: **Create an Admin User**

     - To access the Airflow web interface, create an admin user with the following command:
       ```sh
        airflow users create --username admin --password admin  --firstname <YourFirstName> --lastname <YourLastName> --role Admin --email admin@example.com
       ```
     - Using **Docker Command** to create **user**:
       ```sh
        docker exec -it apache-airflow airflow users create --username admin --firstname Admin --lastname User --role Admin --email rodgerso65@gmail.com --password admin
       ```

  7. **Step 7**: **Run the Web Server and Scheduler**

     - Start the Airflow web server and scheduler components in separate terminals:

       ```sh
        airflow webserver --port 8080
        airflow scheduler
       ```

     - The Airflow web server will be accessible at http://localhost:8086 in your web browser and log in using the above-created User.
     - Go to http://localhost:8086/
     - On the first login; the **username** is `admin` and the **password** can be found in the `standalone_admin_password.txt` file.

- **Additonal Tips**:

  1. **Disable Example DAGs**:
     - In the Airflow configuration file (`airflow.cfg`), set `load_examples = False` to prevent the automatic loading of example **DAGs** during initialization. This can help keep your Airflow environment clean and focused on your specific use cases.
       ```sh
        load_examples = False
       ```
  2. **Configure the DAGs Directory**
     - In the Airflow configuration file (`airflow.cfg`), specify the location where your DAG files will reside. This allows you to organize your DAGs in a specific directory.
       ```sh
        dags_folder = ~/airflow/dags
       ```
  3. **Use a Reverse Proxy**:

     - If you plan to deploy Airflow in a production environment, consider setting up a reverse proxy like Nginx or Apache in front of the Airflow web server. This adds an extra layer of security and can help with performance and scalability.

  4. **Monitoring and Logging**

     - Configure logging and monitoring solutions to keep an eye on your Airflow instance. Tools like **Prometheus**, **Grafana**, or third-party services can provide insights into your workflow performance.

  5. **Backup and Recovery Plan**:
     - Regularly backup your Airflow metadata database to prevent data loss in case of system failures. Implement a recovery plan to restore your Airflow instance quickly.

# Creaing DAGs Uisng Python

- Step 1: Create `dags/` directory inside the `project-folder/`
  - Create a `test.py` file with the following:

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
