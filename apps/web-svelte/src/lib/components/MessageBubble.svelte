<script lang="ts">
  import { bindTableToolbars, renderMarkdown } from "@agentos/ui/markdown";
  import { lightbox } from "$lib/stores/lightbox.svelte";
  import type { ChatMessage } from "$lib/types";
  import SourcePills from "./SourcePills.svelte";

  let { message }: { message: ChatMessage } = $props();
  const isUser = $derived(message.role === "user");

  let html = $state("");
  let mdRoot: HTMLDivElement | undefined = $state();

  // Markdown re-rendering during streaming is the single biggest cost in
  // the chat: marked + DOMPurify + the post-process regex run on EVERY
  // token, and the cost is linear in the message length, so a 500-token
  // response is O(N²). We coalesce updates with requestAnimationFrame so
  // we render at most ~60Hz no matter how fast tokens arrive.
  //
  // Tracks: the last text we actually rendered, and the in-flight RAF id
  // so we can cancel a pending render when a newer one arrives.
  let pendingRaf = 0;
  let lastRendered = "";

  $effect(() => {
    const text = message.content;
    if (!text || isUser) {
      html = "";
      return;
    }
    if (text === lastRendered) return;

    if (pendingRaf) cancelAnimationFrame(pendingRaf);
    pendingRaf = requestAnimationFrame(() => {
      pendingRaf = 0;
      const snapshot = message.content;
      lastRendered = snapshot;
      renderMarkdown(snapshot).then((rendered) => {
        // Discard if a newer token arrived while we were parsing — no
        // point flashing stale HTML when a fresh render is queued.
        if (snapshot === lastRendered) html = rendered;
      });
    });

    // Cleanup if effect re-runs (component teardown / message swap).
    return () => {
      if (pendingRaf) {
        cancelAnimationFrame(pendingRaf);
        pendingRaf = 0;
      }
    };
  });

  // After every re-render: wire CSV toolbar + click-to-zoom on images.
  // Both are idempotent (data-bound flag) so streaming re-renders don't
  // duplicate listeners.
  $effect(() => {
    html;
    queueMicrotask(() => {
      bindTableToolbars(mdRoot ?? null);
      bindImageZoom();
    });
  });

  function bindImageZoom(): void {
    if (!mdRoot) return;
    mdRoot.querySelectorAll("img").forEach((img) => {
      if ((img as HTMLImageElement).dataset.zoomBound === "1") return;
      (img as HTMLImageElement).dataset.zoomBound = "1";
      img.style.cursor = "zoom-in";
      img.addEventListener("click", (e) => {
        e.preventDefault();
        const el = e.currentTarget as HTMLImageElement;
        lightbox.show({
          src: el.src,
          alt: el.alt,
          caption: el.alt || undefined,
        });
      });
    });
  }
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
      <div bind:this={mdRoot}>
        <!-- eslint-disable-next-line svelte/no-at-html-tags -->
        {@html html || `<p>${message.content.replace(/</g, "&lt;")}</p>`}
      </div>
      <SourcePills web={message.webSources} rag={message.ragSources} />
    {:else}
      <span class="inline-flex items-center gap-1 text-text-muted">
        <span class="thinking-dot inline-block h-1.5 w-1.5 rounded-full bg-text-muted"></span>
        <span class="thinking-dot inline-block h-1.5 w-1.5 rounded-full bg-text-muted"></span>
        <span class="thinking-dot inline-block h-1.5 w-1.5 rounded-full bg-text-muted"></span>
      </span>
    {/if}
  </div>
</div>
