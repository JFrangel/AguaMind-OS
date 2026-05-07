# AguaMind OS — Implementación Técnica de Sensores

> Documento de ingeniería detallada: dónde se instala cada sensor, con qué
> herramienta, qué calibración requiere, qué resistencias de acondicionamiento
> y cuál es el protocolo de validación pre y post instalación.

---

## 1. Mapa de Implementación — Punto a Punto

```
┌───────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│           UNIAJC SEDE SUR — DISTRIBUCIÓN DE NODOS AGUAMIND                  │
│                                                                             │
│   Acuífero Río Pance                                                        │
│   (~5,000,000 L)                                                            │
│        │                                                                     │
│        ├─ POZO 1 ────► Aljibe 1 ──► [NODO 1] ──┐                          │
│        │              (~12m prof)   YF-S201    │                            │
│        │                            4-20mA     │                            │
│        │                                       ▼                            │
│        │                                    PTAP                            │
│        │                                  [NODO 2]                          │
│        │                                  MPX5700AP                         │
│        │                                  TSD-10                            │
│        │                                  SW-420 ×3                         │
│        │                                       │                            │
│        │                                       ▼                            │
│        │                                ┌─Tanque A 36k L─┐                  │
│        │                                │  [NODO 3]      │                  │
│        │                                │  JSN-SR04T     │                  │
│        │                                │  Termistor     │                  │
│        │                                └────────┬───────┘                  │
│        │                                         │                          │
│        ├─ POZO 2 ────► Aljibe 2 ──► [NODO 4] ──┤                          │
│                       (~15m prof)   YF-S201     │                          │
│                                     4-20mA      │                          │
│                                                 ▼                          │
│                                          ┌─Tanque B 16k L─┐                │
│                                          │  [NODO 5]      │                │
│                                          │  JSN-SR04T     │                │
│                                          └────────┬───────┘                │
│                                                   │                        │
│                                  ┌────────┬───────┼──────┬─────────┐       │
│                                  ▼        ▼       ▼      ▼         ▼       │
│                              [NODO 6]  [NODO 7] [NODO 8] [NODO 9] [NODO 10]│
│                              Bloque A  Alameda  Cafetería Labs    Riego    │
│                              YF-S201   YF-S201  YF-S201  YF-S201  Higróm.  │
│                              EV-A1     EV-AL1   EV-CAF1  EV-LAB1  EV-RC1   │
│                              SW-420    SW-420   SW-420   SW-420   YF-DN50  │
│                                                                             │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Detalle de Cada Nodo

### NODO 1 — Captación Aljibe 1

| Parámetro | Especificación |
|-----------|----------------|
| **Ubicación** | Boca del aljibe 1, ~50 m al sur del bloque administrativo |
| **Coordenadas** | 3.396° N, -76.555° O (aprox · ajustar con plano real) |
| **Profundidad** | Sensor freático sumergido a 8 m bajo brocal |
| **Tubería destino** | PVC presión Ø 2" → entrada PTAP filtros |
| **Sensores** | YF-S201 (caudal salida) + transductor 4-20mA (nivel freático) |
| **Actuadores** | — (sólo medición) |

**Procedimiento de instalación:**
1. Cerrar válvula de salida del aljibe (pre-PTAP).
2. Cortar tubería PVC en sección recta (mínimo 10 cm aguas arriba y abajo del sensor).
3. Insertar YF-S201 con uniones roscadas 1/2" NPT y teflón industrial.
4. Sumergir transductor 4-20mA con cable estanco PVC submarino, fijar a tubo de PVC vertical.
5. Conectar shunt 150Ω en gabinete IP65 a 1 m sobre el suelo.
6. Calibrar caudal con el método de aforo volumétrico (cubeta 20 L cronometrada).

**Acondicionamiento eléctrico:**
```
YF-S201 (rojo +5V, negro GND, amarillo señal)
  └── Divisor R1=10kΩ, R2=20kΩ → 3.33V GPIO 34 ESP32 (interrupción)
  └── Frecuencia esperada: 0–225 Hz (1–30 L/min)
  └── Calibración: F (Hz) = 7.5 × Q (L/min)

Transductor 4-20mA submersible
  ├── Loop: ESP32 (no alimenta el loop)
  ├── Fuente externa 24V DC (alimenta el lazo)
  ├── Resistencia shunt 150Ω → caída 0.6V (4mA) a 3V (20mA)
  └── ADS1115 Ch1 (rango ±4.096V) → 0–10 m H₂O
