export type SSEEventType =
  | "token"
  | "status"
  | "crew_status"
  | "thinking"
  | "done"
  | "error";

export interface SSEEvent {
  type: SSEEventType;
  content?: string;
  node?: string;
  agent?: string;
  task?: string;
  error?: string;
  kind?: "all_providers_failed";
  summary?: string;
  providers?: { name: string; reason: string; retry_seconds: number | null }[];
  retry_seconds?: number | null;
  stage?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
  agentTrace?: AgentTraceEntry[];
  attachments?: ChatAttachment[];
}

export interface ChatAttachment {
  filename: string;
  size: number;
  adapter: string;
}

export interface AgentTraceEntry {
  id: string;
  node: string;
  agent?: string;
  content: string;
  timestamp: number;
}

export interface ProviderStatus {
  registered: boolean;
  available: boolean;
  failures: number;
}

export interface HealthResponse {
  status: "ok" | "degraded" | "down";
  providers: Record<string, ProviderStatus>;
  timestamp: number;
}

export type Language = "es" | "en" | "pt" | "fr" | "de" | "it";
export type ContextType = "chat" | "analysis" | "research";

export interface SendOptions {
  contextType?: ContextType;
  language?: Language;
  useRag?: boolean;
  useWeb?: boolean;
}
