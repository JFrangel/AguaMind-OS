# AguaMind OS — Documento Maestro

**Sistema Inteligente de Gestión Hídrica · UNIAJC Sede Sur**

> **Hackathon UNIAJC 2026 · Facultad de Ingeniería · 7-8 de mayo**
> Versión post-asesoría con jurados (mayo 7) — incorpora feedback recibido.
> Repositorio: [github.com/JFrangel/AguaMind-OS](https://github.com/JFrangel/AguaMind-OS)

---

## Tabla de Contenido

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Feedback del Jurado y Ajustes](#2-feedback-del-jurado-y-ajustes)
3. [El Problema Real](#3-el-problema-real)
4. [Datos Validados (4 tesis UNIAJC)](#4-datos-validados-4-tesis-uniajc)
5. [Solución AguaMind OS](#5-solución-aguamind-os)
6. [Estrategia de Datos — el corazón de la propuesta](#6-estrategia-de-datos)
7. [Sensores e Instrumentación](#7-sensores-e-instrumentación)
8. [Modelo 3D del Campus](#8-modelo-3d-del-campus)
9. [Estrategias derivadas de los datos](#9-estrategias-derivadas-de-los-datos)
10. [Sistema Multi-Agente IA](#10-sistema-multi-agente-ia)
11. [Mitigación Activa](#11-mitigación-activa)
12. [Cumplimiento Normativo](#12-cumplimiento-normativo)
13. [Plan por Fases (15 años)](#13-plan-por-fases-15-años)
14. [Costo-Beneficio + ROI](#14-costo-beneficio--roi)
15. [Impacto + ODS](#15-impacto--ods)
16. [Pitch 5 minutos](#16-pitch-5-minutos)
17. [Q&A Anticipado](#17-qa-anticipado)
18. [Roles del Equipo](#18-roles-del-equipo)
19. [Referencias](#19-referencias)

---

## 1. Resumen Ejecutivo

**AguaMind OS es una plataforma de caracterización inteligente de agua** que combina sensores IoT distribuidos, un sistema multi-agente de IA y un modelo 3D interactivo del campus para **convertir datos en estrategias de mitigación** que protegen el recurso hídrico, evitan sanciones normativas y empoderan a la comunidad universitaria.

### Diferenciadores clave (post-feedback jurado)

> *El jurado fue claro: "todos van a poner sensores. La diferencia está en lo que hacen con los datos."*

1. **Modelo 3D del campus** — visualización de tuberías + identificación de fugas por zona/hora
2. **Estrategias derivadas de datos** (NO predicciones) — concientización, diferenciación potable/riego, planes de sequía
3. **Protocolo de datos riguroso** — frecuencia de muestreo, almacenamiento auditable, transmisión confiable
4. **Sistema 15 años** — escalable a universidad de 12,000 usuarios proyectados a 2030
5. **Honra trabajo previo** — integra 4 tesis UNIAJC (Caycedo, Sánchez, Gómez, Aristizábal)

### Inversión total

| Fase | Inversión | Beneficio anual proyectado |
|------|-----------|----------------------------|
| Fase 1 piloto (1 nodo PTAP) | $1.4M COP | $3M+ ahorro directo |
| Fase 2 expansión (5 nodos) | $5.4M COP | $11.6M ahorro + protección legal |
| Fase 3 sensorización masiva | $9.2M COP | $18M ahorro + cumplimiento normativo |

---

## 2. Feedback del Jurado y Ajustes

### Lo que el jurado señaló

| Comentario jurado | Ajuste en AguaMind OS |
|-------------------|------------------------|
| *"Todos van a poner sensores, la innovación está en qué haces con los datos"* | Reescribir innovación: **estrategias de mitigación**, no predicción |
| *"No digan 'predecir' si ya están midiendo. Eso es contradictorio"* | Eliminar lenguaje "predictivo" → cambiar por **caracterización + estrategias** |
| *"Modelo 3D para detectar dónde está la fuga"* | Implementar mapa SVG con zonas + ubicación exacta de fugas |
| *"PTAR tiene desborde — sale más agua que la que entra"* | Balance entrada-salida por edificio (ya implementado) |
| *"Estrategias durante fenómeno del Niño"* | Plan de acción ante sequía + diferenciación potable/riego |
| *"Concientización con ministerio universitario"* | Smart Water Ledger conecta con bienestar universitario |
| *"Sensores precisos, no los más baratos ni caros"* | Sensores comerciales validados + especificación de precisión |
| *"Verifiquen conectividad WiFi en cada punto"* | Plan de contingencia: WiFi + 4G + cache local |
| *"Universidad va a crecer 15 años"* | Plan de escalabilidad documentado a 2040 |
| *"Cada cuánto toman datos? ¿Cómo los almacenan?"* | Protocolo formal: 30s muestreo, MQTT + HTTP fallback, Supabase |
| *"Pueden haber soluciones costo-beneficio más económicas"* | Mantener método "tanques nocturnos" como complemento de bajo costo |
| *"5 minutos para presentar TODO"* | Pitch reescrito con foco en estrategias |
| *"Lean Manufacturing aplicado PTAP UNIAJC ya existe"* | Integración con tesis Sánchez Sotelo (2021) — datos validados |
| *"En el panel cambien 'agente' por 'lo que aporta'"* | Renombrar tab "Agente IA" → "Inteligencia operativa" |

### Lema corregido del proyecto

**Antes:** *"AguaMind OS predice fugas"*
**Después:** *"AguaMind OS caracteriza el sistema hídrico y deriva estrategias de mitigación accionables"*

---

## 3. El Problema Real

### Datos del campus UNIAJC Sede Sur

```
Población:           3,230 estudiantes/día · 8,234 usuarios totales
Crecimiento:         +59% entre 2015-2019 (Caycedo & Jaramillo 2021)
Proyección 2030:     ~5,800 estudiantes / ~12,000 usuarios totales
Área:                38,755.88 m² (zonas Alameda + Parquesoft)
Fuentes de agua:     161 puntos (51 sanitarios + 53 lavamanos + ...)
Distribución:        Parquesoft 67% · Alameda 33%
PTAP instalada:      2011 — sin instrumentación
Caudal entrada:      113.56 L/min combinado · 5.56 L/seg validado
Producción diaria:   43,819 L medidos (Sánchez Sotelo 2021)
Pérdidas medidas:    1,587 L/día = 579.5 m³/año
Costo desperdicio:   $1.1M COP/año en agua + $1.1M operario + $0.8M cloro
```

### Problemas críticos diagnosticados

```
PTAP (Planta Tratamiento Agua Potable):
  P1. Calidad del agua FUERA de norma (Resolución 2115/2007):
        - Nitratos hasta 22.5 mg/L (límite 10) → 2.25× sobre
        - Fosfatos hasta 1.91 mg/L (límite 0.5) → 3.82× sobre
        - Cloro residual variable 0.28-2.10 ppm
  P2. Sin sistema de medición (desde 2011)
  P3. Pérdidas no contabilizadas (medidas: 1,587 L/día)
  P4. Bombeo sin demanda real (ciclos 3-4 min innecesarios)
  P5. Acuífero sin monitoreo (Decreto 1076/2015 incumple)
  P6. Tanque cloración 200 L NO hermético con fugas ignoradas
  P7. Dosificación cloro manual (500 g sin medición precisa)
  P8. Sin alertas, sin KPIs, sin trazabilidad

PTAR (Planta Tratamiento Aguas Residuales):
  R1. Capacidad 2,000 estudiantes vs 8,234 usuarios actuales
  R2. Sin monitoreo Resolución 0631/2015 (DBO5, pH, SST)
  R3. Sale más agua que la que entra (DESBORDE confirmado)
  R4. Vertimientos sin caracterizar al río Pance/Cauca
  R5. Mantenimiento solo correctivo (cuando hay olores)
```

---

## 4. Datos Validados (4 tesis UNIAJC)

### 4.1 Tesis Caycedo Saa & Jaramillo Moreno (2021) — Caracterización

| Aporte | Dato exacto |
|--------|-------------|
| 161 fuentes de consumo | 51 sanitarios, 53 lavamanos, 14 orinales, 14 duchas, 24 llaves, 5 lavaplatos |
| Distribución por zona | Alameda 33% / Parquesoft 67% |
| Crecimiento estudiantil | 1,315 (2015) → 2,090 (2019) = +59% |
| 8 hallazgos de incumplimiento normativo | Toma de muestras, calidad agua, seguridad, manuales, personal, insumos, mantenimiento, equipos |
| 4 parámetros químicos fuera de norma | Cloro residual, nitratos, fosfatos, pH |
| Recomendaciones | Bomba dosificadora, VFD, medidores pH/turbidez/flujo |

### 4.2 Tesis Sánchez Sotelo (2021) — Lean Manufacturing

| Aporte | Dato exacto |
|--------|-------------|
| Caudal validado | 5.56 L/seg medido in-situ |
| Equivalencia tanque | 1 cm = 160 L |
| Desperdicio bruto medido | 960 L en 13 horas nocturnas |
| Desperdicio neto/hora | 66.15 L/hr |
| Desperdicio neto/día | 1,587.69 L/día |
| Desperdicio anual | 579.5 m³ |
| Costo anual | $1,107,637 COP (estrato 3, $1,910/m³) |
| Sistema presión | 38–60 PSI (rango fijo no optimizado) |
| Ciclo bombeo | 3-4 minutos |

### 4.3 Tesis Gómez Mina (2022) — Mantenimiento

| Equipo PTAP | Código UNIAJC | Especificación |
|-------------|---------------|-----------------|
| Bomba sumergible aljibe 1 | CP-BS-01 | Barnes 4SP 2526 · 5 HP · 32 gal/min |
| Bomba sumergible aljibe 2 | CP-BS-02 | Barnes 4SP 2511 · 2 HP · 32 gal/min |
| Filtros 1, 2, 3 | SF-FT-01/02/03 | OHS Ingenieros · 861.53 L · 400 L/min |
| Tanque cloración | SD-TM-01 | Ajover Wave · 250 L |
| Bomba dosificadora | SD-BD-01 | LMI C111-362TI · 150 PSI · 2.5 GPH |
| Tanques almacenamiento | AL-TA-01/02 | 36,000 L + 16,000 L |
| Hidroneumáticos | SB-TH-01/02 | Altamira PRO XLB · 119 gal · 125 PSI |
| Bombas centrífugas | SB-BC-03/04 | Barmesa Pumps |

### 4.4 Tesis Aristizábal & Largacha (2025) — Modelo Vensim

| Escenario | Resultado |
|-----------|-----------|
| Cooperación 0% | Colapso del sistema en 2 años |
| Cooperación 15% | Sostenibilidad parcial |
| Cooperación 50% | Sistema sostenible largo plazo |

---

## 5. Solución AguaMind OS

### Arquitectura conceptual

```
┌──────────────────────────────────────────────────────────────────┐
│                    CAMPUS UNIAJC SEDE SUR                          │
│                                                                     │
│   Aljibes ─→ PTAP ─→ Tanques ─→ Edificios ─→ PTAR ─→ Río Pance    │
│      │         │         │           │           │                 │
│      ▼         ▼         ▼           ▼           ▼                 │
│   [Sensores distribuidos en cada etapa]                           │
└──────────────────────────────────────┬─────────────────────────────┘
                                        │ MQTT/HTTP
                                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                     AGUAMIND OS — Backend                        │
│                                                                   │
│   ┌────────────────────────────────────────────────────────┐    │
│   │  CARACTERIZACIÓN DE DATOS                               │    │
│   │  · Caudales por edificio (entrada+salida)               │    │
│   │  · Calidad del agua (turbidez, pH, cloro)               │    │
│   │  · Niveles de tanques + acuífero                        │    │
│   │  · Patrones temporales (hora, día, semana, mes)         │    │
│   └─────────────────────────┬───────────────────────────────┘    │
│                              │                                     │
│   ┌──────────────────────────▼───────────────────────────────┐   │
│   │  INTELIGENCIA OPERATIVA (5 agentes especializados)        │   │
│   │  · Detección de anomalías (IsolationForest)               │   │
│   │  · Análisis Lean (7 mudas)                                │   │
│   │  · Validación de calidad de señales                       │   │
│   │  · Coordinación + reportes                                │   │
│   │  · Decisión de acciones de mitigación                     │   │
│   └─────────────────────────┬───────────────────────────────┘    │
│                              │                                     │
│   ┌──────────────────────────▼───────────────────────────────┐   │
│   │  ESTRATEGIAS DE MITIGACIÓN (lo que el jurado pidió)       │   │
│   │  · Cierre automático de electroválvulas                   │   │
│   │  · Reducción de presión nocturna                          │   │
│   │  · Plan diferenciado potable/riego                        │   │
│   │  · Concientización por edificio (Smart Water Ledger)      │   │
│   │  · Respuesta automática ante fenómeno del Niño            │   │
│   │  · Reporte automático a INVIMA, CVC, Min. Vivienda        │   │
│   └─────────────────────────┬───────────────────────────────┘    │
└──────────────────────────────┼─────────────────────────────────────┘
                                │
        ┌───────────────────────┼─────────────────────┐
        ▼                       ▼                     ▼
   ┌─────────────────┐   ┌────────────────┐  ┌─────────────────┐
   │ Modelo 3D Web   │   │ Bot Telegram   │  │ Reporte PDF auto│
   │ (visualización  │   │ (notificacio-  │  │ (cumplimiento   │
   │  fugas + zonas) │   │  nes + acción) │  │  normativo)     │
   └─────────────────┘   └────────────────┘  └─────────────────┘
```

---

## 6. Estrategia de Datos

> **El jurado fue enfático: "tu eres la base sobre la cual se construye todo lo demás. Si el dato está mal tomado, todo lo demás falla."**

### 6.1 Protocolo de muestreo

| Variable | Frecuencia muestreo | Frecuencia transmisión | Justificación |
|----------|---------------------|-------------------------|---------------|
| Caudal | 1 segundo | 30 segundos (promedio) | Detectar picos sin saturar canal |
| Nivel tanques | 5 segundos | 30 segundos | Cambia lento, suficiente |
| Presión | 1 segundo | 30 segundos | Detectar caídas súbitas |
| Turbidez | 30 segundos | 30 segundos | Cambia lento, alerta inmediata si fuera norma |
| Nivel freático | 1 minuto | 5 minutos | Cambio gradual del acuífero |
| Vibración | 100 muestras/seg | Solo eventos | Detección acústica embebida |
| pH (futuro) | 30 segundos | 30 segundos | Crítico para Resolución 0631 |

### 6.2 Arquitectura de transmisión

```
ESP32 (cada nodo)
   │
   ├── Buffer circular RAM (30 muestras = 30 segundos)
   │   - Promedio + min + max + desviación
   │
   ├── MQTT publish (preferido)
   │   - Broker: HiveMQ Cloud (TLS 8883)
   │   - Topic: campus/uniajc/sensors/{nodeId}
   │   - QoS 1 (al menos una entrega)
   │
   ├── HTTP fallback (si MQTT falla)
   │   - POST /water/ingest
   │   - Reintento exponencial
   │
   └── NVS local (si no hay internet)
       - Almacena hasta 1,000 lecturas
       - Reenvía cuando vuelve conexión
```

### 6.3 Almacenamiento

| Capa | Tecnología | Retención |
|------|-----------|-----------|
| Edge (ESP32) | NVS flash | 1,000 lecturas backup |
| Hot (FastAPI) | RAM + cache | Última hora |
| Warm (Supabase PostgreSQL) | Tabla `water_readings` indexada | 90 días |
| Cold (export Parquet S3) | Archivo trimestral | 5 años |
| Reporte normativo | PDF mensual auditable | Permanente |

### 6.4 Verificación de conectividad WiFi (validación con jurado)

**Plan de validación pre-instalación:**
1. Visita técnica a cada punto candidato (PTAP, Bloque A, Alameda, Cancha, Cafetería, Labs)
2. Medición RSSI WiFi con app InSSIDer
3. Si RSSI < -75 dBm: instalar repetidor Wi-Fi adicional
4. Plan B: módem 4G dedicado por nodo crítico ($45K/mes)
5. Plan C: LoRa para comunicación entre nodos sin internet

---

## 7. Sensores e Instrumentación

### 7.1 Criterio de selección (validado con jurado)

> *"No el más caro ni el más barato — el que da los datos verdaderos con la precisión que necesitamos."*

### 7.2 Sensores propuestos (con justificación de precisión)

| Sensor | Modelo | Precisión | Salida | Por qué este | Costo |
|--------|--------|-----------|--------|--------------|-------|
| Caudal pequeño | YF-S201 (1/2") | ±2% | Pulsos Hall (7.5 Hz/L/min) | Estándar industrial · validado en miles de instalaciones | $25K |
| Caudal grande | YF-DN50 | ±3% | Pulsos | Para entrada PTAP de 333 L/min | $95K |
| Presión | MPX5700AP | ±2.5% FS | 0-5V analógica | Cubre 0-700 kPa con sobre-rango seguro | $45K |
| Nivel tanque | JSN-SR04T | ±1 cm | PWM digital | Impermeable, distancia hasta 4.5m | $30K |
| Vibración | SW-420 + LM393 | Digital | TTL ON/OFF | Detección de eventos acústicos | $10K |
| Nivel freático | Transductor 4-20mA | ±0.5% FS | Loop industrial | Estándar para pozos profundos | $180K |
| Turbidez | TSD-10 | ±0.5 NTU | Analógica 0-4.5V | Crítico para cumplimiento Res. 2115 | $55K |
| pH (Fase 3) | DFRobot SEN0161 | ±0.1 pH | Analógica | Crítico para Resolución 0631 PTAR | $120K |
| Conductividad | DFR0300 | ±5% | Analógica | Indica contaminación química | $90K |
| Cloro residual | ORP / redox | ±10 mV | Analógica | Cumplimiento Decreto 1575 | $200K |

### 7.3 Microcontrolador

| Característica | ESP32-WROOM-32 | Justificación |
|----------------|----------------|---------------|
| CPU dual core 240 MHz | Procesa sensores + comunicación en paralelo |
| WiFi 802.11 b/g/n | Conectividad nativa sin shield |
| RAM 520 KB | Suficiente para buffer + edge ML |
| Flash 4 MB | Firmware + NVS + backup |
| ADC 12-bit | + ADS1115 16-bit externo para mejor resolución |
| Costo | $35K — relación calidad/precio óptima |

### 7.4 ADC externo (precisión)

> ESP32 ADC tiene no-linearidad. Usamos **ADS1115 16-bit por I2C** para sensores analógicos críticos (presión, freático, turbidez).

```
Resolución ADS1115 con gain=1: 4.096V / 32,768 = 0.125 mV
   → Equivalente a 0.05 NTU en turbidez
   → Equivalente a 0.4 kPa en presión
   → Más que suficiente para precisión normativa
```

### 7.5 Calibración pre-instalación (cada sensor)

**Test 1 — Caudal:** cubeta 20 L cronometrada vs lectura sensor (criterio < 5% error)
**Test 2 — Nivel:** tanque graduado a 5 niveles (20, 40, 60, 80, 100 cm) → criterio < 2 cm error
**Test 3 — Presión:** compresor con manómetro patrón → criterio < 3% error
**Test 4 — Turbidez:** soluciones patrón Formazin (1, 5, 10 NTU) → criterio < 0.5 NTU error

---

## 8. Modelo 3D del Campus

> **Solicitud directa del jurado:** *"Modelo 3D donde se vea todas las tuberías para detectar dónde hay fuga."*

### 8.1 Implementación actual (Fase 1 — SVG 2D)

Mapa SVG interactivo en `/agua` tab "Mitigación":
- Aljibes 1 y 2
- PTAP con 3 filtros + tanque cloración
- Tanques A (36k L) + B (16k L) con nivel real
- 6 edificios: Bloque A, Alameda, Cafetería, Labs, Cancha, Limpieza
- 2 PTAR (Alameda + Entrada)
- Río Pance/Cauca con etiqueta normativa
- Pulso rojo animado en zona con fuga detectada
- Estado de cada electroválvula

### 8.2 Evolución a Modelo 3D (Fase 5 — propuesto)

```
Tecnologías:
  Frontend: Three.js + React Three Fiber
  Modelo:   Blender (gratuito) → glTF
  Datos:    Tiempo real desde FastAPI
  AR:       WebXR para tabletas mantenimiento

Capas visualizables:
  ▢ Edificios (geometría)
  ▢ Tuberías agua potable (azul)
  ▢ Tuberías aguas residuales (naranja)
  ▢ Sensores (puntos pulsantes)
  ▢ Electroválvulas (estado abierto/cerrado)
  ▢ Mapa de calor de consumo por hora
  ▢ Mapa de calor de fugas (último 30 días)
  ▢ Cortes transversales (raycasting)

Interacción:
  · Click en sensor → muestra histórico
  · Click en válvula → permite cerrar/abrir (con confirmación)
  · Slider temporal → reproducir histórico
  · Filtro por hora del día → "ver consumo 6-8 AM"
```

### 8.3 Mientras tanto: Modelo 3D simplificado en SVG

Vista isométrica del campus con tuberías visibles **ya implementada** en el dashboard. Mostrar al jurado en el pitch.

---

## 9. Estrategias derivadas de los datos

> **El jurado pidió enfocarse aquí.** No es predecir, es **qué hacemos con los datos**.

### 9.1 Estrategia ante Fenómeno del Niño / sequía

```
Trigger:  Pronóstico IDEAM "El Niño" en 30 días + nivel freático < 5 m
Acciones automáticas del sistema:
  1. Activar modo "ahorro hídrico" en todo el campus
  2. Reducir presión nocturna en baños (38 → 25 PSI)
  3. Cerrar EV-RC1 (riego cancha) — reasignar agua tratada a uso humano
  4. Notificar Telegram a 8,234 usuarios con consejos de ahorro
  5. Activar campaña "30 días sin desperdicio"
  6. Pantallas LED muestran "ALERTA SEQUÍA - cuidemos el agua"

Impacto esperado: -25% consumo total durante alerta
```

### 9.2 Estrategia diferenciación potable/riego

```
Hoy: Aljibe 2 envía agua sin tratar a riego, pero también aporta a PTAP.
     Mezcla operativa sin claridad.

Con AguaMind OS:
  · YF-DN50 mide flujo exacto en derivación riego
  · Higrómetros HW-080 miden humedad real del suelo
  · EV-RC1 controla apertura/cierre

Reglas operativas (datos → estrategia):
  SI humedad_suelo > 60% → cerrar riego (no necesario)
  SI hora ∈ [10:00-16:00] → cerrar riego (evaporación alta)
  SI lluvia_pronosticada(24h) → cerrar riego
  SI demanda_potable > 80% capacidad → cerrar riego (priorizar humano)
  SI nivel_freático < 4m → modo emergencia (riego × 0.3)

Resultado: 4,000 L/día → 2,200 L/día (-45%)
```

### 9.3 Estrategia concientización con Bienestar Universitario

```
Smart Water Ledger:
  1 Crédito = 1 m³ ahorrado vs línea base mensual

Conexión real con Bienestar UNIAJC:
  100 créditos → mejora zona común del edificio
  500 créditos → renovación cafetería
  1,000 créditos → presupuesto para proyecto estudiantil
  Ranking público mensual en pantallas LED

Reportes ciudadanos QR:
  Estudiante escanea QR en baño → reporta fuga → +20 puntos
  AguaMind valida con sensores → si confirma, genera OT
  Si falsa alarma → +5 puntos por colaborar

Resultado: -10 a -15% consumo por cambio cultural
         (referencia: campañas similares en otras universidades)
```

### 9.4 Estrategia de bombeo eficiente (datos → energía)

```
Hoy: Bombas centrífugas funcionan a misma potencia siempre (Sánchez 2021)
     Ciclos 3-4 minutos = consumo eléctrico innecesario

Con datos AguaMind OS:
  · Histórico de demanda hora por hora
  · Identificación de horas pico vs valle
  · Curva característica de bombas (TPM)

Estrategia:
  Modo eco-nocturno (22:00 - 06:00):
    Reducir presión a 25 PSI con VFD
    -40% consumo eléctrico bombas
  
  Modo pico (07:00 - 09:00):
    Pre-presurizar tanques antes del pico
    Evitar arranque emergencia
  
  Modo estándar:
    Optimizar ciclos según demanda histórica

Resultado: -596 kWh/año proyectado
         (alineado con Ley 1931/2018 eficiencia energética)
```

### 9.5 Estrategia respuesta a desborde PTAR

```
Problema identificado por jurado:
  "PTAR tiene desborde — sale más agua que la que entra"

Análisis con datos:
  Q_entrada_PTAR = Σ Q_out edificios
  Q_salida_PTAR = sensor caudal en vertimiento

Si Q_salida > Q_entrada × 1.05 (5% tolerancia):
  → Hay infiltración freática en colectores
  → O hay vertidos no autorizados
  → Genera alerta crítica + investigación

Si Q_entrada > capacidad PTAR (2,000 estudiantes):
  → Sobrecarga sistemática
  → Justifica ampliación PTAR ante CVC
  → Reporte trimestral automatizado
```

---

## 10. Sistema Multi-Agente IA

> Renombrado en el dashboard: **"Inteligencia Operativa"** (sugerencia jurado)

### 10.1 Por qué multi-agente y no un solo modelo

Un solo modelo de IA dice "hay anomalía". Cinco agentes especializados deliberan y dicen:
- *Qué tipo de anomalía* (estadística, sensórica, operacional)
- *Con qué confianza* (0-100%)
- *Qué acción tomar* (validada por consenso)
- *Por qué esa acción* (auditable)

### 10.2 Los 5 agentes

| Agente | Rol | Tecnología base |
|--------|-----|-----------------|
| **Orchestrator** | Coordina deliberación | LangGraph + LLM cascade |
| **Systems** | KPIs + anomalías estadísticas | IsolationForest |
| **Sensor** | Calidad de señales | Validación rangos físicos |
| **Industrial** | Lean + procesos | Reglas mudas + costos |
| **Mitigation** | Acción autónoma | Reglas de decisión + EV |

### 10.3 Tiempo de deliberación

```
Sensor detecta vibración + caída presión 28%
        ↓ (1 segundo)
Orchestrator reparte tarea a 4 agentes
        ↓ (1 segundo)
4 agentes analizan en paralelo
        ↓ (2 segundos)
Voto consensual → "fuga crítica, cerrar EV-A2"
        ↓ (1 segundo)
Mitigation ejecuta acción
        ↓ Total: 5 segundos

vs Humano: 2-4 horas (turno mantenimiento)
```

---

## 11. Mitigación Activa

### 11.1 Lo que hace AguaMind OS que ningún otro sistema hace

| Acción | Antes (manual) | Con AguaMind OS |
|--------|---------------|------------------|
| Detectar fuga | Días/semanas | < 5 segundos |
| Cerrar válvula | Personal va al sitio | Automático en 3 segundos |
| Notificar | Llamada telefónica | Telegram + dashboard |
| Generar OT | Papel | PDF automático con ID rastreable |
| Calcular impacto | No se mide | L + COP + CO₂ acumulados |
| Reportar a CVC | Trimestral manual | Automático con datos |

### 11.2 8 electroválvulas controladas

```
EV-A1   Bloque A entrada principal
EV-A2   Bloque A baños 2do piso
EV-AL1  Alameda entrada
EV-RC1  Riego/Cancha solenoide
EV-CAF1 Cafetería entrada
EV-LAB1 Laboratorios entrada
EV-OUT-A Salida Tanque A
EV-OUT-B Salida Tanque B
```

### 11.3 5 triggers de mitigación automática

| Trigger | Acción | Litros evitados |
|---------|--------|-----------------|
| `leak` | Cierra EV afectada + bomba standby | ~14,500 L |
| `peak_irrigation` | Cierra EV-RC1, reprograma noche | ~1,800 L |
| `turbidity` | Cierra EV-OUT-A/B, alerta sanitaria | Protección 8,234 usuarios |
| `tank_overflow` | Apaga bomba antes de desborde | ~6,500 L |
| `phreatic_low` | Reduce extracción 70% | Preserva acuífero |

---

## 12. Cumplimiento Normativo

### 12.1 Normativas mapeadas

```
CALIDAD AGUA POTABLE:
  · Decreto 1575 de 2007 — control calidad agua humana
  · Resolución 2115 de 2007 — IRCA, parámetros físico-químicos
  · Decreto 3930 de 2010 — uso recurso hídrico
  · RAS 2000 Cap. C.17 — retrolavado mínimo 2/año
  · Decreto 2105 de 1983 — potabilización

CONCESIÓN Y ACUÍFERO:
  · Decreto 1541 de 1978 — concesión aguas públicas
  · Decreto 1076 de 2015 — monitoreo piezométrico
  · Ley 79 de 1986 — conservación del agua

VERTIMIENTOS:
  · Resolución 0631 de 2015 — DBO5 ≤ 90 mg/L, pH 6-9
  · Decreto 050 de 2018 — Plan de cumplimiento
  · Resolución 1207 de 2014 — reúso para riego

SEGURIDAD INFORMACIÓN:
  · Ley 1581 de 2012 — Habeas Data
  · Ley 1928 de 2018 — ciberseguridad
  · Decreto 338 de 2022 — riesgos cibernéticos
  · Ley 1712 de 2014 — transparencia
  · Resolución 055 UNIAJC enero 2025
```

### 12.2 Reportes automáticos generados

| Reporte | Frecuencia | Autoridad | Contenido |
|---------|------------|-----------|-----------|
| IRCA | Mensual | INVIMA | Turbidez, cloro, pH |
| Caudal extraído | Trimestral | CVC | Aljibes 1 y 2 vs concesión |
| Vertimientos PTAR | Trimestral | CVC | DBO5, pH, SST |
| Mantenimiento RAS | Semestral | Min. Vivienda | Retrolavados, lavado tanques |
| Datos abiertos | Continuo | Procuraduría | Dashboard público |

### 12.3 Exposición legal evitada

| Sanción potencial | Multa máxima |
|-------------------|--------------|
| Suspensión por IRCA | 1,000 SMMLV ≈ $1,300M COP |
| Revocatoria concesión CVC | 5,000 SMMLV ≈ $6,500M COP |
| Multa Res. 0631/2015 | 5,000 SMMLV ≈ $6,500M COP |
| Multa Ley 1581/2012 | 2,000 SMMLV ≈ $2,600M COP |
| **TOTAL EXPOSICIÓN** | **$16,900M COP** |
| **Inversión AguaMind para evitarlo** | **$5–19M COP** |

> Cada peso invertido protege $890–3,380 en exposición legal.

---

## 13. Plan por Fases (15 años)

> **Solicitud jurado:** *"Pensar en universidad de 12,000 usuarios a 2030"*

### Fase 1 — Hackathon (Mayo 2026)
- ✅ Backend + dashboard + simulador
- ✅ Documentación completa
- ✅ PDF entregable

### Fase 2 — Piloto PTAP (Mes 1)
**Inversión:** $1.4M COP
- 1 nodo IoT en PTAP completo
- 6 sensores instalados
- Validación in-situ

### Fase 3 — Expansión (Meses 2-6)
**Inversión:** $5.4M COP acumulada
- 5 nodos zonas críticas
- Cobertura ~80% del campus
- Dashboard público activo

### Fase 4 — Sensorización masiva (Meses 7-12)
**Inversión:** $9.2M COP acumulada
- Nodos por sub-circuito de baños
- Hidrófonos en uniones críticas
- TPP < 10% confirmado

### Fase 5 — Smart Water Ledger (Año 2)
**Inversión:** $11M COP acumulada
- Gamificación con bienestar
- App QR para reportes ciudadanos
- Pantallas LED en hall edificios

### Fase 6 — Modelo 3D + AR (Año 3)
**Inversión:** $13.5M COP acumulada
- Three.js + WebXR
- Tabletas para mantenimiento
- Simulación predictiva Vensim integrada

### Fase 7 — Replicación UNIAJC (Año 4-5)
- 4 sedes UNIAJC
- Modelo open source publicado
- Caso de éxito ICONTEC

### Fase 8 — Replicación regional (Año 6-10)
- 30+ universidades del Valle
- Spin-off como startup tech
- Publicaciones científicas

### Fase 9 — Crecimiento UNIAJC 2030 (Año 5-10)
**Capacidad proyectada:**
- 12,000 usuarios totales
- ~75,000 L/día demanda
- Sistema soporta crecimiento sin reescritura
- Solo añadir más nodos a la red existente

### Fase 10 — Madurez (Año 10-15)
- AguaMind OS como infraestructura crítica institucional
- Integración con SUI (Sistema Único de Información)
- Reporte automático ICONTEC + ISO 14001

---

## 14. Costo-Beneficio + ROI

### 14.1 Inversión Fase 1 (1 nodo PTAP)

```
Hardware (BOM):
  ESP32 + ADS1115:                $50K
  6 sensores principales:         $400K
  Electroválvulas + relay:        $185K
  Acondicionamiento + PCB:        $80K
  Gabinete IP65 + cableado:       $135K
  Indicadores locales:            $32K
  Energía + backup:                $99K
  Subtotal hardware:              $981K

Mano de obra (auto-construido equipo):
  Subtotal MO:                    $0 COP

Software (open source):
  FastAPI + LangGraph + SvelteKit: $0
  Supabase free tier:              $0
  HiveMQ Cloud free tier:          $0
  Subtotal software:               $0

Imprevistos (10%):                $98K

INVERSIÓN TOTAL FASE 1:        $1,431,000 COP (~$340 USD)
```

### 14.2 Beneficios anuales proyectados

```
1. Reducción pérdidas físicas (TPP 25% → 10%):
   9,073 L/día × 365 × $3.5/L = $11,586,925 COP/año

2. Optimización riego automatizado:
   1,800 L/día × 365 × $3.5/L = $2,299,500 COP/año

3. Mantenimiento preventivo vs correctivo:
   2 eventos/año → 0.3 eventos/año = $4,250,000 COP/año

4. Eficiencia energética bombeo (-40% nocturno):
   ~$2,400,000 COP/año en electricidad

5. Evita sanciones (riesgo evitado, no caja):
   $16,900M COP exposición × probabilidad

TOTAL AHORRO ANUAL:           $20,536,425 COP/año (proyectado)
```

### 14.3 Indicadores financieros

| Indicador | Valor |
|-----------|-------|
| Período recuperación | **~25 días** |
| VPN 5 años (12%) | **$73M COP** |
| TIR | **> 1,000%** |
| Ratio Beneficio/Costo | **17.4×** |
| Agua recuperada 5 años | **16.5M L** |

---

## 15. Impacto + ODS

### ODS impactados directamente

```
ODS 6  Agua Limpia y Saneamiento
       Meta 6.4 — eficiencia uso agua
       AguaMind: TPP 25% → 10%

ODS 12 Producción/Consumo Responsables
       Meta 12.5 — reducción desperdicios
       AguaMind: 7 mudas Lean atacadas

ODS 13 Acción por el Clima
       Meta 13.3 — educación mitigación
       AguaMind: 7.6 ton CO₂ evitadas/5 años

ODS 9  Industria, Innovación, Infraestructura
       Meta 9.4 — modernizar
       AguaMind: IoT + IA en infraestructura 2011

ODS 11 Ciudades Sostenibles
       Meta 11.6 — reducir impacto ambiental
       AguaMind: modelo Smart Campus
```

### ODS impactados indirectamente

ODS 3 Salud · ODS 4 Educación · ODS 5 Igualdad · ODS 8 Trabajo · ODS 10 Desigualdades · ODS 14 Vida marina · ODS 15 Ecosistemas · ODS 16 Paz · ODS 17 Alianzas

---

## 16. Pitch 5 minutos

### Estructura cronometrada

| Tiempo | Sección | Mensaje clave |
|--------|---------|---------------|
| 0:00–0:30 | Apertura | "9 litros perdidos mientras hablo" |
| 0:30–1:15 | Problema | UNIAJC pierde 1,587 L/día medidos · agua fuera de norma · sanción $16,900M |
| 1:15–2:30 | Solución (demo en vivo) | Modelo 3D + 5 agentes deliberando + cierre EV automático |
| 2:30–3:30 | Diferenciadores | Estrategias derivadas de datos (no predicción) · 4 estrategias clave |
| 3:30–4:15 | Impacto | $1.4M inversión · 25 días ROI · 5 ODS · 16.5M L recuperados |
| 4:15–4:45 | Validación académica | 4 tesis UNIAJC integradas (Caycedo, Sánchez, Gómez, Aristizábal) |
| 4:45–5:00 | Cierre | "4 tesis. 4 diagnósticos. 0 soluciones implementadas. AguaMind OS las pone en operación. Hoy." |

### Apertura textual

> *"Antes de empezar, una pregunta para el jurado: ¿cuántos litros de agua perdió esta universidad mientras yo decía estas palabras? La respuesta es 9 litros. Y nadie en UNIAJC se ha enterado todavía. Cada minuto, en silencio, esta planta del 2011 deja escapar agua que nadie mide. Lleva 13 años haciéndolo."*

### Cierre textual

> *"AguaMind OS no es un proyecto. Es la culminación de 5 años de investigación en UNIAJC sobre la PTAP, llevada a operación. Caycedo y Jaramillo caracterizaron en 2021. Sánchez Sotelo midió las pérdidas en 2021. Gómez Mina diseñó mantenimiento en 2022. Aristizábal y Largacha modelaron en 2025. Cuatro tesis. Cuatro diagnósticos. Cero soluciones implementadas. AguaMind OS las toma todas y las pone en operación. Hoy."*

---

## 17. Q&A Anticipado

### "¿Por qué no usaron un SCADA tradicional?"
> SCADA cuesta $50M+, es cerrado, no aprende, no cumple normativa automáticamente, no se conecta con la comunidad. AguaMind OS cuesta $1.4M, es open source, multiagente y replicable.

### "¿Qué pasa si el agente toma una decisión incorrecta?"
> Triple validación: 5 agentes deben coincidir, alerta humana en menos de 30 segundos, override manual desde dashboard. En Fase 1 piloto requerimos confirmación humana antes de actuar.

### "¿Cómo aseguran la calidad de los datos?"
> SensorAgent valida cada lectura contra rangos físicos imposibles. Calibración pre-instalación con 4 protocolos documentados. Calibración trimestral. ADS1115 16-bit para precisión normativa.

### "¿Y si los estudiantes que crearon esto se gradúan?"
> Código en GitHub público. Documentación en español. Semillero SEGESTOP UNIAJC puede continuar. Más de 50 ingenieros graduados al año pueden mantenerlo.

### "¿Qué hacen los próximos 6 meses?"
> Mes 1: instalar primer nodo en PTAP. Mes 2-3: extender Bloque A y Cancha. Mes 4-6: sensores PTAR + reporte automático CVC. Mes 7+: replicación a Sede Norte y Centro.

### "¿Cómo verifican conectividad WiFi en cada punto?"
> Visita técnica pre-instalación con InSSIDer (RSSI). Si RSSI < -75 dBm, instalar repetidor. Plan B: módem 4G dedicado. Plan C: LoRa entre nodos.

### "¿Qué pasa si se cae internet?"
> ESP32 tiene NVS flash que almacena hasta 1,000 lecturas. Cuando vuelve conexión, reenvía. OLED + LED RGB + buzzer locales muestran estado sin internet.

### "Pueden haber soluciones costo-beneficio más económicas (mencionado por jurado)"
> Sí. Mantenemos como complemento el método "tanques nocturnos" (medir nivel a las 6 PM y 7 AM = pérdida nocturna). Es de costo cero y se suma a los datos automáticos para validación cruzada.

---

## 18. Roles del Equipo

### Sistemas (1+)
- Backend FastAPI + agentes LangGraph
- Dashboard SvelteKit con modelo 3D
- Bot Telegram + protocolo de datos
- Diagrama UML de componentes y estados

### Electrónica (1+)
- Esquemático ESP32 + sensores
- BOM con costos COP
- Calibración pre-instalación
- Plan de conectividad WiFi/4G

### Industrial (1+)
- KPIs IEH/TPP/CPE/ICA con fórmulas
- Análisis Lean (7 mudas + Ishikawa)
- Costo-beneficio + ROI
- Estrategias de mitigación derivadas de datos

> El equipo cumple el requisito mínimo del hackathon: 3-5 integrantes con al menos 1 estudiante de cada ingeniería.

---

## 19. Referencias

### Trabajos académicos UNIAJC

1. **Caycedo Saa, M. A., & Jaramillo Moreno, A. F. (2021).** *Propuesta de caracterización del proceso técnico-operativo de la planta de tratamiento de agua de la Institución Universitaria Antonio José Camacho Sede Sur.* Repositorio UNIAJC handle/586.

2. **Sánchez Sotelo, A. (2021).** *Propuesta de mejora con aplicación de herramientas de Lean Manufacturing para la planta de potabilización de agua en la Universidad Antonio José Camacho Sede Sur.*

3. **Gómez Mina, P. A. (2022).** *Diseño de un programa de mantenimiento para la planta de tratamiento de agua potable de la Institución Universitaria Antonio José Camacho sede sur.*

4. **Aristizábal Torres, H. W., & Largacha Perdomo, S. (2025).** *Desarrollo de un modelo de dinámica de sistemas para simular la demanda y el suministro de agua en la Institución Universitaria Antonio José Camacho, Sede Sur.*

5. **Arias Montoya, Y. D., Montiel Angel, R. E., & Osorio Hernández, C. A. (2024).** *Diseño de un sistema de ahorro para el mejoramiento de la eficiencia del servicio suministrado por la PTAP en la Institución Universitaria Antonio José Camacho Sede Sur.*

6. **Mosquera Zapata, L. L., & Lozano Beltrán, S. (2024).** *Modelo de dinámica de sistemas para brindar información a la comunidad académica del impacto sobre la PTAR y el ecosistema, UNIAJC sede sur en Cali.*

### Marco normativo colombiano

- Decreto 2105 de 1983 — Potabilización
- Decreto 1575 de 2007 — Calidad agua humana
- Resolución 2115 de 2007 — IRCA
- Decreto 3930 de 2010 — Uso recurso hídrico
- Resolución 0631 de 2015 — Vertimientos
- Decreto 1076 de 2015 — Monitoreo piezométrico
- RAS 2000 Cap. C.17 — Operación PTAP
- Ley 1581 de 2012 — Habeas Data
- Ley 1712 de 2014 — Transparencia
- Resolución 055 UNIAJC enero 2025 — Seguridad información

### Otros documentos AguaMind OS (consolidados aquí)

- `INNOVACION-RADICAL.md`
- `PITCH-DEFINITIVO.md`
- `ESTRATEGIA-RUBRICA.md`
- `INTEGRACION-TESIS-UNIAJC.md`
- `IMPLEMENTACION-TECNICA-SENSORES.md`
- `ARQUITECTURA-POR-EDIFICIO.md`
- `PROBLEMAS-PTAP-PTAR.md`
- `CUMPLIMIENTO-NORMATIVO-Y-SOLUCIONES.md`
- `MITIGACION-Y-ESTRATEGIA.md`
- `IMPACTO-AMBIENTAL-Y-ODS.md`
- `DIAGRAMAS-Y-DISEÑO.md`
- `PREGUNTAS-ASESORIA.md`
- `SIMULACION-Y-CONEXION.md`
- `PROBLEMA-DEL-AGENTE.md`
- `AGUAMIND-OS-DOCUMENTACION.md`

---

## Cierre

> **AguaMind OS** = Caracterización inteligente + Estrategias accionables + Comunidad empoderada
>
> No predecimos. **Caracterizamos.**
> No avisamos. **Actuamos.**
> No competimos con tesis previas. **Las llevamos a operación.**
>
> *Tecnología con Propósito · Inteligencia con Conciencia*

---

*Documento maestro v2.0 · Post-asesoría jurados · 7 de mayo 2026*
*AguaMind OS · Hackathon UNIAJC 2026 · github.com/JFrangel/AguaMind-OS*