```

---

### NODO 2 — PTAP (Planta de Tratamiento)

| Parámetro | Especificación |
|-----------|----------------|
| **Ubicación** | Edificio PTAP existente (caseta junto a aljibes) |
| **Sensores** | MPX5700AP (presión post-filtros) + TSD-10 (turbidez) + SW-420 ×3 (vibración en uniones críticas) |
| **Actuadores** | — |

**Procedimiento:**
1. Instalar MPX5700AP con T-junction roscado en línea de salida del filtro de carbón activado.
2. TSD-10 con cápsula transparente cortando 5 cm de tubería en derivación; usar válvula de bypass para mantenimiento.
3. SW-420 con cinta vibración + epoxy industrial en 3 codos críticos (entrada filtro arena, unión filtro carbón, salida pulido).

**Acondicionamiento:**
```
MPX5700AP (Vs=5V, Vout=0.2–4.7V)
  ├── Buffer LM358 (impedancia adaptación)
  ├── Divisor 5V→3.3V (R1=10kΩ, R2=20kΩ)
  └── ADS1115 Ch0 (16-bit, gain=1)
  └── Conversión: P (kPa) = (V/Vs - 0.04) / 0.0012858

TSD-10 (Vs=5V, salida 0–4.5V)
  ├── Divisor 4.5V→3.3V (R1=10kΩ, R2=22kΩ)
  └── ADS1115 Ch2
  └── Curva: NTU = -1120.4·V² + 5742.3·V - 4352.9 (fabricante)

SW-420 (Vs=3.3V o 5V tolerante, salida digital)
  ├── Pull-up interno ESP32 GPIO 33
  └── Lectura: 50 muestras a 5 kHz, anomalía si > 30% HIGH
```

---

### NODO 3 — Tanque A (Principal 36,000 L)

| Parámetro | Especificación |
|-----------|----------------|
| **Ubicación** | Tapa superior del tanque A, accesible por escalera fija |
| **Sensores** | JSN-SR04T (nivel ultrasónico impermeable) + DS18B20 (temperatura agua) |
| **Actuadores** | Relay SSR 30A para bomba (ON/OFF) + EV-OUT-A salida tanque |

**Cálculos del tanque:**
- Geometría: vertical cilíndrico
- Altura interna útil: 1.80 m (180 cm)
- Diámetro interno: 5.05 m
- Volumen total: π × (5.05/2)² × 1.80 ≈ 36.05 m³ → 36,050 L
- Umbral bomba ON: 24,000 L → 67% nivel → distancia desde tapa = 60 cm
- Umbral crítico: 12,000 L → 33% nivel → distancia desde tapa = 120 cm

**Instalación JSN-SR04T:**
1. Perforar Ø 22mm en tapa, sellar con prensaestopas + silicona neutra.
2. Sensor a 5 cm sobre el nivel máximo (riesgo de salpicadura).
3. Cable apantallado 4 hilos hasta gabinete ESP32 (máx 4 m).
4. TRIG y ECHO con divisor resistivo (1kΩ + 2kΩ) para 3.3V.

**Calibración:**
```python
# distancia_cm = (echo_us × 0.0343) / 2
# nivel_pct = ((tank_height - distancia) / tank_height) × 100

# Validación de campo:
#   1. Medir distancia con cinta métrica desde sensor al espejo de agua
#   2. Comparar con lectura ESP32
#   3. Ajustar TANK_A_HEIGHT_CM si discrepancia > 2 cm
```

---

### NODO 4 — Aljibe 2 (con derivación a riego)

Idéntico al NODO 1 pero con esta diferencia clave:

> **Aljibe 2 tiene derivación directa a riego sin tratamiento.**
> Por eso instalamos UNA EV en T-junction para poder cortar el flujo
> al riego cuando el agente IA detecte sobreconsumo (>13,000 L/día).

```
Aljibe 2 ──▶ T-junction ──┬── PTAP (con tratamiento)
                          │
                          └── EV-RC1 ──▶ Riego cancha (sin tratar)
