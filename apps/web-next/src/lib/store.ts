"use client";

import { create } from "zustand";

import type {
  AgentTraceEntry,
  ChatAttachment,
  ChatMessage,
  ContextType,
  Language,
  RagSourceItem,
  SSEEvent,
  SendOptions,
  WebSourceItem,
} from "./types";

const uid = (): string =>
  globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2)}`;

interface ChatState {
  messages: ChatMessage[];
  streaming: boolean;
  currentNode: string | null;
  currentAgent: string | null;
  error: string | null;
  language: Language;
  useRag: boolean;
  useWeb: boolean;
  lastQuery: string | null;
  lastContextType: ContextType;
  setLanguage: (lang: Language) => void;
  setUseRag: (v: boolean) => void;
  setUseWeb: (v: boolean) => void;
  send: (content: string, options?: SendOptions) => Promise<void>;
  rerun: () => Promise<void>;
  ingestFile: (file: File) => Promise<ChatAttachment | null>;
  exportLastResponseAsPdf: () => Promise<void>;
  reset: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  streaming: false,
  currentNode: null,
  currentAgent: null,
  error: null,
  language: "es",
  useRag: true,
  useWeb: true,
  lastQuery: null,
  lastContextType: "chat",

  setLanguage: (language) => set({ language }),
  setUseRag: (useRag) => set({ useRag }),
  setUseWeb: (useWeb) => set({ useWeb }),
  reset: () => set({ messages: [], error: null, currentNode: null, currentAgent: null }),

  send: async (content, options = {}) => {
    const state = get();
    if (!content.trim() || state.streaming) return;

    const contextType: ContextType = options.contextType ?? "chat";
    const language: Language = options.language ?? state.language;
    const useRag = options.useRag ?? state.useRag;
    const useWeb = options.useWeb ?? state.useWeb;

    const userMsg: ChatMessage = { id: uid(), role: "user", content, timestamp: Date.now() };
    const assistantMsg: ChatMessage = {
      id: uid(),
      role: "assistant",
      content: "",
      timestamp: Date.now(),
      agentTrace: [],
    };

    set((s) => ({
      error: null,
      streaming: true,
      lastQuery: content,
      lastContextType: contextType,
      messages: [...s.messages, userMsg, assistantMsg],
    }));

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: content,
          context_type: contextType,
          language,
          use_rag: useRag,
          use_web: useWeb,
        }),
      });

      if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const payload = line.slice(6).trim();
          if (!payload) continue;
          try {
            applyEvent(set, assistantMsg.id, JSON.parse(payload) as SSEEvent);
          } catch {
            // skip
          }
        }
      }
    } catch (e) {
      set({ error: e instanceof Error ? e.message : "Unknown error" });
    } finally {
      set({ streaming: false, currentNode: null, currentAgent: null });
    }
  },

  rerun: async () => {
    const { lastQuery, lastContextType, streaming, send } = get();
    if (!lastQuery || streaming) return;
    await send(lastQuery, { contextType: lastContextType });
  },

  ingestFile: async (file) => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch("/api/upload", { method: "POST", body: form });
    if (!res.ok) {
      set({ error: `Upload failed (${res.status})` });
      return null;
    }
    const json = (await res.json()) as { data?: { adapter?: string; chunks_created?: number }; error?: string };
    if (json.error) {
      set({ error: json.error });
      return null;
    }
    const attachment: ChatAttachment = {
      filename: file.name,
      size: file.size,
      adapter: json.data?.adapter ?? "rag",
    };
    const sysMsg: ChatMessage = {
      id: uid(),
      role: "assistant",
      content: `📎 ${file.name} indexado (${json.data?.chunks_created ?? 0} chunks)`,
      timestamp: Date.now(),
      attachments: [attachment],
    };
    set((s) => ({ messages: [...s.messages, sysMsg] }));
    return attachment;
  },

  exportLastResponseAsPdf: async () => {
    const last = [...get().messages].reverse().find((m) => m.role === "assistant" && m.content);
    if (!last) return;
    const res = await fetch("/api/export-pdf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: "AgentOS — Respuesta", content: last.content }),
    });
    if (!res.ok) {
      set({ error: `PDF export failed (${res.status})` });
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `agentos-${Date.now()}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  },
}));

function applyEvent(
  set: (updater: (s: ChatState) => Partial<ChatState>) => void,
  messageId: string,
  event: SSEEvent,
): void {
  set((s) => {
    const idx = s.messages.findIndex((m) => m.id === messageId);
    if (idx < 0) return {};
    const msg = { ...s.messages[idx] };
    let patch: Partial<ChatState> = {};

    switch (event.type) {
      case "status": {
        const trace: AgentTraceEntry = {
          id: uid(),
          node: event.node ?? "unknown",
          content: event.content ?? "",
          timestamp: Date.now(),
        };
        msg.agentTrace = [...(msg.agentTrace ?? []), trace];
        patch = { currentNode: event.node ?? null };
        break;
      }
      case "crew_status": {
        const trace: AgentTraceEntry = {
          id: uid(),
          node: "crew",
          agent: event.agent,
          content: event.task ?? "",
          timestamp: Date.now(),
        };
        msg.agentTrace = [...(msg.agentTrace ?? []), trace];
        patch = { currentAgent: event.agent ?? null };
        break;
      }
      case "token":
        msg.content += event.content ?? "";
        break;
      case "sources": {
        const items = event.items ?? [];
        if (event.kind === "web") {
          msg.webSources = [...(msg.webSources ?? []), ...(items as WebSourceItem[])];
        } else if (event.kind === "rag") {
          msg.ragSources = [...(msg.ragSources ?? []), ...(items as RagSourceItem[])];
        }
        break;
      }
      case "error": {
        if (event.kind === "all_providers_failed" && event.summary) {
          const lines = [event.summary];
          if (event.providers?.length) {
            lines.push(
              event.providers
                .map(
                  (p) =>
                    `• ${p.name}: ${p.reason}${
                      p.retry_seconds !== null ? ` (retry ${p.retry_seconds}s)` : ""
                    }`,
                )
                .join("\n"),
            );
          }
          patch = { error: lines.join("\n") };
        } else {
          patch = { error: event.error ?? "Stream error" };
        }
        break;
      }
      case "done":
        patch = { currentNode: null, currentAgent: null };
        break;
    }

    const messages = [...s.messages];
    messages[idx] = msg;
    return { messages, ...patch };
  });
}
