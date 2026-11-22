// ESLint 9 flat config (Next.js 16 removed `next lint`; run: pnpm --filter data-portal lint)
import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";

export default defineConfig([
  ...nextVitals,
  globalIgnores([
    // eslint-config-next defaults
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    // Prisma-generated client
    "src/generated/**",
  ]),
]);
