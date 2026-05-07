# AguaMind OS — Plan Hackathon UNIAJC 2026
## "Tecnologías con Propósito · Inteligencia con Conciencia"
### Fecha límite: 8 de mayo 2026 · 5:00 PM · Pitch ante jurado

---

## ¿Qué hay que entregar?

El hackathon evalúa 4 criterios (100 pts total):
- **Novedad** 30% — qué tan original e innovadora es la solución
- **Aplicación Industrial** 30% — viabilidad técnica real, escalable
- **Actividad Inventiva** 20% — integración multidisciplinar, metodología
- **Impacto** 20% — sostenibilidad, bienestar, comunidad

Entregables concretos:
1. **Solución funcional** (app corriendo = AguaMind OS sobre AgentOS)
2. **Documentación técnica** con diagramas UML, circuito electrónico, análisis industrial
3. **Mockups / Wireframes** de las interfaces
4. **Pitch de 5 minutos** ante el jurado

---

## FASE A — SOFTWARE: AguaMind OS (sobre AgentOS)
> Lo que el equipo de Sistemas construye. AgentOS es el boilerplate, AguaMind es el producto.

### A1 · Dashboard Web `/agua`  ✅ HECHO (SvelteKit)
- [x] KPIs en tiempo real: IEH, TPP, CPE con colores de alerta
- [x] Niveles de tanques A y B (barras animadas)
- [x] Consumo por zona del campus (barras horizontales)
- [x] Historial 24h (sparkline + tabla)
- [x] Tab Costo-Beneficio con análisis ROI
- [x] Botones de escenarios demo: Normal / Fuga / Pico riego
- [ ] **Pendiente:** Actualizar datos con valores exactos del PDF (Fase A1a)
- [ ] **Pendiente:** Botón "Activar/Detener Agente" visible en UI
- [ ] **Pendiente:** Panel de alertas activas en tiempo real (auto-refresh 10s)
- [ ] **Pendiente:** Mockup/wireframe exportable (captura + Figma o similar)

### A2 · Bot Telegram  ✅ HECHO
- [x] `/agua` — estado completo del sistema
- [x] `/zonas` — consumo por zona
- [x] `/kpis` — indicadores con estado
- [x] `/reporte_agua` — resumen diario
- [x] `/alerta` — demo fuga
- [x] `/riego` — demo pico riego
- [x] `/normal` — reset
- [ ] **Pendiente:** Notificación automática PUSH cuando agente detecta anomalía

### A3 · Agente Autónomo LangGraph  ⚠️ PENDIENTE — el más importante para la nota
> "Al menos un agente que monitoree automáticamente las variables del sistema y tome al menos UNA decisión de forma autónoma"

**Qué hace el agente:**
1. Cada 60 segundos lee el sensor simulado (`GET /water/reading`)
2. Analiza si hay anomalías (pérdidas > 15%, tanque < 25%, pico de riego)
3. Decide autónomamente qué hacer:
   - Pérdida leve → genera alerta en dashboard
   - Pérdida crítica → envía notificación Telegram + genera reporte PDF
   - Tanque bajo → recomienda activar bombeo extra
4. A las 6:00 PM genera reporte diario automático y lo envía por Telegram

**Archivos a crear:**
```
services/api/app/routers/agent_water.py     ← endpoints: start, stop, status
packages/agents/agentos_agents/graphs/water_monitor.py  ← grafo LangGraph
packages/agents/agentos_agents/nodes/water_nodes.py     ← nodos del agente
```

**Diagrama de estados UML del agente (para el entregable):**
```
[IDLE]
  │ POST /water/agent/start
  ▼
[MONITORING] ──── cada 60s lee sensores
  │ anomalía detectada
  ▼
[ANALYZING] ──── compara vs umbrales + ML
  │ normal         │ anomalía
  ▼                ▼
[MONITORING]   [DECIDING]
                  │ leve         │ crítica
                  ▼              ▼
              [ALERTING]    [ALERTING]
                                 │
                            [REPORTING] ── genera PDF
                  │
                  ▼
             [MONITORING]
  │ hora 18:00 (diario)
  ▼
[REPORTING_DAILY] → PDF + Telegram
  │
  ▼
[MONITORING]
```

