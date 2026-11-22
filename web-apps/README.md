# Web Applications

## Table Of Contents

1. [Layout](#layout)
2. [Databases](#databases)
3. [Getting started (local, without Docker)](#getting-started-local-without-docker)
4. [Docker (self-hosting)](#docker-self-hosting)
5. [Vercel](#vercel)

# Layout

How it fits together (dependencies, image, configuration, deployment): [docs/architecture.md](docs/architecture.md).

pnpm workspace: one shared `node_modules` + one `pnpm-lock.yaml` for all apps.

```
web-apps/
├── package.json          # workspace root (scripts, pinned pnpm)
├── pnpm-workspace.yaml   # apps/* + packages/*
├── pnpm-lock.yaml        # one lockfile for every app
├── Dockerfile            # one image recipe for every app (--build-arg APP=<folder>)
├── docker-compose-web-apps.{base,dev,prod}.yml
├── Makefile              # make web-apps-<target> from the repo root
├── apps/                 # Next.js apps
│   ├── web-portal/
│   ├── web-portal-starter/
│   ├── survey-app/
│   └── data-portal/
└── packages/             # shared code (ui, config) - create when first needed
```

| App | Port (`ports.env`) | Data |
| --- | --- | --- |
| `apps/web-portal` | 3010 `WEB_PORTAL_HOST_PORT` | Postgres schema `web_portal`, MongoDB `survey_service` |
| `apps/survey-app` | 3011 `SURVEY_APP_HOST_PORT` | Postgres schema `survey_app` |
| `apps/web-portal-starter` | 3012 `WEB_PORTAL_STARTER_HOST_PORT` | none |
| `apps/data-portal` | 3013 `DATA_PORTAL_HOST_PORT` | none yet (backend = route handlers in `src/app/api/`) |

The same port is used by `pnpm dev` (in each app's `package.json`) and by Docker, so only one of the two runs at a time.
Commands for installing, building and running: [Getting started](#getting-started-local-without-docker).

- New app: `pnpm create next-app apps/<name>` — anything under `apps/` (or `packages/`) joins the workspace automatically.
- Apps that read the repo-root `data-ops/.env` load it as `../../../.env` relative to the app folder; update that if an app moves.
- Prisma apps generate their client into `src/generated/prisma` (not the shared `@prisma/client`), so schemas from different apps don't overwrite each other.

## Databases

The apps read their own settings from `data-ops/.env` (template in `.env.example`):
`WEB_APPS_POSTGRES_HOST` / `_PORT` / `_USER` / `_PASSWORD` / `_DB` and `WEB_APPS_MONGODB_URI`.
Both Prisma apps build their connection URL from these (`src/app/lib/postgres-url.*`) and keep
their tables in their own schema of `WEB_APPS_POSTGRES_DB`. `.env` points at `localhost` for
host-run apps; Docker swaps in `postgres` / `mongodb`.

Schema changes go through **Prisma Migrate** (history in `prisma/migrations/`, committed):

```sh
pnpm --filter web-portal db:migrate --name add_phone   # after editing prisma/schema.prisma: creates + applies a migration
pnpm --filter web-portal db:status                     # applied vs pending migrations
pnpm --filter web-portal db:deploy                     # apply pending migrations (prod/CI, never creates any)
pnpm --filter survey-app prisma studio                 # any other Prisma command, same connection
```

Prisma 7 reads the connection from each app's `prisma.config.mjs`, which builds it from the
settings above (`db:migrate` also runs `prisma generate`, which Prisma 7 no longer does on its own).
Don't use `prisma db push` any more - it changes the database without recording a migration.

# Getting started (local, without Docker)

Build and run the apps directly on your machine - the fastest loop, with hot reload in `dev`.
Use **pnpm**, not npm: this is a pnpm workspace and dependencies are managed from `web-apps/`.

## One-time setup

- **Node.js** 20.19+, 22.12+ or 24+ (the repo uses 24 LTS, also in the Docker image).
- **pnpm**, at the version pinned in `package.json` (`packageManager`):

  ```sh
  corepack enable                # Node includes corepack; provides the pinned pnpm
  # if that fails with a permissions error (it writes to the Node install folder):
  npm install -g pnpm@9.15.0
  ```

- **Install** every app's dependencies, once and after pulling changes to any `package.json` or the lockfile:

  ```sh
  cd web-apps
  pnpm install                   # also generates the Prisma clients
  ```

## From `web-apps/`, naming the app

`--filter` takes the app's package name, which is the same as its folder name in `apps/`:

```sh
cd web-apps

pnpm --filter web-portal build      # build one app
pnpm --filter web-portal start      # run that build (production mode) on its port
pnpm --filter web-portal dev        # hot-reload dev server
pnpm --filter web-portal lint

pnpm -r build                       # build every app
pnpm -r lint                        # lint every app (next build no longer lints)
```

Shortcuts in `web-apps/package.json`:

```sh
pnpm dev:portal          # web-portal         -> http://localhost:3010
pnpm dev:survey          # survey-app         -> http://localhost:3011
pnpm dev:portal-starter  # web-portal-starter -> http://localhost:3012
pnpm dev:data-portal     # data-portal        -> http://localhost:3013
```

## Or from the app's own folder

```sh
cd web-apps/apps/web-portal
pnpm build
pnpm start
```

`npm run build` also works there, because `npm run` only executes the script and the
dependencies are already installed. **Never run `npm install` inside an app folder**: it
creates a separate `package-lock.json` and its own `node_modules` copy, which undoes the
shared setup. Add packages with pnpm instead:

```sh
pnpm --filter survey-app add zod         # runtime dependency of one app
pnpm --filter survey-app add -D vitest   # dev dependency
```

## Good to know

- **`build` needs no database** - data pages render per request, so it works with the databases stopped.
- **`start` / `dev` need the databases** for data pages: apps read `data-ops/.env` (`WEB_APPS_POSTGRES_*`
  -> `localhost`), so run Postgres and MongoDB (e.g. `make mongodb-dev-up` from `data-ops/`). See [Databases](#databases).
- **Ports are shared with Docker** (3010-3013): stop an app's container before running it locally,
  e.g. `make web-portal-dev-down`.
- **Schema changes:** `pnpm --filter <app> db:migrate --name <change>` (see [Databases](#databases)).
- **On Windows** `next build` produces a normal build, not `standalone` (that's only for the Docker image).

# Docker (self-hosting)

One multi-stage `Dockerfile` builds any app from the workspace root and ships only Next.js
`standalone` output. Hot-reload development stays native (`pnpm dev:*`); Docker is for running
the production image locally next to the data stack, or self-hosting.

Each app has its own commands (run from `data-ops/` or `web-apps/`), so you can work on one app at a time:

```sh
make web-portal-dev-up          # build if changed + start just the portal
make web-portal-dev-logs
make web-portal-dev-shell
make web-portal-dev-down        # stop + remove just the portal
make survey-app-dev-up-build    # rebuild without cache
make web-apps-dev-up            # all apps at once (also: web-apps-dev-down, -logs, -prod-up, ...)
```

`make help` (or `make -C web-apps help`) lists every target per app.

- Production runs images built by CI ([`web-apps-images.yml`](../.github/workflows/web-apps-images.yml): pushes `ghcr.io/nyangweso-rodgers/data-ops/<app>:sha-<commit>` and `:latest` on every push to `main`), never builds on the server:

  ```sh
  make web-portal-prod-up WEB_APPS_IMAGE_TAG=sha-1a2b3c4   # pull + start that version (roll back = previous tag)
  ```

  The tag is required. Private GHCR packages need `docker login ghcr.io` (token with `read:packages`) on the server.
- Inside Docker the apps reach `postgres` / `mongodb` on `data-ops-network`; compose overrides the host-only settings from `.env`.
- `output: "standalone"` is skipped on Windows (pnpm's symlinks need Developer Mode), so a local `next build` on Windows produces a normal build; Docker/Linux builds produce standalone.

# Vercel

Create one Vercel project per app from this repo, with **Root Directory** = `web-apps/apps/<app>`.
Vercel detects pnpm and the workspace from `web-apps/pnpm-lock.yaml`; the Dockerfile and compose files
are ignored. Set the env vars the app reads (`WEB_APPS_POSTGRES_*`, plus `WEB_APPS_MONGODB_URI` for
web-portal) in the project settings, pointing at databases reachable from Vercel (the local Docker ones aren't).
Apply migrations before (or as part of) each deploy: `pnpm --filter <app> db:deploy` against the target
database, from CI or as the project's build command (`pnpm db:deploy && pnpm build`).

# Resources and Further Reading

1. [getcssscan.com - css-buttons-examples](https://getcssscan.com/css-buttons-examples)
2. [https://www.programiz.com/css/button-styling](https://www.programiz.com/css/button-styling)
