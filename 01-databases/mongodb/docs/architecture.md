# MongoDB - Architecture

One MongoDB 7.0 Community Server container, used as the document store for the web apps. Running it is covered in the [Readme](../Readme.md).

## Components

| Piece | Value |
| --- | --- |
| Container | `mongodb` (`mongodb/mongodb-community-server:7.0.7-ubi8`) |
| Compose project | `data-ops`, shared with the other stacks. Not in the root `docker-compose.yml`. Compose warns about "orphan containers" (the other services in the project). Never add `--remove-orphans`. |
| Data | external volume `mongodb-data` → `/data/db` |
| Command | `mongod --bind_ip_all`, so other containers can reach it |
| Bundled tools | `mongosh`, `mongoimport` / `mongoexport`, `mongodump` / `mongorestore` |

## Design choices

- **MongoDB's own image** (`mongodb/mongodb-community-server`), not Docker Hub's `mongo`. That's why the root-user variables are `MONGODB_INITDB_ROOT_*`, not `MONGO_INITDB_ROOT_*`.
- **Auth on, root user created on first start.** The entrypoint creates the root user in `admin` on an empty volume, then restarts `mongod` with auth enabled. The healthcheck allows a 30s start period for that. Changing the variables later doesn't change the existing user.
- **Credential-free healthcheck** (`db.adminCommand('ping')`), so no password shows up in `docker inspect`.
- **External, named volume**, as with Postgres and MySQL. Compose never creates or deletes `mongodb-data`, so renaming the folder or running `down -v` can't lose data. On a fresh machine, create it first with `docker volume create mongodb-data`.
- **No init scripts mounted.** The image's entrypoint supports `/docker-entrypoint-initdb.d`, but the stack doesn't use it. Databases and users are created on demand (see the Readme). To seed a fresh volume automatically, mount an `init-scripts/` folder there, as Postgres and MySQL do.

## Dev vs prod

| | dev | prod |
| --- | --- | --- |
| Restart | `no` | `unless-stopped` |
| Root password | optional | required (`${MONGODB_INITDB_ROOT_PASSWORD:?}`) |
| Limits | none | 2 CPU / 4G (`MONGODB_CPU_LIMIT`, `MONGODB_MEMORY_LIMIT`) |
| Logs | Docker default | 100m × 10 |

## Open items

- **MG1** `docker stop` ends with exit code 137: `mongod` doesn't shut down within the 10s grace period and gets killed. Journaling makes this safe, but it's an unclean shutdown. Add `stop_grace_period: 30s` and check that the entrypoint forwards `SIGTERM`.
- Port 27017 is published by base, so prod publishes it too (root TODO X3).
