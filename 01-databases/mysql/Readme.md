# MySQL

## Table Of Contents

# How To Run Mysql In Docker With Data Persistence

## Step 1. Create Dockerfile

- Create a new file with the name `DockerFile`. Add the following lines of code to the file.

  ```DockerFile
    # Use the official MySQL image as the base image
    FROM mysql:latest

    # Expose the default MySQL port
    EXPOSE 3306
  ```

## Step 2. Create `docker-compose.yml`

- Create a new file with the name `docker-compose.yml` and add the following content to the file.
  ```yml
  services:
  ```

## Step 3. Run Docker Container

- Run docker container by:
  ```sh
    docker compose up -d
  ```

# Database Initialization

- Connect to MySQL Server via MySQLWorkbench, and Execute the following ddl :

  ```sql
    -- Use the schema
    USE transactions;

    -- Create the transactions table
    CREATE TABLE IF NOT EXISTS transactions (
        id VARCHAR(36) PRIMARY KEY,
        amount DECIMAL(18, 2) NOT NULL,
        currency VARCHAR(10) NOT NULL,
        status ENUM('pending', 'completed', 'failed') NOT NULL,
        user_id VARCHAR(36) NOT NULL,
        merchant_id VARCHAR(36) NOT NULL,
        payment_method VARCHAR(50) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Create the index for user_id
    CREATE INDEX idx_user_id ON transactions(user_id);
  ```

- Step : Access the MySQL Container via Terminal
  - Access the Container: Run the following command from your host machine (where mysql-db is the container name from your docker-compose.yml):
    ```sh
      docker exec -it mysql-db mysql -u root -p
    ```
  - **Commands**:
    1. **Create a New Database**: Once inside the MySQL prompt, you can create a new database:
       ```sh
        CREATE DATABASE new_database;
       ```
    2. **Show Databases**: Verify databases by:
       ```sh
        SHOW DATABASES;
       ```

# Resources and Further Reading
