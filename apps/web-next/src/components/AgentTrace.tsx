"use client";

import type { AgentTraceEntry } from "@/lib/types";

const NODE_STYLES: Record<string, string> = {
  router: "bg-accent-blue/15 text-accent-blue border-accent-blue/30",
  researcher: "bg-status-green/15 text-status-green border-status-green/30",
  analyst: "bg-status-yellow/15 text-status-yellow border-status-yellow/30",
  writer: "bg-purple-500/15 text-purple-300 border-purple-500/30",
  responder: "bg-bg-elevated text-text-secondary border-bg-elevated",
  crew: "bg-orange-500/15 text-orange-300 border-orange-500/30",
  rag: "bg-cyan-500/15 text-cyan-300 border-cyan-500/30",
  web: "bg-pink-500/15 text-pink-300 border-pink-500/30",
};

interface Props {
  trace: AgentTraceEntry[];
  streaming: boolean;
  currentNode: string | null;
  currentAgent: string | null;
}

export function AgentTrace({ trace, streaming, currentNode, currentAgent }: Props) {
  return (
    <div className="flex flex-col gap-3">
      {trace.length === 0 && !streaming && (
        <p className="text-xs text-text-muted">
          Sin razonamiento aún. Envía un mensaje para ver los pasos del agente.
        </p>
      )}

      {trace.map((step) => (
        <div
          key={step.id}
          className="flex flex-col gap-1 rounded-xl border border-bg-elevated bg-bg-card px-3 py-2"
        >
          <div className="flex items-center justify-between">
            <span
              className={`rounded-md border px-2 py-0.5 font-mono text-[10px] font-medium ${
                NODE_STYLES[step.node] ?? "border-bg-elevated bg-bg-elevated text-text-secondary"
              }`}
            >
              {step.agent ? `${step.node}/${step.agent}` : step.node}
            </span>
            <span className="font-mono text-[10px] text-text-muted">
              {new Date(step.timestamp).toLocaleTimeString()}
            </span>
          </div>
          <p className="text-xs text-text-primary">{step.content}</p>
        </div>
      ))}

      {streaming && (currentNode || currentAgent) && (
        <div className="flex items-center gap-2 rounded-xl border border-accent-blue/30 bg-accent-blue/10 px-3 py-2">
          <span className="thinking-dot inline-block h-1.5 w-1.5 rounded-full bg-accent-blue" />
          <span className="thinking-dot inline-block h-1.5 w-1.5 rounded-full bg-accent-blue" />
          <span className="thinking-dot inline-block h-1.5 w-1.5 rounded-full bg-accent-blue" />
          <span className="font-mono text-[11px] font-medium text-accent-blue">
            {currentAgent ? `agent: ${currentAgent}` : `node: ${currentNode}`}
          </span>
        </div>
      )}
    </div>
  );
}
