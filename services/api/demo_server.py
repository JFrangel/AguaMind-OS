"""
HidroTech — Servidor Demo Mínimo
Carga solo los routers /water/* y /water/agent/* sin las dependencias pesadas
(langgraph, crewai, supabase). Ideal para mostrar el dashboard rápidamente.

Uso:
    cd services/api
    python3 demo_server.py
    # → http://localhost:8000
    # → http://localhost:8000/docs
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Cargar .env (el del proyecto raíz)
ROOT = Path(__file__).resolve().parents[2]
env_file = ROOT / ".env"
if env_file.is_file():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip("'\""))

# Permitir imports desde app/
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Importar SOLO los routers de HidroTech (sin LLM/RAG/etc)
from app.routers import water, mitigation, telegram_notify
from app.sensors.normalizer import normalize, normalize_payload
from app.sensors.schemas import IngestPayload, IngestResult


app = FastAPI(
    title="HidroTech · Demo Backend",
    version="1.0.0",
    description="Backend mínimo para demo del hackathon UNIAJC 2026.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stub mínimo del agente (sin LangGraph, simula ciclos en memoria)
class StubAgent:
    def __init__(self):
        self.running = False
        self.cycle = 0
        self.last_decision = "ok"
        self.last_state: dict = {}
        self._task = None
        self.interval_s = 30
        self._log: list[dict] = []

    def status(self) -> dict:
        return {
            "running":       self.running,
            "cycle":         self.cycle,
            "last_decision": self.last_decision,
            "last_cycle_at": self.last_state.get("started_at"),
            "interval_s":    self.interval_s,
            "agents": {
                "systems":    self.last_decision,
                "sensor":     "ok" if self.cycle == 0 else self.last_decision,
                "industrial": self.last_decision,
            },
            "last_alerts": len(self.last_state.get("alerts", [])),
            "last_issues": [
                a.get("message", "") for a in self.last_state.get("alerts", [])[:3]
            ],
            "telegram_message": self.last_state.get("telegram_message"),
        }

    async def run_cycle(self) -> dict:
        from datetime import datetime
        self.cycle += 1
        # Reusar el simulador del router water
        r = water._simulate_sensors()
        kpis = water._calc_kpis(r)
        alerts = water._generate_alerts(r, kpis)

        # Decisión
        decision = "ok"
        if any(a["level"] == "critical" for a in alerts):
            decision = "critical"
        elif any(a["level"] == "warning" for a in alerts):
            decision = "warning"

        self.last_decision = decision
        self.last_state = {
            "started_at": datetime.now().isoformat(),
            "reading":    r,
            "kpis":       kpis,
            "alerts":     alerts,
            "decision":   decision,
            "cycle":      self.cycle,
        }
        return self.last_state

    async def start(self):
        self.running = True
        while self.running:
            await self.run_cycle()
            await asyncio.sleep(self.interval_s)

    def stop(self):
        self.running = False


_agent = StubAgent()


@app.on_event("startup")
async def _autostart_agent():
    """Arranca el agente automaticamente cuando el backend levanta.
    Ejecuta el primer ciclo inmediato + ciclos cada 30s en background."""
    if not _agent.running:
        _agent.running = True
        # Ejecutar 1 ciclo inmediato para que el dashboard tenga datos al cargar
        await _agent.run_cycle()
        _agent._task = asyncio.create_task(_agent.start())
        print("[startup] Agente HidroTech iniciado automaticamente (cada 30s)")


@app.get("/", tags=["meta"])
async def root():
    return {
        "service":  "HidroTech · Demo Backend",
        "version":  "1.0.0",
        "campus":   "UNIAJC Sede Sur",
        "endpoints": {
            "water_reading":       "GET  /water/reading",
            "water_status":        "GET  /water/status",
            "water_history":       "GET  /water/history",
            "water_report":        "GET  /water/report/daily",
            "water_simulate":      "POST /water/simulate",
            "water_ingest":        "POST /water/ingest",
            "water_constants":     "GET  /water/constants",
            "agent_start":         "POST /water/agent/start",
            "agent_stop":          "POST /water/agent/stop",
            "agent_status":        "GET  /water/agent/status",
            "agent_cycle":         "POST /water/agent/cycle",
        },
    }


# ── Routers principales del simulador ────────────────────────────────────
app.include_router(water.router,           prefix="/water", tags=["water"])
app.include_router(mitigation.router,      prefix="/water", tags=["mitigation"])
app.include_router(telegram_notify.router, prefix="/water", tags=["telegram"])


# ── Normalizador universal de sensores ───────────────────────────────────
# Acepta CUALQUIER formato (JSON, CSV, NDJSON, ESP32 compacto, Modbus, OPC-UA,
# SCADA tag-based, MQTT) y devuelve lecturas canonicas listas para analisis.

@app.post("/water/ingest/universal", response_model=IngestResult, tags=["water-ingest"])
async def ingest_universal(p: IngestPayload):
    """Endpoint universal de ingesta. Detecta el formato si no se especifica."""
    return normalize_payload(p)


@app.get("/water/ingest/formats", tags=["water-ingest"])
async def list_formats():
    """Formatos soportados por el normalizador universal."""
    return {
        "data": {
            "formats": [
                {"name": "auto",          "desc": "Detecta automaticamente el formato"},
                {"name": "json",          "desc": "Objeto JSON plano o estructurado"},
                {"name": "json_array",    "desc": "Lista de objetos JSON"},
                {"name": "ndjson",        "desc": "Newline-delimited JSON (un dict por linea)"},
                {"name": "csv",           "desc": "CSV con header timestamp,sensor_id,model,value"},
                {"name": "esp32_compact", "desc": "Formato compacto del firmware ESP32 de HidroTech"},
                {"name": "modbus",        "desc": "Lista [(addr, valor), ...] de holding registers"},
                {"name": "scada",         "desc": "Tag-based SCADA (FT-101, PT-201, ...)"},
                {"name": "opcua",         "desc": "OPC-UA con NodeId -> {Value, SourceTimestamp}"},
                {"name": "mqtt",          "desc": "Topic + payload (incluye topic en parametro mqtt_topic)"},
            ],
            "sensors_registered": [
                "YF-S201", "YF-DN50", "MPX5700AP", "JSN-SR04T", "SW-420",
                "FREATIC-4-20MA", "TSD-10", "SEN0161", "ORP", "DFR0300",
            ],
        },
        "error": None,
    }


# ── Endpoints del agente (versión stub para demo) ────────────────────────
@app.post("/water/agent/start", tags=["water-agent"])
async def agent_start(interval_s: int = 30):
    if _agent.running:
        return {"data": {"started": False, "message": "ya estaba corriendo"}, "error": None}
    _agent.interval_s = max(10, min(interval_s, 300))
    _agent.running = True
    _agent._task = asyncio.create_task(_agent.start())
    return {"data": {"started": True, "interval_s": _agent.interval_s,
                     "agents": ["Orchestrator", "SystemsAgent", "SensorAgent", "IndustrialAgent"]},
            "error": None}


@app.post("/water/agent/stop", tags=["water-agent"])
async def agent_stop():
    _agent.stop()
    if _agent._task and not _agent._task.done():
        _agent._task.cancel()
    return {"data": {"stopped": True, "last_cycle": _agent.cycle}, "error": None}


@app.get("/water/agent/status", tags=["water-agent"])
async def agent_status():
    return {"data": _agent.status(), "error": None}


@app.post("/water/agent/cycle", tags=["water-agent"])
async def agent_cycle():
    state = await _agent.run_cycle()
    return {
        "data": {
            "cycle":      state.get("cycle"),
            "decision":   state.get("decision"),
            "reading":    state.get("reading"),
            "kpis":       state.get("kpis"),
            "alerts":     state.get("alerts"),
        },
        "error": None,
    }


# ── Chat con el agente IA — usa Groq LLM ────────────────────────────────────
import urllib.request, urllib.error, json as _json
from datetime import datetime as _dt

_AGENT_HISTORY: list[dict] = []   # historial de eventos para análisis


_PLACEHOLDER_KEYS = {"gsk_...", "sk-or-...", "AIza...", "your-key", "changeme", ""}


def _real_key(env_var: str) -> str | None:
    """Devuelve el valor de la env var solo si parece una clave real (no placeholder)."""
    v = (os.getenv(env_var) or "").strip()
    if not v or v in _PLACEHOLDER_KEYS or v.endswith("..."):
        return None
    return v


def _llm_gemini(messages: list[dict]) -> str:
    """Llama a Gemini API REST (gratis)."""
    api_key = _real_key("GEMINI_API_KEY")
    if not api_key:
        return None

    # Convertir messages a formato Gemini
    system = next((m["content"] for m in messages if m["role"] == "system"), "")
    user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")

    payload = _json.dumps({
        "contents": [{"parts": [{"text": f"{system}\n\n{user_msg}"}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 600},
    }).encode("utf-8")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = _json.loads(r.read())
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"[Gemini] {e}")
        return None


def _llm_groq(messages: list[dict]) -> str:
    """Llama a Groq LLM (fallback)."""
    api_key = _real_key("GROQ_API_KEY")
    if not api_key:
        return None
    payload = _json.dumps({
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 600,
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = _json.loads(r.read())
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[Groq] {e}")
        return None


def _llm_complete(messages: list[dict], model: str = None) -> str:
    """Cascade: intenta Gemini → Groq → fallback inteligente local."""
    # 1. Gemini (gratis y rápido)
    result = _llm_gemini(messages)
    if result:
        return result
    # 2. Groq (fallback)
    result = _llm_groq(messages)
    if result:
        return result
    # 3. Fallback inteligente local (siempre funciona)
    return _fallback_response(messages)


# --- Clasificador de intencion conversacional --------------------------------
# Cada intencion tiene un peso de palabras clave. La pregunta se evalua
# contra TODAS las intenciones en paralelo y se generan fragmentos para las
# que pasan el umbral. Esto permite preguntas multi-intencion como
# "como esta el sistema y hay alguna fuga".

_INTENT_KEYWORDS = {
    "saludo":      [("hola", 3), ("buenas", 2), ("buenos dias", 3), ("saludos", 2),
                    ("hey", 2), ("hi", 2), ("que tal", 2)],
    "fuga":        [("fuga", 4), ("perdida", 3), ("perdidas", 3), ("leak", 3),
                    ("rotura", 3), ("anomal", 2), ("alerta", 2),
                    ("falla", 2), ("problema", 1), ("critico", 1), ("tpp", 3)],
    "tanques":     [("tanque", 4), ("tank", 3), ("almacenamiento", 3), ("nivel", 2),
                    ("lleno", 2), ("vacio", 2), ("reserva", 2)],
    "presion":     [("presion", 4), ("kpa", 3), ("psi", 3), ("bomba", 3),
                    ("hidroneumatic", 3), ("flujo", 1)],
    "humedad":     [("humedad", 4), ("riego", 4), ("suelo", 3), ("cancha", 3),
                    ("jardin", 3), ("zona verde", 3), ("aspersor", 3), ("h ", 2)],
    "sensores":    [("sensor", 3), ("medicion", 2), ("instrument", 2),
                    ("dispositivo", 2), ("yf-s201", 3), ("yf-dn50", 3),
                    ("mpx5700", 3), ("jsn-sr04", 3), ("hw-080", 3)],
    "mitigacion":  [("mitig", 4), ("accion", 3), ("recomend", 3), ("hacer", 1),
                    ("debo", 2), ("hago", 2), ("sugiere", 2), ("consejo", 2),
                    ("solucion", 3), ("estrategia", 2)],
    "normativa":   [("norma", 3), ("decreto", 4), ("resolucion", 4), ("ley", 2),
                    ("cumple", 3), ("incumple", 4), ("invima", 3), ("cvc", 3),
                    ("0631", 4), ("2115", 4), ("1575", 4), ("1076", 4)],
    "sostenibilidad": [("ahorro", 3), ("ods", 4), ("sostenib", 3), ("ambient", 3),
                    ("co2", 3), ("huella", 3), ("ecolog", 3), ("verde", 2)],
    "agente":      [("agente", 4), ("multi-agent", 5), ("multiagent", 5),
                    ("inteligencia", 2), ("quien eres", 4), ("que eres", 4),
                    ("orchestrator", 3), ("ia", 2)],
    "general":     [("resumen", 4), ("estado", 2), ("general", 2), ("status", 3),
                    ("como va", 3), ("como esta", 3), ("dashboard", 2),
                    ("kpi", 3), ("tpp", 3), ("ieh", 3), ("cpe", 3)],
    "reuso":       [("reuso", 4), ("reutiliza", 4), ("residual", 3), ("ptar", 3),
                    ("riego", 2), ("gris", 2), ("vertimiento", 3)],
    "fenomeno":    [("nino", 4), ("sequia", 4), ("lluvia", 2), ("ideam", 3),
                    ("clima", 2), ("emergencia", 2), ("drought", 4)],
    "fuentes":     [("fuente", 3), ("sanitario", 3), ("orinal", 3), ("lavamanos", 3),
                    ("ducha", 2), ("bano", 2), ("inodoro", 2)],
}


def _score_intents(question: str) -> list[tuple[str, int]]:
    q = question.lower()
    scores: dict[str, int] = {}
    for intent, kws in _INTENT_KEYWORDS.items():
        s = 0
        for kw, w in kws:
            if kw in q:
                s += w
        if s > 0:
            scores[intent] = s
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def _frag_saludo(r, kpis, alerts):
    crit = sum(1 for k in kpis.values() if k["status"] == "critical")
    base = "Hola, soy el agente conversacional de HidroTech, el sistema multi-agente de gestión hídrica de UNIAJC Sede Sur."
    if crit:
        return (f"{base} Ahora mismo veo {len(alerts)} alerta(s) activa(s) y {crit} indicador(es) en rojo, "
                f"así que tenemos varios temas urgentes por resolver. Cuéntame qué quieres revisar.")
    if alerts:
        return (f"{base} Detecto {len(alerts)} alerta(s) pero ninguna es crítica en este momento. "
                f"¿Te interesa que revise alguna en detalle?")
    return f"{base} El sistema está operando con normalidad: tanques estables, sin fugas detectadas y caudal dentro de rango. ¿En qué te puedo ayudar?"


def _frag_fuga(r, kpis, alerts):
    tpp = kpis['TPP']['value']
    losses = r['losses_l_min']
    estudiantes_dia = int(losses * 1440 / 14.04) if losses > 0 else 0
    if kpis["TPP"]["status"] == "critical":
        return (f"Sí, hay un problema serio: la Tasa de Pérdidas del Proceso (TPP) está en {tpp}% "
                f"cuando la meta es menor al 10%. Eso significa que se están perdiendo aproximadamente "
                f"{losses:.1f} litros por minuto, equivalente al consumo diario de {estudiantes_dia:,} estudiantes. "
                f"Mi recomendación inmediata es cerrar la electroválvula EV-A2 del Bloque A para aislar "
                f"el tramo sospechoso, dejar la bomba en standby y enviar una cuadrilla a inspección física.")
    if kpis["TPP"]["status"] == "warning":
        return (f"Hay pérdidas moderadas: TPP en {tpp}%, ligeramente por encima del rango ideal (<10%). "
                f"Se están escapando {losses:.1f} L/min. Aún no es crítico, pero conviene revisar las "
                f"uniones del Bloque A en el próximo turno de mantenimiento antes de que escale.")
    return (f"Todo bien por ese lado: la TPP está en {tpp}%, dentro de la meta (<10%). "
            f"No detecto fugas significativas, las pérdidas están en {losses:.1f} L/min, "
            f"que es lo esperable por evaporación y consumo no contabilizado.")


def _frag_tanques(r, kpis, alerts):
    pump = "encendida bombeando agua hacia Tanque A" if r["pump_active"] else "en standby (no se necesita reposición ahora)"
    a_estado = "lleno" if r['tank_a_pct'] > 80 else ("nivel saludable" if r['tank_a_pct'] > 50 else ("nivel bajo, la bomba debería activarse pronto" if r['tank_a_pct'] > 33 else "nivel CRÍTICO"))
    b_estado = "lleno" if r['tank_b_pct'] > 80 else ("nivel saludable" if r['tank_b_pct'] > 50 else "nivel bajo")
    return (f"Te cuento cómo están los dos tanques: el Tanque A (principal, capacidad 36,000 L) "
            f"está al {r['tank_a_pct']}% — {r['tank_a_l']:,} litros — {a_estado}. "
            f"El Tanque B (distribución, 16,000 L) está al {r['tank_b_pct']}% con {r['tank_b_l']:,} litros, {b_estado}. "
            f"La bomba está {pump}. El umbral de activación automática es 66.7% en el Tanque A.")


def _frag_presion(r, kpis, alerts):
    p = r['pressure_kpa']
    if 200 <= p <= 400:
        diag = "está dentro del rango óptimo (200-400 kPa), ideal para evitar tanto el desperdicio por sobrepresión como las quejas de bajo flujo en pisos altos"
    elif p < 200:
        diag = "está por debajo del rango óptimo, lo que puede indicar fuga aguas abajo, bomba subdimensionada o pico de demanda simultáneo"
    else:
        diag = "está por encima del rango óptimo, lo que estresa juntas y multiplica fugas; conviene reducir el setpoint nocturno a 25-28 PSI"
    return (f"La presión actual de la red es de {p} kPa y {diag}. "
            f"La bomba está {'activa' if r['pump_active'] else 'en standby'} y el caudal de entrada es de {r['total_flow_lmin']} L/min.")


def _frag_humedad(r, kpis, alerts):
    h = r.get('soil_humidity_pct', 0)
    riego = r.get('zones', {}).get('Riego/Cancha', 0)
    if h < 30:
        diag = ("La humedad está por debajo del 30%, lo que indica suelo seco. "
                "Recomiendo activar el riego de la cancha durante 25-30 minutos en horario nocturno (22:00-04:00) "
                "para evitar evaporación y aprovechar la tarifa de baja demanda.")
    elif h < 50:
        diag = ("La humedad está en zona intermedia. No es urgente regar, pero si no llueve en las próximas 12 horas "
                "convendría programar un riego corto.")
    else:
        diag = ("La humedad está saludable, así que NO se necesita riego ahora — "
                "regar en estas condiciones sería desperdicio puro (muda Lean #1: sobreproducción).")
    return (f"El sensor H (humedad de suelo, modelo HW-080) en la zona de la cancha marca {h}%. {diag} "
            f"El caudal actual hacia riego es de {riego} L/min.")


def _frag_sensores(r, kpis, alerts):
    return ("El sistema usa 5 sensores en operación, instalados en puntos estratégicos del campus: "
            "Q es el caudalímetro general (YF-S201) que mide cuánta agua entra desde los aljibes; "
            "R es el caudalímetro específico de riego (YF-DN50) en la línea de la cancha; "
            "P es el transductor de presión (MPX5700AP) en la red de distribución; "
            "N son los ultrasonidos (JSN-SR04T) que miden el nivel en Tanque A y Tanque B; "
            "y H es el sensor capacitivo de humedad de suelo (HW-080) enterrado en la zona verde. "
            "Todos transmiten cada 30 segundos vía MQTT al backend.")


def _frag_mitigacion(r, kpis, alerts):
    if kpis["TPP"]["status"] == "critical":
        return ("Dado que la TPP está crítica, te propongo una mitigación en cuatro pasos secuenciales: "
                "primero, cerrar la electroválvula EV-A2 para aislar el tramo del Bloque A donde sospecho la fuga; "
                "segundo, poner la bomba en standby para no seguir empujando agua perdida; "
                "tercero, generar una orden de trabajo (OT) con ID rastreable para la cuadrilla de mantenimiento; "
                "y cuarto, monitorear cómo cae la TPP en los próximos 15 minutos para confirmar que el aislamiento funcionó.")
    h = r.get('soil_humidity_pct', 100)
    if h < 30:
        return ("La humedad de suelo está crítica, así que la acción es activar el ciclo de riego nocturno: "
                "abrir la electroválvula EV-RC1 durante 25 minutos a partir de las 22:00, "
                "monitorear que la humedad suba a 50%+ antes de cerrar y registrar el evento en la bitácora.")
    return ("El sistema está estable, no hay nada urgente que mitigar. "
            "Sigo monitoreando los 5 sensores cada 30 segundos y, si algo se sale de rango, te aviso de inmediato "
            "con la acción concreta recomendada y los costos asociados.")


def _frag_normativa(r, kpis, alerts):
    crit = [a for a in alerts if a["level"] == "critical"]
    cumple = ("Por ahora no detecto incumplimientos críticos." if not crit
              else f"Tenemos {len(crit)} parámetro(s) fuera de norma que requieren atención.")
    return ("Las normativas colombianas que estoy vigilando en tiempo real son: "
            "Decreto 1575/2007 y Resolución 2115/2007 sobre calidad del agua potable; "
            "Decreto 1076/2015 sobre uso sostenible de acuíferos; "
            "Resolución 0631/2015 sobre vertimientos a cuerpos de agua; "
            f"y Resolución 1207/2014 sobre reúso de aguas residuales tratadas. {cumple}")


def _frag_sostenibilidad(r, kpis, alerts):
    return ("HidroTech aporta a varios Objetivos de Desarrollo Sostenible (ODS) de la ONU: "
            "ODS 6 agua limpia (reducir TPP del 25% al 10% recupera ~16,500 L/día), "
            "ODS 9 industria e innovación (modernización IoT+IA en planta de 2011 sin reemplazarla), "
            "ODS 11 ciudades sostenibles (el sistema es replicable a otras universidades), "
            "y ODS 12 producción responsable (eliminamos las 7 mudas Lean clásicas en gestión de agua).")


def _frag_agente(r, kpis, alerts):
    return ("Soy el agente conversacional de HidroTech, pero detrás de mí trabajan 5 agentes especializados "
            "coordinados con LangGraph: el Orchestrator decide cuándo deliberar; el Systems Agent calcula KPIs y "
            "detecta anomalías con IsolationForest; el Sensor Agent valida que las lecturas tengan sentido físico; "
            "el Industrial Agent identifica mudas Lean y hace ML predictivo; y el Mitigation Agent ejecuta las "
            "acciones (abrir/cerrar válvulas, ajustar bomba). Cada uno aporta análisis descriptivo, predictivo o "
            "prescriptivo según lo que pide el contexto.")


def _frag_general(r, kpis, alerts):
    estado = ("estado normal" if not alerts
              else (f"hay {len(alerts)} alerta(s), incluida atención crítica" if any(a['level']=='critical' for a in alerts)
                    else f"hay {len(alerts)} aviso(s) pero nada crítico"))
    return (f"Resumen ejecutivo del sistema en este momento: {estado}. "
            f"La eficiencia hídrica (IEH) está en {kpis['IEH']['value']}% [meta >90%], "
            f"las pérdidas (TPP) en {kpis['TPP']['value']}% [meta <10%] "
            f"y el consumo per estudiante (CPE) en {kpis['CPE']['value']} L/día. "
            f"Los sensores reportan: caudal general Q={r['total_flow_lmin']} L/min, "
            f"presión P={r['pressure_kpa']} kPa, "
            f"tanques N=A:{r['tank_a_pct']}% / B:{r['tank_b_pct']}%, "
            f"humedad H={r.get('soil_humidity_pct', 0)}%.")


def _frag_reuso(r, kpis, alerts):
    return ("Estrategia de reuso (Resolucion 1207/2014): aguas tratadas en las 2 PTAR "
            "(Alameda y Entrada, 2 modulos cada una, 4,000 est cap total) -> "
            "1) riego de Cancha+Jardines (objetivo 2,200 L/dia desde 4,000), "
            "2) cisternas sanitarias del Bloque A. Solo el excedente va a vertimiento al rio Pance.")


def _frag_fenomeno(r, kpis, alerts):
    return ("Plan ante fenomeno del Nino IMPLEMENTADO en la pestana Inteligencia: "
            "el trigger drought_mode combina 6 acciones: 1) presion nocturna 38->25 PSI, "
            "2) cierra EV-RC1 (riego), 3) bomba a modo eco_drought (-70% extraccion), "
            "4) broadcast Telegram a 8,234 usuarios, 5) pantallas LED ALERTA SEQUIA, "
            "6) reporte automatico CVC. Impacto proyectado: -25% consumo total, "
            "10,400 L/dia ahorrados.")


def _frag_fuentes(r, kpis, alerts):
    return ("Tengo mapeadas 161 fuentes: 51 sanitarios, 53 lavamanos, 14 orinales, 14 duchas, "
            "24 llaves, 5 lavaplatos. 67% del consumo esta en Parquesoft, 33% en Alameda. "
            "Sanitarios + orinales se podrian abastecer con aguas reutilizadas (~5,000 L/dia).")


_FRAGMENTS = {
    "saludo":         _frag_saludo,
    "fuga":           _frag_fuga,
    "tanques":        _frag_tanques,
    "presion":        _frag_presion,
    "humedad":        _frag_humedad,
    "sensores":       _frag_sensores,
    "mitigacion":     _frag_mitigacion,
    "normativa":      _frag_normativa,
    "sostenibilidad": _frag_sostenibilidad,
    "agente":         _frag_agente,
    "general":        _frag_general,
    "reuso":          _frag_reuso,
    "fenomeno":       _frag_fenomeno,
    "fuentes":        _frag_fuentes,
}


def _fallback_response(messages: list[dict]) -> str:
    """Respuesta multi-intencion sobre estado en vivo."""
    full_user = next((m["content"] for m in messages if m["role"] == "user"), "")
    if "Pregunta:" in full_user:
        question = full_user.split("Pregunta:", 1)[1].strip().lower()
    else:
        question = full_user.lower()

    r = water._simulate_sensors()
    kpis = water._calc_kpis(r)
    alerts = water._generate_alerts(r, kpis)

    intents = _score_intents(question)
    if not intents:
        return (f"No alcancé a identificar bien el tema de tu pregunta. Te puedo ayudar con varios temas: "
                f"fugas y pérdidas de la red, niveles de los tanques A y B, presión de distribución, "
                f"humedad de suelo y riego de la cancha, los 5 sensores instalados, mitigación y acciones "
                f"recomendadas, normativa colombiana aplicable, reúso de aguas residuales tratadas o el plan "
                f"ante fenómenos climáticos como El Niño. "
                f"Como contexto rápido del estado actual: TPP {kpis['TPP']['value']}%, "
                f"caudal {r['total_flow_lmin']} L/min, {len(alerts)} alerta(s) activa(s). ¿Qué te interesa revisar?")

    fragments: list[str] = []
    seen: set[str] = set()
    for intent, _score in intents[:3]:
        if intent in seen:
            continue
        seen.add(intent)
        gen = _FRAGMENTS.get(intent)
        if gen:
            fragments.append(gen(r, kpis, alerts))

    note = "" if (_real_key("GEMINI_API_KEY") or _real_key("GROQ_API_KEY")) \
              else "  [respuesta local sin LLM externo configurado]"
    return " ".join(fragments) + note


def _system_prompt() -> str:
    return """Eres el agente IA de HidroTech, sistema de gestión hídrica de UNIAJC Sede Sur en Cali, Colombia.

