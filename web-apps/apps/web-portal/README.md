# web-portal

Internal portal: marketing forms and reports (participants survey, delegates) and market-management (customer registration, customer reports).

Part of the `web-apps` pnpm workspace - [workspace README](../../README.md) ·
[stack architecture](../../docs/architecture.md). Port **3010** (`WEB_PORTAL_HOST_PORT` in `ports.env`).

## Getting started

One-time setup (Node.js, pnpm, `pnpm install` from `web-apps/`): see the
[workspace README](../../README.md#getting-started-local-without-docker).

From `web-apps/`:

```sh
pnpm --filter web-portal dev      # hot reload  -> http://localhost:3010
pnpm --filter web-portal build    # production build
pnpm --filter web-portal start    # serve that build on 3010
pnpm --filter web-portal lint     # ESLint (next build doesn't lint)
# shortcut: pnpm dev:portal
```

Or from this folder (`web-apps/apps/web-portal/`): `pnpm dev`, `pnpm build`, `pnpm start`, `pnpm lint`.
Add dependencies with `pnpm --filter web-portal add <pkg>` (never `npm install` here).

- **Needs:** Postgres (schema `web_portal`) and MongoDB (`survey_service`) running for the data pages - `WEB_APPS_POSTGRES_*` and `WEB_APPS_MONGODB_URI` in `data-ops/.env` (e.g. `make mongodb-dev-up`). Static pages work without them.
- **Port 3010 is shared with Docker:** if it's taken (`EADDRINUSE`), stop the container first -
  `make web-portal-dev-down` from `data-ops/`.

## Database

Postgres via Prisma 7: tables live in the `web_portal` schema of `WEB_APPS_POSTGRES_DB`
(models: `User`, `Customer`, `DelegatesSurvey`). Connection: `prisma.config.mjs` (CLI) and `src/app/lib/prisma.js` (app),
both built from `WEB_APPS_POSTGRES_*` in `data-ops/.env`.

```sh
pnpm --filter web-portal db:migrate --name <change>   # after editing prisma/schema.prisma
pnpm --filter web-portal db:status                    # applied vs pending migrations
pnpm --filter web-portal db:deploy                    # apply pending migrations (prod/CI)
pnpm --filter web-portal prisma studio                # browse the tables
```

Migration history: `prisma/migrations/` (committed). Don't use `prisma db push`.

MongoDB (Mongoose) holds the participants survey: `src/app/model/participants-survey-schema.js`, connection in `src/app/utils/participants-survey-mongodb-connection.js` (`WEB_APPS_MONGODB_URI`).

## Docker

Runs the production image (no hot reload), from `data-ops/` or `web-apps/`:

```sh
make web-portal-dev-up        # build if changed + start  -> http://localhost:3010
make web-portal-dev-logs
make web-portal-dev-shell     # shell in the container
make web-portal-dev-down      # stop + remove (image kept)
make web-portal-prod-up WEB_APPS_IMAGE_TAG=sha-<commit>   # production: pull the CI image
```

## Layout

- `src/app/marketing/` - forms (`participants-survey`, `register-delegates`) and reports (`view-participants-survey`, `view-delegates-survey`, `view-registered-delegates`)
- `src/app/market-management/` - forms (`register-customer`, `user-onboarding`) and reports (`view-customers`)
- `src/app/dashboard/` - dashboard page
- `src/app/api/` - route handlers: `get-customer` (Postgres), `get-participants-survey`, `get-participants-survey-data-v2`, `submit-participants-survey` (MongoDB)
- `src/app/components/` - header, left sidebar, error and success messages
- `src/app/lib/` - Prisma client + Postgres URL builder; `src/app/model/`, `src/app/utils/` - Mongoose model + connection
- `src/app/styles/` - CSS modules; `prisma/` - schema + migrations; `src/generated/prisma/` - generated client (not committed)
