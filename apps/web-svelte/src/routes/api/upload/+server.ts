import { env } from "$env/dynamic/private";
import { json } from "@sveltejs/kit";
import type { RequestHandler } from "./$types";

const BACKEND_URL = env.BACKEND_URL ?? "http://localhost:8000";

export const POST: RequestHandler = async ({ request, fetch }) => {
  const form = await request.formData();
  const upstream = await fetch(`${BACKEND_URL}/rag/ingest`, {
    method: "POST",
    body: form,
  });
  if (!upstream.ok) {
    return json(
      { data: null, error: `Backend error: ${upstream.status}` },
      { status: upstream.status },
    );
  }
  return new Response(upstream.body, {
    headers: { "Content-Type": "application/json" },
  });
};
