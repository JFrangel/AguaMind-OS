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
  let tab = $state<"dashboard" | "history" | "industrial" | "agent" | "mitigation">("dashboard");
  let valves = $state<any>(null);
  let mitigationHistory = $state<any[]>([]);
  let impact = $state<any>(null);
  let leaderboard = $state<any[]>([]);
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

  async function fetchMitigation() {
    try {
      const [v, h, i, l] = await Promise.all([
        fetch("/api/water?endpoint=mitigate/valves").then(r => r.json()),
        fetch("/api/water?endpoint=mitigate/history&limit=10").then(r => r.json()),
        fetch("/api/water?endpoint=mitigate/impact").then(r => r.json()),
        fetch("/api/water?endpoint=leaderboard").then(r => r.json()),
      ]);
      if (v.data)  valves = v.data;
      if (h.data)  mitigationHistory = h.data.actions ?? [];
      if (i.data)  impact = i.data;
      if (l.data)  leaderboard = l.data.buildings ?? [];
    } catch {}
  }

  async function executeAutoMitigation(trigger: string) {
    try {
      await fetch("/api/water?endpoint=mitigate/auto", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ trigger, severity: "critical" }),
      });
      await fetchMitigation();
    } catch {}
  }

  async function toggleValve(valveId: string, currentState: string) {
    const action = currentState === "open" ? "close" : "open";
    try {
      await fetch(`/api/water?endpoint=mitigate/valve/${action}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ valve_id: valveId, reason: "manual_dashboard" }),
      });
      await fetchMitigation();
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
    await fetchMitigation();
    interval = setInterval(async () => {
      if (liveMode) { await fetchReading(); await fetchAgent(); await fetchMitigation(); }
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
        <div class="relative w-10 h-10 rounded-xl bg-gradient-to-br from-sky-400 via-sky-500 to-cyan-600 flex items-center justify-center shadow-lg shadow-sky-500/20">
          <svg viewBox="0 0 24 24" fill="none" class="w-5 h-5 text-white" stroke="currentColor" stroke-width="2.2">
            <path d="M12 2.5C12 2.5 6 9 6 14a6 6 0 0012 0c0-5-6-11.5-6-11.5z" stroke-linejoin="round"/>
          </svg>
          <span class="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-emerald-400 ring-2 ring-[#0a0e14] animate-pulse"></span>
        </div>
        <div class="leading-tight">
          <h1 class="text-[15px] font-semibold tracking-tight text-white flex items-center gap-1.5">
            AguaMind <span class="text-sky-400 font-light">OS</span>
          </h1>
          <p class="text-[11px] text-slate-500 mt-0.5 tracking-wide">UNIAJC Sede Sur · Gestión Hídrica Inteligente</p>
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
    <div class="mx-auto max-w-7xl px-6 flex gap-1">
      {#each [
        ["dashboard",  "Operación",         "01"],
        ["history",    "Tendencias",        "02"],
        ["industrial", "Gestión Industrial","03"],
        ["agent",      "Inteligencia",      "04"],
        ["mitigation", "Mapa del Campus",   "05"],
      ] as [key, label, num]}
        <button
          onclick={() => { tab = key as typeof tab; if (key === "history") fetchHistory(); }}
          class="group relative px-4 py-3 text-[12px] font-medium tracking-tight border-b-2 transition-all -mb-px flex items-center gap-2
            {tab === key ? 'border-sky-500 text-white' : 'border-transparent text-slate-500 hover:text-slate-300 hover:border-white/10'}"
        >
          <span class="text-[9px] font-mono opacity-60">{num}</span>
          <span>{label}</span>
        </button>
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

      <!-- Sección Indicadores de Desempeño -->
      <div class="mb-5">
        <div class="flex items-baseline justify-between mb-3">
          <div>
            <h2 class="text-[13px] font-semibold text-white tracking-tight">Indicadores de Desempeño</h2>
            <p class="text-[11px] text-slate-500 mt-0.5">KPIs en tiempo real · actualización cada 10 segundos</p>
          </div>
          <span class="text-[10px] font-mono text-slate-600">live</span>
        </div>
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {#each Object.entries(kpis) as [name, kpi]}
            {@const labels = {IEH: "Eficiencia Hídrica", TPP: "Pérdidas Proceso", CPE: "Consumo Estudiante", ICA: "Calidad Agua"}}
            <div class="group relative overflow-hidden rounded-2xl border border-white/[0.06] bg-gradient-to-br from-white/[0.02] to-white/[0.005] hover:from-white/[0.04] hover:to-white/[0.01] transition-all duration-300 p-5">
              <!-- Barra superior gradiente -->
              <div class="absolute top-0 left-0 right-0 h-[2px]" style="background:linear-gradient(90deg, transparent, {statusHex(kpi.status)}, transparent)"></div>

              <!-- Pulso de fondo si crítico -->
              {#if kpi.status === 'critical'}
                <div class="absolute inset-0 opacity-[0.04]" style="background:radial-gradient(circle at 50% 0%, {statusHex(kpi.status)}, transparent 70%)"></div>
              {/if}

              <div class="relative">
                <div class="flex items-center justify-between mb-3">
                  <div>
                    <div class="text-[10px] font-mono font-bold tracking-[0.15em] text-slate-400">{name}</div>
                    <div class="text-[10px] text-slate-600 mt-0.5">{labels[name as keyof typeof labels] ?? ""}</div>
                  </div>
                  <span class="text-[9px] font-medium px-2 py-0.5 rounded-full uppercase tracking-wider border"
                        style="color:{statusHex(kpi.status)};background:{statusHex(kpi.status)}10;border-color:{statusHex(kpi.status)}30">{kpi.status === 'ok' ? 'óptimo' : kpi.status === 'warning' ? 'alerta' : 'crítico'}</span>
                </div>
                <div class="flex items-baseline gap-1">
                  <span class="text-[32px] font-semibold tracking-tighter leading-none text-white" style="font-family:'JetBrains Mono','SF Mono',monospace">
                    {fmt(kpi.value, name === "CPE" ? 2 : 1)}
                  </span>
                  <span class="text-[12px] text-slate-500 font-normal">{kpi.unit ?? ""}</span>
                </div>
                <div class="text-[10px] text-slate-500 mt-2 font-mono">meta {kpi.target ?? ""}</div>
              </div>
            </div>
          {/each}
        </div>
      </div>

      <!-- Sección Almacenamiento + Sensores -->
      <div class="mb-3">
        <div class="flex items-baseline justify-between mb-3">
          <div>
            <h2 class="text-[13px] font-semibold text-white tracking-tight">Almacenamiento y Sensores</h2>
            <p class="text-[11px] text-slate-500 mt-0.5">Tanques principales · Variables monitoreadas</p>
          </div>
        </div>
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

      <!-- Sección Consumo por Zona -->
      <div class="mb-3 mt-6">
        <div class="flex items-baseline justify-between mb-3">
          <div>
            <h2 class="text-[13px] font-semibold text-white tracking-tight">Distribución del Consumo</h2>
            <p class="text-[11px] text-slate-500 mt-0.5">Caudal por zona del campus · {Object.keys(reading.zones ?? {}).length} zonas activas</p>
          </div>
          <span class="text-[10px] font-mono text-slate-600">L/min</span>
        </div>
      </div>

      <!-- Consumo por zonas -->
      <div class="rounded-2xl border border-white/[0.06] bg-gradient-to-br from-white/[0.02] to-white/[0.005] p-5 mb-5">
        <div class="flex items-center justify-between mb-4">
          <div class="text-[10px] font-mono tracking-[0.15em] uppercase text-slate-500">Mapa térmico</div>
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

      <!-- Sección Eventos y Alertas -->
      <div class="mb-3 mt-6">
        <div class="flex items-baseline justify-between mb-3">
          <div>
            <h2 class="text-[13px] font-semibold text-white tracking-tight">Eventos y Alertas</h2>
            <p class="text-[11px] text-slate-500 mt-0.5">Notificaciones del sistema · Última hora</p>
          </div>
        </div>
      </div>

      <!-- Alertas -->
      {#if alerts.length > 0}
        <div class="rounded-2xl border border-white/[0.06] bg-gradient-to-br from-white/[0.02] to-white/[0.005] p-5">
          <div class="flex items-center justify-between mb-4">
            <div class="text-[10px] font-mono tracking-[0.15em] uppercase text-slate-500">Activas ahora</div>
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

          <!-- 5 agentes -->
          <div class="text-[10px] font-medium tracking-wider uppercase text-slate-500 mb-2">5 Agentes Especializados</div>
          <div class="space-y-1.5 mb-4">
            {#each [
              { code: "ORC", name: "Orchestrator",     desc: "Coordinador general · consolida",     status: agent?.last_decision ?? "—" },
              { code: "SYS", name: "SystemsAgent",     desc: "KPIs IEH/TPP/CPE · IsolationForest",  status: agent?.agents?.systems    ?? "—" },
              { code: "SEN", name: "SensorAgent",      desc: "Validación 6 sensores · calidad señal", status: agent?.agents?.sensor   ?? "—" },
              { code: "IND", name: "IndustrialAgent",  desc: "Lean (7 mudas) · ODS · costos",       status: agent?.agents?.industrial ?? "—" },
              { code: "MIT", name: "MitigationAgent",  desc: "Acción autónoma · electroválvulas",   status: (agent?.last_decision && agent.last_decision !== "ok") ? "execute" : "idle" },
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

    <!-- ════════════════════════════════════════════════════════════════════ -->
    <!-- TAB 5: MITIGACIÓN -->
    <!-- ════════════════════════════════════════════════════════════════════ -->
    {:else if tab === "mitigation"}

      <!-- Métricas de impacto -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
        {#each [
          { label: "Litros ahorrados",   value: impact?.liters_saved_formatted ?? "0 L",     accent: "#10b981", code: "L" },
          { label: "Dinero evitado",     value: impact?.cop_saved_formatted ?? "$0 COP",     accent: "#0ea5e9", code: "$" },
          { label: "CO₂ evitado",        value: impact?.co2_kg_formatted ?? "0 kg",          accent: "#34d399", code: "C" },
          { label: "Acciones tomadas",   value: String(impact?.actions_taken ?? 0),          accent: "#a78bfa", code: "A" },
        ] as m}
          <div class="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
            <div class="flex items-center gap-2 mb-2">
              <span class="w-5 h-5 rounded-md flex items-center justify-center text-[11px] font-mono font-bold" style="background:{m.accent}1A;color:{m.accent}">{m.code}</span>
              <span class="text-[10px] font-medium tracking-wider uppercase text-slate-500">{m.label}</span>
            </div>
            <div class="text-[20px] font-semibold tracking-tight text-white" style="font-family:'JetBrains Mono',monospace">{m.value}</div>
          </div>
        {/each}
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-3 mb-3">

        <!-- Mapa SVG del campus (2 columnas) -->
        <div class="lg:col-span-2 rounded-xl border border-white/[0.06] bg-white/[0.02] p-5">
          <div class="flex items-center justify-between mb-3">
            <div>
              <div class="text-[11px] font-medium tracking-wider uppercase text-slate-500">Mapa del Campus · UNIAJC Sede Sur</div>
              <div class="text-[10px] text-slate-600 mt-0.5">Localización en tiempo real de cada nodo · clic para abrir/cerrar válvula</div>
            </div>
            <div class="flex gap-2 text-[10px]">
              <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-emerald-400"></span>OK</span>
              <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-amber-400"></span>Alerta</span>
              <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-red-400"></span>Crítico</span>
            </div>
          </div>

          <!-- SVG MAP -->
          <svg viewBox="0 0 800 480" class="w-full h-auto rounded-lg" style="background:linear-gradient(135deg,rgba(14,165,233,0.06) 0%,rgba(99,102,241,0.04) 100%)">
            <!-- Grid background -->
            <defs>
              <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(148,163,184,0.08)" stroke-width="1"/>
              </pattern>
              <radialGradient id="alertPulse">
                <stop offset="0%" stop-color="#ef4444" stop-opacity="0.6"/>
                <stop offset="100%" stop-color="#ef4444" stop-opacity="0"/>
              </radialGradient>
            </defs>
            <rect width="800" height="480" fill="url(#grid)"/>

            <!-- Río Pance / Cauca al sur (recibe efluente PTAR) -->
            <path d="M 0 440 Q 200 450 400 435 T 800 445 L 800 480 L 0 480 Z" fill="rgba(56,189,248,0.10)" stroke="rgba(56,189,248,0.4)" stroke-width="1"/>
            <text x="20" y="460" fill="rgba(56,189,248,0.7)" font-size="10" font-family="JetBrains Mono">río Pance / Cauca</text>
            <text x="20" y="473" fill="rgba(56,189,248,0.5)" font-size="8" font-family="JetBrains Mono">Resolución 0631/2015 · DBO ≤ 90 mg/L</text>

            <!-- ALJIBES (centro-sur del campus) -->
            <g>
              <circle cx="320" cy="385" r="14" fill="rgba(125,211,252,0.15)" stroke="#7dd3fc" stroke-width="2"/>
              <text x="320" y="389" text-anchor="middle" fill="#7dd3fc" font-size="10" font-family="JetBrains Mono" font-weight="bold">A1</text>
            </g>
            <g>
              <circle cx="380" cy="385" r="14" fill="rgba(125,211,252,0.15)" stroke="#7dd3fc" stroke-width="2"/>
              <text x="380" y="389" text-anchor="middle" fill="#7dd3fc" font-size="10" font-family="JetBrains Mono" font-weight="bold">A2</text>
            </g>
            <text x="350" y="375" text-anchor="middle" fill="rgba(125,211,252,0.6)" font-size="9" font-family="JetBrains Mono">aljibes</text>

            <!-- PTAP -->
            <g>
              <rect x="320" y="340" width="100" height="60" rx="6" fill="rgba(99,102,241,0.15)" stroke="#818cf8" stroke-width="2"/>
              <text x="370" y="365" text-anchor="middle" fill="#818cf8" font-size="11" font-family="Inter" font-weight="bold">PTAP</text>
              <text x="370" y="382" text-anchor="middle" fill="rgba(129,140,248,0.7)" font-size="9">3 filtros · 2011</text>
              <text x="370" y="396" text-anchor="middle" fill="rgba(129,140,248,0.6)" font-size="8" font-family="JetBrains Mono">113.56 L/min</text>
            </g>

            <!-- Tanques -->
            <g>
              <rect x="480" y="320" width="70" height="80" rx="4" fill="rgba(34,197,94,0.10)" stroke="#22c55e" stroke-width="2"/>
              <rect x="480" y="320" width="70" height="80" rx="4" fill="rgba(34,197,94,0.30)" style="clip-path: inset({100 - (reading?.tank_a_pct ?? 65)}% 0 0 0)"/>
              <text x="515" y="355" text-anchor="middle" fill="#22c55e" font-size="11" font-family="Inter" font-weight="bold">Tank A</text>
              <text x="515" y="372" text-anchor="middle" fill="white" font-size="14" font-family="JetBrains Mono" font-weight="bold">{fmt(reading?.tank_a_pct, 0)}%</text>
              <text x="515" y="390" text-anchor="middle" fill="rgba(34,197,94,0.7)" font-size="8">36k L</text>
            </g>
            <g>
              <rect x="600" y="340" width="60" height="60" rx="4" fill="rgba(56,189,248,0.10)" stroke="#38bdf8" stroke-width="2"/>
              <rect x="600" y="340" width="60" height="60" rx="4" fill="rgba(56,189,248,0.30)" style="clip-path: inset({100 - (reading?.tank_b_pct ?? 70)}% 0 0 0)"/>
              <text x="630" y="370" text-anchor="middle" fill="#38bdf8" font-size="10" font-family="Inter" font-weight="bold">Tank B</text>
              <text x="630" y="387" text-anchor="middle" fill="white" font-size="13" font-family="JetBrains Mono" font-weight="bold">{fmt(reading?.tank_b_pct, 0)}%</text>
            </g>

            <!-- Conexiones tuberías agua potable -->
            <line x1="332" y1="380" x2="320" y2="370" stroke="#7dd3fc" stroke-width="2" stroke-dasharray="4 3" opacity="0.6"/>
            <line x1="380" y1="370" x2="370" y2="370" stroke="#7dd3fc" stroke-width="2" stroke-dasharray="4 3" opacity="0.6"/>
            <line x1="420" y1="370" x2="480" y2="360" stroke="#818cf8" stroke-width="2" opacity="0.6"/>
            <line x1="550" y1="360" x2="600" y2="370" stroke="#22c55e" stroke-width="2" opacity="0.6"/>

            <!-- Edificios del campus -->
            <!-- Bloque A -->
            <g class="cursor-pointer" onclick={() => executeAutoMitigation("leak")}>
              <rect x="100" y="120" width="120" height="80" rx="6" fill="rgba(168,85,247,0.10)" stroke={reading?.vibration ? "#ef4444" : "#a855f7"} stroke-width="2"/>
              {#if reading?.vibration}
                <circle cx="160" cy="160" r="50" fill="url(#alertPulse)">
                  <animate attributeName="r" from="20" to="60" dur="2s" repeatCount="indefinite"/>
                  <animate attributeName="opacity" from="0.6" to="0" dur="2s" repeatCount="indefinite"/>
                </circle>
              {/if}
              <text x="160" y="155" text-anchor="middle" fill={reading?.vibration ? "#fca5a5" : "#a855f7"} font-size="13" font-family="Inter" font-weight="bold">Bloque A</text>
              <text x="160" y="172" text-anchor="middle" fill="rgba(168,85,247,0.6)" font-size="9">Aulas + baños</text>
              <circle cx="195" cy="135" r="4" fill={reading?.vibration ? "#ef4444" : "#10b981"}>
                {#if reading?.vibration}<animate attributeName="opacity" from="1" to="0.3" dur="1s" repeatCount="indefinite"/>{/if}
              </circle>
            </g>

            <!-- Alameda -->
            <g>
              <rect x="280" y="100" width="140" height="100" rx="6" fill="rgba(245,158,11,0.08)" stroke="#f59e0b" stroke-width="2"/>
              <text x="350" y="145" text-anchor="middle" fill="#f59e0b" font-size="13" font-family="Inter" font-weight="bold">Alameda</text>
              <text x="350" y="162" text-anchor="middle" fill="rgba(245,158,11,0.6)" font-size="9">Aulas + administración</text>
              <circle cx="405" cy="115" r="4" fill="#10b981"/>
            </g>

            <!-- Cafetería -->
            <g>
              <rect x="480" y="120" width="80" height="60" rx="6" fill="rgba(249,115,22,0.10)" stroke="#f97316" stroke-width="2"/>
              <text x="520" y="150" text-anchor="middle" fill="#f97316" font-size="11" font-family="Inter" font-weight="bold">Cafetería</text>
              <text x="520" y="166" text-anchor="middle" fill="rgba(249,115,22,0.6)" font-size="8">240 L/día</text>
              <circle cx="550" cy="135" r="3.5" fill="#10b981"/>
            </g>

            <!-- Laboratorios -->
            <g>
              <rect x="600" y="120" width="100" height="60" rx="6" fill="rgba(96,165,250,0.10)" stroke="#60a5fa" stroke-width="2"/>
              <text x="650" y="150" text-anchor="middle" fill="#60a5fa" font-size="11" font-family="Inter" font-weight="bold">Laboratorios</text>
              <text x="650" y="166" text-anchor="middle" fill="rgba(96,165,250,0.6)" font-size="8">64 L/día</text>
              <circle cx="690" cy="135" r="3.5" fill="#10b981"/>
            </g>

            <!-- Cancha + Riego -->
            <g class="cursor-pointer">
              <rect x="100" y="240" width="240" height="60" rx="6" fill="rgba(34,197,94,0.08)" stroke="#22c55e" stroke-width="2" stroke-dasharray="6 3"/>
              <text x="220" y="270" text-anchor="middle" fill="#22c55e" font-size="12" font-family="Inter" font-weight="bold">Cancha + Jardines</text>
              <text x="220" y="287" text-anchor="middle" fill="rgba(34,197,94,0.6)" font-size="9">Riego ~4,000 L/día</text>
              <circle cx="320" cy="255" r="3.5" fill={(reading?.zones?.["Riego/Cancha"] ?? 0) > 6 ? "#f59e0b" : "#10b981"}/>
            </g>

            <!-- Limpieza -->
            <g>
              <rect x="380" y="240" width="120" height="60" rx="6" fill="rgba(148,163,184,0.10)" stroke="#94a3b8" stroke-width="2"/>
              <text x="440" y="270" text-anchor="middle" fill="#94a3b8" font-size="11" font-family="Inter" font-weight="bold">Limpieza</text>
              <text x="440" y="287" text-anchor="middle" fill="rgba(148,163,184,0.6)" font-size="9">3,000 L/día</text>
              <circle cx="485" cy="255" r="3.5" fill="#10b981"/>
            </g>

            <!-- ═══ PTAR ALAMEDA + ENTRADA ═══ -->
            <!-- Bajantes residuales desde edificios → colector → PTARs -->
            <line x1="160" y1="200" x2="160" y2="320" stroke="#fbbf24" stroke-width="1.5" stroke-dasharray="3 2" opacity="0.5"/>
            <line x1="350" y1="200" x2="350" y2="320" stroke="#fbbf24" stroke-width="1.5" stroke-dasharray="3 2" opacity="0.5"/>
            <line x1="520" y1="180" x2="520" y2="320" stroke="#fbbf24" stroke-width="1.5" stroke-dasharray="3 2" opacity="0.5"/>
            <line x1="650" y1="180" x2="650" y2="320" stroke="#fbbf24" stroke-width="1.5" stroke-dasharray="3 2" opacity="0.5"/>

            <!-- Colector residuales horizontal -->
            <line x1="80" y1="320" x2="700" y2="320" stroke="#f59e0b" stroke-width="2.5" opacity="0.5" stroke-dasharray="5 3"/>
            <text x="80" y="315" fill="rgba(245,158,11,0.7)" font-size="8" font-family="JetBrains Mono">colector aguas residuales</text>

            <!-- PTAR Alameda (oeste) -->
            <g class="cursor-pointer">
              <rect x="80" y="400" width="120" height="36" rx="6" fill="rgba(245,158,11,0.10)" stroke="#f59e0b" stroke-width="2" stroke-dasharray="3 2"/>
              <text x="140" y="416" text-anchor="middle" fill="#f59e0b" font-size="10" font-family="Inter" font-weight="bold">PTAR Alameda</text>
              <text x="140" y="429" text-anchor="middle" fill="rgba(245,158,11,0.6)" font-size="8">cap. 1,000 est · módulo 1</text>
              <circle cx="190" cy="408" r="3.5" fill="#f59e0b"/>
              <!-- Conexión desde colector -->
              <line x1="140" y1="320" x2="140" y2="400" stroke="#f59e0b" stroke-width="2" opacity="0.6" stroke-dasharray="4 2"/>
            </g>

            <!-- PTAR Entrada (este) -->
            <g class="cursor-pointer">
              <rect x="580" y="400" width="120" height="36" rx="6" fill="rgba(245,158,11,0.10)" stroke="#f59e0b" stroke-width="2" stroke-dasharray="3 2"/>
              <text x="640" y="416" text-anchor="middle" fill="#f59e0b" font-size="10" font-family="Inter" font-weight="bold">PTAR Entrada</text>
              <text x="640" y="429" text-anchor="middle" fill="rgba(245,158,11,0.6)" font-size="8">cap. 1,000 est · módulo 2</text>
              <circle cx="690" cy="408" r="3.5" fill="#f59e0b"/>
              <!-- Conexión desde colector -->
              <line x1="640" y1="320" x2="640" y2="400" stroke="#f59e0b" stroke-width="2" opacity="0.6" stroke-dasharray="4 2"/>
            </g>

            <!-- Vertimiento de PTAR al río -->
            <line x1="140" y1="436" x2="140" y2="460" stroke="#fbbf24" stroke-width="2" opacity="0.5"/>
            <line x1="640" y1="436" x2="640" y2="460" stroke="#fbbf24" stroke-width="2" opacity="0.5"/>

            <!-- Etiqueta capacidad -->
            <text x="320" y="375" fill="rgba(245,158,11,0.6)" font-size="9" font-family="JetBrains Mono">⚠ capacidad PTAR: 2,000 est · campus: 8,234 usuarios</text>

            <!-- Leyenda -->
            <text x="20" y="30" fill="rgba(148,163,184,0.7)" font-size="10" font-family="Inter" font-weight="600">UNIAJC Sede Sur · 38,755 m²</text>
            <text x="20" y="45" fill="rgba(148,163,184,0.5)" font-size="9" font-family="JetBrains Mono">8,234 usuarios · 219 disp. hidráulicos</text>

            <!-- Leyenda flujos -->
            <g transform="translate(540, 25)">
              <line x1="0" y1="0" x2="20" y2="0" stroke="#7dd3fc" stroke-width="2"/>
              <text x="24" y="3" fill="rgba(148,163,184,0.7)" font-size="8" font-family="JetBrains Mono">potable</text>
              <line x1="80" y1="0" x2="100" y2="0" stroke="#f59e0b" stroke-width="2" stroke-dasharray="3 2"/>
              <text x="104" y="3" fill="rgba(148,163,184,0.7)" font-size="8" font-family="JetBrains Mono">residual</text>
              <line x1="160" y1="0" x2="180" y2="0" stroke="#22c55e" stroke-width="2" stroke-dasharray="6 3"/>
              <text x="184" y="3" fill="rgba(148,163,184,0.7)" font-size="8" font-family="JetBrains Mono">riego</text>
            </g>
          </svg>

          <div class="mt-3 flex flex-wrap gap-1.5">
            {#each ["leak", "peak_irrigation", "turbidity", "tank_overflow", "phreatic_low"] as trigger}
              <button
                onclick={() => executeAutoMitigation(trigger)}
                class="px-2.5 py-1 rounded-md text-[10px] border border-white/10 bg-white/[0.04] hover:bg-amber-500/10 hover:border-amber-500/40 hover:text-amber-400 text-slate-300 transition-colors font-mono"
              >▶ {trigger}</button>
            {/each}
          </div>
        </div>

        <!-- Electroválvulas -->
        <div class="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5">
          <div class="text-[11px] font-medium tracking-wider uppercase text-slate-500 mb-3">Electroválvulas</div>
          <div class="space-y-1.5">
            {#each Object.entries(valves?.valves ?? {}) as [vid, v]}
              {@const valve = v as any}
              <button
                onclick={() => toggleValve(vid, valve.state)}
                class="w-full flex items-center justify-between p-2 rounded-md border bg-white/[0.02] hover:bg-white/[0.04] transition-colors
                  {valve.state === 'closed' ? 'border-red-500/30' : 'border-white/[0.06]'}"
              >
                <div class="text-left min-w-0 flex-1">
                  <div class="text-[10px] font-mono font-bold text-slate-300">{vid}</div>
                  <div class="text-[10px] text-slate-500 truncate">{valve.name}</div>
                </div>
                <span class="text-[9px] font-mono font-bold uppercase shrink-0 px-1.5 py-0.5 rounded
                  {valve.state === 'closed' ? 'bg-red-500/20 text-red-400' : 'bg-emerald-500/20 text-emerald-400'}">
                  {valve.state}
                </span>
              </button>
            {/each}
          </div>

          <div class="mt-4 pt-3 border-t border-white/[0.06]">
            <div class="text-[10px] font-medium tracking-wider uppercase text-slate-500 mb-2">Bomba principal</div>
            <div class="text-[11px] font-mono">
              <div>Estado: <span class="{valves?.pump?.state === 'auto' ? 'text-emerald-400' : 'text-amber-400'}">{valves?.pump?.state ?? '—'}</span></div>
              <div>Presión: <span class="text-white">{valves?.pump?.pressure_pct ?? 100}%</span></div>
            </div>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-3">

        <!-- Historial de mitigaciones -->
        <div class="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5">
          <div class="text-[11px] font-medium tracking-wider uppercase text-slate-500 mb-3">Historial de Acciones</div>
          {#if mitigationHistory.length === 0}
            <div class="text-center py-6 text-[11px] text-slate-500">Sin acciones registradas — ejecuta una mitigación para ver historial</div>
          {:else}
            <div class="space-y-2">
              {#each mitigationHistory.slice(0, 6) as h}
                <div class="text-[11px] p-2 rounded-md border border-white/[0.04] bg-white/[0.02]">
                  <div class="flex justify-between items-start mb-1">
                    <span class="font-mono uppercase text-[10px] {h.type === 'auto' ? 'text-amber-400' : h.type === 'close' ? 'text-red-400' : 'text-sky-400'}">{h.type}</span>
                    <span class="font-mono text-[9px] text-slate-500">{h.timestamp?.slice(11, 19)}</span>
                  </div>
                  <div class="text-slate-300 text-[11px]">{h.detail}</div>
                  {#if h.impact}
                    <div class="mt-1 text-[10px] text-emerald-400 font-mono">→ {h.impact.liters_saved?.toLocaleString()} L · ${h.impact.cop_saved?.toLocaleString()} COP</div>
                  {/if}
                </div>
              {/each}
            </div>
          {/if}
        </div>

        <!-- Smart Water Ledger / Ranking -->
        <div class="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5">
          <div class="flex items-center justify-between mb-3">
            <div>
              <div class="text-[11px] font-medium tracking-wider uppercase text-slate-500">Smart Water Ledger</div>
              <div class="text-[10px] text-slate-600 mt-0.5">Ranking mensual · Créditos hídricos por edificio</div>
            </div>
          </div>
          <div class="space-y-2">
            {#each leaderboard as b, i}
              {@const medals = ["1°", "2°", "3°", "4°", "5°"]}
              <div class="flex items-center gap-3 p-2 rounded-md {i === 0 ? 'bg-amber-500/[0.06] border border-amber-500/20' : 'bg-white/[0.02] border border-white/[0.04]'}">
                <span class="text-[12px] font-mono font-bold w-6 text-center {i === 0 ? 'text-amber-400' : 'text-slate-500'}">{medals[i] ?? `${i+1}°`}</span>
                <div class="flex-1 min-w-0">
                  <div class="text-[12px] font-medium text-white truncate">{b.name}</div>
                  <div class="text-[10px] text-slate-500 font-mono">{b.consumption_l_day?.toLocaleString()} L/día</div>
                </div>
                <span class="text-[14px] font-mono font-semibold {i === 0 ? 'text-amber-400' : 'text-sky-400'}">{b.credits}<span class="text-[9px] text-slate-500 ml-0.5 font-normal">cr</span></span>
              </div>
            {/each}
          </div>
          <div class="mt-3 pt-3 border-t border-white/[0.06] text-[10px] text-slate-500">
            <div>1 Crédito Hídrico = 1 m³ ahorrado vs línea base</div>
            <div class="mt-1">100 cr → mejora zona común · 500 cr → renovación · 1000 cr → proyecto</div>
          </div>
        </div>
      </div>
    {/if}

  </main>

  <!-- Footer -->
  <footer class="border-t border-white/[0.04] mt-12">
    <div class="mx-auto max-w-7xl px-6 py-6">
      <div class="flex items-start justify-between mb-4">
        <div>
          <div class="flex items-center gap-2 mb-2">
            <div class="w-6 h-6 rounded-md bg-gradient-to-br from-sky-400 to-cyan-600 flex items-center justify-center">
              <svg viewBox="0 0 24 24" fill="none" class="w-3.5 h-3.5 text-white" stroke="currentColor" stroke-width="2.2">
                <path d="M12 2.5C12 2.5 6 9 6 14a6 6 0 0012 0c0-5-6-11.5-6-11.5z" stroke-linejoin="round"/>
              </svg>
            </div>
            <span class="text-[12px] font-semibold text-white">AguaMind OS</span>
            <span class="text-[10px] text-slate-500 ml-1">v1.0</span>
          </div>
          <p class="text-[10px] text-slate-500 max-w-md leading-relaxed">
            Sistema inteligente de gestión hídrica · Caracterización + Estrategias de mitigación · Open source MIT
          </p>
        </div>
        <div class="text-right text-[10px] text-slate-500 space-y-1">
          <div class="text-slate-400 font-medium">Hackathon UNIAJC 2026</div>
          <div>Tecnología con Propósito · Inteligencia con Conciencia</div>
        </div>
      </div>
      <div class="border-t border-white/[0.04] pt-4 flex flex-wrap items-center justify-between gap-3 text-[10px] text-slate-600">
        <div class="flex items-center gap-3 flex-wrap">
          <span>Fuentes:</span>
          <span class="text-slate-500">Caycedo &amp; Jaramillo (2021)</span>
          <span class="text-slate-700">·</span>
          <span class="text-slate-500">Sánchez Sotelo (2021)</span>
          <span class="text-slate-700">·</span>
          <span class="text-slate-500">Gómez Mina (2022)</span>
          <span class="text-slate-700">·</span>
          <span class="text-slate-500">Aristizábal &amp; Largacha (2025)</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-mono">Res. 2115/2007</span>
          <span class="px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-mono">Res. 0631/2015</span>
        </div>
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
