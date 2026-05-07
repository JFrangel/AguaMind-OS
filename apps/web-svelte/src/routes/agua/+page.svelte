<script lang="ts">
  import { onMount, onDestroy } from "svelte";

  // ── Types ──────────────────────────────────────────────────────────────
  type KPIStatus = "ok" | "warning" | "critical";
  interface KPI { value: number; unit: string; target: string; formula: string; status: KPIStatus; }
  interface Reading {
    timestamp: string; inflow_l_min: number; total_demand_l_min: number;
    losses_l_min: number; tank_a_pct: number; tank_b_pct: number;
    zones: Record<string, number>; hour: number;
  }
  interface Alert { level: string; zone: string; message: string; action: string; }
  interface WaterData {
    reading: Reading;
    kpis: Record<string, KPI>;
    alerts: Alert[];
    projection: { projected_consumption_l: number; projected_losses_l: number; vs_baseline_pct: number; cost_benefit: { current_daily_loss_l: number; annual_water_savings_cop: number; roi_months: number; sensor_cost_cop: number; }; };
  }
  interface HistoryPoint { hour: string; date: string; consumption_l: number; losses_l: number; inflow_l_min: number; tank_a_pct: number; tank_b_pct: number; }

  // ── State ──────────────────────────────────────────────────────────────
  let data = $state<WaterData | null>(null);
  let history = $state<HistoryPoint[]>([]);
  let error = $state<string | null>(null);
  let loading = $state(true);
  let lastRefresh = $state<Date | null>(null);
  let activeScenario = $state<"normal" | "leak" | "peak_irrigation">("normal");
  let scenarioLoading = $state(false);
  let tab = $state<"dashboard" | "history" | "report">("dashboard");

  // ── Helpers ────────────────────────────────────────────────────────────
  function statusColor(s: KPIStatus) {
    return s === "ok" ? "#22c55e" : s === "warning" ? "#f59e0b" : "#ef4444";
  }
  function statusBg(s: KPIStatus) {
    return s === "ok" ? "rgba(34,197,94,.12)" : s === "warning" ? "rgba(245,158,11,.12)" : "rgba(239,68,68,.12)";
  }
  function statusEmoji(s: KPIStatus) {
    return s === "ok" ? "✅" : s === "warning" ? "⚠️" : "🚨";
  }
  function alertColor(l: string) {
    return l === "critical" ? "#ef4444" : l === "warning" ? "#f59e0b" : "#60a5fa";
  }
  function fmt(n: number, dec = 1) { return n.toFixed(dec); }
  function fmtK(n: number) {
    return n >= 1000 ? (n / 1000).toFixed(1) + "k" : n.toFixed(0);
  }

  const ZONE_COLORS: Record<string, string> = {
    "Baños Bloque A": "#60a5fa", "Baños Alameda": "#818cf8",
    "Cafetería": "#f97316", "Riego/Cancha": "#22c55e",
    "Laboratorios": "#a78bfa", "Limpieza": "#94a3b8",
  };

  // ── Data fetching ──────────────────────────────────────────────────────
  async function fetchData() {
    try {
      const [statusRes, histRes] = await Promise.all([
        fetch("/api/water?endpoint=status"),
        fetch("/api/water?endpoint=history&hours=24"),
      ]);
      const statusJson = await statusRes.json();
      const histJson = await histRes.json();
      if (statusJson.error) { error = statusJson.error; return; }
      // Map /water/status response to WaterData shape
      const s = statusJson.data;
      data = {
        reading: {
          timestamp: s.timestamp,
          inflow_l_min: s.inflow_l_min,
          total_demand_l_min: s.total_demand_l_min,
          losses_l_min: s.losses_l_min,
          tank_a_pct: s.tank_a_pct,
          tank_b_pct: s.tank_b_pct,
          zones: s.zones,
          hour: new Date(s.timestamp).getHours(),
        },
        kpis: s.kpis,
        alerts: s.alerts ?? [],
        projection: {
          projected_consumption_l: s.total_demand_l_min * 1440,
          projected_losses_l: s.losses_l_min * 1440,
          vs_baseline_pct: ((s.total_demand_l_min * 1440 - 45367) / 45367) * 100,
          cost_benefit: { current_daily_loss_l: s.losses_l_min * 1440, annual_water_savings_cop: s.losses_l_min * 1440 * 365 * 3.5, roi_months: 4500000 / Math.max(1, s.losses_l_min * 1440 * 365 * 3.5 / 12), sensor_cost_cop: 4500000 },
        },
      };
      if (!histJson.error && histJson.data) history = histJson.data;
      error = null;
      lastRefresh = new Date();
    } catch (e) {
      error = String(e);
    } finally {
      loading = false;
    }
  }

  async function runScenario(scenario: typeof activeScenario) {
    scenarioLoading = true;
    try {
      const res = await fetch("/api/water", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ scenario }) });
      const json = await res.json();
      if (json.data) {
        activeScenario = scenario;
        const d2 = json.data;
        data = {
          reading: d2.reading,
          kpis: d2.kpis,
          alerts: d2.alerts ?? [],
          projection: {
            projected_consumption_l: d2.reading.total_demand_l_min * 1440,
            projected_losses_l: d2.reading.losses_l_min * 1440,
            vs_baseline_pct: ((d2.reading.total_demand_l_min * 1440 - 45367) / 45367) * 100,
            cost_benefit: { current_daily_loss_l: d2.reading.losses_l_min * 1440, annual_water_savings_cop: d2.reading.losses_l_min * 1440 * 365 * 3.5, roi_months: 4500000 / Math.max(1, d2.reading.losses_l_min * 1440 * 365 * 3.5 / 12), sensor_cost_cop: 4500000 },
          },
        };
      }
    } finally {
      scenarioLoading = false;
    }
  }

  let interval: ReturnType<typeof setInterval>;
  onMount(() => { fetchData(); interval = setInterval(fetchData, 30000); });
  onDestroy(() => clearInterval(interval));
