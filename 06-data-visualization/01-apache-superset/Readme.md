# Apache Superset

## Table Of Contents

# Apache Superset

- **Apache Superset** as its name, coming from Apache Software Foundation, which is a non-organization profit that focus on open-source project software. It is the top-level project licensed by Apache 2.0.
- Superset provides non-code interface for building charts. However, it is included SQL query that can save data in Superset database table that can be used for data visualization too.

# Unique Functions in Superset

1. Superset Database with SQL Query

   - Data from many sources include PostgreSQL, Google BigQuery, and Amazon Redshift can be saved in Superset Database. It is provided by Superset that can make the user collecting many sources. The data can be shown in the SQL Query which can make the datasets connected each other. The connected datasets that created by SQL Query have to be saved as a table if the user want to use it as data visualization. The user can save the SQL Query too for later used which may be the user want to edit part of query to create another table later.

2. A Table for A Data Visualization
   - Using SQL Query if you want to combine many tables is required. Superset only accepts one table for one data visualization. It is shown all tables that saved in Superset Database, but the visualization only accept one table. Therefore, if the user wants to use data from many tables that connect many tables, the user has to create the table and save it in Superset Database first before creating data visualization or the user only use the table for the visualization itself and then combine with another visualization in a dashboard to make a comprehensive data insight.

- Features of Apache Superset

  1. Supports 40+ visualizations from simple line charts to highly detailed geospatial charts
  2. Able to access many SQL and NoSQL databases
  3. Admin panel available with very detailed settings, including users and roles privileges
  4. Able to cache data for dashboard visualizations

- Remarks:
  - Superset is designed to handle datasets of any size since it operates as a thin layer on top of your databases, which manage all the data processing. The platform’s performance is more dependent on user activity and the number of users rather than the data size. A setup with 8 GB RAM and 2vCPUs is sufficient for a moderate user base.

# Setup

1. **Requirements**

   - Since **Python 3.11** is stable and works with **Superset**, it's the best choice for setting up **superset**. Eventually, when all dependencies are updated, Superset will support Python 3.12.
   - **Remarks**:
     - **Apache Superset** cannot be installed using **Python 3.12** because some of its dependencies rely on older Python features that were removed in **Python 3.12**.
     - **Superset** (or its dependencies, like `setuptools` or `pkg_resources`) still expects `pkgutil.ImpImporter`, which was deprecated in **Python 3.10** and removed in **Python 3.12**
     - When **Superset** (or its dependencies) tries to use `pkgutil.ImpImporter`, you get this error:
       ```sh
        AttributeError: module 'pkgutil' has no attribute 'ImpImporter'
       ```
     - This issue happens because **Superset** or one of its dependencies has not been updated to work with **Python 3.12**.

2. **Step** : **Setup WSL**

3. **Step** : **Install Python 3.11 from Deadsnakes PPA** (**Recommended**)

   - Add the Deadsnakes Repository
     ```sh
      sudo apt update
      sudo apt install software-properties-common -y
      sudo add-apt-repository ppa:deadsnakes/ppa -y
      sudo apt update
     ```
   - Install Python 3.11
     ```sh
      sudo apt install python3.11 python3.11-venv python3.11-dev -y
     ```
   - Verify Installation
     ```sh
      python3.11 --version
     ```

4. **Step**: **Setup Python Virtual Environment**

   - Once Python 3.11 is installed, set up a virtual environment and install Superset:
     ```sh
      python3.11 -m venv superset-linux-venv
      source superset-linux-venv/bin/activate
     ```

5. **Step**: **Install Libraries**
   - Install the libraries by:
     ```sh
        ip install apache-superset
     ```

# Resources and Further Reading
