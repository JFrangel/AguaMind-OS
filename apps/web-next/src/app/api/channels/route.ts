const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export const runtime = "nodejs";

export async function GET() {
  try {
    const res = await fetch(`${BACKEND_URL}/notify/channels`);
    if (!res.ok) {
      return Response.json({ data: { configured: [], all: [] }, error: null });
    }
    return new Response(res.body, {
      headers: { "Content-Type": "application/json" },
    });
  } catch {
    return Response.json({ data: { configured: [], all: [] }, error: null });
  }
}
