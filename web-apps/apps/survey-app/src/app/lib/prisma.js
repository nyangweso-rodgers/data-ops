import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "../../generated/prisma/client";
import {
  POSTGRES_SCHEMA,
  buildPostgresUrl,
  missingPostgresVars,
} from "./postgres-url.mjs";

const missing = missingPostgresVars();
if (missing.length) {
  // Don't throw at import time: Next.js imports routes during `next build`.
  console.error(`Postgres not configured, missing: ${missing.join(", ")}`);
}

// Prisma 7 connects through a driver adapter (node-postgres). The app's tables
// live in their own Postgres schema, passed to the adapter rather than the URL.
function createClient() {
  const adapter = new PrismaPg(
    { connectionString: buildPostgresUrl() },
    { schema: POSTGRES_SCHEMA }
  );
  return new PrismaClient({ adapter });
}

// Reuse one client across hot reloads in dev.
const globalForPrisma = globalThis;
const prisma = globalForPrisma.prisma ?? createClient();
if (process.env.NODE_ENV !== "production") globalForPrisma.prisma = prisma;

export default prisma;
