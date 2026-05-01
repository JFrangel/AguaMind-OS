<script lang="ts">
  import { createQuery } from "@tanstack/svelte-query";
  import { fetchHealth } from "$lib/api";

  const query = createQuery({
    queryKey: ["health"],
    queryFn: () => fetchHealth(),
    refetchInterval: 15_000,
    retry: 1,
  });

  const status = $derived($query.data?.status ?? null);
  const providers = $derived($query.data?.providers ?? {});

  const STATUS_STYLES: Record<string, string> = {
    ok: "border-status-green/40 bg-status-green/10 text-status-green",
    degraded: "border-status-yellow/40 bg-status-yellow/10 text-status-yellow",
    down: "border-status-red/40 bg-status-red/10 text-status-red",
  };

  const DOT_STYLES: Record<string, string> = {
    ok: "bg-status-green",
    degraded: "bg-status-yellow",
    down: "bg-status-red",
  };
</script>

<div class="flex items-center gap-3">
  {#if $query.isError}
    <span class="rounded-full border border-status-red/40 bg-status-red/10 px-3 py-1 text-xs font-medium text-status-red">
      Backend offline
    </span>
  {:else if status}
    <div class="flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium {STATUS_STYLES[status] ?? STATUS_STYLES.degraded}">
      <span class="inline-block h-1.5 w-1.5 rounded-full {DOT_STYLES[status] ?? DOT_STYLES.degraded}"></span>
      {status}
    </div>
    <div class="hidden md:flex items-center gap-1">
      {#each Object.entries(providers) as [name, info]}
        <span
          title="{name}: {info.available ? 'available' : 'down'} (failures: {info.failures})"
          class="font-mono text-[10px] {info.available ? 'text-status-green' : 'text-text-muted'}"
        >
          {name}
        </span>
      {/each}
    </div>
  {:else}
    <span class="rounded-full border border-bg-elevated bg-bg-card px-3 py-1 text-xs text-text-muted">
      cargando…
    </span>
  {/if}
</div>
