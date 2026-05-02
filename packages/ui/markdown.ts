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
  const stripped = stripDuplicateSourcesSection(input);
  const raw = (await marked.parse(stripped)) as string;
  const enriched = enrichTables(raw, opts.tableToolbarRows ?? 5);
  const sanitized = await sanitize(enriched);
  return opts.wrap === false ? sanitized : `<div class="agentos-md">${sanitized}</div>`;
}

/**
 * Some models keep emitting a "Referencias" / "Fuentes" / "Sources" section
 * at the bottom of an answer despite the system prompt forbidding it. The
 * frontend already shows numbered source pills under every message via
 * SourcePills, so a markdown duplicate of the same list is pure noise.
 *
 * This is a defense-in-depth strip: if the LAST heading-like line in the
 * message uses one of the forbidden labels, drop it and everything that
 * follows. We accept four shapes:
 *   - `## Referencias` / `### Fuentes` / `# Sources`   (markdown heading)
 *   - `**Referencias**` / `*Fuentes*`                  (bold/italic standalone)
 *   - `Referencias:` / `Fuentes:`                      (plain text + colon)
 *   - `Referencias\n` / `Fuentes\n`                    (plain text alone on a line)
 *
 * Only strips when the section is at the tail of the message — if
 * "Referencias" appears mid-answer it's probably topical content (the
 * user asked about academic references) and we leave it alone.
 */
// Match: optional heading/bold prefix, the forbidden label word,
// optional colon and bold-close, newline(s), then one or more lines
// that LOOK like a sources list (URL, bullet, numbered, or [N]
// reference). Requiring the URL/list-pattern follow-up avoids false
// positives like "Aquí mis referencias importantes." in prose.
const FORBIDDEN_SOURCE_HEADINGS =
  /(?:^|\n)\s*(?:#{1,3}\s+|\*{1,2}\s*)?(?:Referencias|Fuentes|Sources|Citations?|References|Bibliograf[íi]a|Bibliography)\b\s*:?\s*\*{0,2}\s*\n+(?:\s*(?:https?:\/\/|[-*]\s|\d+[.)]\s|\[\s*\d)[^\n]*\n?)+\s*$/i;

function stripDuplicateSourcesSection(input: string): string {
  return input.replace(FORBIDDEN_SOURCE_HEADINGS, "");
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
      let out: string = instance.sanitize(input, {
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
      // Post-process: (1) <img> tags get lazy-loading + decoding hints +
      // referrer policy (so we don't leak the chat URL to image hosts).
      // (2) <a> tags whose visible text is just a 1-3 digit number get a
      // `cite` class so the markdown.css pill style applies. The writer
      // prompt instructs the model to use `[1](URL)` style citations;
      // detecting numeric-only text here turns those into superscript
      // pills automatically without the model having to emit HTML. Done
      // after sanitize so DOMPurify doesn't strip our additions.
      out = out.replace(/<img\b([^>]*)>/g, (_match: string, attrs: string) => {
        const has = (a: string) => new RegExp(`\\b${a}=`).test(attrs);
        const extra =
          (has("loading") ? "" : ' loading="lazy"') +
          (has("decoding") ? "" : ' decoding="async"') +
          (has("referrerpolicy") ? "" : ' referrerpolicy="no-referrer"');
        return `<img${attrs}${extra}>`;
      });
      out = out.replace(
        /<a\b([^>]*?)>(\s*\d{1,3}\s*)<\/a>/g,
        (_m: string, attrs: string, text: string) => {
          // Don't double-class. Don't break existing class= attribute.
          if (/\bclass=/.test(attrs)) {
            return `<a${attrs.replace(/class="([^"]*)"/, 'class="$1 cite"')}>${text}</a>`;
          }
          return `<a${attrs} class="cite">${text}</a>`;
        },
      );
      // (3) Force every link in chat markdown to open in a new tab. Without
      // this a click on a citation pill or any other link navigates the
      // chat tab away, which loses the conversation. We only add target/
      // rel when missing so we don't clobber anything DOMPurify or the
      // upstream renderer set. `noopener noreferrer` is mandatory once
      // target=_blank is set — `noopener` blocks tabnabbing, `noreferrer`
      // also hides the chat URL from the destination site.
      out = out.replace(/<a\b([^>]*?)>/g, (m: string, attrs: string) => {
        const has = (a: string) => new RegExp(`\\b${a}=`).test(attrs);
        if (has("target")) return m;
        const extra = ` target="_blank"${has("rel") ? "" : ' rel="noopener noreferrer"'}`;
        return `<a${attrs}${extra}>`;
      });
      return out;
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
      // Three formats encoded into data-* attrs so the bind-time JS
      // doesn't have to re-parse the table:
      //  - CSV: for pasting into spreadsheets as-is.
      //  - MD: markdown table for pasting back into chat / docs / GitHub.
      //  - HTML: fully inline-styled <table> so Word / Google Sheets /
      //    Notion / Gmail / Outlook keep colors, header bold, zebra rows,
      //    and right-aligned numeric columns when the user pastes it.
      const csv = encodeURIComponent(htmlTableToCsv(full));
      const md = encodeURIComponent(htmlTableToMarkdown(full));
      const styledHtml = encodeURIComponent(htmlTableToStyledHtml(annotated));
      const toolbar = `<div class="table-toolbar">
        <button type="button" data-action="copy-md" data-md="${md}" data-html="${styledHtml}" title="Copiar tabla con formato (Word, Sheets, Notion, Gmail)">Copiar tabla</button>
        <button type="button" data-action="copy" data-csv="${csv}" title="Copiar como CSV">Copiar CSV</button>
        <button type="button" data-action="download" data-html="${styledHtml}" title="Descargar como HTML con estilos">Descargar</button>
      </div>`;
      return `<div class="table-wrap">${toolbar}${annotated}</div>`;
    }
    return annotated;
  });
}

