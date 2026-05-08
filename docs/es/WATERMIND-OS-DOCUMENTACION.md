#  Camaleón OS

## Sistema Inteligente de Gestión Hídrica para UNIAJC Sede Sur

**"Tecnologías con Propósito · Inteligencia con Conciencia"**

> Hackathon UNIAJC 2026 · Facultad de Ingeniería · Cali, Colombia
> Fecha de entrega: 8 de mayo 2026 · 5:00 PM
> Repositorio: [github.com/JFrangel/Camaleón-OS](https://github.com/JFrangel/Camaleón-OS)

---

## 1. ¿De qué se trata Camaleón OS?

Camaleón OS es un **sistema inteligente** que mide, analiza y optimiza el consumo de agua del campus UNIAJC Sede Sur en tiempo real. Combina **sensores físicos (IoT)**, **agentes de inteligencia artificial autónomos**, un **dashboard web moderno** y un **bot de Telegram** que envía alertas automáticas cuando algo no está funcionando bien.

En lugar de seguir perdiendo entre el 20% y 30% del agua sin saber dónde ni por qué, Camaleón OS **detecta fugas en menos de 5 minutos**, **alerta automáticamente** al personal de mantenimiento y **toma decisiones por sí solo** (como cerrar válvulas, reducir riego, generar reportes) sin necesidad de supervisión humana constante.

### En una frase

> *"Camaleón OS convierte cada gota de agua del campus en un dato medible, decidible y ahorrable."*

---

## 2. ¿Qué problema resuelve?

La PTAP (Planta de Tratamiento de Agua Potable) de UNIAJC Sede Sur fue instalada en **2011** y desde entonces ha funcionado **sin ningún sistema de medición**. Esto significa:

| Problema | Consecuencia |
|----------|-------------|
|  No hay caudalímetros | No se sabe cuánta agua entra ni sale del sistema |
|  No hay sensores de nivel | No se sabe cuándo los tanques están llenos o vacíos |
|  No hay detección de fugas | Las pérdidas se descubren días o semanas después |
|  No hay KPIs definidos | No se puede medir si el sistema mejora o empeora |
|  No hay alertas automáticas | El personal debe inspeccionar manualmente |
|  No hay datos históricos | Imposible identificar patrones o tendencias |

### Datos del problema (fuentes: tesis UNIAJC 2024-2025)

- **45,367 L/día** se consumen en el campus
- **3,230 estudiantes** activos por día (8,234 usuarios totales)
- **113.56 L/min** entran desde los aljibes
- **20-30% de pérdidas estimadas** = $19.3 millones COP/año desperdiciados
- **219 dispositivos hidráulicos** sin instrumentación
- **2 tanques** (36,000 L + 16,000 L) sin sensores de nivel

---

## 3. ¿Qué hace Camaleón OS de novedoso?

Camaleón OS es la **primera solución multidisciplinar** que combina **IoT + IA agéntica + dashboard + Telegram** para gestión hídrica universitaria en Colombia. Estos son sus 5 elementos novedosos:

###  Multi-agente IA con LangGraph

No es un chatbot. Son **4 agentes que trabajan juntos** y toman decisiones autónomas:

| Agente | Rol | Decide sobre |
|--------|-----|--------------|
| **Orchestrator** | Coordinador general | Cuándo alertar, cuándo reportar |
| **SystemsAgent** | Especialista en software | KPIs (IEH, TPP, CPE), anomalías estadísticas |
| **SensorAgent** | Especialista electrónico | Calidad de señales, sensores fuera de rango |
| **IndustrialAgent** | Especialista de procesos | Mudas Lean, costos, ODS |

Los agentes ejecutan **ciclos cada 30 segundos** y toman decisiones sin intervención humana: "este TPP está al 25%, hay vibración anómala → notificar Telegram + cerrar sección + generar reporte".

###  6 sensores con costo bajo (~$1M COP)

A diferencia de soluciones SCADA industriales que cuestan $50M+ COP, Camaleón OS usa sensores accesibles que cualquier estudiante de ingeniería entiende:

1. **Caudal** YF-S201 (efecto Hall) — $25K COP
2. **Presión** MPX5700AP — $45K COP
3. **Nivel tanque** JSN-SR04T (ultrasónico impermeable) — $30K COP
4. **Vibración tuberías** SW-420 — $10K COP
5. **Nivel freático** transductor 4-20mA — $180K COP
6. **Turbidez** TSD-10 (calidad agua) — $55K COP

Todos conectados a un **ESP32** ($35K COP) que envía datos por WiFi.

###  Telegram como interfaz oficial

En lugar de pedirle al personal que aprenda otro software, Camaleón OS usa **Telegram** (que todos ya tienen). Los administradores reciben:

- Alertas automáticas cuando hay fugas
- Reportes diarios a las 6:00 PM
- Comandos rápidos: `/agua`, `/zonas`, `/kpis`

###  Dashboard moderno y minimalista

Estilo *dark mode* tipo Linear/Vercel — diseño limpio, datos a primera vista, 4 pestañas:

1. **Dashboard** — KPIs + tanques + sensores en tiempo real
2. **Historial** — gráficas 24h + tabla detallada
3. **Industrial** — KPIs con fórmulas + análisis Lean + costo-beneficio
4. **Agente IA** — control del agente + log de decisiones en vivo

###  Modelo replicable y escalable

Funciona en UNIAJC Sede Sur, pero **el mismo sistema** puede instalarse en cualquier universidad o institución con problemas similares. Todo el código es **open source**.

---

## 4. Arquitectura — ¿Cómo funciona técnicamente?

```
┌─────────────────────────────────────────────────────────────────────┐
│  CAMPUS UNIAJC SEDE SUR  │
│  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Aljibe 1 │  │ Aljibe 2 │  │ Tanques  │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│  │  │  │  │
│  ▼  ▼  ▼  │
│  [YF-S201]  [YF-S201]  [JSN-SR04T ×2]  │
│  [MPX5700]  [4-20mA]  [SW-420]  │
│  [TSD-10]  [Vibración]  │
│  │  │  │  │
│  └──────────────┴────────────────┘  │
│  │  │
│  ┌────────▼────────┐  │
│  │  ESP32  │  ← Microcontrolador WiFi  │
│  │  (firmware)  │  procesa señales,  │
│  └────────┬────────┘  publica MQTT cada 30s  │
└────────────────────── │ ──────────────────────────────────────────── │
  │ WiFi 2.4 GHz
  ▼
  ┌─────────┐
  │  HiveMQ  │  ← Broker MQTT en la nube (gratis)
  │  Cloud  │
  └────┬─────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  CAMALEON OS — Backend (Python)  │
│  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  FastAPI · /water/* + /water/agent/*  │  │
│  │  • POST /water/ingest  ← recibe datos del ESP32  │  │
│  │  • GET  /water/reading ← simulador para demo  │  │
│  │  • POST /water/agent/start ← arranca agente autónomo  │  │
│  │  • GET  /water/agent/stream ← SSE en tiempo real  │  │
│  └──────────────────────┬───────────────────────────────────────┘  │
│  │  │
│  ┌──────────────────────▼───────────────────────────────────────┐  │
│  │  SISTEMA MULTI-AGENTE (LangGraph)  │  │
│  │  │  │
│  │  [WaterOrchestratorAgent]  │  │
│  │  │  │  │
│  │  ┌────────────┼────────────┐  │  │
│  │  ▼  ▼  ▼  │  │
│  │  Systems  Sensor  Industrial  │  │
│  │  Agent  Agent  Agent  │  │
│  │  (KPIs)  (Señales)  (Lean+Costos)  │  │
│  └──────────────────────┬───────────────────────────────────────┘  │
│  │  │
└────────────────────────  │  ──────────────────────────────────────── │
  ┌───────────┴───────────┐
  ▼  ▼
  ┌─────────────────┐  ┌──────────────────┐
  │  Supabase DB  │  │  Telegram Bot  │
  │  • lecturas  │  │  • alertas push  │
  │  • alertas  │  │  • /comandos  │
  │  • KPIs  │  │  • reporte 18:00 │
  └─────────────────┘  └──────────────────┘
  │
  ▼
  ┌─────────────────────────────┐
  │  Dashboard SvelteKit /agua  │
  │  • Dashboard  │
  │  • Historial  │
  │  • Industrial  │
  │  • Agente IA  │
  └─────────────────────────────┘
```

### Stack técnico

| Capa | Tecnología | ¿Por qué? |
|------|-----------|-----------|
| **Sensores** | ESP32 + 6 sensores | Bajo costo, comunidad enorme, WiFi integrado |
| **Comunicación** | MQTT vía HiveMQ | Estándar IoT, gratis, latencia <100ms |
| **Backend** | FastAPI (Python) | Documentación auto, validación Pydantic, async |
| **Agentes IA** | LangGraph + CrewAI | Multi-agente, estados, decisiones autónomas |
| **Modelos LLM** | Cascada Groq→OpenRouter→Gemini | Failover automático, $0 USD en pruebas |
| **Base de datos** | Supabase PostgreSQL | Gratis, auth, realtime, ya usado en AgentOS |
| **Frontend** | SvelteKit + Tailwind | Reactivo, ligero, tema dark moderno |
| **Bot** | python-telegram-bot | Estándar, fácil despliegue |
| **Reportes PDF** | WeasyPrint + Jinja2 | HTML→PDF profesional |

---

## 5. Reto Sistemas — ¿Qué entregamos? (30 pts)

### 5.1 Arquitectura UML

Diagrama de componentes mostrando los 8 módulos: ESP32, MQTT, FastAPI, LangGraph (4 agentes), Supabase, Telegram, SvelteKit y los actores (Personal mantenimiento, Administrador, Estudiantes).

### 5.2 Interfaces con Diseño Centrado en Usuario (UCD)

**Dashboard web** y **Bot Telegram** siguen 5 principios UCD:

1. **Visibilidad del estado** — KPIs siempre visibles arriba
2. **Feedback inmediato** — alertas en rojo/amarillo cuando hay anomalías
3. **Prevención de errores** — confirmación antes de cambiar escenarios
4. **Accesibilidad** — colores semafóricos + texto explicativo
5. **Consistencia** — mismo lenguaje en Telegram y dashboard

### 5.3 Agente Autónomo

**WaterMonitorAgent** orquesta a 4 sub-agentes y toma **decisiones autónomas**:

```
[IDLE] ──30s──▶ [MONITORING] ──▶ [ANALYZING] ──▶ [DECIDING]
  │
  ┌──── ok ────┐  ┌── alert ──┐  ┌── critical ──┐
  ▼  ▼  ▼  ▼  ▼  ▼
  [IDLE]  [ALERTING]  [REPORTING + ALERTING]
  │  │
  ▼  ▼
  Telegram  PDF + Telegram
```

**Ejemplos de decisiones autónomas reales que toma:**

- "TPP supera el 20% → enviar alerta crítica + activar protocolo fuga"
- "Tanque A bajo 33% → notificar bomba activa, programar revisión"
- "Hora 18:00 → generar reporte diario + enviar PDF por Telegram"
- "Turbidez > 4 NTU → suspender distribución + alertar PTAP"

---

## 6. Reto Electrónica — ¿Qué entregamos? (30 pts)

### 6.1 Los 6 sensores que medimos

| # | Variable | Sensor | Ubicación | Rango |
|---|----------|--------|-----------|-------|
| 1 | **Caudal** | YF-S201 | Salida aljibes 1 y 2 | 1–30 L/min |
| 2 | **Presión** | MPX5700AP | Red de distribución | 0–700 kPa |
| 3 | **Nivel tanque** | JSN-SR04T | Tapa tanques A y B | 0–450 cm |
| 4 | **Vibración tuberías** | SW-420 | Codos y uniones | Digital ON/OFF |
| 5 | **Nivel freático** | Transductor 4-20mA | Fondo aljibes | 0–10 m WC |
| 6 | **Turbidez** | TSD-10 | Salida filtros | 0–10 NTU |

### 6.2 Circuito de acondicionamiento

Cada sensor pasa por un circuito que adapta su señal al ESP32:

- **YF-S201** (5V) → divisor resistivo → 3.3V GPIO
- **JSN-SR04T** → divisor resistivo en ECHO → 3.3V GPIO
- **MPX5700AP** → ADS1115 (ADC 16-bit I2C) → ESP32
- **SW-420** → directo GPIO 3.3V tolerante
- **4-20mA** → resistencia shunt 150Ω → ADS1115
- **TSD-10** → divisor 4.5V→3.3V → ADS1115

### 6.3 Arquitectura embebida

Los 4 módulos del sistema embebido:

| Módulo | Función |
|--------|---------|
| **Sensado** | 6 sensores + ADS1115 + acondicionamiento |
| **Procesamiento** | ESP32 dual-core: Core 0 lee, Core 1 procesa |
| **Comunicación** | Local: OLED + LED RGB + Buzzer · Remota: WiFi + MQTT |
| **Alimentación** | 220V→5V (HLK-PM01) + Batería 18650 backup |

### 6.4 Firmware (MicroPython)

Sin Arduino IDE — todo en **MicroPython** sobre ESP32. El firmware ejecuta:

```python
# Cada 1 segundo (Core 0):
# - lee los 6 sensores
# - aplica filtro media móvil (N=10)

# Cada 30 segundos (Core 1):
# - calcula promedios
# - evalúa umbrales locales
# - actualiza OLED + LED RGB
# - publica MQTT a HiveMQ
# - si sin internet: guarda en flash NVS
```

---

## 7. Reto Industrial — ¿Qué entregamos? (30 pts + bonificación)

### 7.1 Los 3 KPIs principales

#### IEH — Índice de Eficiencia Hídrica
$$\text{IEH (\%)} = \frac{Q_{entrada} - Q_{pérdidas}}{Q_{entrada}} \times 100$$

| Estado | Valor | Color |
|--------|-------|-------|
| Crítico | < 75% |  Rojo |
| Advertencia | 75-89% |  Amarillo |
| Óptimo | ≥ 90% |  Verde |

**Actual UNIAJC: ~75% · Meta con Camaleón: > 90%**

#### TPP — Tasa de Pérdidas del Proceso
$$\text{TPP (\%)} = \frac{Q_{pérdidas}}{Q_{entrada}} \times 100$$

| Estado | Valor |
|--------|-------|
| Crítico | > 20% |
| Advertencia | 10-20% |
| Óptimo | < 10% |

**Actual UNIAJC: ~25% · Meta: < 10%**

#### CPE — Consumo Per Estudiante
$$\text{CPE (L/est/día)} = \frac{\text{Consumo diario}}{\text{Estudiantes activos}}$$

**Actual: 14.04 L/est/día (línea base) · Meta: ≤ 12.0 L/est/día**

### 7.2 Análisis Lean — 7 Mudas

| # | Muda | Manifestación | Solución Camaleón |
|---|------|--------------|-------------------|
| 1 | Defectos | Fugas no detectadas | Sensores + IsolationForest |
| 2 | Sobreproducción | Bombeo sin demanda | Activación automática por nivel |
| 3 | Espera | Detección manual tarda días | Ciclos de 30s del agente |
| 4 | Inventario | Tanques sin medición | JSN-SR04T en cada tanque |
| 5 | Movimiento | Personal inspecciona físicamente | Dashboard remoto |
| 6 | Transporte | Agua tratada para riego | Aljibe 2 directo + sensor |
| 7 | Talento | Datos sin uso para decidir | Multi-agente IA |

### 7.3 Diagrama Ishikawa — Causa raíz "Pérdidas 20-30%"

5 categorías: **Medición**, **Infraestructura**, **Personas**, **Procesos**, **Gestión**.

Causa principal: **falta de instrumentación** desde 2011 → cascada de problemas.

### 7.4 2 Acciones de mejora concretas

**Acción 1 — Instrumentación IoT con Camaleón Node**
- Inversión: $1,043,000 COP (hardware + instalación)
- Impacto: TPP de 25% → 10% (reduce pérdidas un 60%)
- Mudas eliminadas: Defectos + Espera

**Acción 2 — Automatización del riego con válvulas solenoides**
- Inversión: $2,800,000 COP
- Impacto: Riego de 4,000 → 2,200 L/día (-45%)
- Mudas eliminadas: Sobreproducción + Transporte

---

## 8. Costo-Beneficio — ¿Cuánto cuesta? ¿Cuánto ahorra?

###  Pérdidas actuales

| Concepto | Valor |
|----------|-------|
| Pérdidas físicas diarias | 15,122 L/día |
| Costo agua EMCALI industrial | $3,500 COP/m³ |
| **Pérdida económica diaria** | **$52,920 COP** |
| **Pérdida económica anual** | **$19,315,800 COP** |
| Pérdida en 5 años (sin acción) | $96,579,000 COP |

###  Inversión Camaleón OS

| Concepto | Valor |
|----------|-------|
| Hardware (ESP32 + 6 sensores) | $693,000 COP |
| Instalación + puesta en marcha | $350,000 COP |
| Software (open source) | $0 COP |
| **TOTAL INVERSIÓN** | **$1,043,000 COP** (~$250 USD) |

###  Ahorros proyectados anuales

| Concepto | Ahorro/año |
|----------|------------|
| Reducción pérdidas físicas (25%→10%) | $11,586,925 |
| Optimización riego automatizado | $2,299,500 |
| Mantenimiento preventivo vs. correctivo | $4,250,000 |
| **TOTAL AHORRO ANUAL** | **$18,136,425 COP** |

###  Indicadores financieros

| Indicador | Valor |
|-----------|-------|
| Período de recuperación | **~21 días** |
| VPN a 5 años (tasa 12%) | **$65,369,000 COP** |
| TIR | **> 1,000% anual** |
| Ratio Beneficio/Costo | **17.4** (muy alto) |
| Agua recuperada en 5 años | 16,558,625 L |
| CO₂ evitado | ~2.3 ton/año |

> **Cada peso invertido en Camaleón OS regresa $17.40 en ahorros.**

---

## 9. Alineación con Objetivos de Desarrollo Sostenible (ODS)

| ODS | ¿Cómo lo aporta Camaleón? |
|-----|---------------------------|
| **ODS 6** — Agua limpia | Reduce pérdidas del 25% al 10%, monitorea calidad |
| **ODS 4** — Educación de calidad | Modelo educativo de sostenibilidad para ingeniería |
| **ODS 9** — Industria e innovación | IoT + IA aplicado con inversión mínima |
| **ODS 11** — Ciudades sostenibles | Modelo replicable a otras universidades |
| **ODS 13** — Acción climática | Reduce huella de carbono (~2.3 ton CO₂/año) |

---

## 10. Roles del equipo — ¿Quién hace qué?

###  Equipo Camaleón OS

| Carrera | Responsabilidad | Entregables |
|---------|----------------|-------------|
| **Sistemas** | Backend, agentes IA, dashboard, bot | FastAPI, LangGraph, SvelteKit, Telegram |
| **Electrónica** | Sensores, ESP32, circuito, firmware | Esquemático, MicroPython, MQTT |
| **Industrial** | Análisis proceso, KPIs, Lean, costos | Diagramas, KPIs, Ishikawa, ROI |

###  Tareas concretas por carrera

####  Equipo Sistemas
- [x] FastAPI con endpoints `/water/*`
- [x] Simulador de los 6 sensores con datos reales
- [x] Sistema multi-agente LangGraph (4 agentes)
- [x] Endpoints del agente (`/water/agent/start`, `/stop`, `/status`, `/stream`)
- [x] Endpoint `/water/ingest` para datos del ESP32
- [x] Dashboard SvelteKit con 4 tabs
- [x] Bot Telegram con 10 comandos
- [x] Diagrama UML de componentes
- [x] Diagrama UML de estados del agente

####  Equipo Electrónica
- [ ] Esquemático del circuito (draw.io / KiCad)
- [ ] Tabla de sensores con modelo, rango, costo
- [ ] Circuito de acondicionamiento de cada sensor
- [ ] Diagrama de comunicación local + remota
- [ ] Firmware MicroPython
- [ ] Diagrama de flujo del firmware
- [ ] Arquitectura embebida (4 módulos)

####  Equipo Industrial
- [x] Diagrama de proceso PTAP completo
- [x] Identificación de variables clave
- [x] 3 KPIs con fórmulas y propósito
- [x] Tabla de 7 mudas Lean
- [x] Diagrama Ishikawa
- [x] 2 acciones de mejora concretas
- [x] Análisis costo-beneficio con ROI
- [x] Alineación con ODS

---

## 11. Demo en vivo — Pitch de 5 minutos

### Estructura del pitch

| Tiempo | Sección | Qué decir |
|--------|---------|-----------|
| 0:00–0:45 | **Problema** | "La PTAP de UNIAJC instalada en 2011 nunca tuvo medición. Pierde el 25% del agua = $19 millones COP/año desperdiciados." |
| 0:45–1:30 | **Solución** | "Camaleón OS: 6 sensores + 4 agentes IA + Telegram + dashboard. Por solo $1 millón COP." |
| 1:30–2:30 | **Demo en vivo** | Abrir dashboard → inyectar fuga → ver alerta en Telegram aparecer automáticamente |
| 2:30–3:15 | **Técnica** | Mostrar UML componentes (30s) + circuito ESP32 (30s) + diagrama Ishikawa (15s) |
| 3:15–4:00 | **Industrial** | "TPP de 25% a 10%. ROI en 21 días. TIR > 1,000%." |
| 4:00–4:45 | **Impacto** | "5 ODS impactados. 2.3 ton CO₂ evitadas. Modelo replicable." |
| 4:45–5:00 | **Cierre** | "Camaleón OS: cada gota cuenta cuando los datos hablan." |

### Lo que el jurado debe ver

 **App corriendo en vivo** (no PowerPoint, app real)
 **Números concretos** (45,367 L/día · $19M/año · 21 días ROI)
 **Los 3 retos cubiertos** (Sistemas + Electrónica + Industrial mencionados explícitamente)
 **Interdisciplinaridad evidente** en cada parte de la presentación
 **Novedad** — agente IA autónomo + Telegram = diferenciador clave

---

## 12. Posibles preguntas del jurado y cómo responder

###  "¿Por qué usar IA si esto se puede hacer con Python básico?"

> "Los umbrales fijos detectan problemas conocidos. La IA detecta **patrones que no sabíamos buscar**. Por ejemplo, una combinación de presión baja + caudal alto + vibración sugiere una fuga, pero ningún umbral simple lo dice. El agente correlaciona variables y aprende del histórico."

###  "¿Qué pasa si se cae el internet?"

> "El ESP32 tiene un OLED + LED RGB + buzzer locales que muestran el estado sin internet. Los datos se guardan en flash NVS y se reenvían cuando vuelve la conexión. La pantalla local sigue mostrando: caudal, niveles y estado del sistema."

###  "¿Es realmente escalable?"

> "Sí. El sistema está diseñado en módulos independientes:
> - Cada **Camaleón Node** (ESP32 + sensores) es autónomo
> - Se pueden añadir N nodos al mismo dashboard
> - El backend es FastAPI (deploy en Koyeb/Railway gratis)
> - Para otras sedes UNIAJC: solo cambiar configuración"

###  "¿Qué hace especial al agente IA?"

> "No es un chatbot, es un **sistema multi-agente LangGraph** con 4 agentes especializados que toman decisiones autónomas: cuándo alertar, cuándo cerrar válvula, cuándo generar reporte. Es como tener 4 ingenieros trabajando 24/7 sin descanso."

###  "¿Cómo validan que los KPIs son correctos?"

> "Los KPIs IEH, TPP y CPE están basados en estándares de la industria (ICONTEC GTC 24, OMS, Aguas de Barrancabermeja 2017). Las fórmulas son auditables y la línea base CPE 14.04 L/est/día viene de la tesis Arias Montoya et al. (2024) UNIAJC."

###  "¿Y la calidad del agua, no solo cantidad?"

> "Por eso incluimos el sensor de **turbidez TSD-10** y el **KPI ICA** (Índice de Calidad del Agua). Si la turbidez supera 4 NTU, el agente automáticamente:
> 1. Alerta crítica por Telegram
> 2. Sugiere suspender distribución
> 3. Programa mantenimiento de filtros"

###  "¿No puede manipularse el sistema?"

> "El ESP32 publica vía MQTT con autenticación TLS. El backend valida cada dato (rangos físicos imposibles → rechazo). El agente Sensor detecta sensores fuera de rango (puede indicar manipulación)."

###  "¿Cuánto demora el despliegue real?"

> "Estimado: 2-3 semanas
> - Semana 1: armar 1 nodo prototipo (ESP32 + 6 sensores)
> - Semana 2: instalar en PTAP + validar lecturas
> - Semana 3: capacitar al personal de mantenimiento UNIAJC"

###  "¿Y después del hackathon?"

> "Tres pasos:
> 1. **Piloto** — instalar 1 Camaleón Node en la PTAP (1 mes)
> 2. **Expansión** — 5 nodos cubriendo zonas críticas (3 meses)
> 3. **Replicación** — otras sedes UNIAJC y publicación open source"

---

## 13. Referencias bibliográficas

- **Aristizábal Torres, H. W., & Largacha Perdomo, S. (2025).** *Desarrollo de un modelo de dinámica de sistemas para simular la demanda y el suministro de agua en la Institución Universitaria Antonio José Camacho, Sede Sur.*
  [repositorio.uniajc.edu.co/handle/uniajc/3000](https://repositorio.uniajc.edu.co/handle/uniajc/3000)

- **Arias Montoya, Y. D., Montiel Angel, R. E., & Osorio Hernández, C. A. (2024).** *Diseño de un sistema de ahorro para el mejoramiento de la eficiencia del servicio suministrado por la planta de tratamiento de agua potable (PTAP) en la Institución Universitaria Antonio José Camacho Sede Sur.*
  [repositorio.uniajc.edu.co/handle/uniajc/2576](https://repositorio.uniajc.edu.co/handle/uniajc/2576)

- **Mosquera Zapata, L. L., & Lozano Beltrán, S. (2024).** *Desarrollo de un modelo de dinámica de sistemas para brindar información a la comunidad académica del impacto de su comportamiento sobre la PTAR y el ecosistema, en la Universidad Antonio José Camacho (UNIAJC) sede sur en Cali.*
  [repositorio.uniajc.edu.co/handle/uniajc/2757](https://repositorio.uniajc.edu.co/handle/uniajc/2757)

- **Ministerio de Ambiente y Desarrollo Sostenible (2015).** *Resolución 0631 — Valores límite máximos permisibles para descargas a cuerpos de agua superficiales.*

- **Aguas de Barrancabermeja (2017).** *Reporte anual de pérdidas de agua no contabilizada en sistemas sin medición.*

---

## 14. Cómo correr Camaleón OS localmente

```bash
# Clonar el repositorio
git clone git@github.com:JFrangel/Camaleón-OS.git
cd Camaleón-OS

# Backend FastAPI (puerto 8000)
cd services/api
pip install -r requirements.txt
uvicorn app.main:app --reload

# Dashboard SvelteKit (puerto 5173)
cd apps/web-svelte
pnpm install
pnpm dev

# Bot Telegram (necesita TELEGRAM_BOT_TOKEN en .env)
cd apps/telegram
python bot.py
```

### Probar el agente

```bash
# Iniciar agente autónomo
curl -X POST http://localhost:8000/water/agent/start

# Ver estado
curl http://localhost:8000/water/agent/status

# Ejecutar 1 ciclo manualmente (para testing)
curl -X POST http://localhost:8000/water/agent/cycle

# Ver el dashboard
open http://localhost:5173/agua
```

### Inyectar escenario de fuga (demo)

```bash
curl -X POST http://localhost:8000/water/simulate \
  -H "Content-Type: application/json" \
  -d '{"scenario": "leak"}'
```

---

## 15. Resumen ejecutivo (1 minuto)

> Camaleón OS es un sistema inteligente que mide, analiza y optimiza el consumo de agua en UNIAJC Sede Sur. Combina **6 sensores IoT** ($1M COP), **4 agentes de IA autónomos** que deciden por sí solos, un **dashboard moderno** y un **bot de Telegram** que avisa cuando hay fugas en menos de 5 minutos.
>
> Resuelve un problema real: la PTAP del 2011 perdía 25% del agua sin saberlo = **$19 millones COP/año**.
>
> Con Camaleón OS, las pérdidas bajan a 10% y el sistema **se paga solo en 21 días**.
>
> Es interdisciplinar (Sistemas + Electrónica + Industrial), abierto, escalable y replicable. Impacta 5 ODS y reduce 2.3 toneladas de CO₂ al año.
>
> **Camaleón OS: cuando los datos hablan, el agua se cuida.**

---

*Documento técnico Camaleón OS · Versión 1.0 · Hackathon UNIAJC 2026*
*Equipo: Sistemas + Electrónica + Industrial*
*Repositorio: github.com/JFrangel/Camaleón-OS*
