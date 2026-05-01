<script lang="ts">
  import { theme, type Theme } from "$lib/stores/theme.svelte";

  const OPTIONS: { value: Theme; label: string; dot: string }[] = [
    { value: "dark-blue",   label: "Slate",  dot: "#2563eb" },
    { value: "dark-purple", label: "Indigo", dot: "#7f5af0" },
    { value: "light",       label: "Ivory",  dot: "#6246ea" },
  ];
</script>

<div class="flex items-center gap-1 rounded-md border border-bg-elevated bg-bg-card p-0.5">
  {#each OPTIONS as opt (opt.value)}
    <button
      type="button"
      class="flex items-center gap-1.5 rounded px-2 py-1 text-[11px] font-medium transition-colors {theme.current === opt.value ? 'bg-bg-elevated text-text-primary' : 'text-text-secondary hover:text-text-primary'}"
      title={`Tema: ${opt.label}`}
      aria-pressed={theme.current === opt.value}
      onclick={() => theme.set(opt.value)}
    >
      <span class="inline-block h-2 w-2 rounded-full" style:background={opt.dot}></span>
      <span class="hidden sm:inline">{opt.label}</span>
    </button>
  {/each}
</div>
