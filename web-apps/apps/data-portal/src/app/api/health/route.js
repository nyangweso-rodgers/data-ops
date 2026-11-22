import { NextResponse } from "next/server";

// Backend lives in Next.js route handlers (src/app/api/*). This one is a
// liveness check for Docker / load balancers: GET /api/health
export const dynamic = "force-dynamic";

export function GET() {
  return NextResponse.json({ status: "ok" });
}
