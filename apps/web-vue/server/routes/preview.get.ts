import { readFile } from "node:fs/promises";
import { join } from "node:path";

// process.cwd() is apps/web-vue during dev and prod. The shared preview.html
// is two levels up at <repo>/scripts/preview.html.
const PREVIEW_HTML = join(process.cwd(), "..", "..", "scripts", "preview.html");

// Cache once per process to avoid disk I/O on every request.
let cached: string | null = null;

export default defineEventHandler(async (event) => {
  try {
    if (cached === null) cached = await readFile(PREVIEW_HTML, "utf-8");
    setResponseHeaders(event, {
      "Content-Type": "text/html; charset=utf-8",
      "Cache-Control": "public, max-age=60, stale-while-revalidate=300",
    });
    return cached;
  } catch (err) {
    setResponseStatus(event, 500);
    return `Could not load preview.html (${err instanceof Error ? err.message : String(err)})`;
  }
});
