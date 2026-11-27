# Trino

Trino 477, a SQL query engine that queries other databases (Postgres, MySQL, ...) through **catalogs**. It stores no data itself. How it's wired: [docs/architecture.md](docs/architecture.md).

## Run it

All commands run from the repo root.

| | |
| --- | --- |
| Host | `http://localhost:8080` (`TRINO_HOST_PORT`). The Web UI accepts any username |
| In-network | `http://trino:8080` on `data-ops-network` |
| Auth | none (dev only, see [architecture](docs/architecture.md#open-items)) |
| Catalogs | `./etc/catalog/*.properties`, plus any created with `CREATE CATALOG` |

Start the catalog sources first, for example `make postgres-dev-up`. Trino doesn't wait for them.

```sh
make trino-dev-up           # start
make trino-dev-cli          # trino CLI in the container
make trino-dev-logs         # follow logs
make trino-dev-restart      # recreate (reloads catalog files)
make trino-help             # every target
```

## Create a test database

In Trino a "database" is a **schema inside a catalog**. Dynamic catalog management is on, so catalogs can be created with SQL from `make trino-dev-cli`. Each one is saved as `etc/catalog/<name>.properties` and survives restarts.

### Option A: in-memory (fastest, nothing to clean up in other databases)

```sql
CREATE CATALOG test USING memory;
CREATE SCHEMA test.orders;
CREATE TABLE test.orders.items (id bigint, name varchar, amount double);
INSERT INTO test.orders.items VALUES (1, 'first', 10.5), (2, 'second', 20.0);
SELECT * FROM test.orders.items;
```

The data lives in Trino's memory and is lost on restart. The catalog file stays until you run `DROP CATALOG test;`.

### Option B: generated sample data

The `tpch` and `tpcds` connectors generate benchmark tables on the fly, with no storage:

```sql
CREATE CATALOG tpch USING tpch;
SELECT * FROM tpch.tiny.nation;                  -- schemas: tiny, sf1, sf10, ...
CREATE TABLE test.orders.nation AS SELECT * FROM tpch.tiny.nation;   -- copy into memory
```

### Option C: a real database through Trino

1. Create the test database in its own stack, for example [Postgres](../postgres/Readme.md#create-a-test-database).
2. Register it as a catalog. `${ENV:...}` reads the password from the container's environment, so it isn't written into the catalog file:

   ```sql
   CREATE CATALOG pg_test USING postgresql WITH (
     "connection-url" = 'jdbc:postgresql://postgres:5432/test_orders',
     "connection-user" = 'postgres',
     "connection-password" = '${ENV:LOCAL_USERS_PG_DB_PASSWORD}'
   );
   SHOW SCHEMAS FROM pg_test;
   SELECT * FROM pg_test.public.<table>;
   ```

3. Drop the catalog when you're done (`DROP CATALOG pg_test;`), then drop the database in its own stack.

### Housekeeping

```sql
SHOW CATALOGS;
SHOW SCHEMAS FROM test;
DROP CATALOG test;      -- also deletes etc/catalog/test.properties
```

Catalog files created in `etc/catalog/` are on your disk. Check them before committing: a catalog created with a literal password stores that password in plain text.
