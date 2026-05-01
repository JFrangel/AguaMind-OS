<script lang="ts">
  import { createQuery } from "@tanstack/svelte-query";

  interface ChannelsResponse {
    data: { configured: string[]; all: string[] };
  }

  const query = createQuery({
    queryKey: ["channels"],
    queryFn: async (): Promise<ChannelsResponse> => {
      const res = await fetch("/api/channels");
      return res.json();
    },
    staleTime: 60_000,
  });

  const configured = $derived($query.data?.data.configured ?? []);
</script>

{#if configured.length > 0}
  <span
    class="hidden items-center gap-1 rounded-full border border-bg-elevated bg-bg-card px-2 py-0.5 font-mono text-[10px] text-text-secondary md:inline-flex"
    title="Canales de notificación configurados"
  >
    🔔 {configured.join(" · ")}
  </span>
{/if}
