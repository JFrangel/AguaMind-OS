<script setup lang="ts">
import { useChatStore } from "~/stores/chat";

type Mode = "chat" | "analysis" | "research";

const chat = useChatStore();
const value = ref("");
const mode = ref<Mode>("chat");
const uploading = ref(false);
const textarea = ref<HTMLTextAreaElement | null>(null);
const fileInput = ref<HTMLInputElement | null>(null);

const ACCEPT = ".pdf,.docx,.csv,.xlsx,.json,.md,.html,.txt,.tsv,.xml,.parquet";

async function submit() {
  const text = value.value.trim();
  if (!text || chat.streaming) return;
  value.value = "";
  autosize();
  await chat.send(text, { contextType: mode.value });
}

function autosize() {
  const el = textarea.value;
  if (!el) return;
  el.style.height = "auto";
  el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    submit();
  }
}

async function onFile(e: Event) {
  const target = e.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;
  uploading.value = true;
  try {
    await chat.ingestFile(file);
  } finally {
    uploading.value = false;
    target.value = "";
  }
}
</script>

<template>
  <div class="flex flex-col gap-2">
    <div class="flex items-center gap-2 px-1">
      <button
        type="button"
        :class="[
          'rounded-md border px-2 py-1 text-[11px] font-medium transition-colors',
          chat.useRag
            ? 'border-accent-blue bg-accent-blue/10 text-accent-blue'
            : 'border-bg-elevated text-text-secondary hover:border-accent-blue hover:text-accent-blue',
        ]"
        @click="chat.useRag = !chat.useRag"
      >
        RAG
      </button>
      <button
        type="button"
        :class="[
          'rounded-md border px-2 py-1 text-[11px] font-medium transition-colors',
          chat.useWeb
            ? 'border-accent-blue bg-accent-blue/10 text-accent-blue'
            : 'border-bg-elevated text-text-secondary hover:border-accent-blue hover:text-accent-blue',
        ]"
        @click="chat.useWeb = !chat.useWeb"
      >
        Web
      </button>
      <span class="text-[11px] text-text-muted">
        {{ chat.useRag || chat.useWeb ? "El agente investigará antes de responder" : "Respuesta directa" }}
      </span>
    </div>

    <div
      class="flex items-end gap-2 rounded-2xl border border-bg-elevated bg-bg-card px-3 py-2 transition-colors focus-within:border-accent-blue"
    >
      <select
        v-model="mode"
        :disabled="chat.streaming"
        aria-label="Modo"
        class="rounded-lg bg-transparent px-2 py-2 text-xs font-medium text-text-secondary hover:bg-bg-elevated focus:outline-none"
      >
        <option value="chat">Chat</option>
        <option value="analysis">Análisis</option>
        <option value="research">Investigación</option>
      </select>

      <button
        type="button"
        :disabled="chat.streaming || uploading"
        class="rounded-lg border border-bg-elevated px-2 py-1.5 text-xs text-text-secondary transition-colors hover:border-accent-blue hover:text-accent-blue disabled:opacity-40"
        title="Adjuntar archivo (PDF, DOCX, CSV, XLSX, JSON, MD, HTML, TXT)"
        @click="fileInput?.click()"
      >
        {{ uploading ? "…" : "📎" }}
      </button>
      <input
        ref="fileInput"
        type="file"
        class="hidden"
        :accept="ACCEPT"
        @change="onFile"
      />

      <textarea
        ref="textarea"
        v-model="value"
        placeholder="Escribe tu pregunta…"
        rows="1"
        :disabled="chat.streaming"
        class="flex-1 resize-none bg-transparent px-2 py-2 text-sm text-text-primary placeholder:text-text-muted focus:outline-none"
        @input="autosize"
        @keydown="onKeydown"
      />

      <button
        type="button"
        :disabled="!value.trim() || chat.streaming"
        class="rounded-xl bg-accent-blue px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-accent-blue-hover disabled:cursor-not-allowed disabled:bg-bg-elevated disabled:text-text-muted"
        @click="submit"
      >
        {{ chat.streaming ? "…" : "Enviar" }}
      </button>
    </div>
  </div>
</template>
