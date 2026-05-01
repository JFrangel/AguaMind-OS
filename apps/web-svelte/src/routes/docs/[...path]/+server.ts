import { readFileSync, existsSync } from "node:fs";
import { dirname, extname, normalize, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

import { error } from "@sveltejs/kit";
import { marked } from "marked";

import type { RequestHandler } from "./$types";

const here = dirname(fileURLToPath(import.meta.url));
// docs/ lives at <repo>/docs — six levels up from this route file.
const DOCS_ROOT = resolve(here, "..", "..", "..", "..", "..", "..", "docs");

const HTML_FRAME = (title: string, body: string) => `<!doctype html>
<html lang="es" data-theme="dark-blue">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>${escapeHtml(title)} · AgentOS</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
<style>
  :root[data-theme="dark-blue"]   { --bg:#0a0e1a; --card:#111827; --elev:#1e293b; --accent:#2563eb; --text:#f8fafc; --text2:#94a3b8; --muted:#475569; }
  :root[data-theme="dark-purple"] { --bg:#16161a; --card:#1f1f24; --elev:#2a2a30; --accent:#7f5af0; --text:#fffffe; --text2:#94a1b2; --muted:#5f6c7b; }
  :root[data-theme="light"]       { --bg:#fafaf8; --card:#fff;    --elev:#e6e6df; --accent:#6246ea; --text:#2b2c34; --text2:#4d4d5a; --muted:#9b9ba6; }
  *{box-sizing:border-box}
  html,body{margin:0;background:var(--bg);color:var(--text);font-family:Inter,system-ui,sans-serif;line-height:1.65;font-size:15px}
  .topbar{position:sticky;top:0;background:color-mix(in srgb,var(--bg) 85%,transparent);backdrop-filter:blur(8px);border-bottom:1px solid var(--elev);padding:14px 24px;display:flex;justify-content:space-between;align-items:center;z-index:10}
  .topbar a.brand{display:inline-flex;align-items:center;gap:10px;text-decoration:none;color:inherit}
  .topbar a.brand .logo{width:30px;height:30px;border-radius:8px;background:var(--accent);color:#fff;display:flex;align-items:center;justify-content:center;font-family:"Space Grotesk";font-weight:700;font-size:14px}
  .topbar nav a{margin-left:18px;color:var(--text2);font-size:13px;text-decoration:none;font-family:"JetBrains Mono",monospace}
  .topbar nav a:hover{color:var(--accent)}
  main{max-width:760px;margin:0 auto;padding:48px 24px 96px}
  h1,h2,h3,h4{font-family:"Space Grotesk",Inter,sans-serif;letter-spacing:-0.01em;color:var(--text)}
  h1{font-size:32px;margin:0 0 18px;line-height:1.15}
  h2{font-size:22px;margin:36px 0 12px;border-bottom:1px solid var(--elev);padding-bottom:6px}
  h3{font-size:17px;margin:28px 0 10px}
  p,li{color:var(--text2)}
  a{color:var(--accent)}
  a:hover{color:var(--accent);text-decoration:underline}
  code{font-family:"JetBrains Mono",monospace;font-size:0.9em;background:var(--elev);padding:2px 6px;border-radius:4px;color:var(--text)}
  pre{background:var(--card);border:1px solid var(--elev);border-radius:8px;padding:14px 18px;overflow-x:auto;font-family:"JetBrains Mono",monospace;font-size:13px;line-height:1.55}
  pre code{background:transparent;padding:0}
  table{border-collapse:collapse;width:100%;margin:14px 0;font-size:13.5px}
  th{background:var(--elev);color:var(--text);text-align:left;padding:8px 12px;border-bottom:1px solid var(--accent)}
  td{padding:8px 12px;border-bottom:1px solid var(--elev)}
  blockquote{border-left:3px solid var(--accent);background:var(--card);padding:8px 16px;margin:12px 0;color:var(--text2);border-radius:4px}
  hr{border:none;border-top:1px solid var(--elev);margin:24px 0}
</style>
</head>
<body>
<div class="topbar">
  <a class="brand" href="/"><span class="logo">A</span><span style="font-family:'Space Grotesk';font-weight:600">AgentOS</span></a>
  <nav><a href="/previewagentos">Preview</a><a href="/">Chat</a></nav>
</div>
<main>${body}</main>
</body>
</html>`;

function escapeHtml(s: string): string {
  return s.replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c] ?? c,
  );
}

const BINARY_EXTS = new Set([".pdf", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"]);
const MIME: Record<string, string> = {
  ".pdf": "application/pdf",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".gif": "image/gif",
  ".svg": "image/svg+xml",
  ".webp": "image/webp",
};

export const GET: RequestHandler = async ({ params }) => {
  const requested = params.path ?? "";
  // Block traversal: resolve and check the result is still inside DOCS_ROOT.
  const target = normalize(resolve(DOCS_ROOT, requested));
  if (!target.startsWith(DOCS_ROOT + sep) && target !== DOCS_ROOT) {
    throw error(403, "outside docs root");
  }

  // Auto-resolve: if the user requested `/docs/es/QUE-ES-AGENTOS` (no extension),
  // try `.md` automatically. PDF and other extensions must be explicit.
  let resolved = target;
  if (!extname(resolved) && !existsSync(resolved)) {
    if (existsSync(resolved + ".md")) resolved = resolved + ".md";
  }
  if (!existsSync(resolved)) throw error(404, `not found: ${requested}`);

  const ext = extname(resolved).toLowerCase();

  if (BINARY_EXTS.has(ext)) {
    const buffer = readFileSync(resolved);
    return new Response(buffer, {
      headers: { "Content-Type": MIME[ext] ?? "application/octet-stream" },
    });
  }

  if (ext === ".md" || ext === ".markdown") {
    const raw = readFileSync(resolved, "utf-8");
    // Title = first H1 in the file, fallback to filename
    const h1 = raw.match(/^#\s+(.+)$/m);
    const title = h1 ? h1[1] : requested;
    const body = await marked.parse(raw, { gfm: true, breaks: false });
    return new Response(HTML_FRAME(title, body as string), {
      headers: { "Content-Type": "text/html; charset=utf-8" },
    });
  }

  // Plain text fallback
  const raw = readFileSync(resolved, "utf-8");
  return new Response(raw, { headers: { "Content-Type": "text/plain; charset=utf-8" } });
};
