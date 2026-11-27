# Redis

Redis 8.2 shared by Prefect, Superset and Redash for caches and queues, plus RedisInsight as a web UI. How it's wired: [docs/architecture.md](docs/architecture.md).

## Run it

All commands run from the repo root.

| | |
| --- | --- |
| Host | `localhost:6379` (`REDIS_HOST_PORT` in `ports.env`) |
| In-network | `redis:6379` on `data-ops-network` |
| Password | `REDIS_PASSWORD` from `.env` (no username) |
| UI | RedisInsight at `http://localhost:5540` (`REDISINSIGHT_HOST_PORT`), already connected to db 1 |
| Data | named volumes `redis-data` (AOF persistence), `redisinsight-data` |

First time on a new machine: `docker network create data-ops-network`.

```sh
make redis-dev-up           # start redis + redisinsight
make redis-dev-cli          # redis-cli, authenticated
make redis-dev-logs         # follow logs
make redis-dev-down         # remove the containers (data volumes kept)
make redis-help             # every target
```

## Create a test database

Redis has no named databases. It has numbered ones (`0` to `15`), and three are taken:

| db | Used by |
| --- | --- |
| 0 | Prefect |
| 1 | Superset (data cache) |
| 2 | Redash (queues) |
| 3-14 | free |
| **15** | **convention: tests and scratch** |

Every command takes `-n <db>`. The password is in `$REDIS_PASSWORD` inside the container. `--no-auth-warning` hides the "password on the command line" notice.

1. Write and read test keys in db 15:

   ```sh
   docker exec redis sh -c 'redis-cli --no-auth-warning -a "$REDIS_PASSWORD" -n 15 SET test:greeting hello'
   docker exec redis sh -c 'redis-cli --no-auth-warning -a "$REDIS_PASSWORD" -n 15 GET test:greeting'
   ```

2. Seed from a file with one command per line (for example `SET test:a 1`, `HSET test:user:1 name Ann`):

   ```sh
   docker exec -i redis sh -c 'redis-cli --no-auth-warning -a "$REDIS_PASSWORD" -n 15' < seed.redis
   ```

3. Connect:
   - host: `redis://:<REDIS_PASSWORD>@localhost:6379/15`
   - another container: `redis://:<REDIS_PASSWORD>@redis:6379/15`

   In RedisInsight, switch the database index to 15 to browse it.

4. Clear it when you're done. Only this database is emptied:

   ```sh
   docker exec redis sh -c 'redis-cli --no-auth-warning -a "$REDIS_PASSWORD" -n 15 FLUSHDB'
   ```

   **Never run `FLUSHALL`.** It empties every database, including Redash's and Prefect's queues.

Useful checks: `INFO keyspace` shows the key count per database. `DBSIZE` (with `-n 15`) counts one database. Prefer `SCAN 0 MATCH test:*` over `KEYS`, which blocks on large data sets.

A connection check from the host lives in `scripts/python/test_redis_connection.py`. It reads `REDIS_HOST`, `REDIS_PORT` and `REDIS_PASSWORD` from `.env`.
