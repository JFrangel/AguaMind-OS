import { readFileSync, existsSync } from "node:fs";
import { dirname, extname, normalize, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

import { error } from "@sveltejs/kit";
import { marked } from "marked";

import type { RequestHandler } from "./$types";

const here = dirname(fileURLToPath(import.meta.url));
// docs/ lives at <repo>/docs — six levels up from this route file.
const DOCS_ROOT = resolve(here, "..", "..", "..", "..", "..", "..", "docs");

/**
 * Renders a markdown file inside an AgentOS-branded HTML frame.
 *
 * Theme handling: the page boots with the same theme the user last picked
 * in the chat (read from localStorage at first paint via inline JS) and
 * exposes a 3-button picker in the topbar so it can be changed without
 * leaving the doc. The CSS variables for all 3 themes ship in the
 * stylesheet so switching is instant and works offline.
 */
const HTML_FRAME = (title: string, body: string) => `<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>${escapeHtml(title)} · AgentOS</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
<script>
  (function () {
    var t = "dark-blue";
    try { t = localStorage.getItem("agentos:theme") || "dark-blue"; } catch (e) {}
    if (!["dark-blue","dark-purple","light"].includes(t)) t = "dark-blue";
    document.documentElement.setAttribute("data-theme", t);
  })();
</script>
<style>
  :root[data-theme="dark-blue"]   {
    --bg:#0a0e1a; --bg2:#0f1629; --card:#111827; --elev:#1e293b;
    --accent:#2563eb; --accent-hover:#1d4ed8; --accent-soft:rgba(37,99,235,0.14);
    --text:#f8fafc; --text2:#94a3b8; --muted:#475569;
    --code-bg:#0f1629;
  }
  :root[data-theme="dark-purple"] {
    --bg:#16161a; --bg2:#1c1c21; --card:#1f1f24; --elev:#2a2a30;
    --accent:#7f5af0; --accent-hover:#6c47e0; --accent-soft:rgba(127,90,240,0.16);
    --text:#fffffe; --text2:#94a1b2; --muted:#5f6c7b;
    --code-bg:#1c1c21;
  }
  :root[data-theme="light"]       {
    --bg:#fafaf8; --bg2:#f4f4f0; --card:#ffffff; --elev:#e6e6df;
    --accent:#6246ea; --accent-hover:#4d35bd; --accent-soft:rgba(98,70,234,0.12);
    --text:#2b2c34; --text2:#4d4d5a; --muted:#9b9ba6;
    --code-bg:#f4f4f0;
  }
  :root[data-theme="light"] { color-scheme: light; }
  :root[data-theme="dark-blue"], :root[data-theme="dark-purple"] { color-scheme: dark; }

  * { box-sizing: border-box; }
  html, body {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: "Inter", system-ui, sans-serif;
    line-height: 1.7;
    font-size: 15px;
    transition: background 200ms ease, color 200ms ease;
  }

  /* Topbar */
  .topbar {
    position: sticky; top: 0; z-index: 10;
    background: color-mix(in srgb, var(--bg) 85%, transparent);
    backdrop-filter: blur(8px);
    border-bottom: 1px solid var(--elev);
    padding: 12px 24px;
    display: flex; justify-content: space-between; align-items: center;
    gap: 12px;
  }
  .topbar a.brand {
    display: inline-flex; align-items: center; gap: 10px;
    text-decoration: none; color: inherit;
  }
  .topbar a.brand .logo {
    width: 30px; height: 30px; border-radius: 8px;
    background: var(--accent); color: white;
    display: flex; align-items: center; justify-content: center;
    font-family: "Space Grotesk"; font-weight: 700; font-size: 14px;
  }
  .topbar a.brand .name {
    font-family: "Space Grotesk"; font-weight: 600; font-size: 15px;
  }
  .topbar .right { display: flex; align-items: center; gap: 12px; }
  .topbar nav a {
    color: var(--text2); font-size: 12px; text-decoration: none;
    font-family: "JetBrains Mono", monospace;
    padding: 4px 8px; border-radius: 5px;
    transition: color 120ms, background 120ms;
  }
  .topbar nav a:hover { color: var(--accent); background: var(--accent-soft); }

  .theme-picker {
    display: inline-flex; gap: 4px; padding: 3px;
    border: 1px solid var(--elev); border-radius: 8px;
    background: var(--card);
  }
  .theme-picker button {
    all: unset; cursor: pointer;
    font: 500 11px "Inter", sans-serif;
    padding: 5px 10px; border-radius: 5px;
    color: var(--text2);
    display: inline-flex; align-items: center; gap: 6px;
    transition: background 120ms, color 120ms;
  }
  .theme-picker button[aria-pressed="true"] {
    background: var(--elev); color: var(--text);
  }
  .swatch { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }

  /* Main content layout */
  main {
    max-width: 760px;
    margin: 0 auto;
    padding: 56px 24px 96px;
  }
  .doc-meta {
    font-family: "JetBrains Mono", monospace;
    font-size: 11px;
    color: var(--muted);
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--elev);
  }

  /* Typography */
  h1, h2, h3, h4, h5, h6 {
    font-family: "Space Grotesk", Inter, sans-serif;
    letter-spacing: -0.01em;
    color: var(--text);
    line-height: 1.25;
  }
  h1 { font-size: 32px; margin: 0 0 18px; }
  h2 { font-size: 22px; margin: 40px 0 14px; padding-bottom: 8px; border-bottom: 1px solid var(--elev); }
  h3 { font-size: 17px; margin: 28px 0 10px; }
  h4 { font-size: 15px; margin: 22px 0 8px; color: var(--text2); }

  p, li { color: var(--text2); }
  p { margin: 0.7em 0; }
  ul, ol { margin: 0.7em 0; padding-left: 1.4em; }
  li { margin: 0.25em 0; }
  li::marker { color: var(--accent); }

  strong { color: var(--text); font-weight: 600; }
  em { color: var(--text); }

  a {
    color: var(--accent);
    text-decoration: underline;
    text-underline-offset: 2px;
    text-decoration-thickness: 1px;
  }
  a:hover { color: var(--accent-hover); }

  /* Inline code */
  code {
    font-family: "JetBrains Mono", monospace;
    font-size: 0.875em;
    background: var(--elev);
    padding: 2px 6px;
    border-radius: 4px;
    color: var(--text);
  }

  /* Code blocks */
  pre {
    background: var(--code-bg);
    border: 1px solid var(--elev);
    border-radius: 8px;
    padding: 16px 18px;
    overflow-x: auto;
    font-family: "JetBrains Mono", monospace;
    font-size: 13px;
    line-height: 1.6;
    margin: 16px 0;
  }
  pre code {
    background: transparent;
    padding: 0;
    font-size: inherit;
    color: var(--text);
  }

  /* Tables — comparable to GitHub */
  table {
    border-collapse: collapse;
    width: 100%;
    margin: 18px 0;
    font-size: 13.5px;
    border: 1px solid var(--elev);
    border-radius: 8px;
    overflow: hidden;
    background: var(--card);
  }
  thead { background: var(--elev); }
  th {
    color: var(--text); font-family: "Space Grotesk", sans-serif;
    text-align: left;
    padding: 9px 14px;
    border-bottom: 2px solid var(--accent);
    font-weight: 600;
  }
  td {
    padding: 9px 14px;
    border-bottom: 1px solid color-mix(in srgb, var(--elev) 50%, transparent);
    color: var(--text2);
  }
  tr:last-child td { border-bottom: none; }
  tr:nth-child(even) td { background: color-mix(in srgb, var(--elev) 25%, transparent); }
  tr:hover td { background: var(--accent-soft); }

  /* Blockquote */
  blockquote {
    border-left: 3px solid var(--accent);
    background: var(--card);
    padding: 10px 18px;
    margin: 16px 0;
    color: var(--text2);
    border-radius: 0 6px 6px 0;
  }
  blockquote p:first-child { margin-top: 0; }
  blockquote p:last-child { margin-bottom: 0; }

  hr {
    border: none;
    border-top: 1px solid var(--elev);
    margin: 32px 0;
  }

  img {
    max-width: 100%;
    height: auto;
    border-radius: 6px;
    border: 1px solid var(--elev);
  }

  /* Footer */
  footer.doc-footer {
    max-width: 760px;
    margin: 0 auto;
    padding: 24px;
    border-top: 1px solid var(--elev);
    font-family: "JetBrains Mono", monospace;
    font-size: 11px;
    color: var(--muted);
    display: flex; justify-content: space-between; flex-wrap: wrap; gap: 12px;
  }
  footer.doc-footer a:hover { color: var(--accent); }
</style>
</head>
<body>
<div class="topbar">
  <a class="brand" href="/">
    <span class="logo">A</span>
    <span class="name">AgentOS</span>
  </a>
  <div class="right">
    <div class="theme-picker" role="group" aria-label="Tema">
      <button data-theme-btn="dark-blue"   aria-pressed="false" title="Slate">
        <span class="swatch" style="background:#2563eb"></span>
        <span style="display:inline-block">Slate</span>
      </button>
      <button data-theme-btn="dark-purple" aria-pressed="false" title="Indigo">
        <span class="swatch" style="background:#7f5af0"></span>
        <span style="display:inline-block">Indigo</span>
      </button>
      <button data-theme-btn="light"       aria-pressed="false" title="Ivory">
        <span class="swatch" style="background:#6246ea"></span>
        <span style="display:inline-block">Ivory</span>
      </button>
    </div>
    <nav>
      <a href="/preview">Preview</a>
      <a href="/">Chat</a>
    </nav>
  </div>
</div>
<main>
  <div class="doc-meta">${escapeHtml(title)} · documentación AgentOS</div>
  ${body}
</main>
<footer class="doc-footer">
  <span>AgentOS · MIT</span>
  <div style="display:flex; gap:12px; flex-wrap:wrap;">
    <a href="/docs/es/QUE-ES-AGENTOS">¿Qué es?</a>
    <a href="/docs/es/GUIA-RAPIDA">Guía rápida</a>
    <a href="/docs/es/IMPLEMENTACION">Implementación</a>
    <a href="/docs/es/FUNCIONALIDADES">Funcionalidades</a>
  </div>
</footer>
<script>
  (function () {
    var KEY = "agentos:theme";
    function setActive(t) {
      document.documentElement.setAttribute("data-theme", t);
      try { localStorage.setItem(KEY, t); } catch (e) {}
      document.querySelectorAll("[data-theme-btn]").forEach(function (b) {
        b.setAttribute("aria-pressed", String(b.dataset.themeBtn === t));
      });
    }
    setActive(document.documentElement.getAttribute("data-theme") || "dark-blue");
    document.querySelectorAll("[data-theme-btn]").forEach(function (btn) {
      btn.addEventListener("click", function () { setActive(btn.dataset.themeBtn); });
    });
  })();
</script>
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
