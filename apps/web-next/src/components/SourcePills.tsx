"use client";

import type { RagSourceItem, WebSourceItem } from "@/lib/types";

function host(url: string | undefined): string {
  if (!url) return "";
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

interface Props {
  web?: WebSourceItem[];
  rag?: RagSourceItem[];
}

export function SourcePills({ web, rag }: Props) {
  if (!web?.length && !rag?.length) return null;

  return (
    <div className="mt-3 flex flex-col gap-2 border-t border-bg-elevated pt-3">
      {web?.length ? (
        <div>
          <div className="mb-1 font-mono text-[10px] uppercase tracking-wider text-text-muted">
            Fuentes web
          </div>
          <div className="flex flex-wrap gap-1.5">
            {web.map((src, i) => (
              <a
                key={src.url ?? i}
                href={src.url}
                target="_blank"
                rel="noopener noreferrer"
                title={src.snippet || src.title}
                className="inline-flex items-center gap-1.5 rounded-md border border-bg-elevated bg-bg-card px-2 py-1 text-[11px] text-text-secondary transition-colors hover:border-accent-blue hover:text-accent-blue"
              >
                <span className="font-mono text-[10px] text-text-muted">{i + 1}</span>
                <span className="max-w-[180px] truncate font-medium">
                  {src.title || host(src.url)}
                </span>
                <span className="text-[10px] text-text-muted">↗</span>
              </a>
            ))}
          </div>
        </div>
      ) : null}

      {rag?.length ? (
        <div>
          <div className="mb-1 font-mono text-[10px] uppercase tracking-wider text-text-muted">
            Fuentes internas (RAG)
          </div>
          <div className="flex flex-wrap gap-1.5">
            {rag.map((src, i) => (
              <span
                key={src.id ?? i}
                title={src.snippet}
                className="inline-flex items-center gap-1.5 rounded-md border border-bg-elevated bg-bg-card px-2 py-1 font-mono text-[11px] text-text-secondary"
              >
                <span className="text-[10px] text-text-muted">INT-{i + 1}</span>
                <span className="max-w-[160px] truncate">
                  {src.filename ?? src.id ?? "interno"}
                </span>
                {typeof src.score === "number" ? (
                  <span className="text-[10px] text-text-muted">{src.score.toFixed(2)}</span>
                ) : null}
              </span>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
