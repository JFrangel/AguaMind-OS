/**
 * A "Profile" wraps AgentOS for one specific problem domain. Multiple
 * profiles coexist in the same deployment; routing is by slug:
 *
 *     /apps/{slug}    → custom landing + chat configured for this domain
 *
 * The agent backend stays generic — the profile only adjusts:
 *   - system prompt sent to the responder/writer nodes
 *   - default toggles (RAG/Web on or off)
 *   - default language and cascade
 *   - the presets shown in the empty chat
 *   - the visual accent + emoji + tagline of the landing hero
 *
 * Anything else in AgentOS (RAG store, file upload, NL→SQL, web search,
 * status events, source pills) keeps working unchanged.
 */
export type Language = "es" | "en" | "pt" | "fr" | "de" | "it";
export type Cascade = "speed" | "reasoning" | "cheap" | "multimodal";

export interface ProfilePreset {
  label: string;
  task: string;
  /** Optional: emoji shown left of the label in the preset card */
  icon?: string;
}

export interface Profile {
  /** URL slug. Must match `[a-z0-9-]+`. */
  slug: string;
  /** Display name shown in the hero. */
  name: string;
  /** One-line tagline below the name. */
  tagline: string;
  /** 2-3 sentence description for the landing card. */
  description: string;

  /** Emoji used as the brand mark (logo box). */
  emoji?: string;
  /**
   * Accent color override (any CSS color). When set, the landing replaces
   * the active theme's `--color-accent-blue` so the same chat UI wears the
   * profile's brand. Falls back to the active theme accent if absent.
   */
  accentOverride?: string;

  /** System prompt sent to the responder/writer agents for this profile. */
  systemPrompt: string;
  defaultLanguage: Language;
  defaultUseRag: boolean;
  defaultUseWeb: boolean;
  cascade?: Cascade;

  /** Preset cards shown in the empty chat. */
  presets: ProfilePreset[];
  /** Override placeholder of the chat composer. */
  placeholder?: string;

  /**
   * Optional disclaimer rendered above the chat. Examples:
   *  - "No constituye consejo médico — siempre consultá a un profesional."
   *  - "Esta herramienta no reemplaza a un abogado."
   */
  warning?: string;

  /**
   * Files the operator should ingest into the RAG store for this profile
   * to work well. Surfaced as a checklist in the landing.
   */
  suggestedFiles?: string[];
}
