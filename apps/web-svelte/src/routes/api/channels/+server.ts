import { env } from "$env/dynamic/private";
import { json } from "@sveltejs/kit";
import type { RequestHandler } from "./$types";

const BACKEND_URL = env.BACKEND_URL ?? "http://localhost:8000";

export const GET: RequestHandler = async ({ fetch }) => {
  try {
    const res = await fetch(`${BACKEND_URL}/notify/channels`);
    if (!res.ok) {
      return json({ data: { configured: [], all: [] }, error: null });
    }
    return new Response(res.body, {
      headers: { "Content-Type": "application/json" },
    });
  } catch {
    return json({ data: { configured: [], all: [] }, error: null });
  }
};