### A4 · Backend FastAPI `/water/*`  ✅ HECHO
- [x] `GET /water/reading` — lectura de sensores
- [x] `GET /water/status` — estado completo
- [x] `GET /water/history?hours=24` — historial
- [x] `GET /water/report/daily` — reporte completo
- [x] `POST /water/simulate` — inyectar escenario
- [ ] **Pendiente:** `POST /water/agent/start` — arrancar agente
- [ ] **Pendiente:** `GET /water/agent/status` — estado del agente
- [ ] **Pendiente:** `POST /water/agent/stop` — detener agente
- [ ] **Pendiente:** Actualizar constantes con datos reales exactos del PDF

### A5 · Actualizar datos reales  ⚠️ PENDIENTE
Correcciones a `services/api/app/routers/water.py` con valores exactos:
```python
# Valores exactos del PDF Aristizábal/Largacha (2025)
TOTAL_USERS = 8_234               # incluyendo docentes y personal
PUMP_MAX_CAPACITY_L_H = 7_268     # capacidad máxima bomba
PUMP_ACTIVATION_L = 24_000        # Tanque A: bomba ON aquí
AQUIFER_INITIAL_L = 5_000_000     # nivel inicial acuífero
DAILY_CONSUMPTION_L = 45_367      # total diario real

# Consumos diarios reales por categoría
ZONE_DAILY_BASE = {
    "Aseo Personal":     31_700,   # 7045 usos × 4.5L
    "Riego/Cancha":       4_000,   # promedio (3x/sem × 94L/min × 45min / 7días)
    "Lavado de Manos":    2_550,   # promedio 2300-2800L
    "Limpieza Pasillos":  1_000,   # promedio 800-1200L
    "Limpieza Baños":       750,   # promedio 600-900L
    "Limpieza Aulas":     1_250,   # promedio 1000-1500L
    "Cafetería":            240,   # medido directamente
    "Laboratorios":          64,   # 450L/sem ÷ 7 días
}
```

---

## FASE B — SISTEMAS: Documentación UML
> Entregable para el jurado. Se presenta en papel/pantalla durante el pitch.

### B1 · Diagrama de Arquitectura de Software (UML — Componentes)
**Herramienta:** draw.io / PlantUML / Lucidchart  
**Qué incluir:**
```
AguaMind OS
├── <<Frontend>> SvelteKit Dashboard
│     ├── /agua — Dashboard hídrico
│     └── / — Chat IA con agente
├── <<Backend>> FastAPI API
│     ├── /water/* — Módulo hídrico
│     ├── /water/agent/* — Agente autónomo
│     ├── /chat/stream — Chat LangGraph
│     └── /reports/generate — PDF WeasyPrint
├── <<Bot>> Telegram Bot
│     ├── WaterCommands (estado, zonas, KPIs)
│     └── AlertNotifier (push automático)
├── <<Agent>> LangGraph Water Monitor
│     ├── SensorReader
│     ├── AnomalyDetector (IsolationForest)
│     ├── DecisionMaker (LLM)
│     ├── AlertDispatcher
│     └── ReportGenerator
└── <<Database>> Supabase (PostgreSQL)
      ├── water_readings
      ├── water_alerts
      └── water_kpi_snapshots
```

### B2 · Diagrama de Estados del Agente Autónomo (UML — StateMachine)
Ver sección A3 arriba — plasmar en draw.io con notación UML estándar.

