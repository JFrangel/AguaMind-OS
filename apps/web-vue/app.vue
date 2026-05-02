<script setup lang="ts">
import { useChatStore } from "~/stores/chat";

useHead({
  htmlAttrs: { lang: "es" },
  link: [
    { rel: "preconnect", href: "https://fonts.googleapis.com" },
    { rel: "preconnect", href: "https://fonts.gstatic.com", crossorigin: "" },
    {
      rel: "stylesheet",
      href: "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&family=JetBrains+Mono:wght@400;500&display=swap",
    },
  ],
});

const chat = useChatStore();
const scrollEl = ref<HTMLElement | null>(null);

const PRESETS = [
  { label: "Analizar tendencia de ventas", task: "Analiza una tendencia de ventas trimestral con estacionalidad" },
  { label: "Investigar un tema", task: "¿Cuáles son los avances recientes en bases de datos vectoriales?" },
  { label: "Escribir un resumen", task: "Resume la diferencia entre LangGraph y CrewAI" },
  { label: "Detectar anomalías", task: "Esquematiza un workflow para detectar anomalías en series temporales" },
];

const lastAssistant = computed(() =>
  [...chat.messages].reverse().find((m) => m.role === "assistant"),
);

const canExport = computed(() => Boolean(lastAssistant.value?.content) && !chat.streaming);

watch(
  () => [chat.messages.length, chat.streaming, lastAssistant.value?.content] as const,
  () => {
    nextTick(() => {
      if (scrollEl.value) {
        scrollEl.value.scrollTo({ top: scrollEl.value.scrollHeight, behavior: "smooth" });
      }
    });
  },
);
</script>

<template>
  <div class="flex h-full flex-col">
    <header class="border-b border-bg-elevated bg-bg-secondary/60 px-6 py-3 backdrop-blur">
      <div class="mx-auto flex max-w-6xl items-center justify-between">
        <div class="flex items-center gap-3">
          <div
            class="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-blue font-display text-sm font-bold text-white"
          >
            A
          </div>
          <div>
            <h1 class="font-display text-sm font-semibold text-text-primary">AgentOS</h1>
            <p class="text-[11px] text-text-secondary">Multi-agente · streaming</p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <ChannelsBadge />
          <ThemeSwitch />
          <LanguageSelect />
          <HealthBadge />
        </div>
      </div>
    </header>

    <div class="flex flex-1 overflow-hidden">
      <main class="flex flex-1 flex-col">
        <div ref="scrollEl" class="flex-1 overflow-y-auto px-6 py-6">
          <div class="mx-auto flex max-w-3xl flex-col gap-3">
            <div
              v-if="chat.messages.length === 0"
              class="rounded-2xl border border-bg-elevated bg-bg-card px-8 py-12 text-center"
            >
              <h2 class="font-display text-lg font-semibold text-text-primary">
                Empieza una conversación
              </h2>
              <p class="mt-2 text-sm text-text-secondary">
                Pregunta algo. El agente muestra su razonamiento mientras responde.
              </p>
              <div class="mt-6 grid grid-cols-1 gap-2 sm:grid-cols-2">
                <button
                  v-for="preset in PRESETS"
                  :key="preset.label"
                  type="button"
                  class="rounded-lg border border-bg-elevated bg-bg-secondary px-4 py-3 text-left text-sm text-text-primary transition-colors hover:border-accent-blue"
                  @click="chat.send(preset.task)"
                >
                  {{ preset.label }}
                </button>
              </div>
            </div>
            <MessageBubble v-for="msg in chat.messages" :key="msg.id" :message="msg" />

            <div
              v-if="chat.error"
              class="rounded-lg border border-status-red/40 bg-status-red/10 px-4 py-3 text-sm text-status-red"
            >
              {{ chat.error }}
            </div>
          </div>
        </div>

        <div class="px-6 pb-4 pt-2">
          <div class="mx-auto max-w-3xl">
            <ChatComposer />
          </div>
        </div>
      </main>

      <aside class="hidden w-72 border-l border-bg-elevated bg-bg-secondary/40 lg:flex lg:flex-col">
        <div class="flex items-center justify-between border-b border-bg-elevated px-5 py-3">
          <div>
            <h2 class="font-display text-xs font-semibold text-text-primary">Razonamiento</h2>
            <p class="text-[11px] text-text-secondary">Pasos en vivo</p>
          </div>
          <button
            type="button"
            :disabled="!chat.lastQuery || chat.streaming"
            class="rounded-md border border-bg-elevated px-2 py-1 text-[11px] font-medium text-text-secondary transition-colors hover:border-accent-blue hover:text-accent-blue disabled:opacity-40"
            title="Volver a ejecutar la última pregunta con los toggles actuales"
            @click="chat.rerun()"
          >
            ↻
          </button>
        </div>
        <div class="flex-1 overflow-y-auto px-5 py-4">
          <AgentTrace
            :trace="lastAssistant?.agentTrace ?? []"
            :streaming="chat.streaming"
            :current-node="chat.currentNode"
            :current-agent="chat.currentAgent"
          />
        </div>
      </aside>
    </div>
  </div>
</template>
