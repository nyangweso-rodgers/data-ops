// Prisma CLI config (Prisma 7 reads the connection from here, not schema.prisma).
//   pnpm --filter web-portal db:migrate --name <change> | db:deploy | db:status
//   pnpm --filter web-portal prisma studio
import { defineConfig } from "prisma/config";
import { buildPostgresUrl } from "./src/app/lib/postgres-url.js";

export default defineConfig({
  schema: "prisma/schema.prisma",
  migrations: { path: "prisma/migrations" },
  datasource: {
    // From WEB_APPS_POSTGRES_* (repo-root .env locally), with ?schema=<app schema>.
    // Empty when unset so `prisma generate` still works without a database
    // (Docker / Vercel builds); migrate commands need the variables.
    url: buildPostgresUrl({ withSchema: true }) ?? "",
  },
});
