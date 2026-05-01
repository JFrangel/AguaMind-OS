const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const res = await fetch(`${BACKEND_URL}/health`, { cache: "no-store" });
    if (!res.ok) {
      return Response.json({ status: "down", providers: {}, timestamp: Date.now() });
    }
    return new Response(res.body, { headers: { "Content-Type": "application/json" } });
  } catch {
    return Response.json({ status: "down", providers: {}, timestamp: Date.now() });
  }
}