/**
 * Convert a marked-rendered <table> into a fully self-styled HTML snippet:
 * every <table>/<th>/<td>/<tr> gets an inline `style` attribute so the
 * styling survives copy-paste into apps that strip <style> blocks (Word,
 * Google Docs, Sheets, Notion, Gmail, Outlook, Slack canvas).
 *
 * Colors are picked to look reasonable on both light and dark recipient
 * backgrounds — neutral grays + a soft header. Numeric columns (those
 * tagged data-num="1" by annotateNumericCells) get text-align:right and
 * tabular-nums. Even-indexed body rows get a subtle zebra background.
 *
 * The header row is detected as the FIRST <tr> in the table, regardless
 * of whether marked wrapped it in <thead> (it usually doesn't for GFM).
 */
function htmlTableToStyledHtml(tableHtml: string): string {
  const TABLE = "border-collapse:collapse;border-spacing:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;font-size:13px;line-height:1.5;color:#1f2937;margin:0;";
  const TH_BASE = "background:#eef2ff;color:#1e1b4b;font-weight:600;text-align:left;padding:8px 12px;border-bottom:2px solid #6366f1;border-right:1px solid #e0e7ff;";
  const TH_NUM = TH_BASE + "text-align:right;font-variant-numeric:tabular-nums;";
  const TD_BASE = "padding:8px 12px;border-bottom:1px solid #e5e7eb;border-right:1px solid #f3f4f6;";
  const TD_NUM = TD_BASE + "text-align:right;font-variant-numeric:tabular-nums;";
  const TR_ZEBRA = ' style="background:#fafbfc;"';

  let rowIdx = -1;
  return tableHtml
    .replace(/<table>/, `<table style="${TABLE}">`)
    .replace(/<tr>/g, () => {
      rowIdx++;
      // First row is the header — leave it un-zebra'd.
      if (rowIdx === 0) return "<tr>";
      // Even body rows get a subtle background. (rowIdx 1 = first body
      // row, no zebra; rowIdx 2 = second body row, zebra; etc.)
      return rowIdx % 2 === 0 ? `<tr${TR_ZEBRA}>` : "<tr>";
    })
    .replace(/<th([^>]*)>/g, (_m, attrs: string) => {
      const isNum = /data-num="1"/.test(attrs);
      return `<th${attrs} style="${isNum ? TH_NUM : TH_BASE}">`;
    })
    .replace(/<td([^>]*)>/g, (_m, attrs: string) => {
      const isNum = /data-num="1"/.test(attrs);
      return `<td${attrs} style="${isNum ? TD_NUM : TD_BASE}">`;
    });
}

