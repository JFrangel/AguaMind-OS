export interface ApiResponse<T = unknown> {
  data: T | null;
  error: string | null;
  meta?: Record<string, unknown>;
}

export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: number;
  metadata?: Record<string, unknown>;
}

export interface AgentStatus {
  status: "idle" | "thinking" | "searching" | "analyzing" | "responding" | "error";
  currentNode: string | null;
  currentAgent: string | null;
  progress: number;
}

export interface SSEEvent {
  type: "token" | "status" | "crew_status" | "thinking" | "done" | "error";
  content?: string;
  node?: string;
  agent?: string;
  task?: string;
  error?: string;
}

export interface LLMProviderStatus {
  provider: "groq" | "openrouter" | "gemini";
  available: boolean;
  latencyMs?: number;
}

export interface HealthResponse {
  status: "ok" | "degraded" | "down";
  providers: LLMProviderStatus[];
  timestamp: number;
}

export interface DocumentChunk {
  id: string;
  content: string;
  metadata: Record<string, unknown>;
  score?: number;
}

export interface GeoPoint {
  lat: number;
  lon: number;
  label?: string;
}

export interface AnomalyResult {
  index: number;
  score: number;
  isAnomaly: boolean;
  features: Record<string, number>;
}
