/**
 * Markdown rendering helper used by the 3 frontends. Wraps `marked` + `dompurify`
 * so chat bubbles can show GFM tables, code blocks, lists, links, blockquotes
 * and inline code without each frontend re-implementing the pipeline.
 *
 * On top of GFM, we add:
 *  - SVG chart rendering for ```chart fenced blocks (see ./charts.ts)
 *  - Table-toolbar (copy CSV / download CSV) for any rendered table over N rows
 *  - data-num attributes on numeric cells so CSS can right-align them
 *
 * Pure ESM, no DOM dependency at module load — DOMPurify is imported inside
 * `renderMarkdown` so SSR consumers (SvelteKit, Next, Nuxt) don't pay the cost
 * during server render.
 */
import { marked, type Tokens } from "marked";

import { renderChart } from "./charts";

// Custom renderer: replace ```chart blocks with SVG instead of <pre><code>.
const renderer = new marked.Renderer();
const defaultCode = renderer.code.bind(renderer);
renderer.code = function (this: unknown, token: Tokens.Code) {
  if ((token.lang ?? "").trim().toLowerCase() === "chart") {
    return renderChart(token.text);
  }
  return defaultCode(token);
};

marked.setOptions({
  gfm: true,
  breaks: true,
  renderer,
});

export interface RenderOptions {
  /**
   * When true, the result is wrapped in a `<div class="agentos-md">` so callers
   * can target a single class for typography styles.
   */
  wrap?: boolean;
  /**
   * Tables with at least this many rows get a sticky header + scrollable
   * container + copy/download toolbar. Default: 5.
   */
  tableToolbarRows?: number;
}

export async function renderMarkdown(input: string, opts: RenderOptions = {}): Promise<string> {
  if (!input) return "";
  const raw = (await marked.parse(input)) as string;
  const enriched = enrichTables(raw, opts.tableToolbarRows ?? 5);
  const sanitized = await sanitize(enriched);
  return opts.wrap === false ? sanitized : `<div class="agentos-md">${sanitized}</div>`;
}

let purifyPromise: Promise<(input: string) => string> | null = null;

function loadPurify(): Promise<(input: string) => string> {
  if (purifyPromise) return purifyPromise;
  purifyPromise = (async () => {
    const mod = await import("dompurify");
    const DOMPurify = mod.default ?? mod;
    if (typeof window === "undefined") {
      return (input: string) => input;
    }
    const factory = (DOMPurify as any).default ?? DOMPurify;
    const instance = typeof factory === "function" ? factory(window) : factory;
    return (input: string) => {
      const out = instance.sanitize(input, {
        // SVG elements + attributes need to survive — chart output is SVG.
        ADD_TAGS: ["svg", "g", "rect", "line", "path", "circle", "text", "title"],
        ADD_ATTR: [
          "target",
          "rel",
          "viewBox",
          "x",
          "y",
          "x1",
          "x2",
          "y1",
          "y2",
          "cx",
          "cy",
          "r",
          "rx",
          "d",
          "width",
          "height",
          "fill",
          "stroke",
          "text-anchor",
          "stroke-width",
          "stroke-dasharray",
          "data-num",
          "data-csv",
          "role",
          "loading",
          "decoding",
          "referrerpolicy",
        ],
        ALLOW_DATA_ATTR: true,
      });
      // Post-process <img> tags to add lazy-loading + decoding hints +
      // referrer policy (so we don't leak the chat URL to image hosts).
      // Done after sanitize so DOMPurify doesn't strip our additions.
      return out.replace(/<img\b([^>]*)>/g, (_, attrs: string) => {
        const has = (a: string) => new RegExp(`\\b${a}=`).test(attrs);
        const extra =
          (has("loading") ? "" : ' loading="lazy"') +
          (has("decoding") ? "" : ' decoding="async"') +
          (has("referrerpolicy") ? "" : ' referrerpolicy="no-referrer"');
        return `<img${attrs}${extra}>`;
      });
    };
  })();
  return purifyPromise;
}

async function sanitize(html: string): Promise<string> {
  const purify = await loadPurify();
  return purify(html);
}

/**
 * Post-process raw marked HTML to:
 *   - Wrap large tables in a scrollable container with a CSV toolbar.
 *   - Tag numeric cells so CSS can right-align them.
 * Operates on the HTML string with regex — markdown tables are simple enough
 * that the cost of a full DOM parse on every render isn't worth it.
 */
