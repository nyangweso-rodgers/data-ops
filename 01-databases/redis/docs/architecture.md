# Redis - Architecture

One Redis 8.2 container shared by three tools, plus RedisInsight as a web UI. Running it is covered in the [Readme](../Readme.md).

## Components

| Service | Image | Role | In-network address |
| --- | --- | --- | --- |
| `redis` | `redis:8.2.0` | Cache + queues, AOF persistence, password auth | `redis:6379` |
| `redisinsight` | `redislabs/redisinsight:2.70` | Web UI (dev only, `tools` profile in prod) | `http://redisinsight:5540` |

Compose project: `redis` (the folder name). The root `docker-compose.yml` also `extends` this base file.

## Database allocation

The tools share one instance and are separated by database number:

| db | Consumer | Contents | Safe to evict? |
| --- | --- | --- | --- |
| 0 | Prefect | messaging (`PREFECT_REDIS_MESSAGING_DB`) | no |
| 1 | Superset | query cache (`CACHE_REDIS_DB`) | yes |
| 2 | Redash | RQ job queues (`REDASH_REDIS_URL`) | no |
| 15 | tests (convention) | scratch data | yes |

Because queues share the instance with a cache, **no `maxmemory` eviction policy is set**: evicting queue entries would lose jobs. Size the memory limit for cache and queue growth together.

## Design choices

- **AOF persistence** (`--appendonly yes`). Every write is logged to `/data`, so queues survive a restart.
- **Password via `--requirepass`** from `REDIS_PASSWORD`. Clients use `redis://:<password>@redis:6379/<db>`.
- **RedisInsight is preconfigured.** `RI_REDIS_*` variables register the connection on every start, so there's no manual "Add database". `RI_ENCRYPTION_KEYTAR=false` is required. Without it, RedisInsight tries OS-keychain encryption, which this image can't do, and silently drops the connection.
- **Pinned volume names** (`redis-data`, `redisinsight-data`), so the stack Makefile and the root compose share the same data.

## Dev vs prod

| | dev | prod |
| --- | --- | --- |
| Restart | `no` | `unless-stopped` |
| Password | optional | required (`${REDIS_PASSWORD:?}`) |
| RedisInsight | started | off (`--profile tools` to start it) |
| Limits | none | 1 CPU / `REDIS_MEMORY_LIMIT` (2G) |
| Logs | Docker default | 100m × 10 |

## Open items

- **RD1** `--requirepass` is on the command line, so it's visible in `docker inspect` (and the healthcheck repeats it). Move it to a mounted `redis.conf`.
- **RD2** No eviction policy, because queues (Redash, Prefect) share the instance with Superset's cache. Split them: cache with eviction, queues with `noeviction`.
- `.env` has `REDIS_HOST=localhost` for host-side scripts. Containers must use `redis` (root TODO X4).
- In prod, Superset, Redash and Prefect should move to a managed Redis (root TODO X5).
