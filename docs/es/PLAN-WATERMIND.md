# WaterMind OS — Plan Maestro por Fases
## Hackathon UNIAJC 2026 · Gestión del Agua Sede Sur

---

## Datos reales del sistema (fuente: Aristizábal Torres & Largacha Perdomo, 2025)

| Variable | Valor real |
|---|---|
| Caudal total aljibes | 113.56 L/min (30 gal/min) |
| Aljibe 1 profundidad | ~12 m → PTAP → Tanque A |
| Aljibe 2 profundidad | ~15 m → PTAP + derivación directa riego cancha |
| Tanque A | 4×3×3 m = 36,000 L (bomba ON a 24,000L) |
| Tanque B | 4×2×2 m = 16,000 L |
| Capacidad máx bombeo | 7,268 L/h |
| Población estudiantes | ~3,230/día (total usuarios: 8,234) |
| Consumo total diario | ~45,367 L/día |
| Aseo personal | 31,700 L/día (7,045 usos × 4.5 L) — 69.73% |
| Riego cancha | 3,000–5,000 L/día (3×/sem, cañón 94 L/min, 45 min) |
| Limpieza pasillos | 800–1,200 L/día |
| Lavado de manos | 2,300–2,800 L/día |
| Limpieza baños | 600–900 L/día |
| Limpieza aulas | 1,000–1,500 L/día |
| Cafetería | 240 L/día |
| Laboratorio química | 450 L/semana |
| Dispositivos hidráulicos | 219 total (39% sanitarios, 39% lavamanos/llaves, 22% aspersores) |
| Pérdidas estimadas | 20–30% del caudal (sin medición) |
| Nivel inicial acuífero | 5,000,000 L (modelo Vensim) |
| Escenario sostenible | 50% cooperación → sistema estable |

---

## FASE 0 — Setup (✅ COMPLETADO)
- [x] Clonar AgentOS como base (Python + TypeScript monorepo)
- [x] Router `/water` con simulador de sensores usando datos reales
- [x] KPIs IEH, TPP, CPE con fórmulas reales
- [x] Bot Telegram: `/agua`, `/estado`, `/zonas`, `/kpis`, `/reporte_agua`, `/alerta`, `/riego`, `/normal`
- [x] Dashboard SvelteKit `/agua` con KPIs, tanques, zonas, historial, costo-beneficio
- [x] Migración Supabase para series de tiempo de sensores

**PRÓXIMO: Actualizar constantes del simulador con datos exactos del PDF**

---

## FASE 1 — Datos Reales + Agente Autónomo 🤖
*Reto mínimo Sistemas: "al menos un agente que monitoree y tome decisiones autónomas"*

### 1A. Actualizar simulador con datos exactos del PDF
**Archivo:** `services/api/app/routers/water.py`

Actualizar:
- `STUDENT_POPULATION = 3_230` → ya correcto
- `TOTAL_USERS = 8_234` (incluyendo docentes y personal)
- Flujos por zona con rangos reales:
  ```python
  ZONE_DAILY_L = {
    "Aseo Personal":    {"min": 28000, "max": 34000, "share": 0.6973},
    "Riego/Cancha":     {"min": 3000,  "max": 5000,  "share": 0.0880, "intermittent": True},
    "Limpieza Pasillos":{"min": 800,   "max": 1200,  "share": 0.0220},
    "Lavado de Manos":  {"min": 2300,  "max": 2800,  "share": 0.0550},
    "Limpieza Baños":   {"min": 600,   "max": 900,   "share": 0.0165},
    "Limpieza Aulas":   {"min": 1000,  "max": 1500,  "share": 0.0275},
    "Cafetería":        {"min": 200,   "max": 280,   "share": 0.0055},
    "Laboratorios":     {"min": 50,    "max": 90,    "share": 0.0015},
  }
  ```
- Pump control real: bomba ON cuando Tanque A < 24,000L, OFF cuando lleno
- Acuífero: nivel inicial 5,000,000L, recarga natural estimada

### 1B. Agente Autónomo de Monitoreo (LangGraph)
**Archivo nuevo:** `services/api/app/routers/agent_water.py`
**Usa:** `packages/agents/agentos_agents/` + LLMFactory

```
Estado del agente (LangGraph):
  IDLE → MONITORING → ANALYZING → DECIDING → ALERTING → REPORTING → IDLE
```

