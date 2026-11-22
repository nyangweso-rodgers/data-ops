/** @type {import('next').NextConfig} */
// "standalone" copies node_modules into .next/standalone. With pnpm's linked
// layout that needs symlinks, which Windows blocks unless Developer Mode is on,
// so only emit it on Linux/macOS (Docker, CI).
const nextConfig = {
  output: process.platform === "win32" ? undefined : "standalone",
};

export default nextConfig;
