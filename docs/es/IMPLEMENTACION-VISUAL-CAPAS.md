# Camaleón OS - Como se ve cada capa implementada (vista visual)

> Este documento muestra **lo que un humano ve y toca** en cada una de las 7
> capas del sistema. Es el complemento visual de
> [ANALISIS-Y-CAPAS-VISUALES.md](ANALISIS-Y-CAPAS-VISUALES.md) (que es la
> arquitectura logica), aqui se ve la **manifestacion fisica** de cada capa.
>
> Hackathon UNIAJC 2026 - v1.0

---

## Indice rapido

| Capa | Donde se ve | Quien la ve | Implementado |
|------|------------|-------------|--------------|
| 1 - Fisica | El campus mismo + planos hidraulicos UNIAJC | Operador, todos | Documentado |
| 2 - Sensado | 6 sensores fisicos + tabla de calibracion | Equipo electronica | Documentado |
| 3 - Edge | Gabinete IP65 con ESP32 + OLED + LED RGB + buzzer | Operador local | Especificado |
| 4 - Comunicacion | MQTT broker + topic structure + fallback HTTP | Sistemas | Codigo + endpoint |
| 5 - Persistencia | API FastAPI + tabla water_readings | Backend developer | Codigo + tests |
| 6 - Inteligencia | Pestana "Inteligencia" del dashboard | Operador, jurado | UI viva |
| 7 - Aplicacion | Dashboard /agua + Bot Telegram + PDFs | Todos | UI viva |

---

## Capa 1 - Fisica (el campus de carne y hueso)

### Lo que existe en UNIAJC Sede Sur

```
                          UNIAJC Sede Sur (38,755 m^2)
                                     |
            +----------------------+--------------------+
            |                      |                    |
        Aljibe 1               Aljibe 2          PTAR Alameda + PTAR Entrada
        (potable)              (potable+riego)   (2 modulos cada una x 1,000 est)
            |                      |
            +----------+-----------+
                       |
                  +----+----+
                  |  PTAP   |  3 filtros: grava+arena, antracita, carbon activado
                  | (2011)  |  cap. 113.56 L/min combinado
                  +----+----+
                       |
              +--------+--------+
              |                 |
          Tank A 36k L      Tank B 16k L
              |                 |
        +-----+----------+------+
        |        |       |      |
      Bloque   Alameda Cafete   Labs
        A                ria
        |        |       |      |
        +---+----+---+---+
            |        |
        Cancha+   Limpieza
        Jardines
            |        |
            +----+---+
                 |
            Aguas grises + negras
                 |
              colector
                 |
            +----+----+
            |         |
         PTAR        PTAR
        Alameda     Entrada
            |         |
        ----+---------+---- vertimiento (Res. 0631/2015)
                 |
            Rio Pance / Cauca
```

### Planos hidraulicos reales (extraidos de tesis Gomez Mina 2022)

**Plano 1 - Detalle interno PTAP** (Ilustracion 22 de la tesis):
- Archivo: [tesis-uniajc/planos/plano-detalle-PTAP.png](../../tesis-uniajc/planos/plano-detalle-PTAP.png)
- Muestra: tanque almacenamiento principal + 3 motobombas con manometros + 2 hidroflows + 3 filtros en cascada (Filtro 1, 2, 3) + tanque cloracion (con bomba dosificadora) + tanque almacenamiento subterraneo + tubo de succion + salida 79 m de 3"
- **Camaleón se conecta:** instrumentando cada filtro con sensores de presion diferencial (detecta saturacion antes del retrolavado), cada motobomba con vibracion (predice falla), tanque cloracion con turbidez post-filtrado.

