# Changelog

## [1.1.1] - 2026-11-22

**Contributors:** Rodgers Nyangweso

### Added

- pnpm workspace (`package.json`, `pnpm-workspace.yaml` = `apps/*` + `packages/*`, one `pnpm-lock.yaml`, pnpm pinned via `packageManager`); root scripts `dev:portal`, `dev:survey`, `dev:portal-starter`.
- Shared multi-stage `Dockerfile` (`--build-arg APP=<app>`, Next.js `standalone` output, non-root user) + `.dockerignore`.
- `docker-compose-web-apps.{base,dev,prod}.yml` and `Makefile` with per-app targets (`make <app>-dev-up`, `-dev-logs`, `-dev-shell`, ...) plus all-apps targets (`make web-apps-dev-up`); root Makefile delegates `web-apps-%`, `web-portal-%`, `survey-app-%`, `web-portal-starter-%`.
- Host ports in `ports.env`: `WEB_PORTAL_HOST_PORT=3010`, `SURVEY_APP_HOST_PORT=3011`, `WEB_PORTAL_STARTER_HOST_PORT=3012` (also used by `pnpm dev`).
- Postgres schemas `web_portal` and `survey_app` in `WEB_APPS_POSTGRES_DB` (created with `prisma db push`).
- Per-app `src/app/lib/postgres-url.*` (builds the URL from `WEB_APPS_POSTGRES_*`) and `prisma.config.mjs` (Prisma CLI connection + migrations path); `pnpm --filter <app> prisma <cmd>`.
- Root `.env` / `.env.example`: `WEB_APPS_POSTGRES_{HOST,PORT,USER,PASSWORD,DB}` and `WEB_APPS_MONGODB_URI` (host-run values; compose overrides the hosts).
- README: layout, databases, Docker and Vercel sections.
- `docs/architecture.md`: stack architecture + open items (`WA*`).
- `apps/data-portal`: new Next.js 16 app (port 3013, `DATA_PORTAL_HOST_PORT`) from the empty `07_dashboards/data_portal_v1` skeleton - its component folders under `src/components/`, backend as route handlers (`/api/health`); wired into the workspace (`dev:data-portal`), compose, `make data-portal-*` and the CI matrix. App-level history: [apps/data-portal/CHANGELOG.md](apps/data-portal/CHANGELOG.md).
- WA3: CI image builds - `.github/workflows/web-apps-images.yml` builds all apps on PRs and pushes `ghcr.io/nyangweso-rodgers/data-ops/<app>:sha-<commit>` + `:latest` on `main`. Prod compose pulls those images (`WEB_APPS_IMAGE_TAG` required, `WEB_APPS_IMAGE_REGISTRY` optional) instead of building on the server; `make <app>-prod-up` = pull + up.
- WA4: Prisma Migrate for web-portal and survey-app - baseline migration `prisma/migrations/0_init` (marked applied on the existing schemas, no drift) and `db:migrate` / `db:deploy` / `db:status` scripts. `prisma db push` is no longer used.

### Fixed