function htmlTableToMarkdown(tableHtml: string): string {
  const rows = [...tableHtml.matchAll(/<tr>([\s\S]*?)<\/tr>/g)].map((rm) => rm[1]);
  if (!rows.length) return "";
  const cells = (row: string, tag: "th" | "td") =>
    [...row.matchAll(new RegExp(`<${tag}[^>]*>([\\s\\S]*?)</${tag}>`, "g"))].map((m) =>
      stripTags(m[1]).replace(/\|/g, "\\|").replace(/\n/g, " ").trim(),
    );
  // Header is the first row's <th>s; bodies are the rest's <td>s.
  const header = cells(rows[0], "th");
  if (!header.length) return rows.map((r) => "| " + cells(r, "td").join(" | ") + " |").join("\n");
  const sep = header.map(() => "---").join(" | ");
  const out = ["| " + header.join(" | ") + " |", "| " + sep + " |"];
  for (const row of rows.slice(1)) {
    const c = cells(row, "td");
    if (c.length) out.push("| " + c.join(" | ") + " |");
  }
  return out.join("\n");
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
      const action = btn.dataset.action;
      if (action === "copy-md") {
        // Copy with formatting preserved. Modern clipboard API takes a
        // ClipboardItem with multiple MIME variants; the receiving app
        // picks whichever it understands. Word / Sheets / Notion / Gmail
        // / Outlook all read text/html and render colors + borders +
        // header bold + zebra rows. Plain editors and the terminal fall
        // back to text/plain (markdown). If the browser doesn't support
        // ClipboardItem (very old Safari / Firefox without flag) we
        // degrade to plain markdown via writeText.
        const md = decodeURIComponent(btn.dataset.md || "");
        const styled = decodeURIComponent(btn.dataset.html || "");
        try {
          if (styled && typeof ClipboardItem !== "undefined") {
            await navigator.clipboard.write([
              new ClipboardItem({
                "text/html": new Blob([styled], { type: "text/html" }),
                "text/plain": new Blob([md], { type: "text/plain" }),
              }),
            ]);
          } else {
            await navigator.clipboard.writeText(md);
          }
          flash(btn, "Copiado ✓");
        } catch {
          // Clipboard API can reject with NotAllowedError if the page
          // lost focus mid-click. Fall back to plain markdown.
          try {
            await navigator.clipboard.writeText(md);
            flash(btn, "Copiado ✓");
          } catch {
            flash(btn, "Error");
          }
        }
        return;
      }
      if (action === "copy") {
        const csv = decodeURIComponent(btn.dataset.csv || "");
        try {
          await navigator.clipboard.writeText(csv);
          flash(btn, "Copiado ✓");
        } catch {
          flash(btn, "Error");
        }
        return;
      }
      if (action === "download") {
        // Download a styled HTML file. Opens in any browser with the
        // visual table look intact; can also be drag-dropped into Excel
        // / Sheets / Numbers, all of which import HTML tables and keep
        // formatting (header bold, alternating rows, right-aligned
        // numeric columns).
        const styled = decodeURIComponent(btn.dataset.html || "");
        const doc = `<!doctype html><html><head><meta charset="utf-8"><title>Tabla AgentOS</title></head><body style="margin:24px;background:#fff;">${styled}</body></html>`;
        const blob = new Blob([doc], { type: "text/html;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `tabla-${Date.now()}.html`;
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
