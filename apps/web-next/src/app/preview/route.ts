import { readFile } from "node:fs/promises";
import { join } from "node:path";

export const runtime = "nodejs";
// Allow Next to cache the response between requests at the framework level.
// We invalidate manually on redeploy by setting Cache-Control below.
export const revalidate = 60;

// process.cwd() is the Next app root (apps/web-next) during dev and build.
// scripts/preview.html lives two levels up: <repo>/scripts/preview.html.
const PREVIEW_HTML = join(process.cwd(), "..", "..", "scripts", "preview.html");

// Cache the bytes once per process to skip disk I/O on every request.
let cached: string | null = null;

export async function GET() {
  try {
    if (cached === null) cached = await readFile(PREVIEW_HTML, "utf-8");
    return new Response(cached, {
      headers: {
        "Content-Type": "text/html; charset=utf-8",
        "Cache-Control": "public, max-age=60, stale-while-revalidate=300",
      },
    });
  } catch (err) {
    return new Response(
      `Could not load preview.html (${err instanceof Error ? err.message : String(err)})`,
      { status: 500 },
    );
  }
}
