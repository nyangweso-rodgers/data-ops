import path from "node:path";
import { fileURLToPath } from "node:url";

const workspaceRoot = path.join(path.dirname(fileURLToPath(import.meta.url)), "../..");

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Self-contained server for the Docker image (web-apps/Dockerfile); Vercel ignores it.
  // It copies node_modules, which under pnpm needs symlinks that Windows blocks
  // without Developer Mode, so skip it on Windows (local `next build` only).
  output: process.platform === "win32" ? undefined : "standalone",
  // pnpm workspace: trace dependencies from web-apps/, not just this app folder.
  outputFileTracingRoot: workspaceRoot,
};

export default nextConfig;
