# Apache Superset

## Table Of Contents

# Apache Superset

- **Apache Superset** as its name, coming from Apache Software Foundation, which is a non-organization profit that focus on open-source project software. It is the top-level project licensed by Apache 2.0.
- **Superset** provides non-code interface for building charts. However, it is included SQL query that can save data in Superset database table that can be used for data visualization too.
- **Unique Functions in Superset**

  1. **Superset Database with SQL Query**

     - Data from many sources include PostgreSQL, Google BigQuery, and Amazon Redshift can be saved in Superset Database. It is provided by Superset that can make the user collecting many sources. The data can be shown in the SQL Query which can make the datasets connected each other. The connected datasets that created by SQL Query have to be saved as a table if the user want to use it as data visualization. The user can save the SQL Query too for later used which may be the user want to edit part of query to create another table later.

  2. **A Table for A Data Visualization**
     - Using SQL Query if you want to combine many tables is required. Superset only accepts one table for one data visualization. It is shown all tables that saved in Superset Database, but the visualization only accept one table. Therefore, if the user wants to use data from many tables that connect many tables, the user has to create the table and save it in Superset Database first before creating data visualization or the user only use the table for the visualization itself and then combine with another visualization in a dashboard to make a comprehensive data insight.

- **Features of Apache Superset**

  1. Supports 40+ visualizations from simple line charts to highly detailed geospatial charts
  2. Able to access many SQL and NoSQL databases
  3. Admin panel available with very detailed settings, including users and roles privileges
  4. Able to cache data for dashboard visualizations

- **Remarks**:
  - **Superset** is designed to handle datasets of any size since it operates as a thin layer on top of your databases, which manage all the data processing. The platform’s performance is more dependent on user activity and the number of users rather than the data size. A setup with 8 GB RAM and 2vCPUs is sufficient for a moderate user base.

# Setup

## Setup Apache Superset on Docker

- Requirements:
- Steps

  1. Set `SECRET_KEY` via Environment Variable
     - **Superset** uses the **SECRET_KEY** for cryptographic operations (e.g., signing cookies, securing sessions).
     - The default `SECRET_KEY` in the base image is insecure and meant to be overridden and Without a custom `SECRET_KEY`, **Superset** halts startup
     - Run this command to generate a random, secure key
       ```sh
        # generate a random, secure key
        openssl rand -base64 42
       ```
     - Update your `.env` file
       ```env
        SUPERSET_SECRET_KEY=<b'YOUR_RANDOM_KEY_HERE_42_CHARACTERS_LONG>
       ```
  2. **Access the Superset Docker Container**
     - Access Superset Docker Container by:
       ```sh
        docker exec -it apache-superset bash
       ```
      - List users:
        ```sh
          superset fab list-users
        ``` 

- **Remarks**:
  - For production use, configure a web server like Gunicorn, Nginx, or Apache. Follow the guidelines on [running Superset on a WSGI HTTP Server](https://superset.apache.org/docs/configuration/configuring-superset/#running-on-a-wsgi-http-server).

# Resources and Further Reading

1. [Medium - Data Visualization in PostgreSQL With Apache Superset](https://medium.com/timescale/data-visualization-in-postgresql-with-apache-superset-aca3c56083b9)
