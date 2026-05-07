<script lang="ts">
  import { onMount, onDestroy } from "svelte";

  // ── Tipos ────────────────────────────────────────────────────────────────
  type KPIStatus = "ok" | "warning" | "critical";
  interface KPI { value: number; unit?: string; target?: string; formula?: string; status: KPIStatus; }
  interface Reading {
    timestamp: string;
    flow1_lmin?: number; flow2_lmin?: number; total_flow_lmin?: number;
    pressure_kpa?: number; phreatic_m?: number; turbidity_ntu?: number;
    vibration?: boolean; pump_active?: boolean;
    tank_a_pct: number; tank_b_pct: number;
    tank_a_l?: number; tank_b_l?: number;
    zones: Record<string, number>;
    losses_l_min?: number; demand_l_min?: number;
  }
  interface Alert { level: string; zone: string; message: string; action: string; sensor?: string; }
  interface AgentStatus {
    running: boolean; cycle: number; last_decision: string; last_cycle_at?: string;
    interval_s: number; agents: Record<string, string>;
    last_alerts: number; last_issues: string[];
  }

  // ── Estado ───────────────────────────────────────────────────────────────
  let reading = $state<Reading | null>(null);
  let kpis = $state<Record<string, KPI>>({});
  let alerts = $state<Alert[]>([]);
  let history = $state<any[]>([]);
  let agent = $state<AgentStatus | null>(null);
  let agentLog = $state<{ts: string; cycle: number; decision: string; issue: string}[]>([]);
  let error = $state<string | null>(null);
  let loading = $state(true);
  let lastRefresh = $state<Date | null>(null);
  let scenario = $state<"normal" | "leak" | "peak_irrigation" | "turbidity">("normal");
  let scenarioLoading = $state(false);
  let tab = $state<"dashboard" | "history" | "industrial" | "agent">("dashboard");
  let liveMode = $state(true);
  let theme = $state<"dark" | "light">("dark");

  $effect(() => {
    if (typeof document !== "undefined") {
      document.documentElement.classList.toggle("light", theme === "light");
    }
  });

  // ── Helpers ──────────────────────────────────────────────────────────────
  function fmt(n: number | undefined, dec = 1): string {
    return n != null && !isNaN(n) ? n.toFixed(dec) : "—";
  }
  function fmtK(n: number | undefined): string {
    if (n == null || isNaN(n)) return "—";
    return n >= 1000 ? (n / 1000).toFixed(1) + "k" : n.toFixed(0);
  }
  function fmtCop(n: number | undefined): string {
    if (n == null || isNaN(n)) return "—";
    return "$" + Math.round(n).toLocaleString("es-CO");
  }

  function statusHex(s: KPIStatus): string {
    return s === "ok" ? "#10b981" : s === "warning" ? "#f59e0b" : "#ef4444";
  }
  function decisionColor(d: string): string {
    if (d === "ok") return "text-emerald-400";
    if (d === "warning" || d === "alert") return "text-amber-400";
    if (d === "critical") return "text-red-400";
    return "text-slate-400";
  }
  function alertBorder(level: string): string {
    if (level === "critical") return "border-red-500/30 bg-red-500/[0.04]";
    if (level === "warning") return "border-amber-500/30 bg-amber-500/[0.04]";
    return "border-sky-500/30 bg-sky-500/[0.04]";
  }

  // ── Fetchers ─────────────────────────────────────────────────────────────
  async function fetchReading() {
    try {
      const res = await fetch("/api/water?endpoint=reading");
      const json = await res.json();
      if (json.error) { error = json.error; return; }
      const d = json.data;
      reading = d.reading;
      kpis = d.kpis ?? {};
      alerts = d.alerts ?? [];
      error = null;
      lastRefresh = new Date();
    } catch (e) {
      error = String(e);
    } finally {
      loading = false;
    }
  }

  async function fetchHistory() {
    try {
      const res = await fetch("/api/water?endpoint=history&hours=24");
      const json = await res.json();
      if (json.data) history = json.data;
    } catch {}
  }

  async function fetchAgent() {
    try {
      const res = await fetch("/api/water?endpoint=agent/status");
      const json = await res.json();
      if (json.data) {
        agent = json.data;
        if (agent && agent.cycle > 0) {
          const ts = new Date().toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" });
          const issue = agent.last_issues[0] ?? "Sistema operando normalmente";
          if (!agentLog.length || agentLog[0].cycle !== agent.cycle) {
            agentLog = [{ ts, cycle: agent.cycle, decision: agent.last_decision, issue }, ...agentLog.slice(0, 9)];
          }
        }
      }
    } catch {}
  }

  async function runScenario(sc: typeof scenario) {
    scenarioLoading = true;
    try {
      const res = await fetch("/api/water", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario: sc }),
      });
      const json = await res.json();
      if (json.data) {
        scenario = sc;
        reading = json.data.reading;
        kpis = json.data.kpis;
        alerts = json.data.alerts ?? [];
        lastRefresh = new Date();
      }
    } finally {
      scenarioLoading = false;
    }
  }

  async function toggleAgent() {
    if (!agent) return;
    const action = agent.running ? "stop" : "start";
    await fetch(`/api/water?endpoint=agent/${action}`, { method: "POST" });
    await fetchAgent();
  }

  async function runCycle() {
    await fetch("/api/water?endpoint=agent/cycle", { method: "POST" });
    await fetchAgent();
    await fetchReading();
  }

  // ── Lifecycle ────────────────────────────────────────────────────────────
  let interval: ReturnType<typeof setInterval>;
  onMount(async () => {
    await fetchReading();
    await fetchHistory();
    await fetchAgent();
    interval = setInterval(async () => {
      if (liveMode) { await fetchReading(); await fetchAgent(); }
    }, 10000);
  });
  onDestroy(() => clearInterval(interval));

  const maxConsumption = $derived(Math.max(...history.map(h => h.consumption_l ?? 0), 1));
  const totalAnnualLoss = $derived((reading?.losses_l_min ?? 0) * 1440 * 365 * 3.5);
  const annualSaving    = $derived(totalAnnualLoss * 0.6);
