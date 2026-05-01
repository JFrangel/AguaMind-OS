<script setup lang="ts">
import { useQuery } from "@tanstack/vue-query";

interface ChannelsResponse {
  data: { configured: string[]; all: string[] };
}

const { data } = useQuery<ChannelsResponse>({
  queryKey: ["channels"],
  queryFn: async () => {
    const res = await fetch("/api/channels");
    return res.json();
  },
  staleTime: 60_000,
});

const configured = computed(() => data.value?.data.configured ?? []);
</script>

<template>
  <span
    v-if="configured.length > 0"
    class="hidden items-center gap-1 rounded-full border border-bg-elevated bg-bg-card px-2 py-0.5 font-mono text-[10px] text-text-secondary md:inline-flex"
    title="Canales de notificación configurados"
  >
    🔔 {{ configured.join(" · ") }}
  </span>
</template>