</script>

<!-- ── Layout ────────────────────────────────────────────────────────────── -->
<div class="min-h-screen bg-[#0f1117] text-white font-sans">

  <!-- Header -->
  <header class="border-b border-white/10 bg-[#0f1117]/80 backdrop-blur sticky top-0 z-20 px-6 py-3">
    <div class="mx-auto max-w-7xl flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-xl bg-blue-500 flex items-center justify-center text-lg font-bold">💧</div>
        <div>
          <h1 class="text-sm font-semibold text-white leading-none">AguaMind OS</h1>
          <p class="text-[11px] text-white/40 mt-0.5">UNIAJC Sede Sur — Gestión Hídrica Inteligente</p>
        </div>
      </div>
      <div class="flex items-center gap-4">
        {#if lastRefresh}
          <span class="text-[11px] text-white/30">Actualizado {lastRefresh.toLocaleTimeString("es-CO")}</span>
        {/if}
        <a href="/" class="text-[11px] text-blue-400 hover:text-blue-300 transition-colors">Chat IA →</a>
      </div>
    </div>
  </header>

  <main class="mx-auto max-w-7xl px-4 py-6 space-y-6">

    <!-- Scenario bar -->
    <div class="flex items-center gap-2 flex-wrap">
      <span class="text-xs text-white/40 mr-1">Escenario demo:</span>
      {#each [["normal","✅ Normal"],["leak","🚨 Fuga"],["peak_irrigation","🌿 Pico Riego"]] as [sc, label]}
        <button
          onclick={() => runScenario(sc as typeof activeScenario)}
          disabled={scenarioLoading}
          class="px-3 py-1 rounded-full text-xs font-medium transition-all border
            {activeScenario === sc
              ? 'bg-blue-500/20 border-blue-500/60 text-blue-300'
              : 'bg-white/5 border-white/10 text-white/50 hover:border-white/30'}"
        >{label}</button>
      {/each}
      {#if scenarioLoading}<span class="text-xs text-white/30 animate-pulse">Cargando…</span>{/if}
    </div>

    <!-- Tab navigation -->
    <div class="flex gap-1 border-b border-white/10">
      {#each [["dashboard","📊 Dashboard"],["history","📈 Historial"],["report","💰 Costo-Beneficio"]] as [t, label]}
        <button
          onclick={() => tab = t as typeof tab}
          class="px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px
            {tab === t ? 'border-blue-500 text-blue-400' : 'border-transparent text-white/40 hover:text-white/70'}"
        >{label}</button>
      {/each}
    </div>

    {#if loading}
      <div class="flex items-center justify-center py-20">
        <div class="text-white/40 text-sm animate-pulse">Conectando con sensores…</div>
      </div>
    {:else if error}
      <div class="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400">
        ⚠️ Error: {error}. Asegúrate de que el backend esté corriendo en localhost:8000.
      </div>
    {:else if data}

      <!-- ═══════════ DASHBOARD TAB ═══════════ -->
      {#if tab === "dashboard"}

        <!-- KPI Cards -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {#each Object.entries(data.kpis) as [name, kpi]}
            <div class="rounded-2xl border p-5 space-y-2"
              style="background:{statusBg(kpi.status)};border-color:{statusColor(kpi.status)}33">
              <div class="flex items-center justify-between">
                <span class="text-xs font-semibold text-white/50 uppercase tracking-wider">{name}</span>
                <span class="text-lg">{statusEmoji(kpi.status)}</span>
              </div>
              <div class="text-3xl font-bold" style="color:{statusColor(kpi.status)}">
                {fmt(kpi.value)}<span class="text-base font-normal text-white/40 ml-1">{kpi.unit}</span>
              </div>
              <div class="text-xs text-white/40">Meta: <span class="text-white/60">{kpi.target}</span></div>
              <div class="text-[10px] text-white/25 font-mono">{kpi.formula}</div>
            </div>
          {/each}
        </div>

        <!-- Caudales + Tanques -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">

          <!-- Caudales en tiempo real -->
          <div class="rounded-2xl border border-white/10 bg-white/[.03] p-5 space-y-4">
            <h3 class="text-sm font-semibold text-white/70">💧 Caudales en tiempo real</h3>
            {#each [
              ["Entrada aljibe", data.reading.inflow_l_min, "#60a5fa", 130],
              ["Demanda total", data.reading.total_demand_l_min, "#a78bfa", 130],
              ["Pérdidas", data.reading.losses_l_min, "#f87171", 20],
            ] as [label, val, color, max]}
              <div class="space-y-1">
                <div class="flex justify-between text-xs">
                  <span class="text-white/50">{label}</span>
                  <span class="font-mono" style="color:{color}">{fmt(val as number)} L/min</span>
                </div>
                <div class="h-2 rounded-full bg-white/10 overflow-hidden">
                  <div class="h-full rounded-full transition-all duration-500"
                    style="width:{Math.min(100, (val as number) / (max as number) * 100)}%;background:{color}">
                  </div>
                </div>
              </div>
            {/each}
          </div>

          <!-- Niveles de tanques -->
          <div class="rounded-2xl border border-white/10 bg-white/[.03] p-5 space-y-4">
            <h3 class="text-sm font-semibold text-white/70">🗄️ Niveles de tanques</h3>
            {#each [
              ["Tanque A", "36,000 L — Potabilización", data.reading.tank_a_pct],
              ["Tanque B", "16,000 L — Distribución", data.reading.tank_b_pct],
            ] as [name, cap, pct]}
              <div class="space-y-1">
                <div class="flex justify-between text-xs">
                  <span class="text-white/50">{name} <span class="text-white/25">({cap})</span></span>
                  <span class="font-mono {(pct as number) < 20 ? 'text-red-400' : (pct as number) < 40 ? 'text-yellow-400' : 'text-green-400'}">{pct}%</span>
                </div>
                <div class="h-4 rounded-full bg-white/10 overflow-hidden relative">
                  <div class="h-full rounded-full transition-all duration-700"
                    style="width:{pct}%;background:{(pct as number) < 20 ? '#ef4444' : (pct as number) < 40 ? '#f59e0b' : '#22c55e'}">
                  </div>
                </div>
              </div>
            {/each}
            <p class="text-[11px] text-white/30 pt-1">
              Proyección consumo diario: <span class="text-white/50">{fmtK(data.projection.projected_consumption_l)} L</span>
              <span class="ml-2 {data.projection.vs_baseline_pct > 10 ? 'text-red-400' : 'text-green-400'}">
                ({data.projection.vs_baseline_pct > 0 ? "+" : ""}{fmt(data.projection.vs_baseline_pct)}% vs. línea base)
              </span>
            </p>
          </div>
        </div>

        <!-- Consumo por zonas -->
        <div class="rounded-2xl border border-white/10 bg-white/[.03] p-5">
          <h3 class="text-sm font-semibold text-white/70 mb-4">🗺️ Consumo por zona del campus</h3>
          <div class="space-y-3">
            {#each Object.entries(data.reading.zones).sort((a,b) => b[1]-a[1]) as [zone, flow]}
              {@const total = Object.values(data.reading.zones).reduce((s,v)=>s+v,0)}
              {@const pct = total > 0 ? (flow / total * 100) : 0}
              {@const color = ZONE_COLORS[zone] ?? "#94a3b8"}
              <div class="flex items-center gap-3">
                <span class="text-xs text-white/50 w-32 shrink-0">{zone}</span>
                <div class="flex-1 h-6 rounded bg-white/5 overflow-hidden">
                  <div class="h-full rounded flex items-center px-2 transition-all duration-500"
                    style="width:{Math.max(4, pct)}%;background:{color}22;border-left:3px solid {color}">
                    <span class="text-[10px] font-mono" style="color:{color}">{fmt(flow)} L/m</span>
                  </div>
                </div>
                <span class="text-xs text-white/30 w-10 text-right">{fmt(pct, 0)}%</span>
              </div>
            {/each}
          </div>
        </div>

        <!-- Alertas -->
        {#if data.alerts.length > 0}
          <div class="rounded-2xl border border-white/10 bg-white/[.03] p-5 space-y-3">
            <h3 class="text-sm font-semibold text-white/70">🔔 Alertas activas ({data.alerts.length})</h3>
            {#each data.alerts as alert}
              <div class="rounded-xl p-3 space-y-1" style="background:{alertColor(alert.level)}11;border-left:3px solid {alertColor(alert.level)}">
                <div class="flex items-center gap-2">
                  <span class="text-xs font-semibold" style="color:{alertColor(alert.level)}">{alert.level.toUpperCase()}</span>
                  <span class="text-xs text-white/50">— {alert.zone}</span>
                </div>
                <p class="text-sm text-white/80">{alert.message}</p>
                <p class="text-xs text-white/40">→ {alert.action}</p>
              </div>
            {/each}
          </div>
        {:else}
          <div class="rounded-2xl border border-green-500/20 bg-green-500/5 p-4 text-sm text-green-400/80">
            ✅ Sistema operando sin alertas activas
          </div>
        {/if}

      <!-- ═══════════ HISTORIAL TAB ═══════════ -->
      {:else if tab === "history"}
        <div class="rounded-2xl border border-white/10 bg-white/[.03] p-5 space-y-4">
          <h3 class="text-sm font-semibold text-white/70">📈 Historial de consumo — últimas 24 horas</h3>
          {#if history.length === 0}
            <p class="text-white/30 text-sm">Cargando historial…</p>
          {:else}
            <!-- Mini sparkline using CSS bars -->
            {@const maxVal = Math.max(...history.map(h => h.consumption_l))}
            <div class="flex items-end gap-[2px] h-32">
              {#each history as point}
                <div class="flex-1 flex flex-col items-center gap-[2px] group relative">
                  <div class="absolute -top-6 left-1/2 -translate-x-1/2 hidden group-hover:block bg-black/80 rounded px-2 py-1 text-[10px] text-white whitespace-nowrap z-10">
                    {point.hour} — {fmtK(point.consumption_l)} L
                  </div>
                  <div class="w-full rounded-t transition-all"
                    style="height:{(point.consumption_l / maxVal * 100)}%;background:rgba(96,165,250,.6)">
                  </div>
                  <div class="w-full rounded-t"
                    style="height:{(point.losses_l / maxVal * 100)}%;background:rgba(239,68,68,.5)">
                  </div>
                </div>
              {/each}
            </div>
            <div class="flex gap-4 text-xs text-white/40">
              <span class="flex items-center gap-1"><span class="w-3 h-3 rounded-sm inline-block bg-blue-400/60"></span>Consumo</span>
              <span class="flex items-center gap-1"><span class="w-3 h-3 rounded-sm inline-block bg-red-400/50"></span>Pérdidas</span>
            </div>

            <!-- Table summary -->
            <div class="overflow-x-auto">
              <table class="w-full text-xs text-white/60">
                <thead>
                  <tr class="border-b border-white/10 text-white/30">
                    <th class="py-2 text-left">Hora</th>
                    <th class="py-2 text-right">Consumo (L)</th>
                    <th class="py-2 text-right">Pérdidas (L)</th>
                    <th class="py-2 text-right">Tanque A</th>
                    <th class="py-2 text-right">Tanque B</th>
                  </tr>
                </thead>
                <tbody>
                  {#each history.slice(-8) as point}
                    <tr class="border-b border-white/5 hover:bg-white/3">
                      <td class="py-1.5">{point.hour}</td>
                      <td class="py-1.5 text-right font-mono">{fmtK(point.consumption_l)}</td>
                      <td class="py-1.5 text-right font-mono text-red-400/70">{fmtK(point.losses_l)}</td>
                      <td class="py-1.5 text-right">{point.tank_a_pct}%</td>
                      <td class="py-1.5 text-right">{point.tank_b_pct}%</td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          {/if}
        </div>

      <!-- ═══════════ COSTO-BENEFICIO TAB ═══════════ -->
      {:else if tab === "report"}
        {@const cb = data.projection.cost_benefit}
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="rounded-2xl border border-white/10 bg-white/[.03] p-5 space-y-4">
            <h3 class="text-sm font-semibold text-white/70">💰 Análisis Costo-Beneficio</h3>
            {#each [
              ["Pérdida diaria estimada", `${fmtK(cb.current_daily_loss_l)} L/día`, "#f87171"],
              ["Ahorro anual proyectado", `$${(cb.annual_water_savings_cop/1e6).toFixed(1)}M COP`, "#22c55e"],
              ["Costo sensores (estimado)", "$4.5M COP", "#60a5fa"],
              ["Recuperación de inversión", `${cb.roi_months.toFixed(1)} meses`, "#a78bfa"],
            ] as [label, val, color]}
              <div class="flex justify-between items-center py-2 border-b border-white/5">
                <span class="text-sm text-white/50">{label}</span>
                <span class="text-sm font-semibold font-mono" style="color:{color}">{val}</span>
              </div>
            {/each}
          </div>

          <div class="rounded-2xl border border-white/10 bg-white/[.03] p-5 space-y-4">
            <h3 class="text-sm font-semibold text-white/70">🏭 Propuesta de Mejora Operativa</h3>
            {#each [
              { icon: "📡", title: "Caudalímetros en puntos críticos", desc: "Entrada PTAP, salida Tanque A, zona de riego. Detección de pérdidas en tiempo real." },
              { icon: "🤖", title: "Válvulas solenoides programables", desc: "Control automático de riego nocturno y horas valle para reducir picos de demanda." },
              { icon: "📊", title: "Dashboard en campus", desc: "Pantallas públicas mostrando KPIs y consumo. Fomenta concientización estudiantil." },
            ] as item}
              <div class="flex gap-3 p-3 rounded-xl bg-white/3 border border-white/5">
                <span class="text-xl">{item.icon}</span>
                <div>
                  <p class="text-sm font-medium text-white/80">{item.title}</p>
                  <p class="text-xs text-white/40 mt-0.5">{item.desc}</p>
                </div>
              </div>
            {/each}
          </div>
        </div>

        <!-- KPIs con fórmulas -->
        <div class="rounded-2xl border border-white/10 bg-white/[.03] p-5">
          <h3 class="text-sm font-semibold text-white/70 mb-4">📐 KPIs — Definición y fórmulas</h3>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            {#each [
              { name:"IEH", full:"Índice de Eficiencia Hídrica", formula:"(Caudal entrada − Pérdidas) / Caudal entrada × 100", target:"> 90%", unit:"%" },
              { name:"TPP", full:"Tasa de Pérdidas del Proceso", formula:"Pérdidas / Caudal entrada × 100", target:"< 10%", unit:"%" },
              { name:"CPE", full:"Consumo Per Estudiante", formula:"Consumo diario total / N° estudiantes activos", target:"≈ 14.04", unit:"L/est/día" },
            ] as kpi}
              <div class="rounded-xl border border-blue-500/20 bg-blue-500/5 p-4 space-y-2">
                <div class="font-bold text-blue-300">{kpi.name}</div>
                <div class="text-xs text-white/60">{kpi.full}</div>
                <code class="text-[11px] text-white/40 font-mono block">{kpi.formula}</code>
                <div class="text-xs text-white/40">Meta: <span class="text-white/60">{kpi.target} {kpi.unit}</span></div>
              </div>
            {/each}
          </div>
        </div>
      {/if}

    {/if}<!-- end if data -->

    <!-- Footer -->
    <footer class="text-center text-[11px] text-white/20 py-4">
      AguaMind OS — Hackathon UNIAJC 2026 · Datos basados en Arias Montoya et al. (2024) · Actualización automática cada 30s
    </footer>
  </main>
</div>
