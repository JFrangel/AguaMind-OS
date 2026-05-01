"use client";

import { useEffect, useRef } from "react";

import { AgentTrace } from "@/components/AgentTrace";
import { ChannelsBadge } from "@/components/ChannelsBadge";
import { ChatComposer } from "@/components/ChatComposer";
import { HealthBadge } from "@/components/HealthBadge";
import { LanguageSelect } from "@/components/LanguageSelect";
import { MessageBubble } from "@/components/MessageBubble";
import { ThemeSwitch } from "@/components/ThemeSwitch";
import { useChatStore } from "@/lib/store";

const PRESETS = [
  { label: "Analizar tendencia de ventas", task: "Analiza una tendencia de ventas trimestral con estacionalidad" },
  { label: "Investigar un tema", task: "¿Cuáles son los avances recientes en bases de datos vectoriales?" },
  { label: "Escribir un resumen", task: "Resume la diferencia entre LangGraph y CrewAI" },
  { label: "Detectar anomalías", task: "Esquematiza un workflow para detectar anomalías en series temporales" },
];

export default function HomePage() {
  const messages = useChatStore((s) => s.messages);
  const streaming = useChatStore((s) => s.streaming);
  const currentNode = useChatStore((s) => s.currentNode);
  const currentAgent = useChatStore((s) => s.currentAgent);
  const error = useChatStore((s) => s.error);
  const send = useChatStore((s) => s.send);
  const rerun = useChatStore((s) => s.rerun);
  const lastQuery = useChatStore((s) => s.lastQuery);
  const exportPdf = useChatStore((s) => s.exportLastResponseAsPdf);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, streaming]);

  const lastAssistant = [...messages].reverse().find((m) => m.role === "assistant");
  const canExport = Boolean(lastAssistant?.content) && !streaming;

  return (
    <div className="flex h-full flex-col">
      <header className="border-b border-bg-elevated bg-bg-secondary/60 px-6 py-3 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-blue font-display text-sm font-bold text-white">
              A
            </div>
            <div>
              <h1 className="font-display text-sm font-semibold text-text-primary">AgentOS</h1>
              <p className="text-[11px] text-text-secondary">Multi-agente · streaming</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <ChannelsBadge />
            <ThemeSwitch />
            <LanguageSelect />
            <HealthBadge />
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <main className="flex flex-1 flex-col">
          <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-6">
            <div className="mx-auto flex max-w-3xl flex-col gap-3">
              {messages.length === 0 ? (
                <div className="rounded-2xl border border-bg-elevated bg-bg-card px-8 py-12 text-center">
                  <h2 className="font-display text-lg font-semibold text-text-primary">
                    Empieza una conversación
                  </h2>
                  <p className="mt-2 text-sm text-text-secondary">
                    Pregunta algo. El agente muestra su razonamiento mientras responde.
                  </p>
                  <div className="mt-6 grid grid-cols-1 gap-2 sm:grid-cols-2">
                    {PRESETS.map((preset) => (
                      <button
                        key={preset.label}
                        type="button"
                        onClick={() => send(preset.task)}
                        className="rounded-lg border border-bg-elevated bg-bg-secondary px-4 py-3 text-left text-sm text-text-primary transition-colors hover:border-accent-blue"
                      >
                        {preset.label}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                messages.map((msg) => <MessageBubble key={msg.id} message={msg} />)
              )}

              {error && (
                <div className="rounded-lg border border-status-red/40 bg-status-red/10 px-4 py-3 text-sm text-status-red">
                  {error}
                </div>
              )}
            </div>
          </div>

          <div className="border-t border-bg-elevated bg-bg-secondary/60 px-6 py-4 backdrop-blur">
            <div className="mx-auto max-w-3xl">
              <ChatComposer />
            </div>
          </div>
        </main>

        <aside className="hidden w-72 border-l border-bg-elevated bg-bg-secondary/40 lg:flex lg:flex-col">
          <div className="flex items-center justify-between border-b border-bg-elevated px-5 py-3">
            <div>
              <h2 className="font-display text-xs font-semibold text-text-primary">Razonamiento</h2>
              <p className="text-[11px] text-text-secondary">Pasos en vivo</p>
            </div>
            <div className="flex items-center gap-1">
              <button
                type="button"
                disabled={!lastQuery || streaming}
                onClick={() => rerun()}
                className="rounded-md border border-bg-elevated px-2 py-1 text-[11px] font-medium text-text-secondary transition-colors hover:border-accent-blue hover:text-accent-blue disabled:opacity-40"
                title="Volver a ejecutar la última pregunta con los toggles actuales"
              >
                ↻
              </button>
              <button
                type="button"
                disabled={!canExport}
                onClick={() => exportPdf()}
                className="rounded-md border border-bg-elevated px-2 py-1 text-[11px] font-medium text-text-secondary transition-colors hover:border-accent-blue hover:text-accent-blue disabled:opacity-40"
                title="Exportar última respuesta a PDF"
              >
                PDF
              </button>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto px-5 py-4">
            <AgentTrace
              trace={lastAssistant?.agentTrace ?? []}
              streaming={streaming}
              currentNode={currentNode}
              currentAgent={currentAgent}
            />
          </div>
        </aside>
      </div>
    </div>
  );
}
