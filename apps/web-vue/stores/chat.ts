import { defineStore } from "pinia";

import type {
  AgentTraceEntry,
  ChatAttachment,
  ChatMessage,
  ContextType,
  Language,
  SSEEvent,
  SendOptions,
} from "~/types";

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
}

export const useChatStore = defineStore("chat", {
  state: (): ChatState => ({
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
  }),

  actions: {
    reset() {
      this.messages = [];
      this.error = null;
      this.currentNode = null;
      this.currentAgent = null;
    },

    setLanguage(lang: Language) {
      this.language = lang;
    },

    async rerun() {
      if (!this.lastQuery || this.streaming) return;
      await this.send(this.lastQuery, { contextType: this.lastContextType });
    },

    async send(content: string, options: SendOptions = {}) {
      if (!content.trim() || this.streaming) return;

      const contextType: ContextType = options.contextType ?? "chat";
      const language: Language = options.language ?? this.language;
      const useRag = options.useRag ?? this.useRag;
      const useWeb = options.useWeb ?? this.useWeb;

      const userMsg: ChatMessage = { id: uid(), role: "user", content, timestamp: Date.now() };
      const assistantMsg: ChatMessage = {
        id: uid(),
        role: "assistant",
        content: "",
        timestamp: Date.now(),
        agentTrace: [],
      };

      this.error = null;
      this.streaming = true;
      this.lastQuery = content;
      this.lastContextType = contextType;
      this.messages.push(userMsg, assistantMsg);

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
              this.applyEvent(assistantMsg.id, JSON.parse(payload) as SSEEvent);
            } catch {
              // skip
            }
          }
        }
      } catch (e) {
        this.error = e instanceof Error ? e.message : "Unknown error";
      } finally {
        this.streaming = false;
        this.currentNode = null;
        this.currentAgent = null;
      }
    },

    async ingestFile(file: File): Promise<ChatAttachment | null> {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch("/api/upload", { method: "POST", body: form });
      if (!res.ok) {
        this.error = `Upload failed (${res.status})`;
        return null;
      }
      const json = (await res.json()) as { data?: { adapter?: string; chunks_created?: number }; error?: string };
      if (json.error) {
        this.error = json.error;
        return null;
      }
      const attachment: ChatAttachment = {
        filename: file.name,
        size: file.size,
        adapter: json.data?.adapter ?? "rag",
      };
      this.messages.push({
        id: uid(),
        role: "assistant",
        content: `📎 ${file.name} indexado (${json.data?.chunks_created ?? 0} chunks)`,
        timestamp: Date.now(),
        attachments: [attachment],
      });
      return attachment;
    },

    async exportLastResponseAsPdf() {
      const last = [...this.messages].reverse().find((m) => m.role === "assistant" && m.content);
      if (!last) return;
      const res = await fetch("/api/export-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: "AgentOS — Respuesta", content: last.content }),
      });
      if (!res.ok) {
        this.error = `PDF export failed (${res.status})`;
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

    applyEvent(messageId: string, event: SSEEvent) {
      const msg = this.messages.find((m) => m.id === messageId);
      if (!msg) return;

      switch (event.type) {
        case "status": {
          this.currentNode = event.node ?? null;
          const trace: AgentTraceEntry = {
            id: uid(),
            node: event.node ?? "unknown",
            content: event.content ?? "",
            timestamp: Date.now(),
          };
          msg.agentTrace = [...(msg.agentTrace ?? []), trace];
          break;
        }
        case "crew_status": {
          this.currentAgent = event.agent ?? null;
          const trace: AgentTraceEntry = {
            id: uid(),
            node: "crew",
            agent: event.agent,
            content: event.task ?? "",
            timestamp: Date.now(),
          };
          msg.agentTrace = [...(msg.agentTrace ?? []), trace];
          break;
        }
        case "token":
          msg.content += event.content ?? "";
          break;
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
            this.error = lines.join("\n");
          } else {
            this.error = event.error ?? "Stream error";
          }
          break;
        }
        case "done":
          this.currentNode = null;
          this.currentAgent = null;
          break;
      }
    },
  },
});
