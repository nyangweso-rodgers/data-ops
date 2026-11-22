// Builds the portal's Postgres connection URL from the repo-root .env.
// Shared by the app (src/app/lib/prisma.js) and the Prisma CLI wrapper
// (scripts/prisma.mjs), so both always hit the same database and schema.
import dotenv from "dotenv";
import path from "path";

// Load the repo-root .env (data-ops/.env); cwd is the app folder when run via pnpm.
// In Docker that file isn't there, so dotenv skips it and container env vars are used.
dotenv.config({ path: path.resolve(process.cwd(), "../../../.env") });

// Postgres schema (namespace) that holds this app's tables, inside
// LOCAL_POSTGRES_TEST_DB_NAME. Prisma creates it on `db push` / `migrate`.
export const POSTGRES_SCHEMA = "web_portal";

const REQUIRED = [
  "LOCAL_POSTGRES_DB_HOST",
  "LOCAL_POSTGRES_DB_USER",
  "LOCAL_POSTGRES_DB_PASSWORD",
  "LOCAL_POSTGRES_TEST_DB_NAME",
];

export function missingPostgresVars() {
  return REQUIRED.filter((key) => !process.env[key]);
}

export function buildPostgresUrl() {
  if (missingPostgresVars().length) return undefined;
  const user = encodeURIComponent(process.env.LOCAL_POSTGRES_DB_USER);
  const password = encodeURIComponent(process.env.LOCAL_POSTGRES_DB_PASSWORD);
  // LOCAL_POSTGRES_DB_HOST is the Docker service name ("postgres"), shared with
  // containerised tools like Dagster. When the portal runs on the host, set
  // WEB_PORTAL_POSTGRES_HOST=localhost to reach the published port instead.
  const host =
    process.env.WEB_PORTAL_POSTGRES_HOST || process.env.LOCAL_POSTGRES_DB_HOST;
  const port = process.env.LOCAL_POSTGRES_DB_PORT || "5432";
  const db = process.env.LOCAL_POSTGRES_TEST_DB_NAME;
  return `postgresql://${user}:${password}@${host}:${port}/${db}?schema=${POSTGRES_SCHEMA}`;
}
