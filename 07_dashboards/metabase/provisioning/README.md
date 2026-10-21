# Metabase provisioning

Declarative, re-runnable provisioning of Metabase **database connections** via the
Metabase REST API — so connections are version-controlled instead of hand-clicked
in the UI.

## Files

| File | Purpose |
|------|---------|
| `databases.json` | Declarative manifest of connections. Secrets are referenced by `${ENV_VAR}` name only (resolved from the repo-root `.env`), so it is safe to commit. |
| `provision_metabase.py` | Idempotent script: authenticates as admin, then creates/updates each connection **by name**. |

## Usage

```bash
# from the repo root
make metabase-provision            # apply the manifest
make metabase-provision-dry-run    # preview changes, secrets redacted
```

Or directly:

```bash
python 07_dashboards/04_metabase/provisioning/provision_metabase.py --dry-run
```

## How it works

1. Reads `MB_ADMIN_EMAIL` / `MB_ADMIN_PASSWORD` and any `${VAR}` from the repo-root `.env`
   (process environment overrides `.env`, so a CI secret manager wins).
2. `POST /api/session` to get an admin session token.
3. `GET /api/database` to find existing connections by name.
4. For each manifest entry: `PUT` if a connection with that name exists, else `POST`.

Re-running is safe — existing connections are updated in place, never duplicated.
The script exits non-zero if any connection fails (e.g. its backing service is
down), so it can gate a deploy.

## Adding a connection

Append an object to `databases.json`. `engine` is Metabase's driver id
(`postgres`, `mysql`, `clickhouse`, `bigquery-cloud-sdk`, `snowflake`, ...).
Reference credentials as `${ENV_VAR}` and add those vars to the repo-root `.env`.

```json
{
  "name": "SC Reporting Service",
  "engine": "postgres",
  "details": {
    "host": "${SC_REPORTING_SERVICE_PG_DB_HOST}",
    "port": 5432,
    "dbname": "${SC_REPORTING_SERVICE_PG_DB_NAME}",
    "user": "${SC_REPORTING_SERVICE_PG_DB_USER}",
    "password": "${SC_REPORTING_SERVICE_PG_DB_PASSWORD}",
    "ssl": true
  }
}
```

## Notes

- Connections to services that aren't running (e.g. `clickhouse-server` when it's
  down) fail their connection test and are reported as failed; other connections
  still provision.
- Hostnames use Docker Compose **service names** (`postgres`, `mysql`,
  `clickhouse-server`) because Metabase talks to them over the shared
  `data-ops-network`, not `localhost`.