function enrichTables(html: string, toolbarMinRows: number): string {
  return html.replace(/<table>([\s\S]*?)<\/table>/g, (full, body: string) => {
    const rows = (body.match(/<tr>[\s\S]*?<\/tr>/g) || []).length;
    const annotated = annotateNumericCells(full);
    if (rows >= toolbarMinRows + 1) {
      // +1 because the header counts as a row in the regex above.
      const csv = encodeURIComponent(htmlTableToCsv(full));
      const toolbar = `<div class="table-toolbar">
        <button type="button" data-action="copy" data-csv="${csv}" title="Copiar como CSV">Copiar CSV</button>
        <button type="button" data-action="download" data-csv="${csv}" title="Descargar CSV">Descargar</button>
      </div>`;
      return `<div class="table-wrap">${toolbar}${annotated}</div>`;
    }
    return annotated;
  });
}

function annotateNumericCells(tableHtml: string): string {
  // Detect columns whose body cells are mostly numeric, then mark every
  // header + cell in those columns with data-num="1".
  const headers = [...tableHtml.matchAll(/<th[^>]*>([\s\S]*?)<\/th>/g)].map((m) => m[1]);
  if (!headers.length) return tableHtml;

  const rowMatches = [...tableHtml.matchAll(/<tr>([\s\S]*?)<\/tr>/g)];
  // First row is header; data rows start at index 1.
  const dataRows = rowMatches.slice(1).map((rm) =>
    [...rm[1].matchAll(/<td[^>]*>([\s\S]*?)<\/td>/g)].map((m) => stripTags(m[1]).trim()),
  );
  const numericCols = new Set<number>();
  for (let col = 0; col < headers.length; col++) {
    const values = dataRows.map((r) => r[col]).filter(Boolean);
    if (!values.length) continue;
    const numeric = values.filter((v) => /^-?\d[\d.,%\s$€]*$/.test(v)).length;
    if (numeric / values.length >= 0.7) numericCols.add(col);
  }
  if (!numericCols.size) return tableHtml;

  // Walk the HTML cell-by-cell with a tiny state machine; mark cells in
  // the numeric columns. Done on the string because building a full DOM
  // for this is overkill.
  let out = "";
  let i = 0;
  let row = -1;
  let col = 0;
  while (i < tableHtml.length) {
    if (tableHtml.startsWith("<tr>", i)) {
      row++;
      col = 0;
      out += "<tr>";
      i += 4;
      continue;
    }
    if (tableHtml.startsWith("<th>", i)) {
      out += numericCols.has(col) ? '<th data-num="1">' : "<th>";
      col++;
      i += 4;
      continue;
    }
    if (tableHtml.startsWith("<td>", i)) {
      out += numericCols.has(col) ? '<td data-num="1">' : "<td>";
      col++;
      i += 4;
      continue;
    }
    out += tableHtml[i];
    i++;
  }
  return out;
}

function htmlTableToCsv(tableHtml: string): string {
  const rows = [...tableHtml.matchAll(/<tr>([\s\S]*?)<\/tr>/g)].map((rm) => rm[1]);
  return rows
    .map((row) =>
      [...row.matchAll(/<t[hd][^>]*>([\s\S]*?)<\/t[hd]>/g)]
        .map((m) => csvCell(stripTags(m[1])))
        .join(","),
    )
    .join("\n");
}

function csvCell(value: string): string {
  const v = value.replace(/\s+/g, " ").trim();
  if (/[",\n]/.test(v)) return `"${v.replace(/"/g, '""')}"`;
  return v;
}

function stripTags(html: string): string {
  return html
    .replace(/<[^>]+>/g, "")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'");
}

/**
 * Wire up the toolbar buttons (copy / download CSV) on a container that holds
 * agentos-md output. Idempotent: re-attaches via `data-bound` flag so streaming
 * renders don't end up with duplicate listeners.
 *
 * Call from each frontend's MessageBubble after the DOM is updated. Only runs
 * on the client.
 */
export function bindTableToolbars(root: HTMLElement | null): void {
  if (!root || typeof window === "undefined") return;
  root.querySelectorAll<HTMLButtonElement>(".table-toolbar button").forEach((btn) => {
    if (btn.dataset.bound === "1") return;
    btn.dataset.bound = "1";
    btn.addEventListener("click", async () => {
      const csv = decodeURIComponent(btn.dataset.csv || "");
      const action = btn.dataset.action;
      if (action === "copy") {
        try {
          await navigator.clipboard.writeText(csv);
          flash(btn, "Copiado");
        } catch {
          flash(btn, "Error");
        }
      } else if (action === "download") {
        const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `tabla-${Date.now()}.csv`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
        flash(btn, "↓ ok");
      }
    });
  });
}

function flash(btn: HTMLButtonElement, text: string): void {
  const original = btn.textContent;
  btn.textContent = text;
  setTimeout(() => {
    btn.textContent = original;
  }, 1200);
}

/**
 * Synchronous fallback used when SSR or an early render needs a plain-text
 * preview without DOMPurify. Strips tags via a basic regex; not safe for
 * arbitrary HTML — only meant for short previews / fallbacks.
 */
export function stripMarkdown(input: string): string {
  return input
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/`[^`]*`/g, " ")
    .replace(/[*_>#-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}
