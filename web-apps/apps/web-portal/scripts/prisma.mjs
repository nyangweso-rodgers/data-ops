// Runs the Prisma CLI against the same database + schema the app uses.
// The CLI only reads env("LOCAL_POSTGRES_TEST_DATABASE_URL") from schema.prisma,
// so build it from the LOCAL_POSTGRES_* vars in the repo-root .env (never stored).
//
//   pnpm --filter web-portal prisma db push
//   pnpm --filter web-portal prisma studio
import { spawnSync } from "node:child_process";
import {
  buildPostgresUrl,
  missingPostgresVars,
} from "../src/app/lib/postgres-url.js";

const missing = missingPostgresVars();
if (missing.length) {
  console.error(`Missing in data-ops/.env: ${missing.join(", ")}`);
  process.exit(1);
}

const result = spawnSync("prisma", process.argv.slice(2), {
  stdio: "inherit",
  shell: true, // resolves node_modules/.bin/prisma(.cmd) on Windows too
  env: { ...process.env, LOCAL_POSTGRES_TEST_DATABASE_URL: buildPostgresUrl() },
});
process.exit(result.status ?? 1);
