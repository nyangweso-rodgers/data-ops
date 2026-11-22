# Web Applications

## Table Of Contents

# Layout

pnpm workspace: one shared `node_modules` + one `pnpm-lock.yaml` for all apps.

```
web-apps/
├── package.json          # workspace root (scripts, pinned pnpm)
├── pnpm-workspace.yaml   # apps/* + packages/*
├── pnpm-lock.yaml        # one lockfile for every app
├── apps/                 # Next.js apps
│   ├── web-portal/
│   ├── web-portal-starter/
│   └── survey-app/
└── packages/             # shared code (ui, config) - create when first needed
```

| App | Port |
| --- | --- |
| `apps/web-portal` | 3004 |
| `apps/web-portal-starter` | 3003 |
| `apps/survey-app` | 3002 |

```sh
corepack enable                                # once, makes `pnpm` available (pinned via packageManager)
pnpm install                                   # from web-apps/, installs every app
pnpm dev:portal                                # or: pnpm --filter <app> dev
pnpm --filter survey-app add zod              # add a dep to one app
```

- New app: `pnpm create next-app apps/<name>` — anything under `apps/` (or `packages/`) joins the workspace automatically.
- Apps that read the repo-root `data-ops/.env` load it as `../../../.env` relative to the app folder; update that if an app moves.
- Prisma apps generate their client into `src/generated/prisma` (not the shared `@prisma/client`), so schemas from different apps don't overwrite each other.

# Setup

## Step 1: Setup Next.js Application with Docker

- Check my, [github.com/nyangweso-rodgers - Setting up Next.js App](https://github.com/nyangweso-rodgers/Programming-with-JavaScript/blob/main/02-JavaScript-Libraries/01-React/03-React-Frameworks/01-Next.js/01-Setting-Next.js-App/Readme.md) github repository on how to setup a **Next.js Application with Docker**.
- **Remark**:
  - Access Next.js Docker Application by:
    ```sh
        docker exec -it <app-name> bash
    ```

# Resources and Further Reading

1. [getcssscan.com - css-buttons-examples](https://getcssscan.com/css-buttons-examples)
2. [https://www.programiz.com/css/button-styling](https://www.programiz.com/css/button-styling)
