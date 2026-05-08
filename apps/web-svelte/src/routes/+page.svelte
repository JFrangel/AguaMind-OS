<script lang="ts">
  // HidroTech — Landing de arquitectura
</script>

<svelte:head>
  <title>HidroTech · Sistema multi-agente de gestión hídrica</title>
</svelte:head>

<div class="min-h-screen bg-[#0a0e14] text-slate-100" style="font-family: 'Inter', -apple-system, system-ui, sans-serif;">

  <!-- Header -->
  <header class="border-b border-white/[0.06] bg-[#0a0e14]/90 backdrop-blur-xl sticky top-0 z-30">
    <div class="mx-auto max-w-7xl px-6 py-4 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="relative w-10 h-10 rounded-xl bg-gradient-to-br from-sky-400 via-sky-500 to-cyan-600 flex items-center justify-center shadow-lg shadow-sky-500/20">
          <svg viewBox="0 0 24 24" fill="none" class="w-5 h-5 text-white" stroke="currentColor" stroke-width="2.2">
            <path d="M12 2.5C12 2.5 6 9 6 14a6 6 0 0012 0c0-5-6-11.5-6-11.5z" stroke-linejoin="round"/>
          </svg>
          <span class="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-emerald-400 ring-2 ring-[#0a0e14] animate-pulse"></span>
        </div>
        <div class="leading-tight">
          <h1 class="text-[15px] font-semibold tracking-tight text-white flex items-center gap-1.5">
            HidroTech <span class="text-sky-400 font-light">OS</span>
          </h1>
          <p class="text-[11px] text-slate-500 mt-0.5 tracking-wide">UNIAJC Sede Sur · Hackathon 2026</p>
        </div>
      </div>
      <a href="/agua" class="px-4 py-2 rounded-lg bg-sky-500/15 hover:bg-sky-500/25 border border-sky-500/30 text-sky-300 text-[12px] font-medium transition-colors flex items-center gap-2">
        Abrir Dashboard
        <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M13 5l7 7-7 7"/></svg>
      </a>
    </div>
  </header>

  <main class="mx-auto max-w-7xl px-6 py-12">

    <!-- HERO -->
    <section class="text-center mb-20 relative">
      <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-500/10 border border-sky-500/20 text-[11px] text-sky-400 font-mono mb-6">
        <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
        Sistema operativo · 5 agentes · 5 sensores · 8 electroválvulas
      </div>
      <h2 class="text-[44px] sm:text-[56px] font-semibold tracking-tighter text-white leading-none mb-5">
        Sistema multi-agente<br/>
        <span class="bg-gradient-to-r from-sky-400 via-cyan-400 to-emerald-400 bg-clip-text text-transparent">de gestión hídrica</span>
      </h2>
      <p class="text-[16px] text-slate-400 max-w-2xl mx-auto leading-relaxed mb-8">
        Caracteriza · delibera · actúa. 5 agentes IA especializados con LangGraph deciden en 5 segundos lo que un humano tardaría 2 horas en analizar.
      </p>
      <div class="flex items-center justify-center gap-3 flex-wrap">
        <a href="/agua" class="px-5 py-2.5 rounded-lg bg-gradient-to-r from-sky-500 to-cyan-500 text-white text-[13px] font-medium hover:from-sky-400 hover:to-cyan-400 transition-all shadow-lg shadow-sky-500/20">
          Abrir Dashboard →
        </a>
        <a href="https://github.com/JFrangel/AguaMind-OS" target="_blank" class="px-5 py-2.5 rounded-lg border border-white/10 hover:border-white/20 hover:bg-white/[0.03] text-slate-300 text-[13px] font-medium transition-colors">
          Ver código fuente
        </a>
      </div>
    </section>

    <!-- LOS 5 AGENTES -->
    <section class="mb-20">
      <div class="mb-8">
        <div class="text-[10px] font-mono tracking-[0.2em] uppercase text-sky-400 mb-2">cómo deliberan</div>
        <h3 class="text-[28px] font-semibold tracking-tight text-white mb-2">5 agentes especializados</h3>
        <p class="text-[13px] text-slate-500">Cada uno mira el mismo evento desde un ángulo diferente · votan → consenso → acción</p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3">
        {#each [
          { code: "ORC", name: "Orchestrator",     role: "Coordinador",     desc: "Reparte tarea a los 4 agentes y consolida votos en 3.2s",                color: "#7dd3fc", framework: "LangGraph" },
          { code: "SYS", name: "SystemsAgent",     role: "Datos + KPIs",    desc: "Calcula IEH, TPP. Detecta anomalías con IsolationForest",                color: "#a855f7", framework: "scikit-learn" },
          { code: "SEN", name: "SensorAgent",      role: "Validación",      desc: "Verifica los 5 sensores (Q·R·P·N·H) en rango físico válido",            color: "#10b981", framework: "Pydantic" },
          { code: "IND", name: "IndustrialAgent",  role: "Lean + costos",   desc: "Mapea anomalías a las 7 mudas Lean y calcula impacto en kWh",            color: "#f59e0b", framework: "Reglas" },
          { code: "MIT", name: "MitigationAgent",  role: "Acción física",   desc: "Cierra EV, controla bomba, genera OT y push Telegram automático",        color: "#ef4444", framework: "FastAPI" },
        ] as a}
          <div class="rounded-2xl border bg-gradient-to-br from-white/[0.02] to-white/[0.005] p-5 transition-all hover:from-white/[0.04] hover:to-white/[0.01]" style="border-color:{a.color}30">
            <div class="flex items-start gap-3 mb-3">
              <div class="w-10 h-10 rounded-lg flex items-center justify-center text-[12px] font-mono font-bold shrink-0" style="background:{a.color}1A;color:{a.color};border:1px solid {a.color}40">{a.code}</div>
              <div class="flex-1 min-w-0">
                <div class="text-[13px] font-semibold text-white">{a.name}</div>
                <div class="text-[10px] text-slate-500 font-mono">{a.role}</div>
              </div>
            </div>
            <p class="text-[11px] text-slate-400 leading-relaxed mb-3">{a.desc}</p>
            <div class="text-[9px] font-mono uppercase tracking-wider px-2 py-0.5 rounded inline-block" style="background:{a.color}10;color:{a.color}">{a.framework}</div>
          </div>
        {/each}
      </div>
    </section>

    <!-- FRAMEWORKS Y STACK -->
    <section class="mb-20">
      <div class="mb-8">
        <div class="text-[10px] font-mono tracking-[0.2em] uppercase text-emerald-400 mb-2">stack tecnológico</div>
        <h3 class="text-[28px] font-semibold tracking-tight text-white mb-2">Frameworks & herramientas</h3>
        <p class="text-[13px] text-slate-500">Open source · cero costo de licencias · estándares de la industria</p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        {#each [
          { tier: "Multi-agente IA",      items: [
            { name: "LangGraph",     desc: "Orquestación de workflow entre agentes" },
            { name: "Gemini 2.0",    desc: "LLM principal · razonamiento + chat" },
            { name: "Groq Llama 3.3",desc: "Fallback rápido · 600 tokens/s" },
            { name: "IsolationForest",desc: "Detección anomalías estadísticas" },
          ] },
          { tier: "Backend",              items: [
            { name: "FastAPI",       desc: "API REST + SSE en Python 3.9+" },
            { name: "Pydantic",      desc: "Validación tipada + auto-docs" },
            { name: "uvicorn",       desc: "Servidor ASGI async de alto rendimiento" },
            { name: "Supabase",      desc: "PostgreSQL + auth + realtime" },
          ] },
          { tier: "Frontend",             items: [
            { name: "SvelteKit",     desc: "SSR + hidratación selectiva" },
            { name: "Svelte 5 runes",desc: "$state · $derived · $effect" },
            { name: "Tailwind CSS",  desc: "Sistema de diseño consistente" },
            { name: "TypeScript",    desc: "Tipos estrictos en todo el frontend" },
          ] },
          { tier: "IoT + Edge",           items: [
            { name: "ESP32-WROOM",   desc: "Microcontrolador WiFi 2.4 GHz" },
            { name: "MicroPython",   desc: "Firmware en cada nodo" },
            { name: "MQTT (HiveMQ)", desc: "Pub/Sub entre nodos y backend" },
            { name: "TinyML",        desc: "Detección acústica fugas embebida" },
          ] },
        ] as group}
          <div class="rounded-2xl border border-white/[0.06] bg-gradient-to-br from-white/[0.02] to-white/[0.005] p-5">
            <div class="text-[10px] font-mono tracking-wider uppercase text-slate-500 mb-3">{group.tier}</div>
            <div class="space-y-3">
              {#each group.items as item}
                <div>
                  <div class="text-[12px] font-semibold text-white">{item.name}</div>
                  <div class="text-[10px] text-slate-500 leading-snug">{item.desc}</div>
                </div>
              {/each}
            </div>
          </div>
        {/each}
      </div>
    </section>

    <!-- ARQUITECTURA POR CAPAS -->
    <section class="mb-20">
      <div class="mb-8">
        <div class="text-[10px] font-mono tracking-[0.2em] uppercase text-amber-400 mb-2">arquitectura</div>
        <h3 class="text-[28px] font-semibold tracking-tight text-white mb-2">7 capas independientes</h3>
        <p class="text-[13px] text-slate-500">Cada capa puede actualizarse sin afectar las demás · de hardware a UI</p>
      </div>

      <div class="rounded-2xl border border-white/[0.06] bg-gradient-to-br from-white/[0.02] to-white/[0.005] p-6">
        <div class="space-y-2">
          {#each [
            { layer: "07", name: "Aplicación",        tech: "SvelteKit · Bot Telegram · WhatsApp",  desc: "Dashboard 5 tabs · 12 comandos bot · push automático",     color: "#7dd3fc" },
            { layer: "06", name: "Inteligencia",      tech: "LangGraph · 5 agentes · LLM cascade",  desc: "Deliberación entre agentes · decisión consensual en 5s",   color: "#a855f7" },
            { layer: "05", name: "Persistencia",      tech: "Supabase PostgreSQL · pgvector",       desc: "Histórico tiempo · embeddings · realtime subscriptions",   color: "#0ea5e9" },
            { layer: "04", name: "Comunicación",      tech: "MQTT (HiveMQ) · HTTP fallback",        desc: "Pub/Sub topic-based · QoS 1 · TLS 8883",                   color: "#10b981" },
            { layer: "03", name: "Edge / Procesamiento", tech: "ESP32 + MicroPython · TinyML",      desc: "Buffer 30s · validación local · acústica embebida",        color: "#f59e0b" },
            { layer: "02", name: "Sensado",           tech: "5 sensores · ADS1115 16-bit",          desc: "Q · R · P · N · H con calibración pre-instalación",        color: "#fb923c" },
            { layer: "01", name: "Física",            tech: "PTAP · 2 PTAR · 8 electroválvulas",    desc: "Tubería · tanques · bombas Barnes · planos UNIAJC",        color: "#ef4444" },
          ] as l}
            <div class="flex items-stretch gap-3 group">
              <div class="w-12 flex items-center justify-center font-mono text-[11px] font-bold rounded-lg" style="background:{l.color}10;color:{l.color};border:1px solid {l.color}25">{l.layer}</div>
              <div class="flex-1 rounded-lg p-3 transition-colors group-hover:bg-white/[0.02]" style="border-left:2px solid {l.color}40">
                <div class="flex items-baseline justify-between gap-3 mb-1">
                  <h4 class="text-[13px] font-semibold text-white">{l.name}</h4>
                  <span class="text-[10px] font-mono text-slate-500">{l.tech}</span>
                </div>
                <p class="text-[11px] text-slate-400">{l.desc}</p>
              </div>
            </div>
          {/each}
        </div>
        <div class="mt-5 pt-4 border-t border-white/[0.04] text-[10px] text-slate-500 text-center font-mono">
          HidroTech = 7 capas independientes · cada una reemplazable sin afectar las demás
        </div>
      </div>
    </section>

    <!-- FLUJO DE DELIBERACIÓN -->
    <section class="mb-20">
      <div class="mb-8">
        <div class="text-[10px] font-mono tracking-[0.2em] uppercase text-purple-400 mb-2">cómo funciona</div>
        <h3 class="text-[28px] font-semibold tracking-tight text-white mb-2">De evento a acción en 5 segundos</h3>
        <p class="text-[13px] text-slate-500">Cada lectura de sensor pasa por 5 agentes que deliberan y deciden</p>
      </div>

      <div class="rounded-2xl border border-white/[0.06] bg-gradient-to-br from-white/[0.02] to-white/[0.005] p-6">
        <div class="grid grid-cols-1 md:grid-cols-7 gap-3 items-stretch">
          {#each [
            { t: "T+0.0s",  who: "Sensor",       msg: "MQTT publica vibración + caída presión 28%",      color: "#7dd3fc" },
            { t: "T+0.5s",  who: "Orchestrator", msg: "Reparte tarea a 4 agentes en paralelo",           color: "#a855f7" },
            { t: "T+1.5s",  who: "SystemsAgent", msg: "Crítico (88%) · IsolationForest 0.78",            color: "#a855f7" },
            { t: "T+1.7s",  who: "SensorAgent",  msg: "OK (95%) · 5/5 sensores en rango",                color: "#10b981" },
            { t: "T+2.0s",  who: "Industrial",   msg: "Crítico (85%) · muda Defectos · $2150/min",        color: "#f59e0b" },
            { t: "T+3.0s",  who: "Mitigation",   msg: "EJECUTA · cierra EV-A2 + bomba standby",           color: "#ef4444" },
            { t: "T+5.0s",  who: "Resultado",    msg: "OT generada · Telegram enviado · 14,500 L salvados", color: "#10b981" },
          ] as step}
            <div class="rounded-xl border bg-white/[0.02] p-3 flex flex-col" style="border-color:{step.color}25">
              <div class="text-[9px] font-mono text-slate-500 mb-1">{step.t}</div>
              <div class="text-[11px] font-semibold mb-2" style="color:{step.color}">{step.who}</div>
              <div class="text-[10px] text-slate-400 leading-snug flex-1">{step.msg}</div>
            </div>
          {/each}
        </div>
      </div>
    </section>

    <!-- CTA FINAL -->
    <section class="rounded-3xl border border-sky-500/20 bg-gradient-to-br from-sky-500/[0.08] via-cyan-500/[0.04] to-transparent p-10 text-center mb-12">
      <h3 class="text-[28px] font-semibold tracking-tight text-white mb-3">HidroTech se adapta · vigila · actúa</h3>
      <p class="text-[14px] text-slate-400 mb-6 max-w-xl mx-auto">
        El dashboard te muestra todo en vivo: KPIs, los 5 sensores, deliberación de agentes, mapa del campus, gamificación con la comunidad.
      </p>
      <a href="/agua" class="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-gradient-to-r from-sky-500 to-cyan-500 text-white text-[14px] font-medium hover:from-sky-400 hover:to-cyan-400 transition-all shadow-lg shadow-sky-500/30">
        Entrar al Dashboard
        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M13 5l7 7-7 7"/></svg>
      </a>
    </section>

  </main>

  <!-- Footer -->
  <footer class="border-t border-white/[0.04]">
    <div class="mx-auto max-w-7xl px-6 py-6 flex flex-wrap items-center justify-between gap-3 text-[10px] text-slate-600">
      <div>HidroTech · Hackathon UNIAJC 2026 · Open source MIT</div>
      <div class="flex items-center gap-3">
        <span>Tecnología con Propósito · Inteligencia con Conciencia</span>
      </div>
    </div>
  </footer>
</div>

<style>
  :global(html), :global(body) {
    background: #0a0e14;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }
</style>
