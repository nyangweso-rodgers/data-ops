# data-portal

Data portal for browsing and filtering data-ops datasets (scaffold: structure, build and deployment in place, data features to come).

Part of the `web-apps` pnpm workspace - [workspace README](../../README.md) ·
[stack architecture](../../docs/architecture.md) · [app architecture](docs/architecture.md) · [CHANGELOG](CHANGELOG.md). Port **3013** (`DATA_PORTAL_HOST_PORT` in `ports.env`).

## Getting started

One-time setup (Node.js, pnpm, `pnpm install` from `web-apps/`): see the
[workspace README](../../README.md#getting-started-local-without-docker).

From `web-apps/`:

```sh
pnpm --filter data-portal dev      # hot reload  -> http://localhost:3013
pnpm --filter data-portal build    # production build
pnpm --filter data-portal start    # serve that build on 3013
pnpm --filter data-portal lint     # ESLint (next build doesn't lint)
# shortcut: pnpm dev:data-portal
```

Or from this folder (`web-apps/apps/data-portal/`): `pnpm dev`, `pnpm build`, `pnpm start`, `pnpm lint`.
Add dependencies with `pnpm --filter data-portal add <pkg>` (never `npm install` here).

- **Needs:** nothing else yet - no database or env vars (see [docs/architecture.md](docs/architecture.md#configuration) for how a data source gets added).
- **Port 3013 is shared with Docker:** if it's taken (`EADDRINUSE`), stop the container first -
  `make data-portal-dev-down` from `data-ops/`.

## Docker

Runs the production image (no hot reload), from `data-ops/` or `web-apps/`:

```sh
make data-portal-dev-up        # build if changed + start  -> http://localhost:3013
make data-portal-dev-logs
make data-portal-dev-shell     # shell in the container
make data-portal-dev-down      # stop + remove (image kept)
make data-portal-prod-up WEB_APPS_IMAGE_TAG=sha-<commit>   # production: pull the CI image
```

## Layout

- `src/app/` - pages (App Router)
- `src/app/api/` - backend: route handlers (`/api/health` -> `{"status":"ok"}`, used for health checks)
- `src/components/{dataTable,filters,layout,navigation,ui,utils}/` - shared UI, imported as `@/components/...` (carried over from `07_dashboards/data_portal_v1`)
