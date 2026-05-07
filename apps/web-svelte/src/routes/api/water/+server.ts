import { env } from "$env/dynamic/private";
import { json } from "@sveltejs/kit";
import type { RequestHandler } from "./$types";

const BACKEND_URL = env.BACKEND_URL ?? "http://localhost:8000";

export const GET: RequestHandler = async ({ url, fetch }) => {
  const endpoint = url.searchParams.get("endpoint") ?? "status";
  const hours = url.searchParams.get("hours") ?? "24";

  let backendPath = `/water/${endpoint}`;
  if (endpoint === "history") backendPath += `?hours=${hours}`;

  try {
    const res = await fetch(`${BACKEND_URL}${backendPath}`);
    if (!res.ok) {
      return json({ data: null, error: `Backend returned ${res.status}` }, { status: 200 });
    }
    return new Response(res.body, { headers: { "Content-Type": "application/json" } });
  } catch (e) {
    return json({ data: null, error: String(e) }, { status: 200 });
  }
};

export const POST: RequestHandler = async ({ request, fetch }) => {
  const body = await request.json();
  try {
    const res = await fetch(`${BACKEND_URL}/water/simulate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return new Response(res.body, { headers: { "Content-Type": "application/json" } });
  } catch (e) {
    return json({ data: null, error: String(e) }, { status: 200 });
  }
};
