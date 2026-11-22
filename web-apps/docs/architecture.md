# Web apps - Architecture

Customer-facing Next.js apps live in one **pnpm workspace** at `web-apps/` ([README](../README.md)). It's the one stack in the repo that is a code workspace as well as a compose stack. Repo-wide conventions (ports, network, Makefile delegation) are in the [root architecture doc](../../docs/architecture.md); this stack's open items are under [Open items](#open-items) below.

## Layout

```
web-apps/
├── package.json, pnpm-workspace.yaml, pnpm-lock.yaml   # workspace: apps/* + packages/*, one lockfile
├── Dockerfile, .dockerignore                           # one image recipe, --build-arg APP=<app>
├── docker-compose-web-apps.{base,dev,prod}.yml, Makefile
├── apps/{web-portal, survey-app, web-portal-starter, data-portal}/
└── packages/                                           # shared code - created when first needed
```

| App | Host port | Data |
| --- | --- | --- |
| web-portal | `WEB_PORTAL_HOST_PORT` (3010) | postgres `WEB_APPS_POSTGRES_DB`, schema `web_portal` (Prisma); mongodb `survey_service` (Mongoose) |
| survey-app | `SURVEY_APP_HOST_PORT` (3011) | postgres `WEB_APPS_POSTGRES_DB`, schema `survey_app` (Prisma) |
| web-portal-starter | `WEB_PORTAL_STARTER_HOST_PORT` (3012) | – |
| data-portal ([architecture](../apps/data-portal/docs/architecture.md)) | `DATA_PORTAL_HOST_PORT` (3013) | – (scaffold; backend = route handlers in `src/app/api/`, `/api/health`) |

## Dependencies

pnpm keeps one copy of each package version in `web-apps/node_modules/.pnpm`; each app's `node_modules` only holds links to the versions it declares (apps may pin different versions, e.g. Next 14.2.3 vs 14.2.7). pnpm is pinned with `packageManager`; run `corepack enable` once on the host.

- **Node.js:** 24 LTS on the host and in the image (`node:24.22.3-alpine3.24`). Prisma 7 needs 20.19+, 22.12+ or 24+.
- **Framework:** Next.js 16 (App Router, Turbopack for `next dev` and `next build`) with React 19 - all apps on the same versions.
- **Linting:** ESLint 9 with a flat `eslint.config.mjs` per app (`eslint-config-next/core-web-vitals`, `src/generated/**` ignored); `pnpm --filter <app> lint` or `pnpm -r lint`. Next.js 16 removed `next lint` and `next build` no longer lints, so CI runs lint as its own job.
- **TypeScript** (no app is written in it, but `eslint-config-next` loads it through `typescript-eslint`) isn't pinned: `typescript-eslint` declares `typescript: ">=4.8.4 <6.1.0"` and pnpm keeps the resolved version inside that range by itself (a fresh resolution picks 6.0.x; the lockfile has 5.9.3). TypeScript 7 becomes possible when a `typescript-eslint` release widens that range - no workspace change needed.

## Running: native vs Docker

- **Native (day-to-day):** `pnpm dev:portal` etc., hot reload, against the databases' published ports.
- **Docker (dev):** `make <app>-dev-up` builds the *production* image locally and runs it on `data-ops-network`, to test it next to the data stack.
- **Docker (prod):** `make <app>-prod-up WEB_APPS_IMAGE_TAG=<tag>` pulls the image CI pushed and runs it with restart policy, resource limits and log rotation; nothing is built on the server. `build:` lives only in the dev override, `image:` (registry) only in the prod one.
- Each app has its own targets (`make web-portal-dev-up`, `make survey-app-dev-logs`, `make <app>-dev-shell`, ...); `make web-apps-<target>` acts on all apps.

## Image

The shared `Dockerfile`:

1. installs pnpm (version from `packageManager`) with npm - not corepack, whose bundled signing keys can lag npm's (and Node 25+ drops corepack);
2. runs `pnpm fetch` (layer cached until the lockfile changes);
3. installs only `APP` and its deps offline (`postinstall` runs `prisma generate`), then builds (`next build`, Turbopack; no lint - that's a CI job);
4. copies just Next.js `standalone` output + static assets into a non-root Alpine runner (`node server.js`, port 3000). There's no Prisma engine to ship: the Prisma 7 client is compiled into the build and `@prisma/adapter-pg` is traced into the standalone `node_modules`.

`next.config.mjs` sets `outputFileTracingRoot` to the workspace root. `standalone` is skipped on Windows (pnpm's symlinks need Developer Mode), so it only appears in Linux/Docker builds.

## Configuration

- Apps read the repo-root `.env` with `dotenv` (path `../../../.env` from the app folder) when run on the host. In Docker the file isn't in the image; compose passes it via `env_file`.
- The apps have their own settings, separate from the `LOCAL_POSTGRES_*` vars other stacks (Dagster) use, and the same names apply on every platform (`.env` locally, project env vars on Vercel):

  | Variable | Purpose |
  | --- | --- |
  | `WEB_APPS_POSTGRES_HOST`, `_PORT`, `_USER`, `_PASSWORD`, `_DB` | Postgres connection (each app uses its own Postgres schema) |
  | `WEB_APPS_MONGODB_URI` | MongoDB connection (web-portal) |

- Postgres URLs are built in code from those parts (`src/app/lib/postgres-url.*`); the app's Postgres schema is passed to the driver adapter at runtime and appended as `?schema=` for the Prisma CLI.
- Host vs container differences are explicit: `.env` has `WEB_APPS_POSTGRES_HOST=localhost` and `WEB_APPS_MONGODB_URI=...@localhost`; compose overrides them with the service names (`postgres`, `mongodb`) and container ports.

## Prisma

Prisma ORM 7 (`prisma`, `@prisma/client`, `@prisma/adapter-pg` 7.10.x; the CLI's npm `latest` tag points at an 8.0 release candidate, so versions are pinned).

- **Client:** `prisma-client` generator, output `src/generated/prisma` per app (TypeScript, compiled by Next.js; not the shared `@prisma/client`, which both apps would overwrite). No Rust query engine binary. `src/app/lib/prisma.js` connects through the node-postgres driver adapter: `new PrismaPg({ connectionString }, { schema: <app schema> })`.
- **CLI config:** each app's `prisma.config.mjs` holds the schema path, migrations path and connection URL (built by the same `postgres-url.*`, with `?schema=`); Prisma 7 no longer reads a URL from `schema.prisma` or loads `.env` itself. The URL is empty when `WEB_APPS_POSTGRES_*` aren't set, so `prisma generate` works in Docker/Vercel builds without a database.
- Schema changes use **Prisma Migrate**; each app's history lives in `prisma/migrations/` (committed). `0_init` is a baseline: generated from the schema the tables were first created with (`prisma db push`) and marked applied with `prisma migrate resolve`, so existing databases weren't recreated.
  - Dev: `pnpm --filter <app> db:migrate --name <change>` (`migrate dev` then `prisma generate`, which Prisma 7 no longer runs automatically; `migrate dev` uses a temporary shadow database, so the Postgres user needs `CREATEDB`).
  - Deploy: `pnpm --filter <app> db:deploy` (`migrate deploy`: applies pending migrations only) from CI or the Vercel build command, before the new code serves traffic. The Docker image doesn't run migrations.
  - Check: `pnpm --filter <app> db:status`.
- Other Prisma commands: `pnpm --filter <app> prisma <command>` (e.g. `prisma studio`); they all read `prisma.config.mjs`, so the full URL is never stored.

## Rendering

Pages and GET routes that read live data are `force-dynamic` and query the database directly (no HTTP calls to the app's own `/api`), so `next build` never needs a database.

## Deployment

- **Vercel (current):** one project per app with Root Directory `web-apps/apps/<app>`. Vercel detects pnpm and the workspace and ignores the Dockerfile and compose files. Env vars must point at databases reachable from Vercel.
- **Self-hosted:** images are built once in CI and pulled by the servers.
  - [`.github/workflows/web-apps-images.yml`](../../.github/workflows/web-apps-images.yml) builds every app (matrix) from `web-apps/Dockerfile`. Pull requests touching `web-apps/` build only; pushes to `main` also push `ghcr.io/nyangweso-rodgers/data-ops/<app>:sha-<7-char commit>` and `:latest` with the built-in `GITHUB_TOKEN` (no registry secrets). Layers are cached per app in the GitHub Actions cache.
  - A server runs `make <app>-prod-up WEB_APPS_IMAGE_TAG=sha-<commit>` (or sets the tag in `.env`); the tag is required, so a deploy is always an explicit version, and rolling back is the same command with the previous tag. `WEB_APPS_IMAGE_REGISTRY` overrides the registry path.
  - New GHCR packages are private: either make each package public (package settings) or `docker login ghcr.io` on the server with a token that has `read:packages`.
  - Run `pnpm --filter <app> db:deploy` against the prod database before starting a new tag that brings migrations.
  - Any other container platform can run the same images.

## Extracting this stack

`web-apps/` is self-contained except for these files outside it. To move it into its own repository (or into another repo), bring or recreate them:

| Outside `web-apps/` | What web-apps uses | In a standalone repo |
| --- | --- | --- |
| `.github/workflows/web-apps-images.yml` | CI: lint + image build/push (here because GitHub only reads root workflows) | Move to the new repo's `.github/workflows/`; drop the `web-apps/` prefixes (see the file's header) |
| `ports.env` | `WEB_PORTAL_HOST_PORT`, `SURVEY_APP_HOST_PORT`, `WEB_PORTAL_STARTER_HOST_PORT`, `DATA_PORTAL_HOST_PORT` (Makefile `include`, compose `--env-file`) | Copy the four lines into a `ports.env` next to the compose files; update the `../ports.env` paths in `Makefile` |
| `.env` / `.env.example` | `WEB_APPS_POSTGRES_*`, `WEB_APPS_MONGODB_URI`, `WEB_APPS_IMAGE_TAG`, and `MONGODB_INITDB_ROOT_*` (compose builds the in-Docker Mongo URI from them) | Own `.env`; update `../.env` in `Makefile` and the compose `env_file`, and `../../../.env` in `src/app/lib/postgres-url.*` and the Mongo connection file |
| `Makefile` (root) | `WEB_APPS_DIR`, delegation rules `web-apps-%`, `web-portal-%`, `survey-app-%`, `web-portal-starter-%`, `data-portal-%`, help block | Not needed - run `make -C web-apps <target>` or `make <target>` inside the folder |
| `docs/architecture.md` (root) | Services table row linking here | Not needed |
| Other stacks | `postgres` (01-databases/01-postgres) and `mongodb` (01-databases/mongodb) on the external `data-ops-network` | Point `WEB_APPS_POSTGRES_*` / `WEB_APPS_MONGODB_URI` and the compose overrides at your databases; create the network or drop `external: true` |

Everything else (apps, workspace, lockfile, Dockerfile, compose files, Makefile, Prisma configs and migrations, docs) is inside `web-apps/`.

## Open items

IDs are stable (closed items are removed, not renumbered); fixes are logged in the [CHANGELOG](../CHANGELOG.md). Next free ID: WA9.

None open.

