<script lang="ts">
  import { lightbox } from "$lib/stores/lightbox.svelte";
  import type { RagSourceItem, WebSourceItem } from "$lib/types";

  let {
    web,
    rag,
  }: {
    web: WebSourceItem[] | undefined;
    rag: RagSourceItem[] | undefined;
  } = $props();

  function host(url: string | undefined): string {
    if (!url) return "";
    try {
      return new URL(url).hostname.replace(/^www\./, "");
    } catch {
      return url;
    }
  }

  function previewSource(src: WebSourceItem): void {
    if (!src.image) return;
    lightbox.show({
      src: src.image,
      alt: src.title,
      sourceUrl: src.url,
      caption: src.title,
    });
  }

  const webWithImage = $derived((web ?? []).filter((s) => s.image));
</script>

{#if web?.length || rag?.length}
  <div class="mt-3 flex flex-col gap-3 border-t border-bg-elevated pt-3">
    {#if webWithImage.length > 0}
      <div class="flex flex-wrap gap-2">
        {#each webWithImage as src, i (src.url ?? i)}
          <button
            type="button"
            onclick={() => previewSource(src)}
            class="group block w-32 overflow-hidden rounded-md border border-bg-elevated bg-bg-card text-left transition-colors hover:border-accent-blue"
            title={src.title || src.url}
            aria-label={`Vista previa de ${src.title ?? "imagen"}`}
          >
            <img
              src={src.image ?? ""}
              alt={src.title || ""}
              loading="lazy"
              decoding="async"
              referrerpolicy="no-referrer"
              class="h-20 w-full object-cover"
              onerror={(e) => ((e.currentTarget as HTMLImageElement).style.display = "none")}
            />
            <div class="px-1.5 py-1 text-[10px] leading-tight text-text-secondary truncate">
              {host(src.url)}
            </div>
          </button>
        {/each}
      </div>
    {/if}

    {#if web?.length}
      <div>
        <div class="mb-1 font-mono text-[10px] uppercase tracking-wider text-text-muted">
          Fuentes web
        </div>
        <div class="flex flex-wrap gap-1.5">
          {#each web as src, i (src.url ?? i)}
            <a
              href={src.url}
              target="_blank"
              rel="noopener noreferrer"
              title={src.snippet || src.title}
              class="inline-flex items-center gap-1.5 rounded-md border border-bg-elevated bg-bg-card px-2 py-1 text-[11px] text-text-secondary transition-colors hover:border-accent-blue hover:text-accent-blue"
            >
              <span class="font-mono text-[10px] text-text-muted">{i + 1}</span>
              <span class="max-w-[180px] truncate font-medium">{src.title || host(src.url)}</span>
              <span class="text-[10px] text-text-muted">↗</span>
            </a>
          {/each}
        </div>
      </div>
    {/if}

    {#if rag?.length}
      <div>
        <div class="mb-1 font-mono text-[10px] uppercase tracking-wider text-text-muted">
          Fuentes internas (RAG)
        </div>
        <div class="flex flex-wrap gap-1.5">
          {#each rag as src, i (src.id ?? i)}
            <span
              title={src.snippet}
              class="inline-flex items-center gap-1.5 rounded-md border border-bg-elevated bg-bg-card px-2 py-1 font-mono text-[11px] text-text-secondary"
            >
              <span class="text-[10px] text-text-muted">INT-{i + 1}</span>
              <span class="max-w-[160px] truncate">{src.filename ?? src.id ?? "interno"}</span>
              {#if typeof src.score === "number"}
                <span class="text-[10px] text-text-muted">{src.score.toFixed(2)}</span>
              {/if}
            </span>
          {/each}
        </div>
      </div>
    {/if}
  </div>
{/if}
