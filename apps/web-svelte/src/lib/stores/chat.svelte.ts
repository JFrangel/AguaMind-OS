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
} from "$lib/types";

const uid = (): string =>
  globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2)}`;

class ChatStore {
  messages = $state<ChatMessage[]>([]);
  streaming = $state(false);
  currentNode = $state<string | null>(null);
  currentAgent = $state<string | null>(null);
  error = $state<string | null>(null);
  language = $state<Language>("es");
  useRag = $state(true);
  useWeb = $state(true);
  lastQuery = $state<string | null>(null);
  lastContext: { contextType: ContextType } = $state({ contextType: "chat" });

  async send(content: string, options: SendOptions = {}): Promise<void> {
    if (!content.trim() || this.streaming) return;

    const contextType: ContextType = options.contextType ?? "chat";
    const language: Language = options.language ?? this.language;
    const useRag = options.useRag ?? this.useRag;
    const useWeb = options.useWeb ?? this.useWeb;

    this.lastQuery = content;
    this.lastContext = { contextType };
    this.error = null;
    const userMsg: ChatMessage = {
      id: uid(),
      role: "user",
      content,
      timestamp: Date.now(),
    };
    const assistantMsg: ChatMessage = {
      id: uid(),
      role: "assistant",
      content: "",
      timestamp: Date.now(),
      agentTrace: [],
    };
    this.messages = [...this.messages, userMsg, assistantMsg];
    this.streaming = true;

    try {
      const response = await fetch("/api/chat", {
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

      if (!response.ok || !response.body) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
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
            // skip malformed event
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
  }

  async ingestFile(file: File): Promise<ChatAttachment | null> {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch("/api/upload", { method: "POST", body: form });
    if (!res.ok) {
      this.error = `Upload failed (${res.status})`;
      return null;
    }
    const json = await res.json();
    if (json.error) {
      this.error = json.error;
      return null;
    }
    const attachment: ChatAttachment = {
      filename: file.name,
      size: file.size,
      adapter: json?.data?.adapter ?? "rag",
    };
    const sysMsg: ChatMessage = {
      id: uid(),
      role: "assistant",
      content: `📎 ${file.name} indexado (${json?.data?.chunks_created ?? 0} chunks)`,
      timestamp: Date.now(),
      attachments: [attachment],
    };
    this.messages = [...this.messages, sysMsg];
    return attachment;
  }

  async rerun(): Promise<void> {
    if (!this.lastQuery || this.streaming) return;
    await this.send(this.lastQuery, this.lastContext);
  }

  async exportLastResponseAsPdf(): Promise<void> {
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
  }

  private applyEvent(messageId: string, event: SSEEvent): void {
    const idx = this.messages.findIndex((m) => m.id === messageId);
    if (idx < 0) return;
    const msg = this.messages[idx];

    // Svelte 5 $state proxies are deeply reactive — direct mutation of
    // msg.content / msg.agentTrace is enough to trigger updates. We do NOT
    // do `this.messages = [...this.messages]` because that rebuilds the
    // array on every token, forcing a re-render of every MessageBubble
    // (each one then re-runs its markdown effect). With ~100 tokens per
    // response the cost is quadratic in the message length.

    switch (event.type) {
      case "status": {
        this.currentNode = event.node ?? null;
        msg.agentTrace = [
          ...(msg.agentTrace ?? []),
          {
            id: uid(),
            node: event.node ?? "unknown",
            content: event.content ?? "",
            timestamp: Date.now(),
          },
        ];
        break;
      }
      case "crew_status": {
        this.currentAgent = event.agent ?? null;
        msg.agentTrace = [
          ...(msg.agentTrace ?? []),
          {
            id: uid(),
            node: "crew",
            agent: event.agent,
            content: event.task ?? "",
            timestamp: Date.now(),
          },
        ];
        break;
      }
      case "token":
        // Pure mutation — no array rebuild. Token arrival rate is ~30/s
        // when the LLM is fast; the array reassignment used to dominate
        // CPU here.
        msg.content += event.content ?? "";
        break;
      case "sources": {
        // Web/RAG sources are emitted as a single event with all hits.
        // Stash them on the assistant message so MessageBubble can render
        // pills under the streamed answer.
        const items = event.items ?? [];
        if (event.kind === "web") {
          msg.webSources = [...(msg.webSources ?? []), ...(items as WebSourceItem[])];
        } else if (event.kind === "rag") {
          msg.ragSources = [...(msg.ragSources ?? []), ...(items as RagSourceItem[])];
        }
        break;
      }
      case "error": {
        // Friendly path: rate-limit on all 3 providers shows a compact summary
        // + per-provider status instead of dumping the raw stack trace.
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
  }

  reset(): void {
    this.messages = [];
    this.error = null;
    this.currentNode = null;
    this.currentAgent = null;
  }
}

export const chat = new ChatStore();