**Nodos del grafo:**
1. `sensor_reader` — lee `/water/reading` cada 60s
2. `anomaly_detector` — compara contra umbrales (usa `packages/ml` IsolationForest)
3. `decision_maker` — LLM con contexto: "¿qué acción tomar?"
4. `alert_dispatcher` — llama `/notify/send` → Telegram + (opcional) email
5. `report_generator` — llama `/reports/generate` → PDF diario

**Endpoint:** `POST /water/agent/start` / `GET /water/agent/status` / `POST /water/agent/stop`

**Diagrama de estados UML (para entregable hackathon):**
```
[IDLE] --start--> [MONITORING]
[MONITORING] --reading_ok--> [ANALYZING]
[MONITORING] --error--> [IDLE]
[ANALYZING] --normal--> [MONITORING]
[ANALYZING] --anomaly_detected--> [DECIDING]
[DECIDING] --low_severity--> [ALERTING]
[DECIDING] --high_severity--> [ALERTING] + [REPORTING]
[ALERTING] --sent--> [MONITORING]
[REPORTING] --pdf_generated--> [MONITORING]
[MONITORING] --daily_trigger--> [REPORTING]
```

### 1C. System Prompt personalizado para agua
**Archivo:** `packages/agents/agentos_agents/nodes/responder.py`

El agente chat debe responder como experto en gestión hídrica de UNIAJC.
Contexto inyectado: datos del campus, KPIs actuales, historial.

---

## FASE 2 — Reto SISTEMAS (UML + Interfaces) 📐
*Entregables: arquitectura UML, interfaces UCD, diagrama de estados del agente*

### 2A. Diagrama de Arquitectura UML — Componentes
Crear diagrama (PlantUML / draw.io) con:
```
<<component>> WaterMind OS
  <<subsystem>> Frontend (SvelteKit)
    <<component>> Dashboard /agua
    <<component>> Chat IA /
  <<subsystem>> Backend (FastAPI)
    <<component>> /water/* (sensores, KPIs, simulador)
    <<component>> /water/agent/* (agente autónomo)
    <<component>> /chat/stream (LangGraph)
    <<component>> /notify/send
    <<component>> /reports/generate
  <<subsystem>> Bot Telegram
    <<component>> WaterCommands
    <<component>> AgentNotifier
  <<subsystem>> Packages (Python)
    <<component>> agentos_agents (LangGraph + CrewAI)
    <<component>> agentos_ml (IsolationForest)
    <<component>> agentos_notifications
    <<component>> agentos_reports (WeasyPrint PDF)
  <<subsystem>> Data
    <<component>> Supabase (PostgreSQL + pgvector)
    <<component>> water_readings table
    <<component>> water_alerts table
```

### 2B. Diagrama de Estados del Agente (UML StateMachine)
Ver sección 1B arriba — plasmar en PlantUML.

### 2C. Mejoras de UX en Dashboard
- Loading skeletons durante refresh
- Indicador de escenario activo (color del header)
- Botón "Exportar PDF del día" → llama `/reports/generate`
- Modo oscuro ya integrado (AgentOS lo provee)
- Responsive mobile-first
- Botón para activar/detener agente desde UI

### 2D. Página de perfil del sistema
Ruta `/agua/info` — descripción del campus, infra, datos reales. Cumple UCD (Diseño Centrado en Usuario): muestra el "por qué" al usuario final.

---

## FASE 3 — Reto ELECTRÓNICA 🔌
*Entregables: esquema de circuito, arquitectura sistema embebido, diagrama de flujo firmware*

> **Nota:** Esta fase es de documentación técnica + propuesta de hardware. No se implementa hardware real en el hackathon, pero sí se especifica con precisión.

### 3A. Esquema del circuito de sensado y acondicionamiento
**Variables a medir:**
| Variable | Sensor propuesto | Rango | Señal salida |
|---|---|---|---|
| Caudal entrada PTAP | Caudalímetro YF-S201 (efecto Hall) | 1–30 L/min | Pulsos digitales |
| Nivel Tanque A | HC-SR04 ultrasónico | 0–400 cm | PWM/Digital |
| Nivel Tanque B | HC-SR04 ultrasónico | 0–200 cm | PWM/Digital |
| Presión red | Sensor MPX5700 | 0–700 kPa | 0–5V analógico |
| Caudal zona riego | Caudalímetro DN25 | 5–150 L/min | Pulsos |

