import { env } from "$env/dynamic/private";
import { json } from "@sveltejs/kit";
import type { RequestHandler } from "./$types";

const BACKEND_URL = env.BACKEND_URL ?? "http://localhost:8000";

/**
 * Proxy SvelteKit → FastAPI
 *   GET  /api/water?endpoint=reading|status|history|report/daily|constants|agent/status
 *   POST /api/water?endpoint=simulate|agent/start|agent/stop|agent/cycle
 */
export const GET: RequestHandler = async ({ url, fetch }) => {
  const endpoint = url.searchParams.get("endpoint") ?? "status";
  const hours = url.searchParams.get("hours");

  let backendPath = `/water/${endpoint}`;
  if (endpoint === "history" && hours) backendPath += `?hours=${hours}`;

  try {
    const res = await fetch(`${BACKEND_URL}${backendPath}`);
    if (!res.ok) {
      return json({ data: null, error: `Backend ${res.status}: ${backendPath}` }, { status: 200 });
    }
    return new Response(res.body, { headers: { "Content-Type": "application/json" } });
  } catch (e) {
    return json({ data: null, error: String(e) }, { status: 200 });
  }
};

export const POST: RequestHandler = async ({ url, request, fetch }) => {
  const endpoint = url.searchParams.get("endpoint") ?? "simulate";
  const backendPath = `/water/${endpoint}`;

  let body: any = null;
  try { body = await request.json(); } catch {}

  try {
    const res = await fetch(`${BACKEND_URL}${backendPath}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : "",
    });
    return new Response(res.body, { headers: { "Content-Type": "application/json" } });
  } catch (e) {
    return json({ data: null, error: String(e) }, { status: 200 });
  }
};
