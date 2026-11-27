# PostgreSQL

Shared Postgres 14 instance for the monorepo: the metadata database for Airflow, Dagster, Metabase, Redash, Superset, n8n, Prefect, Open WebUI and the web apps, plus `users` (the Debezium CDC source) and `local_postgres` for ad-hoc work. How it's wired: [docs/architecture.md](docs/architecture.md).

## Run it

All commands run from the repo root.

| | |
| --- | --- |
| Host | `localhost:5432` (`POSTGRES_HOST_PORT` in `ports.env`) |
| In-network | `postgres:5432` on `data-ops-network` |
| Superuser | `postgres` / `LOCAL_USERS_PG_DB_PASSWORD` from `.env` |
| Data | external volume `postgres-data` |

First time on a new machine:

```sh
docker network create data-ops-network
docker volume create postgres-data
```

Then:

```sh
make postgres-dev-up        # start
make postgres-dev-psql      # psql as postgres
make postgres-dev-logs      # follow logs
make postgres-dev-down      # remove the container (data volume kept)
make postgres-help          # every target
```

Production (`make postgres-prod-up`) adds a required password, resource limits and log rotation. It's only for a self-hosted Postgres. Every other stack's prod config uses RDS instead.

## Create a test database

`PGUSER=postgres` is set inside the container, so `psql`, `createdb` and `dropdb` need no `-U`.

1. Create the database, plus an owner role if the app should not log in as `postgres`:

   ```sh
   docker exec postgres createdb test_orders
   docker exec postgres psql -d postgres -c "CREATE ROLE test_orders_user LOGIN PASSWORD 'change-me'" -c "ALTER DATABASE test_orders OWNER TO test_orders_user"
   ```

2. Load a schema or seed data from a file on the host:

   ```sh
   docker exec -i postgres psql -d test_orders -v ON_ERROR_STOP=1 < seed.sql
   ```

3. Connect:
   - host: `postgresql://test_orders_user:change-me@localhost:5432/test_orders`
   - another container: `postgresql://test_orders_user:change-me@postgres:5432/test_orders`

4. Drop it when you're done (`--force` disconnects open sessions):

   ```sh
   docker exec postgres dropdb --force test_orders
   docker exec postgres psql -d postgres -c "DROP ROLE test_orders_user"
   ```

### Make it permanent

To recreate a database on every fresh volume, add `init-scripts/init-<name>-db.sql`. Postgres has no `CREATE DATABASE IF NOT EXISTS`, so use `\gexec` to keep the script safe to re-run:

```sql
SELECT 'CREATE DATABASE test_orders'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'test_orders')\gexec
```

Init scripts only run when the volume is empty. To apply a new script to the running instance:

```sh
docker exec postgres psql -d postgres -f /docker-entrypoint-initdb.d/init-<name>-db.sql
```

## Example databases

`example_databases/<db>/` holds reference DDL and queries for databases in this instance (`local_dagster`, `local_metabase`, `local_postgres`, `local_airflow`): `01_meta` for database-level scripts, `02_tables/<table>` for per-table SQL and helpers.

## Useful queries

```sh
docker exec postgres psql -c "\l+"                                        # databases and sizes
docker exec postgres psql -d test_orders -c "\dt+"                         # tables in a database
docker exec postgres psql -c "SELECT datname, usename, state FROM pg_stat_activity WHERE datname IS NOT NULL"
```
