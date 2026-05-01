import type { NextRequest } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  const body = await request.text();
  const upstream = await fetch(`${BACKEND_URL}/reports/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
  });
  if (!upstream.ok || !upstream.body) {
    return new Response(`Backend error: ${upstream.status}`, { status: upstream.status });
  }
  return new Response(upstream.body, {
    headers: {
      "Content-Type": upstream.headers.get("Content-Type") ?? "application/pdf",
      "Content-Disposition": "attachment; filename=agentos-response.pdf",
    },
  });
}
