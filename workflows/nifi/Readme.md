# Apache NiFi

Everything here is declared in files and applied automatically: `make nifi-dev-up` starts NiFi, then the one-shot `nifi-provisioner` init container applies connections and pipelines and exits (`docker logs nifi-provisioner` shows what it did).

- UI: `https://localhost:8443/nifi` (HTTPS only in NiFi 2.x; accept the self-signed certificate warning)
- Login: `NIFI_USER` / `NIFI_PASSWORD` from the root `.env` (password ≥ 12 characters; re-applied on every start)

## Layout

```
workflows/nifi/
├── configs/                          # HOW things run - declarative config
│   ├── connections.yml               #   shared DB connections (controller services)
│   └── mysql/to_clickhouse.yml       #   all MySQL -> ClickHouse pipelines, grouped
├── schemas/                          # WHAT the data is - contracts (Avro), per source table
│   └── mysql/test_reporting_service/ml_payg_interventions.avsc
├── pipelines/                        # flow LOGIC - reusable NiFi flow definitions (templates)
│   └── jdbc_incremental_to_clickhouse.json
├── provisioning/                     # the Python package that applies the three folders above
│                                     #   (python -m provisioning) - map: provisioning/README.md
├── tests/unit/                       # provisioning tests: `uv run pytest` from workflows/nifi
├── pyproject.toml + uv.lock          # provisioning's Python dependencies
└── Dockerfile                        # NiFi + JDBC drivers (in drivers/, not lib/)
```

The three concerns are kept apart on purpose:

| Concern | File | Becomes in NiFi |
|---|---|---|
| Schema - columns, types, nullability | `schemas/<system>/<db>/<table>.avsc` | `#{schema.text}` used by the record writer: only contract fields are read, in contract types |
| Config - keys, engine, schedule, target | `configs/<system>/to_<target>.yml` | one **parameter context** per table (inherits `connections`) |
| Logic - processors and wiring | `pipelines/<name>.json` | the flow inside each table's **process group**, every setting a `#{parameter}` |

## Connections

`configs/connections.yml` → NiFi-native chain:

```
.env (NIFI_CONN_*, SC_CLICKHOUSE_CLOUD_*) -> container env CONN_*  (docker-compose-nifi.base.yml)
    -> Parameter Provider "env-connections"  (Environment Variable provider, CONN_.* only)
    -> Parameter Context "connections"       (*_PASSWORD params stored as sensitive)
    -> Controller Services in the root group: postgres-local, mysql-local, clickhouse, clickhouse-sc
```

Unset `NIFI_CONN_*` values fall back to the local `postgres` / `mysql` / `clickhouse-server` containers. `clickhouse-sc` is ClickHouse Cloud, built from `SC_CLICKHOUSE_CLOUD_*` (port must be the HTTPS one, 8443).

## Pipelines

A config file lists groups of tables that share a source and target:

```yaml
# configs/mysql/to_clickhouse.yml
etl_mysql_reporting_service:
  pipeline: jdbc_incremental_to_clickhouse   # pipelines/<name>.json
  source_connection: mysql-local
  target_connection: clickhouse-sc
  source_db: test_reporting_service
  target_db: test
  defaults:                                  # overridable per table
    batch_size: 5000
    schedule: 30 min                         # or cron: "0 0 */2 * * ?"
    partition_column: id
    synced_at_column: _synced_at
  tables:
    - name: ml_payg_interventions
      target_table: test_nifi_reporting_service_ml_payg_interventions
      incremental_key: updatedAt
      engine: ReplacingMergeTree(updatedAt)
      order_by: id
```

Each table becomes `mysql → clickhouse` › `etl_mysql_reporting_service` › `ml_payg_interventions` in the NiFi canvas. The full option list is documented at the top of the config file.

**What one cycle does** (`jdbc_incremental_to_clickhouse`):

```
trigger (schedule / cron from the config)
 -> ensure target table   CREATE TABLE IF NOT EXISTS, generated from schema + config (engine, order_by)
 -> plan incremental queries   GenerateTableFetch: rows with incremental_key > last seen value,
                               split into pages by partition_column ranges
 -> read rows             ExecuteSQLRecord: rows -> contract-shaped Avro
 -> write to target       PutDatabaseRecord: one INSERT batch per page
failures (any step) -> queue into the funnel; right-click the queue > List queue to inspect
```

- **When it runs**: `schedule: 30 min` / `2 hr` / `1 day` = NiFi *timer driven* (once on start, then every interval); `cron: "0 30 6 * * ?"` = NiFi *CRON driven* at clock times (Quartz format, seconds first, UTC). Set in `defaults` or per table; the table's own setting wins. Default: 30 min.
- **No manual DDL**: the target table is created by the flow itself from the schema + config.
- **Upsert** comes from the ClickHouse engine: NiFi only INSERTs; `ReplacingMergeTree(updatedAt) ORDER BY id` keeps the latest version per id. Query with `FINAL` for exact results before background merges run.
- **Incremental state** (the high-water mark) is kept by NiFi: right-click *plan incremental queries* > View state. Clearing it forces a full reload (safe with ReplacingMergeTree).
- **Limits**: rows updated with the *same* `updatedAt` as the stored mark after a cycle ran are missed; hard deletes aren't seen (that needs CDC, e.g. `CaptureChangeMySQL`). An index on the incremental column keeps large tables cheap to poll.

### Adding things

**No contract, no pipeline.** The engineer building a pipeline writes its contract - the fields it needs and their types - and deploys it with the config. Nothing generates contracts. On every provisioning run:

- A table in a config **without** `schemas/<system>/<db>/<table>.avsc` fails and is skipped (other tables still provision).
- A table **with** a contract is drift-checked against the live source: a contract column missing in the source is an error (table skipped - the sync would fail); source columns not in the contract, or differing types, are notices (fine when intentional - the contract decides).

| You want | Change |
|---|---|
| Another table, same source/target | Write `schemas/mysql/<db>/<table>.avsc` + one entry under `tables:` |
| Fewer columns synced | Remove fields from the table's `.avsc` |
| A different engine / sort key for one table | Set `engine` / `order_by` on that table entry |
| The same table to another target | A new `configs/mysql/to_<target>.yml` (+ a template and DDL generator for that target); the schema is reused |

Then `make nifi-provision` (or just restart). Template, parameter and schema changes are applied in place; incremental state and queued data are kept.

## Commands

First time on a new machine, create the network and the external volumes. Compose never creates or deletes them:

```sh
docker network create data-ops-network
docker volume create nifi-vol
docker volume create nifi-flows
```

| After changing | Run |
|---|---|
| `configs/`, `schemas/` or `pipelines/` | `make nifi-provision` (preview: `make nifi-provision-dry-run`) |
| A `NIFI_CONN_*` / `SC_CLICKHOUSE_CLOUD_*` value in `.env` | `make nifi-dev-restart` (the nifi container must see the new env) |
| Which `#{param}` a sensitive property references | `docker-compose ... run --rm nifi-provisioner --force` (NiFi masks sensitive values, so this can't be detected) |
| The Dockerfile (drivers) | `make nifi-dev-up-build` |

To check a connection really works: root canvas > right-click > Controller Services > disable the service > **Verify** (checkmark icon) > enable it again.

## Notes

- ClickHouse Cloud services idle when unused; the first cycle after a wake-up can fail with `Read timed out`. The trigger retries every cycle, so it recovers on its own.
- The NiFi container has a fixed `hostname: nifi` - the self-signed certificate NiFi generates on first start (kept in the `nifi-vol` volume) is issued for it.
