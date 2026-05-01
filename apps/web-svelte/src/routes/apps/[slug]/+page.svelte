<script lang="ts">
  import { onMount } from "svelte";

  import { profileChat } from "$lib/stores/profileChat.svelte";
  import ChatComposerProfile from "$lib/components/ChatComposerProfile.svelte";
  import MessageBubble from "$lib/components/MessageBubble.svelte";
  import AgentTrace from "$lib/components/AgentTrace.svelte";
  import HealthBadge from "$lib/components/HealthBadge.svelte";
  import LanguageSelect from "$lib/components/LanguageSelect.svelte";
  import ThemeSwitch from "$lib/components/ThemeSwitch.svelte";
  import type { Language } from "$lib/types";

  let { data } = $props();
  const profile = $derived(data.profile);

  let scrollEl: HTMLDivElement | undefined = $state();

  // Wire the profile into the chat store on mount and whenever the slug
  // changes (SvelteKit re-uses the layout, so navigating /apps/medico → /apps/legal
  // hits this same component).
  $effect(() => {
    profileChat.configure(profile);
  });

  $effect(() => {
    profileChat.messages;
    profileChat.streaming;
    queueMicrotask(() => scrollEl?.scrollTo({ top: scrollEl.scrollHeight, behavior: "smooth" }));
  });

  const lastAssistant = $derived(
    [...profileChat.messages].reverse().find((m) => m.role === "assistant"),
  );

  function setLanguage(lang: Language): void {
    profileChat.language = lang;
  }
</script>

<svelte:head>
  <title>{profile.name} · AgentOS</title>
</svelte:head>

<!-- Per-profile accent override: scoped to this route so the rest of the
     app keeps the global theme accent. -->
{#if profile.accentOverride}
  <style>
    :root[data-app-profile="{profile.slug}"] {
      --color-accent-blue: {profile.accentOverride};
      --color-accent-blue-hover: {profile.accentOverride};
    }
  </style>
{/if}

<svelte:document />

<div
  data-app-profile={profile.slug}
  style:--color-accent-blue={profile.accentOverride ?? null}
  class="flex h-full flex-col"
>
  <header class="border-b border-bg-elevated bg-bg-secondary/60 px-6 py-3 backdrop-blur">
    <div class="mx-auto flex max-w-6xl items-center justify-between">
      <div class="flex items-center gap-3">
        <a href="/apps" class="flex items-center gap-2 text-text-muted hover:text-accent-blue">
          <span class="text-lg">←</span>
          <span class="font-mono text-[10px] uppercase tracking-wider">Apps</span>
        </a>
        <div
          class="flex h-9 w-9 items-center justify-center rounded-xl font-display text-base font-bold text-white"
          style:background={profile.accentOverride ?? "var(--color-accent-blue)"}
        >
          {profile.emoji ?? "·"}
        </div>
        <div>
          <h1 class="font-display text-sm font-semibold text-text-primary">{profile.name}</h1>
          <p class="text-[11px] text-text-secondary">{profile.tagline}</p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <ThemeSwitch />
        <LanguageSelect value={profileChat.language} onChange={setLanguage} />
        <HealthBadge />
      </div>
    </div>
  </header>

  <div class="flex flex-1 overflow-hidden">
    <main class="flex flex-1 flex-col">
      <div bind:this={scrollEl} class="scrollbar-thin flex-1 overflow-y-auto px-6 py-6">
        <div class="mx-auto flex max-w-3xl flex-col gap-3">
          {#if profileChat.messages.length === 0}
            <div class="rounded-2xl border border-bg-elevated bg-bg-card px-8 py-10">
              <div class="flex items-start gap-4">
                <div
                  class="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-xl font-display text-2xl font-bold text-white"
                  style:background={profile.accentOverride ?? "var(--color-accent-blue)"}
                >
                  {profile.emoji ?? "·"}
                </div>
                <div>
                  <h2 class="font-display text-xl font-semibold text-text-primary">{profile.name}</h2>
                  <p class="mt-1 text-sm text-text-secondary">{profile.description}</p>
                </div>
              </div>

              {#if profile.warning}
                <div class="mt-4 rounded-md border border-status-yellow/40 bg-status-yellow/10 px-3 py-2 text-xs text-status-yellow">
                  ⚠ {profile.warning}
                </div>
              {/if}

              {#if profile.suggestedFiles?.length}
                <div class="mt-4">
                  <div class="mb-1 font-mono text-[10px] uppercase tracking-wider text-text-muted">
                    Archivos sugeridos para subir al RAG (📎)
                  </div>
                  <div class="flex flex-wrap gap-1.5">
                    {#each profile.suggestedFiles as f}
                      <span class="rounded-md border border-bg-elevated bg-bg-secondary px-2 py-0.5 font-mono text-[11px] text-text-secondary">
                        {f}
                      </span>
                    {/each}
                  </div>
                </div>
              {/if}

              <div class="mt-6 grid grid-cols-1 gap-2 sm:grid-cols-2">
                {#each profile.presets as preset}
                  <button
                    type="button"
                    class="rounded-lg border border-bg-elevated bg-bg-secondary px-4 py-3 text-left text-sm text-text-primary transition-colors hover:border-accent-blue"
                    onclick={() => profileChat.send(preset.task)}
                  >
                    <span class="mr-2 text-base">{preset.icon ?? "·"}</span>
                    {preset.label}
                  </button>
                {/each}
              </div>
            </div>
          {:else}
            {#each profileChat.messages as msg (msg.id)}
              <MessageBubble message={msg} />
            {/each}
          {/if}

          {#if profileChat.error}
            <div class="rounded-lg border border-status-red/40 bg-status-red/10 px-4 py-3 text-sm text-status-red">
              {profileChat.error}
            </div>
          {/if}
        </div>
      </div>

      <div class="border-t border-bg-elevated bg-bg-secondary/60 px-6 py-4 backdrop-blur">
        <div class="mx-auto max-w-3xl">
          <ChatComposerProfile placeholder={profile.placeholder} />
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
          disabled={!profileChat.lastQuery || profileChat.streaming}
          onclick={() => profileChat.rerun()}
          title="Volver a ejecutar la última pregunta"
        >
          ↻
        </button>
      </div>
      <div class="scrollbar-thin flex-1 overflow-y-auto px-5 py-4">
        <AgentTrace
          trace={lastAssistant?.agentTrace ?? []}
          streaming={profileChat.streaming}
          currentNode={profileChat.currentNode}
          currentAgent={profileChat.currentAgent}
        />
      </div>
    </aside>
  </div>
</div>