**Circuito de acondicionamiento:**
- Microcontrolador: ESP32 (WiFi + Bluetooth integrado)
- ADC: ADS1115 (16-bit, para señales analógicas de presión)
- Nivel lógico: optoacopladores para protección
- Alimentación: 5V DC regulado con backup batería 18650
- Comunicación local: UART/I2C a pantalla OLED 128×64
- Comunicación remota: WiFi → MQTT → Backend FastAPI

### 3B. Arquitectura sistema embebido
```
┌─────────────────────────────────────────────┐
│           ESP32 — WaterMind Node              │
│                                              │
│  ┌────────────┐   ┌────────────────────────┐ │
│  │  SENSADO   │   │      PROCESAMIENTO     │ │
│  │ YF-S201    │──▶│  Interrupción pulsos   │ │
│  │ HC-SR04 ×2 │──▶│  Filtro promedio móvil │ │
│  │ MPX5700    │──▶│  Detección umbral      │ │
│  └────────────┘   └───────────┬────────────┘ │
│                               │              │
│  ┌────────────┐   ┌───────────▼────────────┐ │
│  │ALIMENTACIÓN│   │     COMUNICACIÓN       │ │
│  │ 5V DC reg. │   │  WiFi → MQTT Broker    │ │
│  │ Battery BU │   │  Display OLED local    │ │
│  └────────────┘   └───────────┬────────────┘ │
└───────────────────────────────┼─────────────┘
                                │ MQTT/HTTP
                    ┌───────────▼────────────┐
                    │   Backend FastAPI       │
                    │   POST /water/ingest    │
                    └────────────────────────┘
```

### 3C. Diagrama de flujo del firmware (embebido)
```
INIT → Config WiFi → Connect MQTT
  ↓
LOOP cada 5s:
  ├── Leer caudalímetro (contar pulsos interrupciones)
  ├── Leer ultrasonidos (trigger → echo → distancia)
  ├── Leer presión (ADC ADS1115)
  ├── Calcular L/min, nivel%, presión kPa
  ├── Comparar vs umbrales locales
  │    ├── Si anomalía → LED rojo + buzzer
  │    └── Normal → LED verde
  ├── Mostrar en OLED: caudal, niveles
  └── Publicar MQTT: {sensor_id, timestamp, readings}
        ↓
    FastAPI /water/ingest → guarda en Supabase
```

---

## FASE 4 — Reto INDUSTRIAL 🏭
*Entregables: diagrama de proceso, KPIs con fórmula, Lean+Ishikawa, costo-beneficio*

### 4A. Diagrama de proceso completo (PTAP Sede Sur)
Basado exactamente en el PDF de Aristizábal/Largacha (2025):

```
[Cuenca Río Pance]
      │
      ▼
[Aljibe 1 ~12m]──────────────[Aljibe 2 ~15m]
      │                              │
      │ 113.56 L/min total           │─────────────────────┐
      ▼                              │                     │
[Filtro 1: Grava+Arena]             │               [Riego Cancha]
[Filtro 2: +Antracita  ]◀───────────┘          (3x/sem, 45min, 94L/min)
[Filtro 3: +C. Activado]                       SIN TRATAMIENTO
      │
      ▼
[Tanque A: 36,000L]──[Bomba: ON@24kL, OFF@lleno]
      │                   capacidad: 7,268 L/h
      ▼
[Tanque B: 16,000L]
      │
      ├──▶ Baños Bloque A + Alameda  (~31,700 L/día · 69.73%)
      ├──▶ Riego zonas verdes         (~3,000-5,000 L/día)
      ├──▶ Limpieza institucional     (~2,600 L/día)
      ├──▶ Cafetería                  (~240 L/día)
      └──▶ Laboratorios               (~64 L/día)

Total: ~45,367 L/día · Pérdidas estimadas: 20-30%
```

### 4B. KPIs con fórmula y propósito
**KPI 1 — IEH: Índice de Eficiencia Hídrica**
- Fórmula: `IEH = (Qentrada − Qpérdidas) / Qentrada × 100`
- Unidad: % | Meta: > 90% | Actual estimado: ~70-80%
- Propósito: mide qué porción del agua captada llega efectivamente a los usuarios

