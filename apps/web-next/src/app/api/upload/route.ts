import type { NextRequest } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  const form = await request.formData();
  const upstream = await fetch(`${BACKEND_URL}/rag/ingest`, {
    method: "POST",
    body: form,
  });
  if (!upstream.ok) {
    return Response.json(
      { data: null, error: `Backend error: ${upstream.status}` },
      { status: upstream.status },
    );
  }
  return new Response(upstream.body, {
    headers: { "Content-Type": "application/json" },
  });
}
