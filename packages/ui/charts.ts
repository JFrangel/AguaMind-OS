/**
 * Tiny SVG chart renderer for AgentOS chat bubbles.
 *
 * The agent can emit a fenced code block tagged `chart` with a JSON body:
 *
 *     ```chart
 *     { "type": "bar", "title": "Ventas Q1", "data": [["Ene", 120], ["Feb", 95], ["Mar", 140]] }
 *     ```
 *
 * `renderChart()` parses that body and returns an SVG string. Three chart
 * types are supported: bar (categorical), line (sequential), and area
 * (line + filled below). No external dependencies — the SVG is raw markup
 * styled by `markdown.css`. Robust to malformed input: returns an inline
 * error block instead of throwing so a single bad chart doesn't break the
 * whole rendered message.
 */

export interface ChartSpec {
  type?: "bar" | "line" | "area";
  title?: string;
  subtitle?: string;
  /**
   * Either an array of [label, value] tuples (single series) or an array of
   * { label, value } objects. Accepted both for ergonomics: agents tend to
   * emit one or the other depending on the model.
   */
  data?: Array<[string, number] | { label: string; value: number }>;
  /** Optional units suffix shown next to each value (e.g. "%", " USD") */
  unit?: string;
}

export function renderChart(jsonText: string): string {
  let spec: ChartSpec;
  try {
    spec = JSON.parse(jsonText);
  } catch (e) {
    return errorChart(`JSON inválido: ${e instanceof Error ? e.message : "?"}`);
  }
  const points = normalizePoints(spec.data);
  if (!points.length) {
    return errorChart("Sin datos para graficar");
  }
  const type = spec.type ?? "bar";
  const body =
    type === "line"
      ? lineSvg(points, false)
      : type === "area"
        ? lineSvg(points, true)
        : barSvg(points, spec.unit);
  return wrap(body, spec.title, spec.subtitle);
}

interface Pt {
  label: string;
  value: number;
}

function normalizePoints(data: ChartSpec["data"]): Pt[] {
  if (!Array.isArray(data)) return [];
  const out: Pt[] = [];
  for (const item of data) {
    if (Array.isArray(item) && item.length >= 2) {
      const [label, value] = item;
      const n = typeof value === "number" ? value : Number(value);
      if (Number.isFinite(n)) out.push({ label: String(label), value: n });
    } else if (item && typeof item === "object") {
      const label = (item as { label: unknown }).label;
      const value = (item as { value: unknown }).value;
      const n = typeof value === "number" ? value : Number(value);
      if (label !== undefined && Number.isFinite(n)) {
        out.push({ label: String(label), value: n });
      }
    }
  }
  return out;
}

function wrap(inner: string, title?: string, subtitle?: string): string {
  const titleHtml = title ? `<div class="chart-title">${escapeHtml(title)}</div>` : "";
  const subHtml = subtitle ? `<div class="chart-sub">${escapeHtml(subtitle)}</div>` : "";
  return `<div class="chart-block">${titleHtml}${subHtml}${inner}</div>`;
}

function errorChart(msg: string): string {
  return `<div class="chart-block"><div class="chart-error">⚠ ${escapeHtml(msg)}</div></div>`;
}

function escapeHtml(s: string): string {
  return s.replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c] ?? c,
  );
}

function fmt(n: number, unit?: string): string {
  // Compact formatting for axis labels; full for tooltips.
  let s: string;
  if (Math.abs(n) >= 1_000_000) s = (n / 1_000_000).toFixed(1) + "M";
  else if (Math.abs(n) >= 1_000) s = (n / 1_000).toFixed(1) + "K";
  else if (Number.isInteger(n)) s = String(n);
  else s = n.toFixed(2);
  return unit ? s + unit : s;
}

const W = 480;
const H = 220;
const PAD_L = 38;
const PAD_R = 12;
const PAD_T = 12;
const PAD_B = 32;

