# web-apps/Dockerfile
# One image recipe for every Next.js app in the pnpm workspace (apps/<APP>).
# Build context is web-apps/ so pnpm sees the workspace + the single lockfile.
#
#   docker build --build-arg APP=web-portal -t data-ops/web-portal .
#   (normally via: make web-apps-dev-up  - see docker-compose-web-apps.*.yml)
#
# The runtime image holds only Next.js "standalone" output (server + traced deps),
# not the full workspace node_modules. Vercel ignores this file.

# Node 24 LTS - keep the major in line with the host (Prisma 7 supports 20.19+, 22.12+, 24+)
ARG NODE_IMAGE=node:24.22.3-alpine3.24

# ---------------------------------------------------------------------------
# base: build tools + pnpm at the version pinned in package.json "packageManager"
# ---------------------------------------------------------------------------
FROM ${NODE_IMAGE} AS base
# libc6-compat: Next.js SWC binaries on Alpine
RUN apk add --no-cache libc6-compat
ENV PNPM_HOME=/pnpm \
    PATH=/pnpm:$PATH \
    NEXT_TELEMETRY_DISABLED=1
WORKDIR /repo
# Install pnpm with npm, not corepack: corepack's bundled signing keys can lag
# npm's (older images reject every pnpm download), and Node 25+ drops corepack.
COPY package.json ./
RUN npm install -g "pnpm@$(node -p "require('./package.json').packageManager.split('@')[1]")" \
 && pnpm --version

# ---------------------------------------------------------------------------
# build: install only APP and its dependencies, then `next build`
# ---------------------------------------------------------------------------
FROM base AS build
ARG APP
RUN test -n "$APP" || (echo "ERROR: --build-arg APP=<folder in apps/> is required" >&2 && exit 1)

# Download every package in the lockfile first: this layer is reused until
# pnpm-lock.yaml changes, whatever source files change.
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN --mount=type=cache,id=pnpm-store,target=/pnpm/store pnpm fetch --frozen-lockfile

COPY apps ./apps
# Offline install from the fetched store; postinstall runs `prisma generate` for
# Prisma apps (src/generated/prisma, TypeScript compiled into the Next.js build).
RUN --mount=type=cache,id=pnpm-store,target=/pnpm/store \
    pnpm install --offline --frozen-lockfile --filter "${APP}..."
RUN pnpm --filter "${APP}" build
# Not every app has public/; create it so the COPY below never fails.
RUN mkdir -p "apps/${APP}/public"

# ---------------------------------------------------------------------------
# runner: minimal production image
# ---------------------------------------------------------------------------
FROM ${NODE_IMAGE} AS runner
ARG APP
RUN addgroup -S -g 1001 nodejs \
 && adduser -S -u 1001 -G nodejs nextjs
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0
WORKDIR /app

# standalone mirrors the workspace layout: server.js lands in apps/<APP>/
COPY --from=build --chown=nextjs:nodejs /repo/apps/${APP}/.next/standalone ./
COPY --from=build --chown=nextjs:nodejs /repo/apps/${APP}/.next/static ./apps/${APP}/.next/static
COPY --from=build --chown=nextjs:nodejs /repo/apps/${APP}/public ./apps/${APP}/public
# No Prisma engine to copy: Prisma 7's client is bundled into the build and talks
# to Postgres through @prisma/adapter-pg (traced into standalone node_modules).

USER nextjs
WORKDIR /app/apps/${APP}
EXPOSE 3000
CMD ["node", "server.js"]
