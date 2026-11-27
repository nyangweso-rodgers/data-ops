# PostgreSQL - Architecture

One Postgres 14.18 container (official image, no Dockerfile) that most other stacks share as their metadata database. Running it is covered in the [Readme](../Readme.md).

## Components

| Piece | Value |
| --- | --- |
| Container | `postgres` (`postgres:14.18`) |
| Compose project | `data-ops`, the same as the root `docker-compose.yml` |
| Data | external volume `postgres-data` → `/var/lib/postgresql/data` |
| Init | `./init-scripts` → `/docker-entrypoint-initdb.d` (read-only in prod) |
| Server flags | `shared_preload_libraries=pg_stat_statements`, `wal_level=logical` |

## Design choices

- **Shared instance, one database per tool.** `init-scripts/` creates `local_metabase`, `local_redash`, `local_superset`, `users` (with a `customers` table) and `local_postgres`. Other tools' databases are created by their own stacks, for example `make n8n-init-db`. In production those tools use RDS, so this container is only for local work or a single-VM deployment.
- **External, named volume.** Compose never creates or deletes `postgres-data`, and the folder name isn't part of the volume name. You can rename or move the stack folder without losing data, and `docker-compose down -v` can't wipe it.
- **Project `data-ops`.** The stack Makefile passes `-p data-ops`, so `make postgres-*` and the root compose manage the same container. Compose warns about "orphan containers" because the other services live in the same project. Never add `--remove-orphans`, because it removes them.
- **`wal_level=logical`** is required by Debezium CDC (`pgoutput`) in [03_streaming/kafka](../../../03_streaming/kafka/docs/architecture.md). `users.customers` is the CDC source table.
- **`pg_stat_statements`** is preloaded for query statistics. Run `CREATE EXTENSION pg_stat_statements` in a database to query the view there.
- **Restart `always` in dev.** Unlike the app stacks, dev keeps auto-restart, because other local services expect Postgres to be up.
- **Healthcheck** runs `pg_isready -h localhost` without a password, so no secret shows up in `docker inspect`.

## Dev vs prod

| | dev | prod |
| --- | --- | --- |
| Restart | `always` | `unless-stopped` |
| Password | optional | required (`${LOCAL_USERS_PG_DB_PASSWORD:?}`) |
| Init scripts | read-write mount | read-only mount |
| Limits | none | 2 CPU / 4G (`POSTGRES_CPU_LIMIT`, `POSTGRES_MEMORY_LIMIT`) |
| Logs | 20m × 5 | 100m × 10 |

## Gotchas

- **Init scripts run once**, only on an empty volume. Changing `LOCAL_USERS_PG_DB_PASSWORD` later doesn't change the existing password: run `ALTER USER postgres PASSWORD '...'` too.
- **Port 5432 is published by base**, so prod publishes it too. Restrict it at the firewall (root TODO X3).
- **Start it from its own Makefile.** The root compose omits the dev log rotation, so it sees a different config and would recreate the container (root TODO X1).