```

---

### NODO 6 — Bloque A (entrada principal)

| Parámetro | Especificación |
|-----------|----------------|
| **Ubicación** | Cuarto de hidráulica del bloque A (planta baja) |
| **Sensores** | YF-S201 (caudal entrada bloque) + SW-420 (vibración tubería principal) |
| **Actuadores** | EV-A1 1/2" 12V DC (corte de flujo a baños) |

**Cobertura del nodo:**
- Aulas piso 1, 2 y 3
- Baños hombres + mujeres por piso (6 baños totales)
- Lavamanos comunes (12 puntos)
- Bebederos (3 unidades)

**Instalación EV-A1:**
1. Aguas abajo del medidor YF-S201, antes de la primera derivación.
2. Válvula con conexión 1/2" hembra-hembra, montada en posición horizontal.
3. Bobina alimentada con 12V DC desde fuente HLK-PM12 dedicada (9 W).
4. Driver MOSFET IRLZ44N + diodo 1N4007 (snubber) en colector ESP32 GPIO 26.
5. Tiempo de actuación: 200 ms (rápido).

**Lógica de corte autónomo:**
```python
# Reglas del MitigationAgent para Bloque A:
SI (es_horario in [22:00 - 06:00]) Y (caudal_bloque > 5 L/min):
    → cerrar EV-A1 (nadie debería consumir agua de noche)
    → pasados 5 min sin consumo: re-abrir
    → si insiste: alerta crítica + EV permanece cerrada
```

---

### NODO 10 — Riego Cancha + Jardines

| Parámetro | Especificación |
|-----------|----------------|
| **Sensores** | YF-DN50 (caudal alta capacidad 5–150 L/min) + Higrómetro suelo HW-080 ×3 |
| **Actuadores** | EV-RC1 solenoide 1" 24V AC (industrial) |

**Higrómetros distribuidos:**
- HW-080 #1: zona 1 cancha (cabecera)
- HW-080 #2: zona 2 cancha (centro)
- HW-080 #3: jardín perimetral

**Lógica de riego inteligente:**
```python
# Riego sólo si TODAS las condiciones se cumplen:
SI (humedad_suelo_promedio < 60%) Y         # suelo seco
   (hora in [22:00 - 05:00]) Y              # nocturno (sin evaporación)
   (caudal_total_campus < 50%) Y            # no compite con consumo punta
   (presión_freática > 5 m):                # acuífero saludable
    → abrir EV-RC1 durante 30 min
    → monitorear humedad cada 5 min
    → cerrar cuando humedad > 80%
