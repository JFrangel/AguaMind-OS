import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import type { RequestHandler } from "./$types";

// Resolve scripts/preview.html relative to this module so the route works
// from any cwd (vite dev, vercel build, smoke tests). The file lives at
// <repo>/scripts/preview.html — five levels up from this route file.
const here = dirname(fileURLToPath(import.meta.url));
const PREVIEW_HTML = resolve(here, "..", "..", "..", "..", "..", "scripts", "preview.html");

export const GET: RequestHandler = async () => {
  try {
    const html = readFileSync(PREVIEW_HTML, "utf-8");
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
};
