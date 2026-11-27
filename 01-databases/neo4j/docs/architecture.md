# Neo4j - Architecture

One Neo4j 4.4 Community container (official image). It's the metadata graph for [Amundsen](../../../metadata/amundsen). Running it is covered in the [Readme](../Readme.md).

## Components

| Piece | Value |
| --- | --- |
| Container | `neo4j` (`neo4j:4.4.46`, Community) |
| Compose project | `data-ops`, the same as the root `docker-compose.yml`, which also `extends` this base file. Compose warns about "orphan containers" (the other services in the project). Never add `--remove-orphans`. |
| Ports | `7474` HTTP (Browser), `7687` Bolt (drivers, cypher-shell) |
| Data | named volume `neo4j_data` → `/data` |
| Logs | bind mount `./logs/neo4j` → `/logs` (gitignored) |
| Memory (dev) | heap 1G initial / 2G max, page cache 512M |

## Design choices

- **The 4.4 line is pinned for Amundsen.** Neo4j is only upgraded together with Amundsen's metadata service (NJ2).
- **Community Edition means one user database.** There's `neo4j` plus `system`. There's no `CREATE DATABASE`, no roles and no clustering, so test data either goes in a throwaway container or under its own label (see the Readme).
- **Auth fixed on first start.** `NEO4J_AUTH=<user>/<password>` only applies when the data volume is created. To rotate `NEO4J_PASSWORD` later, also run `ALTER CURRENT USER SET PASSWORD FROM '<old>' TO '<new>'` (against `system`).
- **Healthcheck runs a real query** (`cypher-shell 'RETURN 1'`). Its credentials go in `NEO4J_HEALTHCHECK_*`, separate variables that Neo4j itself ignores. `make neo4j-dev-shell` reuses them.
- **Named volume, not a bind mount.** Older notes mention `./data/neo4j`. That layout is gone, but its gitignore entries remain.

## Dev vs prod

| | dev | prod |
| --- | --- | --- |
| Restart | `no` | `unless-stopped` |
| Password | optional | required (`${NEO4J_PASSWORD:?}`) |
| Heap / page cache | 1G-2G / 512M | `NEO4J_HEAP_INITIAL` / `NEO4J_HEAP_MAX` (2G) / `NEO4J_PAGECACHE` (1G) |
| Limits | none | 2 CPU / 4G (heap + page cache + ~1G overhead) |
| Logs | Docker default | 100m × 10 |

## Open items

- **NJ2** Upgrade off the 4.4 line together with Amundsen's metadata service.
- Ports 7474 and 7687 are published by base, so prod publishes them too (root TODO X3).
