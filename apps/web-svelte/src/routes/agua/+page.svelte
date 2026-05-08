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
  let scenario = $state<"normal" | "leak" | "peak_irrigation" | "tank_low" | "soil_dry">("normal");
  let scenarioLoading = $state(false);
  let tab = $state<"dashboard" | "history" | "agent" | "mitigation" | "community">("dashboard");
  let gamification = $state<any>(null);
  let redeemMessage = $state<string | null>(null);
  let valves = $state<any>(null);
  let mitigationHistory = $state<any[]>([]);
  let impact = $state<any>(null);
  let leaderboard = $state<any[]>([]);
  let mapView3D = $state<boolean>(false);   // toggle vista isometrica del mapa

  // Datos sintéticos para el bar chart cuando el backend no responde aún.
  // Patrón realista 24 h: valle nocturno + picos académicos 7-9, 12-13, 15-17.
  const SYNTHETIC_HOURLY_BARS: { hour: string; consumption_l: number; losses_l: number; inflow_lmin: number; turbidity_ntu: number; tank_a_pct: number; phreatic_m: number }[] = (() => {
    const pattern = [481, 502, 471, 488, 447, 481, 1927, 2850, 3088, 3108, 2775, 2666, 2546, 1484, 1443, 2521, 2358, 2443, 1864, 481, 504, 482, 473, 450];
    return pattern.map((c, i) => ({
      hour: `${String(i).padStart(2,'0')}:00`,
      consumption_l: c,
      losses_l: Math.round(c * (i >= 22 || i < 6 ? 0.45 : 0.13)),
      inflow_lmin: 14 + (c / 200),
      turbidity_ntu: 0.9 + Math.sin(i / 24 * Math.PI * 2) * 0.5,
      tank_a_pct: 70 + Math.sin((i - 4) / 24 * Math.PI * 2) * 12,
      phreatic_m: 7.9 + Math.cos(i / 24 * Math.PI * 2) * 0.3,
    }));
  })();

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
  "¿Hay alguna fuga detectada en la red?",
  "¿Cómo están los tanques A y B?",
  "¿Necesita riego la cancha (humedad H)?",
  "¿Cuánta agua se está perdiendo por minuto?",
  "Dame un resumen ejecutivo del estado actual",
  ];
  let liveMode = $state(true);
  let theme = $state<"dark" | "light">("dark");

  // Cargar preferencia desde localStorage / clase ya marcada en <html>
  $effect(() => {
  if (typeof document === "undefined") return;
  if (document.documentElement.classList.contains("light") && theme !== "light") {
  theme = "light";
  } else if (typeof localStorage !== "undefined") {
  const saved = localStorage.getItem("hidrotech-theme");
  if (saved === "light" && theme !== "light") theme = "light";
  }
  });

  $effect(() => {
  if (typeof document === "undefined") return;
  document.documentElement.classList.toggle("light", theme === "light");
  if (typeof localStorage !== "undefined") {
  localStorage.setItem("hidrotech-theme", theme);
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

  // Notificaciones a Telegram — sin feedback visible en el dashboard (silencioso por diseño:
  // la sorpresa del pitch es que llega al celular, no que el dashboard cante).
  async function notifyTelegram(endpoint: string, body: any) {
    try {
      const res = await fetch(`/api/water?endpoint=notify/${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const json = await res.json();
      return json.data?.sent === true;
    } catch (_e) {
      return false;
    }
  }

  // Sugerencias por fenómeno (texto que viaja a Telegram)
  const PHENOMENON_SUGGESTIONS: Record<string, { days: number; suggestion: string }> = {
    drought_mode: {
      days: 30,
      suggestion: "IDEAM proyecta El Niño moderado en 30 días + freático bajando. Activar plan ahorra 10,400 L/día y protege el acuífero (-70% extracción).",
    },
    flood_mode: {
      days: 7,
      suggestion: "Pronóstico de lluvias intensas en 7 días. Activar plan corta riego innecesario y prepara colectores PTAR (5,500 L/día).",
    },
    quake_mode: {
      days: 0,
      suggestion: "Evento sísmico inminente o detectado. Activar plan cierra todas las EV y bomba a emergencia para evitar daños.",
    },
    contamination_mode: {
      days: 0,
      suggestion: "Turbidez >4 NTU o pH fuera de rango. Activar plan aísla los tanques y avisa INVIMA. Suspende distribución hasta toma de muestra.",
    },
    surge_mode: {
      days: 1,
      suggestion: "Pico de demanda >150% baseline previsto. Activar plan prioriza uso humano y refuerza la presión de bomba.",
    },
  };

  async function executeAutoMitigation(trigger: string) {
  // 1. Ejecutar la mitigación en backend
  let mitigationResult: any = null;
  try {
  const res = await fetch("/api/water?endpoint=mitigate/auto", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ trigger, severity: "critical" }),
  });
  mitigationResult = (await res.json())?.data;
  await fetchMitigation();
  } catch {}

  // 2. Disparar notificación Telegram
  if (mitigationResult) {
    await notifyTelegram("mitigation_executed", {
      trigger,
      impact_l: mitigationResult?.impact?.liters_saved ?? 0,
      cop_saved: mitigationResult?.impact?.cop_saved ?? 0,
      summary: mitigationResult?.detail ?? "",
      ot_id: mitigationResult?.id ?? "",
    });
  }
  }

  async function notifyPhenomenon(phenomenon: string) {
    // Aviso al operador SIN ejecutar todavía — el operador decide desde Telegram con el botón inline
    const cfg = PHENOMENON_SUGGESTIONS[phenomenon] ?? { days: 30, suggestion: "El agente sugiere activar el plan." };
    await notifyTelegram("phenomenon", {
      phenomenon,
      severity: "warning",
      forecast_days: cfg.days,
      suggestion: cfg.suggestion,
    });
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
  // Notifica al operador on-call vía Telegram con el resultado del ciclo
  if (agent) {
    await notifyTelegram("agent_cycle", {
      cycle: agent.cycle,
      decision: agent.last_decision,
      issues: agent.last_issues ?? [],
    });
  }
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

  // Fallback: si el backend aún no respondió, usa los datos sintéticos
  const displayHistory = $derived<any[]>(history.length > 0 ? history : SYNTHETIC_HOURLY_BARS);
  const maxConsumption = $derived(Math.max(...displayHistory.map(h => h.consumption_l ?? 0), 1));
  const totalAnnualLoss = $derived((reading?.losses_l_min ?? 0) * 1440 * 365 * 3.5);
  const annualSaving  = $derived(totalAnnualLoss * 0.6);

  // Colores de tanques (derivados según nivel)
  const tankAColor      = $derived((reading?.tank_a_pct ?? 0) < 33 ? "#ef4444" : (reading?.tank_a_pct ?? 0) < 67 ? "#f59e0b" : "#0ea5e9");
  const tankAColorLight = $derived((reading?.tank_a_pct ?? 0) < 33 ? "#fca5a5" : (reading?.tank_a_pct ?? 0) < 67 ? "#fbbf24" : "#7dd3fc");
  const tankBColor      = $derived((reading?.tank_b_pct ?? 0) < 33 ? "#ef4444" : "#06b6d4");
  const tankBColorLight = $derived((reading?.tank_b_pct ?? 0) < 33 ? "#fca5a5" : "#a5f3fc");

  // KPIs derivados para tab Operación (4 KPIs solicitados)
  const tppValue       = $derived(kpis?.TPP?.value ?? 0);
  const iehValue       = $derived(kpis?.IEH?.value ?? Math.max(0, 100 - tppValue));
  const iehStatusVal   = $derived(kpis?.IEH?.status ?? (iehValue >= 90 ? 'ok' : iehValue >= 75 ? 'warning' : 'critical'));
  const tppStatusVal   = $derived(kpis?.TPP?.status ?? 'ok');
  // Consumo diario real = demanda efectiva × 1440 (no caudal bombeado)
  // demand_l_min es el agua que llega a usuarios; total_flow es bombeo + pérdidas
  const consumoDiario  = $derived(Math.round(((reading as any)?.demand_l_min ?? (reading?.total_flow_lmin ?? 0) * 0.28) * 1440));
  // Ahorro de agua vs línea base UNIAJC (45,367 L/día medidos por Sánchez Sotelo 2021)
  const baselineLitersDay = 45_367;
  const ahorroPct         = $derived(Math.max(-100, Math.min(100, ((baselineLitersDay - consumoDiario) / baselineLitersDay) * 100)));
  const ahorroStatus      = $derived(ahorroPct >= 10 ? 'ok' : ahorroPct >= 0 ? 'warning' : 'critical');
  const mainKpis          = $derived([
    { code: "CONSUMO",  name: "Consumo total diario",   value: consumoDiario.toLocaleString(), unit: "L/día",  status: 'ok' as KPIStatus,        meta: `línea base ${baselineLitersDay.toLocaleString()} L` },
    { code: "FUGAS",    name: "Pérdidas por fuga",      value: fmt(tppValue, 1),                unit: "%",      status: tppStatusVal as KPIStatus, meta: "meta < 10% (TPP)" },
    { code: "AHORRO",   name: "Ahorro de agua",         value: fmt(ahorroPct, 1),                unit: "%",      status: ahorroStatus as KPIStatus, meta: `vs línea base UNIAJC` },
    { code: "IEH",      name: "Eficiencia hídrica",     value: fmt(iehValue, 1),                unit: "%",      status: iehStatusVal as KPIStatus, meta: "meta > 90%" },
  ]);

  // Sensores derivados (5: Caudal, Riego, Presión, Nivel, Humedad)
  const flowIrrigation = $derived((reading?.zones as any)?.["Riego/Cancha"] ?? 0);
  const tankAvg        = $derived(((reading?.tank_a_pct ?? 0) + (reading?.tank_b_pct ?? 0)) / 2);
  const soilHumidity   = $derived((reading as any)?.soil_humidity_pct ?? Math.max(45, Math.min(85, 65 + Math.sin(Date.now()/60000) * 8)));
  const sensorList     = $derived([
    { label: "Caudal general",  value: fmt(reading?.total_flow_lmin, 1) + " L/min", pct: (reading?.total_flow_lmin ?? 0) / 150 * 100, color: "#7dd3fc", code: "Q" },
    { label: "Caudal riego",    value: fmt(flowIrrigation, 1) + " L/min",           pct: flowIrrigation / 30 * 100,                    color: "#22c55e", code: "R" },
    { label: "Presión red",     value: fmt(reading?.pressure_kpa, 0) + " kPa",      pct: (reading?.pressure_kpa ?? 0) / 700 * 100,      color: "#a5b4fc", code: "P" },
    { label: "Nivel tanques",   value: fmt(tankAvg, 1) + " %",                      pct: tankAvg,                                        color: "#0ea5e9", code: "N" },
    { label: "Humedad suelo",   value: fmt(soilHumidity, 0) + " %",                 pct: soilHumidity,                                   color: "#34d399", code: "H" },
  ]);
</script>

<svelte:head>
  <title>HidroTech · UNIAJC</title>
</svelte:head>

<div class="min-h-screen am-root" style="font-family: 'Inter', -apple-system, system-ui, sans-serif;">

  <!-- ══ Header ════════════════════════════════════════════════════════════ -->
  <header class="border-b border-white/[0.06] bg-[#0a0e14]/90 backdrop-blur-xl sticky top-0 z-30">
  <div class="mx-auto max-w-7xl px-6 py-4 flex items-center justify-between">

  <!-- Logo + título -->
  <div class="flex items-center gap-3">
  <div class="am-keep relative w-10 h-10 rounded-xl bg-gradient-to-br from-sky-400 via-sky-500 to-cyan-600 flex items-center justify-center shadow-lg shadow-sky-500/20">
  <svg viewBox="0 0 24 24" fill="none" class="w-5 h-5 text-white" stroke="currentColor" stroke-width="2.2">
  <path d="M12 2.5C12 2.5 6 9 6 14a6 6 0 0012 0c0-5-6-11.5-6-11.5z" stroke-linejoin="round"/>
  </svg>
  <span class="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-emerald-400 ring-2 ring-[#0a0e14] animate-pulse"></span>
  </div>
  <div class="leading-tight">
  <h1 class="text-[15px] font-semibold tracking-tight text-white flex items-center gap-1.5">
  HidroTech <span class="text-sky-400 font-light">OS</span>
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
  <option value="leak">Fuga (Q ↑ · P ↓)</option>
  <option value="peak_irrigation">Pico riego (R ↑)</option>
  <option value="tank_low">Tanque bajo (N ↓)</option>
  <option value="soil_dry">Suelo seco (H ↓)</option>
  </select>

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
  <svg viewBox="0 0 24 24" fill="none" class="w-4 h-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="4"/>
  <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>
  </svg>
  {:else}
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
  ["dashboard",  "Operación",       "01"],
  ["history",    "Tendencias",      "02"],
  ["agent",      "Inteligencia",    "03"],
  ["mitigation", "Mapa del Campus", "04"],
  ["community",  "Comunidad",       "05"],
  ] as [key, label, num]}
  <button
  onclick={() => { tab = key as typeof tab; if (key === "history") fetchHistory(); if (key === "community") fetchGamification(); }}
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
    {#each mainKpis as kpi}
      <div class="group relative overflow-hidden rounded-2xl border border-white/[0.06] bg-gradient-to-br from-white/[0.02] to-white/[0.005] hover:from-white/[0.04] hover:to-white/[0.01] transition-all duration-300 p-5">
        <div class="absolute top-0 left-0 right-0 h-[2px]" style="background:linear-gradient(90deg, transparent, {statusHex(kpi.status)}, transparent)"></div>
        {#if kpi.status === 'critical'}
          <div class="absolute inset-0 opacity-[0.04]" style="background:radial-gradient(circle at 50% 0%, {statusHex(kpi.status)}, transparent 70%)"></div>
        {/if}
        <div class="relative">
          <div class="flex items-center justify-between mb-3">
            <div>
              <div class="text-[10px] font-mono font-bold tracking-[0.15em] text-slate-400">{kpi.code}</div>
              <div class="text-[10px] text-slate-600 mt-0.5">{kpi.name}</div>
            </div>
            <span class="text-[9px] font-medium px-2 py-0.5 rounded-full uppercase tracking-wider border"
              style="color:{statusHex(kpi.status)};background:{statusHex(kpi.status)}10;border-color:{statusHex(kpi.status)}30">{kpi.status === 'ok' ? 'óptimo' : kpi.status === 'warning' ? 'alerta' : 'crítico'}</span>
          </div>
          <div class="flex items-baseline gap-1">
            <span class="text-[32px] font-semibold tracking-tighter leading-none text-white" style="font-family:'JetBrains Mono','SF Mono',monospace">{kpi.value}</span>
            <span class="text-[12px] text-slate-500 font-normal">{kpi.unit}</span>
          </div>
          <div class="text-[10px] text-slate-500 mt-2 font-mono">{kpi.meta}</div>
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

  <!-- Tanque A visual con olas animadas -->
  <div class="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5">
    <div class="flex items-center justify-between mb-4">
      <div>
        <div class="text-[11px] font-medium tracking-wider uppercase text-slate-500">Tanque A · Principal</div>
        <div class="text-[10px] text-slate-600 mt-0.5">36,000 L · Bomba {reading.pump_active ? "ACTIVA" : "OFF"}</div>
      </div>
      <div class="text-[10px] font-mono text-slate-500">{fmtK(reading.tank_a_l)} L</div>
    </div>
    <div class="relative h-36 bg-[#060a10] rounded-lg overflow-hidden border border-white/[0.04]">
      <!-- Agua con olas animadas SVG -->
      <div class="absolute bottom-0 left-0 right-0 transition-all duration-1000" style="height:{reading.tank_a_pct}%">
        <!-- Cuerpo de agua con gradiente -->
        <div class="absolute inset-0" style="background:linear-gradient(180deg,{tankAColorLight},{tankAColor})"></div>
        <!-- Olas SVG animadas en la superficie -->
        <svg class="absolute -top-3 left-0 right-0 w-full h-6" viewBox="0 0 1200 24" preserveAspectRatio="none">
          <path d="M 0 12 Q 100 0 200 12 T 400 12 T 600 12 T 800 12 T 1000 12 T 1200 12 V 24 H 0 Z" fill={tankAColorLight} opacity="0.85">
            <animate attributeName="d" dur="3s" repeatCount="indefinite"
              values="M 0 12 Q 100 0 200 12 T 400 12 T 600 12 T 800 12 T 1000 12 T 1200 12 V 24 H 0 Z;
                      M 0 12 Q 100 24 200 12 T 400 12 T 600 12 T 800 12 T 1000 12 T 1200 12 V 24 H 0 Z;
                      M 0 12 Q 100 0 200 12 T 400 12 T 600 12 T 800 12 T 1000 12 T 1200 12 V 24 H 0 Z"/>
          </path>
          <path d="M 0 16 Q 150 4 300 16 T 600 16 T 900 16 T 1200 16 V 24 H 0 Z" fill={tankAColor} opacity="0.6">
            <animate attributeName="d" dur="4s" repeatCount="indefinite"
              values="M 0 16 Q 150 4 300 16 T 600 16 T 900 16 T 1200 16 V 24 H 0 Z;
                      M 0 16 Q 150 24 300 16 T 600 16 T 900 16 T 1200 16 V 24 H 0 Z;
                      M 0 16 Q 150 4 300 16 T 600 16 T 900 16 T 1200 16 V 24 H 0 Z"/>
          </path>
        </svg>
        <!-- Burbujas de aire ascendiendo -->
        {#each [1,2,3] as i}
          <span class="absolute rounded-full bg-white/40" style="
            width:{4+i*2}px; height:{4+i*2}px;
            left:{15+i*30}%; bottom:{i*15}%;
            animation: bubble{i} {3+i}s ease-in infinite;
            animation-delay:{i*0.7}s"></span>
        {/each}
      </div>
      <!-- Porcentaje centrado -->
      <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
        <span class="am-keep am-tank-pct text-[36px] font-semibold tracking-tight text-white drop-shadow-md" style="font-family:'JetBrains Mono',monospace;text-shadow:0 2px 8px rgba(0,0,0,0.6)">{fmt(reading.tank_a_pct)}%</span>
      </div>
      <!-- Línea umbral bomba -->
      <div class="absolute left-0 right-0 border-t border-amber-500/40 border-dashed" style="bottom:66.7%">
        <span class="absolute right-2 -top-3 text-[9px] text-amber-500/80 font-mono">66.7% · bomba</span>
      </div>
    </div>
  </div>

  <!-- Tanque B visual con olas animadas -->
  <div class="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5">
    <div class="flex items-center justify-between mb-4">
      <div>
        <div class="text-[11px] font-medium tracking-wider uppercase text-slate-500">Tanque B · Distribución</div>
        <div class="text-[10px] text-slate-600 mt-0.5">16,000 L</div>
      </div>
      <div class="text-[10px] font-mono text-slate-500">{fmtK(reading.tank_b_l)} L</div>
    </div>
    <div class="relative h-36 bg-[#060a10] rounded-lg overflow-hidden border border-white/[0.04]">
      <div class="absolute bottom-0 left-0 right-0 transition-all duration-1000" style="height:{reading.tank_b_pct}%">
        <div class="absolute inset-0" style="background:linear-gradient(180deg,{tankBColorLight},{tankBColor})"></div>
        <svg class="absolute -top-3 left-0 right-0 w-full h-6" viewBox="0 0 1200 24" preserveAspectRatio="none">
          <path d="M 0 12 Q 100 0 200 12 T 400 12 T 600 12 T 800 12 T 1000 12 T 1200 12 V 24 H 0 Z" fill={tankBColorLight} opacity="0.85">
            <animate attributeName="d" dur="3.5s" repeatCount="indefinite"
              values="M 0 12 Q 100 0 200 12 T 400 12 T 600 12 T 800 12 T 1000 12 T 1200 12 V 24 H 0 Z;
                      M 0 12 Q 100 24 200 12 T 400 12 T 600 12 T 800 12 T 1000 12 T 1200 12 V 24 H 0 Z;
                      M 0 12 Q 100 0 200 12 T 400 12 T 600 12 T 800 12 T 1000 12 T 1200 12 V 24 H 0 Z"/>
          </path>
          <path d="M 0 16 Q 150 4 300 16 T 600 16 T 900 16 T 1200 16 V 24 H 0 Z" fill={tankBColor} opacity="0.6">
            <animate attributeName="d" dur="4.5s" repeatCount="indefinite"
              values="M 0 16 Q 150 4 300 16 T 600 16 T 900 16 T 1200 16 V 24 H 0 Z;
                      M 0 16 Q 150 24 300 16 T 600 16 T 900 16 T 1200 16 V 24 H 0 Z;
                      M 0 16 Q 150 4 300 16 T 600 16 T 900 16 T 1200 16 V 24 H 0 Z"/>
          </path>
        </svg>
        {#each [1,2,3] as i}
          <span class="absolute rounded-full bg-white/40" style="
            width:{3+i*2}px; height:{3+i*2}px;
            left:{20+i*25}%; bottom:{i*12}%;
            animation: bubbleB{i} {3.5+i}s ease-in infinite;
            animation-delay:{i*0.5}s"></span>
        {/each}
      </div>
      <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
        <span class="am-keep am-tank-pct text-[36px] font-semibold tracking-tight text-white drop-shadow-md" style="font-family:'JetBrains Mono',monospace;text-shadow:0 2px 8px rgba(0,0,0,0.6)">{fmt(reading.tank_b_pct)}%</span>
      </div>
    </div>
  </div>

  <!-- 5 sensores compactos -->
  <div class="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5">
  <div class="text-[11px] font-medium tracking-wider uppercase text-slate-500 mb-4">5 Sensores · Tiempo real</div>
  <div class="space-y-3">
  {#each sensorList as s}
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

  <!-- ── HEATMAP día × hora (consumo principal) ─────────────────────────── -->
  <div class="mb-3 flex items-baseline justify-between">
    <div>
      <h2 class="text-[14px] font-semibold text-white tracking-tight">Patrón de consumo · día × hora</h2>
      <p class="text-[11px] text-slate-500 mt-0.5">Cada celda = caudal promedio (L/min) · pasa el cursor para ver detalle</p>
    </div>
    <div class="flex items-center gap-3 text-[10px]">
      <div class="flex items-center gap-1.5">
        <div class="w-3 h-3 rounded-sm bg-sky-500/20"></div>
        <span class="text-slate-500">bajo</span>
      </div>
      <div class="flex items-center gap-1.5">
        <div class="w-3 h-3 rounded-sm bg-sky-500/60"></div>
        <span class="text-slate-500">medio</span>
      </div>
      <div class="flex items-center gap-1.5">
        <div class="w-3 h-3 rounded-sm bg-red-500/80"></div>
        <span class="text-slate-500">pico</span>
      </div>
    </div>
  </div>

  <div class="rounded-2xl border border-white/[0.06] bg-gradient-to-br from-white/[0.02] to-white/[0.005] p-5 mb-6 overflow-x-auto">
    <table class="w-full" style="font-family: 'Inter', system-ui;">
      <thead>
        <tr>
          <th class="w-12"></th>
          {#each [0,2,4,6,8,10,12,14,16,18,20,22] as hLabel}
            <th class="text-[9px] font-mono font-medium text-slate-500 pb-2" colspan="2">{String(hLabel).padStart(2,'0')}h</th>
          {/each}
        </tr>
      </thead>
      <tbody>
        {#each ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"] as dia, dayI}
          {@const isWeekend = dayI >= 5}
          <tr>
            <td class="text-[11px] font-medium text-slate-400 pr-2 py-0.5 align-middle">{dia}</td>
            {#each Array(24) as _, hour}
              {@const isPeakMorning = hour >= 7 && hour <= 9}
              {@const isPeakLunch = hour >= 12 && hour <= 13}
              {@const isPeakAfternoon = hour >= 15 && hour <= 17}
              {@const isOff = hour >= 22 || hour < 6}
              {@const intensity = isWeekend
                ? (isOff ? 0.04 : 0.10)
                : isOff ? 0.08
                : isPeakMorning ? 0.95
                : isPeakLunch ? 0.78
                : isPeakAfternoon ? 0.72
                : hour >= 6 && hour <= 18 ? 0.42
                : 0.15}
              {@const valueLpm = Math.round(intensity * 180)}
              {@const isPeak = intensity >= 0.7 && !isWeekend}
              <td class="p-0.5 group relative">
                <div
                  class="w-full h-7 rounded transition-all hover:scale-110 hover:z-10 cursor-pointer"
                  style="background: {isPeak ? `rgba(239,68,68,${intensity})` : `rgba(14,165,233,${Math.max(0.05, intensity)})`}"
                  title="{dia} {String(hour).padStart(2,'0')}:00 · {valueLpm} L/min"
                ></div>
                <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-2 py-1 rounded-md bg-slate-900 border border-white/10 text-[10px] text-white font-mono whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none z-20">
                  {dia} · {String(hour).padStart(2,'0')}:00<br/>
                  <span class="text-sky-300">{valueLpm} L/min</span>
                </div>
              </td>
            {/each}
          </tr>
        {/each}
      </tbody>
    </table>

    <!-- Insights debajo del heatmap -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-5 pt-4 border-t border-white/[0.04]">
      <div>
        <div class="text-[10px] uppercase tracking-wider text-slate-500 mb-1">Pico máximo</div>
        <div class="text-[14px] font-mono font-semibold text-red-400">Mar 8h</div>
        <div class="text-[10px] text-slate-500">~171 L/min</div>
      </div>
      <div>
        <div class="text-[10px] uppercase tracking-wider text-slate-500 mb-1">Hora valle</div>
        <div class="text-[14px] font-mono font-semibold text-sky-400">03h</div>
        <div class="text-[10px] text-slate-500">~14 L/min</div>
      </div>
      <div>
        <div class="text-[10px] uppercase tracking-wider text-slate-500 mb-1">Patrón académico</div>
        <div class="text-[14px] font-mono font-semibold text-emerald-400">7-9h · 12-13h · 15-17h</div>
        <div class="text-[10px] text-slate-500">3 picos diarios L-V</div>
      </div>
      <div>
        <div class="text-[10px] uppercase tracking-wider text-slate-500 mb-1">Fin de semana</div>
        <div class="text-[14px] font-mono font-semibold text-slate-300">−85%</div>
        <div class="text-[10px] text-slate-500">vs días lectivos</div>
      </div>
    </div>
  </div>

  <!-- ── Tendencias 24h por sensor (5 sensores reales del campus) ─────── -->
  <div class="mb-4 flex items-baseline justify-between">
    <div>
      <h2 class="text-[14px] font-semibold text-white tracking-tight">Tendencias 24 h · 5 sensores</h2>
      <p class="text-[11px] text-slate-500 mt-0.5">Curva por sensor · valor actual destacado · min/max del día</p>
    </div>
    <span class="text-[10px] font-mono text-slate-600">simulación · datos sintéticos calibrados</span>
  </div>

  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mb-6">
  {#each [
    { code: "Q", name: "Caudal general",  unit: "L/min", color: "#7dd3fc", values: [60,55,52,48,45,50,90,140,165,160,155,148,130,135,158,160,155,145,120,95,80,70,65,62] },
    { code: "R", name: "Caudal riego",    unit: "L/min", color: "#22c55e", values: [0,0,0,0,0,0,0,2,3,4,3,2,2,2,3,4,3,2,1,0,0,0,0,0] },
    { code: "P", name: "Presión red",     unit: "kPa",   color: "#a5b4fc", values: [280,278,275,270,268,275,310,390,420,410,395,380,365,360,395,410,400,385,355,320,300,290,285,282] },
    { code: "N", name: "Nivel tanques",   unit: "%",     color: "#0ea5e9", values: [88,86,84,80,76,72,65,55,48,52,60,68,74,78,72,65,58,62,72,82,88,92,93,92] },
    { code: "H", name: "Humedad suelo",   unit: "%",     color: "#34d399", values: [70,68,67,66,65,64,63,62,61,60,58,55,52,50,49,52,58,62,66,68,70,71,72,71] },
  ] as v}
  {@const min = Math.min(...v.values)}
  {@const max = Math.max(...v.values)}
  {@const range = max - min || 1}
  <div class="rounded-2xl border border-white/[0.06] bg-gradient-to-br from-white/[0.02] to-white/[0.005] hover:from-white/[0.04] hover:to-white/[0.01] transition-colors p-4">
  <div class="flex items-start justify-between mb-3">
    <div class="flex items-center gap-2">
      <span class="w-6 h-6 rounded-md flex items-center justify-center text-[11px] font-mono font-bold" style="background:{v.color}1A;color:{v.color}">{v.code}</span>
      <div>
        <div class="text-[11px] text-slate-200 font-medium">{v.name}</div>
        <div class="text-[9px] text-slate-500 font-mono">{v.unit}</div>
      </div>
    </div>
    <div class="text-right">
      <div class="text-[18px] font-mono font-semibold leading-none" style="color:{v.color}">{v.values[v.values.length-1]}</div>
      <div class="text-[9px] text-slate-500 font-mono mt-1">min {min} · max {max}</div>
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
  <svg viewBox="0 0 900 220" class="w-full h-auto am-chart">
  <!-- Gridlines -->
  {#each [0, 25, 50, 75, 100] as pct}
  <line x1="60" y1={30 + (100 - pct) * 1.6} x2="880" y2={30 + (100 - pct) * 1.6} class="am-grid"/>
  <text x="55" y={34 + (100 - pct) * 1.6} text-anchor="end" class="am-axis" font-size="9" font-family="JetBrains Mono">{pct}%</text>
  {/each}

  <!-- Área de pérdidas (abajo, rojo) -->
  <path d="M 60 190 {STACK_DATA.map(d => `L ${60 + (d.h / 23) * 820} ${190 - d.perdidas * 1.6}`).join(' ')} L 880 190 Z"
        fill="rgba(239,68,68,0.30)" stroke="#ef4444" stroke-width="1.5"/>

  <!-- Área de consumo (arriba, azul) -->
  <path d="M 60 190 {STACK_DATA.map(d => `L ${60 + (d.h / 23) * 820} ${190 - (d.consumo + d.perdidas) * 1.6}`).join(' ')} L 880 190 Z"
        fill="rgba(14,165,233,0.30)" stroke="#0ea5e9" stroke-width="1.5"/>

  <!-- Eje X labels -->
  {#each [0, 6, 12, 18, 23] as h}
  <text x={60 + (h / 23) * 820} y="208" text-anchor="middle" class="am-axis" font-size="9" font-family="JetBrains Mono">{String(h).padStart(2,'0')}h</text>
  {/each}

  <!-- Leyenda -->
  <rect x="700" y="35" width="14" height="10" fill="rgba(14,165,233,0.30)" stroke="#0ea5e9"/>
  <text x="720" y="44" class="am-legend" font-size="10" font-family="Inter">consumo real</text>
  <rect x="700" y="55" width="14" height="10" fill="rgba(239,68,68,0.30)" stroke="#ef4444"/>
  <text x="720" y="64" class="am-legend" font-size="10" font-family="Inter">pérdidas técnicas</text>
  </svg>
  <div class="text-[10px] text-slate-500 mt-2">Las pérdidas representan ~10-15% del flujo total durante el día y crecen al ~50% del flujo nocturno (madrugada). Esto es justo lo que el método "tanques nocturnos" detecta y valida.</div>
  </div>

  <!-- ── Bar chart consumo histórico (existente · simplificado) ───────── -->
  <div class="rounded-2xl border border-white/[0.04] p-4 mb-5" style="background: rgba(255,255,255,0.015)">
  <div class="flex items-center justify-between mb-4">
  <div>
  <div class="text-[11px] font-medium tracking-wider uppercase text-slate-500">Consumo agregado por hora · barras</div>
  <div class="text-[10px] text-slate-500 mt-0.5">{displayHistory.length} muestras {history.length > 0 ? 'del simulador en vivo' : '(simuladas · esperando backend)'}</div>
  </div>
  <div class="text-right">
  <div class="text-[10px] text-slate-500 uppercase tracking-wider">Total 24h</div>
  <div class="text-[14px] font-mono text-sky-400 font-semibold">{displayHistory.reduce((sum, h) => sum + (h.consumption_l ?? 0), 0).toLocaleString()} L</div>
  </div>
  </div>
  <div class="flex items-end gap-px h-32">
  {#each displayHistory as h}
  <div class="flex-1 min-w-0 group relative">
  <div class="w-full bg-gradient-to-t from-sky-600 to-sky-400 hover:from-sky-500 hover:to-sky-300 rounded-t transition-colors"
  style="height:{Math.max(2, (h.consumption_l / maxConsumption) * 100)}%"></div>
  <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 text-[10px] bg-slate-900 border border-white/10 text-slate-200 px-2 py-1 rounded opacity-0 group-hover:opacity-100 whitespace-nowrap z-10 pointer-events-none font-mono">
  {h.hour}: {(h.consumption_l ?? 0).toLocaleString()} L
  </div>
  </div>
  {/each}
  </div>
  <div class="flex justify-between text-[9px] text-slate-600 font-mono mt-2">
  {#each [0, Math.floor(displayHistory.length/4), Math.floor(displayHistory.length/2), Math.floor(displayHistory.length*3/4), displayHistory.length-1] as idx}
  <span>{displayHistory[idx]?.hour ?? "—"}</span>
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
  {#each displayHistory.slice(-12).reverse() as h}
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
  { code: "SEN", name: "SensorAgent",  desc: "Validación 5 sensores · Q·R·P·N·H",   status: agent?.agents?.sensor  ?? "—" },
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
  <button
  onclick={() => notifyPhenomenon('drought_mode')}
  class="text-[10px] font-mono px-2 py-1 rounded bg-emerald-500/15 text-emerald-400 hover:bg-emerald-500/25 transition-colors cursor-pointer"
  title="estado del sistema">sistema OK</button>
  </div>

  <!-- Grid de fenómenos (5 cards) -->
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-2">
  {#each [
  {
  trigger: "leak", title: "Fuga detectada", color: "#ef4444",
  cond: "Q ↑ + P ↓ 28% en <90s",
  impact_l: 14500,
  acts: ["Cierra EV-A2 inmediato", "Bomba a standby",
  "Genera OT mantenimiento", "Push Telegram al equipo"],
  },
  {
  trigger: "peak_irrigation", title: "Pico riego", color: "#22c55e",
  cond: "R > 3× baseline + horario diurno",
  impact_l: 1800,
  acts: ["Cierra EV-RC1 inmediato", "Reprograma a 22:00-05:00",
  "Verifica humedad H del suelo", "Notifica jardinería"],
  },
  {
  trigger: "tank_low", title: "Tanque bajo", color: "#0ea5e9",
  cond: "N < 33% (12,000 L Tanque A)",
  impact_l: 0,
  acts: ["Activa bomba auto", "Pre-llena Tanque A",
  "Eleva presión P si hay demanda alta", "Aviso operador"],
  },
  {
  trigger: "soil_dry", title: "Suelo seco", color: "#34d399",
  cond: "H < 30% en zona riego",
  impact_l: 0,
  acts: ["Activa EV-RC1 (riego inteligente)", "Solo si horario nocturno",
  "Monitorea humedad post-riego", "Cierra al alcanzar 60%"],
  },
  {
  trigger: "drought_mode", title: "Sequía / El Niño", color: "#f59e0b",
  cond: "IDEAM El Niño + tendencia Q ↓ semanal",
  impact_l: 10400,
  acts: ["Bomba eco (-70% extracción)", "Cierra EV-RC1 todo el día",
  "Presión nocturna 380→260 kPa", "Reporte CVC + activa campaña"],
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
  Cada plan ejecuta acciones físicas reales (cierre EV vía MQTT + ajuste VFD bomba) + reporte auditable. Documentación: <span class="text-amber-400 font-mono">docs/es/CAMALEON-OS-MASTER.md §9</span>
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
  Sensores locales (Q caudal YF-S201, R caudal riego YF-DN50, P presión MPX5700AP, N nivel JSN-SR04T, H humedad HW-080) complementan el contexto meteorológico. El backend hace fetch periódico (15 min) a estas APIs y normaliza con <span class="font-mono text-sky-400">app/sensors/normalizer.py</span>.
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
  conf: 96,
  text: reading
  ? `5/5 sensores en rango. Q caudal ${reading.total_flow_lmin?.toFixed(1)} L/min, R riego ${(reading.zones?.["Riego/Cancha"] ?? 0).toFixed(1)} L/min, P presión ${reading.pressure_kpa} kPa, N tanques A=${reading.tank_a_pct}%/B=${reading.tank_b_pct}%, H humedad ${(reading as any).soil_humidity_pct ?? 65}%.`
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

  <!-- Impacto hídrico en vivo -->
  <div class="rounded-xl border border-sky-500/[0.18] bg-gradient-to-br from-sky-500/[0.04] to-sky-500/[0.01] p-5">
  <div class="text-[11px] font-medium tracking-wider uppercase text-sky-400 mb-1">Impacto hídrico del agente</div>
  <div class="text-[10px] text-slate-500 mb-4">Cada decisión convertida en litros recuperados y agua disponible</div>

  <!-- Big number: litros perdiéndose ahora -->
  <div class="rounded-lg border border-white/[0.06] bg-white/[0.02] p-3 mb-3">
  <div class="text-[10px] text-slate-500 uppercase tracking-wider">Pérdidas por minuto (live)</div>
  <div class="text-[22px] font-mono font-bold text-red-400 mt-1">{reading ? fmt(reading.losses_l_min ?? 0, 1) : '—'} L/min</div>
  <div class="text-[9px] text-slate-500 font-mono">{reading ? Math.round(((reading.losses_l_min ?? 0)/((reading.total_flow_lmin ?? 0)||1))*100) : 0}% del caudal · meta {'<'} 10%</div>
  </div>

  <!-- Stack de números -->
  <div class="space-y-2 text-[11px]">
  <div class="flex items-center justify-between">
  <span class="text-slate-400">Pérdida proyectada/día</span>
  <span class="font-mono text-red-400 font-bold">{reading ? Math.round((reading.losses_l_min ?? 0)*1440).toLocaleString() : '—'} L</span>
  </div>
  <div class="flex items-center justify-between">
  <span class="text-slate-400">Pérdida proyectada/año</span>
  <span class="font-mono text-red-400 font-bold">{reading ? Math.round((reading.losses_l_min ?? 0)*1440*365/1000).toLocaleString() : '—'} m³</span>
  </div>
  <div class="flex items-center justify-between pt-2 border-t border-white/[0.06]">
  <span class="text-slate-400">Litros recuperados (acumulado)</span>
  <span class="font-mono text-emerald-400 font-bold">{impact ? impact.liters_saved.toLocaleString() : '0'} L</span>
  </div>
  <div class="flex items-center justify-between">
  <span class="text-slate-400">Estudiantes·día equivalentes</span>
  <span class="font-mono text-sky-400 font-bold">{impact ? Math.round((impact.liters_saved||0)/14.04).toLocaleString() : '0'}</span>
  </div>
  <div class="flex items-center justify-between">
  <span class="text-slate-400">Acciones autónomas del agente</span>
  <span class="font-mono text-amber-400 font-bold">{impact ? impact.actions_taken : '0'}</span>
  </div>
  </div>

  <div class="mt-4 pt-3 border-t border-white/[0.06] text-[10px] text-slate-500 leading-relaxed">
  El agente convierte cada lectura de sensor en una <span class="text-sky-400">decisión cuantificada en litros</span>. Cada 14.04 L recuperados equivalen al consumo diario de un estudiante UNIAJC.
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
  <div class="am-keep w-7 h-7 rounded-lg bg-gradient-to-br from-sky-400 to-cyan-600 flex items-center justify-center shrink-0 text-white text-[11px] font-bold">AI</div>
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
  <div class="am-keep w-7 h-7 rounded-lg bg-gradient-to-br from-sky-400 to-cyan-600 flex items-center justify-center shrink-0 text-white text-[11px] font-bold">AI</div>
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
  { label: "Estudiantes·día equiv.",  value: impact ? Math.round((impact.liters_saved||0)/14.04).toLocaleString() : "0",  accent: "#0ea5e9", code: "👥" },
  { label: "Pérdidas evitadas/min",  value: reading ? `${fmt(reading.losses_l_min ?? 0, 1)} L/min` : "0 L/min",  accent: "#f59e0b", code: "P" },
  { label: "Acciones autónomas",  value: String(impact?.actions_taken ?? 0),  accent: "#a78bfa", code: "A" },
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
  <text x="360" y="352" text-anchor="middle" class="am-keep-fill" fill="white" font-size="16" font-family="JetBrains Mono" font-weight="bold">{fmt(reading?.tank_a_pct, 0)}%</text>
  <text x="360" y="370" text-anchor="middle" fill="rgba(34,197,94,0.7)" font-size="9">36k L</text>
  </g>

  <!-- Tank B -->
  <g>
  <rect x="430" y="315" width="70" height="70" rx="4" fill="rgba(56,189,248,0.10)" stroke="#38bdf8" stroke-width="2"/>
  <rect x="430" y="315" width="70" height="70" rx="4" fill="rgba(56,189,248,0.30)" style="clip-path: inset({100 - (reading?.tank_b_pct ?? 70)}% 0 0 0)"/>
  <text x="465" y="335" text-anchor="middle" fill="#38bdf8" font-size="10" font-family="Inter" font-weight="bold">Tank B</text>
  <text x="465" y="357" text-anchor="middle" class="am-keep-fill" fill="white" font-size="14" font-family="JetBrains Mono" font-weight="bold">{fmt(reading?.tank_b_pct, 0)}%</text>
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
  <div class="text-[26px] font-mono font-semibold text-white">{Math.round(gamification.stats.liters_saved_community / 14.04).toLocaleString()}</div>
  <div class="text-[10px] text-slate-500 mt-0.5">Estudiantes·día equiv.</div>
  <div class="text-[10px] text-emerald-400 mt-0.5">consumo recuperado</div>
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
  <div class="am-keep relative w-12 h-12 rounded-xl bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center font-bold text-white text-[14px]">
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
  <span class="text-[12px] font-semibold text-white">HidroTech</span>
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
  :global(html.light) .am-root .text-slate-700  { color: #334155; }

  /* Texto que debe quedarse blanco aunque sea modo claro (sobre fondos de color) */
  :global(html.light) .am-root .am-keep,
  :global(html.light) .am-root .am-keep * { color: #ffffff !important; }
  :global(html.light) .am-root .am-keep-fill { fill: #ffffff !important; }

  /* Drop-shadow para tanques en modo claro */
  :global(html.light) .am-root .drop-shadow-md { filter: drop-shadow(0 1px 2px rgba(0,0,0,0.3)); }

  /* Sombras de texto sobre agua de tanque: oscurecer en modo claro para mantener legibilidad blanca */
  :global(html.light) .am-root .am-tank-pct {
  text-shadow: 0 2px 8px rgba(0,0,0,0.55), 0 0 2px rgba(0,0,0,0.4) !important;
  }

  /* Header sticky */
  :global(html.light) .am-root header.sticky { background: rgba(248, 250, 252, 0.95); }
  :global(html.light) .am-root header { background: rgba(248, 250, 252, 0.92) !important; }

  /* Borde del badge de notificación (era ring-2 ring-[#0a0e14]) */
  :global(html.light) .am-root .ring-\[\#0a0e14\] { --tw-ring-color: #f8fafc; }

  /* Bg negro ([#060a10]) reemplazo en modo claro */
  :global(html.light) .am-root [style*="background:#0a0e14"],
  :global(html.light) .am-root [style*="background: #0a0e14"] { background: #f8fafc !important; }

  /* Tonos sky/emerald muy claros sobre fondos translúcidos: oscurecer en modo claro */
  :global(html.light) .am-root .text-sky-100  { color: #075985; }
  :global(html.light) .am-root .text-sky-200  { color: #0369a1; }
  :global(html.light) .am-root .text-sky-300  { color: #0284c7; }
  :global(html.light) .am-root .text-sky-400  { color: #0284c7; }
  :global(html.light) .am-root .text-emerald-400 { color: #047857; }
  :global(html.light) .am-root .text-amber-400 { color: #b45309; }
  :global(html.light) .am-root .text-red-400 { color: #b91c1c; }

  /* Placeholders */
  :global(html.light) .am-root input::placeholder,
  :global(html.light) .am-root textarea::placeholder { color: #94a3b8; }

  /* Inputs / selects: fondo y texto */
  :global(html.light) .am-root input,
  :global(html.light) .am-root select,
  :global(html.light) .am-root textarea { color: #0f172a; }

  /* Tooltips internos en gráfico (bg-slate-900) */
  :global(html.light) .am-root .bg-slate-900 { background: #1e293b; }
  :global(html.light) .am-root .bg-slate-800 { background: #334155; }

  /* Badge "Tú" del chat (bg-slate-700) en modo claro */
  :global(html.light) .am-root .bg-slate-700 { background: #cbd5e1; color: #0f172a; }

  /* SVG charts: ejes, gridlines y leyendas que respondan al tema */
  .am-root .am-grid    { stroke: rgba(255,255,255,0.05); }
  .am-root .am-axis    { fill: rgba(255,255,255,0.5); }
  .am-root .am-legend  { fill: rgba(255,255,255,0.7); }
  :global(html.light) .am-root .am-grid    { stroke: rgba(15,23,42,0.10); }
  :global(html.light) .am-root .am-axis    { fill: rgba(15,23,42,0.65); }
  :global(html.light) .am-root .am-legend  { fill: rgba(15,23,42,0.85); }

  /* Burbujas Tanque A */
  @keyframes bubble1 { 0%{transform:translateY(0);opacity:0} 20%{opacity:0.7} 100%{transform:translateY(-100px);opacity:0} }
  @keyframes bubble2 { 0%{transform:translateY(0);opacity:0} 20%{opacity:0.6} 100%{transform:translateY(-120px);opacity:0} }
  @keyframes bubble3 { 0%{transform:translateY(0);opacity:0} 20%{opacity:0.5} 100%{transform:translateY(-90px);opacity:0} }
  /* Burbujas Tanque B */
  @keyframes bubbleB1 { 0%{transform:translateY(0);opacity:0} 20%{opacity:0.7} 100%{transform:translateY(-95px);opacity:0} }
  @keyframes bubbleB2 { 0%{transform:translateY(0);opacity:0} 20%{opacity:0.6} 100%{transform:translateY(-110px);opacity:0} }
  @keyframes bubbleB3 { 0%{transform:translateY(0);opacity:0} 20%{opacity:0.5} 100%{transform:translateY(-85px);opacity:0} }
</style>
