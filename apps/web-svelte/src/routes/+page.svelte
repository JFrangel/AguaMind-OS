<script lang="ts">
  import { chat } from "$lib/stores/chat.svelte";
  import ChatComposer from "$lib/components/ChatComposer.svelte";
  import MessageBubble from "$lib/components/MessageBubble.svelte";
  import AgentTrace from "$lib/components/AgentTrace.svelte";
  import HealthBadge from "$lib/components/HealthBadge.svelte";
  import ChannelsBadge from "$lib/components/ChannelsBadge.svelte";
  import LanguageSelect from "$lib/components/LanguageSelect.svelte";
  import ThemeSwitch from "$lib/components/ThemeSwitch.svelte";
  import type { Language } from "$lib/types";

  let scrollEl: HTMLDivElement | undefined = $state();

  $effect(() => {
    chat.messages;
    chat.streaming;
    queueMicrotask(() => scrollEl?.scrollTo({ top: scrollEl.scrollHeight, behavior: "smooth" }));
  });

  const lastAssistant = $derived(
    [...chat.messages].reverse().find((m) => m.role === "assistant"),
  );

  const PRESETS = [
    { label: "Analizar tendencia de ventas", task: "Analiza una tendencia de ventas trimestral con estacionalidad" },
    { label: "Investigar un tema", task: "¿Cuáles son los avances recientes en bases de datos vectoriales?" },
    { label: "Escribir un resumen", task: "Resume la diferencia entre LangGraph y CrewAI" },
    { label: "Detectar anomalías", task: "Esquematiza un workflow para detectar anomalías en series temporales" },
  ];

  function setLanguage(lang: Language): void {
    chat.language = lang;
  }
</script>

<div class="flex h-full flex-col">
  <header class="border-b border-bg-elevated bg-bg-secondary/60 px-6 py-3 backdrop-blur">
    <div class="mx-auto flex max-w-6xl items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-blue font-display text-sm font-bold text-white">
          A
        </div>
        <div>
          <h1 class="font-display text-sm font-semibold text-text-primary">AgentOS</h1>
          <p class="text-[11px] text-text-secondary">Multi-agente · streaming</p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <a
          href="/apps"
          class="rounded-md border border-bg-elevated px-2 py-1 font-mono text-[11px] text-text-secondary transition-colors hover:border-accent-blue hover:text-accent-blue"
          title="Ver el catálogo de apps por problemática"
        >
          /apps
        </a>
        <ChannelsBadge />
        <ThemeSwitch />
        <LanguageSelect value={chat.language} onChange={setLanguage} />
        <HealthBadge />
      </div>
    </div>
  </header>

  <div class="flex flex-1 overflow-hidden">
    <main class="flex flex-1 flex-col">
      <div bind:this={scrollEl} class="scrollbar-thin flex-1 overflow-y-auto px-6 py-6">
        <div class="mx-auto flex max-w-3xl flex-col gap-3">
          {#if chat.messages.length === 0}
            <div class="rounded-2xl border border-bg-elevated bg-bg-card px-8 py-12 text-center">
              <h2 class="font-display text-lg font-semibold text-text-primary">Empieza una conversación</h2>
              <p class="mt-2 text-sm text-text-secondary">
                Pregunta algo. El agente muestra su razonamiento mientras responde.
              </p>
              <div class="mt-6 grid grid-cols-1 gap-2 sm:grid-cols-2">
                {#each PRESETS as preset}
                  <button
                    type="button"
                    class="rounded-lg border border-bg-elevated bg-bg-secondary px-4 py-3 text-left text-sm text-text-primary transition-colors hover:border-accent-blue"
                    onclick={() => chat.send(preset.task)}
                  >
                    {preset.label}
                  </button>
                {/each}
              </div>
            </div>
          {:else}
            {#each chat.messages as msg (msg.id)}
              <MessageBubble message={msg} />
            {/each}
          {/if}

          {#if chat.error}
            <div class="rounded-lg border border-status-red/40 bg-status-red/10 px-4 py-3 text-sm text-status-red">
              {chat.error}
            </div>
          {/if}
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
          class="rounded-md border border-bg-elevated px-2 py-1 text-[11px] font-medium text-text-secondary transition-colors hover:border-accent-blue hover:text-accent-blue disabled:opacity-40"
          disabled={!chat.lastQuery || chat.streaming}
          onclick={() => chat.rerun()}
          title="Volver a ejecutar la última pregunta con los toggles actuales"
        >
          ↻
        </button>
      </div>
      <div class="scrollbar-thin flex-1 overflow-y-auto px-5 py-4">
        <AgentTrace
          trace={lastAssistant?.agentTrace ?? []}
          streaming={chat.streaming}
          currentNode={chat.currentNode}
          currentAgent={chat.currentAgent}
        />
      </div>
    </aside>
  </div>
</div>
