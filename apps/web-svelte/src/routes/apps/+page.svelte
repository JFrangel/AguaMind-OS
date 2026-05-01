<script lang="ts">
  import { listProfiles, type Profile } from "@agentos/profiles";

  const profiles: readonly Profile[] = listProfiles();
</script>

<svelte:head>
  <title>AgentOS · Apps</title>
</svelte:head>

<div class="min-h-full">
  <header class="border-b border-bg-elevated bg-bg-secondary/60 px-6 py-3 backdrop-blur">
    <div class="mx-auto flex max-w-6xl items-center justify-between">
      <a href="/" class="flex items-center gap-3 no-underline">
        <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-blue font-display text-sm font-bold text-white">A</div>
        <div>
          <h1 class="font-display text-sm font-semibold text-text-primary">AgentOS</h1>
          <p class="text-[11px] text-text-secondary">Catálogo de apps</p>
        </div>
      </a>
      <nav class="flex items-center gap-3 text-xs text-text-secondary">
        <a href="/" class="hover:text-accent-blue">Chat</a>
        <a href="/previewagentos" class="hover:text-accent-blue">Preview</a>
      </nav>
    </div>
  </header>

  <main class="mx-auto max-w-6xl px-6 py-12">
    <h2 class="font-display text-2xl font-semibold text-text-primary">Una instancia · varias problemáticas</h2>
    <p class="mt-2 max-w-2xl text-sm text-text-secondary">
      Cada tarjeta es un <strong>profile</strong>: AgentOS por dentro, con un system prompt, presets
      y branding específicos para una problemática. Para agregar uno nuevo, creá un archivo en
      <code class="rounded bg-bg-elevated px-1.5 py-0.5 font-mono text-[11px]">packages/profiles/profiles/&lt;slug&gt;.ts</code>
      y registralo en <code class="rounded bg-bg-elevated px-1.5 py-0.5 font-mono text-[11px]">catalog.ts</code>.
    </p>

    <div class="mt-8 grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
      {#each profiles as profile (profile.slug)}
        <a
          href={`/apps/${profile.slug}`}
          class="group block rounded-2xl border border-bg-elevated bg-bg-card p-5 no-underline transition-all hover:-translate-y-0.5 hover:border-accent-blue"
        >
          <div class="flex items-center gap-3">
            <div
              class="flex h-10 w-10 items-center justify-center rounded-xl font-display text-xl font-bold text-white"
              style:background={profile.accentOverride ?? "var(--color-accent-blue)"}
            >
              {profile.emoji ?? "·"}
            </div>
            <div>
              <div class="font-display text-base font-semibold text-text-primary">{profile.name}</div>
              <div class="font-mono text-[10px] uppercase tracking-wider text-text-muted">/apps/{profile.slug}</div>
            </div>
          </div>
          <p class="mt-3 text-sm font-medium text-text-secondary">{profile.tagline}</p>
          <p class="mt-2 text-xs text-text-muted leading-relaxed">{profile.description}</p>
          <div class="mt-4 flex flex-wrap gap-1">
            {#each profile.presets.slice(0, 2) as preset}
              <span class="rounded-md border border-bg-elevated bg-bg-secondary px-2 py-0.5 font-mono text-[10px] text-text-muted">
                {preset.icon ?? "·"} {preset.label}
              </span>
            {/each}
            {#if profile.presets.length > 2}
              <span class="font-mono text-[10px] text-text-muted">+{profile.presets.length - 2}</span>
            {/if}
          </div>
        </a>
      {/each}
    </div>
  </main>
</div>
