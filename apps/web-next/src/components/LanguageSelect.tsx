"use client";

import { useChatStore } from "@/lib/store";
import type { Language } from "@/lib/types";

const LABELS: Record<Language, string> = {
  es: "ES",
  en: "EN",
  pt: "PT",
  fr: "FR",
  de: "DE",
  it: "IT",
};

export function LanguageSelect() {
  const language = useChatStore((s) => s.language);
  const setLanguage = useChatStore((s) => s.setLanguage);

  return (
    <select
      aria-label="Idioma"
      value={language}
      onChange={(e) => setLanguage(e.target.value as Language)}
      className="rounded-md border border-bg-elevated bg-bg-card px-2 py-1 font-mono text-[11px] font-medium text-text-secondary transition-colors hover:border-accent-blue focus:border-accent-blue focus:outline-none"
    >
      {Object.entries(LABELS).map(([code, label]) => (
        <option key={code} value={code}>
          {label}
        </option>
      ))}
    </select>
  );
}
