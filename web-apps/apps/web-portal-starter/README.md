# web-portal-starter

Minimal Next.js + Bootstrap starter - a clean base to copy when starting a new app. No database.

Part of the `web-apps` pnpm workspace - [workspace README](../../README.md) ·
[stack architecture](../../docs/architecture.md). Port **3012** (`WEB_PORTAL_STARTER_HOST_PORT` in `ports.env`).

## Getting started

One-time setup (Node.js, pnpm, `pnpm install` from `web-apps/`): see the
[workspace README](../../README.md#getting-started-local-without-docker).

From `web-apps/`:

```sh
pnpm --filter web-portal-starter dev      # hot reload  -> http://localhost:3012
pnpm --filter web-portal-starter build    # production build
pnpm --filter web-portal-starter start    # serve that build on 3012
pnpm --filter web-portal-starter lint     # ESLint (next build doesn't lint)
# shortcut: pnpm dev:portal-starter
```

Or from this folder (`web-apps/apps/web-portal-starter/`): `pnpm dev`, `pnpm build`, `pnpm start`, `pnpm lint`.
Add dependencies with `pnpm --filter web-portal-starter add <pkg>` (never `npm install` here).

- **Needs:** nothing else - no database or env vars.
- **Port 3012 is shared with Docker:** if it's taken (`EADDRINUSE`), stop the container first -
  `make web-portal-starter-dev-down` from `data-ops/`.

## Docker

Runs the production image (no hot reload), from `data-ops/` or `web-apps/`:

```sh
make web-portal-starter-dev-up        # build if changed + start  -> http://localhost:3012
make web-portal-starter-dev-logs
make web-portal-starter-dev-shell     # shell in the container
make web-portal-starter-dev-down      # stop + remove (image kept)
make web-portal-starter-prod-up WEB_APPS_IMAGE_TAG=sha-<commit>   # production: pull the CI image
```

## Layout

- `src/app/page.js`, `layout.js`, `globals.css` - home page and root layout
- `src/app/components/navigation/header/` - header
- `src/app/styles/` - CSS modules