**KPI 2 — TPP: Tasa de Pérdidas del Proceso**
- Fórmula: `TPP = Qno_contabilizado / Qentrada × 100`
- Unidad: % | Meta: < 10% | Actual: ~20-30% (sin medición)
- Propósito: identifica ineficiencias de distribución y fugas no detectadas

**KPI 3 — CPE: Consumo Per Estudiante**
- Fórmula: `CPE = Consumo_total_diario / N°_estudiantes_activos`
- Unidad: L/est/día | Referencia: 14.04 L/est/día (Arias Montoya et al., 2024)
- Propósito: benchmark de eficiencia hídrica per cápita vs. otras IES

### 4C. Lean Manufacturing — Identificación de desperdicios (Mudas)
**Desde perspectiva Lean:**

| Muda (Desperdicio) | Manifestación en UNIAJC |
|---|---|
| **Sobreproducción** | Bombeo excesivo sin demanda real (tanques llenos pero bomba activa) |
| **Espera** | Tiempo entre detección de fuga y reparación (sin sistema de alertas) |
| **Transporte** | Agua no contabilizada en tramos sin medición entre tanques y puntos de uso |
| **Procesamiento excesivo** | Agua tratada usada para riego (Aljibe 2 ya lo evita parcialmente) |
| **Inventario** | Sobrenllenado de tanques → presión excesiva → aumento de fugas |
| **Movimiento** | Personal de mantenimiento revisando niveles manualmente sin automatización |
| **Defectos** | Agua tratada con pérdidas por fugas no detectadas (20-30% estimado) |

**Diagrama de Ishikawa (causa-raíz del problema principal):**
```
                      EFECTO: Pérdidas de agua 20-30% sin detectar
                                    │
        ┌───────────────────────────┼──────────────────────────┐
        │                           │                          │
   MEDICIÓN                    INFRAESTRUCTURA             COMPORTAMIENTO
        │                           │                          │
  Sin caudalímetros          Red sin sectorizár         Sin cultura ahorro
  Sin sensores nivel         Tuberías antiguas          Riego sin horario
  Sin SCADA/IoT              Sin mantenimiento          Grifos abiertos
  Datos manuales             preventivo                 Sin señalética
        │                           │                          │
   GESTIÓN                     PROCESOS                   FORMACIÓN
        │                           │                          │
  Sin KPIs definidos          Sin SOP escrito           Sin capacitación
  Sin alertas automáticas     Riego sin protocolo       Sin métricas
  Sin reporting               Sin inventario            Sin incentivos
```

### 4D. Propuesta de mejora operativa (mínimo 2 acciones)
**Acción 1: Instalación de caudalímetros + sensores de nivel (IoT)**
- Qué: 3 caudalímetros YF-S201/DN25 + 2 ultrasonidos HC-SR04 + 1 ESP32
- Costo: $4,500,000 COP (estimado)
- Impacto: detección de fugas en tiempo real, medición exacta por zona
- Reducción esperada: 15-20% del consumo actual

**Acción 2: Sistema de riego automatizado con horario**
- Qué: Válvulas solenoides + controlador + programación fuera de pico
- Costo: $2,800,000 COP
- Impacto: reducir consumo de riego de 3,000-5,000 a 1,500-2,500 L/día
- Ahorro: ~1,500 L/día × 365 = 547,500 L/año

### 4E. Análisis Costo-Beneficio
| Concepto | Valor |
|---|---|
| Pérdida diaria estimada (20%) | 9,073 L/día |
| Costo agua Cali (EMCALI) | ~$3,500 COP/m³ |
| Pérdida económica diaria | ~$31,755 COP/día |
| Pérdida económica anual | ~$11,591,000 COP/año |
| **Inversión total sensores+automatización** | **$7,300,000 COP** |
| Ahorro anual proyectado (15% reducción) | ~$5,800,000 COP/año |
| **Tiempo recuperación inversión** | **~15 meses** |

---

## FASE 5 — Integración Final + Demo 🎯
*Objetivo: demo fluido de 5 minutos para el pitch*

