# Redash

## Table of Contents

# Visualizations Supported by Redash

1. Boxplot
2. Chart
3. Cohort
4. Counter
5. Funnel
6. Map
7. Pivot Table
8. Sankey
9. Sunburst
10. Word Cloud

# Redash Pricing

1. The Starter pack costs $49/month but only allows you to connect with three data sources.
2. The Professional version costs $99/month and allows 10 data sources.
3. The Business version is priced at $450/month and has unlimited data sources and dashboards.

# Local Setup

Runs as three services (**server**, **scheduler**, **worker**) sharing the stack's existing Postgres and Redis — see `docker-compose-redash.base.yml` (+ `.dev.yml` / `.prod.yml` overrides).

1. `make postgres-dev-up` / `make redis-dev-up` (if not already running)
2. `make redash-init-db` — **one-time, required**. Unlike Metabase/Superset, Redash does not run its schema migrations on boot; this runs `create_db` to set them up. Skipping it leaves the server erroring against an empty database.
3. `make redash-dev-up` — starts server/scheduler/worker at http://localhost:5001

# Provisioning

Declarative, re-runnable provisioning of Redash **data sources** and
**dashboards** via its REST API — mirrors `../04_metabase/provisioning`
(runtime API calls against the running container) rather than
`../01_superset/provisioning` (baked into the image at build time), since
Redash here runs the stock `redash/redash` image with no custom Dockerfile.

| Path | Purpose |
|------|---------|
| `provisioning/data_sources.json` | Manifest of Redash data source connections. Secrets referenced by `${ENV_VAR}` name only, resolved from the repo-root `.env`. |
| `provisioning/dashboards/*.yml` | One file per dashboard: its widgets, each backed by its own query + visualization. See `global_overview.yml` for the full format docstring. |
| `provisioning/provision_redash.py` | Idempotent script: authenticates with a Redash user API key (`Authorization: Key <key>`, from an admin's profile page — Redash has no `/api/session`-style email+password login for automation), then creates/updates data sources, queries, visualizations, dashboards, and widgets by name. |

## Usage

```bash
# from the repo root
make redash-provision            # apply data sources + dashboards
make redash-provision-dry-run    # preview data-source changes, secrets redacted (dashboards need a live run)
```

## Dashboards

Three dashboards port the KPIs from `../01_superset/provisioning/dashboards/sales_overview.yml`
(same `marts.mart_accounts`-backed `sales_report_cte`: latest snapshot per
account, excluding refunds) onto Redash's query/visualization/widget model —
Sales, Selling Agents, and Agent Productivity counters (Today/This Week/This
Month/YTD), plus trend lines and (Global only) a country-split pie:

- **Global Overview** — both Kenya and Uganda
- **SunCulture Dashboard - Ke** — Kenya only
- **SunCulture Dashboard - Ug** — Uganda only

One simplification vs. the Superset version: Redash's `COUNTER` visualization
shows a single current value, not a built-in "% vs prior period" delta, so
those comparison cards were dropped rather than faked with a second query
per KPI.

## Notes

- `provision_redash.py` does one full listing of existing queries/dashboards
  and matches by exact name client-side, rather than using Redash's `q=`
  search parameter — that's full-text search, not exact-match, and silently
  returned the wrong country's queries for short tokens like "Ke" during
  testing (a real bug, not a hypothetical).
- `REDASH_API_KEY` (in the repo-root `.env`) is the first admin's key,
  fetched straight from Redash's own Postgres right after `make
  redash-init-db` — see the script's docstring for the query.

# Resources and Further Reading

1. [GitHub - Redash](https://github.com/getredash/redash) is an open-source data collaboration platform that enables you to connect to any data source, visualize data and share it.