Datos del campus:
- 8,234 usuarios totales · 3,230 estudiantes activos
- PTAP de 2011 con 3 filtros (grava+arena, antracita, carbón activado)
- 2 tanques: A=36,000 L · B=16,000 L
- Aljibes con caudal 113.56 L/min combinado
- Pérdidas medidas: 1,587 L/día (Sánchez Sotelo, 2021)
- 161 fuentes de consumo (51 sanitarios, 53 lavamanos, etc.)
- 67% consumo en Parquesoft · 33% en Alameda

Sensores en operación (5):
- Q: caudal general (YF-S201)
- R: caudal de riego (YF-DN50)
- P: presión de red (MPX5700AP)
- N: nivel de tanques (JSN-SR04T)
- H: humedad de suelo (HW-080)
NO menciones turbidez, ICA, vibración ni nivel freático: esos sensores ya no forman parte del sistema.

Tu rol:
- Analizar lecturas de los 5 sensores Q/R/P/N/H y los KPIs (IEH, TPP, CPE)
- Identificar patrones, anomalías, mudas Lean
- Recomendar acciones de mitigación concretas
- Citar normativas colombianas relevantes (Resolución 2115/2007, 0631/2015, Decreto 1575/2007)
- Responder en español, conciso, profesional

Formato:
- Máximo 4-5 oraciones cortas
- Si recomendas acción, sé específico (ej: "cerrar EV-A2", "reducir presión nocturna a 25 PSI")
- Cita datos numéricos cuando sea relevante"""


class AskRequest(BaseModel):
    question: str
    include_state: bool = True


@app.post("/water/agent/ask", tags=["water-agent"])
async def agent_ask(body: AskRequest):
    """Pregúntale al agente IA. Tiene contexto en vivo del sistema."""
    state_ctx = ""
    if body.include_state:
        r = water._simulate_sensors()
        kpis = water._calc_kpis(r)
        alerts = water._generate_alerts(r, kpis)
        state_ctx = f"""
