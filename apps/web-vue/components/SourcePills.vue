<script setup lang="ts">
import type { RagSourceItem, WebSourceItem } from "~/types";

const props = defineProps<{
  web?: WebSourceItem[];
  rag?: RagSourceItem[];
}>();

function host(url: string | undefined): string {
  if (!url) return "";
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

const webWithImage = computed(() => (props.web ?? []).filter((s) => s.image));
</script>

<template>
  <div
    v-if="(web && web.length) || (rag && rag.length)"
    class="mt-3 flex flex-col gap-3 border-t border-bg-elevated pt-3"
  >
    <div v-if="webWithImage.length > 0" class="flex flex-wrap gap-2">
      <a
        v-for="(src, i) in webWithImage"
        :key="(src.url ?? '') + i"
        :href="src.url"
        target="_blank"
        rel="noopener noreferrer"
        :title="src.title || src.url"
        class="group block w-32 overflow-hidden rounded-md border border-bg-elevated bg-bg-card transition-colors hover:border-accent-blue"
      >
        <img
          :src="src.image ?? ''"
          :alt="src.title || ''"
          loading="lazy"
          decoding="async"
          referrerpolicy="no-referrer"
          class="h-20 w-full object-cover"
          @error="(e: Event) => ((e.target as HTMLImageElement).style.display = 'none')"
        />
        <div class="truncate px-1.5 py-1 text-[10px] leading-tight text-text-secondary">
          {{ host(src.url) }}
        </div>
      </a>
    </div>

    <div v-if="web && web.length">
      <div class="mb-1 font-mono text-[10px] uppercase tracking-wider text-text-muted">
        Fuentes web
      </div>
      <div class="flex flex-wrap gap-1.5">
        <a
          v-for="(src, i) in web"
          :key="src.url ?? i"
          :href="src.url"
          target="_blank"
          rel="noopener noreferrer"
          :title="src.snippet || src.title"
          class="inline-flex items-center gap-1.5 rounded-md border border-bg-elevated bg-bg-card px-2 py-1 text-[11px] text-text-secondary transition-colors hover:border-accent-blue hover:text-accent-blue"
        >
          <span class="font-mono text-[10px] text-text-muted">{{ i + 1 }}</span>
          <span class="max-w-[180px] truncate font-medium">
            {{ src.title || host(src.url) }}
          </span>
          <span class="text-[10px] text-text-muted">↗</span>
        </a>
      </div>
    </div>

    <div v-if="rag && rag.length">
      <div class="mb-1 font-mono text-[10px] uppercase tracking-wider text-text-muted">
        Fuentes internas (RAG)
      </div>
      <div class="flex flex-wrap gap-1.5">
        <span
          v-for="(src, i) in rag"
          :key="src.id ?? i"
          :title="src.snippet"
          class="inline-flex items-center gap-1.5 rounded-md border border-bg-elevated bg-bg-card px-2 py-1 font-mono text-[11px] text-text-secondary"
        >
          <span class="text-[10px] text-text-muted">INT-{{ i + 1 }}</span>
          <span class="max-w-[160px] truncate">{{ src.filename ?? src.id ?? "interno" }}</span>
          <span v-if="typeof src.score === 'number'" class="text-[10px] text-text-muted">
            {{ src.score.toFixed(2) }}
          </span>
        </span>
      </div>
    </div>
  </div>
</template>
