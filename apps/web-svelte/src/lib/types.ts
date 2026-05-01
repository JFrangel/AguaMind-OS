export type SSEEventType =
  | "token"
  | "status"
  | "crew_status"
  | "thinking"
  | "done"
  | "error"
  | "sources";

export interface WebSourceItem {
  title?: string;
  url?: string;
  snippet?: string;
}

export interface RagSourceItem {
  id?: string;
  score?: number;
  filename?: string;
  snippet?: string;
}

export interface SSEEvent {
  type: SSEEventType;
  content?: string;
  node?: string;
  agent?: string;
  task?: string;
  error?: string;
  // Extended shape emitted by the runner when AllProvidersFailed:
  kind?: "all_providers_failed" | "rag" | "web";
  summary?: string;
  providers?: { name: string; reason: string; retry_seconds: number | null }[];
  retry_seconds?: number | null;
  stage?: string;
  // For type="sources":
  items?: (WebSourceItem | RagSourceItem)[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
  agentTrace?: AgentTraceEntry[];
  attachments?: ChatAttachment[];
  webSources?: WebSourceItem[];
  ragSources?: RagSourceItem[];
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
