import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import type { RequestHandler } from "./$types";

// Canonical /preview route. /previewagentos is kept as a 301 redirect for
// back-compat with old bookmarks/links. Resolve scripts/preview.html
// relative to this module so the route works from any cwd (vite dev,
// vercel build, smoke tests). The file lives at <repo>/scripts/preview.html
// — five levels up from this route file.
const here = dirname(fileURLToPath(import.meta.url));
const PREVIEW_HTML = resolve(here, "..", "..", "..", "..", "..", "scripts", "preview.html");

// Cache the bytes once per process. The file is static and ~70KB; reading
// it on every request adds disk I/O for nothing. Vite dev still reloads on
// edit because the dev server restarts the module.
let cached: string | null = null;

export const GET: RequestHandler = async () => {
  try {
    if (cached === null) cached = readFileSync(PREVIEW_HTML, "utf-8");
    return new Response(cached, {
      headers: {
        "Content-Type": "text/html; charset=utf-8",
        // 60s cache + SWR keeps the page snappy without making redeploys
        // wait an hour to take effect.
        "Cache-Control": "public, max-age=60, stale-while-revalidate=300",
      },
    });
  } catch (err) {
    return new Response(
      `Could not load preview.html (${err instanceof Error ? err.message : String(err)})`,
      { status: 500 },
    );
  }
};
