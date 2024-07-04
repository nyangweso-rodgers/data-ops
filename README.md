# Data Ops

# Project Description

- This prject is for:
  - **Data Pipeline** Service with **Apache Kafka**, **Postgres**, and **MongoDB**.
  - API service, and a
  - Next.js Application.

# Services

- The project has the following services running as Docker containers

  1. mongo
  2. postgres
  3. pgadmin
     - [dpage/pgadmin4](https://hub.docker.com/r/dpage/pgadmin4) is a web based administration tool for the PostgreSQL database.
  4. kafka
  5. kafka-ui
  6. zookeeper
  7. schema-registry
  8. sale-order-api
  9. customer-api
  10. nextjs.app

# 1. PostgreSQL Docker Container

- Check my [github.com/nyangweso-rodgers - Running PostgreSQL Docker Container](https://github.com/nyangweso-rodgers/My-Databases/tree/main/02-Transactional-Databases/01-postgresql/01-setup-postgresql/01-postgres-docker-container), GitHub repo on how to configure and run postgresql docker container using **docker-compose**.
  ```yml
  services:
  ```

## Connect to a Postgres Docker Container

- To connect to a **PostgreSQL** instance running within a **Docker container**, you can use the `docker exec` command combined with the `psql` command:
- Example:
  ```bash
    #accessing postgres docker container
    docker exec -it postgres psql -U admin -d test_db
  ```
- Remarks:
  - Check my [GitHub Repo](https://github.com/nyangweso-rodgers/My-Databases/blob/main/02-Transactional-Databases/01-postgresql/02-connect-to-postgresql/01-psql-commands/Readme.md) for a list of `psql` commands

# 2. MongoDB Docker Container

- Check [github.com/nyangweso-rodgers - Run MongoDB Docker Container](https://github.com/nyangweso-rodgers/My-Databases/blob/main/03-Working-with-MongoDB/02-Setup-MongoDB/01-Run-MongoDB-Docker-Container/Readme.md) repo on how to run a mongo docker container using docker-compose.
- Check [github.com/nyangweso-rodgers - mongoDB replica set](https://github.com/nyangweso-rodgers/My-Databases/blob/main/03-Working-with-MongoDB/01-Fundamentals-of-MongoDB/mongoDB-replica-set/Readme.md) repo, to successfully set up a **MongoDB** **replica set** with **Docker Compose**. This ensures that you have a highly available and resilient MongoDB deployment.
  ```yml
  services:
  ```

# Zookeeper

```yml
services:
```

# Kafka

```yml
services:
```

# Schema Registry

```yml
services:
```

# Debezium

```yml
services:
```

## Register Debezium Connector

- To **register** the above **connector**, run the below `curl` commands:

  ```sh
    curl -X POST --location "http://localhost:8083/connectors" -H "Content-Type: application/json" -H "Accept: application/json" -d @register-customer-postgresdb-connector.json
  ```

# Kafka UI

```yml
services:
```

# Debezium UI

```yml
services:
```

# Service 3: Metabase Docker Container

```yml
services:
```

## Access Metabase

- Once the **Docker Compose** is up and running, you can access Metabase at http://localhost:3000 in your web browser.

## Connect Metabase to PostgreSQL

- When you first open **Metabase**, it will ask you to setup a connection to your database. Here are the settings you need to use:
  1. Database type: PostgreSQL
  2. Host: postgres
  3. Port: 5432
  4. Database name: <provide database name>
  5. Username: <username>
  6. Password: <password>
- Now, you should be able to explore your **PostgreSQL** data using **Metabase**!

# Resources and Further Reading

1. [github.com/nyangweso-rodgers - Docker-Commands](https://github.com/nyangweso-rodgers/My-Journey-Into-Computer-Science/blob/master/04-VMs-vs-Containers/02-Containers/01-Docker/01-Docker-Commands/Readme.md)

2. [github.com/nyangweso-rodgers - Setting Express.js Development Environment](https://github.com/nyangweso-rodgers/Programming-with-JavaScript/blob/main/03-JavaScript-Frameworks/02-Express.js/01-Setting-Express-Development-Environment/Readme.md)
3. [github.com/nyangweso-rodgers - Docker Compose File](https://github.com/nyangweso-rodgers/My-Journey-Into-Computer-Science/blob/master/04-VMs-vs-Containers/02-Containers/01-Docker/02-Docker-Compose-File/Readme.md)