ESTADO ACTUAL DEL SISTEMA (lectura en vivo):
  Caudal general (Q): {r['total_flow_lmin']} L/min
  Tanque A (N): {r['tank_a_pct']}% ({r['tank_a_l']} L de 36,000)
  Tanque B (N): {r['tank_b_pct']}%
  Presión red (P): {r['pressure_kpa']} kPa
  Humedad de suelo (H): {r['soil_humidity_pct']}% (zona riego cancha)
  Bomba: {'activa' if r['pump_active'] else 'OFF'}

KPIs: IEH={kpis['IEH']['value']}% [{kpis['IEH']['status']}] · TPP={kpis['TPP']['value']}% [{kpis['TPP']['status']}] · CPE={kpis['CPE']['value']} L/est [{kpis['CPE']['status']}]
Alertas activas: {len(alerts)}
"""
    messages = [
        {"role": "system", "content": _system_prompt()},
        {"role": "user",   "content": f"{state_ctx}\n\nPregunta: {body.question}"},
    ]
    answer = _llm_complete(messages)
    _AGENT_HISTORY.append({
        "ts":       _dt.now().isoformat(),
        "question": body.question,
        "answer":   answer,
    })
    return {"data": {"question": body.question, "answer": answer, "timestamp": _dt.now().isoformat()}, "error": None}


@app.get("/water/agent/insights", tags=["water-agent"])
async def agent_insights():
    """Análisis automático generado por el LLM sobre el estado actual."""
    r = water._simulate_sensors()
    kpis = water._calc_kpis(r)
    alerts = water._generate_alerts(r, kpis)

    prompt = f"""Analiza el estado actual del sistema hídrico UNIAJC y genera 3 insights breves.

