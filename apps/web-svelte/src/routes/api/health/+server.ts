import { env } from "$env/dynamic/private";
import { json } from "@sveltejs/kit";
import type { RequestHandler } from "./$types";

const BACKEND_URL = env.BACKEND_URL ?? "http://localhost:8000";

export const GET: RequestHandler = async ({ fetch }) => {
  try {
    const res = await fetch(`${BACKEND_URL}/health`);
    if (!res.ok) {
      return json({ status: "down", providers: {}, timestamp: Date.now() }, { status: 200 });
    }
    return new Response(res.body, {
      headers: { "Content-Type": "application/json" },
    });
  } catch {
    return json({ status: "down", providers: {}, timestamp: Date.now() }, { status: 200 });
  }
};
