# 🔌 Camaleón OS — Guía de Simulación y Conexión

> Cómo simular el sistema completo (sensores + ESP32 + dashboard + Telegram) sin necesidad de hardware físico.

---

## 1. Visión general del flujo de datos

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SIMULACIÓN  (sin hardware físico)                  │
│                                                                       │
│   ┌──────────────┐                                                   │
│   │   Proteus    │  ←  Sensores virtuales (pots, generadores)       │
│   │  o Wokwi     │  ←  ESP32 simulado con MicroPython/Arduino       │
│   │  o sim_pc.py │  ←  Script Python que genera datos realistas     │
│   └──────┬───────┘                                                   │
│          │ HTTP POST JSON / MQTT publish                             │
│          ▼                                                            │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │  FastAPI Backend  →  POST /water/ingest                      │  │
│   │  • Valida payload (Pydantic)                                  │  │
│   │  • Calcula KPIs (IEH/TPP/CPE/ICA)                            │  │
│   │  • Genera alertas según los 6 sensores                       │  │
│   │  • Despierta a los 4 agentes IA                              │  │
│   └──────┬─────────────────────────────────┬─────────────────────┘  │
│          │                                  │                        │
│          ▼                                  ▼                        │
│   ┌─────────────────┐             ┌────────────────────┐            │
│   │  Dashboard /agua │             │  Telegram Bot      │            │
│   │  • 4 tabs        │             │  • Push automático │            │
│   │  • Live SSE      │             │  • /agua /kpis     │            │
│   └─────────────────┘             └────────────────────┘            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Tres opciones de simulación

### 🥇 Opción 1 — Simulador Python (más rápido, ideal para demo)

**Cuándo usar:** durante el pitch del hackathon, desarrollo, demos a profesores.

**Cómo correr:**

```bash
# Terminal 1 — Backend
cd services/api
uvicorn app.main:app --reload

# Terminal 2 — Dashboard
cd apps/web-svelte
pnpm dev
# Abrir http://localhost:5173/agua

# Terminal 3 — Bot Telegram (necesita token)
cd apps/telegram
python bot.py

# Terminal 4 — Simulador ESP32 (envía datos cada 5s)
python firmware/simulator_pc.py --scenario normal

# Para demostrar fuga en pitch
python firmware/simulator_pc.py --scenario leak
```

**Ventaja:** funciona en 30 segundos, sin hardware ni IDE adicional.

---

### 🥈 Opción 2 — Wokwi (simulador ESP32 en navegador)

**Cuándo usar:** mostrar el firmware MicroPython funcionando "en hardware" al jurado.

**Cómo configurar:**