### B3 · Wireframes / Mockups
Capturas del dashboard real + anotaciones de UCD:
- Principio 1: Visibilidad del estado del sistema (KPIs siempre visibles)
- Principio 2: Feedback inmediato (alertas en rojo cuando hay anomalía)
- Principio 3: Prevención de errores (confirmación antes de simular escenario)
- Principio 4: Accesibilidad (colores semafóricos + texto)
- Principio 5: Consistencia (mismo lenguaje en Telegram y dashboard)

---

## FASE C — ELECTRÓNICA: Circuito + Sistema Embebido
> Documentación técnica. No se implementa hardware en el hackathon — se especifica.

### C1 · Circuito de Sensado y Acondicionamiento de Señal

**Variables a medir y sensores:**
| Variable | Sensor | Tipo señal | Rango |
|---|---|---|---|
| Caudal entrada PTAP | YF-S201 (efecto Hall) | Pulsos digitales | 1–30 L/min |
| Nivel Tanque A | HC-SR04 (ultrasónico) | PWM digital | 0–400 cm |
| Nivel Tanque B | HC-SR04 (ultrasónico) | PWM digital | 0–200 cm |
| Presión red distribución | MPX5700AP | 0–5V analógico | 0–700 kPa |
| Caudal zona riego | Caudalímetro DN25 | Pulsos digitales | 5–150 L/min |

**Circuito de acondicionamiento:**
- MCU: ESP32 DevKit (WiFi integrado, 2 núcleos, 240 MHz)
- ADC externo: ADS1115 (16-bit, 4 canales, I2C) para señal presión
- Protección: optoacopladores 4N35 entre sensores y MCU
- Display local: OLED SSD1306 128×64 (I2C) — muestra caudal + niveles
- Alimentación: 5V DC regulado (LM7805) + batería Li-Ion 18650 como backup
- Comunicación remota: WiFi → MQTT → Backend FastAPI
- LED RGB: indicador de estado (verde=normal, amarillo=warning, rojo=crítico)
- Buzzer: alerta sonora local en fuga crítica

### C2 · Arquitectura Completa del Sistema Embebido
```
┌─────────────────────────────────────────────────────────┐
│                  AguaMind Node (ESP32)                   │
│                                                          │
│  ┌──────────────┐    ┌─────────────────────────────────┐ │
│  │   SENSADO    │    │        PROCESAMIENTO             │ │
│  │ YF-S201 ×2  │───▶│  • Lectura interrupciones        │ │
│  │ HC-SR04 ×2  │───▶│  • Filtro media móvil (N=5)      │ │
│  │ MPX5700     │───▶│  • Conversión: pulsos→L/min      │ │
│  │ ADS1115     │───▶│  • Detección de umbrales         │ │
│  └──────────────┘    │  • Buffer circular de lecturas   │ │
│                      └─────────────┬───────────────────┘ │
│  ┌──────────────┐                  │                      │
│  │ ALIMENTACIÓN │    ┌─────────────▼───────────────────┐ │
│  │ 5V LM7805   │    │       COMUNICACIÓN               │ │
│  │ 18650 backup│    │  LOCAL: OLED + LED RGB + Buzzer  │ │
│  └──────────────┘    │  REMOTA: WiFi → MQTT → FastAPI  │ │
│                      └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
              │ MQTT / HTTP POST
              ▼
   ┌──────────────────────┐
   │  Backend FastAPI     │
   │  POST /water/ingest  │
   │  → Supabase DB       │
   └──────────────────────┘
```

