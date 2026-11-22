# Changelog

## [0.1.0] - 2026-11-22

**Contributors:** Rodgers Nyangweso

### Added

- Next.js 16 app (App Router, React 19, Turbopack) in the `web-apps` pnpm workspace, sharing its `node_modules` and lockfile; port 3013 (`DATA_PORTAL_HOST_PORT`).
- Home page (`src/app/page.js`) and root layout with a system font stack and light/dark colour tokens (`src/app/globals.css`); no `next/font/google`, so builds need no network for fonts.
- Backend as Next.js route handlers in `src/app/api/`, starting with `GET /api/health` → `{"status":"ok"}` (`force-dynamic`), used for container health checks.
- Component folders `src/components/{dataTable,filters,layout,navigation,ui,utils}/` (placeholders, `.gitkeep`), carried over from the `07_dashboards/data_portal_v1` skeleton.
- ESLint 9 flat config (`eslint.config.mjs`, `eslint-config-next/core-web-vitals`), `jsconfig.json` with the `@/*` → `src/*` alias, `next.config.mjs` (`standalone` output, workspace tracing root).
- Run/deploy wiring: `pnpm dev:data-portal`, `make data-portal-*` (dev builds the image locally; prod pulls `ghcr.io/nyangweso-rodgers/data-ops/data-portal:<tag>`), `data-portal` service in `docker-compose-web-apps.*.yml`, and the CI build matrix.
- `docs/architecture.md`.

### Deleted

- `07_dashboards/data_portal_v1/` - untracked skeleton with only empty folders and a 0-byte `docker-compose.data-portal-v1.yml`; superseded by this app.
