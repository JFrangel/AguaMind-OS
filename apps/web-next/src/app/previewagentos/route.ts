import { readFile } from "node:fs/promises";
import { join } from "node:path";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

// process.cwd() is the Next app root (apps/web-next) during dev and build.
// scripts/preview.html lives two levels up: <repo>/scripts/preview.html.
const PREVIEW_HTML = join(process.cwd(), "..", "..", "scripts", "preview.html");

export async function GET() {
  try {
    const html = await readFile(PREVIEW_HTML, "utf-8");
    return new Response(html, {
      headers: {
        "Content-Type": "text/html; charset=utf-8",
        "Cache-Control": "no-cache",
      },
    });
  } catch (err) {
    return new Response(
      `Could not load preview.html (${err instanceof Error ? err.message : String(err)})`,
      { status: 500 },
    );
  }
}
