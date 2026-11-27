# Neo4j

Neo4j 4.4 Community, the graph store behind Amundsen's metadata service. How it's wired: [docs/architecture.md](docs/architecture.md).

## Run it

All commands run from the repo root.

| | |
| --- | --- |
| Browser | `http://localhost:7474` (`NEO4J_HTTP_HOST_PORT`) |
| Bolt | `bolt://localhost:7687` (`NEO4J_BOLT_HOST_PORT`). In-network `bolt://neo4j:7687` |
| User | `NEO4J_USER` (default `neo4j`) / `NEO4J_PASSWORD` from `.env` |
| Data | named volume `neo4j_data`. Logs in `./logs/neo4j` (gitignored) |

First time on a new machine: `docker network create data-ops-network`. The login is fixed when the volume is first created (see [architecture](docs/architecture.md#design-choices)).

```sh
make neo4j-dev-up           # start
make neo4j-dev-shell        # cypher-shell, authenticated
make neo4j-dev-logs         # follow logs
make neo4j-dev-down         # remove the container (data volume kept)
make neo4j-help             # every target
```

## Create a test database

**Community Edition has a single user database, `neo4j`.** `CREATE DATABASE` is Enterprise-only, and that database holds Amundsen's metadata graph. There are two ways to test.

### Option A: a separate throwaway instance (recommended)

This is fully isolated, and deleting it can't touch Amundsen's data:

```sh
docker run -d --rm --name neo4j-test --network data-ops-network \
  -e NEO4J_AUTH=neo4j/test-password -p 17474:7474 -p 17687:7687 neo4j:4.4.46

docker exec -it neo4j-test cypher-shell -u neo4j -p test-password      # once it's up (~20s)
docker stop neo4j-test                                                  # --rm deletes it and its data
```

Browser: `http://localhost:17474`. Bolt: `bolt://localhost:17687`, or `bolt://neo4j-test:7687` from another container. With no volume mounted, the data disappears when the container stops.

### Option B: a label namespace in the shared instance

Put every test node under its own label, here `Test`, and only ever match on that label.

1. Create test data:

   ```sh
   docker exec neo4j sh -c 'cypher-shell -u "$NEO4J_HEALTHCHECK_USER" -p "$NEO4J_HEALTHCHECK_PASSWORD" \
     "CREATE (:Test:Person {name: \"Ann\"})-[:KNOWS]->(:Test:Person {name: \"Bob\"})"'
   ```

2. Seed from a `.cypher` file on the host (statements separated by `;`):

   ```sh
   docker exec -i neo4j sh -c 'cypher-shell -u "$NEO4J_HEALTHCHECK_USER" -p "$NEO4J_HEALTHCHECK_PASSWORD"' < seed.cypher
   ```

3. Query: `MATCH (p:Test:Person)-[r]->(q) RETURN p.name, type(r), q.name;`

4. Clean up, removing **only** the test label:

   ```sh
   docker exec neo4j sh -c 'cypher-shell -u "$NEO4J_HEALTHCHECK_USER" -p "$NEO4J_HEALTHCHECK_PASSWORD" "MATCH (n:Test) DETACH DELETE n"'
   ```

   **Never run `MATCH (n) DETACH DELETE n`** in the shared instance. It wipes Amundsen's graph.

The credentials are in `NEO4J_HEALTHCHECK_USER` / `NEO4J_HEALTHCHECK_PASSWORD` inside the container. They're the same values as `NEO4J_USER` / `NEO4J_PASSWORD`.
