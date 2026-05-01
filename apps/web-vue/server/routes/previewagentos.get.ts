import { readFile } from "node:fs/promises";
import { join } from "node:path";

// process.cwd() is apps/web-vue during dev and prod. The shared preview.html
// is two levels up at <repo>/scripts/preview.html.
const PREVIEW_HTML = join(process.cwd(), "..", "..", "scripts", "preview.html");

export default defineEventHandler(async (event) => {
  try {
    const html = await readFile(PREVIEW_HTML, "utf-8");
    setResponseHeaders(event, {
      "Content-Type": "text/html; charset=utf-8",
      "Cache-Control": "no-cache",
    });
    return html;
  } catch (err) {
    setResponseStatus(event, 500);
    return `Could not load preview.html (${err instanceof Error ? err.message : String(err)})`;
  }
});