### C3 · Diagrama de Flujo del Firmware (Software Embebido)
```
INICIO
  │
  ├── Inicializar GPIO, I2C, UART
  ├── Conectar WiFi (SSID/PASS desde EEPROM)
  ├── Conectar MQTT broker
  ├── Inicializar sensores (ping HC-SR04, test ADC)
  │
LOOP principal (cada 5 segundos):
  │
  ├── [SENSADO]
  │     ├── Leer YF-S201: contar pulsos en 1s → L/min
  │     ├── Leer HC-SR04 ×2: distancia → nivel %
  │     ├── Leer ADS1115: tensión → kPa
  │     └── Almacenar en buffer circular
  │
  ├── [PROCESAMIENTO]
  │     ├── Calcular media móvil de últimas 5 lecturas
  │     ├── Comparar vs umbrales:
  │     │     • caudal < umbral_bajo → fuga probable
  │     │     • nivel_tanque < 20% → nivel crítico
  │     │     • presión > max → pico de demanda
  │     └── Generar estado: OK / WARNING / CRITICAL
  │
  ├── [SALIDA LOCAL]
  │     ├── Actualizar display OLED (caudal, niveles, estado)
  │     ├── LED: verde/amarillo/rojo según estado
  │     └── Si CRITICAL: activar buzzer 3 pulsos
  │
  └── [COMUNICACIÓN REMOTA]
        ├── Publicar MQTT: {id, ts, caudal, nivel_a, nivel_b, presion, estado}
        └── Si fallo MQTT: guardar en memoria flash local (retry en 30s)

FIN LOOP
```

---

## FASE D — INDUSTRIAL: Análisis y Diagramas
> Documentos para el entregable del reto industrial. Basado 100% en datos reales del PDF.

### D1 · Diagrama de Proceso del Sistema Hídrico (Flujo PTAP)
```
[Cuenca Río Pance]
        │ captación subterránea
        ▼
  ┌─────────────┐     ┌─────────────┐
  │   ALJIBE 1  │     │   ALJIBE 2  │
  │  ~12m prof. │     │  ~15m prof. │
  └──────┬──────┘     └──────┬──────┘
         │ 113.56 L/min      │─────────────────────────────┐
         │ (30 gal/min)      │                             │
         ▼                   ▼                     [RIEGO CANCHA]
   ┌────────────────────────────────┐          (3×/sem · 45min · 94L/min)
   │           PTAP                │           SIN TRATAMIENTO · ~4,000L/día
   │  Filtro 1: Grava + Arena      │
   │  Filtro 2: + Antracita        │
   │  Filtro 3: + Carbón activado  │
   └────────────────┬───────────────┘
                    │ agua potable
         ┌──────────▼──────────┐
         │    TANQUE A         │
         │  36,000 L           │
         │  Bomba ON @ 24,000L │
         │  Capacidad: 7,268L/h│
         └──────────┬──────────┘
                    │
         ┌──────────▼──────────┐
         │    TANQUE B         │
         │  16,000 L           │
         └──────────┬──────────┘
                    │ distribución
        ┌───────────┼───────────────┬──────────┬────────┐
        ▼           ▼               ▼          ▼        ▼
   [Baños]    [Lavamanos]    [Limpieza]  [Cafetería] [Labs]
  31,700L/d   2,550L/d      3,000L/d     240L/d     64L/d
   (69.73%)
```

**Variables clave identificadas:**
- Caudal entrada: 113.56 L/min
- Demanda total: 45,367 L/día
- Pérdidas estimadas: 9,073–13,610 L/día (20–30%)
- Nivel crítico Tanque A: < 24,000L → activa bomba
- Cooperación comunitaria: factor determinante de sostenibilidad (Vensim: 50% = sistema estable)

### D2 · Tres KPIs con Fórmula y Propósito

**KPI 1 — IEH: Índice de Eficiencia Hídrica**
```
IEH (%) = [(Caudal entrada – Pérdidas no contabilizadas) / Caudal entrada] × 100
```
- Meta: > 90% | Actual estimado: ~70–80% (sin medición exacta)
- Propósito: mide qué porción del agua captada llega efectivamente a los usuarios finales

**KPI 2 — TPP: Tasa de Pérdidas del Proceso**
```
TPP (%) = [Agua no contabilizada / Caudal entrada total] × 100
```
- Meta: < 10% | Actual: ~20–30% (rango documentado en sistemas sin medición — Aguasde Barrancabermeja, 2017)
- Propósito: cuantifica ineficiencias de distribución y fugas para priorizar intervenciones

