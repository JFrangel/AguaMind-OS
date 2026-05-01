/**
 * Markdown rendering helper used by the 3 frontends. Wraps `marked` + `dompurify`
 * so the chat bubbles can show GFM tables, code blocks, lists, links, blockquotes
 * and inline code without each frontend re-implementing the pipeline.
 *
 * Pure ESM, no DOM dependency at module load — DOMPurify is imported inside
 * `renderMarkdown` so SSR consumers (SvelteKit, Next, Nuxt) don't pay the cost
 * during server render of pages that don't show user content.
 */
import { marked } from "marked";

marked.setOptions({
  gfm: true,
  breaks: true,
});

export interface RenderOptions {
  /**
   * When true, the result is wrapped in a `<div class="agentos-md">` so callers
   * can target a single class for typography styles.
   */
  wrap?: boolean;
}

export async function renderMarkdown(input: string, opts: RenderOptions = {}): Promise<string> {
  if (!input) return "";
  const raw = (await marked.parse(input)) as string;
  const sanitized = await sanitize(raw);
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
    return (input: string) =>
      instance.sanitize(input, {
        ADD_ATTR: ["target", "rel"],
        ALLOW_DATA_ATTR: false,
      });
  })();
  return purifyPromise;
}

async function sanitize(html: string): Promise<string> {
  const purify = await loadPurify();
  return purify(html);
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
