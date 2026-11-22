# Data portal - Architecture

A Next.js app in the `web-apps` workspace. Shared stack concerns (pnpm workspace, the
Dockerfile, compose, CI, configuration conventions) are described once in the
[web-apps architecture doc](../../../docs/architecture.md); this page covers what is
specific to the data portal. It is currently a **scaffold**: the structure, build and
deployment are in place, the data features are not (see [Open items](#open-items)).

## Purpose

A web UI for browsing data-ops datasets: tables of records with filters, behind a
small server-side API. The component folders carried over from the original
`07_dashboards/data_portal_v1` skeleton (`dataTable`, `filters`, ...) reflect that intent.

## Layout

```
apps/data-portal/
├── package.json, next.config.mjs, eslint.config.mjs, jsconfig.json
├── public/                       # static assets (served from /)
├── docs/architecture.md          # this file
└── src/
    ├── app/                      # App Router: pages, layouts
    │   ├── layout.js, page.js, globals.css
    │   └── api/                  # backend: route handlers
    │       └── health/route.js   # GET /api/health
    └── components/               # shared UI, imported as "@/components/..."
        ├── dataTable/            # tabular views of records
        ├── filters/              # filter controls for those views
        ├── layout/               # page chrome (shells, grids)
        ├── navigation/           # menus, breadcrumbs
        ├── ui/                   # generic building blocks (buttons, inputs)
        └── utils/                # non-visual helpers used by components
```

`src/components/` sits outside `src/app/`, so nothing in it becomes a route.

## Frontend and backend in one app

The original skeleton had separate `frontend/` and `backend/` folders. Here both are one
Next.js app, the framework's own model:

- **Pages** are server components by default and can read data directly on the server;
  add `"use client"` only to components that need browser interactivity (e.g. filter
  controls).
- **Backend endpoints** are route handlers in `src/app/api/<name>/route.js` (`GET`,
  `POST`, ...). Use them for anything called from the browser or by other services.
  Server-rendered pages should query their data source directly rather than calling
  the app's own `/api` over HTTP.
- One build, one image, one port. If the API ever needs to be deployed or scaled on its
  own, split it into a separate workspace app (e.g. `apps/data-portal-api`) at that point.

## Rendering

The home page is static. `/api/health` is `force-dynamic` (never cached or prerendered).
Pages and routes that read live data must also be dynamic, so `next build` never needs a
database (same rule as the other apps).

## Configuration

None yet: the app reads no environment variables. When it gets a data source, follow
the web-apps conventions: `WEB_APPS_*` variables in `data-ops/.env` locally and in the
project settings on Vercel, a URL builder in `src/app/lib/`, and, for Postgres, Prisma 7
with this app's own Postgres schema (`data_portal`) and `prisma.config.mjs`, like
`web-portal` and `survey-app`.

## Running and deploying

| What | Command / value |
| --- | --- |
| Dev (hot reload) | `pnpm dev:data-portal` from `web-apps/` → http://localhost:3013 |
| Lint | `pnpm --filter data-portal lint` (also a CI job) |
| Docker, local build | `make data-portal-dev-up` / `-dev-logs` / `-dev-shell` / `-dev-down` |
| Docker, prod | `make data-portal-prod-up WEB_APPS_IMAGE_TAG=sha-<commit>` (pulls the CI image) |
| Image | `ghcr.io/nyangweso-rodgers/data-ops/data-portal:sha-<commit>` / `:latest` |
| Health check | `GET /api/health` → `{"status":"ok"}`; the container healthcheck requests `/` |
| Port | 3013, `DATA_PORTAL_HOST_PORT` in `ports.env` (container port 3000) |
| Vercel | Project Root Directory `web-apps/apps/data-portal` |

## Open items

IDs are stable (closed items are removed, not renumbered); fixes go in the
[CHANGELOG](../CHANGELOG.md). Next free ID: DP3.

- **DP1** No data source yet: decide what the portal reads (Postgres, ClickHouse, an
  existing API) and add its config following [Configuration](#configuration).
- **DP2** Component folders are placeholders (`.gitkeep`); build the first data table +
  filters page, and remove each `.gitkeep` once its folder has real files.