```

---

## 3. Bill of Materials (BOM) Completo

### Por nodo AguaMind Node v1 (instalación PTAP típica)

| Categoría | Item | Modelo / Spec | Cant | Costo unit COP | Subtotal |
|-----------|------|---------------|------|----------------|----------|
| **MCU** | Microcontrolador | ESP32-WROOM-32 DevKit | 1 | 35,000 | 35,000 |
| **MCU** | Conversor ADC | ADS1115 16-bit I2C | 1 | 15,000 | 15,000 |
| **Sensores** | Caudalímetro | YF-S201 1/2" | 2 | 25,000 | 50,000 |
| **Sensores** | Caudalímetro grande | YF-DN50 (sólo NODO riego) | 1 | 95,000 | 95,000 |
| **Sensores** | Nivel ultrasónico | JSN-SR04T impermeable | 2 | 30,000 | 60,000 |
| **Sensores** | Presión | MPX5700AP | 1 | 45,000 | 45,000 |
| **Sensores** | Nivel freático | Transductor sumergible 4-20mA 10m WC | 1 | 180,000 | 180,000 |
| **Sensores** | Turbidez | TSD-10 / SEN0189 DFRobot | 1 | 55,000 | 55,000 |
| **Sensores** | Vibración | SW-420 + LM393 | 3 | 10,000 | 30,000 |
| **Sensores** | Higrómetro suelo | HW-080 capacitivo | 3 | 8,000 | 24,000 |
| **Sensores** | Temperatura | DS18B20 sumergible | 1 | 12,000 | 12,000 |
| **Actuadores** | Electroválvula | 1/2" 12V DC NC | 2 | 80,000 | 160,000 |
| **Actuadores** | Electroválvula industrial | 1" 24V AC riego | 1 | 220,000 | 220,000 |
| **Actuadores** | Relay SSR | 30A 240V (bomba) | 1 | 25,000 | 25,000 |
| **Actuadores** | Driver MOSFET | IRLZ44N + diodo 1N4007 | 2 | 4,000 | 8,000 |
| **Indicadores** | OLED display | SSD1306 128×64 I2C | 1 | 18,000 | 18,000 |
| **Indicadores** | LED RGB cátodo común | 5mm difuso | 1 | 2,000 | 2,000 |
| **Indicadores** | Buzzer activo | 5V 85dB | 1 | 6,000 | 6,000 |
| **Energía** | Fuente principal | HLK-PM12 220V→12V/2A | 1 | 35,000 | 35,000 |
| **Energía** | Convertidor | LM7805 5V/1A | 1 | 8,000 | 8,000 |
| **Energía** | Convertidor | AMS1117-3.3V | 1 | 4,000 | 4,000 |
| **Energía** | Batería respaldo | 18650 3.7V 2600mAh | 2 | 22,000 | 44,000 |
| **Energía** | Cargador litio | TP4056 USB-C | 1 | 8,000 | 8,000 |
| **Pasivos** | Resistencias varias | 1%, 1/4W (kit) | 1 | 15,000 | 15,000 |
| **Pasivos** | Condensadores | 100nF, 10µF, 100µF | 1 | 12,000 | 12,000 |
| **Pasivos** | Op-Amp | LM358 dual | 2 | 3,500 | 7,000 |
| **Mecánico** | Gabinete IP65 | 200×150×100 mm | 1 | 80,000 | 80,000 |
| **Mecánico** | Prensaestopas | PG7, PG9 (varios) | 6 | 3,000 | 18,000 |
| **Mecánico** | Cable apantallado | 4×0.5mm² (10 m) | 1 | 25,000 | 25,000 |
| **Mecánico** | PCB | Universal 7×9 cm | 2 | 8,000 | 16,000 |
| **Cone­xiones** | Borneras | 5mm passo (kit 20) | 1 | 18,000 | 18,000 |
| **Cone­xiones** | Conectores | JST XH (varios) | 1 | 12,000 | 12,000 |
| **Cone­xiones** | Mangueras flexibles | acero inox 1/2" | 4 | 22,000 | 88,000 |
| | | | | | |
| | **TOTAL HARDWARE** | | | | **~$1,431,000 COP** |

### Software y servicios (todo gratis con plan free)

| Item | Costo |
|------|-------|
| Backend FastAPI | $0 (open source) |
| LangGraph + agentes IA | $0 |
| Supabase PostgreSQL (500 MB) | $0/mes |
| HiveMQ Cloud MQTT | $0/mes |
| Vercel hosting dashboard | $0/mes |
| Koyeb backend (1 nano) | $0/mes |
| LLM Cascade (Groq + Gemini + OpenRouter) | $0 |
| Telegram Bot API | $0 |
| **Total software/mes** | **$0 COP** |

### Mano de obra instalación (estimada)

| Concepto | Horas | Tarifa | Total |
|----------|-------|--------|-------|
| Diseño electrónico + PCB | 16 | $35,000 | $560,000 |
| Armado y soldadura | 24 | $25,000 | $600,000 |
| Programación firmware | 32 | $40,000 | $1,280,000 |
| Instalación in situ | 12 | $30,000 | $360,000 |
| Pruebas y calibración | 8 | $30,000 | $240,000 |
| **Total servicios** | | | **$3,040,000 COP** |

### Inversión total Fase 1 (1 nodo PTAP)

| Concepto | Valor |
|----------|-------|
| Hardware | $1,431,000 |
| Mano de obra | $3,040,000 |
| Imprevistos (10%) | $447,000 |
| **TOTAL** | **$4,918,000 COP** |
| **TOTAL si auto-construido** | **$1,431,000 COP** |

> El equipo del hackathon construye el primer nodo como TFG (Trabajo de Final de
> Grado), reduciendo costo de mano de obra a $0 → inversión real $1,431,000 COP.

---

## 4. Protocolo de Pruebas Pre-Despliegue

### Test 1 — Sensor de caudal (YF-S201)

```
Equipo: Cubeta graduada 20 L, cronómetro, fuente de agua a presión conocida.

Procedimiento:
  1. Conectar YF-S201 en línea con manguera flexible
  2. Abrir flujo a caudal conocido (ej. 5 L/min con regulador)
  3. Llenar cubeta 20 L y cronometrar
  4. Q_real = 20 L / tiempo_min
  5. Comparar con lectura ESP32

Criterio aceptación: error < 5%
```

### Test 2 — Nivel ultrasónico (JSN-SR04T)

```
Equipo: Tanque de prueba 200L con escala graduada cada 10 cm.

Procedimiento:
  1. Llenar tanque a 5 niveles (20, 40, 60, 80, 100 cm desde fondo)
  2. Medir distancia ESP32 desde tapa
  3. Calcular: nivel_real = altura_tanque - distancia
  4. Comparar con escala visual

