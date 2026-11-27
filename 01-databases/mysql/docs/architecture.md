# MySQL - Architecture

One MySQL 9.2.0 container (official image, no Dockerfile). It holds OpenMetadata's database and local test / reporting databases. Running it is covered in the [Readme](../Readme.md).

## Components

| Piece | Value |
| --- | --- |
| Container | `mysql` (`mysql:9.2.0`) |
| Compose project | `data-ops`, the same as the root `docker-compose.yml` |
| Data | external volume `mysql-data` → `/var/lib/mysql` |
| Init | `./init-scripts` → `/docker-entrypoint-initdb.d` (read-only) |
| Server flags | `--bind-address=0.0.0.0`, `wait_timeout` / `interactive_timeout` = 8h |

## Design choices

- **External, named volume.** Compose never creates or deletes `mysql-data`, so renaming the folder or running `down -v` can't lose data.
- **Project `data-ops`.** This works the same way as Postgres: the stack Makefile and the root compose manage one container. Ignore the "orphan containers" warning and never add `--remove-orphans`.
- **Long idle timeouts (8h)**, so long-running ETL and BI connections aren't dropped mid-job.
- **Restart `always` in dev**, because OpenMetadata expects MySQL to be up.
- **Root password from the environment.** `LOCAL_MYSQL_DB_PASSWORD` in `.env` becomes `MYSQL_ROOT_PASSWORD` inside the container. Shell into the container and use the variable rather than typing the password.

## Init scripts

Init scripts run once, only on an empty volume, in file-name order:

| File | Creates | In git |
| --- | --- | --- |
| `init-mysql-db.sql` | `test`, `test_greeno`, `test_kaleidofin` | yes |
| `init-mysql-users.sql` | `mysql_user` and its grants on those databases | **no** (gitignored, holds a password) |

A fresh clone has no `init-mysql-users.sql`. Create it before the first start, or create the user by hand afterwards. Both files use `IF NOT EXISTS`, so you can re-apply them to a running instance (see the Readme).

## Dev vs prod

| | dev | prod |
| --- | --- | --- |
| Restart | `always` | `unless-stopped` |
| Password | optional | required (`${LOCAL_MYSQL_DB_PASSWORD:?}`) |
| Limits | none | 2 CPU / 4G (`MYSQL_CPU_LIMIT`, `MYSQL_MEMORY_LIMIT`) |
| Logs | 20m × 5 | 100m × 10 |

## Open items

- **MY1** `init-mysql-db.sql` has drifted from the live server. It still creates `test_greeno`, but the server holds `test_grdata`, `test_kaleidofin_partner_data` and `test_reporting_service`. Update the script so a fresh volume matches.
- **MY2** Add a committed `init-mysql-users.sql.example`, with the password read from the environment or left as a placeholder, so a fresh clone knows the file is needed.
- Port 3306 is published by base, so prod publishes it too (root TODO X3).