- web-portal build: restored `globals.css` and `buttons.module.css` (deleted in `6ce553b` / `2bff71b` but still imported).
- web-portal Mongo connection: no longer logs the URI (password), no undeclared `isConnected` (reported successful connects as errors), reuses one cached connection, fails fast (5 s) and lazily checks the env var so `next build` doesn't need it.
- `submit-participants-survey` no longer closes the shared Mongo connection per request; Mongo/Prisma connect calls moved inside route `try` blocks.
- Report pages (`view-customers`, `view-participants-survey`) query the DB directly instead of fetching `http://localhost:3003` (wrong port, unreachable at build time); they and the GET API routes are `force-dynamic`. Customers table shows `created_at`/`updated_at`; "Agreed To Terms" renders Yes/No.
- Prisma apps generate into `src/generated/prisma`, so the two schemas no longer overwrite each other's client in the shared store.
- Port clashes: web-portal 3004 (Dagster) and survey-app 3002 (Docusaurus).
- WA1: linting never ran - `.eslintrc.json` extended the nonexistent `next/babel` (now `next/core-web-vitals` only), and pnpm had auto-installed TypeScript 7 as `@typescript-eslint/parser`'s peer, which crashes it (TypeScript now capped, see WA8). Fixed the two lint errors this surfaced in web-portal (unescaped `'` in JSX).
- WA6: the Windows `EPERM` race when both apps ran `prisma generate` at once is gone with Prisma 7 (no query engine binary to write; 5/5 parallel generate runs clean). Pruned the orphaned Prisma 5 packages from the store.
- web-portal: `participants-survey-schema.js` reuses the registered Mongoose model (`mongoose.models.participants_survey ??`), fixing `OverwriteModelError` (500 on `/api/get-participants-survey`) when the module is loaded more than once (Turbopack bundles, dev hot reload).
- WA7: web-portal sidebar dead links - the three report links pointed at `/marketing-reports/...` (now `/marketing/reports/...`); removed the "Deligates Survey" form link (no such page; the `DelegatesSurvey` Prisma model has no form yet).

### Changed

- Layout: `web_apps/web-apps/<app>` and root `next.js-web-portal/` → `web-apps/apps/<app>`; renamed `next.js-web-portal` → `web-portal`, `next.js-survey-app` → `survey-app`, the former `web_apps` portal starter → `web-portal-starter`.
- npm → pnpm (one shared store instead of a `node_modules` copy per app).
- Postgres: `POSTGRES_TEST_DATABASE_URL` / `POSTGRES_SURVEY_DATABASE_URL` → `WEB_APPS_POSTGRES_*` parts (full URL never stored).
- WA2: the apps' own neutral `WEB_APPS_*` env vars (same names locally, on Vercel and in prod) replace the shared `LOCAL_POSTGRES_*` / `LOCAL_MONGODB_URI` and the `LOCAL_POSTGRES_DB_HOST` fallback; `LOCAL_POSTGRES_*` stays for other stacks.
- Compose: `build:` moved from base to the dev override (local builds), prod override sets the registry `image:`.
- `next.config.mjs`: `output: "standalone"` (skipped on Windows) + `outputFileTracingRoot` = workspace root.
- WA5: Prisma 5.22 → 7.10.1 (web-portal, survey-app): `prisma-client` generator, connection in `prisma.config.mjs` (removed from `schema.prisma`), `@prisma/adapter-pg` driver adapter with the Postgres schema as an adapter option, `db:migrate` runs `prisma generate` explicitly. Migrations, status and drift unchanged.
- Node.js 23.7 (EOL, unsupported by Prisma 7) → 24.22.3 LTS on the host; Docker image `node:22.12.0-alpine3.20` → `node:24.22.3-alpine3.24`, dropped `openssl` and the Prisma engine copy.
- WA8: Next.js 14 → 16.4.6 (Turbopack builds) and React 18 → 19.3.1 in all apps; ESLint 8 → 9 with flat `eslint.config.mjs` (replaces `.eslintrc.json`), `lint` = `eslint .`. `eslint-config-next@16` uses current `typescript-eslint`, whose declared `typescript <6.1.0` range pnpm honours, so the manual TypeScript cap (`pnpm.overrides`) is removed. CI gained a `lint` job since `next build` no longer lints.

### Deleted

- `07_dashboards/data_portal_v1/` (untracked, only empty folders and a 0-byte compose file; replaced by `apps/data-portal`).
- Per-app `package-lock.json`, `Dockerfile` and `.dockerignore` (replaced by the workspace lockfile and shared Dockerfile).
- Per-app `scripts/prisma.mjs` CLI wrappers (replaced by `prisma.config.mjs`).
- Per-app `.eslintrc.json` (replaced by `eslint.config.mjs`) and the root `pnpm.overrides` TypeScript cap.
