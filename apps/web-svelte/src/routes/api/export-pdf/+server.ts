import { env } from "$env/dynamic/private";
import type { RequestHandler } from "./$types";

const BACKEND_URL = env.BACKEND_URL ?? "http://localhost:8000";

export const POST: RequestHandler = async ({ request, fetch }) => {
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
};
