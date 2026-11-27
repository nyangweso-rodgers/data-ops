# Elasticsearch - Architecture

A single-node Elasticsearch 9.2 cluster with security enabled, and Kibana in front of it. It's the search backend for Amundsen and OpenMetadata. Running it is covered in the [Readme](../Readme.md).

## Components

| Service | Image | Role | In-network address |
| --- | --- | --- | --- |
| `elasticsearch` | `elasticsearch:9.2.1` | Single-node cluster, `xpack.security` on | `http://elasticsearch:9200` (transport `9300`) |
| `kibana` | `kibana:9.2.1` | UI and Dev Tools. Starts once ES is healthy | `http://kibana:5601` |

Compose project: `data-ops`, the same as the root `docker-compose.yml`, which also `extends` this base file. Compose warns about "orphan containers" (the other services in the project). Never add `--remove-orphans`.

## Design choices

- **`discovery.type: single-node`.** There's no cluster formation and no replicas. Create indices with `number_of_replicas: 0`, or they stay **yellow**. The healthcheck accepts yellow as well as green so the stack still starts.
- **Security on, even in dev.** The `elastic` superuser's password comes from `ELASTICSEARCH_PASSWORD`, which the container receives as `ELASTIC_PASSWORD`. Clients use basic auth over plain HTTP, because TLS isn't configured.
- **Heap via `ELASTICSEARCH_JAVA_OPTS`** (default `-Xms2g -Xmx2g`). In prod, keep the container memory limit around 2× the heap for page cache and off-heap use.
- **`memlock` / `nofile` ulimits** are raised for indexing. Prod also sets `bootstrap.memory_lock: true`.
- **Pinned volume name** `elasticsearch_data`, shared by the stack Makefile and the root compose.

## Kibana authentication

Kibana 8+ refuses to connect to Elasticsearch as the `elastic` superuser, so it uses a **service-account token** (`ELASTICSEARCH_SERVICEACCOUNTTOKEN` in `.env`). Create one once, with only Elasticsearch running:

```sh
docker exec elasticsearch sh -c 'curl -s -u "elastic:$ELASTIC_PASSWORD" -X POST \
  "localhost:9200/_security/service/elastic/kibana/credential/token/kibana-token"'
```

Put the returned `token.value` in `.env` as `ELASTICSEARCH_SERVICEACCOUNTTOKEN`, then start Kibana. You still log in to the Kibana UI as `elastic`.

## Dev vs prod

| | dev | prod |
| --- | --- | --- |
| Restart | `no` | `unless-stopped` |
| Password | optional | required (`${ELASTICSEARCH_PASSWORD:?}`) |
| Memory lock | off | `bootstrap.memory_lock: true` |
| Limits | none | ES 2 CPU / 4G (`ELASTICSEARCH_CPU_LIMIT`, `ELASTICSEARCH_MEMORY_LIMIT`), Kibana 1 CPU / 1G |
| Logs | 10m × 3 | 100m × 10 |

## Open items

- **E1** The prod host needs `vm.max_map_count >= 262144` (`sysctl -w vm.max_map_count=262144`) for memory locking and mmap.
- Ports 9200, 9300 and 5601 are published by base, so prod publishes them too (root TODO X3). Prod also has no TLS.
