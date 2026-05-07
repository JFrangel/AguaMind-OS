# AguaMind OS — Diagramas, Arquitectura y Diseño

> Documento técnico de diseño para el jurado del Hackathon UNIAJC 2026
> Incluye: diagramas UML profesionales, arquitectura por capas, principios UCD,
> caracterización del producto, fases de implementación.

---

## 1. Diagrama UML de Componentes — Arquitectura Lógica

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                                │
│                          AguaMind OS — Sistema Distribuido                     │
│                                                                                │
├─ CAPA DE PERCEPCIÓN ─────────────────────────────────────────────────────────┤
│                                                                                │
│   <<device>>           <<device>>           <<device>>                         │
│   ┌──────────┐         ┌──────────┐         ┌──────────┐                      │
│   │ AguaMind │         │ AguaMind │         │ AguaMind │   ← N nodos          │
│   │ Node 01  │         │ Node 02  │         │ Node N   │                       │
│   │ (ESP32)  │         │ (ESP32)  │         │ (ESP32)  │                       │
│   └────┬─────┘         └────┬─────┘         └────┬─────┘                      │
│        │                    │                    │                             │
│        ↓ MQTT publish       ↓                    ↓                             │
│                                                                                │
├─ CAPA DE TRANSPORTE ─────────────────────────────────────────────────────────┤
│                                                                                │
│              ┌────────────────────────────────┐                               │
│              │   <<broker>> HiveMQ Cloud      │                               │
│              │   topic: campus/uniajc/sensors │                               │
│              └─────────────┬──────────────────┘                               │
│                            │                                                   │
├─ CAPA DE APLICACIÓN ─────────────────────────────────────────────────────────┤
│                                                                                │
│   ┌──────────────────────────────────────────────────────────────────────┐    │
│   │                  <<service>> FastAPI Backend                          │    │
│   │                                                                       │    │
│   │   ┌────────────────┐    ┌─────────────────┐   ┌──────────────────┐   │    │
│   │   │ /water/ingest  │───▶│  Domain Service │──▶│ Persistence Adp  │   │    │
│   │   │ /water/reading │    │  · KPIs         │   │ · Supabase       │   │    │
│   │   │ /water/agent/* │    │  · Alerts       │   │ · Cache          │   │    │
│   │   │ /water/report  │    │  · Validation   │   │                  │   │    │
│   │   └────────────────┘    └────────┬────────┘   └──────────────────┘   │    │
│   │                                  │                                    │    │
│   │   ┌──────────────────────────────▼────────────────────────────────┐   │    │
│   │   │           <<orchestrator>> WaterMonitorAgent (LangGraph)      │   │    │
│   │   │                                                                │   │    │
│   │   │   ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │   │    │
│   │   │   │ Systems     │  │ Sensor      │  │ Industrial          │   │   │    │
│   │   │   │ Agent       │  │ Agent       │  │ Agent               │   │   │    │
│   │   │   │ (KPIs+ML)   │  │ (Calidad)   │  │ (Lean+Costos)       │   │   │    │
│   │   │   └─────────────┘  └─────────────┘  └─────────────────────┘   │   │    │
│   │   └────────────────────────────────────────────────────────────────┘   │    │
│   └──────────────────────────────────────────────────────────────────────┘    │
│                                  │                                              │
├─ CAPA DE PRESENTACIÓN ───────────────────────────────────────────────────────┤
│                                  │                                              │
│      ┌───────────────────────────┼────────────────────────────┐                │
│      ▼                           ▼                            ▼                │
│   ┌──────────────┐       ┌─────────────────┐       ┌────────────────┐         │
│   │ <<UI>>       │       │ <<bot>>         │       │ <<adapter>>    │         │
│   │ Dashboard    │       │ Telegram Bot    │       │ Sistemas       │         │
│   │ SvelteKit    │       │ Push Alerts     │       │ Existentes     │         │
│   │ (4 tabs)     │       │ + Comandos      │       │ (SCADA, etc)   │         │
│   └──────────────┘       └─────────────────┘       └────────────────┘         │
│                                                                                │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Diagrama UML de Despliegue (Deployment)

```
                          ┌─────────────────────────┐
                          │   Cloud (Vercel/Koyeb)  │
                          │                          │
                          │  [Dashboard SvelteKit]   │
                          │       :443/agua          │
                          │            │             │
                          │            ▼             │
                          │  [FastAPI Backend]       │
                          │       :443/water/*       │
                          └─────────────┬────────────┘
                                        │ HTTPS
                                        │
        ┌───────────────────────────────┼─────────────────────────┐
        │                               │                         │
        ▼                               ▼                         ▼
  ┌─────────────┐               ┌─────────────┐         ┌──────────────┐
  │ HiveMQ      │               │ Supabase    │         │ Telegram API │
  │ MQTT Broker │               │ PostgreSQL  │         │ Bot          │
  │ TLS 8883    │               │ + pgvector  │         │ Webhook      │
  └──────▲──────┘               └─────────────┘         └──────────────┘
         │ MQTT/TLS
         │
   ╔═════╧═════════════════════════════════════════════════════════╗
   ║                  Campus UNIAJC Sede Sur (Cali)                  ║
   ║                                                                  ║
   ║   ┌──────────────────┐                                          ║
   ║   │  AguaMind Node   │  Punto de instalación: PTAP              ║
   ║   │  ESP32-WROOM-32  │  Alimentación: 220V → HLK-PM01 → 5V      ║
   ║   │                  │  Backup: Batería 18650                    ║
   ║   │  6 sensores +    │  Conectividad: WiFi 2.4 GHz campus       ║
   ║   │  OLED + LED      │  Comm local: I2C + GPIO                  ║
   ║   └──────────────────┘                                           ║
   ╚════════════════════════════════════════════════════════════════╝
```

---

## 3. Diagrama UML de Estados — WaterMonitorAgent

```
                          ╔═══════════╗
              ┌──────────▶║   IDLE    ║◀──────────────┐
              │           ╚═════╤═════╝                │
              │                 │ timer 30s            │
              │                 ▼                       │
              │           ╔═══════════╗                 │
              │           ║MONITORING ║  POST /reading │
              │           ╚═════╤═════╝                 │
              │                 │                       │
              │                 ▼                       │
              │           ╔═══════════╗                 │
              │           ║ ANALYZING ║                 │
              │           ║ (Sys+Sen+ │  IsolationForest│
              │           ║  Industr) ║  + reglas       │
              │           ╚═════╤═════╝                 │
              │                 │                       │
              │                 ▼                       │
              │           ╔═══════════╗                 │
              │           ║ DECIDING  ║                 │
              │           ╚═══╤══╤═╤══╝                 │
              │               │  │ │                    │
              │       ┌───────┘  │ └────────┐           │
              │       │ ok      │ alert    │ critical  │
              │       │         │           │           │
              │       │         ▼           ▼           │
              │       │   ╔═══════════╗  ╔═══════════╗ │
              │       │   ║ ALERTING  ║  ║ ALERTING  ║ │
              │       │   ╚═════╤═════╝  ╚═════╤═════╝ │
              │       │         │              │       │
              │       │   Telegram        Telegram     │
              │       │     push            push       │
              │       │         │              ▼       │
              │       │         │        ╔═══════════╗ │
              │       │         │        ║ REPORTING ║ │
              │       │         │        ╚═════╤═════╝ │
              │       │         │              │       │
              │       │         │         PDF + push   │
              │       │         │              │       │
              └───────┴─────────┴──────────────┘       │
                                                        │
                              hour == 18:00 (diario) ──┘
                              → REPORTING_DAILY → IDLE
```

---

## 4. Diagrama de Secuencia — Detección de Fuga

```
┌─────┐    ┌──────┐    ┌────────┐    ┌────────┐    ┌──────┐    ┌──────┐
│ESP32│    │MQTT  │    │FastAPI │    │Multi-  │    │ Tele │    │Dashb │
│Node │    │Broker│    │/ingest │    │Agente  │    │ gram │    │board │
└──┬──┘    └──┬───┘    └───┬────┘    └───┬────┘    └──┬───┘    └──┬───┘
   │ vibración│             │              │           │            │
   │ detectada│             │              │           │            │
   ├─publish─▶│             │              │           │            │
   │         ├─→            │              │           │            │
   │         │              │              │           │            │
   │         │  fwd msg     │              │           │            │
   │         ├──────────────▶              │           │            │
   │         │              ├─validate────▶│           │            │
   │         │              │              │           │            │
   │         │              │              │ IsolationForest        │
   │         │              │              │ score = 0.78           │
   │         │              │              ├──crítico──┐            │
   │         │              │              │           │            │
   │         │              │              │           │            │
   │         │              │              │  4 agentes evalúan     │
   │         │              │              │  → DECISION = critical │
   │         │              │              │                        │
   │         │              │              ├─alert────▶│            │
   │         │              │              │           │            │
   │         │              │              │           ├─push──────▶│
   │         │              │              │           │   chat_id  │
   │         │              │              │           │            │
   │         │              │              ├─SSE event─────────────▶│
   │         │              │              │           │            │
   │         │              ◀──response────┤           │            │
   │         │              │              │           │            │
   │ ack     │              │              │           │            │
   │◀────────┤              │              │           │            │
   │         │              │              │           │            │
   │         │              │              │           │            │
   │         │              │              │   tiempo total: < 5s   │
```

---

## 5. Arquitectura por Capas

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                             ║
║                         PRESENTATION LAYER                                  ║
║   ─────────────────────────────────────────────────────────────────        ║
║   • Dashboard SvelteKit (4 tabs · dark mode · minimalista)                  ║
║   • Bot Telegram (10 comandos + push automático)                            ║
║   • OLED local en cada nodo ESP32                                           ║
║                                                                             ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║                         APPLICATION LAYER                                   ║
║   ─────────────────────────────────────────────────────────────────        ║
║   • FastAPI (REST + SSE)                                                    ║
║   • Routers: /water · /water/agent · /water/ingest                          ║
║   • Pydantic validation · CORS · Rate limiting                              ║
║                                                                             ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║                         DOMAIN LAYER                                        ║
║   ─────────────────────────────────────────────────────────────────        ║
║   • WaterMonitorAgent (LangGraph orchestrator)                              ║
║       ├─ SystemsAgent     · KPIs + IsolationForest                          ║
║       ├─ SensorAgent      · validación señales                              ║
║       └─ IndustrialAgent  · Lean + costos + ODS                             ║
║   • LLM Cascade: Groq → OpenRouter → Gemini                                 ║
║                                                                             ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║                         INFRASTRUCTURE LAYER                                ║
║   ─────────────────────────────────────────────────────────────────        ║
║   • Supabase PostgreSQL (water_readings, water_alerts, water_kpi_snapshots) ║
║   • HiveMQ Cloud (MQTT broker)                                              ║
║   • Telegram Bot API                                                        ║
║   • WeasyPrint (generación PDF reportes)                                    ║
║                                                                             ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║                         PERCEPTION LAYER                                    ║
║   ─────────────────────────────────────────────────────────────────        ║
║   • ESP32-WROOM-32 (firmware MicroPython · FreeRTOS)                        ║
║   • 6 sensores: caudal, presión, nivel, vibración, freático, turbidez      ║
║   • Acondicionamiento: ADS1115 + LM358 + divisores resistivos              ║
║                                                                             ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

## 6. Principios de Diseño Centrado en Usuario (UCD)

### Aplicados al Dashboard y Bot Telegram

| # | Principio | Implementación en AguaMind OS |
|---|-----------|-------------------------------|
| **1** | **Visibilidad del estado** | KPIs (IEH, TPP, CPE, ICA) siempre visibles en la parte superior. Indicador "En vivo" pulsante. Última actualización en formato HH:MM:SS. |
| **2** | **Coincidencia con el mundo real** | Lenguaje técnico hídrico familiar: "tanque", "caudal", "presión". Iconografía monocromática que evoca instrumentación industrial. |
| **3** | **Control y libertad del usuario** | Botón pausar/reanudar el modo en vivo. Ejecución de ciclos manuales del agente. Selector de escenarios demo sin commitments. |
| **4** | **Consistencia y estándares** | Misma paleta semafórica (verde/ámbar/rojo) en dashboard y Telegram. Comandos predecibles: `/agua`, `/zonas`, `/kpis`. |
| **5** | **Prevención de errores** | Confirmación antes de detener el agente. Validación Pydantic en backend. Estados claros: "Detenido" vs "En monitoreo". |
| **6** | **Reconocimiento, no recordar** | Tabla de zonas con barras visuales de proporción. Iconos compactos (Q, P, N, T, V) para los 6 sensores. Tooltips en hover con detalles. |
| **7** | **Flexibilidad y eficiencia** | Auto-refresh + comandos manuales. SSE para tiempo real. Atajos en Telegram para usuarios avanzados. |
| **8** | **Diseño estético minimalista** | Dark mode `#0a0e14` + tipografía Inter. Espaciado generoso. Datos numéricos en monoespaciada (JetBrains Mono). Sin emojis. |
| **9** | **Recuperación de errores** | Mensajes claros: "Backend no disponible". Botón directo a la API docs. Estado degradado visible (no falla silencioso). |
| **10** | **Ayuda contextual** | Cada KPI muestra fórmula y meta. Tooltip explicativo en sensores. Tab Industrial con análisis Lean explicado. |

---

## 7. Caracterización del Producto

### 7.1 Definición del producto

**AguaMind OS** es una plataforma SaaS de gestión hídrica inteligente que combina:

```
        Hardware IoT          +          IA Multi-Agente          =       Decisiones autónomas
         (sensores)                      (LangGraph)                       (alertas/reportes)
            ↓                                  ↓                                    ↓
       6 sensores                     4 agentes coordinados           Telegram + Dashboard + PDF
       ESP32 + MQTT                   IsolationForest                   en tiempo real
```

### 7.2 Atributos del producto

| Atributo | Especificación |
|----------|---------------|
| **Tipo** | Plataforma SaaS + Hardware IoT |
| **Modelo** | Open Source (MIT) + Hardware ~$1M COP |
| **Despliegue** | Cloud (Vercel + Koyeb + Supabase) + Edge (ESP32) |
| **Latencia** | Sensor → Dashboard < 5 segundos · Sensor → Telegram < 30 segundos |
| **Disponibilidad objetivo** | 99% (con failover MQTT → HTTP) |
| **Escalabilidad** | N nodos por campus, 1 backend coordina |
| **Idioma** | Español (UI) · API en inglés |
| **Accesibilidad** | Web responsive · Telegram (cross-platform) |
| **Autenticación** | Supabase Auth (futuro) · Telegram chat_id whitelist |
| **Compliance** | Resolución 0631/2015 (Min. Ambiente Colombia) |

### 7.3 Usuarios objetivo (Personas)

| Persona | Necesidad | Cómo AguaMind la resuelve |
|---------|-----------|---------------------------|
| **Director de Mantenimiento** | Ver estado del sistema sin ir al sitio | Dashboard remoto + alertas Telegram |
| **Operario PTAP** | Saber cuándo activar bomba | Pantalla OLED + LED RGB local |
| **Coordinador de Sostenibilidad** | Reportes ODS para acreditación | PDF diario automático |
| **Decano de Ingeniería** | KPIs para junta directiva | Tab Industrial con costo-beneficio |
| **Estudiante de Ingeniería** | Tomar decisiones basadas en datos | Modelo educativo open source |

---

## 8. Fases de Implementación

### Fase 0 · Diseño y Validación (Día -7 a Día 0)

```
[Hito]  Diseño técnico aprobado
─────────────────────────────────
• Definición de los 6 sensores (✓ hecho)
• Diagramas UML componentes/estados (✓ hecho)
• Validación de costo-beneficio (✓ ROI 21 días)
• Configuración entornos (Supabase, GitHub) (✓ hecho)
• Plan de pitch 5 min ensayado (en curso)

Entregables: Documentación · PDF entregable · Repo público
```

### Fase 1 · Demo Funcional (Día 1 del Hackathon · 7 mayo)

```
[Hito]  MVP corriendo end-to-end
─────────────────────────────────
08:00  Setup local · Backend FastAPI + Dashboard SvelteKit
09:00  Validación simulador → /water/ingest
10:00  Activar agente IA · ver ciclos en dashboard
11:00  Crear bot Telegram (BotFather) + obtener chat_id
12:00  Test push automático (escenario fuga)
13:00  Almuerzo · grabar GIFs de demos
14:00  Diagramas finales (draw.io export PNG)
15:00  Generación PDF entregable (WeasyPrint)
16:00  Mockups Wokwi/Proteus (esquemático ESP32)
17:00  Ensayo del pitch · validación cronómetro
18:00  Subir todo al repo · push final

Entregables: Demo funcional · PDF · Diagramas · Pitch ensayado
```

### Fase 2 · Pitch (Día 2 del Hackathon · 8 mayo)

```
[Hito]  Defensa exitosa ante el jurado
──────────────────────────────────────
08:00  Setup demo en sala (laptop + proyector)
09:00  Validar que backend + dashboard + simulador corren
10:00  Inicia pitch · 5 min cronometrados
       ├─ 0:00–0:45  Problema (UNIAJC pierde $19M/año)
       ├─ 0:45–1:30  Solución (AguaMind OS funcional)
       ├─ 1:30–2:30  Demo en vivo (inyectar fuga · alerta Telegram)
       ├─ 2:30–3:15  Técnica (UML + circuito ESP32)
       ├─ 3:15–4:00  Industrial (KPIs · Ishikawa · ROI 21 días)
       ├─ 4:00–4:45  Impacto (5 ODS · 16M L/5 años)
       └─ 4:45–5:00  Cierre

11:00  Q&A jurado (máximo 5 minutos)
12:00  Resultados

Entregables: Defensa · Premio (objetivo)
```

### Fase 3 · Piloto Real (Mes 1 post-hackathon)

```
[Hito]  AguaMind Node físico instalado en PTAP UNIAJC
─────────────────────────────────────────────────────
Semana 1  Compra hardware (ESP32 + 6 sensores · ~$700K COP)
Semana 2  Armado en protoboard · validación bench
Semana 3  Diseño PCB final · gabinete IP65
Semana 4  Instalación in situ · capacitación al personal

Entregables: 1 nodo funcional · Datos reales en dashboard
```

### Fase 4 · Escalamiento (Meses 2-6)

```
[Hito]  5 nodos en zonas críticas
─────────────────────────────────
Mes 2  Análisis de datos del piloto · ajustes firmware
Mes 3  Nodo 2 (Tanque B + Red distribución)
Mes 4  Nodo 3 (Riego cancha) + Nodo 4 (Cafetería)
Mes 5  Nodo 5 (Laboratorios) · auditoría completa
Mes 6  Reporte de ahorros reales · validación KPIs

Entregables: 5 nodos · Reporte ROI real · Caso de éxito
```

### Fase 5 · Replicación Regional (Meses 7-12)

```
[Hito]  Otras universidades de Cali adoptan AguaMind OS
───────────────────────────────────────────────────────
Mes 7-9   Otras sedes UNIAJC (Norte, Centro)
Mes 10-12 Univalle, Icesi, USB · paquete instalable

Entregables: Modelo escalable · Whitepaper publicado
```

---

## 9. Esquema de Conexión Completo (de sensor a usuario)

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  PUNTO 1 · Aljibe                                                            │
│  ━━━━━━━━━━━━━━                                                              │
│  ┌──────────────┐                                                           │
│  │   YF-S201    │── pulsos Hall ──┐                                         │
│  │ (caudal)     │                  │                                         │
│  └──────────────┘                  │                                         │
│  ┌──────────────┐                  ├──▶ ESP32 GPIO 34/35                    │
│  │ 4-20mA       │── corriente ─┐   │      ↓                                 │
│  │ (freático)   │              │   │   procesamiento                         │
│  └──────────────┘              ▼   │      ↓                                 │
│                              ADS1115                                         │
│  PUNTO 2 · PTAP filtros                                                      │
│  ━━━━━━━━━━━━━━━━━━━                                                         │
│  ┌──────────────┐                                                           │
│  │   TSD-10     │── 0–4.5V ─────────▶ ADS1115 Ch2                          │
│  │ (turbidez)   │                                                            │
│  └──────────────┘                                                            │
│                                                                              │
│  PUNTO 3 · Tanques                                                           │
│  ━━━━━━━━━━━━━━━                                                             │
│  ┌──────────────┐                                                           │
│  │  JSN-SR04T   │── trig/echo ──▶ ESP32 GPIO 25/26 (Tanque A)              │
│  │  (nivel)     │   trig/echo ──▶ ESP32 GPIO 27/14 (Tanque B)              │
│  └──────────────┘                                                            │
│                                                                              │
│  PUNTO 4 · Red distribución                                                  │
│  ━━━━━━━━━━━━━━━━━━━━━━━━                                                    │
│  ┌──────────────┐                                                           │
│  │  MPX5700AP   │── 0–5V ──▶ LM358 ──▶ ADS1115 Ch0                         │
│  │  (presión)   │                                                            │
│  └──────────────┘                                                            │
│  ┌──────────────┐                                                           │
│  │   SW-420     │── digital ───────▶ ESP32 GPIO 33                         │
│  │ (vibración)  │                                                            │
│  └──────────────┘                                                            │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
                                     │
                              ESP32 procesa cada 30s
                                     │
                       publica MQTT  ▼  publica HTTP fallback
                              ┌──────────┐
                              │ HiveMQ   │
                              └─────┬────┘
                                    ▼
                          ┌──────────────────┐
                          │  FastAPI         │
                          │  /water/ingest   │
                          └────┬───────┬─────┘
                               │       │
                               ▼       ▼
                       Multi-agente   Supabase
                       LangGraph      PostgreSQL
                            │
                ┌───────────┼───────────┐
                ▼           ▼           ▼
         Dashboard      Telegram    PDF Report
                                     (18:00)
                            │
                            ▼
                    📱 Jose F. (+57 318 293 6639)
                       chat_id whitelist
```

---

## 10. Resumen de Diferenciadores

```
┌───────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   DIFERENCIADORES CLAVE de AguaMind OS                                 │
│   ─────────────────────────────────────────                            │
│                                                                         │
│   [1]  Sistema multi-agente IA (no chatbot · 4 agentes especializados) │
│   [2]  6 sensores accesibles ($1M COP vs SCADA $50M+)                   │
│   [3]  Telegram como interfaz oficial (sin software adicional)          │
│   [4]  Dashboard moderno minimalista (estilo Linear/Vercel)             │
│   [5]  Open source · replicable · interoperable                         │
│   [6]  Datos reales del campus (tesis Aristizábal & Largacha 2025)     │
│   [7]  ROI 21 días + 5 ODS impactados                                   │
│   [8]  Documentación profesional con WeasyPrint (auto-generada)         │
│                                                                         │
└───────────────────────────────────────────────────────────────────────┘
```

---

*Documento de diseño técnico · AguaMind OS · Hackathon UNIAJC 2026*
*Sistema multi-agente de gestión hídrica · Datos reales · Open Source*
