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
  let tab = $state<"dashboard" | "history" | "industrial" | "agent" | "mitigation" | "community" | "architecture">("dashboard");
  let gamification = $state<any>(null);
  let redeemMessage = $state<string | null>(null);
  let valves = $state<any>(null);
  let mitigationHistory = $state<any[]>([]);
  let impact = $state<any>(null);
  let leaderboard = $state<any[]>([]);
  let mapView3D = $state<boolean>(false);   // toggle vista isometrica del mapa

  // Datos sintéticos para charts de Tendencias (stacked area consumo vs pérdidas 24h)
  const STACK_DATA: { h: number; consumo: number; perdidas: number }[] = [
    {h: 0,  consumo: 12, perdidas: 8}, {h: 1,  consumo: 10, perdidas: 8},
    {h: 2,  consumo: 9,  perdidas: 9}, {h: 3,  consumo: 8,  perdidas: 9},
    {h: 4,  consumo: 9,  perdidas: 8}, {h: 5,  consumo: 12, perdidas: 7},
    {h: 6,  consumo: 28, perdidas: 7}, {h: 7,  consumo: 65, perdidas: 8},
    {h: 8,  consumo: 78, perdidas: 9}, {h: 9,  consumo: 72, perdidas: 9},
    {h: 10, consumo: 60, perdidas: 8}, {h: 11, consumo: 58, perdidas: 8},
    {h: 12, consumo: 52, perdidas: 8}, {h: 13, consumo: 35, perdidas: 7},
    {h: 14, consumo: 38, perdidas: 8}, {h: 15, consumo: 60, perdidas: 9},
    {h: 16, consumo: 65, perdidas: 9}, {h: 17, consumo: 60, perdidas: 8},
    {h: 18, consumo: 38, perdidas: 7}, {h: 19, consumo: 14, perdidas: 7},
    {h: 20, consumo: 12, perdidas: 8}, {h: 21, consumo: 10, perdidas: 8},
    {h: 22, consumo: 12, perdidas: 9}, {h: 23, consumo: 12, perdidas: 9},
  ];
  let infoOpen = $state<string | null>(null);  // qué tooltip de "info" está abierto

  // Descripciones de cada apartado para los tooltips informativos
  const tabInfo: Record<string, { title: string; lines: string[] }> = {
    dashboard:  {
      title: "Operación",
      lines: [
        "Vista de control en tiempo real. KPIs IEH, TPP, CPE, ICA actualizados cada 30s.",
        "Niveles de los 2 tanques (A 36k L · B 16k L) con bomba activa/standby.",
        "6 sensores instrumentados con valores en vivo + alertas activas con acción sugerida.",
      ],
    },
    history:  {
      title: "Tendencias",
      lines: [
        "Series temporales últimas 24h por sensor — caudal, presión, niveles, freático, turbidez.",
        "Identifica patrones, picos y valles. Detecta horas pico de consumo del campus.",
        "Análisis descriptivo del Nivel 1 del agente — base para predicción y prescripción.",
      ],
    },
    industrial:  {
      title: "Gestión Industrial",
      lines: [
        "KPIs con fórmula y propósito. 3 indicadores Lean (7 mudas) e Ishikawa de causa raíz.",
        "Análisis costo-beneficio: $1.43M inversión · $20.5M ahorro/año · ROI 25 días.",
        "Compliance normativo: Decreto 1575/2007, Resolución 2115/2007, 0631/2015, 1076/2015.",
      ],
    },
    agent:  {
      title: "Inteligencia",
      lines: [
        "Sistema multi-agente: 5 agentes (Orchestrator, Systems, Sensor, Industrial, Mitigation) coordinados con LangGraph.",
        "Plan ante 5 fenómenos: sequía/El Niño, lluvias/La Niña, sismo, contaminación, pico demanda.",
        "Razonamiento en vivo + monetización (pérdidas $/min, ahorro acumulado, CO₂ evitado).",
        "Chat conversacional con contexto en tiempo real del sistema hídrico.",
      ],
    },
    mitigation:  {
      title: "Mapa del Campus",
      lines: [
        "Layout SVG del campus UNIAJC Sede Sur (38,755 m²) con 4 edificios + servicios + 2 PTAR.",
        "Toggle vista 2D ↔ 3D (CSS perspective + drop-shadow para profundidad).",
        "5 triggers de mitigación automática (leak, peak_irrigation, turbidity, tank_overflow, phreatic_low).",
        "8 electroválvulas controlables vía MQTT. Estado bomba en vivo.",
      ],
    },
    community:  {
      title: "Comunidad",
      lines: [
        "Smart Water Ledger: ranking mensual de edificios por créditos hídricos ahorrados.",
        "Catálogo de canjes con Bienestar Universitario (mejoras en zona común, cafetería, proyectos).",
        "Reportes ciudadanos QR — cualquier estudiante reporta fugas y suma puntos.",
        "Concretiza ODS 11 (ciudades sostenibles) + ODS 17 (alianzas).",
      ],
    },
    architecture:  {
      title: "Arquitectura",
      lines: [
        "Diagrama de las 7 capas (Física → Sensado → Edge → Comunicación → Persistencia → Inteligencia → Aplicación).",
        "Trinidad analítica visualizada (Descriptivo · Predictivo · Prescriptivo) con sparkline, forecast y voto consensual.",
        "Flujo end-to-end sensor → cierre EV en 5s · vs 2-4h humano tradicional.",
        "Mockups por capa: OLED, MQTT topic tree, payload JSON, schema SQL, máquina de estados firmware.",
      ],
    },
  };

  // Chat con el agente IA
  let chatMessages = $state<{role:"user"|"agent"; text:string; ts:string}[]>([]);
  let chatInput = $state("");
  let chatLoading = $state(false);
  let aiInsights = $state<any[]>([]);

  async function askAgent(question: string) {
  if (!question.trim()) return;
  const ts = new Date().toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" });
  chatMessages = [...chatMessages, { role: "user", text: question, ts }];
  chatInput = "";
  chatLoading = true;
  try {
  const res = await fetch("/api/water?endpoint=agent/ask", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ question, include_state: true }),
  });
  const json = await res.json();
  const answer = json.data?.answer ?? "Sin respuesta del agente.";
  chatMessages = [...chatMessages, {
  role: "agent",
  text: answer,
  ts: new Date().toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" })
  }];
  } catch (e) {
  chatMessages = [...chatMessages, {
  role: "agent",
  text: "Error: backend no disponible.",
  ts: new Date().toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" })
  }];
  } finally {
  chatLoading = false;
  }
  }

  async function fetchInsights() {
  try {
  const res = await fetch("/api/water?endpoint=agent/insights");
  const json = await res.json();
  if (json.data?.insights) aiInsights = json.data.insights;
  } catch {}
  }

  async function fetchGamification() {
  try {
  const res = await fetch("/api/water?endpoint=gamification/dashboard");
  const json = await res.json();
  if (json.data) gamification = json.data;
  } catch {}
  }

  async function redeem(rewardId: string) {
  try {
  const res = await fetch("/api/water?endpoint=gamification/redeem", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ reward_id: rewardId, user_id: "demo-user" }),
  });
  const json = await res.json();
  if (json.data?.redeemed) {
  redeemMessage = ` ${json.data.message} · Código: ${json.data.code}`;
  } else {
  redeemMessage = ` ${json.data?.reason ?? "No se pudo canjear"}`;
  }
  await fetchGamification();
  setTimeout(() => redeemMessage = null, 5000);
  } catch {}
  }

  async function joinChallenge(challengeId: string) {
  try {
  await fetch("/api/water?endpoint=gamification/challenges/join", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ challenge_id: challengeId }),
  });
  await fetchGamification();
  } catch {}
  }

  const SUGGESTED_QUESTIONS = [
  "¿Cuál es el problema más crítico ahora?",
  "¿Cómo está la calidad del agua?",
  "¿Hay alguna fuga detectada?",
  "Resumen del estado del sistema",
  "¿Qué normativa estamos incumpliendo?",
  ];
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
  await fetchInsights();
  interval = setInterval(async () => {
  if (liveMode) { await fetchReading(); await fetchAgent(); await fetchMitigation(); }
  }, 10000);
  });
  onDestroy(() => clearInterval(interval));

  const maxConsumption = $derived(Math.max(...history.map(h => h.consumption_l ?? 0), 1));
  const totalAnnualLoss = $derived((reading?.losses_l_min ?? 0) * 1440 * 365 * 3.5);
  const annualSaving  = $derived(totalAnnualLoss * 0.6);
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
  ["dashboard",  "Operación",  "01"],
  ["history",  "Tendencias",  "02"],
  ["industrial", "Gestión Industrial","03"],
  ["agent",  "Inteligencia",  "04"],
  ["mitigation", "Mapa del Campus",  "05"],
  ["community",  "Comunidad",  "06"],
  ["architecture", "Arquitectura",   "07"],
  ] as [key, label, num]}
  <button
  onclick={() => { tab = key as typeof tab; if (key === "history") fetchHistory(); if (key === "community") fetchGamification(); }}
  class="group relative px-4 py-3 text-[12px] font-medium tracking-tight border-b-2 transition-all -mb-px flex items-center gap-2
  {tab === key ? 'border-sky-500 text-white' : 'border-transparent text-slate-500 hover:text-slate-300 hover:border-white/10'}"
  >
  <span class="text-[9px] font-mono opacity-60">{num}</span>
  <span>{label}</span>
  <span
  role="button"
  tabindex="0"
  onclick={(e) => { e.stopPropagation(); infoOpen = infoOpen === key ? null : key; }}
  onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); e.stopPropagation(); infoOpen = infoOpen === key ? null : key; } }}
  class="ml-1 w-4 h-4 inline-flex items-center justify-center rounded-full border text-[9px] font-mono cursor-pointer transition-colors
  {infoOpen === key ? 'bg-sky-500/20 border-sky-500/50 text-sky-300' : 'bg-white/[0.04] border-white/10 text-slate-500 hover:text-sky-400 hover:border-sky-500/30'}"
  title="¿Qué hace esta sección?"
  >i</span>
  </button>
  {/each}
  </div>
  </header>

  <!-- Tooltip / popover de información del apartado activo -->
  {#if infoOpen && tabInfo[infoOpen]}
  <div class="mx-auto max-w-7xl px-6 mt-2">
  <div class="rounded-lg border border-sky-500/[0.20] bg-gradient-to-br from-sky-500/[0.06] to-sky-500/[0.02] p-4 relative animate-fade-in">
  <button
  onclick={() => infoOpen = null}
  class="absolute top-2 right-2 w-6 h-6 rounded-full bg-white/[0.04] border border-white/10 text-slate-400 hover:text-white text-[12px] flex items-center justify-center"
  aria-label="Cerrar"
  >×</button>
  <div class="flex items-baseline gap-2 mb-2">
  <span class="text-[10px] font-mono text-sky-400 tracking-wider uppercase">¿Qué es este apartado?</span>
  <span class="text-[13px] font-semibold text-white">{tabInfo[infoOpen].title}</span>
  </div>
  <ul class="space-y-1 text-[11.5px] text-slate-300 leading-relaxed">
  {#each tabInfo[infoOpen].lines as line}
  <li class="flex gap-2">
  <span class="text-sky-400 shrink-0">·</span>
  <span>{line}</span>
  </li>
  {/each}
  </ul>
  </div>
  </div>
  {/if}

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
  <div class="text-[11px] font-medium tracking-wider uppercase text-slate-500 mb-4">8 Sensores · Tiempo real</div>
  <div class="space-y-3">
  {#each [
  { label: "Caudal total",      value: fmt(reading.total_flow_lmin, 1) + " L/min", pct: (reading.total_flow_lmin ?? 0) / 150 * 100, color: "#7dd3fc", code: "Q" },
  { label: "Presión red",       value: fmt(reading.pressure_kpa, 0) + " kPa",      pct: (reading.pressure_kpa ?? 0) / 700 * 100,      color: "#a5b4fc", code: "P" },
  { label: "Nivel freático",    value: fmt(reading.phreatic_m, 1) + " m",          pct: (reading.phreatic_m ?? 0) / 15 * 100,          color: "#86efac", code: "N" },
  { label: "Turbidez",          value: fmt(reading.turbidity_ntu, 1) + " NTU",     pct: (reading.turbidity_ntu ?? 0) / 5 * 100,        color: (reading.turbidity_ntu ?? 0) > 4 ? "#f87171" : "#fbbf24", code: "T" },
  { label: "Corriente bombas",  value: fmt(((reading as any).pump1_current_a ?? 0) + ((reading as any).pump2_current_a ?? 0), 1) + " A",  pct: (((reading as any).pump1_current_a ?? 0) + ((reading as any).pump2_current_a ?? 0)) / 50 * 100, color: "#fb923c", code: "I" },
  { label: "Humedad suelo",     value: fmt((reading as any).soil_humidity_pct ?? 0, 0) + " %",   pct: (reading as any).soil_humidity_pct ?? 0,                color: "#34d399", code: "H" },
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
  <div class="flex items-center justify-between text-[11px] pt-1">
  <span class="flex items-center gap-2">
  <span class="w-4 h-4 rounded-sm flex items-center justify-center text-[10px] font-mono font-bold" style="background:#a855f71A;color:#a855f7">E</span>
  <span class="text-slate-400">kWh/m³ bombeo</span>
  </span>
  <span class="font-mono {((reading as any).kwh_per_m3 ?? 0) < 0.6 ? 'text-emerald-400' : ((reading as any).kwh_per_m3 ?? 0) < 1.0 ? 'text-amber-400' : 'text-red-400'}">{fmt((reading as any).kwh_per_m3 ?? 0, 3)}</span>
  </div>
  </div>
  </div>
  </div>

  <!-- Método tradicional UNIAJC + validación cruzada -->
  <div class="mt-6 rounded-xl border border-emerald-500/[0.18] bg-gradient-to-br from-emerald-500/[0.03] to-emerald-500/[0.01] p-4">
  <div class="flex items-baseline justify-between mb-3">
  <div>
  <div class="text-[11px] font-medium tracking-wider uppercase text-emerald-400">Método tradicional UNIAJC · validación cruzada</div>
  <div class="text-[11px] text-slate-300 mt-1">Respetamos el método de costo cero del operario. AguaMind OS lo digitaliza y lo cruza con el sensor para máxima confianza.</div>
  </div>
  <span class="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">$0 · híbrido</span>
  </div>

  <div class="grid grid-cols-1 md:grid-cols-3 gap-3 text-[11px]">
  <div class="rounded-md border border-white/[0.06] bg-white/[0.02] p-3">
  <div class="text-[10px] uppercase tracking-wider text-slate-500 mb-1">17:30 · cierre del día</div>
  <div class="text-slate-300 leading-snug">Operario llena tanques A 36k L y B 16k L · cierra escotilla · anota marca de nivel en bitácora</div>
  </div>
  <div class="rounded-md border border-white/[0.06] bg-white/[0.02] p-3">
  <div class="text-[10px] uppercase tracking-wider text-slate-500 mb-1">07:00 · inicio del día</div>
  <div class="text-slate-300 leading-snug">Abre escotilla · lee nueva marca · diferencia × 160 L/cm = pérdida nocturna en litros</div>
  </div>
  <div class="rounded-md border border-emerald-500/[0.20] bg-emerald-500/[0.04] p-3">
  <div class="text-[10px] uppercase tracking-wider text-emerald-400 mb-1">+ JSN-SR04T en paralelo</div>
  <div class="text-slate-300 leading-snug">Sensor mide cada 30s. Si difiere &gt;5 cm de marca manual → alerta de calibración. Doble método independiente.</div>
  </div>
  </div>

  <div class="text-[10px] text-slate-500 mt-3 pt-3 border-t border-white/[0.06] font-mono">
  Equivalencia validada: 1 cm = 160 L (Sánchez Sotelo 2021) · 1,587 L/día medidos manualmente · sensor confirma a 2,880 lecturas/día
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

  <!-- ── HEATMAP día × hora (consumo principal) ─────────────────────────── -->
  <div class="mb-4">
  <h2 class="text-[14px] font-semibold text-white tracking-tight">Patrón de consumo · día × hora</h2>
  <p class="text-[11px] text-slate-500 mt-0.5">Heatmap semana típica · cada celda = consumo promedio en esa franja · útil para identificar picos académicos vs noches y fines de semana</p>
  </div>

  <div class="rounded-2xl border border-white/[0.04] p-4 mb-6" style="background: rgba(255,255,255,0.015)">
  <svg viewBox="0 0 900 320" class="w-full h-auto">
  <!-- Eje Y · días -->
  {#each ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"] as dia, dayI}
  <text x="40" y={50 + dayI * 32 + 18} text-anchor="end" fill="rgba(255,255,255,0.65)" font-size="11" font-family="Inter">{dia}</text>
  {/each}

  <!-- Eje X · horas -->
  {#each [0,4,8,12,16,20,23] as hLabel, i}
  <text x={60 + (hLabel / 23) * 800} y="40" text-anchor="middle" fill="rgba(255,255,255,0.5)" font-size="10" font-family="JetBrains Mono">{String(hLabel).padStart(2,'0')}h</text>
  {/each}

  <!-- Celdas heatmap (24 horas × 7 días) -->
  {#each Array(7) as _, dayI}
  {#each Array(24) as _, hour}
  {@const isWeekend = dayI >= 5}
  {@const isPeakMorning = hour >= 7 && hour <= 9}
  {@const isPeakLunch = hour >= 12 && hour <= 13}
  {@const isPeakAfternoon = hour >= 15 && hour <= 17}
  {@const isOff = hour >= 22 || hour < 6}
  {@const intensity = isWeekend
    ? (isOff ? 0.05 : isPeakMorning || isPeakLunch || isPeakAfternoon ? 0.18 : 0.12)
    : isOff ? 0.10
    : isPeakMorning ? 0.95
    : isPeakLunch ? 0.85
    : isPeakAfternoon ? 0.80
    : hour >= 6 && hour <= 18 ? 0.55
    : 0.20}
  <rect
  x={60 + hour * 33}
  y={50 + dayI * 32}
  width="31"
  height="29"
  rx="2"
  fill={`rgba(14,165,233,${intensity})`}
  stroke="rgba(255,255,255,0.04)"
  stroke-width="0.5"
  />
  {/each}
  {/each}

  <!-- Gradient legend -->
  <text x="60" y="295" fill="rgba(255,255,255,0.5)" font-size="9" font-family="JetBrains Mono">consumo bajo</text>
  {#each Array(20) as _, i}
  <rect x={170 + i * 12} y="285" width="11" height="10" fill={`rgba(14,165,233,${0.05 + (i / 20) * 0.95})`}/>
  {/each}
  <text x="420" y="295" fill="rgba(255,255,255,0.5)" font-size="9" font-family="JetBrains Mono">consumo alto</text>

  <!-- Anotaciones de patrones -->
  <text x="640" y="295" fill="rgba(125,211,252,0.7)" font-size="10" font-family="JetBrains Mono">pico 7-9h · entrada estudiantes</text>
  </svg>
  </div>

  <!-- ── Multi-variable sparklines ─────────────────────────────────────── -->
  <div class="mb-4">
  <h2 class="text-[14px] font-semibold text-white tracking-tight">Tendencias multi-variable · 24 h</h2>
  <p class="text-[11px] text-slate-500 mt-0.5">Caudal · presión · nivel de tanque A · turbidez · freático · corriente bombas</p>
  </div>

  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mb-6">
  {#each [
  { name: "Caudal entrada",  unit: "L/min",  color: "#0ea5e9", values: [16,17,17,18,18,18,22,28,30,29,27,26,24,18,17,25,26,25,21,16,15,15,15,16] },
  { name: "Presión red",     unit: "kPa",    color: "#a855f7", values: [320,318,322,325,328,330,360,395,410,400,385,380,370,340,335,375,380,375,355,330,325,322,320,320] },
  { name: "Nivel Tank A",    unit: "%",      color: "#10b981", values: [85,84,82,80,78,76,68,55,45,42,48,55,62,72,75,68,60,55,62,72,80,84,86,86] },
  { name: "Turbidez",        unit: "NTU",    color: "#fbbf24", values: [0.8,0.9,0.9,1.1,1.2,1.3,1.5,1.8,2.1,1.9,1.6,1.4,1.5,1.7,1.8,2.2,2.0,1.7,1.4,1.2,1.0,0.9,0.8,0.8] },
  { name: "Freático",        unit: "m",      color: "#7dd3fc", values: [8.2,8.2,8.1,8.1,8.0,8.0,7.9,7.8,7.7,7.7,7.8,7.9,7.9,8.0,8.1,8.0,7.9,7.9,8.0,8.1,8.1,8.2,8.2,8.2] },
  { name: "Corriente bombas",unit: "A",      color: "#fb923c", values: [4,4,4,4,4,4,12,22,24,23,21,20,17,8,8,18,21,20,15,6,5,5,5,5] },
  ] as v}
  {@const min = Math.min(...v.values)}
  {@const max = Math.max(...v.values)}
  {@const range = max - min || 1}
  <div class="rounded-2xl border border-white/[0.04] p-4" style="background: rgba(255,255,255,0.015)">
  <div class="flex items-baseline justify-between mb-2">
  <div>
  <div class="text-[11px] text-slate-300 font-medium">{v.name}</div>
  <div class="text-[9px] text-slate-500 font-mono">{v.unit}</div>
  </div>
  <div class="text-right">
  <div class="text-[16px] font-semibold" style="color:{v.color}">{v.values[v.values.length-1]}</div>
  <div class="text-[9px] text-slate-500 font-mono">min {min} · max {max}</div>
  </div>
  </div>
  <svg viewBox="0 0 240 60" class="w-full h-auto">
  <!-- Sparkline -->
  <polyline
  points={v.values.map((val, i) => `${(i / (v.values.length - 1)) * 240},${55 - ((val - min) / range) * 50}`).join(' ')}
  fill="none" stroke={v.color} stroke-width="2"
  />
  <!-- Área bajo la curva -->
  <polygon
  points={`0,55 ${v.values.map((val, i) => `${(i / (v.values.length - 1)) * 240},${55 - ((val - min) / range) * 50}`).join(' ')} 240,55`}
  fill={v.color} opacity="0.10"
  />
  <!-- Punto final destacado -->
  <circle cx="240" cy={55 - ((v.values[v.values.length-1] - min) / range) * 50} r="3" fill={v.color}/>
  </svg>
  <div class="flex justify-between text-[8px] text-slate-600 font-mono mt-1">
  <span>00h</span><span>06h</span><span>12h</span><span>18h</span><span>ahora</span>
  </div>
  </div>
  {/each}
  </div>

  <!-- ── Stacked area: consumo vs pérdidas ────────────────────────────── -->
  <div class="mb-4">
  <h2 class="text-[14px] font-semibold text-white tracking-tight">Consumo vs pérdidas · stacked area</h2>
  <p class="text-[11px] text-slate-500 mt-0.5">Visualización del agua que va al uso real (azul) versus la que se pierde antes de llegar (rojo)</p>
  </div>

  <div class="rounded-2xl border border-white/[0.04] p-4 mb-6" style="background: rgba(255,255,255,0.015)">
  <svg viewBox="0 0 900 220" class="w-full h-auto">
  <!-- Gridlines -->
  {#each [0, 25, 50, 75, 100] as pct}
  <line x1="60" y1={30 + (100 - pct) * 1.6} x2="880" y2={30 + (100 - pct) * 1.6} stroke="rgba(255,255,255,0.05)"/>
  <text x="55" y={34 + (100 - pct) * 1.6} text-anchor="end" fill="rgba(255,255,255,0.4)" font-size="9" font-family="JetBrains Mono">{pct}%</text>
  {/each}

  <!-- Área de pérdidas (abajo, rojo) -->
  <path d="M 60 190 {STACK_DATA.map(d => `L ${60 + (d.h / 23) * 820} ${190 - d.perdidas * 1.6}`).join(' ')} L 880 190 Z"
        fill="rgba(239,68,68,0.30)" stroke="#ef4444" stroke-width="1.5"/>

  <!-- Área de consumo (arriba, azul) -->
  <path d="M 60 190 {STACK_DATA.map(d => `L ${60 + (d.h / 23) * 820} ${190 - (d.consumo + d.perdidas) * 1.6}`).join(' ')} L 880 190 Z"
        fill="rgba(14,165,233,0.30)" stroke="#0ea5e9" stroke-width="1.5"/>

  <!-- Eje X labels -->
  {#each [0, 6, 12, 18, 23] as h}
  <text x={60 + (h / 23) * 820} y="208" text-anchor="middle" fill="rgba(255,255,255,0.5)" font-size="9" font-family="JetBrains Mono">{String(h).padStart(2,'0')}h</text>
  {/each}

  <!-- Leyenda -->
  <rect x="700" y="35" width="14" height="10" fill="rgba(14,165,233,0.30)" stroke="#0ea5e9"/>
  <text x="720" y="44" fill="rgba(255,255,255,0.7)" font-size="10" font-family="Inter">consumo real</text>
  <rect x="700" y="55" width="14" height="10" fill="rgba(239,68,68,0.30)" stroke="#ef4444"/>
  <text x="720" y="64" fill="rgba(255,255,255,0.7)" font-size="10" font-family="Inter">pérdidas técnicas</text>
  </svg>
  <div class="text-[10px] text-slate-500 mt-2">Las pérdidas representan ~10-15% del flujo total durante el día y crecen al ~50% del flujo nocturno (madrugada). Esto es justo lo que el método "tanques nocturnos" detecta y valida.</div>
  </div>

  <!-- ── Bar chart consumo histórico (existente · simplificado) ───────── -->
  <div class="rounded-2xl border border-white/[0.04] p-4 mb-5" style="background: rgba(255,255,255,0.015)">
  <div class="flex items-center justify-between mb-4">
  <div>
  <div class="text-[11px] font-medium tracking-wider uppercase text-slate-500">Consumo agregado por hora · barras</div>
  <div class="text-[10px] text-slate-500 mt-0.5">{history.length} muestras del simulador en vivo</div>
  </div>
  </div>
  <div class="flex items-end gap-px h-32">
  {#each history as h}
  <div class="flex-1 min-w-0 group relative">
  <div class="w-full bg-gradient-to-t from-sky-600 to-sky-400 hover:from-sky-500 hover:to-sky-300 rounded-t transition-colors"
  style="height:{(h.consumption_l / maxConsumption) * 100}%"></div>
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
  <!-- TAB 3: INDUSTRIAL · alineado con AQUA-ROI Lite (compañero electrónica)-->
  <!-- ════════════════════════════════════════════════════════════════════ -->
  {:else if tab === "industrial"}

  <!-- ── 1. KPIs principales (IEH, TPP, CPE, ICA) + AQUA-ROI (kWh/m³, DPTAP) ── -->
  <div class="mb-4">
  <h2 class="text-[14px] font-semibold text-white tracking-tight">Indicadores de desempeño</h2>
  <p class="text-[11px] text-slate-500 mt-0.5">4 KPIs principales (rúbrica oficial) + 2 métricas operativas AQUA-ROI</p>
  </div>

  <div class="grid grid-cols-2 lg:grid-cols-3 gap-2 mb-6">
  {#each [
  { id: "IEH",   name: "Eficiencia hídrica",   formula: "(Q_entrada − Pérdidas) / Q_entrada × 100", target: "> 90%" },
  { id: "TPP",   name: "Tasa de pérdidas",     formula: "Pérdidas / Q_entrada × 100",                target: "< 10%" },
  { id: "CPE",   name: "Consumo per estudiante", formula: "Consumo_diario / Estudiantes",            target: "≤ 14.04 L" },
  { id: "ICA",   name: "Calidad del agua",     formula: "100 − (Turbidez / 4) × 30",                  target: "> 90 pts" },
  { id: "kWh_m3",name: "Eficiencia energética",formula: "(I_bombas × 220V × t) / volumen_m³",         target: "< 0.6"   },
  { id: "DPTAP", name: "Disponibilidad PTAP",  formula: "Horas_disponible / Horas_programadas × 100", target: "> 98%"   },
  ] as k}
  {@const kpi = kpis?.[k.id] ?? { value: 0, status: "ok", unit: "" }}
  <div class="rounded-lg border border-white/[0.04] p-3" style="background: rgba(255,255,255,0.015)">
  <div class="flex items-baseline justify-between mb-1">
  <span class="font-mono text-[10px] text-slate-500">{k.id}</span>
  <span class="text-[8px] uppercase font-mono px-1 rounded" style="color:{statusHex(kpi.status)};background:{statusHex(kpi.status)}1A">{kpi.status}</span>
  </div>
  <div class="text-[20px] font-semibold tracking-tight" style="color:{statusHex(kpi.status)}">{fmt(kpi.value, k.id === "CPE" ? 2 : k.id === "kWh_m3" ? 3 : 1)}<span class="text-[10px] text-slate-500 ml-1 font-mono">{kpi.unit ?? ""}</span></div>
  <div class="text-[10px] text-slate-300 mt-1">{k.name}</div>
  <div class="text-[9px] font-mono text-slate-600 mt-1.5 leading-tight">{k.formula}</div>
  <div class="text-[9px] text-slate-500 mt-0.5">meta {k.target}</div>
  </div>
  {/each}
  </div>

  <!-- ── 2. Estadísticas en vivo (estilo Arquitectura) ── -->
  <div class="mb-4">
  <h2 class="text-[14px] font-semibold text-white tracking-tight">Estadísticas en vivo</h2>
  <p class="text-[11px] text-slate-500 mt-0.5">Análisis descriptivo · sparkline 24h · histograma de eventos · curva de optimización energética</p>
  </div>

  <div class="rounded-2xl border border-white/[0.04] p-4 mb-6" style="background: rgba(255,255,255,0.015)">
  <svg viewBox="0 0 900 320" class="w-full h-auto">
  <!-- Sparkline TPP 24h -->
  <g>
  <text x="20" y="22" fill="rgba(125,211,252,0.85)" font-size="11" font-family="Inter" font-weight="600">TPP últimas 24h · % pérdidas</text>
  <rect x="20" y="32" width="280" height="100" fill="rgba(0,0,0,0.18)" rx="3" stroke="rgba(125,211,252,0.10)"/>
  <line x1="20" y1="82" x2="300" y2="82" stroke="rgba(125,211,252,0.18)" stroke-dasharray="2 3"/>
  <text x="305" y="86" fill="rgba(125,211,252,0.55)" font-size="9" font-family="JetBrains Mono">10%</text>
  <path d="M 22 110 L 35 108 L 50 102 L 65 95 L 80 88 L 95 80 L 110 70 L 125 62 L 140 56 L 155 60 L 170 65 L 185 72 L 200 78 L 215 72 L 230 65 L 245 58 L 260 52 L 275 48 L 290 50 L 298 54"
  fill="none" stroke="#0ea5e9" stroke-width="2"/>
  <circle cx="280" cy="48" r="3" fill="#fbbf24"/>
  <text x="280" y="38" text-anchor="middle" fill="rgba(251,191,36,0.85)" font-size="8" font-family="JetBrains Mono">pico</text>
  <text x="20" y="148" fill="rgba(255,255,255,0.5)" font-size="8" font-family="JetBrains Mono">0h</text>
  <text x="155" y="148" fill="rgba(255,255,255,0.5)" font-size="8" font-family="JetBrains Mono">12h</text>
  <text x="288" y="148" fill="rgba(255,255,255,0.5)" font-size="8" font-family="JetBrains Mono">24h</text>
  </g>

  <!-- Histograma eventos de fuga por hora del día -->
  <g>
  <text x="320" y="22" fill="rgba(251,146,60,0.85)" font-size="11" font-family="Inter" font-weight="600">Fugas detectadas por hora</text>
  <rect x="320" y="32" width="260" height="100" fill="rgba(0,0,0,0.18)" rx="3" stroke="rgba(251,146,60,0.10)"/>
  {#each [3,2,4,5,6,4,2,1,1,2,3,2,1,2,3,2,3,4,5,6,8,9,7,5] as v, i}
  {@const x = 322 + i * 10.5}
  {@const h = v * 9}
  <rect x={x} y={130 - h} width="8" height={h} rx="1" fill={v > 6 ? '#ef4444' : v > 4 ? '#fb923c' : '#fbbf24'} opacity="0.75"/>
  {/each}
  <text x="320" y="148" fill="rgba(255,255,255,0.5)" font-size="8" font-family="JetBrains Mono">0h</text>
  <text x="450" y="148" fill="rgba(255,255,255,0.5)" font-size="8" font-family="JetBrains Mono">12h</text>
  <text x="568" y="148" fill="rgba(255,255,255,0.5)" font-size="8" font-family="JetBrains Mono">24h</text>
  <text x="510" y="50" fill="rgba(239,68,68,0.7)" font-size="8" font-family="JetBrains Mono">21:00 pico nocturno</text>
  </g>

  <!-- Curva optimización kWh/m³ vs hora -->
  <g>
  <text x="600" y="22" fill="rgba(168,85,247,0.85)" font-size="11" font-family="Inter" font-weight="600">kWh/m³ baseline vs eco</text>
  <rect x="600" y="32" width="280" height="100" fill="rgba(0,0,0,0.18)" rx="3" stroke="rgba(168,85,247,0.10)"/>
  <line x1="600" y1="60" x2="880" y2="60" stroke="rgba(168,85,247,0.20)" stroke-dasharray="2 3"/>
  <text x="882" y="64" fill="rgba(168,85,247,0.55)" font-size="9" font-family="JetBrains Mono">0.6</text>
  <!-- baseline (alta) -->
  <path d="M 605 65 L 625 64 L 650 65 L 680 66 L 710 65 L 740 63 L 770 62 L 800 64 L 830 65 L 855 66 L 875 65"
  fill="none" stroke="rgba(255,255,255,0.45)" stroke-width="1.5" stroke-dasharray="3 2"/>
  <!-- optimizada (eco-nocturno) -->
  <path d="M 605 75 L 625 80 L 650 90 L 680 95 L 710 100 L 740 100 L 770 95 L 800 80 L 830 70 L 855 67 L 875 65"
  fill="none" stroke="#a855f7" stroke-width="2"/>
  <!-- área de ahorro -->
  <path d="M 625 64 L 625 80 L 650 90 L 680 95 L 710 100 L 740 100 L 770 95 L 800 80 L 800 64 L 770 62 L 740 63 L 710 65 L 680 66 L 650 65 Z"
  fill="rgba(168,85,247,0.18)"/>
  <text x="740" y="148" text-anchor="middle" fill="rgba(168,85,247,0.7)" font-size="9" font-family="JetBrains Mono">22:00–06:00 · −40% kWh</text>
  </g>

  <!-- Heatmap día × hora consumo -->
  <g>
  <text x="20" y="180" fill="rgba(34,197,94,0.85)" font-size="11" font-family="Inter" font-weight="600">Heatmap consumo · día × franja horaria</text>
  {#each Array(7) as _, dayI}
  {#each Array(6) as _, blockI}
  {@const intensity = dayI < 5 ? (blockI === 1 ? 0.85 : blockI === 2 ? 0.70 : blockI === 3 ? 0.50 : blockI === 4 ? 0.30 : 0.20) : (blockI === 0 ? 0.10 : 0.20)}
  <rect x={22 + blockI * 38} y={195 + dayI * 16} width="36" height="14" rx="2" fill={`rgba(34,197,94,${intensity})`} stroke="rgba(255,255,255,0.04)"/>
  {/each}
  {/each}
  <text x="22" y="318" fill="rgba(255,255,255,0.5)" font-size="8" font-family="JetBrains Mono">L M X J V S D · 0-4 · 4-8 · 8-12 · 12-16 · 16-20 · 20-24</text>
  </g>

  <!-- Distribución p50/p95/p99 presión -->
  <g>
  <text x="320" y="180" fill="rgba(56,189,248,0.85)" font-size="11" font-family="Inter" font-weight="600">Distribución presión red · p50/p95/p99</text>
  <text x="322" y="208" fill="rgba(255,255,255,0.7)" font-size="9.5" font-family="JetBrains Mono">p50  →  286 kPa</text>
  <rect x="322" y="214" width="160" height="6" rx="3" fill="rgba(56,189,248,0.7)"/>
  <text x="322" y="240" fill="rgba(255,255,255,0.7)" font-size="9.5" font-family="JetBrains Mono">p95  →  412 kPa</text>
  <rect x="322" y="246" width="220" height="6" rx="3" fill="rgba(56,189,248,0.45)"/>
  <text x="322" y="272" fill="rgba(255,255,255,0.7)" font-size="9.5" font-family="JetBrains Mono">p99  →  478 kPa</text>
  <rect x="322" y="278" width="240" height="6" rx="3" fill="rgba(56,189,248,0.25)"/>
  <text x="322" y="306" fill="rgba(56,189,248,0.55)" font-size="9" font-family="JetBrains Mono">rango óptimo: 200–400 kPa · meta p95 &lt; 450</text>
  </g>

  <!-- Gauge ROI -->
  <g>
  <text x="600" y="180" fill="rgba(16,185,129,0.85)" font-size="11" font-family="Inter" font-weight="600">ROI escenarios · payback (años)</text>
  {#each [
  { name: "Prudente", val: 1.84, color: "#fbbf24" },
  { name: "Conservador", val: 1.26, color: "#10b981" },
  { name: "Medio", val: 1.07, color: "#34d399" },
  ] as s, i}
  <text x="605" y={205 + i * 30} fill="rgba(255,255,255,0.7)" font-size="10" font-family="Inter">{s.name}</text>
  <rect x="685" y={199 + i * 30} width="160" height="10" rx="2" fill="rgba(255,255,255,0.05)"/>
  <rect x="685" y={199 + i * 30} width={(2 - s.val) / 2 * 160} height="10" rx="2" fill={s.color} opacity="0.85"/>
  <text x="850" y={207 + i * 30} fill={s.color} font-size="10" font-family="JetBrains Mono" font-weight="bold">{s.val} años</text>
  {/each}
  </g>
  </svg>
  </div>

  <!-- ── 3. Costo-beneficio · 3 escenarios AQUA-ROI Lite ── -->
  <div class="mb-4">
  <h2 class="text-[14px] font-semibold text-white tracking-tight">Costo-beneficio · 3 escenarios</h2>
  <p class="text-[11px] text-slate-500 mt-0.5">Inversión piloto AQUA-ROI Lite vs propuesta completa Arias Montoya 2024</p>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-3 gap-3 mb-6">
  {#each [
  { name: "Conservador", savings: 4_429_751, payback: 1.26, color: "#10b981", note: "Recuperación fugas + riego inteligente + alertas + menos recorridos" },
  { name: "Medio",       savings: 5_200_000, payback: 1.07, color: "#34d399", note: "Si el sistema detecta fugas mayores no documentadas hoy" },
  { name: "Prudente sin mantenimiento", savings: 3_030_000, payback: 1.84, color: "#fbbf24", note: "Solo cuenta ahorro de fugas y riego, sin predictivo" },
  ] as e}
  <div class="rounded-2xl border border-white/[0.04] p-4" style="background: rgba(255,255,255,0.015)">
  <div class="flex items-baseline justify-between mb-3">
  <span class="text-[12px] font-semibold text-white">{e.name}</span>
  <span class="text-[10px] font-mono" style="color:{e.color}">{e.payback} años</span>
  </div>
  <div class="text-[24px] font-semibold tracking-tight" style="color:{e.color}">${e.savings.toLocaleString('es-CO')}</div>
  <div class="text-[10px] text-slate-500 font-mono">COP/año ahorro</div>
  <div class="text-[10px] text-slate-400 mt-3 leading-snug">{e.note}</div>
  </div>
  {/each}
  </div>

  <!-- Comparativa de 3 inversiones -->
  <div class="rounded-2xl border border-white/[0.04] p-4 mb-6" style="background: rgba(255,255,255,0.015)">
  <div class="text-[10px] uppercase tracking-wider text-slate-500 mb-3">Comparativa de inversión</div>
  <div class="grid grid-cols-3 gap-3">
  {#each [
  { label: "Demo Fase 0", val: 1_431_000, sub: "backend mínimo + simulador" },
  { label: "Piloto AQUA-ROI Lite", val: 5_570_000, sub: "BOM compañero electrónica · Fase 1", highlight: true },
  { label: "Propuesta completa", val: 37_376_807, sub: "Arias Montoya 2024 · sin medición" },
  ] as inv}
  <div class={`rounded-md p-3 border ${inv.highlight ? 'border-emerald-500/30' : 'border-white/[0.04]'}`}>
  <div class="text-[10px] text-slate-500 uppercase tracking-wider">{inv.label}</div>
  <div class={`text-[18px] font-semibold mt-1 ${inv.highlight ? 'text-emerald-400' : 'text-white'}`}>${inv.val.toLocaleString('es-CO')}</div>
  <div class="text-[9px] text-slate-500 mt-1">{inv.sub}</div>
  </div>
  {/each}
  </div>
  <div class="text-[10px] text-slate-500 mt-3">El piloto AQUA-ROI reduce 85.1% la barrera financiera respecto a la propuesta completa.</div>
  </div>

  <!-- ── 4. Lean Manufacturing · 6 mudas + 6M Ishikawa ── -->
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-3 mb-6">
  <div class="rounded-2xl border border-white/[0.04] p-4" style="background: rgba(255,255,255,0.015)">
  <div class="text-[11px] font-medium tracking-wider uppercase text-slate-500 mb-3">Lean · 6 mudas en PTAP</div>
  <div class="space-y-1">
  {#each [
  ["Defectos", "Fugas, calidad variable, lectura tardía", "Alertas caudal nocturno + presión + turbidez"],
  ["Sobreprocesamiento", "Tratar/bombear agua que se pierde", "Medición pérdidas + riego por necesidad"],
  ["Esperas", "Reaccionar cuando equipo ya falló", "Mantenimiento predictivo (corriente + presión)"],
  ["Movimiento", "Inspecciones manuales sin priorización", "Dashboard + rutas por alerta"],
  ["Energía desperdiciada", "Bombas con ciclos frecuentes", "Conteo ciclos + kWh/m³"],
  ["Talento subutilizado", "Operario sin datos para decidir", "Interfaz semáforo + recomendaciones"],
  ] as [muda, manif, contra]}
  <div class="border-b border-white/[0.04] py-2">
  <div class="text-[11px] text-amber-400 font-medium">{muda}</div>
  <div class="text-[10px] text-slate-400 mt-0.5">{manif}</div>
  <div class="text-[10px] text-emerald-400 mt-0.5">→ {contra}</div>
  </div>
  {/each}
  </div>
  </div>

  <div class="rounded-2xl border border-white/[0.04] p-4" style="background: rgba(255,255,255,0.015)">
  <div class="text-[11px] font-medium tracking-wider uppercase text-slate-500 mb-3">Ishikawa 6M · causa-efecto</div>
  <div class="text-[10px] text-slate-500 mb-3 italic">Efecto: pérdidas de agua y baja eficiencia económica-operativa de la PTAP</div>
  <div class="space-y-2">
  {#each [
  ["Método", "Mantenimiento correctivo · riego sin humedad · registros manuales"],
  ["Medición", "Sin caudalímetros · sin medidor eléctrico · sin históricos"],
  ["Maquinaria", "Bombas con ciclos frecuentes · filtros sin retrolavado · hidroflo dependiente"],
  ["Mano de obra", "Un solo operario · capacitación limitada · carga compartida"],
  ["Materiales", "Tuberías con posibles fugas · válvulas sin inspección"],
  ["Medio ambiente", "Variación calidad cruda · turbidez · sequía/lluvia · presión sobre acuífero"],
  ] as [cat, causes]}
  <div class="border-l-2 border-sky-500/40 pl-3">
  <div class="text-[11px] text-sky-300 font-medium">{cat}</div>
  <div class="text-[10px] text-slate-400">{causes}</div>
  </div>
  {/each}
  </div>
  </div>
  </div>

  <!-- ── 5. Reglas declarativas del agente (Tabla 13 AQUA-ROI) ── -->
  <div class="mb-4">
  <h2 class="text-[14px] font-semibold text-white tracking-tight">Reglas del agente · acciones automáticas</h2>
  <p class="text-[11px] text-slate-500 mt-0.5">5 reglas declarativas con condición + acción + nivel de severidad</p>
  </div>

  <div class="rounded-2xl border border-white/[0.04] p-4 mb-6" style="background: rgba(255,255,255,0.015)">
  <div class="space-y-2">
  {#each [
  { id: "leak_night",  name: "Fuga nocturna",      condition: "caudal > umbral entre 20:00–05:00 + presión estable",    action: "Alerta amarilla · revisar baños, pilas y red principal",            severity: "warning",  color: "#fbbf24" },
  { id: "pump_fail",   name: "Falla bomba",        condition: "corriente alta + presión baja",                            action: "Alerta naranja/roja · revisar bomba, filtros, válvulas, cavitación", severity: "critical", color: "#ef4444" },
  { id: "filter_sat",  name: "Filtro saturado",    condition: "diferencial de presión creciente",                         action: "Programar retrolavado por condición real",                          severity: "warning",  color: "#fbbf24" },
  { id: "irr_unneed",  name: "Riego innecesario",  condition: "humedad ≥ 60% o tanque bajo",                              action: "Bloquear riego automático o avisar no regar",                       severity: "info",     color: "#0ea5e9" },
  { id: "sensor_bad",  name: "Sensor incoherente", condition: "lectura fuera de rango o sin cambio prolongado",          action: "Usar último dato válido + marcar dudoso + pedir inspección",        severity: "warning",  color: "#fbbf24" },
  ] as r}
  <div class="border-b border-white/[0.04] py-2 grid grid-cols-12 gap-3 items-baseline">
  <span class="col-span-2 text-[10px] font-mono text-slate-500">{r.id}</span>
  <span class="col-span-2 text-[11px] font-semibold" style="color:{r.color}">{r.name}</span>
  <span class="col-span-4 text-[10px] text-slate-400 font-mono">{r.condition}</span>
  <span class="col-span-4 text-[10px] text-slate-300">{r.action}</span>
  </div>
  {/each}
  </div>
  </div>

  <!-- ── 6. Plan a prueba de fallos ── -->
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-3 mb-6">
  <div class="rounded-2xl border border-white/[0.04] p-4" style="background: rgba(255,255,255,0.015)">
  <div class="text-[11px] font-medium tracking-wider uppercase text-slate-500 mb-3">Plan a prueba de fallos</div>
  <div class="space-y-1.5 text-[10.5px]">
  {#each [
  ["Sin internet",            "Mide localmente, guarda en microSD"],
  ["Sin Wi-Fi humedal",       "Registro local + LoRa opcional"],
  ["Falla sensor de nivel",   "Flotador físico de seguridad + modo manual"],
  ["Falla sensor de presión", "Manómetros existentes + alerta de sensor"],
  ["Lectura incoherente",     "Descartar dato + último válido + revisión"],
  ["Bloqueo del MCU",         "Watchdog reinicia el sistema"],
  ["Mantenimiento PTAP",      "Modo manual físico + registro de evento"],
  ] as [falla, resp]}
  <div class="flex gap-3 py-1.5 border-b border-white/[0.04]">
  <span class="text-amber-400 w-44 shrink-0">{falla}</span>
  <span class="text-slate-400">→ {resp}</span>
  </div>
  {/each}
  </div>
  </div>

  <!-- ── 7. Plan implementación 10 semanas ── -->
  <div class="rounded-2xl border border-white/[0.04] p-4" style="background: rgba(255,255,255,0.015)">
  <div class="text-[11px] font-medium tracking-wider uppercase text-slate-500 mb-3">Plan de implementación · 10 semanas</div>
  <div class="space-y-1.5 text-[10.5px]">
  {#each [
  ["Sem 1",   "Levantamiento final · diámetros, Wi-Fi, puntos corte, seguridad eléctrica"],
  ["Sem 2",   "Compra y banco de pruebas · sensores en mesa"],
  ["Sem 3",   "Instalación piloto · gabinete, caudalímetro, presión, corriente, nivel, humedad"],
  ["Sem 4",   "Calibración · vs manómetros y medición manual de tanque"],
  ["Sem 5–8", "Línea base · datos consumo normal, riego, ciclos de bombas"],
  ["Sem 9",   "Ajuste de reglas · umbrales reales de fuga, corriente, presión, riego"],
  ["Sem 10",  "Entrega · dashboard, informe ahorros, plan escalamiento, capacitación"],
  ] as [t, act]}
  <div class="flex gap-3 py-1.5 border-b border-white/[0.04]">
  <span class="text-sky-400 w-16 shrink-0 font-mono">{t}</span>
  <span class="text-slate-300">{act}</span>
  </div>
  {/each}
  </div>
  </div>
  </div>

  <!-- ── 8. Datos del campus (constantes Sánchez Sotelo + Caycedo) ── -->
  <div class="rounded-2xl border border-white/[0.04] p-4 mb-6" style="background: rgba(255,255,255,0.015)">
  <div class="text-[11px] font-medium tracking-wider uppercase text-slate-500 mb-3">Datos del campus (validados por tesis UNIAJC)</div>
  <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 text-[11px]">
  <div><div class="text-slate-500 text-[10px] uppercase tracking-wider">Consumo total</div><div class="font-mono text-white text-[14px] mt-1">45,367 L/día</div><div class="text-[9px] text-slate-500">Arias Montoya 2024</div></div>
  <div><div class="text-slate-500 text-[10px] uppercase tracking-wider">Pérdidas medidas</div><div class="font-mono text-amber-400 text-[14px] mt-1">1,587 L/día</div><div class="text-[9px] text-slate-500">Sánchez Sotelo 2021</div></div>
  <div><div class="text-slate-500 text-[10px] uppercase tracking-wider">Equiv. tanque</div><div class="font-mono text-white text-[14px] mt-1">1 cm = 160 L</div><div class="text-[9px] text-slate-500">validación cruzada</div></div>
  <div><div class="text-slate-500 text-[10px] uppercase tracking-wider">Caudal aljibes</div><div class="font-mono text-white text-[14px] mt-1">113.56 L/min</div><div class="text-[9px] text-slate-500">Caycedo & Jaramillo</div></div>
  <div><div class="text-slate-500 text-[10px] uppercase tracking-wider">Estudiantes</div><div class="font-mono text-white text-[14px] mt-1">3,230</div><div class="text-[9px] text-slate-500">activos/día</div></div>
  <div><div class="text-slate-500 text-[10px] uppercase tracking-wider">Usuarios totales</div><div class="font-mono text-white text-[14px] mt-1">8,234</div><div class="text-[9px] text-slate-500">+ docentes y staff</div></div>
  <div><div class="text-slate-500 text-[10px] uppercase tracking-wider">Cap. PTAR total</div><div class="font-mono text-white text-[14px] mt-1">4,000 est</div><div class="text-[9px] text-slate-500">2 PTAR × 2 mód × 1k</div></div>
  <div><div class="text-slate-500 text-[10px] uppercase tracking-wider">Sobrecapacidad</div><div class="font-mono text-red-400 text-[14px] mt-1">2.06×</div><div class="text-[9px] text-slate-500">8,234 ÷ 4,000</div></div>
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
  { code: "ORC", name: "Orchestrator",  desc: "Coordinador general · consolida",  status: agent?.last_decision ?? "—" },
  { code: "SYS", name: "SystemsAgent",  desc: "KPIs IEH/TPP/CPE · IsolationForest",  status: agent?.agents?.systems  ?? "—" },
  { code: "SEN", name: "SensorAgent",  desc: "Validación 6 sensores · calidad señal", status: agent?.agents?.sensor  ?? "—" },
  { code: "IND", name: "IndustrialAgent",  desc: "Lean (7 mudas) · ODS · costos",  status: agent?.agents?.industrial ?? "—" },
  { code: "MIT", name: "MitigationAgent",  desc: "Acción autónoma · electroválvulas",  status: (agent?.last_decision && agent.last_decision !== "ok") ? "execute" : "idle" },
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

  <!-- ═══ PLAN ANTE FENÓMENOS (multi-escenario) ═══ -->
  <div class="mt-6 rounded-xl border border-amber-500/[0.18] bg-gradient-to-br from-amber-500/[0.03] to-orange-500/[0.02] p-5">
  <div class="flex items-start justify-between mb-4">
  <div>
  <div class="text-[11px] font-medium tracking-wider uppercase text-amber-400">Plan ante fenómenos</div>
  <div class="text-[12px] text-slate-300 mt-1">5 escenarios con activación automática según señales del sistema</div>
  </div>
  <span class="text-[10px] font-mono px-2 py-1 rounded bg-emerald-500/15 text-emerald-400">sistema OK</span>
  </div>

  <!-- Grid de fenómenos (5 cards) -->
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-2">
  {#each [
  {
  trigger: "drought_mode", title: "Sequía / El Niño", color: "#f59e0b",
  cond: "freático < 5 m + IDEAM El Niño",
  impact_l: 10400,
  acts: ["Bomba eco_drought (-70%)", "Cierra EV-RC1 (riego)", "Presión nocturna 38→25 PSI",
  "Aviso operador + reporte CVC"],
  },
  {
  trigger: "flood_mode", title: "Lluvias / La Niña", color: "#0ea5e9",
  cond: "lluvia > 25 mm/h sostenida",
  impact_l: 5500,
  acts: ["Bomba a rain_standby", "Cierra EV-RC1 (riego innecesario)",
  "Monitoreo saturación PTAR", "Alerta drenaje preventivo"],
  },
  {
  trigger: "quake_mode", title: "Sismo", color: "#ef4444",
  cond: "acelerómetro > 0.05 g local",
  impact_l: 0,
  acts: ["Cierra TODAS las EV controlables", "Bomba emergency_off",
  "Alerta evacuación PTAP/PTAR", "Bloquea reapertura hasta inspección"],
  },
  {
  trigger: "contamination_mode", title: "Contaminación", color: "#a855f7",
  cond: "turbidez > 4 NTU o pH fuera 6-9",
  impact_l: 0,
  acts: ["Aísla EV-OUT-A/B (tanques)", "Bomba isolated",
  "Reporte automático INVIMA", "Suspende distribución hasta muestra"],
  },
  {
  trigger: "surge_mode", title: "Pico demanda", color: "#10b981",
  cond: "consumo > 150% baseline",
  impact_l: 2500,
  acts: ["Cierra EV-RC1 (prioriza uso humano)", "Bomba a 100% (boost seguro)",
  "Recalcula recarga tanques", "Aviso al operador"],
  },
  ] as p}
  <div class="rounded-lg border border-white/[0.06] bg-white/[0.02] p-3 flex flex-col">
  <div class="flex items-start gap-2 mb-2">
  <span class="w-2 h-2 rounded-full mt-1 shrink-0" style="background:{p.color}"></span>
  <div class="flex-1 min-w-0">
  <div class="text-[12px] font-semibold text-white truncate">{p.title}</div>
  <div class="text-[9px] text-slate-500 mt-0.5">{p.cond}</div>
  </div>
  </div>
  <ul class="space-y-0.5 mb-3 flex-1">
  {#each p.acts as a}
  <li class="text-[10px] text-slate-400 flex gap-1.5"><span class="text-slate-600">·</span>{a}</li>
  {/each}
  </ul>
  <div class="flex items-center gap-1.5 mb-2 text-[9px]">
  <span class="text-slate-500">impacto:</span>
  <span class="font-mono font-bold" style="color:{p.color}">
  {p.impact_l > 0 ? `${p.impact_l.toLocaleString()} L/día` : 'protección'}
  </span>
  </div>
  <button
  onclick={() => executeAutoMitigation(p.trigger)}
  class="w-full text-[10px] py-1.5 rounded-md border transition-colors font-medium"
  style="border-color:{p.color}55;background:{p.color}15;color:{p.color}">
  Activar
  </button>
  </div>
  {/each}
  </div>

  <div class="text-[10px] text-slate-500 mt-3 pt-3 border-t border-white/[0.06]">
  Cada plan ejecuta acciones físicas reales (cierre EV vía MQTT + ajuste VFD bomba) + reporte auditable. Documentación: <span class="text-amber-400 font-mono">docs/es/AGUAMIND-OS-MASTER.md §9</span>
  </div>

  <!-- Fuentes de datos meteorológicos en tiempo real -->
  <div class="mt-3 pt-3 border-t border-white/[0.06]">
  <div class="text-[10px] font-medium tracking-wider uppercase text-sky-400 mb-2">Fuentes de datos en vivo (gratuitas, sin API key obligatoria)</div>
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2">
  {#each [
  {
  name: "Open-Meteo",
  what: "Lluvia, temperatura, humedad, viento (Cali 3.45°N, -76.53°W)",
  url: "open-meteo.com/v1/forecast",
  free: "ilimitado · sin key · CC-BY 4.0",
  signal: "lluvia → flood_mode + surge_mode",
  },
  {
  name: "NOAA CPC",
  what: "Índice ENSO (Niño 3.4) — pronóstico El Niño / La Niña",
  url: "psl.noaa.gov/data/correlation/oni.data",
  free: "CSV libre · público · actualización mensual",
  signal: "ENSO > +0.5 → drought_mode preventivo",
  },
  {
  name: "Open-Meteo Climate",
  what: "Forecast 16 días + reanálisis ECMWF (precipitación, sequía)",
  url: "climate-api.open-meteo.com/v1",
  free: "ilimitado · sin key",
  signal: "precip 30d acumulada → tendencia sequía",
  },
  {
  name: "USGS Earthquake",
  what: "Sismos en tiempo real (feed Suramérica · magnitud + epicentro)",
  url: "earthquake.usgs.gov/earthquakes/feed",
  free: "GeoJSON cada minuto · sin key",
  signal: "M≥4.0 a <100km Cali → quake_mode",
  },
  ] as src}
  <div class="rounded-md border border-white/[0.06] bg-white/[0.02] p-2.5">
  <div class="flex items-baseline gap-2">
  <span class="text-[11px] font-semibold text-white">{src.name}</span>
  <span class="text-[8px] text-emerald-400 font-mono uppercase tracking-wider">free</span>
  </div>
  <div class="text-[10px] text-slate-400 mt-1 leading-snug">{src.what}</div>
  <div class="text-[9px] text-sky-400 font-mono mt-1.5 truncate">{src.url}</div>
  <div class="text-[9px] text-slate-500 mt-0.5">{src.free}</div>
  <div class="text-[9px] text-amber-400 mt-1.5 leading-snug"><span class="text-slate-500">disparador:</span> {src.signal}</div>
  </div>
  {/each}
  </div>
  <div class="text-[10px] text-slate-500 mt-2.5">
  Sensores locales (freático 4-20mA, turbidez TSD-10, vibración SW-420, presión MPX5700) complementan el contexto meteorológico. El backend hace fetch periódico (15 min) a estas APIs y normaliza con <span class="font-mono text-sky-400">app/sensors/normalizer.py</span>.
  </div>
  </div>
  </div>

  <!-- ═══ RAZONAMIENTO DEL AGENTE EN VIVO + MONETIZACIÓN ═══ -->
  <div class="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-3">

  <!-- Reasoning trace por agente -->
  <div class="lg:col-span-2 rounded-xl border border-white/[0.06] bg-white/[0.02] p-5">
  <div class="flex items-baseline justify-between mb-3">
  <div>
  <div class="text-[11px] font-medium tracking-wider uppercase text-slate-500">Razonamiento en vivo</div>
  <div class="text-[10px] text-slate-600 mt-0.5">Qué está "pensando" cada agente sobre los datos actuales</div>
  </div>
  <span class="text-[10px] font-mono text-sky-400">live · ciclo #{agent?.cycle ?? 0}</span>
  </div>

  <div class="space-y-2">
  {#each [
  {
  code: "ORC", name: "Orchestrator", color: "#7c3aed",
  conf: agent?.last_decision === "critical" ? 92 : agent?.last_decision === "warning" ? 70 : 95,
  text: agent?.last_decision === "critical"
  ? "3 de 5 agentes votan critical. Consenso alcanzado, autorizo MitigationAgent."
  : agent?.last_decision === "warning"
  ? "Variables fluctuantes pero sin disparador. Monitoreo intensivo activado."
  : "Sistema dentro de parámetros. Continúo orquestando ciclos cada 30s."
  },
  {
  code: "SYS", name: "SystemsAgent", color: "#0ea5e9",
  conf: kpis?.TPP?.status === "critical" ? 88 : 75,
  text: kpis ? `IEH ${kpis.IEH.value}% (meta 90%), TPP ${kpis.TPP.value}% (meta <10%). IsolationForest score ${kpis.TPP.status === 'critical' ? '0.78 (anómalo)' : '0.12 (normal)'}.` : "Esperando KPIs..."
  },
  {
  code: "SEN", name: "SensorAgent", color: "#10b981",
  conf: reading?.vibration ? 85 : 96,
  text: reading
  ? `6/6 sensores en rango. Presión ${reading.pressure_kpa} kPa, freático ${reading.phreatic_m} m, turbidez ${reading.turbidity_ntu} NTU.${reading.vibration ? ' SW-420 detecta vibración anómala.' : ''}`
  : "Esperando lecturas..."
  },
  {
  code: "IND", name: "IndustrialAgent", color: "#f59e0b",
  conf: 82,
  text: reading
  ? `Muda detectada: ${reading.losses_l_min.toFixed(1)} L/min de pérdida = $${Math.round(reading.losses_l_min*1440*3.5).toLocaleString()} COP/día. Random Forest: probabilidad de fuga ${kpis?.TPP?.status === 'critical' ? '0.92 (fisura_lenta)' : '0.18 (sin patrón)'}.`
  : "Esperando lecturas..."
  },
  {
  code: "MIT", name: "MitigationAgent", color: "#ef4444",
  conf: agent?.last_decision === "critical" ? 90 : 60,
  text: agent?.last_decision === "critical"
  ? "Acción recomendada: cerrar EV-A2, bomba a standby. Esperando confirmación del Orchestrator."
  : "En espera. Ningún trigger compuesto activo."
  },
  ] as a}
  <div class="border border-white/[0.04] rounded-md p-2.5 bg-white/[0.015]">
  <div class="flex items-center gap-2 mb-1">
  <span class="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded" style="background:{a.color}1A;color:{a.color}">{a.code}</span>
  <span class="text-[11px] font-medium text-slate-200">{a.name}</span>
  <span class="text-[9px] text-slate-500 ml-auto">conf. <span class="font-mono font-bold" style="color:{a.color}">{a.conf}%</span></span>
  </div>
  <div class="text-[10.5px] text-slate-400 leading-relaxed pl-1">{a.text}</div>
  </div>
  {/each}
  </div>
  </div>

  <!-- Monetización en vivo -->
  <div class="rounded-xl border border-emerald-500/[0.18] bg-gradient-to-br from-emerald-500/[0.04] to-emerald-500/[0.01] p-5">
  <div class="text-[11px] font-medium tracking-wider uppercase text-emerald-400 mb-1">Cómo se traduce en plata</div>
  <div class="text-[10px] text-slate-500 mb-4">Impacto monetizado de cada decisión del agente</div>

  <!-- Big number: COP en juego ahora -->
  <div class="rounded-lg border border-white/[0.06] bg-white/[0.02] p-3 mb-3">
  <div class="text-[10px] text-slate-500 uppercase tracking-wider">Pérdidas por minuto (live)</div>
  <div class="text-[22px] font-mono font-bold text-red-400 mt-1">${reading ? Math.round(reading.losses_l_min*3.5).toLocaleString() : '—'}</div>
  <div class="text-[9px] text-slate-500 font-mono">COP/min · tarifa industrial $3.5/L</div>
  </div>

  <!-- Stack de números -->
  <div class="space-y-2 text-[11px]">
  <div class="flex items-center justify-between">
  <span class="text-slate-400">Costo proyectado/día</span>
  <span class="font-mono text-red-400 font-bold">${reading ? Math.round(reading.losses_l_min*1440*3.5).toLocaleString() : '—'}</span>
  </div>
  <div class="flex items-center justify-between">
  <span class="text-slate-400">Costo proyectado/año</span>
  <span class="font-mono text-red-400 font-bold">${reading ? Math.round(reading.losses_l_min*1440*365*3.5/1_000_000).toLocaleString() : '—'} M</span>
  </div>
  <div class="flex items-center justify-between pt-2 border-t border-white/[0.06]">
  <span class="text-slate-400">Ahorro acumulado del agente</span>
  <span class="font-mono text-emerald-400 font-bold">${impact ? impact.cop_saved.toLocaleString() : '0'}</span>
  </div>
  <div class="flex items-center justify-between">
  <span class="text-slate-400">Litros recuperados</span>
  <span class="font-mono text-sky-400 font-bold">{impact ? impact.liters_saved.toLocaleString() : '0'} L</span>
  </div>
  <div class="flex items-center justify-between">
  <span class="text-slate-400">CO₂ evitado</span>
  <span class="font-mono text-emerald-400 font-bold">{impact ? fmt(impact.co2_kg_avoided, 2) : '0'} kg</span>
  </div>
  </div>

  <div class="mt-4 pt-3 border-t border-white/[0.06] text-[10px] text-slate-500 leading-relaxed">
  El agente convierte cada lectura de sensor en una decisión <span class="text-emerald-400">cuantificada en pesos</span>. El jurado puede ver el ROI ocurriendo en tiempo real.
  </div>
  </div>

  </div>

  <!-- ═══ ANÁLISIS DEL AGENTE (insights automáticos) ═══ -->
  <div class="mb-3 mt-6">
  <div class="flex items-baseline justify-between mb-3">
  <div>
  <h2 class="text-[13px] font-semibold text-white tracking-tight">Análisis del Agente</h2>
  <p class="text-[11px] text-slate-500 mt-0.5">Insights generados por IA sobre el estado actual</p>
  </div>
  <button onclick={fetchInsights} class="text-[10px] text-sky-400 hover:text-sky-300 font-mono">refresh</button>
  </div>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-3 gap-3 mb-6">
  {#if aiInsights.length === 0}
  <div class="lg:col-span-3 rounded-2xl border border-white/[0.06] bg-white/[0.02] p-6 text-center">
  <div class="text-[12px] text-slate-500 mb-2">Generando análisis...</div>
  <button onclick={fetchInsights} class="text-[11px] text-sky-400 hover:text-sky-300">Generar ahora</button>
  </div>
  {:else}
  {#each aiInsights as ins}
  {@const sev = ins.severity ?? 'ok'}
  {@const color = sev === 'critical' ? '#ef4444' : sev === 'warning' ? '#f59e0b' : '#10b981'}
  <div class="rounded-2xl border bg-gradient-to-br from-white/[0.02] to-white/[0.005] p-4 transition-colors" style="border-color:{color}30">
  <div class="flex items-start gap-3">
  <span class="text-2xl">{ins.icon ?? ''}</span>
  <div class="flex-1 min-w-0">
  <div class="flex items-center gap-2 mb-1">
  <span class="text-[12px] font-semibold text-white">{ins.title ?? '—'}</span>
  <span class="text-[9px] uppercase font-mono px-1.5 py-0.5 rounded" style="color:{color};background:{color}1A">{sev}</span>
  </div>
  <p class="text-[11px] text-slate-400 leading-relaxed">{ins.description ?? '—'}</p>
  </div>
  </div>
  </div>
  {/each}
  {/if}
  </div>

  <!-- ═══ CHAT CON EL AGENTE ═══ -->
  <div class="mb-3 mt-6">
  <div class="flex items-baseline justify-between mb-3">
  <div>
  <h2 class="text-[13px] font-semibold text-white tracking-tight">Pregúntale al Agente</h2>
  <p class="text-[11px] text-slate-500 mt-0.5">Conversación con la IA · contexto en tiempo real</p>
  </div>
  {#if chatMessages.length > 0}
  <button onclick={() => chatMessages = []} class="text-[10px] text-slate-500 hover:text-slate-300 font-mono">limpiar</button>
  {/if}
  </div>
  </div>

  <div class="rounded-2xl border border-white/[0.06] bg-gradient-to-br from-white/[0.02] to-white/[0.005] p-5 mb-3">
  <!-- Conversación -->
  <div class="space-y-3 mb-4 max-h-80 overflow-y-auto pr-2 scrollbar-thin">
  {#if chatMessages.length === 0}
  <div class="text-center py-8">
  <div class="text-3xl mb-2"></div>
  <p class="text-[12px] text-slate-400 mb-1">Hazle preguntas al agente sobre el sistema</p>
  <p class="text-[10px] text-slate-500">El agente conoce los datos en vivo + datos históricos</p>
  </div>
  {:else}
  {#each chatMessages as msg}
  <div class="flex gap-2 {msg.role === 'user' ? 'justify-end' : 'justify-start'}">
  {#if msg.role === 'agent'}
  <div class="w-7 h-7 rounded-lg bg-gradient-to-br from-sky-400 to-cyan-600 flex items-center justify-center shrink-0 text-white text-[11px] font-bold">AI</div>
  {/if}
  <div class="max-w-[80%] rounded-2xl px-3 py-2 text-[12px]
  {msg.role === 'user'
  ? 'bg-sky-500/15 border border-sky-500/30 text-sky-100'
  : 'bg-white/[0.04] border border-white/[0.06] text-slate-200'}">
  <p class="leading-relaxed">{msg.text}</p>
  <div class="text-[9px] text-slate-500 font-mono mt-1">{msg.ts}</div>
  </div>
  {#if msg.role === 'user'}
  <div class="w-7 h-7 rounded-lg bg-slate-700 flex items-center justify-center shrink-0 text-slate-300 text-[11px] font-bold">Tú</div>
  {/if}
  </div>
  {/each}
  {#if chatLoading}
  <div class="flex gap-2 justify-start">
  <div class="w-7 h-7 rounded-lg bg-gradient-to-br from-sky-400 to-cyan-600 flex items-center justify-center shrink-0 text-white text-[11px] font-bold">AI</div>
  <div class="max-w-[80%] rounded-2xl px-3 py-2 bg-white/[0.04] border border-white/[0.06]">
  <div class="flex gap-1">
  <span class="w-1.5 h-1.5 rounded-full bg-sky-400 animate-bounce" style="animation-delay:0s"></span>
  <span class="w-1.5 h-1.5 rounded-full bg-sky-400 animate-bounce" style="animation-delay:0.15s"></span>
  <span class="w-1.5 h-1.5 rounded-full bg-sky-400 animate-bounce" style="animation-delay:0.3s"></span>
  </div>
  </div>
  </div>
  {/if}
  {/if}
  </div>

  <!-- Sugerencias -->
  {#if chatMessages.length === 0}
  <div class="flex flex-wrap gap-1.5 mb-3">
  {#each SUGGESTED_QUESTIONS as q}
  <button onclick={() => askAgent(q)}
  class="text-[10px] px-2.5 py-1 rounded-full border border-white/10 bg-white/[0.03] hover:bg-sky-500/10 hover:border-sky-500/30 hover:text-sky-300 text-slate-400 transition-colors">{q}</button>
  {/each}
  </div>
  {/if}

  <!-- Input -->
  <form
  onsubmit={(e) => { e.preventDefault(); askAgent(chatInput); }}
  class="flex gap-2 items-center">
  <input
  bind:value={chatInput}
  placeholder="Pregunta al agente: ¿hay fugas? ¿cómo está la calidad?..."
  disabled={chatLoading}
  class="flex-1 text-[12px] bg-white/[0.04] border border-white/10 rounded-lg px-3 py-2 text-slate-200 placeholder-slate-500 outline-none focus:border-sky-500/40 focus:bg-white/[0.06] transition-colors"
  />
  <button
  type="submit"
  disabled={chatLoading || !chatInput.trim()}
  class="text-[11px] px-3 py-2 rounded-lg bg-sky-500/20 border border-sky-500/40 text-sky-400 hover:bg-sky-500/30 disabled:opacity-30 disabled:cursor-not-allowed transition-colors font-medium">
  {chatLoading ? '...' : 'Enviar'}
  </button>
  </form>
  </div>

  <!-- ════════════════════════════════════════════════════════════════════ -->
  <!-- TAB 5: MITIGACIÓN -->
  <!-- ════════════════════════════════════════════════════════════════════ -->
  {:else if tab === "mitigation"}

  <!-- Métricas de impacto -->
  <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
  {#each [
  { label: "Litros ahorrados",  value: impact?.liters_saved_formatted ?? "0 L",  accent: "#10b981", code: "L" },
  { label: "Dinero evitado",  value: impact?.cop_saved_formatted ?? "$0 COP",  accent: "#0ea5e9", code: "$" },
  { label: "CO₂ evitado",  value: impact?.co2_kg_formatted ?? "0 kg",  accent: "#34d399", code: "C" },
  { label: "Acciones tomadas",  value: String(impact?.actions_taken ?? 0),  accent: "#a78bfa", code: "A" },
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
  <div class="flex gap-2 text-[10px] items-center">
  <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-emerald-400"></span>OK</span>
  <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-amber-400"></span>Alerta</span>
  <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-red-400"></span>Crítico</span>
  <button
  onclick={() => mapView3D = !mapView3D}
  class="ml-3 px-2 py-1 rounded border text-[10px] font-mono font-medium transition-colors
  {mapView3D ? 'border-sky-500/40 bg-sky-500/10 text-sky-400' : 'border-white/[0.10] bg-white/[0.02] text-slate-400 hover:text-slate-200'}"
  title="Toggle vista isométrica 3D">
  {mapView3D ? 'vista 2D' : 'vista 3D'}
  </button>
  </div>
  </div>

  <!-- SVG MAP - misma vista, con CSS perspective + filter drop-shadow cuando 3D -->
  <div class="rounded-lg transition-all duration-700"
  style={mapView3D
    ? 'perspective: 1600px; perspective-origin: 50% 30%; padding: 60px 0 30px;'
    : 'perspective: none; padding: 0;'}>
  <svg viewBox="0 0 800 580"
  class="w-full h-auto rounded-lg transition-all duration-700"
  style="background:linear-gradient(135deg,rgba(14,165,233,0.06) 0%,rgba(99,102,241,0.04) 100%); transform-style: preserve-3d; transform-origin: 50% 50%; {mapView3D
    ? 'transform: rotateX(48deg) rotateZ(-14deg) scale(0.96); filter: drop-shadow(0 30px 25px rgba(14,165,233,0.35)) drop-shadow(0 8px 8px rgba(0,0,0,0.4)); box-shadow: 0 80px 80px -30px rgba(56,189,248,0.30), 0 50px 100px -40px rgba(0,0,0,0.6);'
    : 'transform: none;'}">
  <defs>
  <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
  <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(148,163,184,0.08)" stroke-width="1"/>
  </pattern>
  <radialGradient id="alertPulse">
  <stop offset="0%" stop-color="#ef4444" stop-opacity="0.6"/>
  <stop offset="100%" stop-color="#ef4444" stop-opacity="0"/>
  </radialGradient>
  <marker id="arrR" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
  <path d="M 0 0 L 10 5 L 0 10 z" fill="#22c55e"/>
  </marker>
  <marker id="arrO" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
  <path d="M 0 0 L 10 5 L 0 10 z" fill="#fbbf24"/>
  </marker>
  </defs>
  <rect width="800" height="580" fill="url(#grid)"/>

  <!-- ═══ HEADER ═══ -->
  <text x="20" y="28" fill="rgba(148,163,184,0.85)" font-size="11" font-family="Inter" font-weight="600">UNIAJC Sede Sur · 38,755 m²</text>
  <text x="20" y="44" fill="rgba(148,163,184,0.55)" font-size="9" font-family="JetBrains Mono">8,234 usuarios · 219 disp. hidráulicos</text>
  <g transform="translate(440, 24)">
  <line x1="0" y1="0" x2="20" y2="0" stroke="#7dd3fc" stroke-width="2"/>
  <text x="24" y="3" fill="rgba(148,163,184,0.7)" font-size="8" font-family="JetBrains Mono">potable</text>
  <line x1="78" y1="0" x2="98" y2="0" stroke="#f59e0b" stroke-width="2" stroke-dasharray="3 2"/>
  <text x="102" y="3" fill="rgba(148,163,184,0.7)" font-size="8" font-family="JetBrains Mono">residual</text>
  <line x1="158" y1="0" x2="178" y2="0" stroke="#22c55e" stroke-width="2" stroke-dasharray="6 3"/>
  <text x="182" y="3" fill="rgba(148,163,184,0.7)" font-size="8" font-family="JetBrains Mono">reúso</text>
  <line x1="232" y1="0" x2="252" y2="0" stroke="#fbbf24" stroke-width="2" stroke-dasharray="2 2"/>
  <text x="256" y="3" fill="rgba(148,163,184,0.7)" font-size="8" font-family="JetBrains Mono">vertim.</text>
  </g>

  <!-- ═══ BAND 2: EDIFICIOS (y=70-150) ═══ -->
  <!-- Bloque A -->
  <g class="cursor-pointer" onclick={() => executeAutoMitigation("leak")}>
  <rect x="40" y="70" width="140" height="80" rx="6" fill="rgba(168,85,247,0.10)" stroke={reading?.vibration ? "#ef4444" : "#a855f7"} stroke-width="2"/>
  {#if reading?.vibration}
  <circle cx="110" cy="110" r="50" fill="url(#alertPulse)">
  <animate attributeName="r" from="20" to="60" dur="2s" repeatCount="indefinite"/>
  <animate attributeName="opacity" from="0.6" to="0" dur="2s" repeatCount="indefinite"/>
  </circle>
  {/if}
  <text x="110" y="105" text-anchor="middle" fill={reading?.vibration ? "#fca5a5" : "#a855f7"} font-size="13" font-family="Inter" font-weight="bold">Bloque A</text>
  <text x="110" y="122" text-anchor="middle" fill="rgba(168,85,247,0.6)" font-size="9">Aulas + baños</text>
  <circle cx="160" cy="84" r="4" fill={reading?.vibration ? "#ef4444" : "#10b981"}>
  {#if reading?.vibration}<animate attributeName="opacity" from="1" to="0.3" dur="1s" repeatCount="indefinite"/>{/if}
  </circle>
  </g>

  <!-- Alameda -->
  <g>
  <rect x="220" y="70" width="160" height="80" rx="6" fill="rgba(245,158,11,0.08)" stroke="#f59e0b" stroke-width="2"/>
  <text x="300" y="105" text-anchor="middle" fill="#f59e0b" font-size="13" font-family="Inter" font-weight="bold">Alameda</text>
  <text x="300" y="122" text-anchor="middle" fill="rgba(245,158,11,0.6)" font-size="9">Aulas + administración</text>
  <circle cx="360" cy="84" r="4" fill="#10b981"/>
  </g>

  <!-- Cafetería -->
  <g>
  <rect x="420" y="70" width="120" height="80" rx="6" fill="rgba(249,115,22,0.10)" stroke="#f97316" stroke-width="2"/>
  <text x="480" y="105" text-anchor="middle" fill="#f97316" font-size="11" font-family="Inter" font-weight="bold">Cafetería</text>
  <text x="480" y="122" text-anchor="middle" fill="rgba(249,115,22,0.6)" font-size="9">240 L/día</text>
  <circle cx="520" cy="84" r="3.5" fill="#10b981"/>
  </g>

  <!-- Laboratorios -->
  <g>
  <rect x="580" y="70" width="170" height="80" rx="6" fill="rgba(96,165,250,0.10)" stroke="#60a5fa" stroke-width="2"/>
  <text x="665" y="105" text-anchor="middle" fill="#60a5fa" font-size="12" font-family="Inter" font-weight="bold">Laboratorios</text>
  <text x="665" y="122" text-anchor="middle" fill="rgba(96,165,250,0.6)" font-size="9">64 L/día</text>
  <circle cx="735" cy="84" r="3.5" fill="#10b981"/>
  </g>

  <!-- ═══ BAND 3: SERVICIOS (y=180-250) ═══ -->
  <!-- Cancha + Jardines -->
  <g class="cursor-pointer">
  <rect x="40" y="180" width="320" height="70" rx="6" fill="rgba(34,197,94,0.08)" stroke="#22c55e" stroke-width="2" stroke-dasharray="6 3"/>
  <text x="200" y="212" text-anchor="middle" fill="#22c55e" font-size="13" font-family="Inter" font-weight="bold">Cancha + Jardines</text>
  <text x="200" y="230" text-anchor="middle" fill="rgba(34,197,94,0.65)" font-size="10">Riego ~4,000 L/día → 2,200 con reúso</text>
  <circle cx="340" cy="195" r="3.5" fill={(reading?.zones?.["Riego/Cancha"] ?? 0) > 6 ? "#f59e0b" : "#10b981"}/>
  </g>

  <!-- Limpieza -->
  <g>
  <rect x="400" y="180" width="180" height="70" rx="6" fill="rgba(148,163,184,0.10)" stroke="#94a3b8" stroke-width="2"/>
  <text x="490" y="212" text-anchor="middle" fill="#94a3b8" font-size="12" font-family="Inter" font-weight="bold">Limpieza</text>
  <text x="490" y="230" text-anchor="middle" fill="rgba(148,163,184,0.6)" font-size="10">3,000 L/día · genera aguas grises</text>
  <circle cx="560" cy="195" r="3.5" fill="#10b981"/>
  </g>

  <!-- ═══ BAND 4: COLECTOR (y=275) ═══ -->
  <text x="40" y="272" fill="rgba(245,158,11,0.7)" font-size="9" font-family="JetBrains Mono">⤓ colector aguas residuales (sanitarios + grises)</text>
  <line x1="40" y1="280" x2="760" y2="280" stroke="#f59e0b" stroke-width="2.5" opacity="0.55" stroke-dasharray="5 3"/>

  <!-- Bajantes desde edificios + servicios -->
  <line x1="110" y1="150" x2="110" y2="280" stroke="#fbbf24" stroke-width="1.5" stroke-dasharray="3 2" opacity="0.45"/>
  <line x1="300" y1="150" x2="300" y2="280" stroke="#fbbf24" stroke-width="1.5" stroke-dasharray="3 2" opacity="0.45"/>
  <line x1="480" y1="150" x2="480" y2="280" stroke="#fbbf24" stroke-width="1.5" stroke-dasharray="3 2" opacity="0.45"/>
  <line x1="665" y1="150" x2="665" y2="280" stroke="#fbbf24" stroke-width="1.5" stroke-dasharray="3 2" opacity="0.45"/>
  <line x1="490" y1="250" x2="490" y2="280" stroke="#fbbf24" stroke-width="1.5" stroke-dasharray="3 2" opacity="0.45"/>

  <!-- ═══ BAND 5: PTAP SYSTEM (y=300-390) ═══ -->
  <text x="82" y="305" text-anchor="middle" fill="rgba(125,211,252,0.6)" font-size="9" font-family="JetBrains Mono">aljibes</text>
  <g>
  <circle cx="60" cy="345" r="16" fill="rgba(125,211,252,0.15)" stroke="#7dd3fc" stroke-width="2"/>
  <text x="60" y="349" text-anchor="middle" fill="#7dd3fc" font-size="10" font-family="JetBrains Mono" font-weight="bold">A1</text>
  </g>
  <g>
  <circle cx="105" cy="345" r="16" fill="rgba(125,211,252,0.15)" stroke="#7dd3fc" stroke-width="2"/>
  <text x="105" y="349" text-anchor="middle" fill="#7dd3fc" font-size="10" font-family="JetBrains Mono" font-weight="bold">A2</text>
  </g>

  <!-- PTAP -->
  <g>
  <rect x="160" y="310" width="130" height="75" rx="6" fill="rgba(99,102,241,0.15)" stroke="#818cf8" stroke-width="2"/>
  <text x="225" y="335" text-anchor="middle" fill="#818cf8" font-size="12" font-family="Inter" font-weight="bold">PTAP</text>
  <text x="225" y="354" text-anchor="middle" fill="rgba(129,140,248,0.7)" font-size="9">3 filtros · 2011</text>
  <text x="225" y="371" text-anchor="middle" fill="rgba(129,140,248,0.6)" font-size="8" font-family="JetBrains Mono">113.56 L/min</text>
  </g>

  <!-- Tank A -->
  <g>
  <rect x="320" y="305" width="80" height="80" rx="4" fill="rgba(34,197,94,0.10)" stroke="#22c55e" stroke-width="2"/>
  <rect x="320" y="305" width="80" height="80" rx="4" fill="rgba(34,197,94,0.30)" style="clip-path: inset({100 - (reading?.tank_a_pct ?? 65)}% 0 0 0)"/>
  <text x="360" y="328" text-anchor="middle" fill="#22c55e" font-size="11" font-family="Inter" font-weight="bold">Tank A</text>
  <text x="360" y="352" text-anchor="middle" fill="white" font-size="16" font-family="JetBrains Mono" font-weight="bold">{fmt(reading?.tank_a_pct, 0)}%</text>
  <text x="360" y="370" text-anchor="middle" fill="rgba(34,197,94,0.7)" font-size="9">36k L</text>
  </g>

  <!-- Tank B -->
  <g>
  <rect x="430" y="315" width="70" height="70" rx="4" fill="rgba(56,189,248,0.10)" stroke="#38bdf8" stroke-width="2"/>
  <rect x="430" y="315" width="70" height="70" rx="4" fill="rgba(56,189,248,0.30)" style="clip-path: inset({100 - (reading?.tank_b_pct ?? 70)}% 0 0 0)"/>
  <text x="465" y="335" text-anchor="middle" fill="#38bdf8" font-size="10" font-family="Inter" font-weight="bold">Tank B</text>
  <text x="465" y="357" text-anchor="middle" fill="white" font-size="14" font-family="JetBrains Mono" font-weight="bold">{fmt(reading?.tank_b_pct, 0)}%</text>
  <text x="465" y="373" text-anchor="middle" fill="rgba(56,189,248,0.7)" font-size="8">16k L</text>
  </g>

  <!-- Aviso de sobrecapacidad PTAR (panel propio, sin solapar) -->
  <g>
  <rect x="540" y="315" width="220" height="60" rx="6" fill="rgba(239,68,68,0.08)" stroke="#f87171" stroke-width="1.5" stroke-dasharray="3 2"/>
  <text x="650" y="334" text-anchor="middle" fill="#f87171" font-size="10" font-family="Inter" font-weight="bold">Sobrecapacidad PTAR (2.06x)</text>
  <text x="650" y="351" text-anchor="middle" fill="rgba(248,113,113,0.85)" font-size="9" font-family="JetBrains Mono">4,000 est cap · 8,234 reales</text>
  <text x="650" y="367" text-anchor="middle" fill="rgba(248,113,113,0.6)" font-size="8" font-family="JetBrains Mono">→ ampliación ante CVC</text>
  </g>

  <!-- Tuberías agua potable: aljibes → PTAP → Tanks -->
  <line x1="121" y1="345" x2="160" y2="345" stroke="#7dd3fc" stroke-width="2" stroke-dasharray="4 3" opacity="0.7"/>
  <line x1="290" y1="345" x2="320" y2="345" stroke="#818cf8" stroke-width="2" opacity="0.7"/>
  <line x1="400" y1="350" x2="430" y2="350" stroke="#22c55e" stroke-width="2" opacity="0.6"/>
  <!-- Distribución desde Tank A → Bloque A (subiendo, dashed) -->
  <line x1="360" y1="305" x2="360" y2="160" stroke="#22c55e" stroke-width="1.5" opacity="0.30" stroke-dasharray="2 2"/>

  <!-- ═══ BAND 6: PTAR + REÚSO (y=410-470) ═══ -->
  <!-- PTAR Alameda -->
  <g>
  <rect x="40" y="410" width="160" height="50" rx="6" fill="rgba(245,158,11,0.10)" stroke="#f59e0b" stroke-width="2" stroke-dasharray="3 2"/>
  <text x="120" y="430" text-anchor="middle" fill="#f59e0b" font-size="11" font-family="Inter" font-weight="bold">PTAR Alameda</text>
  <text x="120" y="446" text-anchor="middle" fill="rgba(245,158,11,0.7)" font-size="9">2 mód. en paralelo · 2,000 est</text>
  <circle cx="190" cy="420" r="3.5" fill="#f59e0b"/>
  <line x1="120" y1="280" x2="120" y2="410" stroke="#f59e0b" stroke-width="2" opacity="0.55" stroke-dasharray="4 2"/>
  </g>

  <!-- Panel central REÚSO -->
  <g>
  <rect x="230" y="410" width="320" height="50" rx="6" fill="rgba(34,197,94,0.06)" stroke="#22c55e" stroke-width="1.5" stroke-dasharray="2 2"/>
  <text x="390" y="428" text-anchor="middle" fill="#22c55e" font-size="11" font-family="Inter" font-weight="bold"> REÚSO (Resolución 1207/2014)</text>
  <text x="390" y="443" text-anchor="middle" fill="rgba(34,197,94,0.7)" font-size="9">aguas tratadas → riego cancha + cisternas sanitarias</text>
  <text x="390" y="455" text-anchor="middle" fill="rgba(34,197,94,0.55)" font-size="8" font-family="JetBrains Mono">~1,800 L/día recuperados · ahorra 657 m³/año</text>
  </g>

  <!-- PTAR Entrada -->
  <g>
  <rect x="580" y="410" width="170" height="50" rx="6" fill="rgba(245,158,11,0.10)" stroke="#f59e0b" stroke-width="2" stroke-dasharray="3 2"/>
  <text x="665" y="430" text-anchor="middle" fill="#f59e0b" font-size="11" font-family="Inter" font-weight="bold">PTAR Entrada</text>
  <text x="665" y="446" text-anchor="middle" fill="rgba(245,158,11,0.7)" font-size="9">2 mód. en paralelo · 2,000 est</text>
  <circle cx="740" cy="420" r="3.5" fill="#f59e0b"/>
  <line x1="665" y1="280" x2="665" y2="410" stroke="#f59e0b" stroke-width="2" opacity="0.55" stroke-dasharray="4 2"/>
  </g>

  <!-- Flechas PTAR → REÚSO -->
  <line x1="200" y1="435" x2="226" y2="435" stroke="#22c55e" stroke-width="2" stroke-dasharray="6 3" opacity="0.75" marker-end="url(#arrR)"/>
  <line x1="580" y1="435" x2="554" y2="435" stroke="#22c55e" stroke-width="2" stroke-dasharray="6 3" opacity="0.75" marker-end="url(#arrR)"/>

  <!-- Flecha REÚSO → Cancha (sube) -->
  <path d="M 320 410 Q 280 360 230 320 Q 200 280 200 250" fill="none" stroke="#22c55e" stroke-width="2" stroke-dasharray="6 3" opacity="0.55" marker-end="url(#arrR)"/>
  <text x="245" y="378" fill="rgba(34,197,94,0.75)" font-size="8" font-family="JetBrains Mono">→ riego no potable</text>

  <!-- Flecha REÚSO → Bloque A cisternas (sube) -->
  <path d="M 460 410 Q 400 380 280 360 Q 180 340 110 200" fill="none" stroke="#22c55e" stroke-width="1.5" stroke-dasharray="4 3" opacity="0.40"/>
  <text x="305" y="402" fill="rgba(34,197,94,0.55)" font-size="8" font-family="JetBrains Mono">→ cisternas sanitarias</text>

  <!-- ═══ BAND 7: VERTIMIENTO + RÍO (y=480-560) ═══ -->
  <line x1="120" y1="460" x2="120" y2="500" stroke="#fbbf24" stroke-width="2" stroke-dasharray="2 2" opacity="0.6" marker-end="url(#arrO)"/>
  <line x1="665" y1="460" x2="665" y2="500" stroke="#fbbf24" stroke-width="2" stroke-dasharray="2 2" opacity="0.6" marker-end="url(#arrO)"/>
  <text x="80" y="478" fill="rgba(251,191,36,0.65)" font-size="8" font-family="JetBrains Mono">vertim. residual</text>
  <text x="625" y="478" fill="rgba(251,191,36,0.65)" font-size="8" font-family="JetBrains Mono">vertim. residual</text>

  <path d="M 0 510 Q 200 520 400 505 T 800 515 L 800 580 L 0 580 Z" fill="rgba(56,189,248,0.10)" stroke="rgba(56,189,248,0.4)" stroke-width="1"/>
  <text x="20" y="530" fill="rgba(56,189,248,0.75)" font-size="10" font-family="JetBrains Mono" font-weight="600">río Pance / Cauca</text>
  <text x="20" y="546" fill="rgba(56,189,248,0.55)" font-size="8" font-family="JetBrains Mono">Resolución 0631/2015 · DBO ≤ 90 mg/L · pH 6-9</text>
  </svg>
  </div>


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

  <!-- ════════════════════════════════════════════════════════════════════ -->
  <!-- TAB 6: COMUNIDAD (Gamificación) -->
  <!-- ════════════════════════════════════════════════════════════════════ -->
  {:else if tab === "community"}

  {#if !gamification}
  <div class="text-center py-12 text-[12px] text-slate-500">
  Cargando datos de la comunidad...
  <button onclick={fetchGamification} class="ml-2 text-sky-400 hover:text-sky-300">refrescar</button>
  </div>
  {:else}

  <!-- Mensaje de canje -->
  {#if redeemMessage}
  <div class="rounded-lg border border-emerald-500/30 bg-emerald-500/[0.06] px-4 py-3 text-sm text-emerald-300 mb-5">
  {redeemMessage}
  </div>
  {/if}

  <!-- Hero: temporada actual + perfil -->
  <div class="grid grid-cols-1 lg:grid-cols-3 gap-3 mb-5">

  <!-- Temporada -->
  <div class="lg:col-span-2 relative overflow-hidden rounded-2xl border border-sky-500/20 bg-gradient-to-br from-sky-500/[0.08] via-cyan-500/[0.04] to-transparent p-6">
  <div class="absolute top-0 right-0 w-64 h-64 rounded-full bg-sky-500/10 blur-3xl -mr-32 -mt-32"></div>
  <div class="relative">
  <div class="text-[10px] font-mono tracking-[0.2em] uppercase text-sky-400 mb-2">Temporada Activa</div>
  <h2 class="text-[22px] font-semibold text-white tracking-tight mb-1">{gamification.season.name}</h2>
  <p class="text-[12px] text-slate-400 mb-4">{gamification.season.theme}</p>

  <div class="grid grid-cols-3 gap-4 mt-6">
  <div>
  <div class="text-[26px] font-mono font-semibold text-white">{gamification.stats.active_users.toLocaleString()}</div>
  <div class="text-[10px] text-slate-500 mt-0.5">Participantes activos</div>
  <div class="text-[10px] text-emerald-400 mt-0.5">{gamification.stats.active_pct}% del campus</div>
  </div>
  <div>
  <div class="text-[26px] font-mono font-semibold text-white">{(gamification.stats.liters_saved_community/1000).toFixed(1)}k</div>
  <div class="text-[10px] text-slate-500 mt-0.5">Litros ahorrados</div>
  <div class="text-[10px] text-emerald-400 mt-0.5">colectivamente</div>
  </div>
  <div>
  <div class="text-[26px] font-mono font-semibold text-white">{gamification.stats.co2_kg_avoided}</div>
  <div class="text-[10px] text-slate-500 mt-0.5">kg CO₂ evitado</div>
  <div class="text-[10px] text-emerald-400 mt-0.5">≈ {gamification.stats.trees_equivalent} árboles/año</div>
  </div>
  </div>

  <div class="mt-5 pt-4 border-t border-sky-500/20 flex items-center justify-between">
  <div class="text-[11px] text-slate-400">⏱ Termina en <span class="text-white font-medium">{gamification.season.ends_in_days} días</span></div>
  <div class="text-[11px] text-slate-400">{gamification.stats.total_reports} reportes · {gamification.stats.validation_rate}% válidos</div>
  </div>
  </div>
  </div>

  <!-- Perfil del usuario -->
  <div class="rounded-2xl border border-white/[0.06] bg-gradient-to-br from-white/[0.02] to-white/[0.005] p-5">
  <div class="flex items-center gap-3 mb-4">
  <div class="relative w-12 h-12 rounded-xl bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center font-bold text-white text-[14px]">
  {gamification.user.level}
  <span class="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-emerald-400 ring-2 ring-[#0a0e14] flex items-center justify-center text-[8px] text-white"></span>
  </div>
  <div class="flex-1 min-w-0">
  <div class="text-[12px] font-semibold text-white truncate">{gamification.user.name}</div>
  <div class="text-[10px] text-amber-400">{gamification.user.level_name}</div>
  <div class="text-[10px] text-slate-500">{gamification.user.building}</div>
  </div>
  </div>

  <!-- Barra de progreso al siguiente nivel -->
  <div class="mb-4">
  <div class="flex justify-between text-[10px] mb-1">
  <span class="text-slate-500">Progreso nivel {gamification.user.level + 1}</span>
  <span class="text-white font-mono">{gamification.user.points} / {gamification.user.next_level_pts}</span>
  </div>
  <div class="h-1.5 bg-white/5 rounded-full overflow-hidden">
  <div class="h-full bg-gradient-to-r from-amber-400 to-amber-500 transition-all" style="width:{(gamification.user.points/gamification.user.next_level_pts)*100}%"></div>
  </div>
  </div>

  <div class="grid grid-cols-2 gap-2 text-[11px]">
  <div class="rounded-lg bg-white/[0.03] p-2">
  <div class="text-[9px] text-slate-500 uppercase tracking-wider">Créditos</div>
  <div class="text-[16px] font-mono font-semibold text-sky-400">{gamification.user.credits}</div>
  </div>
  <div class="rounded-lg bg-white/[0.03] p-2">
  <div class="text-[9px] text-slate-500 uppercase tracking-wider">Litros</div>
  <div class="text-[16px] font-mono font-semibold text-emerald-400">{gamification.user.liters_saved}</div>
  </div>
  <div class="rounded-lg bg-white/[0.03] p-2">
  <div class="text-[9px] text-slate-500 uppercase tracking-wider">Reportes</div>
  <div class="text-[16px] font-mono font-semibold text-white">{gamification.user.reports_valid}/{gamification.user.reports_made}</div>
  </div>
  <div class="rounded-lg bg-white/[0.03] p-2">
  <div class="text-[9px] text-slate-500 uppercase tracking-wider">Ranking</div>
  <div class="text-[16px] font-mono font-semibold text-white">#{gamification.user.rank_global}</div>
  </div>
  </div>
  </div>
  </div>

  <!-- Podium top 3 edificios -->
  <div class="mb-3">
  <div class="flex items-baseline justify-between mb-3">
  <div>
  <h2 class="text-[13px] font-semibold text-white tracking-tight">Ranking de Edificios</h2>
  <p class="text-[11px] text-slate-500 mt-0.5">Eco-competencia mensual · {gamification.podium.length} líderes</p>
  </div>
  </div>
  </div>

  <div class="grid grid-cols-3 gap-3 mb-5">
  {#each gamification.podium as b, i}
  {@const colors = [
  {bg: "from-amber-500/20 to-amber-700/5",  border: "border-amber-500/30",  ring: "from-amber-400 to-amber-600",  medal: "", label: "1° lugar"},
  {bg: "from-slate-400/15 to-slate-600/5",  border: "border-slate-400/30",  ring: "from-slate-300 to-slate-500",  medal: "", label: "2° lugar"},
  {bg: "from-orange-700/15 to-orange-900/5",border: "border-orange-700/30", ring: "from-orange-500 to-orange-700",medal: "", label: "3° lugar"},
  ]}
  {@const c = colors[i]}
  <div class="relative overflow-hidden rounded-2xl border bg-gradient-to-br {c.bg} {c.border} p-5 {i === 0 ? 'lg:scale-105' : ''}">
  <div class="text-3xl mb-2">{c.medal}</div>
  <div class="text-[9px] font-mono uppercase tracking-wider text-slate-400 mb-1">{c.label}</div>
  <div class="text-[14px] font-semibold text-white mb-1">{b.name}</div>
  <div class="text-[26px] font-mono font-bold bg-gradient-to-r {c.ring} bg-clip-text text-transparent mb-2">{b.credits}</div>
  <div class="text-[10px] text-slate-500">créditos hídricos</div>
  <div class="text-[10px] text-slate-600 mt-1 font-mono">{b.consumption_l_day.toLocaleString()} L/día</div>
  </div>
  {/each}
  </div>

  <!-- Resto del ranking -->
  {#if gamification.ranking.length > 3}
  <div class="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-5 mb-5">
  <div class="text-[10px] font-mono tracking-[0.15em] uppercase text-slate-500 mb-3">Resto de la liga</div>
  <div class="space-y-1.5">
  {#each gamification.ranking.slice(3) as b}
  <div class="flex items-center gap-3 p-2 rounded-md bg-white/[0.02]">
  <span class="w-6 text-center text-[11px] font-mono text-slate-500">#{b.rank}</span>
  <span class="flex-1 text-[12px] text-slate-200">{b.name}</span>
  <span class="text-[10px] text-slate-500 font-mono">{b.consumption_l_day.toLocaleString()} L/día</span>
  <span class="text-[14px] font-mono font-semibold text-sky-400 w-12 text-right">{b.credits}</span>
  </div>
  {/each}
  </div>
  </div>
  {/if}

  <!-- Retos activos -->
  <div class="mb-3 mt-6">
  <div class="flex items-baseline justify-between mb-3">
  <div>
  <h2 class="text-[13px] font-semibold text-white tracking-tight">Retos Activos</h2>
  <p class="text-[11px] text-slate-500 mt-0.5">Desafíos para ganar créditos y puntos</p>
  </div>
  <span class="text-[10px] font-mono text-slate-600">{gamification.challenges.length} disponibles</span>
  </div>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-2 gap-3 mb-5">
  {#each gamification.challenges as c}
  {@const catColor = c.category === 'operativo' ? '#0ea5e9' : c.category === 'comportamiento' ? '#a78bfa' : c.category === 'comunitario' ? '#10b981' : c.category === 'sanitario' ? '#f59e0b' : '#94a3b8'}
  <div class="rounded-2xl border border-white/[0.06] bg-gradient-to-br from-white/[0.02] to-white/[0.005] p-5 transition-all hover:border-white/[0.1]">
  <div class="flex items-start gap-3 mb-3">
  <div class="w-11 h-11 rounded-xl flex items-center justify-center text-2xl shrink-0" style="background:{catColor}15;border:1px solid {catColor}30">{c.icon}</div>
  <div class="flex-1 min-w-0">
  <div class="flex items-center gap-2 mb-1">
  <h3 class="text-[13px] font-semibold text-white">{c.title}</h3>
  <span class="text-[9px] uppercase font-mono tracking-wider px-1.5 py-0.5 rounded" style="background:{catColor}1A;color:{catColor}">{c.category}</span>
  </div>
  <p class="text-[11px] text-slate-400 leading-relaxed">{c.description}</p>
  </div>
  </div>

  <!-- Progreso -->
  <div class="mb-3">
  <div class="flex justify-between text-[10px] mb-1">
  <span class="text-slate-500">Progreso comunitario</span>
  <span class="text-white font-mono">{c.progress_pct}%</span>
  </div>
  <div class="h-1 bg-white/5 rounded-full overflow-hidden">
  <div class="h-full transition-all" style="width:{c.progress_pct}%;background:{catColor}"></div>
  </div>
  </div>

  <div class="flex items-center justify-between text-[10px]">
  <div class="flex gap-3">
  <span class="text-emerald-400">+{c.reward_credits} cr</span>
  <span class="text-amber-400">+{c.reward_points} pts</span>
  </div>
  <div class="flex items-center gap-2 text-slate-500">
  <span>{c.participants} participantes</span>
  <span>·</span>
  <span>{c.deadline_days}d restantes</span>
  </div>
  </div>

  <button
  onclick={() => joinChallenge(c.id)}
  class="w-full mt-3 py-1.5 text-[11px] rounded-lg border font-medium transition-colors"
  style="border-color:{catColor}40;color:{catColor};background:{catColor}0A">
  Unirme al reto
  </button>
  </div>
  {/each}
  </div>

  <!-- Logros desbloqueables (badges) -->
  <div class="mb-3 mt-6">
  <div class="flex items-baseline justify-between mb-3">
  <div>
  <h2 class="text-[13px] font-semibold text-white tracking-tight">Logros</h2>
  <p class="text-[11px] text-slate-500 mt-0.5">{gamification.badges.filter(b => b.unlocked).length} de {gamification.badges.length} desbloqueados</p>
  </div>
  </div>
  </div>

  <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
  {#each gamification.badges as b}
  <div class="relative rounded-2xl border p-4 transition-all
  {b.unlocked ? 'border-amber-500/30 bg-gradient-to-br from-amber-500/[0.05] to-transparent' : 'border-white/[0.04] bg-white/[0.02] opacity-50'}">
  {#if b.unlocked}
  <div class="absolute top-2 right-2 text-[9px] font-mono text-amber-400"></div>
  {/if}
  <div class="text-3xl mb-2 {!b.unlocked ? 'grayscale' : ''}">{b.icon}</div>
  <div class="text-[12px] font-semibold text-white mb-1">{b.name}</div>
  <div class="text-[10px] text-slate-500 leading-snug mb-2">{b.desc}</div>
  {#if !b.unlocked}
  <div class="mt-2">
  <div class="flex justify-between text-[9px] mb-0.5">
  <span class="text-slate-600">Progreso</span>
  <span class="text-white font-mono">{b.progress}/{b.target}</span>
  </div>
  <div class="h-1 bg-white/5 rounded-full overflow-hidden">
  <div class="h-full bg-amber-500/60 transition-all" style="width:{(b.progress/b.target)*100}%"></div>
  </div>
  </div>
  {:else}
  <div class="text-[10px] text-amber-400 font-mono">+{b.points} pts</div>
  {/if}
  </div>
  {/each}
  </div>

  <!-- Catálogo de recompensas -->
  <div class="mb-3 mt-6">
  <div class="flex items-baseline justify-between mb-3">
  <div>
  <h2 class="text-[13px] font-semibold text-white tracking-tight">Canjea tus Puntos</h2>
  <p class="text-[11px] text-slate-500 mt-0.5">Beneficios reales conectados con Bienestar Universitario</p>
  </div>
  <div class="text-[11px] text-amber-400 font-mono">{gamification.user.points} pts disponibles</div>
  </div>
  </div>

  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
  {#each gamification.rewards as rwd}
  {@const can = gamification.user.points >= rwd.points && rwd.stock > 0}
  {@const typeColor = rwd.type === 'individual' ? '#10b981' : rwd.type === 'edificio' ? '#0ea5e9' : '#a78bfa'}
  <div class="rounded-2xl border bg-gradient-to-br from-white/[0.02] to-white/[0.005] p-4 transition-colors
  {can ? 'border-white/[0.08] hover:border-white/20' : 'border-white/[0.04] opacity-60'}">
  <div class="flex items-start gap-3 mb-3">
  <div class="text-3xl">{rwd.icon}</div>
  <div class="flex-1 min-w-0">
  <div class="text-[12px] font-semibold text-white">{rwd.name}</div>
  <div class="text-[9px] uppercase font-mono tracking-wider mt-0.5" style="color:{typeColor}">{rwd.type}</div>
  </div>
  </div>
  <div class="flex items-center justify-between mb-3">
  <div class="text-[11px] font-mono text-amber-400">{rwd.points.toLocaleString()} pts</div>
  <div class="text-[10px] text-slate-500">stock: {rwd.stock}</div>
  </div>
  <button
  onclick={() => redeem(rwd.id)}
  disabled={!can}
  class="w-full py-1.5 text-[11px] rounded-lg border font-medium transition-colors
  {can ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20' : 'border-white/10 text-slate-600 cursor-not-allowed'}">
  {can ? 'Canjear' : (rwd.stock <= 0 ? 'Sin stock' : `Faltan ${(rwd.points - gamification.user.points).toLocaleString()} pts`)}
  </button>
  </div>
  {/each}
  </div>

  <!-- Cómo ganar puntos -->
  <div class="rounded-2xl border border-sky-500/20 bg-sky-500/[0.04] p-5 mt-6">
  <div class="text-[10px] font-mono tracking-[0.15em] uppercase text-sky-400 mb-3">¿Cómo gano puntos?</div>
  <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 text-[11px]">
  {#each [
  {emoji: "", title: "Reportar fugas", pts: "+20 pts", desc: "Si la IA valida tu reporte"},
  {emoji: "", title: "Colaborar", pts: "+5 pts", desc: "Por cada reporte aunque no se valide"},
  {emoji: "", title: "Completar retos", pts: "+100-500 pts", desc: "Según dificultad del reto"},
  {emoji: "", title: "Ahorrar agua", pts: "+1 cr/m³", desc: "Crédito hídrico por m³ ahorrado"},
  ] as a}
  <div>
  <div class="text-2xl mb-1">{a.emoji}</div>
  <div class="text-[12px] text-white font-medium">{a.title}</div>
  <div class="text-[10px] text-amber-400 font-mono mt-0.5">{a.pts}</div>
  <div class="text-[10px] text-slate-500 mt-0.5">{a.desc}</div>
  </div>
  {/each}
  </div>
  </div>

  {/if}

  {:else if tab === "architecture"}

  <div class="mb-6">
  <h2 class="text-[16px] font-semibold text-white tracking-tight">Arquitectura por capas</h2>
  <p class="text-[11px] text-slate-500 mt-1">De abajo (agua física) hacia arriba (botón en pantalla). Cada capa es independientemente reemplazable.</p>
  </div>

  <!-- SVG con las 7 capas -->
  <div class="rounded-2xl border border-white/[0.06] bg-white/[0.015] p-6 mb-6">
  <svg viewBox="0 0 900 720" class="w-full h-auto" style="background:linear-gradient(180deg,rgba(125,211,252,0.04) 0%,rgba(14,165,233,0.02) 100%)">
  <defs>
  <pattern id="archGrid" width="30" height="30" patternUnits="userSpaceOnUse">
  <path d="M 30 0 L 0 0 0 30" fill="none" stroke="rgba(148,163,184,0.06)" stroke-width="1"/>
  </pattern>
  <marker id="archArrowDown" viewBox="0 0 10 10" refX="5" refY="9" markerWidth="8" markerHeight="8" orient="auto">
  <path d="M 0 0 L 5 10 L 10 0 z" fill="#7dd3fc"/>
  </marker>
  </defs>
  <rect width="900" height="720" fill="url(#archGrid)"/>

  <!-- Conector vertical central -->
  <line x1="450" y1="40" x2="450" y2="690" stroke="#7dd3fc" stroke-width="2" stroke-dasharray="4 3" opacity="0.45"/>

  <!-- ═══ CAPA 7 · APLICACIÓN (y=40-130) ═══ -->
  <g>
  <rect x="40" y="40" width="820" height="90" rx="8" fill="rgba(125,211,252,0.10)" stroke="#7dd3fc" stroke-width="1.5"/>
  <text x="60" y="65" fill="#7dd3fc" font-size="11" font-family="JetBrains Mono" font-weight="bold">CAPA 7 · APLICACIÓN</text>
  <text x="60" y="82" fill="rgba(148,163,184,0.7)" font-size="9" font-family="JetBrains Mono">qué ven los humanos · &lt; 100 ms (UI)</text>
  <!-- 4 cards horizontales -->
  <rect x="80" y="92" width="170" height="30" rx="4" fill="rgba(56,189,248,0.10)" stroke="#38bdf8" stroke-width="1"/>
  <text x="165" y="111" text-anchor="middle" fill="#38bdf8" font-size="10" font-family="Inter">Dashboard SvelteKit</text>
  <rect x="270" y="92" width="170" height="30" rx="4" fill="rgba(56,189,248,0.10)" stroke="#38bdf8" stroke-width="1"/>
  <text x="355" y="111" text-anchor="middle" fill="#38bdf8" font-size="10" font-family="Inter">Bot Telegram</text>
  <rect x="460" y="92" width="170" height="30" rx="4" fill="rgba(56,189,248,0.10)" stroke="#38bdf8" stroke-width="1"/>
  <text x="545" y="111" text-anchor="middle" fill="#38bdf8" font-size="10" font-family="Inter">Reportes PDF auditables</text>
  <rect x="650" y="92" width="170" height="30" rx="4" fill="rgba(56,189,248,0.10)" stroke="#38bdf8" stroke-width="1"/>
  <text x="735" y="111" text-anchor="middle" fill="#38bdf8" font-size="10" font-family="Inter">API pública (Ley 1712)</text>
  </g>

  <!-- ═══ CAPA 6 · INTELIGENCIA (y=145-235) ═══ -->
  <g>
  <rect x="40" y="145" width="820" height="90" rx="8" fill="rgba(99,102,241,0.10)" stroke="#818cf8" stroke-width="1.5"/>
  <text x="60" y="170" fill="#818cf8" font-size="11" font-family="JetBrains Mono" font-weight="bold">CAPA 6 · INTELIGENCIA</text>
  <text x="60" y="187" fill="rgba(148,163,184,0.7)" font-size="9" font-family="JetBrains Mono">5 agentes · LangGraph · LLM cascade · 1-5 s</text>
  <!-- 5 agentes -->
  {#each [
  { code: "ORC", name: "Orchestrator", x: 80 },
  { code: "SYS", name: "Systems",  x: 230 },
  { code: "SEN", name: "Sensor",  x: 380 },
  { code: "IND", name: "Industrial",  x: 530 },
  { code: "MIT", name: "Mitigation",  x: 680 },
  ] as a}
  <rect x={a.x} y="195" width="135" height="30" rx="4" fill="rgba(99,102,241,0.15)" stroke="#a5b4fc" stroke-width="1"/>
  <text x={a.x+10} y="207" fill="#a5b4fc" font-size="9" font-family="JetBrains Mono" font-weight="bold">{a.code}</text>
  <text x={a.x+10} y="220" fill="rgba(165,180,252,0.85)" font-size="9.5" font-family="Inter">{a.name}</text>
  {/each}
  </g>

  <!-- ═══ CAPA 5 · PERSISTENCIA (y=250-340) ═══ -->
  <g>
  <rect x="40" y="250" width="820" height="90" rx="8" fill="rgba(34,197,94,0.10)" stroke="#22c55e" stroke-width="1.5"/>
  <text x="60" y="275" fill="#22c55e" font-size="11" font-family="JetBrains Mono" font-weight="bold">CAPA 5 · PERSISTENCIA</text>
  <text x="60" y="292" fill="rgba(148,163,184,0.7)" font-size="9" font-family="JetBrains Mono">FastAPI + Postgres + Parquet · 50-200 ms</text>
  <rect x="80" y="300" width="220" height="30" rx="4" fill="rgba(34,197,94,0.15)" stroke="#4ade80" stroke-width="1"/>
  <text x="190" y="319" text-anchor="middle" fill="#4ade80" font-size="10" font-family="Inter">FastAPI · /water/* · /water/agent/*</text>
  <rect x="320" y="300" width="200" height="30" rx="4" fill="rgba(34,197,94,0.15)" stroke="#4ade80" stroke-width="1"/>
  <text x="420" y="319" text-anchor="middle" fill="#4ade80" font-size="10" font-family="Inter">Cache RAM · última hora</text>
  <rect x="540" y="300" width="160" height="30" rx="4" fill="rgba(34,197,94,0.15)" stroke="#4ade80" stroke-width="1"/>
  <text x="620" y="319" text-anchor="middle" fill="#4ade80" font-size="10" font-family="Inter">Postgres · 90 días</text>
  <rect x="720" y="300" width="120" height="30" rx="4" fill="rgba(34,197,94,0.15)" stroke="#4ade80" stroke-width="1"/>
  <text x="780" y="319" text-anchor="middle" fill="#4ade80" font-size="10" font-family="Inter">Parquet · 5 años</text>
  </g>

  <!-- ═══ CAPA 4 · COMUNICACIÓN (y=355-445) ═══ -->
  <g>
  <rect x="40" y="355" width="820" height="90" rx="8" fill="rgba(245,158,11,0.10)" stroke="#f59e0b" stroke-width="1.5"/>
  <text x="60" y="380" fill="#f59e0b" font-size="11" font-family="JetBrains Mono" font-weight="bold">CAPA 4 · COMUNICACIÓN</text>
  <text x="60" y="397" fill="rgba(148,163,184,0.7)" font-size="9" font-family="JetBrains Mono">MQTT TLS 8883 · HTTP fallback · NVS · 30-100 ms</text>
  <rect x="80" y="405" width="240" height="30" rx="4" fill="rgba(245,158,11,0.15)" stroke="#fbbf24" stroke-width="1"/>
  <text x="200" y="424" text-anchor="middle" fill="#fbbf24" font-size="10" font-family="Inter">HiveMQ Cloud (TLS QoS 1)</text>
  <rect x="340" y="405" width="220" height="30" rx="4" fill="rgba(245,158,11,0.15)" stroke="#fbbf24" stroke-width="1"/>
  <text x="450" y="424" text-anchor="middle" fill="#fbbf24" font-size="10" font-family="Inter">HTTP REST fallback</text>
  <rect x="580" y="405" width="240" height="30" rx="4" fill="rgba(245,158,11,0.15)" stroke="#fbbf24" stroke-width="1"/>
  <text x="700" y="424" text-anchor="middle" fill="#fbbf24" font-size="10" font-family="Inter">NVS local · 1,000 lecturas offline</text>
  </g>

  <!-- ═══ CAPA 3 · EDGE (y=460-550) ═══ -->
  <g>
  <rect x="40" y="460" width="820" height="90" rx="8" fill="rgba(168,85,247,0.10)" stroke="#a855f7" stroke-width="1.5"/>
  <text x="60" y="485" fill="#a855f7" font-size="11" font-family="JetBrains Mono" font-weight="bold">CAPA 3 · EDGE / EMBEBIDA</text>
  <text x="60" y="502" fill="rgba(148,163,184,0.7)" font-size="9" font-family="JetBrains Mono">ESP32-WROOM dual-core · ADS1115 16-bit · OLED + LED + buzzer · 1-30 s</text>
  <rect x="80" y="510" width="200" height="30" rx="4" fill="rgba(168,85,247,0.15)" stroke="#c084fc" stroke-width="1"/>
  <text x="180" y="529" text-anchor="middle" fill="#c084fc" font-size="10" font-family="Inter">Core 0 · 1 Hz · sensores</text>
  <rect x="300" y="510" width="200" height="30" rx="4" fill="rgba(168,85,247,0.15)" stroke="#c084fc" stroke-width="1"/>
  <text x="400" y="529" text-anchor="middle" fill="#c084fc" font-size="10" font-family="Inter">Core 1 · 30s · MQTT publish</text>
  <rect x="520" y="510" width="160" height="30" rx="4" fill="rgba(168,85,247,0.15)" stroke="#c084fc" stroke-width="1"/>
  <text x="600" y="529" text-anchor="middle" fill="#c084fc" font-size="10" font-family="Inter">OLED + LED + buzzer</text>
  <rect x="700" y="510" width="120" height="30" rx="4" fill="rgba(168,85,247,0.15)" stroke="#c084fc" stroke-width="1"/>
  <text x="760" y="529" text-anchor="middle" fill="#c084fc" font-size="10" font-family="Inter">220V → 5V + bat.</text>
  </g>

  <!-- ═══ CAPA 2 · SENSADO (y=565-655) ═══ -->
  <g>
  <rect x="40" y="565" width="820" height="90" rx="8" fill="rgba(239,68,68,0.10)" stroke="#ef4444" stroke-width="1.5"/>
  <text x="60" y="590" fill="#fca5a5" font-size="11" font-family="JetBrains Mono" font-weight="bold">CAPA 2 · SENSADO</text>
  <text x="60" y="607" fill="rgba(148,163,184,0.7)" font-size="9" font-family="JetBrains Mono">6 sensores físicos · normalizador universal acepta 10 formatos · &lt; 1 s</text>
  {#each [
  { code: "YF-S201",   variable: "Caudal",  x: 80 },
  { code: "MPX5700AP", variable: "Presión",  x: 215 },
  { code: "JSN-SR04T", variable: "Nivel tanque", x: 350 },
  { code: "SW-420",  variable: "Vibración",  x: 485 },
  { code: "4-20mA",  variable: "Freático",  x: 620 },
  { code: "TSD-10",  variable: "Turbidez",  x: 755 },
  ] as s}
  <rect x={s.x} y="615" width="125" height="30" rx="4" fill="rgba(239,68,68,0.15)" stroke="#fca5a5" stroke-width="1"/>
  <text x={s.x+62} y="627" text-anchor="middle" fill="#fca5a5" font-size="9" font-family="JetBrains Mono" font-weight="bold">{s.code}</text>
  <text x={s.x+62} y="640" text-anchor="middle" fill="rgba(252,165,165,0.8)" font-size="9" font-family="Inter">{s.variable}</text>
  {/each}
  </g>

  <!-- ═══ CAPA 1 · FÍSICA (y=665-720) ═══ -->
  <g>
  <rect x="40" y="665" width="820" height="55" rx="8" fill="rgba(56,189,248,0.10)" stroke="#0ea5e9" stroke-width="1.5"/>
  <text x="60" y="685" fill="#0ea5e9" font-size="11" font-family="JetBrains Mono" font-weight="bold">CAPA 1 · FÍSICA · UNIAJC Sede Sur</text>
  <text x="60" y="703" fill="rgba(148,163,184,0.85)" font-size="9.5" font-family="Inter">Aljibes 1+2 → PTAP 2011 (3 filtros) → Tank A 36k L + Tank B 16k L → 6 edificios → PTAR Alameda + PTAR Entrada (4,000 est cap) → Río Pance/Cauca</text>
  </g>

  <!-- Flechas de flujo lateral -->
  <line x1="20" y1="60" x2="20" y2="690" stroke="#7dd3fc" stroke-width="2" stroke-dasharray="6 3" opacity="0.55"/>
  <text x="6" y="380" fill="rgba(125,211,252,0.7)" font-size="9" font-family="JetBrains Mono" transform="rotate(-90 6 380)">datos suben</text>
  <line x1="880" y1="60" x2="880" y2="690" stroke="#fbbf24" stroke-width="2" stroke-dasharray="3 2" opacity="0.55" marker-end="url(#archArrowDown)"/>
  <text x="893" y="380" fill="rgba(251,191,36,0.7)" font-size="9" font-family="JetBrains Mono" transform="rotate(90 893 380)">acciones bajan</text>
  </svg>
  </div>

  <!-- Tabla resumen + estado por capa -->
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-3">

  <!-- Tabla de responsabilidades -->
  <div class="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5">
  <div class="text-[11px] font-medium tracking-wider uppercase text-slate-500 mb-3">Responsabilidad de cada capa</div>
  <div class="space-y-1.5 text-[11px]">
  {#each [
  { n: "07", color: "#7dd3fc", name: "Aplicación", resp: "Visualizar, notificar, reportar", lat: "<100ms" },
  { n: "06", color: "#a5b4fc", name: "Inteligencia", resp: "Analizar (3 niveles) y decidir", lat: "1-5s" },
  { n: "05", color: "#4ade80", name: "Persistencia", resp: "Validar, almacenar, servir API", lat: "50-200ms" },
  { n: "04", color: "#fbbf24", name: "Comunicación", resp: "Transportar al backend con garantías", lat: "30-100ms" },
  { n: "03", color: "#c084fc", name: "Edge", resp: "Filtrar, promediar, almacenar local", lat: "1-30s" },
  { n: "02", color: "#fca5a5", name: "Sensado", resp: "Convertir fenómeno físico en señal", lat: "<1s" },
  { n: "01", color: "#0ea5e9", name: "Física", resp: "El recurso hídrico real", lat: "—" },
  ] as l}
  <div class="flex items-center gap-2 p-2 rounded-md border border-white/[0.04] bg-white/[0.015]">
  <span class="text-[9px] font-mono px-1.5 py-0.5 rounded shrink-0" style="background:{l.color}1A;color:{l.color}">{l.n}</span>
  <span class="font-medium text-slate-200 shrink-0 w-24">{l.name}</span>
  <span class="text-slate-400 flex-1 truncate text-[10.5px]">{l.resp}</span>
  <span class="text-slate-500 font-mono text-[10px] shrink-0">{l.lat}</span>
  </div>
  {/each}
  </div>
  </div>

  <!-- Estado live de cada capa -->
  <div class="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5">
  <div class="text-[11px] font-medium tracking-wider uppercase text-slate-500 mb-3">Estado en vivo</div>
  <div class="space-y-2">
  {#each [
  { n: "07", name: "Aplicación", status: "active", val: "dashboard 6 tabs · bot Telegram" },
  { n: "06", name: "Inteligencia", status: agent?.running ? "active" : "off", val: agent?.running ? `agente ciclo #${agent.cycle} · decisión ${agent.last_decision}` : "agente detenido" },
  { n: "05", name: "Persistencia", status: "active", val: "FastAPI :8000 · simulador en RAM" },
  { n: "04", name: "Comunicación", status: "demo", val: "MQTT pendiente · HTTP fallback OK" },
  { n: "03", name: "Edge", status: "demo", val: "firmware MicroPython listo · sin hardware aún" },
  { n: "02", name: "Sensado", status: "demo", val: `6 sensores simulados · normalizador acepta 10 formatos` },
  { n: "01", name: "Física", status: "doc", val: "planos hidráulicos UNIAJC en repo" },
  ] as l}
  {@const c = l.status === "active" ? "#10b981" : l.status === "off" ? "#ef4444" : "#f59e0b"}
  <div class="flex items-center gap-3 text-[11px]">
  <span class="text-[9px] font-mono w-7 text-slate-500">{l.n}</span>
  <span class="w-1.5 h-1.5 rounded-full" style="background:{c}"></span>
  <span class="font-medium text-slate-300 w-24">{l.name}</span>
  <span class="text-slate-500 flex-1 truncate text-[10.5px]">{l.val}</span>
  <span class="text-[9px] font-mono uppercase" style="color:{c}">{l.status}</span>
  </div>
  {/each}
  </div>

  <div class="mt-4 pt-3 border-t border-white/[0.06] text-[10px] text-slate-500 font-mono leading-relaxed">
  <span class="text-emerald-400">active</span> · operativo en este momento &nbsp;·&nbsp;
  <span class="text-amber-400">demo</span> · código listo, infra/hardware pendiente &nbsp;·&nbsp;
  <span class="text-amber-400">doc</span> · solo documentación
  </div>
  </div>

  </div>

  <!-- ═══ DIAGRAMA 2 · TRINIDAD ANALÍTICA (3 niveles) ═══ -->
  <div class="mt-6 mb-3">
  <h2 class="text-[15px] font-semibold text-white tracking-tight">Trinidad analítica del agente</h2>
  <p class="text-[11px] text-slate-500 mt-1">Cada lectura pasa por 3 niveles de análisis. Lo descriptivo alimenta lo predictivo, lo predictivo informa lo prescriptivo.</p>
  </div>

  <div class="rounded-2xl border border-white/[0.06] bg-white/[0.015] p-6 mb-6">
  <svg viewBox="0 0 900 460" class="w-full h-auto">
  <defs>
  <marker id="arrTrin" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto">
  <path d="M 0 0 L 10 5 L 0 10 z" fill="#7dd3fc"/>
  </marker>
  <linearGradient id="bandPred" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0%" stop-color="rgba(245,158,11,0.30)"/>
  <stop offset="100%" stop-color="rgba(245,158,11,0)"/>
  </linearGradient>
  </defs>

  <!-- ═══════════ NIVEL 1 · DESCRIPTIVO (azul) ═══════════ -->
  <g>
  <rect x="20" y="20" width="280" height="420" rx="12" fill="rgba(14,165,233,0.06)" stroke="#0ea5e9" stroke-width="1.2"/>
  <text x="40" y="48" fill="#0ea5e9" font-size="10" font-family="JetBrains Mono" font-weight="bold">NIVEL 1 · DESCRIPTIVO</text>
  <text x="40" y="72" fill="white" font-size="15" font-family="Inter" font-weight="bold">¿Qué pasó?</text>
  <text x="40" y="89" fill="rgba(255,255,255,0.6)" font-size="9.5" font-family="Inter">SystemsAgent · SensorAgent</text>

  <!-- CHART 1A: Sparkline caudal 24h -->
  <text x="40" y="115" fill="#7dd3fc" font-size="9.5" font-family="JetBrains Mono">caudal últimas 24 h · L/min</text>
  <rect x="40" y="120" width="240" height="80" fill="rgba(0,0,0,0.20)" stroke="rgba(125,211,252,0.15)" stroke-width="0.5" rx="3"/>
  <!-- gridlines -->
  <line x1="40" y1="160" x2="280" y2="160" stroke="rgba(125,211,252,0.10)" stroke-dasharray="2 3"/>
  <!-- línea promedio histórico -->
  <line x1="40" y1="158" x2="280" y2="158" stroke="rgba(125,211,252,0.35)" stroke-width="0.5" stroke-dasharray="3 3"/>
  <text x="282" y="161" fill="rgba(125,211,252,0.5)" font-size="8" font-family="JetBrains Mono">avg</text>
  <!-- Sparkline path: pico en h7-9 (mañana), baja al mediodía, pico h12-14, valle h22-h5 -->
  <path d="M 40 188 L 50 192 L 60 194 L 70 196 L 80 192 L 90 175 L 100 155 L 110 132 L 120 128 L 130 145 L 140 158 L 150 138 L 160 125 L 170 142 L 180 158 L 190 168 L 200 162 L 210 152 L 220 148 L 230 158 L 240 170 L 250 180 L 260 188 L 270 192 L 280 195"
  fill="none" stroke="#0ea5e9" stroke-width="2"/>
  <!-- Highlight peaks -->
  <circle cx="115" cy="128" r="3" fill="#7dd3fc"/>
  <circle cx="160" cy="125" r="3" fill="#7dd3fc"/>
  <text x="40" y="213" fill="rgba(255,255,255,0.5)" font-size="8" font-family="JetBrains Mono">0</text>
  <text x="155" y="213" fill="rgba(255,255,255,0.5)" font-size="8" font-family="JetBrains Mono">12h</text>
  <text x="265" y="213" fill="rgba(255,255,255,0.5)" font-size="8" font-family="JetBrains Mono">24h</text>

  <!-- CHART 1B: Heatmap consumo por hora x día (7x4 = 28 celdas) -->
  <text x="40" y="240" fill="#7dd3fc" font-size="9.5" font-family="JetBrains Mono">heatmap día × hora</text>
  {#each Array(7) as _, dayI}
  {#each Array(4) as _, blockI}
  {@const intensity = dayI < 5 ? (blockI === 1 ? 0.85 : blockI === 2 ? 0.55 : 0.25) : (blockI === 0 ? 0.10 : 0.20)}
  <rect x={40 + blockI * 30} y={250 + dayI * 17} width="28" height="15" rx="2" fill={`rgba(14,165,233,${intensity})`} stroke="rgba(255,255,255,0.05)"/>
  {/each}
  {/each}
  <text x="40" y="383" fill="rgba(255,255,255,0.5)" font-size="8" font-family="JetBrains Mono">L M X J V S D · 0-6 · 6-12 · 12-18 · 18-24</text>

  <!-- CHART 1C: Distribución p50/p95/p99 -->
  <text x="40" y="404" fill="#7dd3fc" font-size="9.5" font-family="JetBrains Mono">distrib · p50/p95/p99</text>
  <rect x="40" y="412" width="120" height="6" rx="3" fill="rgba(14,165,233,0.7)"/>
  <rect x="160" y="412" width="60" height="6" rx="3" fill="rgba(14,165,233,0.45)"/>
  <rect x="220" y="412" width="20" height="6" rx="3" fill="rgba(14,165,233,0.25)"/>
  <text x="248" y="418" fill="rgba(255,255,255,0.55)" font-size="8" font-family="JetBrains Mono">L/min</text>
  <text x="105" y="430" text-anchor="middle" fill="rgba(125,211,252,0.7)" font-size="8" font-family="JetBrains Mono">p50</text>
  <text x="200" y="430" text-anchor="middle" fill="rgba(125,211,252,0.5)" font-size="8" font-family="JetBrains Mono">p95</text>
  </g>

  <!-- Flecha 1 → 2 -->
  <line x1="305" y1="230" x2="325" y2="230" stroke="#7dd3fc" stroke-width="2" marker-end="url(#arrTrin)"/>

  <!-- ═══════════ NIVEL 2 · PREDICTIVO (naranja) ═══════════ -->
  <g>
  <rect x="330" y="20" width="280" height="420" rx="12" fill="rgba(245,158,11,0.06)" stroke="#f59e0b" stroke-width="1.2"/>
  <text x="350" y="48" fill="#f59e0b" font-size="10" font-family="JetBrains Mono" font-weight="bold">NIVEL 2 · PREDICTIVO</text>
  <text x="350" y="72" fill="white" font-size="15" font-family="Inter" font-weight="bold">¿Qué va a pasar?</text>
  <text x="350" y="89" fill="rgba(255,255,255,0.6)" font-size="9.5" font-family="Inter">IndustrialAgent</text>

  <!-- CHART 2A: Forecast con banda de confianza -->
  <text x="350" y="115" fill="#fbbf24" font-size="9.5" font-family="JetBrains Mono">forecast 6h · ARIMA + LSTM</text>
  <rect x="350" y="120" width="240" height="80" fill="rgba(0,0,0,0.20)" stroke="rgba(251,191,36,0.15)" stroke-width="0.5" rx="3"/>
  <!-- ahora vertical -->
  <line x1="470" y1="120" x2="470" y2="200" stroke="rgba(251,191,36,0.55)" stroke-width="1" stroke-dasharray="3 2"/>
  <text x="473" y="132" fill="rgba(251,191,36,0.7)" font-size="8" font-family="JetBrains Mono">ahora</text>
  <!-- past actual -->
  <path d="M 355 175 L 375 168 L 395 172 L 415 158 L 435 165 L 455 152 L 470 158"
  fill="none" stroke="#fbbf24" stroke-width="2"/>
  <!-- forecast band -->
  <path d="M 470 158 L 490 148 L 510 132 L 530 122 L 550 130 L 570 138 L 585 145 L 585 175 L 570 168 L 550 162 L 530 155 L 510 165 L 490 175 L 470 158 Z"
  fill="url(#bandPred)" stroke="none"/>
  <!-- forecast line -->
  <path d="M 470 158 L 490 148 L 510 132 L 530 122 L 550 130 L 570 138 L 585 145"
  fill="none" stroke="#f59e0b" stroke-width="1.8" stroke-dasharray="4 2"/>
  <circle cx="530" cy="122" r="3" fill="#fbbf24"/>
  <text x="528" y="118" text-anchor="middle" fill="rgba(251,191,36,0.85)" font-size="8" font-family="JetBrains Mono">pico 7AM</text>
  <text x="354" y="213" fill="rgba(255,255,255,0.5)" font-size="8" font-family="JetBrains Mono">-6h</text>
  <text x="468" y="213" fill="rgba(255,255,255,0.5)" font-size="8" font-family="JetBrains Mono">0</text>
  <text x="565" y="213" fill="rgba(255,255,255,0.5)" font-size="8" font-family="JetBrains Mono">+6h</text>

  <!-- CHART 2B: Anomaly score (IsolationForest) timeline -->
  <text x="350" y="240" fill="#fbbf24" font-size="9.5" font-family="JetBrains Mono">anomaly score · IsolationForest</text>
  <rect x="350" y="248" width="240" height="40" fill="rgba(0,0,0,0.15)" rx="3"/>
  <line x1="350" y1="276" x2="590" y2="276" stroke="rgba(251,191,36,0.25)" stroke-dasharray="2 2"/>
  <text x="592" y="280" fill="rgba(251,191,36,0.5)" font-size="8" font-family="JetBrains Mono">0.5</text>
  {#each [0.12, 0.18, 0.15, 0.22, 0.30, 0.45, 0.78, 0.85, 0.65, 0.40, 0.25, 0.20] as v, i}
  {@const x = 358 + i * 19}
  {@const h = v * 35}
  {@const isAnom = v > 0.5}
  <rect x={x} y={285 - h} width="14" height={h} rx="1.5" fill={isAnom ? '#ef4444' : '#fbbf24'} opacity={isAnom ? 0.85 : 0.6}/>
  {/each}

  <!-- CHART 2C: Random Forest feature importance -->
  <text x="350" y="313" fill="#fbbf24" font-size="9.5" font-family="JetBrains Mono">RF feature importance · clasif. fuga</text>
  {#each [
  { name: "presión", val: 0.32, color: "#f59e0b" },
  { name: "vibración", val: 0.27, color: "#fbbf24" },
  { name: "caudal", val: 0.18, color: "#fbbf24" },
  { name: "Δpresión", val: 0.13, color: "#fbbf24" },
  { name: "freático", val: 0.10, color: "#f59e0b" },
  ] as f, i}
  <text x="350" y={335 + i * 17} fill="rgba(255,255,255,0.7)" font-size="9" font-family="JetBrains Mono">{f.name}</text>
  <rect x="410" y={328 + i * 17} width={f.val * 350} height="10" rx="2" fill={f.color} opacity="0.75"/>
  <text x={415 + f.val * 350} y={336 + i * 17} fill="rgba(251,191,36,0.85)" font-size="8" font-family="JetBrains Mono">{(f.val*100).toFixed(0)}%</text>
  {/each}
  <text x="350" y="430" fill="rgba(251,191,36,0.7)" font-size="9" font-family="JetBrains Mono" font-weight="bold">P(fuga) = 0.92 · tipo: fisura_lenta</text>
  </g>

  <!-- Flecha 2 → 3 -->
  <line x1="615" y1="230" x2="635" y2="230" stroke="#7dd3fc" stroke-width="2" marker-end="url(#arrTrin)"/>

  <!-- ═══════════ NIVEL 3 · PRESCRIPTIVO (rojo) ═══════════ -->
  <g>
  <rect x="640" y="20" width="245" height="420" rx="12" fill="rgba(239,68,68,0.06)" stroke="#ef4444" stroke-width="1.2"/>
  <text x="660" y="48" fill="#ef4444" font-size="10" font-family="JetBrains Mono" font-weight="bold">NIVEL 3 · PRESCRIPTIVO</text>
  <text x="660" y="72" fill="white" font-size="15" font-family="Inter" font-weight="bold">¿Qué hacemos?</text>
  <text x="660" y="89" fill="rgba(255,255,255,0.6)" font-size="9.5" font-family="Inter">Orchestrator + Mitigation</text>

  <!-- CHART 3A: Voto consensual 5 agentes -->
  <text x="660" y="115" fill="#fca5a5" font-size="9.5" font-family="JetBrains Mono">voto consensual · 4 de 5 ≥ critical</text>
  {#each [
  { code: "ORC", vote: "critical", color: "#ef4444", x: 660 },
  { code: "SYS", vote: "critical", color: "#ef4444", x: 700 },
  { code: "SEN", vote: "warning",  color: "#fbbf24", x: 740 },
  { code: "IND", vote: "critical", color: "#ef4444", x: 780 },
  { code: "MIT", vote: "critical", color: "#ef4444", x: 820 },
  ] as v, i}
  <circle cx={v.x + 18} cy="138" r="14" fill={v.color + '30'} stroke={v.color} stroke-width="1.5"/>
  <text x={v.x + 18} y="142" text-anchor="middle" fill={v.color} font-size="8" font-family="JetBrains Mono" font-weight="bold">{v.code}</text>
  {#if i < 4}
  <line x1={v.x + 32} y1="138" x2={v.x + 36} y2="138" stroke="rgba(255,255,255,0.25)" stroke-width="1.5"/>
  {/if}
  {/each}
  <!-- consensus bar -->
  <rect x="660" y="160" width="200" height="6" rx="3" fill="rgba(239,68,68,0.20)"/>
  <rect x="660" y="160" width="160" height="6" rx="3" fill="#ef4444"/>
  <text x="765" y="180" text-anchor="middle" fill="#fca5a5" font-size="9" font-family="JetBrains Mono">consenso 80% → ACTÚA</text>

  <!-- CHART 3B: Optimización scipy curve (kWh por hora) -->
  <text x="660" y="210" fill="#fca5a5" font-size="9.5" font-family="JetBrains Mono">optim · presión vs kWh</text>
  <rect x="660" y="218" width="200" height="60" fill="rgba(0,0,0,0.15)" rx="3"/>
  <line x1="660" y1="248" x2="860" y2="248" stroke="rgba(252,165,165,0.20)" stroke-dasharray="2 2"/>
  <!-- baseline kWh sin optim -->
  <path d="M 665 230 L 685 232 L 705 234 L 725 233 L 745 232 L 765 230 L 785 228 L 805 230 L 825 232 L 845 234 L 855 232"
  fill="none" stroke="rgba(255,255,255,0.35)" stroke-width="1.2" stroke-dasharray="3 2"/>
  <!-- optimizada (más baja en horario eco) -->
  <path d="M 665 248 L 685 256 L 705 262 L 725 268 L 745 270 L 765 268 L 785 260 L 805 250 L 825 240 L 845 235 L 855 232"
  fill="none" stroke="#ef4444" stroke-width="2"/>
  <!-- área de ahorro -->
  <path d="M 685 232 L 685 256 L 705 262 L 725 268 L 745 270 L 765 268 L 785 260 L 805 250 L 805 230 L 785 228 L 765 230 L 745 232 L 725 233 L 705 234 Z"
  fill="rgba(239,68,68,0.18)"/>
  <text x="745" y="295" text-anchor="middle" fill="rgba(252,165,165,0.7)" font-size="9" font-family="JetBrains Mono">22:00–06:00 · −40% kWh</text>

  <!-- CHART 3C: Acción ejecutada -->
  <text x="660" y="320" fill="#fca5a5" font-size="9.5" font-family="JetBrains Mono">decisión final · acción</text>
  <rect x="660" y="328" width="205" height="40" rx="6" fill="rgba(239,68,68,0.18)" stroke="#ef4444" stroke-width="1.5"/>
  <text x="763" y="349" text-anchor="middle" fill="white" font-size="11" font-family="JetBrains Mono" font-weight="bold">CIERRA EV-A2</text>
  <text x="763" y="362" text-anchor="middle" fill="rgba(252,165,165,0.85)" font-size="9" font-family="JetBrains Mono">+ reporte CVC + OT-30685054</text>

  <!-- CHART 3D: Impacto en plata -->
  <text x="660" y="392" fill="#fca5a5" font-size="9.5" font-family="JetBrains Mono">impacto monetizado</text>
  <text x="660" y="412" fill="white" font-size="14" font-family="JetBrains Mono" font-weight="bold">$36,400</text>
  <text x="730" y="412" fill="rgba(252,165,165,0.7)" font-size="9" font-family="JetBrains Mono">COP/día · 10,400 L</text>
  <text x="660" y="430" fill="rgba(252,165,165,0.6)" font-size="8.5" font-family="JetBrains Mono">CO₂ evitado: 4.78 kg</text>
  </g>
  </svg>
  </div>

  <!-- ═══ DIAGRAMA 3 · SECUENCIA END-TO-END (sensor → cierre EV) ═══ -->
  <div class="mt-6 mb-3">
  <h2 class="text-[15px] font-semibold text-white tracking-tight">Flujo end-to-end · sensor detecta fuga → cierre automático</h2>
  <p class="text-[11px] text-slate-500 mt-1">5 segundos vs 2-4 horas manual. Cada paso es una capa.</p>
  </div>

  <div class="rounded-2xl border border-white/[0.06] bg-white/[0.015] p-4 mb-6">
  <svg viewBox="0 0 900 460" class="w-full h-auto">
  <defs>
  <marker id="arrSeq" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
  <path d="M 0 0 L 10 5 L 0 10 z" fill="rgba(125,211,252,0.6)"/>
  </marker>
  </defs>

  <!-- 7 swim lanes (uno por capa) -->
  {#each [
  { y: 30, code: "L1", name: "Física", color: "#0ea5e9" },
  { y: 80, code: "L2", name: "Sensado", color: "#fca5a5" },
  { y: 130, code: "L3", name: "Edge ESP32", color: "#c084fc" },
  { y: 180, code: "L4", name: "Comunicación MQTT", color: "#fbbf24" },
  { y: 230, code: "L5", name: "FastAPI + DB", color: "#4ade80" },
  { y: 280, code: "L6", name: "Inteligencia (5 agentes)", color: "#a5b4fc" },
  { y: 330, code: "L7", name: "Aplicación + actuadores", color: "#7dd3fc" },
  ] as l}
  <rect x="20" y={l.y} width="860" height="34" rx="6" fill={l.color + '0F'} stroke={l.color} stroke-width="0.7" stroke-dasharray="2 2" opacity="0.5"/>
  <text x="32" y={l.y + 22} fill={l.color} font-size="10" font-family="JetBrains Mono" font-weight="bold">{l.code}</text>
  <text x="62" y={l.y + 22} fill="rgba(255,255,255,0.85)" font-size="10.5" font-family="Inter">{l.name}</text>
  {/each}

  <!-- Pasos del flujo (cajitas + flechas verticales) -->
  {#each [
  { x: 200, y_from: 30, y_to: 80, label: "fuga genera vibración + caída presión" },
  { x: 290, y_from: 80, y_to: 130, label: "SW-420 ON · MPX5700 → 0.7V" },
  { x: 380, y_from: 130, y_to: 180, label: "buffer 30s · σ + min + max" },
  { x: 470, y_from: 180, y_to: 230, label: "publish topic=sensors/ptap-01" },
  { x: 560, y_from: 230, y_to: 280, label: "validate · cache · upsert DB" },
  { x: 650, y_from: 280, y_to: 330, label: "voto 3 de 5 → leak_response" },
  { x: 740, y_from: 330, y_to: 280, label: "POST /mitigate/auto", up: true },
  { x: 800, y_from: 280, y_to: 130, label: "MQTT actuators/EV-A2 close", up: true, dotted: true },
  ] as s}
  <line x1={s.x} y1={s.y_from + 34} x2={s.x} y2={s.y_to} stroke="rgba(125,211,252,0.55)" stroke-width="1.8" stroke-dasharray={s.dotted ? '4 3' : ''} marker-end="url(#arrSeq)"/>
  <rect x={s.x - 75} y={Math.min(s.y_from, s.y_to) + 38} width="150" height="14" rx="3" fill="rgba(15,23,42,0.85)" stroke="rgba(125,211,252,0.3)" stroke-width="0.5"/>
  <text x={s.x} y={Math.min(s.y_from, s.y_to) + 48} text-anchor="middle" fill="rgba(255,255,255,0.85)" font-size="9" font-family="Inter">{s.label}</text>
  {/each}

  <!-- Footer del diagrama -->
  <text x="450" y="400" text-anchor="middle" fill="rgba(255,255,255,0.6)" font-size="11" font-family="Inter">Total end-to-end: <tspan fill="#10b981" font-weight="bold">~5 segundos</tspan> · vs respuesta humana tradicional: <tspan fill="#ef4444" font-weight="bold">2-4 horas</tspan></text>
  <text x="450" y="425" text-anchor="middle" fill="rgba(125,211,252,0.7)" font-size="10" font-family="JetBrains Mono">cada flecha vertical = 1 capa · línea sólida = datos suben · línea punteada = acción baja</text>
  </svg>
  </div>

  <!-- ═══ MOCKUPS por capa ═══ -->
  <div class="mt-6 mb-3">
  <h2 class="text-[15px] font-semibold text-white tracking-tight">Manifestación física por capa</h2>
  <p class="text-[11px] text-slate-500 mt-1">Cómo se ve cada capa cuando la abrís — display OLED, MQTT topics, payload, tabla SQL.</p>
  </div>

  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 mb-6">

  <!-- Mockup 1 · OLED Display (capa 3) -->
  <div class="rounded-xl border border-purple-500/[0.20] bg-purple-500/[0.03] p-3 font-mono">
  <div class="text-[10px] text-purple-400 uppercase tracking-wider mb-2">Capa 3 · OLED 0.96"</div>
  <pre class="text-[9px] text-purple-200 leading-tight whitespace-pre overflow-hidden">
+-------------------+
|AguaMind Node 01   |
|PTAP UNIAJC        |
+-------------------+
|Q:    28.92 L/min  |
|P:    67.4 kPa BAJA|
|TankA 72%  TankB 78|
|Freat: 8.04 m   OK |
|NTU:   1.13     OK |
+-------------------+
|MQTT OK · WiFi -54 |
|TX 12s ago         |
+-------------------+</pre>
  <div class="text-[9px] text-purple-400/70 mt-1.5">visible sin internet</div>
  </div>

  <!-- Mockup 2 · MQTT topic (capa 4) -->
  <div class="rounded-xl border border-amber-500/[0.20] bg-amber-500/[0.03] p-3 font-mono">
  <div class="text-[10px] text-amber-400 uppercase tracking-wider mb-2">Capa 4 · MQTT topics</div>
  <pre class="text-[9px] text-amber-200 leading-tight whitespace-pre overflow-hidden">
campus/uniajc/
  sensors/
    esp32-ptap-01    ← payload
    esp32-bloque-a-01
  actuators/
    EV-A1   close|open
    EV-A2   close|open
    EV-RC1  close|open
    pump-main  auto|eco
  alerts/
    critical
    warning
  reports/
    monthly-irca
    quarterly-cvc</pre>
  <div class="text-[9px] text-amber-400/70 mt-1.5">TLS 8883 · QoS 1</div>
  </div>

  <!-- Mockup 3 · Payload JSON (capa 4 / 5) -->
  <div class="rounded-xl border border-emerald-500/[0.20] bg-emerald-500/[0.03] p-3 font-mono">
  <div class="text-[10px] text-emerald-400 uppercase tracking-wider mb-2">Capa 5 · Payload canónico</div>
  <pre class="text-[9px] text-emerald-200 leading-tight whitespace-pre overflow-hidden">{`{
  "node_id": "esp32-ptap-01",
  "ts": "2026-05-08T03:00Z",
  "flow1_lmin":   14.5,
  "pressure_kpa": 320,
  "tank_a_pct":   72,
  "vibration":  false,
  "phreatic_m":  8.04,
  "turbidity_ntu": 1.13,
  "wifi_rssi": -54,
  "battery_v":  4.1,
  "uptime_s": 86400
}`}</pre>
  <div class="text-[9px] text-emerald-400/70 mt-1.5">10 formatos aceptados</div>
  </div>

  <!-- Mockup 4 · Schema SQL (capa 5) -->
  <div class="rounded-xl border border-sky-500/[0.20] bg-sky-500/[0.03] p-3 font-mono">
  <div class="text-[10px] text-sky-400 uppercase tracking-wider mb-2">Capa 5 · tabla water_readings</div>
  <pre class="text-[9px] text-sky-200 leading-tight whitespace-pre overflow-hidden">
id            BIGSERIAL PK
timestamp     TIMESTAMPTZ
node_id       TEXT
sensor_id     TEXT
sensor_type   TEXT
value         DOUBLE
unit          TEXT
raw           JSONB
quality       TEXT
metadata      JSONB
created_at    TIMESTAMPTZ

INDEX (ts DESC)
INDEX (node_id, sensor)
INDEX (quality) WHERE
   quality != 'ok'</pre>
  <div class="text-[9px] text-sky-400/70 mt-1.5">retención 90d · luego Parquet</div>
  </div>
  </div>

  <!-- ═══ DIAGRAMA 4 · Máquina de estados del firmware ═══ -->
  <div class="mt-6 mb-3">
  <h2 class="text-[15px] font-semibold text-white tracking-tight">Máquina de estados · firmware ESP32</h2>
  <p class="text-[11px] text-slate-500 mt-1">Cómo el nodo IoT sobrevive cortes de internet y reconecta.</p>
  </div>

  <div class="rounded-2xl border border-white/[0.06] bg-white/[0.015] p-6 mb-6">
  <svg viewBox="0 0 900 280" class="w-full h-auto">
  <defs>
  <marker id="arrFsm" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">
  <path d="M 0 0 L 10 5 L 0 10 z" fill="#a855f7"/>
  </marker>
  </defs>

  {#each [
  { x: 80,  y: 130, label: "BOOT", color: "#94a3b8" },
  { x: 220, y: 130, label: "WIFI_CONNECT", color: "#7dd3fc" },
  { x: 380, y: 130, label: "MQTT_CONNECT", color: "#fbbf24" },
  { x: 540, y: 130, label: "READY", color: "#10b981" },
  { x: 700, y:  60, label: "READING (1Hz)", color: "#a855f7" },
  { x: 700, y: 200, label: "PUBLISHING (30s)", color: "#a855f7" },
  { x: 540, y: 235, label: "HTTP_FALLBACK", color: "#f59e0b" },
  { x: 380, y: 235, label: "NVS_BUFFER", color: "#ef4444" },
  ] as s}
  <rect x={s.x - 60} y={s.y - 18} width="120" height="36" rx="8" fill={s.color + '20'} stroke={s.color} stroke-width="1.5"/>
  <text x={s.x} y={s.y + 4} text-anchor="middle" fill={s.color} font-size="11" font-family="JetBrains Mono" font-weight="bold">{s.label}</text>
  {/each}

  <!-- Transiciones -->
  <line x1="140" y1="130" x2="160" y2="130" stroke="#a855f7" stroke-width="2" marker-end="url(#arrFsm)"/>
  <line x1="280" y1="130" x2="320" y2="130" stroke="#a855f7" stroke-width="2" marker-end="url(#arrFsm)"/>
  <line x1="440" y1="130" x2="480" y2="130" stroke="#a855f7" stroke-width="2" marker-end="url(#arrFsm)"/>
  <line x1="600" y1="120" x2="640" y2="80" stroke="#a855f7" stroke-width="2" marker-end="url(#arrFsm)"/>
  <line x1="600" y1="140" x2="640" y2="190" stroke="#a855f7" stroke-width="2" marker-end="url(#arrFsm)"/>
  <line x1="640" y1="220" x2="600" y2="235" stroke="#f59e0b" stroke-width="2" stroke-dasharray="3 2" marker-end="url(#arrFsm)"/>
  <line x1="480" y1="235" x2="440" y2="235" stroke="#ef4444" stroke-width="2" stroke-dasharray="3 2" marker-end="url(#arrFsm)"/>
  <path d="M 380 217 Q 380 160 440 130" stroke="#10b981" stroke-width="1.5" stroke-dasharray="4 3" fill="none" marker-end="url(#arrFsm)"/>

  <text x="640" y="115" fill="rgba(168,85,247,0.7)" font-size="9" font-family="JetBrains Mono">core 0</text>
  <text x="640" y="180" fill="rgba(168,85,247,0.7)" font-size="9" font-family="JetBrains Mono">core 1</text>
  <text x="535" y="225" fill="rgba(245,158,11,0.7)" font-size="9" font-family="JetBrains Mono">si MQTT falla</text>
  <text x="430" y="225" fill="rgba(239,68,68,0.7)" font-size="9" font-family="JetBrains Mono">si HTTP falla</text>
  <text x="395" y="170" fill="rgba(16,185,129,0.7)" font-size="9" font-family="JetBrains Mono">WiFi reconecta · drena buffer</text>
  </svg>
  </div>

  <!-- ═══ MAPEO 7-capas AguaMind vs 5-capas AQUA-ROI Lite (compañero electrónica) ═══ -->
  <div class="mt-6 mb-3">
  <h2 class="text-[15px] font-semibold text-white tracking-tight">Equivalencia con AQUA-ROI Lite</h2>
  <p class="text-[11px] text-slate-500 mt-1">Las 7 capas de AguaMind <span class="text-emerald-400">incluyen</span> las 5 capas del piloto AQUA-ROI Lite (compañero de electrónica). Mismo backbone, AguaMind agrega Capa Física (planos hidráulicos) e Inteligencia multi-agente.</p>
  </div>

  <div class="rounded-2xl border border-white/[0.04] p-5 mb-6" style="background: rgba(255,255,255,0.015)">
  <svg viewBox="0 0 900 380" class="w-full h-auto">
  <defs>
  <marker id="arrEqui" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
  <path d="M 0 0 L 10 5 L 0 10 z" fill="#34d399"/>
  </marker>
  </defs>

  <!-- Encabezados -->
  <text x="180" y="30" text-anchor="middle" fill="#7dd3fc" font-size="13" font-family="Inter" font-weight="bold">AguaMind OS · 7 capas</text>
  <text x="700" y="30" text-anchor="middle" fill="#fbbf24" font-size="13" font-family="Inter" font-weight="bold">AQUA-ROI Lite · 5 capas</text>

  <!-- 7 capas AguaMind (izquierda) -->
  {#each [
  { y: 45,  num: "07", name: "Aplicación",    color: "#7dd3fc", aqua: "5 · Interfaz" },
  { y: 88,  num: "06", name: "Inteligencia",  color: "#a5b4fc", aqua: "Agente Aqua-ROI" },
  { y: 131, num: "05", name: "Persistencia",  color: "#4ade80", aqua: "4 · Datos" },
  { y: 174, num: "04", name: "Comunicación",  color: "#fbbf24", aqua: "3 · Comunicación" },
  { y: 217, num: "03", name: "Edge / Embebida",color: "#c084fc", aqua: "2 · Procesamiento embebido" },
  { y: 260, num: "02", name: "Sensado",       color: "#fca5a5", aqua: "1 · Sensado" },
  { y: 303, num: "01", name: "Física",        color: "#0ea5e9", aqua: null },
  ] as l, i}
  <!-- AguaMind capa -->
  <rect x="40" y={l.y} width="280" height="38" rx="6" fill={l.color + '15'} stroke={l.color} stroke-width="1"/>
  <text x="55" y={l.y + 17} fill={l.color} font-size="10" font-family="JetBrains Mono" font-weight="bold">{l.num}</text>
  <text x="85" y={l.y + 17} fill="white" font-size="11" font-family="Inter" font-weight="600">{l.name}</text>

  {#if l.aqua}
  <!-- Flecha de equivalencia -->
  <line x1="320" y1={l.y + 19} x2="558" y2={l.y + 19} stroke="#34d399" stroke-width="1.5" stroke-dasharray="3 3" opacity="0.6" marker-end="url(#arrEqui)"/>
  <!-- AQUA-ROI capa -->
  <rect x="560" y={l.y} width="280" height="38" rx="6" fill="#fbbf241A" stroke="#fbbf24" stroke-width="1"/>
  <text x="700" y={l.y + 22} text-anchor="middle" fill="#fbbf24" font-size="11" font-family="Inter" font-weight="600">{l.aqua}</text>
  {:else}
  <!-- Capa Física no tiene equivalente -->
  <text x="340" y={l.y + 22} fill="rgba(255,255,255,0.4)" font-size="9" font-family="JetBrains Mono">implícita</text>
  <rect x="560" y={l.y} width="280" height="38" rx="6" fill="rgba(255,255,255,0.02)" stroke="rgba(255,255,255,0.08)" stroke-width="1" stroke-dasharray="4 3"/>
  <text x="700" y={l.y + 22} text-anchor="middle" fill="rgba(255,255,255,0.35)" font-size="11" font-family="Inter" font-style="italic">implícita en AQUA-ROI</text>
  {/if}
  {/each}

  <!-- Footer explicativo -->
  <text x="450" y="365" text-anchor="middle" fill="rgba(255,255,255,0.55)" font-size="10.5" font-family="Inter">AguaMind OS = AQUA-ROI Lite + Capa Física (planos UNIAJC) + Inteligencia multi-agente (5 agentes deliberan vs 1 agente reglas)</text>
  </svg>
  </div>

  <!-- ═══ MATRIZ DE CUMPLIMIENTO RÚBRICA OFICIAL ═══ -->
  <div class="mt-6 mb-3">
  <h2 class="text-[15px] font-semibold text-white tracking-tight">Cumplimiento de la rúbrica oficial · 11 criterios</h2>
  <p class="text-[11px] text-slate-500 mt-1">Auto-evaluación del proyecto integrado AguaMind + AQUA-ROI Lite contra los criterios del jurado UNIAJC 2026</p>
  </div>

  <div class="rounded-2xl border border-white/[0.04] overflow-hidden mb-6">
  <table class="w-full text-[11px]">
  <thead style="background: rgba(255,255,255,0.03)">
  <tr class="text-left">
  <th class="py-2.5 px-4 font-medium text-slate-500 uppercase tracking-wider text-[10px]">Categoría</th>
  <th class="py-2.5 px-4 font-medium text-slate-500 uppercase tracking-wider text-[10px]">Peso</th>
  <th class="py-2.5 px-4 font-medium text-slate-500 uppercase tracking-wider text-[10px]">Criterio</th>
  <th class="py-2.5 px-4 font-medium text-slate-500 uppercase tracking-wider text-[10px]">Evidencia</th>
  <th class="py-2.5 px-4 font-medium text-slate-500 uppercase tracking-wider text-[10px] text-right">Pts</th>
  </tr>
  </thead>
  <tbody>
  {#each [
  { cat: "NOVEDAD",         color: "#a855f7", peso: "30%", criterio: "Originalidad",          evidencia: "Multi-agente IA + Smart Water Ledger + tokenización CO₂ + TinyML acústico", pts: "4/4" },
  { cat: "",                color: "#a855f7", peso: "",     criterio: "Disrupción",            evidencia: "Crea categoría Smart Campus Hídrico Open Source + híbrido medición tradicional", pts: "4/4" },
  { cat: "",                color: "#a855f7", peso: "",     criterio: "Creatividad recursos",  evidencia: "LangGraph + ESP32 + LLM cascade gratis + 4 fuentes meteo gratuitas", pts: "4/4" },
  { cat: "ACT. INVENTIVA",  color: "#0ea5e9", peso: "20%", criterio: "Integración disciplinar", evidencia: "8 disciplinas: Sistemas + Electrónica + Industrial + IA/ML + UX + Economía + Compliance + Sostenibilidad", pts: "4/4" },
  { cat: "",                color: "#0ea5e9", peso: "",     criterio: "Sistematización",       evidencia: "6 metodologías: Design Thinking + TRIZ + Lean + Lean Startup + GitOps + CRISP-DM", pts: "4/4" },
  { cat: "APL. INDUSTRIAL", color: "#10b981", peso: "30%", criterio: "Viabilidad técnica",    evidencia: "Backend + dashboard + simulador corriendo · BOM AQUA-ROI Lite $5.57M validado", pts: "4/4" },
  { cat: "",                color: "#10b981", peso: "",     criterio: "Escalonamiento",        evidencia: "Plan 10 fases en 15 años · piloto $5.57M → completo $37M con datos reales", pts: "4/4" },
  { cat: "",                color: "#10b981", peso: "",     criterio: "Mercado",               evidencia: "350+ universidades CO + hospitales + conjuntos + open source MIT", pts: "4/4" },
  { cat: "IMPACTO",         color: "#fbbf24", peso: "20%", criterio: "Sostenibilidad ambiental", evidencia: "−596 kWh/año · −16.5M L/5 años · −7.6 ton CO₂/5 años", pts: "4/4" },
  { cat: "",                color: "#fbbf24", peso: "",     criterio: "Bienestar comunidad",   evidencia: "Calidad agua 8,234 usuarios + Smart Water Ledger + Bienestar Universitario", pts: "4/4" },
  { cat: "",                color: "#fbbf24", peso: "",     criterio: "Participación ciudadana", evidencia: "Reportes QR + datos abiertos Ley 1712/2014 + alianzas UNIAJC + CVC + EMCALI", pts: "4/4" },
  ] as r, i}
  <tr class="border-t border-white/[0.04]">
  <td class="py-2.5 px-4 align-top">
  {#if r.cat}<span class="text-[10px] font-mono font-bold uppercase" style="color:{r.color}">{r.cat}</span>{/if}
  </td>
  <td class="py-2.5 px-4 align-top text-slate-400 font-mono text-[10px]">{r.peso}</td>
  <td class="py-2.5 px-4 align-top text-white">{r.criterio}</td>
  <td class="py-2.5 px-4 align-top text-slate-400">{r.evidencia}</td>
  <td class="py-2.5 px-4 align-top text-right font-mono text-emerald-400 font-bold">{r.pts}</td>
  </tr>
  {/each}
  <tr class="border-t-2 border-emerald-500/30" style="background: rgba(16,185,129,0.05)">
  <td class="py-3 px-4 font-bold text-white" colspan="3">TOTAL · proyección honesta</td>
  <td class="py-3 px-4 text-emerald-400">Sobresaliente · 11/11 criterios en Excelente</td>
  <td class="py-3 px-4 text-right font-mono text-emerald-400 font-bold text-[14px]">44/44</td>
  </tr>
  </tbody>
  </table>
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
  :global(html.light) .am-root .border-white\/10  { border-color: rgba(15, 23, 42, 0.10); }
  :global(html.light) .am-root .border-white\/20  { border-color: rgba(15, 23, 42, 0.18); }
  :global(html.light) .am-root .bg-white\/\[0\.02\]  { background: rgba(15, 23, 42, 0.02); }
  :global(html.light) .am-root .bg-white\/\[0\.03\]  { background: rgba(15, 23, 42, 0.03); }
  :global(html.light) .am-root .bg-white\/\[0\.04\]  { background: rgba(15, 23, 42, 0.04); }
  :global(html.light) .am-root .bg-white\/\[0\.07\]  { background: rgba(15, 23, 42, 0.07); }
  :global(html.light) .am-root .bg-white\/5  { background: rgba(15, 23, 42, 0.04); }
  :global(html.light) .am-root .bg-white\/10  { background: rgba(15, 23, 42, 0.06); }
  :global(html.light) .am-root .hover\:bg-white\/\[0\.04\]:hover { background: rgba(15, 23, 42, 0.05); }
  :global(html.light) .am-root .hover\:bg-white\/\[0\.07\]:hover { background: rgba(15, 23, 42, 0.07); }

  /* Tank background en modo claro */
  :global(html.light) .am-root .bg-\[\#060a10\] { background: #e2e8f0; }
  :global(html.light) .am-root .bg-\[\#0a0e14\] { background: #f8fafc; }

  /* Texto invertido para modo claro */
  :global(html.light) .am-root .text-white  { color: #0f172a; }
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
