"use client";

import { useQuery } from "@tanstack/react-query";

import type { HealthResponse } from "@/lib/types";

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

export function HealthBadge() {
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

  if (isError) {
    return (
      <span className="rounded-full border border-status-red/40 bg-status-red/10 px-3 py-1 text-xs font-medium text-status-red">
        Backend offline
      </span>
    );
  }
  if (!data) {
    return (
      <span className="rounded-full border border-bg-elevated bg-bg-card px-3 py-1 text-xs text-text-muted">
        cargando…
      </span>
    );
  }
  return (
    <div className="flex items-center gap-3">
      <div
        className={`flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium ${
          STATUS_STYLES[data.status] ?? STATUS_STYLES.degraded
        }`}
      >
        <span
          className={`inline-block h-1.5 w-1.5 rounded-full ${DOT_STYLES[data.status] ?? DOT_STYLES.degraded}`}
        />
        {data.status}
      </div>
      <div className="hidden items-center gap-1 md:flex">
        {Object.entries(data.providers).map(([name, info]) => (
          <span
            key={name}
            title={`${name}: ${info.available ? "available" : "down"} (failures: ${info.failures})`}
            className={`font-mono text-[10px] ${info.available ? "text-status-green" : "text-text-muted"}`}
          >
            {name}
          </span>
        ))}
      </div>
    </div>
  );
}