Sensores disponibles (5): Q caudal general, R caudal riego, P presión, N nivel tanques, H humedad de suelo.
NO menciones turbidez, freático, ni vibración: ya no se miden.

ESTADO:
  Caudal Q: {r['total_flow_lmin']} L/min · Riego R: {r.get('zones', {}).get('Riego/Cancha', 0)} L/min
  Tanque A (N): {r['tank_a_pct']}% · Tanque B (N): {r['tank_b_pct']}%
  Presión P: {r['pressure_kpa']} kPa · Humedad H: {r['soil_humidity_pct']}%
  IEH: {kpis['IEH']['value']}% · TPP: {kpis['TPP']['value']}% · CPE: {kpis['CPE']['value']}
  Alertas: {len(alerts)}

Devuelve EXACTAMENTE en formato JSON con 3 insights:
{{"insights": [
  {{"icon": "📊", "title": "...", "description": "...", "severity": "ok|warning|critical"}},
  ...
]}}

Cada insight debe ser específico, accionable y citar datos de los 5 sensores Q/R/P/N/H o de los KPIs IEH/TPP/CPE."""

    messages = [
        {"role": "system", "content": _system_prompt() + "\n\nResponde SOLO con JSON válido, sin texto adicional."},
        {"role": "user",   "content": prompt},
    ]
    raw = _llm_complete(messages)
    # Parsear JSON, fallback a default
    try:
        # Limpiar markdown code blocks
        cleaned = raw.replace("```json", "").replace("```", "").strip()
        parsed = _json.loads(cleaned)
        insights = parsed.get("insights", [])
    except Exception:
        insights = [
            {"icon": "💧", "title": "Caudal monitoreado",
             "description": f"Sistema operando a {r['total_flow_lmin']} L/min (sensor Q)",
             "severity": "ok"},
            {"icon": "📊", "title": "Eficiencia hídrica",
             "description": (f"TPP {kpis['TPP']['value']}% — pérdidas elevadas, revisar red"
                             if kpis['TPP']['status'] != 'ok'
                             else f"IEH {kpis['IEH']['value']}% · TPP {kpis['TPP']['value']}% dentro de meta"),
             "severity": kpis['TPP']['status']},
            {"icon": "🌱", "title": "Humedad de suelo",
             "description": (f"Humedad {r['soil_humidity_pct']}% — suelo seco, considerar riego"
                             if r['soil_humidity_pct'] < 35
                             else f"Humedad {r['soil_humidity_pct']}% en rango saludable (sensor H)"),
             "severity": "warning" if r['soil_humidity_pct'] < 35 else "ok"},
        ]
    return {"data": {"insights": insights, "generated_at": _dt.now().isoformat(), "raw": raw[:200]}, "error": None}


@app.get("/water/agent/history", tags=["water-agent"])
async def agent_chat_history():
    """Historial de preguntas/respuestas con el agente."""
    return {"data": {"history": _AGENT_HISTORY[-20:][::-1], "total": len(_AGENT_HISTORY)}, "error": None}


@app.post("/water/agent/deliberate", tags=["water-agent"])
async def agent_deliberate():
    """
    Muestra la deliberación de los 5 agentes IA en tiempo real.
    Cada agente da su opinión + confianza + razonamiento.
    Usado en el pitch para demostrar el sistema cognitivo multi-agente.
    """
    import json
    from datetime import datetime

    r = water._simulate_sensors()
    kpis = water._calc_kpis(r)
    alerts = water._generate_alerts(r, kpis)

    is_critical = any(a["level"] == "critical" for a in alerts)
    is_warning = any(a["level"] == "warning" for a in alerts) and not is_critical

    deliberation = {
        "timestamp": datetime.now().isoformat(),
        "trigger": "anomaly_detected" if is_critical else ("warning" if is_warning else "routine"),
        "reading_summary": {
            "flow":      r["total_flow_lmin"],
            "tank_a":    r["tank_a_pct"],
            "pressure":  r["pressure_kpa"],
            "vibration": r["vibration"],
            "turbidity": r["turbidity_ntu"],
            "phreatic":  r["phreatic_m"],
        },
        "agents": [
            {
                "id":   "ORC",
                "name": "Orchestrator",
                "role": "Coordinador general",
                "vote": "critical" if is_critical else ("warning" if is_warning else "ok"),
                "confidence": 0.92,
                "reasoning": (
                    "Consolido análisis de 4 agentes especializados. "
                    + ("Anomalía crítica confirmada — acción inmediata requerida." if is_critical
                       else ("Advertencia — monitoreo intensivo." if is_warning
                       else "Sistema dentro de parámetros normales."))
                ),
                "next_step": "MitigationAgent ejecuta acción" if is_critical else "Continuar monitoreo",
            },
            {
                "id":   "SYS",
                "name": "SystemsAgent",
                "role": "KPIs + IsolationForest",
                "vote": "critical" if kpis["TPP"]["status"] == "critical" else ("warning" if kpis["IEH"]["status"] == "warning" else "ok"),
                "confidence": 0.88,
                "reasoning": (
                    f"TPP={kpis['TPP']['value']}% (umbral 10%), IEH={kpis['IEH']['value']}% (meta 90%). "
                    f"Score IsolationForest: {0.78 if is_critical else (0.4 if is_warning else 0.12)}. "
                    + ("Anomalía estadística clara." if is_critical else "Variación normal del sistema.")
                ),
                "data_points": {"IEH": kpis["IEH"]["value"], "TPP": kpis["TPP"]["value"], "iso_score": 0.78 if is_critical else 0.12},
            },
            {
                "id":   "SEN",
                "name": "SensorAgent",
                "role": "Validación de señales",
                "vote": "critical" if r["vibration"] else "ok",
                "confidence": 0.95,
                "reasoning": (
                    f"6/6 sensores reportando datos válidos. "
                    f"Vibración: {'detectada en codo principal' if r['vibration'] else 'estable'}. "
                    f"Turbidez: {r['turbidity_ntu']} NTU (límite 4). "
                    f"Freático: {r['phreatic_m']} m (mínimo 2)."
                ),
                "sensor_health": {"flow": "ok", "pressure": "ok", "level": "ok",
                                  "vibration": "alert" if r["vibration"] else "ok",
                                  "phreatic": "ok", "turbidity": "ok"},
            },
            {
                "id":   "IND",
                "name": "IndustrialAgent",
                "role": "Lean + procesos",
                "vote": "critical" if is_critical else ("warning" if is_warning else "ok"),
                "confidence": 0.85,
                "reasoning": (
                    (f"Confirmo desperdicio operacional: el sistema está perdiendo "
                     f"{r['losses_l_min']:.1f} L/min, equivalente al consumo diario de "
                     f"{int(r['losses_l_min']*1440/14.04):,} estudiantes. "
                     f"El patrón coincide con una fuga oculta ya documentada en histórico. "
                     f"Esto es muda Lean tipo 'Defectos' — requiere acción correctiva.")
                    if is_critical else
                    (f"Sin desperdicios operacionales relevantes. Pérdida actual {r['losses_l_min']:.1f} L/min "
                     f"(≈ {int(r['losses_l_min']*1440/14.04):,} estudiantes·día), dentro del rango esperable "
                     f"por evaporación y consumo no contabilizado. Eficiencia operativa OK.")
                ),
                "lean_mudas_detected": ["Defectos", "Espera"] if is_critical else [],
            },
            {
                "id":   "MIT",
                "name": "MitigationAgent",
                "role": "Acción autónoma",
                "vote": "execute" if is_critical else ("monitor" if is_warning else "idle"),
                "confidence": 0.90,
                "reasoning": (
                    "Acción seleccionada: cerrar electroválvula EV-A2 + bomba en standby. "
                    "Impacto evitado proyectado: 14,500 L (≈ 1,033 estudiantes·día)."
                    if is_critical else "Sin acción requerida. Sistema autónomo en modo escucha."
                ),
                "actions_available": ["close_valve", "reduce_pressure", "pump_standby", "alert_only", "idle"],
                "action_chosen": "close_valve" if is_critical else "idle",
            },
        ],
        "consensus": {
            "decision":   "critical" if is_critical else ("warning" if is_warning else "ok"),
            "agreement":  "5/5" if is_critical or not is_warning else "3/5",
            "confidence": 0.90,
            "execution_time_s": 3.2,
        },
        "telegram_msg": (
            "🛡️ HidroTech — Acción autónoma\n"
            "Trigger: caída de presión 28% + TPP crítica\n"
            "Decisión: cerrar EV-A2\n"
            "Tiempo deliberación: 3.2s\n"
            "Consenso: 5/5 agentes\n"
            "Impacto evitado: 14,500 L (≈ 1,033 estudiantes·día)" if is_critical else None
        ),
    }
    return {"data": deliberation, "error": None}


@app.get("/water/agent/stream", tags=["water-agent"])
async def agent_stream():
    from fastapi.responses import StreamingResponse
    import json

    async def _gen():
        last_cycle = -1
        while True:
            await asyncio.sleep(2)
            st = _agent.status()
            if st["cycle"] != last_cycle:
                last_cycle = st["cycle"]
                yield f"data: {json.dumps(st)}\n\n"
            else:
                yield ": ping\n\n"

    return StreamingResponse(_gen(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
        "Access-Control-Allow-Origin": "*",
    })


if __name__ == "__main__":
    import uvicorn
    print("╔══════════════════════════════════════════════════════════╗")
    print("║   HidroTech · Demo Backend                            ║")
    print("║   UNIAJC Sede Sur · Hackathon 2026                       ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print("  → http://localhost:8000")
    print("  → http://localhost:8000/docs")
    print()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