**Plano 2 - Distribucion hidraulica del campus** (Ilustracion 23 de la tesis):
- Archivo: [tesis-uniajc/planos/plano-distribucion-hidraulica.png](../../tesis-uniajc/planos/plano-distribucion-hidraulica.png)
- Muestra: PTAR (2 ubicaciones: lote-baldio sur y planta electrica sur), Aljibe central, Cancha futbol + voley + zona altura, Coliseo, GYM, Bienestar, Relax center, Salones, Oficinas, Biblioteca, Cafeteria, Cocina, Parqueaderos, Posteta entrada y salida, Punto cero.
- Tuberias coloreadas (rojo, verde, morado, naranja) muestran diferentes redes (potable, residual, riego, retorno).
- **Camaleón se conecta:** modela este layout en el SVG del dashboard `/agua` -> "Mapa del Campus", actualiza el flujo en tiempo real con datos de cada sensor.

---

## Capa 2 - Sensado (los 6 sensores fisicos)

### Tabla de equipamiento con calibracion documentada

| Variable | Modelo | Salida | Rango | Conversion a SI | Costo aprox |
|----------|--------|--------|-------|------------------|--------------|
| Caudal pequeno | YF-S201 (1/2") | Pulsos Hall (Hz) | 1-30 L/min | `L/min = Hz / 7.5` | $25K COP |
| Caudal grande | YF-DN50 | Pulsos Hall (Hz) | 0-400 L/min | `L/min = Hz / 0.2` | $95K COP |
| Presion | MPX5700AP | 0-5V analog | 0-700 kPa | `kPa = (V/5) * 700` | $45K COP |
| Nivel tanque | JSN-SR04T | PWM us | 0-450 cm | `cm = us * 0.0343 / 2` | $30K COP |
| Vibracion | SW-420 + LM393 | Digital ON/OFF | 0/1 | bool directo | $10K COP |
| Nivel freatico | Transductor 4-20mA | Loop industrial | 0-10 m | `m = (mA-4) * 10/16` | $180K COP |
| Turbidez | TSD-10 | 0-4.5V analog | 0-10 NTU | `NTU = 10 * (1 - V/4.5)` | $55K COP |

### Como se ve un nodo IoT instalado (Fase 1 - 1 nodo en PTAP)

```
        +------- GABINETE IP65 (visible en pared PTAP) -------+
        |                                                       |
        |   +---------+   +-----------+   +---------------+    |
        |   |  ESP32  |---|  ADS1115  |---|  6 sensores   |    |
        |   |  WROOM  |   |  ADC 16b  |   |  conectados   |    |
        |   +---------+   +-----------+   +---------------+    |
        |        |              |                              |
        |   +----+----+    +----+----+                         |
        |   |  OLED   |    |  LED RGB|   ESTADO LOCAL          |
        |   | 0.96"   |    |  + buzzer|  (visible sin internet)|
        |   +---------+    +---------+                         |
        |        |                                             |
        |   +----+--------- 220V -> 5V (HLK-PM01) -------+    |
        |   |    + bateria 18650 backup (6 horas)         |    |
        |   +----+----------------------------------------+    |
        |                                                       |
        +-------------------------------------------------------+
                              |
                          WiFi 2.4 GHz / 4G
                              |
                              v
                       (Capa 3 - Edge processing)
```

**Mockup del display OLED** (lo que ve el operador local sin abrir el dashboard):

```
+---------------------------+
| Camaleón Node 01          |
| PTAP UNIAJC               |
+---------------------------+
| Caudal:  28.92 L/min      |
| Presion: 67.4 kPa  [BAJA] |
| Tank A:  72%   Tank B: 78%|
| Freat:   8.04 m           |
| NTU:     1.13     OK      |
+---------------------------+
| MQTT: OK   WiFi: -54 dBm  |
| Last TX: 12s ago          |
+---------------------------+
```

LED RGB:
- Verde fijo: todo OK
- Amarillo parpadeando 1 Hz: alerta moderada
- Rojo parpadeando 2 Hz: critico
- Azul fijo: sin red, modo NVS buffer

Buzzer: 3 beeps cortos en alerta critica.

---

## Capa 3 - Edge / Embebida (firmware ESP32)

### Pseudocodigo del firmware MicroPython (lo que corre dentro del ESP32)

```python
# Core 0 (1 Hz) - lectura de sensores
async def read_loop():
    while True:
        flow1 = read_pulse_counter(GPIO_FLOW1)        # Hz
        flow2 = read_pulse_counter(GPIO_FLOW2)
        pressure = ads.read(channel=0)                  # V
        tank_a_us = read_ultrasonic(TRIG_A, ECHO_A)    # us
        tank_b_us = read_ultrasonic(TRIG_B, ECHO_B)
        vibration = digitalRead(GPIO_VIB)
        phreatic_ma = ads.read(channel=1) * 5.0        # mA
        turbidity = ads.read(channel=2)                 # V

        buffer.append({
            "ts": time.time(),
            "flow1_hz": flow1, "flow2_hz": flow2,
            "pressure_v": pressure,
            "tank_a_us": tank_a_us, "tank_b_us": tank_b_us,
            "vibration": vibration,
            "phreatic_ma": phreatic_ma, "turbidity_v": turbidity,
        })
        if len(buffer) > 30: buffer.pop(0)            # ventana movil 30s

        update_oled(latest_summary())                  # refresh display local
        await asyncio.sleep(1)


# Core 1 (cada 30 s) - publicacion MQTT
async def publish_loop():
    while True:
        await asyncio.sleep(30)
        avg = compute_average(buffer)                  # media + min + max + sigma
        payload = {
            "node_id": "esp32-ptap-01",
            "timestamp": time.time(),
            "flow1_lmin":   avg.flow1_hz / 7.5,
            "pressure_kpa": (avg.pressure_v / 5.0) * 700,
            ...
        }
        try:
            mqtt.publish("campus/uniajc/sensors/esp32-ptap-01", json.dumps(payload))
            led_green()
        except MQTTError:
            try:
                http.post(BACKEND_URL + "/water/ingest", json=payload)
                led_yellow()
            except NetworkError:
                nvs.append(payload)                    # buffer offline 1000 lecturas
                led_blue()
```

### Diagrama de estados del firmware

```
[BOOT] -> [WIFI_CONNECT] -> [MQTT_CONNECT] -> [READY]
                                                  |
                                                  +--> [READING] (Core 0, loop 1Hz)
                                                  |
                                                  +--> [PUBLISHING] (Core 1, loop 30s)
                                                          |
                                                          +-- exito -> READY
                                                          |
                                                          +-- MQTT fail -> [HTTP_FALLBACK]
                                                                              |
                                                                              +-- exito -> READY
                                                                              |
                                                                              +-- network fail -> [NVS_BUFFER]
                                                                                                      |
                                                                                                      +-- WiFi reconectada -> [DRAIN_NVS] -> READY
```

---

## Capa 4 - Comunicacion (MQTT + HTTP fallback)

### Topic structure (lo que se ve en el broker HiveMQ)

```
campus/
  uniajc/
    sensors/
      esp32-ptap-01/         <-- payload con 6 mediciones cada 30s
      esp32-bloque-a-01/     <-- (Fase 2)
      esp32-cancha-01/       <-- (Fase 2)
    actuators/
      EV-A1                  <-- comandos de cierre/apertura
      EV-A2
      EV-RC1
      pump-main              <-- comando standby/auto/eco_drought
    alerts/
      critical               <-- broadcast a operadores
      warning
    reports/
      monthly-irca           <-- subscripcion INVIMA
      quarterly-vertimientos <-- subscripcion CVC
```

### Payload tipo (ejemplo real)

```json
{
  "node_id": "esp32-ptap-01",
  "timestamp": "2026-05-08T03:00:00Z",
  "flow1_lmin": 14.5,
  "flow2_lmin": 13.2,
  "pressure_kpa": 320,
  "tank_a_pct": 72,
  "tank_b_pct": 78,
  "vibration": false,
  "phreatic_m": 8.04,
  "turbidity_ntu": 1.13,
  "wifi_rssi": -54,
  "battery_v": 4.1,
  "uptime_s": 86400
}
```

---

## Capa 5 - Persistencia (FastAPI + Postgres)

### Endpoint que ve el desarrollador

```
GET    /water/reading                    -> ultima lectura simulada o real
GET    /water/status                     -> KPIs + alertas
GET    /water/history?from=...&to=...    -> series temporales
POST   /water/ingest                     -> ingestion (formato esp32_compact)
POST   /water/ingest/universal           -> ingestion (CUALQUIER formato)
GET    /water/ingest/formats             -> lista de formatos soportados
GET    /water/agent/status               -> estado del agente y ciclos
POST   /water/agent/start                -> inicia ciclos autonomos
POST   /water/agent/cycle                -> ejecuta 1 ciclo manualmente
POST   /water/agent/ask                  -> pregunta libre al agente conversacional
GET    /water/agent/insights             -> 3 insights generados por LLM
POST   /water/mitigate/auto              -> ejecuta trigger compuesto (incluye drought_mode)
GET    /water/mitigate/valves            -> estado de las 8 EV
GET    /water/mitigate/impact            -> impacto acumulado (L, COP, CO2)
```

### Lo que ve el DBA (schema Postgres)

```sql
water_readings  (BIGSERIAL, ts, node_id, sensor_id, sensor_type,
                 value DOUBLE, unit, raw JSONB, quality, metadata JSONB)
                INDEX (ts DESC), (node_id, sensor_id, ts DESC), (quality)

alerts          (BIGSERIAL, ts, level, sensor_id, message, action,
                 acknowledged_by, resolved_at)

mitigation_actions (BIGSERIAL, ts, trigger, severity, summary,
                    actions_taken JSONB, impact JSONB, telegram_msg, ot_id)

valves_state    (valve_id PK, state, last_change_ts, controllable)

kpis_hourly     (hour TIMESTAMPTZ, ieh, tpp, cpe, ica)  -- materialized view

reports         (id, ts, type, period, pdf_url, sha256, sent_to JSONB)
```

---

## Capa 6 - Inteligencia (5 agentes + IA conversacional)

### Lo que ve el jurado en la pestana "Inteligencia"

**Bloque 1 - WaterMonitorAgent**
- Boton: "Iniciar agente" / "Detener"
- Estado: EN MONITOREO / DETENIDO con LED pulsante
- Contador de ciclos, ultima decision (OK / WARNING / CRITICAL)
- Lista de los 5 agentes especializados (Orchestrator, SystemsAgent, SensorAgent, IndustrialAgent, MitigationAgent) con su estado individual
- Boton "Ejecutar ciclo unico"

**Bloque 2 - Log de decisiones**
- Cronologico inverso, ultimos 20 ciclos: timestamp, ciclo, decision, issue
- Maquina de estados visual: IDLE -> MONITORING -> ANALYZING -> DECIDING

**Bloque 3 - Plan ante fenomeno El Nino (NUEVO)**
- Header amber con badge "normal" o "SEQUIA INMINENTE" (si freatico < 5m)
- 3 indicadores ambientales:
  - Pronostico IDEAM 30d: "El Nino moderado · prob 78%"
  - Nivel freatico actual (auto-color rojo si < 5m)
  - Lluvia 7 dias acumulada vs media historica
- **Plan automatico de 6 acciones** numeradas con su impacto cuantificado
- **Boton accion "Activar modo SEQUIA ahora"** -> POST /water/mitigate/auto {trigger: "drought_mode"}
- Boton secundario "Solo reducir extraccion (-70%)"
- Footer: "Impacto proyectado: -25% consumo total"

**Bloque 4 - Analisis del Agente (insights IA)**
- 3 cards generados por el LLM con titulo + descripcion + severidad
- Boton "refresh" para regenerar

**Bloque 5 - Pregunta al Agente (chat conversacional)**
- Input + 5 botones de preguntas sugeridas
- Conversacion persistente mientras dura la sesion
- Cada respuesta tiene timestamp y trazabilidad de fragmentos

### Como responde el agente conversacional (ejemplo real, datos en vivo)

```
Pregunta: "que pasa cuando se aproxima el fenomeno del nino?"

Respuesta del agente:
> Plan ante fenomeno del Nino IMPLEMENTADO en la pestana Inteligencia:
> el trigger drought_mode combina 6 acciones: 1) presion nocturna 38->25 PSI,
> 2) cierra EV-RC1 (riego), 3) bomba a modo eco_drought (-70% extraccion),
> 4) broadcast Telegram a 8,234 usuarios, 5) pantallas LED ALERTA SEQUIA,
> 6) reporte automatico CVC. Impacto proyectado: -25% consumo total,
> 10,400 L/dia ahorrados.
```

---

## Capa 7 - Aplicacion (lo que ve cada usuario final)

### Operador de mantenimiento UNIAJC

Pantalla principal: `/agua` -> tab "Operacion"
- 4 KPIs grandes (IEH, TPP, CPE, ICA) con semaforo
- Niveles de tanques A y B con animacion
- Caudal, presion, freatico, turbidez en cards
- Lista de alertas activas con accion sugerida

Notificaciones: Telegram bot
- Push automatico cuando hay alerta critica
- Reporte diario 18:00 PM con PDF adjunto
- Comandos: /agua, /zonas, /kpis, /alertas, /tanques

### Estudiante / comunidad universitaria

Pantalla publica: `/agua` -> tab "Comunidad"
- Smart Water Ledger: ranking de edificios por ahorro mensual
- QR para reportar fugas (en cada bano)
- Creditos acumulados de su edificio
- Informacion sobre el plan ante El Nino

### Administrador / decanato

PDF mensual generado automaticamente:
- Resumen ejecutivo: TPP, IEH, costo evitado
- Cumplimiento normativo por norma
- Acciones de mitigacion del periodo (con OT ID)
- Adjunto Parquet con datos crudos para auditoria

### Inspector externo (INVIMA / CVC)

Endpoint publico: `/water/reports/irca/2026-04`
- PDF firmado con SHA-256
- Contiene los 7 parametros de Resolucion 2115/2007
- Datos crudos en Parquet anexo (Ley 1712/2014)

---

## Resumen visual de "lo implementado vs lo proyectado"

| Capa | Componente | Implementado HOY | En el PDF de fases |
|------|-----------|------------------|---------------------|
| 1 | Layout campus en SVG | OK (mapa interactivo `/agua`) | - |
| 1 | Planos hidraulicos extraidos | OK ([planos PNG](../../tesis-uniajc/planos)) | - |
| 2 | Calibracion 6 sensores documentada | OK (registry.py) | - |
| 2 | Hardware fisico instalado | NO (Fase 2 - mes 1) | Mes 1 |
| 3 | Firmware ESP32 escrito | parcial (pseudocodigo + simulator_pc.py) | Mes 1 |
| 4 | Endpoint MQTT/HTTP recepcion | OK (/water/ingest + /water/ingest/universal) | - |
| 4 | Broker HiveMQ configurado | NO (free tier listo cuando se despliegue) | Mes 1 |
| 5 | API FastAPI | OK (todos los endpoints listados) | - |
| 5 | Postgres + Supabase | NO (modo demo en RAM ahora) | Mes 1 |
| 6 | Plan El Nino UI + accion | **OK (recien agregado)** | - |
| 6 | 5 agentes coordinados | OK (codigo + dashboard) | - |
| 6 | LLM cascade Groq->OpenRouter->Gemini | OK (con fallback local) | - |
| 7 | Dashboard SvelteKit | OK (`/agua` con 6 tabs) | - |
| 7 | Bot Telegram | OK (codigo en `apps/telegram/`) | Mes 1 (deploy) |
| 7 | PDFs auditables | OK (WeasyPrint en backend) | - |

> Lo que esta marcado **NO** son cosas que requieren contratacion (compra de
> hardware, deploy en infra). El **codigo del sistema esta 100% listo** para
> consumir esos recursos cuando esten disponibles.

---

*v1.0 - Hackathon UNIAJC 2026 - github.com/JFrangel/Camaleón-OS*
