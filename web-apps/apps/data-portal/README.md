# data-portal

Next.js 16 app in the `web-apps` pnpm workspace (see [../../README.md](../../README.md) and
[../../docs/architecture.md](../../docs/architecture.md)). Port 3013 (`DATA_PORTAL_HOST_PORT`).

Architecture: [docs/architecture.md](docs/architecture.md) · History: [CHANGELOG.md](CHANGELOG.md)

```sh
pnpm dev:data-portal                 # from web-apps/: hot-reload dev on http://localhost:3013
pnpm --filter data-portal lint
make data-portal-dev-up              # Docker (production image), from data-ops/ or web-apps/
```

Layout:

- `src/app/` - pages (App Router)
- `src/app/api/` - backend: route handlers (`/api/health` for health checks)
- `src/components/{dataTable,filters,layout,navigation,ui,utils}/` - shared UI (carried over from `07_dashboards/data_portal_v1`)