function barSvg(points: Pt[], unit?: string): string {
  const innerW = W - PAD_L - PAD_R;
  const innerH = H - PAD_T - PAD_B;
  const max = Math.max(0, ...points.map((p) => p.value));
  const min = Math.min(0, ...points.map((p) => p.value));
  const range = max - min || 1;
  const step = innerW / points.length;
  const barW = Math.max(2, step * 0.65);
  const yOf = (v: number) => PAD_T + ((max - v) / range) * innerH;

  const ticks = niceTicks(min, max, 4);
  const grid = ticks
    .map((t) => `<line x1="${PAD_L}" y1="${yOf(t)}" x2="${W - PAD_R}" y2="${yOf(t)}"/>`)
    .join("");
  const yLabels = ticks
    .map((t) => `<text x="${PAD_L - 6}" y="${yOf(t) + 3}" text-anchor="end">${escapeHtml(fmt(t, unit))}</text>`)
    .join("");
  const bars = points
    .map((p, i) => {
      const x = PAD_L + i * step + (step - barW) / 2;
      const y0 = yOf(Math.max(0, p.value));
      const y1 = yOf(Math.min(0, p.value));
      const h = Math.max(1, y1 - y0);
      return `<rect class="bar" x="${x}" y="${y0}" width="${barW}" height="${h}" rx="2"><title>${escapeHtml(
        p.label,
      )}: ${escapeHtml(fmt(p.value, unit))}</title></rect>`;
    })
    .join("");
  const xLabels = points
    .map((p, i) => {
      const cx = PAD_L + i * step + step / 2;
      const short = p.label.length > 10 ? p.label.slice(0, 9) + "…" : p.label;
      return `<text class="bar-label" x="${cx}" y="${H - PAD_B + 14}">${escapeHtml(short)}</text>`;
    })
    .join("");

  return `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" role="img">
  <g class="grid">${grid}</g>
  <g class="axis">${yLabels}</g>
  ${bars}
  ${xLabels}
</svg>`;
}

function lineSvg(points: Pt[], filled: boolean): string {
  const innerW = W - PAD_L - PAD_R;
  const innerH = H - PAD_T - PAD_B;
  const max = Math.max(...points.map((p) => p.value));
  const min = Math.min(...points.map((p) => p.value));
  const range = max - min || 1;
  const xOf = (i: number) =>
    PAD_L + (points.length === 1 ? innerW / 2 : (i / (points.length - 1)) * innerW);
  const yOf = (v: number) => PAD_T + ((max - v) / range) * innerH;

  const linePath = points
    .map((p, i) => `${i === 0 ? "M" : "L"}${xOf(i)} ${yOf(p.value)}`)
    .join(" ");
  const areaPath = filled
    ? `${linePath} L${xOf(points.length - 1)} ${yOf(min)} L${xOf(0)} ${yOf(min)} Z`
    : "";
  const ticks = niceTicks(min, max, 4);
  const grid = ticks
    .map((t) => `<line x1="${PAD_L}" y1="${yOf(t)}" x2="${W - PAD_R}" y2="${yOf(t)}"/>`)
    .join("");
  const yLabels = ticks
    .map((t) => `<text x="${PAD_L - 6}" y="${yOf(t) + 3}" text-anchor="end">${escapeHtml(fmt(t))}</text>`)
    .join("");
  const dots = points
    .map(
      (p, i) =>
        `<circle class="dot" cx="${xOf(i)}" cy="${yOf(p.value)}" r="2.5"><title>${escapeHtml(
          p.label,
        )}: ${escapeHtml(fmt(p.value))}</title></circle>`,
    )
    .join("");
  const xLabels = points
    .map((p, i) => {
      const short = p.label.length > 10 ? p.label.slice(0, 9) + "…" : p.label;
      return `<text class="bar-label" x="${xOf(i)}" y="${H - PAD_B + 14}">${escapeHtml(short)}</text>`;
    })
    .join("");

  return `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" role="img">
  <g class="grid">${grid}</g>
  <g class="axis">${yLabels}</g>
  ${filled ? `<path class="area" d="${areaPath}"/>` : ""}
  <path class="line" d="${linePath}"/>
  ${dots}
  ${xLabels}
</svg>`;
}

function niceTicks(min: number, max: number, count: number): number[] {
  if (min === max) return [min];
  const step = niceStep((max - min) / count);
  const start = Math.floor(min / step) * step;
  const end = Math.ceil(max / step) * step;
  const out: number[] = [];
  for (let v = start; v <= end + 1e-9; v += step) {
    out.push(Number(v.toFixed(6)));
  }
  return out;
}

function niceStep(raw: number): number {
  if (raw <= 0) return 1;
  const exp = Math.floor(Math.log10(raw));
  const base = Math.pow(10, exp);
  const norm = raw / base;
  let nice: number;
  if (norm < 1.5) nice = 1;
  else if (norm < 3) nice = 2;
  else if (norm < 7) nice = 5;
  else nice = 10;
  return nice * base;
}