1. Abrir [wokwi.com](https://wokwi.com) → New Project → ESP32
2. Pegar el contenido de `firmware/main.py`, `sensors.py`, `mqtt_client.py`, `display.py`, `config.py`
3. En el archivo `diagram.json` añadir:

```json
{
  "version": 1,
  "author": "Camaleón OS UNIAJC",
  "parts": [
    { "type": "board-esp32-devkit-c-v4", "id": "esp", "top": 0, "left": 0 },
    { "type": "wokwi-ssd1306",            "id": "oled", "top": -120, "left": 100 },
    { "type": "wokwi-led",                "id": "led_g", "top": 50, "left": 200, "attrs": {"color":"green"} },
    { "type": "wokwi-led",                "id": "led_r", "top": 80, "left": 200, "attrs": {"color":"red"} },
    { "type": "wokwi-buzzer",             "id": "buzz", "top": 120, "left": 200 },
    { "type": "wokwi-pushbutton",         "id": "vibration_sim", "top": 150, "left": -50, "attrs": {"label": "SW-420"} },
    { "type": "wokwi-potentiometer",      "id": "tank_a_sim", "top": -50, "left": -100, "attrs": {"label": "Nivel A"} },
    { "type": "wokwi-potentiometer",      "id": "pressure_sim", "top": 0, "left": -100, "attrs": {"label": "Presión"} },
    { "type": "wokwi-potentiometer",      "id": "turbidity_sim", "top": 50, "left": -100, "attrs": {"label": "Turbidez"} }
  ],
  "connections": [
    [ "esp:GPIO34", "vibration_sim:OUT", "green", [] ],
    [ "esp:GPIO21", "oled:SDA", "blue", [] ],
    [ "esp:GPIO22", "oled:SCL", "yellow", [] ],
    [ "esp:GPIO4",  "led_g:A",  "green", [] ],
    [ "esp:GPIO32", "led_r:A",  "red",   [] ],
    [ "esp:GPIO5",  "buzz:1",   "purple",[] ]
  ]
}
```

4. Wokwi soporta **WiFi virtual** (`wifi_connect()`) → el ESP32 simulado conecta a internet real
5. Cambiar `BACKEND_URL` en `config.py` a tu URL pública (ej. ngrok del FastAPI local)

**Ventaja:** muestra ESP32 + sensores virtuales + WiFi real al jurado.

---

### 🥉 Opción 3 — Proteus 8 (simulación profesional)

**Cuándo usar:** entregable formal del reto Electrónica · esquemático profesional para el PDF.

**Componentes a incluir en el esquemático Proteus:**

| Componente | Librería Proteus | Función |
|------------|-----------------|---------|
| **ESP32-WROOM-32** | `MX_ESP32` (custom) | Microcontrolador principal |
| **YF-S201 ×2** | `WATERFLOW` (custom) | Sensores de caudal |
| **HC-SR04 ×2** | `HC-SR04` | Nivel ultrasónico (eq. JSN-SR04T) |
| **MPX5700AP** | `MPX5700AP` o pot+OPAMP | Sensor presión analógico |
| **TSD-10** | Pot + LDR | Simulación turbidez |
| **SW-420** | `BUTTON` con vibración | Vibración tuberías |
| **4-20mA** | Generador corriente | Nivel freático |
| **ADS1115** | `ADS1115` | ADC externo I2C |
| **OLED SSD1306** | `SSD1306` | Display local |
| **LED RGB** | `LED-RGB` | Indicador estado |
| **Buzzer** | `SOUNDER` | Alerta sonora |
| **Resistencias** | Stock | Divisores 10kΩ + 20kΩ + 1kΩ + 2kΩ |
| **Op-Amp LM358** | `LM358` | Acondicionamiento MPX5700 |
| **Capacitores** | 100nF desacople | Filtrado |
| **Cristal 40MHz** | Stock | Oscilador ESP32 |
| **Fuente HLK-PM01** | Bloque genérico | 220V→5V |

**Diagrama de conexiones (texto descriptivo para el esquemático):**

```
ESP32 GPIO34 ◀── R1 (10kΩ) ── R2 (20kΩ) ◀── YF-S201 #1 (Aljibe 1)
ESP32 GPIO35 ◀── R1 (10kΩ) ── R2 (20kΩ) ◀── YF-S201 #2 (Aljibe 2)
ESP32 GPIO25 ──▶ HC-SR04 #1 TRIG (Tanque A)
ESP32 GPIO26 ◀── R1 (1kΩ) ── R2 (2kΩ) ◀── HC-SR04 #1 ECHO
ESP32 GPIO27 ──▶ HC-SR04 #2 TRIG (Tanque B)
ESP32 GPIO14 ◀── divisor ◀── HC-SR04 #2 ECHO
ESP32 GPIO33 ◀── SW-420 OUT (vibración)
ESP32 GPIO21 ◀──▶ I2C SDA (ADS1115 + OLED)
ESP32 GPIO22 ◀──▶ I2C SCL
ESP32 GPIO4  ──▶ LED Verde
ESP32 GPIO32 ──▶ LED Rojo
ESP32 GPIO2  ──▶ LED Azul
ESP32 GPIO5  ──▶ Buzzer (PWM)

ADS1115 Ch0 ◀── LM358 amplificación ◀── MPX5700AP (presión)
ADS1115 Ch1 ◀── R shunt 150Ω ◀── 4-20mA loop (freático)
ADS1115 Ch2 ◀── divisor 4.5V→3.3V ◀── TSD-10 (turbidez)
```

**Conexión Proteus → Camaleón OS:**

Proteus puede usar **VSPE (Virtual Serial Port Emulator)** para emitir datos por puerto serie. Un script Python lee ese puerto y publica vía HTTP al backend:

```python
# scripts/proteus_bridge.py
import serial
import requests
import json

ser = serial.Serial("COM3", 115200)  # ajusta el puerto VSPE
while True:
    line = ser.readline().decode().strip()
    if line.startswith("{"):
        data = json.loads(line)
        requests.post("http://localhost:8000/water/ingest", json=data)
```

**Ventaja:** entregable visualmente profesional para el reto Electrónica.

---

## 3. Cómo se conecta cada parte

### A. Sensores → ESP32 (firmware)

El firmware `main.py` ejecuta dos tareas paralelas:

```python
# Cada 1 segundo (TASK 0)
r = board.read_all()      # lee los 6 sensores
buffer.append(r)

# Cada 30 segundos (TASK 1)
avg = aggregate_buffer(buffer)
status = evaluate_local_status(avg)
display.show_reading(avg, status)
mqtt.publish_reading(avg)  # publica al backend
```

### B. ESP32 → Backend FastAPI

**Vía MQTT (preferido):**
```
ESP32 ──publish──▶ HiveMQ Cloud
                         │
                         ▼
              FastAPI suscriptor MQTT
              → POST /water/ingest internamente
```

**Vía HTTP fallback (si MQTT cae):**
```
ESP32 ──HTTP POST JSON──▶ /water/ingest
```

**Payload exacto:**
```json
{
  "flow1_lmin":    48.3,
  "flow2_lmin":    50.1,
  "level_a_pct":   78.2,
  "level_b_pct":   65.1,
  "pressure_kpa":  318.5,
  "phreatic_m":    7.2,
  "turbidity_ntu": 1.8,
  "vibration":     false,
  "node_id":       "esp32-ptap-01"
}
```

### C. Backend → Dashboard SvelteKit

El dashboard `/agua` se actualiza por dos mecanismos:

1. **Polling cada 15s** — `fetch('/api/water/reading')`
2. **SSE en vivo** — `EventSource('/api/water/agent/stream')` para el log del agente

```typescript
// apps/web-svelte/src/routes/agua/+page.svelte
const eventSource = new EventSource('/api/water/agent/stream');
eventSource.onmessage = (e) => {
  const data = JSON.parse(e.data);
  agentCycle    = data.cycle;
  agentDecision = data.decision;
  // ... actualiza UI reactivamente
};
```

### D. Backend → Telegram Bot

Cuando el agente IA detecta `decision === "critical"`, envía notificación PUSH:

```python
# packages/agents/agentos_agents/graphs/water_orchestrator.py
async def alerting_node(state):
    msg = f"🚨 Camaleón OS — UNIAJC\n..."
    # NotificationDispatcher → bot.send_message(chat_id, msg)
```

Los usuarios además pueden consultar bajo demanda:

```
/agua          → estado completo
/zonas         → consumo por zona
/kpis          → IEH, TPP, CPE
/reporte_agua  → reporte diario
/agente_start  → iniciar agente
/agente_stop   → detener agente
```

---

## 4. Plan de implementación (Sprint del Hackathon)

### Día 1 (7 mayo) — Software + Demo

| Hora | Tarea | Responsable |
|------|-------|-------------|
| 08:00 | Pull repo + setup local (uvicorn + pnpm dev) | Todos |
| 09:00 | Validar `/water/ingest` con simulador PC | Sistemas |
| 10:00 | Probar agente: `POST /water/agent/start` | Sistemas |
| 11:00 | Captura UI dashboard 4 tabs | Sistemas |
| 12:00 | Esquemático Proteus 6 sensores | Electrónica |
| 13:00 | Almuerzo |
| 14:00 | Diagramas UML componentes + estados (draw.io) | Sistemas |
| 15:00 | Diagrama Ishikawa + tabla Lean | Industrial |
| 16:00 | Análisis costo-beneficio en Excel/Notion | Industrial |
| 17:00 | Validación end-to-end + bug fixing | Todos |
| 18:00 | Generar PDF entregable | Industrial |

### Día 2 (8 mayo) — Pitching

| Hora | Tarea |
|------|-------|
| 08:00 | Ensayo del pitch (5 min) |
| 09:00 | Setup demo: laptop + dashboard + Telegram |
| 10:00 | Pitch ante jurado |
| 12:00 | Preguntas y respuestas |
| 14:00 | Resultados |

---

## 5. Comandos útiles para el demo

```bash
# Demo: estado normal
python firmware/simulator_pc.py --scenario normal

# Demo: simular fuga (durante pitch)
python firmware/simulator_pc.py --scenario leak

# Demo: pico de riego
python firmware/simulator_pc.py --scenario peak

# Demo: turbidez alta
python firmware/simulator_pc.py --scenario turbidity

# Iniciar agente IA
curl -X POST http://localhost:8000/water/agent/start

# Ver estado del agente
curl http://localhost:8000/water/agent/status | jq

# Ejecutar 1 ciclo manualmente
curl -X POST http://localhost:8000/water/agent/cycle | jq

# Stream SSE (para ver decisiones en vivo)
curl http://localhost:8000/water/agent/stream

# Generar reporte diario (HTML)
curl http://localhost:8000/water/report/daily | jq

# Ver constantes del campus
curl http://localhost:8000/water/constants | jq
```

---

## 6. Checklist final de demo

- [ ] FastAPI corriendo en `localhost:8000` ✓
- [ ] Dashboard accesible en `localhost:5173/agua` ✓
- [ ] Bot Telegram con token válido respondiendo a `/agua` ✓
- [ ] Simulador `simulator_pc.py` enviando datos cada 5s ✓
- [ ] Agente IA arrancado: ver tab "Agente IA" con ciclos avanzando ✓
- [ ] Botón "Demo: Fuga" inyecta escenario y aparece alerta roja ✓
- [ ] Telegram recibe push automático al inyectar fuga ✓
- [ ] PDF entregable generado en `docs/pdf/` ✓
- [ ] Diagramas UML exportados (PNG/SVG) ✓
- [ ] Esquemático Proteus exportado ✓

---

*Documento técnico de simulación · Camaleón OS · Hackathon UNIAJC 2026*
