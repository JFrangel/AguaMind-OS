import type { NextRequest } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(request: NextRequest) {
  const body = await request.json();
  const upstreamPayload = {
    message: body.message,
    context_type: body.context_type ?? "chat",
    language: body.language ?? "es",
    use_rag: Boolean(body.use_rag),
    use_web: Boolean(body.use_web),
  };

  const upstream = await fetch(`${BACKEND_URL}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(upstreamPayload),
  });

  if (!upstream.ok || !upstream.body) {
    return new Response(`Backend error: ${upstream.status}`, { status: upstream.status });
  }

  return new Response(upstream.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}
