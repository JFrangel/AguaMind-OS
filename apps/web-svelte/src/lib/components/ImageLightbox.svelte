<script lang="ts">
  import { onMount } from "svelte";
  import { lightbox } from "$lib/stores/lightbox.svelte";

  function host(url: string | undefined): string {
    if (!url) return "";
    try {
      return new URL(url).hostname.replace(/^www\./, "");
    } catch {
      return url;
    }
  }

  function onKey(e: KeyboardEvent): void {
    if (e.key === "Escape") lightbox.close();
  }

  onMount(() => {
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });
</script>

{#if lightbox.open}
  <div
    role="dialog"
    aria-modal="true"
    aria-label="Vista previa de imagen"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm"
    onclick={() => lightbox.close()}
    onkeydown={onKey}
    tabindex="-1"
  >
    <div
      class="relative flex max-h-[90vh] max-w-5xl flex-col overflow-hidden rounded-xl border border-bg-elevated bg-bg-card shadow-2xl"
      onclick={(e) => e.stopPropagation()}
      role="document"
    >
      <button
        type="button"
        aria-label="Cerrar vista previa"
        onclick={() => lightbox.close()}
        class="absolute right-3 top-3 z-10 rounded-md border border-bg-elevated bg-bg-card/80 px-2 py-1 font-mono text-xs text-text-secondary backdrop-blur transition-colors hover:border-accent-blue hover:text-accent-blue"
      >
        ✕
      </button>

      <div class="flex flex-1 items-center justify-center overflow-auto p-2">
        <img
          src={lightbox.open.src}
          alt={lightbox.open.alt ?? ""}
          class="max-h-[75vh] max-w-full object-contain"
          loading="eager"
          decoding="async"
          referrerpolicy="no-referrer"
        />
      </div>

      <div class="flex flex-wrap items-center justify-between gap-3 border-t border-bg-elevated bg-bg-secondary/60 px-4 py-3 backdrop-blur">
        <div class="flex min-w-0 flex-col">
          {#if lightbox.open.caption}
            <span class="truncate text-sm font-medium text-text-primary">{lightbox.open.caption}</span>
          {/if}
          {#if lightbox.open.sourceUrl}
            <span class="truncate font-mono text-[11px] text-text-muted">
              {host(lightbox.open.sourceUrl)}
            </span>
          {/if}
        </div>
        {#if lightbox.open.sourceUrl}
          <a
            href={lightbox.open.sourceUrl}
            target="_blank"
            rel="noopener noreferrer"
            class="inline-flex items-center gap-1.5 rounded-md bg-accent-blue px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-accent-blue-hover"
          >
            Ir a la página
            <span aria-hidden="true">↗</span>
          </a>
        {/if}
      </div>
    </div>
  </div>
{/if}