**KPI 3 — CPE: Consumo Per Estudiante**
```
CPE (L/est/día) = Consumo total diario / N° estudiantes activos
```
- Meta: ≤ 14.04 L/est/día (línea base UNIAJC — Arias Montoya et al., 2024)
- Propósito: benchmark de eficiencia hídrica por usuario para evaluar impacto de campañas de concientización

### D3 · Identificación de Ineficiencias — Lean Manufacturing (Mudas)

| # | Muda (Tipo) | Manifestación en UNIAJC | Impacto estimado |
|---|---|---|---|
| 1 | **Defectos** | Fugas no detectadas (sin caudalímetros) | 20–30% caudal perdido |
| 2 | **Sobreproducción** | Bombeo sin demanda real (tanque lleno sin saberlo) | Desgaste bomba + energía |
| 3 | **Espera** | Tiempo entre detección manual de fuga y reparación | Días o semanas de pérdida |
| 4 | **Inventario** | Tanques sobrellenos → presión excesiva → más fugas | Efecto cascada |
| 5 | **Movimiento** | Personal revisando niveles manualmente | Tiempo improductivo |
| 6 | **Transporte** | Agua tratada usada sin diferenciación para riego | Costo de tratamiento innecesario |
| 7 | **Procesamiento excesivo** | Tratar agua que irá a riego (Aljibe 2 parcialmente resuelve esto) | Reactivos desperdiciados |

**Diagrama de Ishikawa — Causa raíz: "Pérdidas de agua 20–30% sin detectar"**
```
                    EFECTO PRINCIPAL
         ┌────────────────────────────────┐
         │  Pérdidas de agua 20-30%       │
         │  sin detectar en campus UNIAJC │
         └────────────────────────────────┘
                          │
    ┌─────────┬────────────┼────────────┬─────────┐
    │         │            │            │         │
MEDICIÓN   INFRAEST.   PERSONAS    PROCESOS   GESTIÓN
    │         │            │            │         │
Sin         Red sin     Sin          Sin SOP   Sin KPIs
caudalí-    secto-      cultura      de        definidos
metros      rizar       ahorro       riego     
            │            │                     
Sin         Tuberías    Sin                    
sensores    sin         señalética             
nivel       mant.       campus                 
            │                                  
Sin         Sin                                
SCADA       planos                             
            hidráulicos                        
```

### D4 · Propuesta de Mejora Operativa

**Acción 1: Instalación sistema IoT de medición (AguaMind Node)**
- Qué: 3 caudalímetros + 2 sensores nivel + 1 ESP32 + dashboard
- Dónde: entrada PTAP, salida Tanque A, zona de riego cancha
- Costo estimado: $4,500,000 COP (hardware + instalación)
- Impacto esperado: reducción 15% pérdidas = 6,805 L/día recuperados
- Beneficio: alertas automáticas en < 5 minutos vs. días sin detección

**Acción 2: Automatización del riego con válvulas solenoides**
- Qué: 2 válvulas solenoides DN25 + controlador horario + sensor suelo
- Dónde: sistema de aspersores cancha + jardines
- Costo estimado: $2,800,000 COP
- Impacto esperado: reducir riego de ~4,000 a ~1,800 L/día (fuera de hora pico)
- Beneficio: ahorro 2,200 L/día × 365 = 803,000 L/año

### D5 · Análisis Costo-Beneficio

**Pérdidas actuales:**
```
Pérdida diaria estimada (20%):  45,367 × 0.20 = 9,073 L/día
Costo agua EMCALI:              ~$3,500 COP/m³  
Pérdida económica diaria:       9.07 m³ × $3,500 = $31,745 COP/día
Pérdida económica anual:        $31,745 × 365   = $11,587,000 COP/año
```

