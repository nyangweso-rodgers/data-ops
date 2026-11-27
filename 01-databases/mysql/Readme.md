# MySQL

MySQL 9.2 instance for OpenMetadata's database and local test / reporting databases. How it's wired: [docs/architecture.md](docs/architecture.md).

## Run it

All commands run from the repo root.

| | |
| --- | --- |
| Host | `localhost:3306` (`MYSQL_HOST_PORT` in `ports.env`) |
| In-network | `mysql:3306` on `data-ops-network` |
| Root user | `root` / `LOCAL_MYSQL_DB_PASSWORD` from `.env` |
| App user | `mysql_user`, created by `init-scripts/init-mysql-users.sql` |
| Data | external volume `mysql-data` |

First time on a new machine:

```sh
docker network create data-ops-network
docker volume create mysql-data
```

Also create `init-scripts/init-mysql-users.sql`. It's gitignored because it holds a password, so a fresh clone doesn't have it (see [architecture](docs/architecture.md#init-scripts)).

Then:

```sh
make mysql-dev-up           # start
make mysql-dev-cli          # mysql client as root
make mysql-dev-logs         # follow logs
make mysql-dev-down         # remove the container (data volume kept)
make mysql-help             # every target
```

## Create a test database

Inside the container the root password is in `$MYSQL_ROOT_PASSWORD`, so the commands below never put it on your command line. The single quotes around `sh -c '...'` make the variable expand inside the container.

1. Create the database and a user for it. You can also paste the same SQL into `make mysql-dev-cli`:

   ```sh
   docker exec -i mysql sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD"' <<'SQL'
   CREATE DATABASE IF NOT EXISTS test_orders;
   CREATE USER IF NOT EXISTS 'test_orders_user'@'%' IDENTIFIED BY 'change-me';
   GRANT ALL PRIVILEGES ON test_orders.* TO 'test_orders_user'@'%';
   SQL
   ```

   To reuse the shared app user instead: `GRANT ALL PRIVILEGES ON test_orders.* TO 'mysql_user'@'%';`

2. Load a schema or seed data from a file on the host:

   ```sh
   docker exec -i mysql sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" test_orders' < seed.sql
   ```

3. Connect:
   - host: `mysql://test_orders_user:change-me@localhost:3306/test_orders`
   - another container: `mysql://test_orders_user:change-me@mysql:3306/test_orders`

4. Drop it when you're done:

   ```sql
   DROP DATABASE test_orders;
   DROP USER 'test_orders_user'@'%';
   ```

The `mysql: [Warning] Using a password on the command line` line is expected and harmless.

### Make it permanent

Add the database to `init-scripts/init-mysql-db.sql` and the grant to `init-scripts/init-mysql-users.sql`. Both use `IF NOT EXISTS`, so they are safe to re-run. They only run on an empty volume. To apply them to the running instance:

```sh
docker exec mysql sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" < /docker-entrypoint-initdb.d/init-mysql-db.sql'
docker exec mysql sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" < /docker-entrypoint-initdb.d/init-mysql-users.sql'
```

Re-applying creates every database the script lists, including ones you have since dropped.

## Example databases

`example_databases/<db>/` holds DDL, queries and helper scripts for the existing test databases (`test`, `test_kaleidofin`, `test_reporting_service`): `01_meta` for database-level scripts, `02_tables/<table>` for per-table DDL, `03_reports` for report queries. `scripts/` has database-wide helpers (`mysql_tables_summary`, `delete-db-tables`).