### 5A. Script del demo (flujo recomendado)
```
1. [0:00] Abrir dashboard /agua → mostrar KPIs en verde (escenario normal)
   "Este es WaterMind OS, sistema inteligente de gestión hídrica para UNIAJC"

2. [0:45] Clic en "Fuga" → KPIs cambian a rojo, alertas aparecen
   "Detectamos anomalía — el agente ya tomó acción"

3. [1:15] Abrir Telegram → mostrar notificación automática recibida
   "/estado" → ver resumen
   "El bot ya notificó al operador de mantenimiento"

4. [1:45] Volver a dashboard → tab "Costo-Beneficio"
   "Con $7.3M COP recuperamos la inversión en 15 meses"

5. [2:30] Mostrar chat IA en /
   Escribir: "¿Cuánta agua pierde la uni por mes?"
   → agente responde con datos reales del campus

6. [3:15] Mostrar tab "Historial" → gráfica de últimas 24h
   "Datos en tiempo real, auto-actualización cada 30s"

7. [4:00] Mostrar diagrama UML de arquitectura
   "Agnete autónomo con LangGraph, 4 estados, toma decisiones sin intervención humana"

8. [4:30] Q&A
```

### 5B. Deploy en vivo (para el día del hackathon)
- Backend: `uvicorn app.main:app --reload` en localhost:8000
- Frontend: `pnpm dev:svelte` → localhost:5173
- Bot: `python bot.py` (con TELEGRAM_BOT_TOKEN en .env)
- Alternativamente: deploy en Vercel (frontend) + Koyeb (backend) usando GitHub Actions

### 5C. .env mínimo para demo
```env
ENVIRONMENT=development
GROQ_API_KEY=gsk_...         # Gratis en console.groq.com
TELEGRAM_BOT_TOKEN=...       # @BotFather en Telegram
TELEGRAM_CHAT_IDS=...        # Tu chat_id para notificaciones
BACKEND_URL=http://localhost:8000
# Supabase es opcional para la demo (usa FAISS en memoria)
```

---

## Resumen de entregas del hackathon cubiertos

| Reto | Entregable | Fase | Estado |
|---|---|---|---|
| **Sistemas** | Arquitectura UML (componentes) | 2A | 📋 Por hacer |
| **Sistemas** | Diagrama estados agente (UML) | 1B + 2B | 📋 Por hacer |
| **Sistemas** | Interfaces UCD | 0 + 2C | ✅ Dashboard hecho |
| **Sistemas** | Agente autónomo (alertas, reportes) | 1B | 📋 Por hacer |
| **Electrónica** | Circuito de sensado | 3A | 📋 Por hacer |
| **Electrónica** | Comunicación local/remota | 3A + 3B | 📋 Por hacer |
| **Electrónica** | Arquitectura sistema embebido | 3B | 📋 Por hacer |
| **Electrónica** | Diagrama flujo firmware | 3C | 📋 Por hacer |
| **Industrial** | Diagrama de proceso completo | 4A | 📋 Por hacer |
| **Industrial** | Variables clave (caudal, demanda, pérdidas) | 4A | ✅ En water.py |
| **Industrial** | 3 KPIs con fórmula y propósito | 4B | ✅ IEH, TPP, CPE |
| **Industrial** | Lean Manufacturing (mudas) | 4C | 📋 Por hacer |
| **Industrial** | Diagrama Ishikawa | 4C | 📋 Por hacer |
| **Industrial** | ≥2 acciones de mejora + impacto | 4D | 📋 Por hacer |
| **Industrial** | Análisis costo-beneficio + ROI | 4E | ✅ En dashboard |

---

## Orden de ejecución recomendado (hackathon en vivo)

```
HORA 0-1:   Fase 0 (setup) + Fase 1A (actualizar datos reales) ← AHORA
HORA 1-3:   Fase 1B (agente autónomo LangGraph)
HORA 3-4:   Fase 2A+2B (diagramas UML — draw.io)
HORA 4-5:   Fase 2C+2D (mejoras dashboard + página info)
HORA 5-7:   Fase 3A+3B+3C (documentación electrónica)
HORA 7-9:   Fase 4A+4B (diagrama proceso + KPIs docs)
HORA 9-11:  Fase 4C+4D+4E (Lean, Ishikawa, costo-beneficio)
HORA 11-12: Fase 5 (ensayo demo, deploy, ajustes)
```
