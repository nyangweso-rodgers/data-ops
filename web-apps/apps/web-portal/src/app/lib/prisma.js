import { PrismaClient } from "../../generated/prisma";
import { buildPostgresUrl, missingPostgresVars } from "./postgres-url.js";

const missing = missingPostgresVars();
if (missing.length) {
  // Don't throw at import time: Next.js imports routes during `next build`.
  console.error(`Postgres not configured, missing: ${missing.join(", ")}`);
}

// Reuse one client across hot reloads in dev.
const globalForPrisma = globalThis;
const prisma =
  globalForPrisma.prisma ??
  new PrismaClient({ datasourceUrl: buildPostgresUrl() });
if (process.env.NODE_ENV !== "production") globalForPrisma.prisma = prisma;

export default prisma;
