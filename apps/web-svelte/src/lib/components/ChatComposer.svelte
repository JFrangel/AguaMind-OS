<script lang="ts">
  import { chat } from "$lib/stores/chat.svelte";

  let value = $state("");
  let mode = $state<"chat" | "analysis" | "research">("chat");
  let textarea: HTMLTextAreaElement | undefined = $state();
  let fileInput: HTMLInputElement | undefined = $state();
  let uploading = $state(false);

  async function submit(): Promise<void> {
    const text = value.trim();
    if (!text || chat.streaming) return;
    value = "";
    autosize();
    await chat.send(text, { contextType: mode });
  }

  function onKeydown(e: KeyboardEvent): void {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  function autosize(): void {
    if (!textarea) return;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 160)}px`;
  }

  async function onFile(e: Event): Promise<void> {
    const target = e.currentTarget as HTMLInputElement;
    const file = target.files?.[0];
    if (!file) return;
    uploading = true;
    try {
      await chat.ingestFile(file);
    } finally {
      uploading = false;
      target.value = "";
    }
  }
</script>

<div class="flex flex-col gap-2">
  <div class="flex items-center gap-2 px-1">
    <button
      type="button"
      class="rounded-md border border-bg-elevated px-2 py-1 text-[11px] font-medium transition-colors {chat.useRag ? 'border-accent-blue bg-accent-blue/10 text-accent-blue' : 'text-text-secondary hover:border-accent-blue hover:text-accent-blue'}"
      onclick={() => (chat.useRag = !chat.useRag)}
    >
      RAG
    </button>
    <button
      type="button"
      class="rounded-md border border-bg-elevated px-2 py-1 text-[11px] font-medium transition-colors {chat.useWeb ? 'border-accent-blue bg-accent-blue/10 text-accent-blue' : 'text-text-secondary hover:border-accent-blue hover:text-accent-blue'}"
      onclick={() => (chat.useWeb = !chat.useWeb)}
    >
      Web
    </button>
    <span class="text-[11px] text-text-muted">
      {chat.useRag || chat.useWeb ? "El agente investigará antes de responder" : "Respuesta directa"}
    </span>
  </div>

  <div
    class="flex items-end gap-2 rounded-2xl border border-bg-elevated bg-bg-card px-3 py-2 transition-colors focus-within:border-accent-blue"
  >
    <select
      class="rounded-lg bg-transparent px-2 py-2 text-xs font-medium text-text-secondary hover:bg-bg-elevated focus:outline-none"
      bind:value={mode}
      disabled={chat.streaming}
      aria-label="Modo"
    >
      <option value="chat">Chat</option>
      <option value="analysis">Análisis</option>
      <option value="research">Investigación</option>
    </select>

    <button
      type="button"
      class="rounded-lg border border-bg-elevated px-2 py-1.5 text-xs text-text-secondary transition-colors hover:border-accent-blue hover:text-accent-blue disabled:opacity-40"
      onclick={() => fileInput?.click()}
      disabled={chat.streaming || uploading}
      title="Adjuntar archivo (PDF, DOCX, CSV, XLSX, JSON, MD, HTML, TXT)"
    >
      {uploading ? "…" : "📎"}
    </button>
    <input
      bind:this={fileInput}
      type="file"
      class="hidden"
      accept=".pdf,.docx,.csv,.xlsx,.json,.md,.html,.txt,.tsv,.xml,.parquet"
      onchange={onFile}
    />

    <textarea
      bind:this={textarea}
      bind:value
      oninput={autosize}
      onkeydown={onKeydown}
      placeholder="Escribe tu pregunta…"
      rows="1"
      class="flex-1 resize-none bg-transparent px-2 py-2 text-sm text-text-primary placeholder:text-text-muted focus:outline-none"
      disabled={chat.streaming}
    ></textarea>

    <button
      type="button"
      onclick={submit}
      disabled={!value.trim() || chat.streaming}
      class="rounded-xl bg-accent-blue px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-accent-blue-hover disabled:cursor-not-allowed disabled:bg-bg-elevated disabled:text-text-muted"
    >
      {chat.streaming ? "…" : "Enviar"}
    </button>
  </div>
</div>
