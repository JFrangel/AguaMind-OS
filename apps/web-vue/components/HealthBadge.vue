<script setup lang="ts">
import { useQuery } from "@tanstack/vue-query";

import type { HealthResponse } from "~/types";

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

const FALLBACK_STATUS = STATUS_STYLES.degraded;
const FALLBACK_DOT = DOT_STYLES.degraded;

const { data, isError } = useQuery<HealthResponse>({
  queryKey: ["health"],
  queryFn: async () => {
    const res = await fetch("/api/health");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },
  refetchInterval: 15_000,
  retry: 1,
});
</script>

<template>
  <span
    v-if="isError"
    class="rounded-full border border-status-red/40 bg-status-red/10 px-3 py-1 text-xs font-medium text-status-red"
  >
    Backend offline
  </span>
  <span
    v-else-if="!data"
    class="rounded-full border border-bg-elevated bg-bg-card px-3 py-1 text-xs text-text-muted"
  >
    cargando…
  </span>
  <div v-else class="flex items-center gap-3">
    <div
      :class="[
        'flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium',
        STATUS_STYLES[data.status] ?? FALLBACK_STATUS,
      ]"
    >
      <span
        :class="[
          'inline-block h-1.5 w-1.5 rounded-full',
          DOT_STYLES[data.status] ?? FALLBACK_DOT,
        ]"
      />
      {{ data.status }}
    </div>
    <div class="hidden items-center gap-1 md:flex">
      <span
        v-for="[name, info] in Object.entries(data.providers)"
        :key="name"
        :title="`${name}: ${info.available ? 'available' : 'down'} (failures: ${info.failures})`"
        :class="[
          'font-mono text-[10px]',
          info.available ? 'text-status-green' : 'text-text-muted',
        ]"
      >
        {{ name }}
      </span>
    </div>
  </div>
</template>
