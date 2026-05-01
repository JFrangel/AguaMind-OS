import type { Profile } from "@agentos/profiles";

import type {
  AgentTraceEntry,
  ChatAttachment,
  ChatMessage,
  ContextType,
  Language,
  RagSourceItem,
  SSEEvent,
  WebSourceItem,
} from "$lib/types";

const uid = (): string =>
  globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2)}`;

/**
 * Chat store specialised for `/apps/<slug>` routes. Mirrors the main
 * `ChatStore` but pre-fills:
 *   - `system_prompt_override` from the active profile
 *   - default toggles (RAG/Web), language, cascade
 * The conversation state is independent from the main chat — switching
 * between profiles doesn't mix histories.
 */
class ProfileChatStore {
  profile: Profile | null = $state(null);
  messages = $state<ChatMessage[]>([]);
  streaming = $state(false);
  currentNode = $state<string | null>(null);
  currentAgent = $state<string | null>(null);
  error = $state<string | null>(null);
  language = $state<Language>("es");
  useRag = $state(false);
  useWeb = $state(false);
  lastQuery = $state<string | null>(null);

  configure(profile: Profile): void {
    // First time we see this profile (or a new one): reset history. Keeping
    // history across profile switches would mix system prompts in the same
    // conversation, which is incoherent.
    if (!this.profile || this.profile.slug !== profile.slug) {
      this.profile = profile;
      this.messages = [];
      this.error = null;
      this.lastQuery = null;
      this.language = profile.defaultLanguage;
      this.useRag = profile.defaultUseRag;
      this.useWeb = profile.defaultUseWeb;
    }
  }

  async send(content: string): Promise<void> {
    if (!content.trim() || this.streaming || !this.profile) return;
    const profile = this.profile;

    this.lastQuery = content;
    this.error = null;

    const userMsg: ChatMessage = { id: uid(), role: "user", content, timestamp: Date.now() };
    const assistantMsg: ChatMessage = {
      id: uid(),
      role: "assistant",
      content: "",
      timestamp: Date.now(),
      agentTrace: [],
    };
    this.messages = [...this.messages, userMsg, assistantMsg];
    this.streaming = true;

    const contextType: ContextType =
      profile.defaultUseRag || profile.defaultUseWeb ? "research" : "chat";

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: content,
          context_type: contextType,
          language: this.language,
          use_rag: this.useRag,
          use_web: this.useWeb,
          cascade: profile.cascade,
          system_prompt_override: profile.systemPrompt,
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

  async rerun(): Promise<void> {
    if (!this.lastQuery || this.streaming) return;
    await this.send(this.lastQuery);
  }

  async ingestFile(file: File): Promise<ChatAttachment | null> {
    const form = new FormData();
    form.append("file", file);
    if (this.profile) form.append("source", this.profile.slug);
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
    this.messages = [
      ...this.messages,
      {
        id: uid(),
        role: "assistant",
        content: `📎 ${file.name} indexado (${json?.data?.chunks_created ?? 0} chunks)`,
        timestamp: Date.now(),
        attachments: [attachment],
      },
    ];
    return attachment;
  }

  private applyEvent(messageId: string, event: SSEEvent): void {
    const idx = this.messages.findIndex((m) => m.id === messageId);
    if (idx < 0) return;
    const msg = this.messages[idx];

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
    this.messages = [...this.messages];
  }
}

export const profileChat = new ProfileChatStore();