</script>

<svelte:head>
  <title>AguaMind OS · UNIAJC</title>
</svelte:head>

<div class="min-h-screen am-root" style="font-family: 'Inter', -apple-system, system-ui, sans-serif;">

  <!-- ══ Header ════════════════════════════════════════════════════════════ -->
  <header class="border-b border-white/[0.06] bg-[#0a0e14]/90 backdrop-blur-xl sticky top-0 z-30">
    <div class="mx-auto max-w-7xl px-6 py-4 flex items-center justify-between">

      <!-- Logo + título -->
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-lg bg-gradient-to-br from-sky-400 to-sky-600 flex items-center justify-center">
          <svg viewBox="0 0 24 24" fill="none" class="w-5 h-5 text-white" stroke="currentColor" stroke-width="2.2">
            <path d="M12 2.5C12 2.5 6 9 6 14a6 6 0 0012 0c0-5-6-11.5-6-11.5z" stroke-linejoin="round"/>
          </svg>
        </div>
        <div class="leading-tight">
          <h1 class="text-[14px] font-semibold tracking-tight text-white">AguaMind OS</h1>
          <p class="text-[11px] text-slate-500 mt-0.5">UNIAJC Sede Sur · Gestión Hídrica Inteligente</p>
        </div>
      </div>

      <!-- Controls -->
      <div class="flex items-center gap-2">
        <select
          bind:value={scenario}
          onchange={() => runScenario(scenario)}
          disabled={scenarioLoading}
          class="text-[11px] bg-white/[0.04] hover:bg-white/[0.07] border border-white/10 rounded-md px-2.5 py-1.5 text-slate-300 outline-none focus:border-sky-500/60 transition-colors"
        >
          <option value="normal">Escenario: Normal</option>
          <option value="leak">Escenario: Fuga</option>
          <option value="peak_irrigation">Escenario: Pico Riego</option>
          <option value="turbidity">Escenario: Turbidez</option>
        </select>

        <button
          onclick={() => liveMode = !liveMode}
          class="flex items-center gap-1.5 text-[11px] px-2.5 py-1.5 rounded-md border transition-colors
            {liveMode ? 'border-emerald-500/30 bg-emerald-500/[0.06] text-emerald-400' : 'border-white/10 bg-white/[0.04] text-slate-400'}"
        >
          <span class="w-1.5 h-1.5 rounded-full {liveMode ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}"></span>
          {liveMode ? "En vivo" : "Pausado"}
        </button>

        {#if lastRefresh}
          <span class="text-[11px] text-slate-500 hidden md:block">{lastRefresh.toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit", second: "2-digit" })}</span>
        {/if}

        <!-- Theme toggle -->
        <button
          onclick={() => theme = theme === "dark" ? "light" : "dark"}
          class="flex items-center justify-center w-8 h-8 rounded-md border border-white/10 hover:border-white/20 bg-white/[0.04] hover:bg-white/[0.07] text-slate-400 transition-colors"
          title="Cambiar tema"
        >
          {#if theme === "dark"}
            <!-- icono sol -->
            <svg viewBox="0 0 24 24" fill="none" class="w-4 h-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="4"/>
              <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>
            </svg>
          {:else}
            <!-- icono luna -->
            <svg viewBox="0 0 24 24" fill="none" class="w-4 h-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/>
            </svg>
          {/if}
        </button>
      </div>
    </div>

    <!-- Tabs -->
    <div class="mx-auto max-w-7xl px-6 flex gap-0">
      {#each [
        ["dashboard",  "Dashboard"],
        ["history",    "Historial"],
        ["industrial", "Industrial"],
        ["agent",      "Agente IA"],
      ] as [key, label]}
        <button
          onclick={() => { tab = key as typeof tab; if (key === "history") fetchHistory(); }}
          class="px-4 py-2.5 text-[12px] font-medium tracking-tight border-b-2 transition-all -mb-px
            {tab === key ? 'border-sky-500 text-white' : 'border-transparent text-slate-500 hover:text-slate-300'}"
        >{label}</button>
      {/each}
    </div>
  </header>

  <main class="mx-auto max-w-7xl px-6 py-6">

    {#if error}
      <div class="rounded-lg border border-red-500/30 bg-red-500/[0.06] px-4 py-2.5 text-sm text-red-300 mb-5">
        Backend no disponible — {error}.
        <a href="http://localhost:8000/docs" target="_blank" class="underline ml-1">abrir API</a>
      </div>
    {/if}

    {#if loading}
      <div class="flex items-center justify-center py-32">
        <span class="text-sm text-slate-500 animate-pulse">Conectando con sensores…</span>
      </div>

    <!-- ════════════════════════════════════════════════════════════════════ -->
    <!-- TAB 1: DASHBOARD -->
    <!-- ════════════════════════════════════════════════════════════════════ -->
    {:else if tab === "dashboard" && reading}

      <!-- Hero KPI strip -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
        {#each Object.entries(kpis) as [name, kpi]}
          <div class="group relative overflow-hidden rounded-xl border border-white/[0.06] bg-white/[0.02] hover:bg-white/[0.04] transition-colors p-4">
            <div class="absolute top-0 left-0 right-0 h-0.5" style="background:{statusHex(kpi.status)}"></div>
            <div class="flex items-center justify-between mb-2">
              <span class="text-[10px] font-mono font-medium uppercase tracking-widest text-slate-500">{name}</span>
              <span class="text-[10px] font-medium px-1.5 py-0.5 rounded uppercase tracking-wider"
                    style="color:{statusHex(kpi.status)};background:{statusHex(kpi.status)}1A">{kpi.status}</span>
            </div>
            <div class="text-[28px] font-semibold tracking-tight text-white" style="font-family:'JetBrains Mono','SF Mono',monospace">
              {fmt(kpi.value, name === "CPE" ? 2 : 1)}<span class="text-sm text-slate-500 ml-1 font-normal">{kpi.unit ?? ""}</span>
            </div>
            <div class="text-[10px] text-slate-500 mt-0.5">{kpi.target ?? ""}</div>
          </div>
        {/each}
      </div>

      <!-- Main grid: 2 tanques + sensores -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-3 mb-5">

        <!-- Tanque A visual -->
        <div class="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5">
          <div class="flex items-center justify-between mb-4">
            <div>
              <div class="text-[11px] font-medium tracking-wider uppercase text-slate-500">Tanque A · Principal</div>
              <div class="text-[10px] text-slate-600 mt-0.5">36,000 L · Bomba {reading.pump_active ? "ACTIVA" : "OFF"}</div>
            </div>
            <div class="text-[10px] font-mono text-slate-500">{fmtK(reading.tank_a_l)} L</div>
          </div>
          <div class="relative h-36 bg-[#060a10] rounded-lg overflow-hidden border border-white/[0.04]">
            <div
              class="absolute bottom-0 left-0 right-0 transition-all duration-1000"
              style="height:{reading.tank_a_pct}%;background:{reading.tank_a_pct < 33 ? 'linear-gradient(180deg,#fca5a5,#ef4444)' : reading.tank_a_pct < 67 ? 'linear-gradient(180deg,#fbbf24,#f59e0b)' : 'linear-gradient(180deg,#7dd3fc,#0ea5e9)'}"
            ></div>
            <div class="absolute inset-0 flex items-center justify-center">
              <span class="text-[36px] font-semibold tracking-tight text-white drop-shadow-md" style="font-family:'JetBrains Mono',monospace">{fmt(reading.tank_a_pct)}%</span>
            </div>
            <!-- Línea umbral bomba -->
            <div class="absolute left-0 right-0 border-t border-amber-500/40 border-dashed" style="bottom:66.7%">
              <span class="absolute right-2 -top-3 text-[9px] text-amber-500/80 font-mono">66.7% · bomba</span>
            </div>
          </div>
        </div>

        <!-- Tanque B visual -->
        <div class="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5">
          <div class="flex items-center justify-between mb-4">
            <div>
              <div class="text-[11px] font-medium tracking-wider uppercase text-slate-500">Tanque B · Distribución</div>
              <div class="text-[10px] text-slate-600 mt-0.5">16,000 L</div>
            </div>
            <div class="text-[10px] font-mono text-slate-500">{fmtK(reading.tank_b_l)} L</div>
          </div>
          <div class="relative h-36 bg-[#060a10] rounded-lg overflow-hidden border border-white/[0.04]">
            <div
              class="absolute bottom-0 left-0 right-0 transition-all duration-1000"
              style="height:{reading.tank_b_pct}%;background:{reading.tank_b_pct < 33 ? 'linear-gradient(180deg,#fca5a5,#ef4444)' : 'linear-gradient(180deg,#a5f3fc,#06b6d4)'}"
            ></div>
            <div class="absolute inset-0 flex items-center justify-center">
              <span class="text-[36px] font-semibold tracking-tight text-white drop-shadow-md" style="font-family:'JetBrains Mono',monospace">{fmt(reading.tank_b_pct)}%</span>
            </div>
          </div>
        </div>

        <!-- 6 sensores compactos -->
        <div class="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5">
          <div class="text-[11px] font-medium tracking-wider uppercase text-slate-500 mb-4">6 Sensores · Tiempo real</div>
          <div class="space-y-3">
            {#each [
              { label: "Caudal total",     value: fmt(reading.total_flow_lmin, 1) + " L/min", pct: (reading.total_flow_lmin ?? 0) / 150 * 100, color: "#7dd3fc", code: "Q" },
              { label: "Presión red",      value: fmt(reading.pressure_kpa, 0) + " kPa",       pct: (reading.pressure_kpa ?? 0) / 700 * 100,    color: "#a5b4fc", code: "P" },
              { label: "Nivel freático",   value: fmt(reading.phreatic_m, 1) + " m",           pct: (reading.phreatic_m ?? 0) / 15 * 100,        color: "#86efac", code: "N" },
              { label: "Turbidez",         value: fmt(reading.turbidity_ntu, 1) + " NTU",      pct: (reading.turbidity_ntu ?? 0) / 5 * 100,       color: (reading.turbidity_ntu ?? 0) > 4 ? "#f87171" : "#fbbf24", code: "T" },
            ] as s}
              <div>
                <div class="flex justify-between items-center text-[11px] mb-1">
                  <span class="flex items-center gap-2">
                    <span class="w-4 h-4 rounded-sm flex items-center justify-center text-[10px] font-mono font-bold" style="background:{s.color}1A;color:{s.color}">{s.code}</span>
                    <span class="text-slate-400">{s.label}</span>
                  </span>
                  <span class="font-mono text-slate-200">{s.value}</span>
                </div>
                <div class="h-1 bg-white/[0.04] rounded-full overflow-hidden">
                  <div class="h-full transition-all duration-700" style="width:{Math.min(100, Math.max(0, s.pct))}%;background:{s.color}"></div>
                </div>
              </div>
            {/each}
            <div class="flex items-center justify-between text-[11px] pt-1.5 border-t border-white/[0.06] mt-2">
              <span class="flex items-center gap-2">
                <span class="w-4 h-4 rounded-sm flex items-center justify-center text-[10px] font-mono font-bold bg-white/[0.06] text-slate-400">V</span>
                <span class="text-slate-400">Vibración tubería</span>
              </span>
              <span class="font-mono {reading.vibration ? 'text-red-400' : 'text-emerald-400'}">{reading.vibration ? "anomalía" : "estable"}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Consumo por zonas -->
      <div class="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5 mb-5">
        <div class="flex items-center justify-between mb-4">
          <div class="text-[11px] font-medium tracking-wider uppercase text-slate-500">Consumo por zona</div>
          <div class="text-[10px] text-slate-600 font-mono">{Object.keys(reading.zones ?? {}).length} zonas</div>
        </div>
        <div class="space-y-2">
          {#each Object.entries(reading.zones ?? {}).sort((a, b) => (b[1] as number) - (a[1] as number)) as [zone, flow]}
            {@const f = flow as number}
            {@const total = (Object.values(reading.zones ?? {}) as number[]).reduce((s, v) => s + v, 0) || 1}
            {@const pct = (f / total) * 100}
            <div class="flex items-center gap-3">
              <span class="text-[11px] text-slate-400 w-40 truncate shrink-0">{zone}</span>
              <div class="flex-1 h-5 bg-white/[0.03] rounded overflow-hidden">
                <div class="h-full rounded transition-all duration-700 flex items-center px-2" style="width:{Math.max(2, pct)}%;background:linear-gradient(90deg,#0ea5e91A,#0ea5e94D);border-left:2px solid #0ea5e9">
                  <span class="text-[10px] font-mono text-sky-300/90">{fmt(f)} L/min</span>
                </div>
              </div>
              <span class="text-[10px] text-slate-500 font-mono w-10 text-right">{fmt(pct, 0)}%</span>
            </div>
          {/each}
        </div>
      </div>

      <!-- Alertas -->
      {#if alerts.length > 0}
        <div class="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5">
          <div class="flex items-center justify-between mb-4">
            <div class="text-[11px] font-medium tracking-wider uppercase text-slate-500">Alertas activas</div>
            <div class="flex items-center gap-2 text-[10px]">
              {#if alerts.filter(a => a.level === "critical").length}
                <span class="px-1.5 py-0.5 rounded bg-red-500/10 text-red-400 font-mono">{alerts.filter(a => a.level === "critical").length} críticas</span>
              {/if}
              {#if alerts.filter(a => a.level === "warning").length}
                <span class="px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 font-mono">{alerts.filter(a => a.level === "warning").length} advertencias</span>
              {/if}
            </div>
          </div>
          <div class="space-y-2">
            {#each alerts.slice(0, 6) as alert}
              <div class="rounded-lg border {alertBorder(alert.level)} px-3 py-2.5">
                <div class="flex items-start justify-between gap-2 mb-1">
                  <div class="flex-1 min-w-0">
                    <div class="text-[12px] font-medium text-white">{alert.zone}</div>
                    <div class="text-[10px] text-slate-500 mt-0.5">{alert.sensor ?? ""}</div>
                  </div>
                  <span class="text-[9px] uppercase tracking-wider font-medium font-mono shrink-0
                    {alert.level === 'critical' ? 'text-red-400' : alert.level === 'warning' ? 'text-amber-400' : 'text-sky-400'}">{alert.level}</span>
                </div>
                <div class="text-[11px] text-slate-300">{alert.message}</div>
                <div class="text-[10px] text-slate-500 mt-1 italic">→ {alert.action}</div>
              </div>
            {/each}
          </div>
        </div>
      {:else}
        <div class="rounded-xl border border-emerald-500/20 bg-emerald-500/[0.04] px-5 py-4 text-center">
          <div class="text-[12px] text-emerald-400">Sistema operando con normalidad</div>
          <div class="text-[10px] text-slate-500 mt-0.5">Sin alertas activas en los 6 sensores</div>
        </div>
      {/if}

    <!-- ════════════════════════════════════════════════════════════════════ -->
    <!-- TAB 2: HISTORIAL -->
    <!-- ════════════════════════════════════════════════════════════════════ -->
    {:else if tab === "history"}

      <div class="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5 mb-5">
        <div class="flex items-center justify-between mb-5">
          <div>
            <div class="text-[11px] font-medium tracking-wider uppercase text-slate-500">Consumo</div>
            <div class="text-[12px] text-slate-300 mt-0.5">Últimas 24 horas · {history.length} muestras</div>
          </div>
        </div>
        <div class="flex items-end gap-px h-32">
          {#each history as h}
            <div class="flex-1 min-w-0 group relative">
              <div
                class="w-full bg-gradient-to-t from-sky-600 to-sky-400 hover:from-sky-500 hover:to-sky-300 rounded-t transition-colors"
                style="height:{(h.consumption_l / maxConsumption) * 100}%"
              ></div>
              <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 text-[10px] bg-slate-900 border border-white/10 text-slate-200 px-2 py-1 rounded opacity-0 group-hover:opacity-100 whitespace-nowrap z-10 pointer-events-none font-mono">
                {h.hour}: {(h.consumption_l ?? 0).toLocaleString()} L
              </div>
            </div>
          {/each}
        </div>
        <div class="flex justify-between text-[9px] text-slate-600 font-mono mt-2">
          {#each [0, Math.floor(history.length/4), Math.floor(history.length/2), Math.floor(history.length*3/4), history.length-1] as idx}
            <span>{history[idx]?.hour ?? "—"}</span>
          {/each}
        </div>
      </div>

      <div class="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5">
        <div class="text-[11px] font-medium tracking-wider uppercase text-slate-500 mb-4">Detalle por hora · últimas 12</div>
        <div class="overflow-x-auto">
          <table class="w-full text-[11px]" style="font-family:'JetBrains Mono',monospace">
            <thead>
              <tr class="text-slate-500 border-b border-white/[0.06]">
                <th class="text-left py-2 px-2 font-medium">Hora</th>
                <th class="text-right py-2 px-2 font-medium">Consumo (L)</th>
                <th class="text-right py-2 px-2 font-medium">Pérdidas (L)</th>
                <th class="text-right py-2 px-2 font-medium">Caudal (L/min)</th>
                <th class="text-right py-2 px-2 font-medium">Turbidez (NTU)</th>
                <th class="text-right py-2 px-2 font-medium">Tanque A (%)</th>
                <th class="text-right py-2 px-2 font-medium">Freático (m)</th>
              </tr>
            </thead>
            <tbody>
              {#each history.slice(-12).reverse() as h}
                <tr class="border-b border-white/[0.03] hover:bg-white/[0.02]">
                  <td class="py-1.5 px-2 text-slate-300">{h.hour}</td>
                  <td class="text-right py-1.5 px-2 text-sky-300">{(h.consumption_l ?? 0).toLocaleString()}</td>
                  <td class="text-right py-1.5 px-2 text-red-400/80">{(h.losses_l ?? 0).toLocaleString()}</td>
                  <td class="text-right py-1.5 px-2 text-slate-300">{fmt(h.inflow_lmin ?? h.inflow_l_min)}</td>
                  <td class="text-right py-1.5 px-2 {(h.turbidity_ntu ?? 0) > 4 ? 'text-red-400' : (h.turbidity_ntu ?? 0) > 2 ? 'text-amber-400' : 'text-emerald-400'}">{fmt(h.turbidity_ntu)}</td>
                  <td class="text-right py-1.5 px-2 text-slate-300">{fmt(h.tank_a_pct)}</td>
                  <td class="text-right py-1.5 px-2 text-slate-400">{fmt(h.phreatic_m)}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      </div>

    <!-- ════════════════════════════════════════════════════════════════════ -->
    <!-- TAB 3: INDUSTRIAL -->
    <!-- ════════════════════════════════════════════════════════════════════ -->
    {:else if tab === "industrial"}

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-3 mb-3">

        <!-- KPIs con fórmulas -->
        <div class="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5">
          <div class="text-[11px] font-medium tracking-wider uppercase text-slate-500 mb-4">Indicadores de Desempeño</div>
          <div class="space-y-4">
            {#each [
              { id: "IEH", name: "Eficiencia Hídrica",       formula: "(Q_entrada − Pérdidas) / Q_entrada × 100",     target: "> 90%" },
              { id: "TPP", name: "Tasa de Pérdidas",         formula: "Pérdidas / Q_entrada × 100",                   target: "< 10%" },
              { id: "CPE", name: "Consumo per Estudiante",   formula: "Consumo_diario / Estudiantes_activos",         target: "≤ 14.04 L/est" },
              { id: "ICA", name: "Calidad de Agua",          formula: "100 − (Turbidez / 4) × 30",                    target: "> 90 pts" },
            ] as k}
              {@const kpi = kpis[k.id] ?? { value: 0, status: "ok" as KPIStatus, unit: "" }}
              <div class="border-l-2 pl-3 py-1" style="border-color:{statusHex(kpi.status)}">
                <div class="flex justify-between items-baseline mb-1">
                  <span class="font-mono font-semibold text-[13px] text-white">{k.id}</span>
                  <span class="text-[18px] font-mono font-semibold" style="color:{statusHex(kpi.status)}">{fmt(kpi.value, k.id === "CPE" ? 2 : 1)}<span class="text-[11px] text-slate-500 ml-1 font-normal">{kpi.unit ?? ""}</span></span>
                </div>
                <div class="text-[11px] text-slate-400">{k.name}</div>
                <div class="text-[10px] font-mono text-slate-600 mt-0.5">{k.formula}</div>
                <div class="text-[10px] text-slate-500 mt-0.5">Meta: {k.target}</div>
              </div>
            {/each}
          </div>
        </div>

        <!-- Costo-Beneficio -->
        <div class="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5">
          <div class="text-[11px] font-medium tracking-wider uppercase text-slate-500 mb-4">Costo-Beneficio</div>
          <div class="space-y-2.5">
            {#each [
              ["Pérdida anual estimada",        fmtCop(totalAnnualLoss),       "text-red-400"],
              ["Inversión AguaMind OS",         "$1,043,000",                  "text-slate-200"],
              ["Ahorro proyectado anual",       fmtCop(annualSaving),          "text-emerald-400"],
              ["Recuperación de inversión",     "21 días",                     "text-emerald-400"],
              ["VPN a 5 años (12%)",            "$65,369,000",                 "text-emerald-400"],
              ["TIR anual",                     "> 1,000%",                    "text-emerald-400"],
              ["Ratio Beneficio/Costo",         "17.4×",                       "text-sky-400"],
            ] as [label, value, color]}
              <div class="flex justify-between items-center text-[12px] py-1.5 border-b border-white/[0.04]">
                <span class="text-slate-400">{label}</span>
                <span class="font-mono {color}">{value}</span>
              </div>
            {/each}
          </div>
          <div class="mt-4 p-3 rounded-lg bg-sky-500/[0.05] border border-sky-500/20">
            <div class="text-[10px] font-medium tracking-wider uppercase text-sky-400 mb-1.5">Objetivos de Desarrollo Sostenible</div>
            <div class="flex flex-wrap gap-1">
              {#each ["ODS 6 · Agua", "ODS 9 · Industria", "ODS 11 · Ciudades", "ODS 13 · Clima", "ODS 4 · Educación"] as ods}
                <span class="text-[10px] px-1.5 py-0.5 rounded bg-sky-500/10 text-sky-300 font-medium">{ods}</span>
              {/each}
            </div>
          </div>
        </div>
      </div>

      <!-- Lean mudas -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <div class="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5">
          <div class="text-[11px] font-medium tracking-wider uppercase text-slate-500 mb-4">Lean Manufacturing · 7 Mudas</div>
          <div class="space-y-2.5">
            {#each [
              ["Defectos",        "Fugas no detectadas (20-30% del caudal perdido)"],
              ["Sobreproducción", "Bombeo sin demanda real (tanque ya lleno)"],
              ["Espera",          "Detección manual tarda días o semanas"],
              ["Inventario",      "Sin control nivel tanques en tiempo real"],
              ["Movimiento",      "Personal revisa niveles físicamente"],
              ["Transporte",      "Agua tratada usada para riego (innecesario)"],
              ["Talento",         "Datos del campus sin análisis ni acción"],
            ] as [muda, desc]}
              <div class="flex gap-3 text-[11px] py-1 border-b border-white/[0.04]">
                <span class="text-amber-400 font-medium w-32 shrink-0">{muda}</span>
                <span class="text-slate-400">{desc}</span>
              </div>
            {/each}
          </div>
        </div>

        <div class="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5">
          <div class="text-[11px] font-medium tracking-wider uppercase text-slate-500 mb-4">Acciones de Mejora</div>
          <div class="space-y-3">
            <div class="border-l-2 border-emerald-500 pl-3 py-1">
              <div class="text-[12px] font-medium text-white">1. Instrumentación IoT</div>
              <div class="text-[10px] text-slate-500 mt-0.5">6 sensores + ESP32 + agente IA</div>
              <div class="flex gap-3 mt-1.5 text-[10px] font-mono">
                <span class="text-slate-400">Inv:</span><span class="text-white">$1,043,000</span>
                <span class="text-slate-400">ROI:</span><span class="text-emerald-400">21 días</span>
              </div>
            </div>
            <div class="border-l-2 border-sky-500 pl-3 py-1">
              <div class="text-[12px] font-medium text-white">2. Riego automatizado</div>
              <div class="text-[10px] text-slate-500 mt-0.5">Válvulas solenoides DN25 nocturnas</div>
              <div class="flex gap-3 mt-1.5 text-[10px] font-mono">
                <span class="text-slate-400">Inv:</span><span class="text-white">$2,800,000</span>
                <span class="text-slate-400">Ahorro:</span><span class="text-emerald-400">803,000 L/año</span>
              </div>
            </div>
            <div class="mt-4 pt-3 border-t border-white/[0.06]">
              <div class="text-[10px] font-medium tracking-wider uppercase text-slate-500 mb-2">Datos del campus</div>
              <div class="grid grid-cols-2 gap-2 text-[11px]">
                <div><span class="text-slate-500">Consumo:</span> <span class="font-mono text-white">45,367 L/día</span></div>
                <div><span class="text-slate-500">Estudiantes:</span> <span class="font-mono text-white">3,230</span></div>
                <div><span class="text-slate-500">Caudal:</span> <span class="font-mono text-white">113.56 L/min</span></div>
                <div><span class="text-slate-500">Usuarios totales:</span> <span class="font-mono text-white">8,234</span></div>
              </div>
            </div>
          </div>
        </div>
      </div>

    <!-- ════════════════════════════════════════════════════════════════════ -->
    <!-- TAB 4: AGENTE IA -->
    <!-- ════════════════════════════════════════════════════════════════════ -->
    {:else if tab === "agent"}

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-3">

        <!-- Control + agentes especializados -->
        <div class="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5">
          <div class="flex items-center justify-between mb-4">
            <div>
              <div class="text-[11px] font-medium tracking-wider uppercase text-slate-500">WaterMonitorAgent</div>
              <div class="text-[12px] text-slate-300 mt-0.5">Sistema multi-agente autónomo</div>
            </div>
            <button
              onclick={toggleAgent}
              class="px-4 py-1.5 rounded-md text-[11px] font-medium transition-colors border
                {agent?.running ? 'border-red-500/30 bg-red-500/10 text-red-400 hover:bg-red-500/20' : 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20'}"
            >{agent?.running ? "Detener" : "Iniciar agente"}</button>
          </div>

          <!-- Estado actual -->
          <div class="rounded-lg border {agent?.running ? 'border-emerald-500/20 bg-emerald-500/[0.03]' : 'border-white/[0.06] bg-white/[0.02]'} p-3 mb-4">
            <div class="flex items-center gap-2 mb-1.5">
              <span class="w-1.5 h-1.5 rounded-full {agent?.running ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}"></span>
              <span class="text-[11px] font-medium {agent?.running ? 'text-emerald-400' : 'text-slate-400'}">{agent?.running ? "EN MONITOREO" : "DETENIDO"}</span>
              <span class="text-[10px] text-slate-500 ml-auto">cada {agent?.interval_s ?? 30}s</span>
            </div>
            <div class="grid grid-cols-2 gap-2 text-[11px]">
              <div><span class="text-slate-500">Ciclo:</span> <span class="font-mono text-white">#{agent?.cycle ?? 0}</span></div>
              <div><span class="text-slate-500">Decisión:</span> <span class="font-mono {decisionColor(agent?.last_decision ?? 'ok')} uppercase">{agent?.last_decision ?? "—"}</span></div>
            </div>
          </div>

          <!-- 4 agentes -->
          <div class="text-[10px] font-medium tracking-wider uppercase text-slate-500 mb-2">4 Agentes Especializados</div>
          <div class="space-y-1.5 mb-4">
            {#each [
              { code: "ORC", name: "Orchestrator",     desc: "Coordinación + reportes",         status: agent?.last_decision ?? "—" },
              { code: "SYS", name: "SystemsAgent",     desc: "KPIs + anomalías IsolationForest", status: agent?.agents?.systems    ?? "—" },
              { code: "SEN", name: "SensorAgent",      desc: "Calidad señales · 6 sensores",    status: agent?.agents?.sensor     ?? "—" },
              { code: "IND", name: "IndustrialAgent",  desc: "Lean + costos + ODS",             status: agent?.agents?.industrial ?? "—" },
            ] as a}
              <div class="flex items-center gap-3 p-2 rounded-md bg-white/[0.02] border border-white/[0.04]">
                <span class="w-7 h-7 rounded flex items-center justify-center text-[10px] font-mono font-bold bg-sky-500/10 text-sky-400 shrink-0">{a.code}</span>
                <div class="flex-1 min-w-0">
                  <div class="text-[11px] font-medium text-slate-200">{a.name}</div>
                  <div class="text-[10px] text-slate-500">{a.desc}</div>
                </div>
                <span class="text-[10px] font-mono uppercase {decisionColor(a.status)}">{a.status}</span>
              </div>
            {/each}
          </div>

          <button onclick={runCycle} class="w-full py-2 text-[11px] rounded-md border border-sky-500/30 bg-sky-500/[0.05] hover:bg-sky-500/[0.1] text-sky-400 font-medium transition-colors">
            Ejecutar ciclo único
          </button>
        </div>

        <!-- Log de decisiones -->
        <div class="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5">
          <div class="flex items-center justify-between mb-4">
            <div>
              <div class="text-[11px] font-medium tracking-wider uppercase text-slate-500">Log de decisiones</div>
              <div class="text-[10px] text-slate-600 mt-0.5">Últimos {agentLog.length} ciclos</div>
            </div>
          </div>

          {#if agentLog.length === 0}
            <div class="text-center py-12">
              <div class="text-[12px] text-slate-500 mb-1">Sin actividad registrada</div>
              <div class="text-[10px] text-slate-600">Inicia el agente para ver decisiones en tiempo real</div>
            </div>
          {:else}
            <div class="space-y-1.5" style="font-family:'JetBrains Mono',monospace">
              {#each agentLog as entry, i}
                <div class="flex gap-3 text-[11px] p-1.5 rounded hover:bg-white/[0.02] {i === 0 ? '' : 'opacity-70'}">
                  <span class="text-slate-600 w-12 shrink-0">{entry.ts}</span>
                  <span class="text-slate-500 w-10 shrink-0">#{entry.cycle}</span>
                  <span class="{decisionColor(entry.decision)} w-16 uppercase shrink-0">{entry.decision}</span>
                  <span class="text-slate-400 truncate">{entry.issue}</span>
                </div>
              {/each}
            </div>
          {/if}

          <!-- Diagrama estados -->
          <div class="mt-5 pt-4 border-t border-white/[0.06]">
            <div class="text-[10px] font-medium tracking-wider uppercase text-slate-500 mb-2.5">Máquina de estados</div>
            <div class="flex items-center flex-wrap gap-1 text-[10px]" style="font-family:'JetBrains Mono',monospace">
              {#each ["IDLE", "MONITORING", "ANALYZING", "DECIDING"] as node, i}
                <span class="px-2 py-1 rounded border border-white/[0.06] bg-white/[0.02] text-slate-400 {agent?.running && node === 'MONITORING' ? '!border-sky-500/40 !bg-sky-500/[0.06] !text-sky-400' : ''}">{node}</span>
                {#if i < 3}<span class="text-slate-600">→</span>{/if}
              {/each}
            </div>
            <div class="flex flex-col gap-1 mt-2 ml-12 text-[10px] text-slate-500" style="font-family:'JetBrains Mono',monospace">
              <div>├── ALERTING <span class="text-slate-600">→ Telegram push</span></div>
              <div>└── REPORTING <span class="text-slate-600">→ PDF + Telegram</span></div>
            </div>
          </div>
        </div>
      </div>
    {/if}

  </main>

  <!-- Footer -->
  <footer class="border-t border-white/[0.04] mt-8">
    <div class="mx-auto max-w-7xl px-6 py-4 flex items-center justify-between text-[10px] text-slate-600">
      <div>AguaMind OS · Hackathon UNIAJC 2026</div>
      <div class="flex items-center gap-3">
        <span>Datos: Aristizábal &amp; Largacha (2025)</span>
        <span class="text-slate-700">·</span>
        <span>Arias Montoya et al. (2024)</span>
      </div>
    </div>
  </footer>
</div>

<style>
  :global(html), :global(body) {
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  /* Tema oscuro (default) */
  :global(html) { --am-bg: #0a0e14; --am-text: #e2e8f0; }
  :global(body) { background: #0a0e14; }
  .am-root { background: #0a0e14; color: #e2e8f0; }

  /* Tema claro */
  :global(html.light) { --am-bg: #f8fafc; --am-text: #0f172a; }
  :global(html.light body) { background: #f8fafc; }
  :global(html.light) .am-root { background: #f8fafc; color: #0f172a; }

  /* Header */
  :global(html.light) .am-root header { background: rgba(248, 250, 252, 0.9); border-color: rgba(15, 23, 42, 0.08); }

  /* Cards y bordes */
  :global(html.light) .am-root .border-white\/\[0\.06\] { border-color: rgba(15, 23, 42, 0.08); }
  :global(html.light) .am-root .border-white\/\[0\.04\] { border-color: rgba(15, 23, 42, 0.05); }
  :global(html.light) .am-root .border-white\/10        { border-color: rgba(15, 23, 42, 0.10); }
  :global(html.light) .am-root .border-white\/20        { border-color: rgba(15, 23, 42, 0.18); }
  :global(html.light) .am-root .bg-white\/\[0\.02\]      { background: rgba(15, 23, 42, 0.02); }
  :global(html.light) .am-root .bg-white\/\[0\.03\]      { background: rgba(15, 23, 42, 0.03); }
  :global(html.light) .am-root .bg-white\/\[0\.04\]      { background: rgba(15, 23, 42, 0.04); }
  :global(html.light) .am-root .bg-white\/\[0\.07\]      { background: rgba(15, 23, 42, 0.07); }
  :global(html.light) .am-root .bg-white\/5             { background: rgba(15, 23, 42, 0.04); }
  :global(html.light) .am-root .bg-white\/10            { background: rgba(15, 23, 42, 0.06); }
  :global(html.light) .am-root .hover\:bg-white\/\[0\.04\]:hover { background: rgba(15, 23, 42, 0.05); }
  :global(html.light) .am-root .hover\:bg-white\/\[0\.07\]:hover { background: rgba(15, 23, 42, 0.07); }

  /* Tank background en modo claro */
  :global(html.light) .am-root .bg-\[\#060a10\] { background: #e2e8f0; }
  :global(html.light) .am-root .bg-\[\#0a0e14\] { background: #f8fafc; }

  /* Texto invertido para modo claro */
  :global(html.light) .am-root .text-white      { color: #0f172a; }
  :global(html.light) .am-root .text-slate-100  { color: #1e293b; }
  :global(html.light) .am-root .text-slate-200  { color: #334155; }
  :global(html.light) .am-root .text-slate-300  { color: #475569; }
  :global(html.light) .am-root .text-slate-400  { color: #64748b; }
  :global(html.light) .am-root .text-slate-500  { color: #475569; }
  :global(html.light) .am-root .text-slate-600  { color: #64748b; }

  /* Drop-shadow para tanques en modo claro */
  :global(html.light) .am-root .drop-shadow-md { filter: drop-shadow(0 1px 2px rgba(0,0,0,0.3)); }

  /* Header sticky */
  :global(html.light) .am-root header.sticky { background: rgba(248, 250, 252, 0.95); }
</style>
