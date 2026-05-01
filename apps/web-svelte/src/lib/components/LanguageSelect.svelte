<script lang="ts">
  import type { Language } from "$lib/types";

  const LABELS: Record<Language, string> = {
    es: "ES",
    en: "EN",
    pt: "PT",
    fr: "FR",
    de: "DE",
    it: "IT",
  };

  let { value, onChange }: { value: Language; onChange: (lang: Language) => void } = $props();
</script>

<select
  class="rounded-md border border-bg-elevated bg-bg-card px-2 py-1 font-mono text-[11px] font-medium text-text-secondary transition-colors hover:border-accent-blue focus:border-accent-blue focus:outline-none"
  aria-label="Idioma"
  value={value}
  onchange={(e) => onChange((e.currentTarget as HTMLSelectElement).value as Language)}
>
  {#each Object.entries(LABELS) as [code, label]}
    <option value={code}>{label}</option>
  {/each}
</select>
