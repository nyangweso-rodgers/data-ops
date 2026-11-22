// Builds the survey app's Postgres connection URL from WEB_APPS_POSTGRES_* (repo-root .env locally, project env vars on Vercel).
// Shared by the app (src/app/lib/prisma.js) and prisma.config.mjs (Prisma CLI),
// so both always hit the same database and schema.
// (.mjs because this package isn't "type": "module" and prisma.config.mjs imports it.)
import dotenv from "dotenv";
import path from "path";

// Load the repo-root .env (data-ops/.env); cwd is the app folder when run via pnpm.
// In Docker that file isn't there, so dotenv skips it and container env vars are used.
dotenv.config({ path: path.resolve(process.cwd(), "../../../.env") });

// Postgres schema (namespace) that holds this app's tables, inside
// WEB_APPS_POSTGRES_DB. Prisma creates it on `db push` / `migrate`.
export const POSTGRES_SCHEMA = "survey_app";

const REQUIRED = [
  "WEB_APPS_POSTGRES_HOST",
  "WEB_APPS_POSTGRES_USER",
  "WEB_APPS_POSTGRES_PASSWORD",
  "WEB_APPS_POSTGRES_DB",
];

export function missingPostgresVars() {
  return REQUIRED.filter((key) => !process.env[key]);
}

// withSchema: append ?schema=<POSTGRES_SCHEMA> for the Prisma CLI (migrate).
// The app passes the schema to the pg driver adapter instead (see prisma.js).
export function buildPostgresUrl({ withSchema = false } = {}) {
  if (missingPostgresVars().length) return undefined;
  const user = encodeURIComponent(process.env.WEB_APPS_POSTGRES_USER);
  const password = encodeURIComponent(process.env.WEB_APPS_POSTGRES_PASSWORD);
  // localhost in data-ops/.env (host-run); docker-compose sets "postgres".
  const host = process.env.WEB_APPS_POSTGRES_HOST;
  const port = process.env.WEB_APPS_POSTGRES_PORT || "5432";
  const db = process.env.WEB_APPS_POSTGRES_DB;
  const url = `postgresql://${user}:${password}@${host}:${port}/${db}`;
  return withSchema ? `${url}?schema=${POSTGRES_SCHEMA}` : url;
}
