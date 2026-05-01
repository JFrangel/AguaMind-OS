<script setup lang="ts">
import { bindTableToolbars, renderMarkdown } from "@agentos/ui/markdown";

import type { ChatMessage } from "~/types";

const props = defineProps<{ message: ChatMessage }>();
const isUser = computed(() => props.message.role === "user");
const html = ref("");
const mdRoot = ref<HTMLElement | null>(null);

watch(
  [() => props.message.content, isUser],
  async ([content, asUser]) => {
    if (asUser || !content) {
      html.value = "";
      return;
    }
    html.value = await renderMarkdown(content as string);
  },
  { immediate: true },
);

// Wire CSV toolbar buttons after each re-render.
watch(html, () => {
  nextTick(() => bindTableToolbars(mdRoot.value));
});
</script>

<template>
  <div :class="['flex', isUser ? 'justify-end' : 'justify-start']">
    <div
      :class="[
        'max-w-[85%] rounded-xl px-4 py-2.5 text-sm leading-relaxed',
        isUser
          ? 'bg-accent-blue text-white'
          : 'assistant-bubble border border-bg-elevated bg-bg-card text-text-primary',
      ]"
    >
      <div v-if="message.attachments?.length" class="mb-2 flex flex-wrap gap-1">
        <span
          v-for="att in message.attachments"
          :key="att.filename"
          class="rounded-md bg-bg-elevated px-2 py-0.5 font-mono text-[10px] text-text-secondary"
        >
          {{ att.filename }}
        </span>
      </div>

      <template v-if="isUser">
        <p v-if="message.content" class="whitespace-pre-wrap">{{ message.content }}</p>
      </template>
      <template v-else-if="message.content">
        <div v-if="html" ref="mdRoot" v-html="html" />
        <p v-else class="whitespace-pre-wrap">{{ message.content }}</p>
        <SourcePills :web="message.webSources" :rag="message.ragSources" />
      </template>
      <span v-else class="inline-flex items-center gap-1 text-text-muted">
        <span class="thinking-dot inline-block h-1.5 w-1.5 rounded-full bg-text-muted" />
        <span class="thinking-dot inline-block h-1.5 w-1.5 rounded-full bg-text-muted" />
        <span class="thinking-dot inline-block h-1.5 w-1.5 rounded-full bg-text-muted" />
      </span>
    </div>
  </div>
</template>
