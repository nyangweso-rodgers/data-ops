# Trino - Architecture

One Trino 477 node (coordinator only, no workers) that queries the other databases through catalogs. Running it is covered in the [Readme](../Readme.md).

## Components

| Piece | Value |
| --- | --- |
| Container | `trino` (`trinodb/trino:477`, full image with all connectors) |
| Compose project | `trino` (the folder name). The root `docker-compose.yml` also `extends` this base file and adds `depends_on: postgres` |
| Catalogs | bind mount `./etc/catalog` → `/etc/trino/catalog` (read-only in prod) |
| Server config | image defaults (`config.properties`, `jvm.config` aren't overridden) |
| State | none. No data volume |

## Design choices

- **Stateless query engine.** Data stays in the source databases. Removing the container loses nothing except the contents of `memory` catalogs.
- **Only the catalog directory is mounted.** The image's own `config.properties` / `jvm.config` stay intact. To tune memory or add workers, mount `./etc` → `/etc/trino` instead (commented out in base).
- **Dynamic catalog management** (`CATALOG_MANAGEMENT=dynamic`). `CREATE CATALOG` / `DROP CATALOG` take effect without a restart and are written to `etc/catalog/<name>.properties`, so they persist across restarts. Files placed there by hand load on the next restart.
- **Secrets via `${ENV:VAR}`.** The container loads `.env`, so catalog properties can reference `${ENV:LOCAL_USERS_PG_DB_PASSWORD}` instead of storing passwords.
- **Cross-stack dependency only in the root compose.** A standalone `make trino-dev-up` doesn't wait for Postgres (root TODO X2).

## Dev vs prod

| | dev | prod |
| --- | --- | --- |
| Restart | `no` | `unless-stopped` |
| Catalog mount | read-write | read-only (breaks `CREATE CATALOG`, T2) |
| Limits | none | 4 CPU / 8G (`TRINO_CPU_LIMIT`, `TRINO_MEMORY_LIMIT`) |
| Logs | Docker default | 100m × 10 |

## Open items

- **T2** Prod mounts `etc/catalog` read-only, which breaks `CATALOG_MANAGEMENT=dynamic`. Drop `:ro`, or use static catalogs in prod.
- **T3** No authentication. Configure password or OAuth auth plus HTTPS before prod.
- **T4** The committed catalog files are in the wrong folder. `etc/postgres.properties` and `etc/mysql.properties` sit in `etc/`, but compose mounts `etc/catalog/`, which doesn't exist in git, so Trino loads neither. Also, `postgres.properties` has a plain-text password committed, and `mysql.properties` is empty. Move the files to `etc/catalog/`, switch the password to `${ENV:...}`, and complete or delete the MySQL catalog.
