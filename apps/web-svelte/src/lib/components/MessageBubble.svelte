<script lang="ts">
  import { renderMarkdown } from "@agentos/ui/markdown";
  import type { ChatMessage } from "$lib/types";

  let { message }: { message: ChatMessage } = $props();
  const isUser = $derived(message.role === "user");

  let html = $state("");
  $effect(() => {
    const text = message.content;
    if (!text || isUser) {
      html = "";
      return;
    }
    renderMarkdown(text).then((rendered) => {
      html = rendered;
    });
  });
</script>

<div class="flex {isUser ? 'justify-end' : 'justify-start'}">
  <div
    class="max-w-[85%] rounded-xl px-4 py-2.5 text-sm leading-relaxed
      {isUser
        ? 'bg-accent-blue text-white'
        : 'assistant-bubble border border-bg-elevated bg-bg-card text-text-primary'}"
  >
    {#if message.attachments?.length}
      <div class="mb-2 flex flex-wrap gap-1">
        {#each message.attachments as att}
          <span class="rounded-md bg-bg-elevated px-2 py-0.5 font-mono text-[10px] text-text-secondary">
            {att.filename}
          </span>
        {/each}
      </div>
    {/if}

    {#if isUser}
      {#if message.content}
        <p class="whitespace-pre-wrap">{message.content}</p>
      {/if}
    {:else if message.content}
      <!-- eslint-disable-next-line svelte/no-at-html-tags -->
      {@html html || `<p>${message.content.replace(/</g, "&lt;")}</p>`}
    {:else}
      <span class="inline-flex items-center gap-1 text-text-muted">
        <span class="thinking-dot inline-block h-1.5 w-1.5 rounded-full bg-text-muted"></span>
        <span class="thinking-dot inline-block h-1.5 w-1.5 rounded-full bg-text-muted"></span>
        <span class="thinking-dot inline-block h-1.5 w-1.5 rounded-full bg-text-muted"></span>
      </span>
    {/if}
  </div>
</div>
