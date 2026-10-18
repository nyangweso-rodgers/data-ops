# MySQL

## Table Of Contents

# How To Run Mysql In Docker With Data Persistence

- Runs the official `mysql:9.2.0` image directly (no Dockerfile). Config lives in `docker-compose-mysql.base.yml` (+ `.dev.yml` / `.prod.yml`).
- Data persists in the external `mysql-data` volume (on a fresh machine: `docker volume create mysql-data`).
- `init-scripts/` is mounted read-only into `/docker-entrypoint-initdb.d/` and runs only when the volume is empty.
- Run it:
  ```sh
    make mysql-dev-up     # from the repo root
    make mysql-dev-cli    # mysql client inside the container
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

## Verify Database Exists

```sh
  # Should show both test and test_kaleidofin
  docker exec -it mysql mysql -u root -p${LOCAL_MYSQL_DB_PASSWORD} -e "SHOW DATABASES;"
```

## Create Database Manually

```sql
  -- Create the database
  CREATE DATABASE IF NOT EXISTS test_kaleidofin;

  -- Grant permissions to mysql_user
  GRANT ALL PRIVILEGES ON test_kaleidofin.* TO '<password>'@'%';
  FLUSH PRIVILEGES;

  -- Verify it was created
  SHOW DATABASES;

  -- Exit
  exit;
```

# Resources and Further Reading