**Inversión AguaMind OS:**
```
Hardware IoT (sensores + ESP32):    $4,500,000 COP
Válvulas solenoides + controlador:  $2,800,000 COP
Instalación y puesta en marcha:     $1,200,000 COP
────────────────────────────────────────────────────
TOTAL INVERSIÓN:                    $8,500,000 COP
```

**Beneficios proyectados:**
```
Reducción pérdidas (15% del consumo):  6,805 L/día × $3.5/L = $23,817 COP/día
Ahorro riego automatizado:             2,200 L/día × $3.5/L = $7,700 COP/día
────────────────────────────────────────────────────────────────────────────────
Ahorro diario total:                   $31,517 COP/día
Ahorro anual proyectado:               $11,503,705 COP/año

TIEMPO DE RECUPERACIÓN INVERSIÓN:     $8,500,000 / $11,503,705 = ~8.9 MESES
```

---

## FASE E — PRESENTACIÓN: Pitch 5 minutos
> El jurado evalúa Novedad, Aplicación Industrial, Actividad Inventiva e Impacto.

### E1 · Estructura del pitch (5 min exactos)

| Tiempo | Sección | Contenido |
|---|---|---|
| 0:00–0:45 | **Problema** | La PTAP no tiene medición. 20-30% de pérdidas invisibles. Dato: $11.5M COP/año desperdiciados. |
| 0:45–1:30 | **Solución** | AguaMind OS: agente IA + IoT + dashboard + Telegram. Demo en vivo: encender app. |
| 1:30–2:30 | **Demo vivo** | Mostrar dashboard → inyectar fuga → ver alerta en Telegram automáticamente. |
| 2:30–3:15 | **Técnica** | Mostrar: diagrama UML (30s) + circuito ESP32 (30s) + diagrama proceso PTAP (15s). |
| 3:15–4:00 | **Industrial** | KPIs en pantalla. Ishikawa. "Con $8.5M COP recuperamos en 9 meses." |
| 4:00–4:45 | **Impacto** | ODS 6. Escalable a otras sedes. 50% cooperación = sistema sostenible (Vensim). |
| 4:45–5:00 | **Cierre** | "AguaMind OS: datos + IA + acción. El agua de la UNIAJC bajo control." |

### E2 · Lo que el jurado va a querer ver
- ✅ **Funcionando en vivo** (no PPT, app real corriendo)
- ✅ **Números reales** (45,367 L/día, $11.5M/año pérdidas, ROI 9 meses)
- ✅ **Los 3 retos cubiertos** (mencionar explícitamente Sistemas + Electrónica + Industrial)
- ✅ **Interdisciplinaridad** visible en la presentación
- ✅ **Novedad** — agente IA autónomo + Telegram es diferenciador

---

## Resumen: ¿Qué falta hacer?

### 🔴 CRÍTICO (sin esto no hay demo)
- [ ] **A3** — Agente autónomo LangGraph (es el diferenciador principal para nota)
- [ ] **A5** — Actualizar datos reales exactos en water.py
- [ ] **A2** — Push automático Telegram cuando agente detecta anomalía

### 🟡 IMPORTANTE (para la nota de documentación)
- [ ] **B1** — Diagrama UML de componentes (draw.io, 1 hoja)
- [ ] **B2** — Diagrama de estados del agente (draw.io, 1 hoja)
- [ ] **B3** — Mockup anotado con principios UCD
- [ ] **C1-C3** — Documentación del circuito ESP32 y firmware
- [ ] **D3-D5** — Ishikawa, tabla Lean, costo-beneficio (este doc ya tiene el contenido)

### 🟢 YA LISTO
- [x] Dashboard web funcional con KPIs, tanques, zonas, historial
- [x] Bot Telegram con 7 comandos de agua
- [x] Backend FastAPI `/water/*` completo
- [x] Migración Supabase para series de tiempo
- [x] Datos base del simulador (necesita ajuste con exactos del PDF)
- [x] Análisis costo-beneficio en UI
- [x] Plan industrial completo (este documento)
