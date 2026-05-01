<script setup lang="ts">
import { useChatStore } from "~/stores/chat";
import type { Language } from "~/types";

const chat = useChatStore();

const LABELS: Record<Language, string> = {
  es: "ES",
  en: "EN",
  pt: "PT",
  fr: "FR",
  de: "DE",
  it: "IT",
};

function onChange(e: Event) {
  const value = (e.target as HTMLSelectElement).value as Language;
  chat.setLanguage(value);
}
</script>

<template>
  <select
    aria-label="Idioma"
    :value="chat.language"
    class="rounded-md border border-bg-elevated bg-bg-card px-2 py-1 font-mono text-[11px] font-medium text-text-secondary transition-colors hover:border-accent-blue focus:border-accent-blue focus:outline-none"
    @change="onChange"
  >
    <option v-for="(label, code) in LABELS" :key="code" :value="code">{{ label }}</option>
  </select>
</template>
