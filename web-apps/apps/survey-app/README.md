# survey-app

Survey forms (participants survey, delegates survey) that store responses in Postgres.

Part of the `web-apps` pnpm workspace - [workspace README](../../README.md) ·
[stack architecture](../../docs/architecture.md). Port **3011** (`SURVEY_APP_HOST_PORT` in `ports.env`).

## Getting started

One-time setup (Node.js, pnpm, `pnpm install` from `web-apps/`): see the
[workspace README](../../README.md#getting-started-local-without-docker).

From `web-apps/`:

```sh
pnpm --filter survey-app dev      # hot reload  -> http://localhost:3011
pnpm --filter survey-app build    # production build
pnpm --filter survey-app start    # serve that build on 3011
pnpm --filter survey-app lint     # ESLint (next build doesn't lint)
# shortcut: pnpm dev:survey
```

Or from this folder (`web-apps/apps/survey-app/`): `pnpm dev`, `pnpm build`, `pnpm start`, `pnpm lint`.
Add dependencies with `pnpm --filter survey-app add <pkg>` (never `npm install` here).

- **Needs:** Postgres (schema `survey_app`) running to submit surveys - `WEB_APPS_POSTGRES_*` in `data-ops/.env`. Pages render without it.
- **Port 3011 is shared with Docker:** if it's taken (`EADDRINUSE`), stop the container first -
  `make survey-app-dev-down` from `data-ops/`.

## Database

Postgres via Prisma 7: tables live in the `survey_app` schema of `WEB_APPS_POSTGRES_DB`
(models: `ParticipantsSurvey`). Connection: `prisma.config.mjs` (CLI) and `src/app/lib/prisma.js` (app),
both built from `WEB_APPS_POSTGRES_*` in `data-ops/.env`.

```sh
pnpm --filter survey-app db:migrate --name <change>   # after editing prisma/schema.prisma
pnpm --filter survey-app db:status                    # applied vs pending migrations
pnpm --filter survey-app db:deploy                    # apply pending migrations (prod/CI)
pnpm --filter survey-app prisma studio                # browse the tables
```

Migration history: `prisma/migrations/` (committed). Don't use `prisma db push`.

## Docker

Runs the production image (no hot reload), from `data-ops/` or `web-apps/`:

```sh
make survey-app-dev-up        # build if changed + start  -> http://localhost:3011
make survey-app-dev-logs
make survey-app-dev-shell     # shell in the container
make survey-app-dev-down      # stop + remove (image kept)
make survey-app-prod-up WEB_APPS_IMAGE_TAG=sha-<commit>   # production: pull the CI image
```

## Layout

- `src/app/forms/` - `participants-survey`, `delegates-survey`
- `src/app/api/participant-survey/create-participant-survey/` - route handler that saves a response (Postgres)
- `src/app/components/navigation/header/` - header
- `src/app/lib/` - Prisma client + Postgres URL builder (`postgres-url.mjs`)
- `src/app/styles/` - CSS modules; `prisma/` - schema + migrations; `src/generated/prisma/` - generated client (not committed)
