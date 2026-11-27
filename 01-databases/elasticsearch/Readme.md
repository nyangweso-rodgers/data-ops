# Elasticsearch

Elasticsearch 9.2 (single node, security on) with Kibana. It's the search backend for Amundsen and OpenMetadata. How it's wired: [docs/architecture.md](docs/architecture.md).

## Run it

All commands run from the repo root.

| | |
| --- | --- |
| Host | `http://localhost:9200` (`ELASTICSEARCH_HOST_PORT`). Transport `9300` |
| In-network | `http://elasticsearch:9200` on `data-ops-network` |
| User | `elastic` / `ELASTICSEARCH_PASSWORD` from `.env` |
| UI | Kibana at `http://localhost:5601` (`KIBANA_HOST_PORT`). Log in as `elastic` |
| Data | named volume `elasticsearch_data` |

First time on a new machine:

1. Run `docker network create data-ops-network`.
2. Kibana needs a service-account token; see [architecture](docs/architecture.md#kibana-authentication).
3. The default heap is 2 GB. On a low-RAM machine, set `ELASTICSEARCH_JAVA_OPTS="-Xms1g -Xmx1g"` in `.env`.

```sh
make elasticsearch-dev-up       # start elasticsearch + kibana (kibana waits for ES to be healthy)
make elasticsearch-dev-health   # cluster health
make elasticsearch-dev-logs     # follow logs
make elasticsearch-dev-down     # remove the containers (data volume kept)
make elasticsearch-help         # every target
```

## Create a test database (index)

Elasticsearch stores data in **indices**, not databases. Prefix test indices with `test_` so you can find and delete them together. Index names must be lowercase.

The password is in `$ELASTIC_PASSWORD` inside the container, so run `curl` there through `sh -c '...'`:

1. Create the index. Set `number_of_replicas: 0`: this is a single node, so a replica can never be placed and the index would stay yellow.

   ```sh
   docker exec elasticsearch sh -c 'curl -s -u "elastic:$ELASTIC_PASSWORD" -X PUT "localhost:9200/test_orders" \
     -H "Content-Type: application/json" \
     -d "{\"settings\":{\"number_of_shards\":1,\"number_of_replicas\":0},\"mappings\":{\"properties\":{\"name\":{\"type\":\"text\"},\"amount\":{\"type\":\"double\"},\"created_at\":{\"type\":\"date\"}}}}"'
   ```

2. Seed it from an NDJSON file on the host, in `_bulk` format: an action line, then a document line.

   ```json
   {"index":{}}
   {"name":"first order","amount":10.5,"created_at":"2026-01-01"}
   ```

   ```sh
   docker exec -i elasticsearch sh -c 'curl -s -u "elastic:$ELASTIC_PASSWORD" -X POST "localhost:9200/test_orders/_bulk?refresh=true" \
     -H "Content-Type: application/x-ndjson" --data-binary @-' < orders.ndjson
   ```

   The file must end with a newline.

3. Query it:

   ```sh
   docker exec elasticsearch sh -c 'curl -s -u "elastic:$ELASTIC_PASSWORD" "localhost:9200/test_orders/_search?q=name:first&pretty"'
   docker exec elasticsearch sh -c 'curl -s -u "elastic:$ELASTIC_PASSWORD" "localhost:9200/_cat/indices/test_*?v"'
   ```

   In Kibana, use **Dev Tools** to run the same requests without the `curl` wrapping.

4. Delete it when you're done:

   ```sh
   docker exec elasticsearch sh -c 'curl -s -u "elastic:$ELASTIC_PASSWORD" -X DELETE "localhost:9200/test_orders"'
   ```

   Wildcard deletes (`test_*`) are blocked by default (`action.destructive_requires_name`). Delete indices by name.

Connect from code with `http://elastic:<ELASTICSEARCH_PASSWORD>@localhost:9200`, or `elasticsearch:9200` from another container.