Criterio: error absoluto < 2 cm en cada nivel
```

### Test 3 — Presión (MPX5700AP)

```
Equipo: Compresor con manómetro patrón, regulador 0–600 kPa.

Procedimiento:
  1. Conectar MPX a entrada del compresor con manómetro Y
  2. Aplicar 6 presiones: 100, 200, 300, 400, 500, 600 kPa
  3. Comparar lectura ESP32 vs manómetro patrón

Criterio: error < 3% del fondo de escala
```

### Test 4 — Detección de fuga acústica (SW-420)

```
Equipo: Tubo PVC 1/2" con válvula reguladora; martillo de goma.

Procedimiento:
  1. Fijar SW-420 con cinta + epoxy en codo de tubería
  2. Generar 3 escenarios:
     a) Flujo normal silencioso → SW-420 debe leer OFF
     b) Golpe ligero martillo de goma → SW-420 debe leer ON
     c) Apertura súbita válvula (golpe ariete) → ON

Criterio: detección > 90% de eventos b y c
```

### Test 5 — Mitigación end-to-end

```
Procedimiento:
  1. Iniciar agente: POST /water/agent/start
  2. Inyectar fuga: POST /water/simulate {"scenario":"leak"}
  3. Verificar:
     ✓ TPP > 20% en dashboard en < 5 segundos
     ✓ Push Telegram recibido en < 10 segundos
     ✓ EV-A2 muestra estado "closed" en mapa
     ✓ Impacto evitado registrado en /water/mitigate/impact

Criterio: todas las condiciones se cumplen
```

---

## 5. Mantenimiento Preventivo

| Componente | Frecuencia | Acción |
|------------|------------|--------|
| YF-S201 | Cada 6 meses | Limpiar rotor (sedimentos), validar pulsos |
| JSN-SR04T | Cada 12 meses | Inspeccionar membrana, recalibrar |
| MPX5700AP | Cada 6 meses | Punto-cero con presión atmosférica |
| TSD-10 | Cada 3 meses | Limpiar lente óptico con agua destilada |
| 4-20mA freático | Cada 12 meses | Extraer, inspeccionar empaquetadura |
| SW-420 | Cada 12 meses | Verificar fijación epoxy |
| Electroválvulas | Cada 6 meses | Ciclar 10× para evitar bloqueo solenoide |
| Batería 18650 | Cada 24 meses | Reemplazar (degradación capacidad) |
| Gabinete IP65 | Cada 6 meses | Inspeccionar empaques, drenajes |
| ESP32 firmware | OTA continuo | Actualización over-the-air vía MQTT |

---

## 6. Plan de Seguridad Eléctrica e Hídrica

### Eléctrica
- Todos los gabinetes con tierra física conectada (RETIE)
- Diferencial de 30 mA por nodo
- Fusibles 2A en línea de 12 V DC, 1A en línea 5 V
- Optocopladores 4N35 entre actuadores AC y ESP32

### Hídrica
- Válvulas redundantes (manual + electrónica) para que mantenimiento pueda
  trabajar sin depender del agente IA
- Override físico con interruptor para "modo mantenimiento" que ignora
  las decisiones del agente
- Bypass mecánico en cada electroválvula crítica

---

## 7. Cronograma Detallado de Implementación

### Sprint 1 — Diseño (1 semana)
```
Día 1-2  Validación de planos + medición de tuberías existentes
Día 3-4  Diseño esquemático en KiCad
Día 5    Pedido de componentes (Mercado Libre / SR Components)
Día 6-7  Diseño PCB
```

### Sprint 2 — Construcción Bench (2 semanas)
```
Sem 1  Recibir componentes + soldadura PCB
Sem 2  Programación firmware + tests laboratorio (cubeta)
```

### Sprint 3 — Instalación PTAP (1 semana)
```
Día 1  Reunión con servicios generales UNIAJC
Día 2  Corte programado de agua + instalación mecánica
Día 3  Cableado eléctrico + WiFi
Día 4  Calibración in situ
Día 5  Validación end-to-end + capacitación operador
```

### Sprint 4 — Operación (4 semanas)
```
Mes 1  Recolección datos basales + ajustes finos
       Reporte semanal a rectoría
       Análisis ROI real vs proyectado
```

---

*Documento técnico de implementación · AguaMind OS · Hackathon UNIAJC 2026*
*Para preguntas específicas: ver docs/es/PREGUNTAS-ASESORIA.md*
