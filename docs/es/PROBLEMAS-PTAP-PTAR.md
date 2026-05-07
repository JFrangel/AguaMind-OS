# Problemas de la PTAP y PTAR — UNIAJC Sede Sur

> Diagnóstico técnico de los problemas reales identificados en la planta de
> tratamiento de agua potable (PTAP) y la planta de tratamiento de aguas
> residuales (PTAR), y cómo AguaMind OS los ataca uno por uno.

---

## 1. La PTAP — Planta de Tratamiento de Agua Potable

### Contexto

La sede sur de UNIAJC, ubicada en zona periurbana de Cali, **no tiene acueducto municipal**. El campus se autoabastece desde **2011** con una PTAP propia que capta agua subterránea de 2 aljibes conectados a la cuenca del río Pance.

```
Acuífero (~5,000,000 L)
       │
   ┌───┴───┐
   ▼       ▼
Aljibe 1  Aljibe 2 ──── derivación directa a Riego (SIN TRATAR)
   │       │                                           │
   └───┬───┘                                           ▼
       ▼                                          Cancha + jardines
   PTAP (3 filtros)
       │ filtro grava+arena → antracita → carbón activado
       ▼
   Tanque A (36,000 L)
       │ bomba ON @ 24,000 L
       ▼
   Tanque B (16,000 L)
       │
   Distribución a edificios (Bloque A, Alameda, Cafetería, Labs, Limpieza)
```

### Problemas críticos identificados

#### P1 — Ausencia total de medición (problema raíz)
- **Síntoma:** la PTAP funciona desde 2011 sin caudalímetros ni sensores de nivel.
- **Consecuencia:** imposible saber cuánta agua entra, sale o se pierde.
- **Magnitud:** pérdidas estimadas 20–30 % del caudal de entrada (≈ 9,073–13,610 L/día).
- **Impacto económico:** $19.3 M COP/año desperdiciados.
- **Solución AguaMind:** Nodo IoT con 6 sensores en PTAP (Fase 1) → visibilidad 100 % del flujo.

#### P2 — Pérdidas no contabilizadas
- **Síntoma:** balance entrada vs. consumo arroja diferencia del 20–30 %.
- **Causas probables:** fugas en uniones envejecidas, grifos mal cerrados, riego excesivo.
- **Solución AguaMind:** TPP medible + IsolationForest detecta anomalías + hidrófono acústico identifica huella de fuga.

#### P3 — Riego con agua tratada (proceso innecesario)
- **Síntoma:** parte del agua que pasa por filtros termina en jardines/cancha.
- **Consecuencia:** desperdicio de reactivos de filtración + costo energético.
- **Cifra:** ~ 4,000 L/día riego, parcialmente desde aljibe 2 sin tratar (correcto), parcialmente desde tanques (incorrecto).
- **Solución AguaMind:** EV-RC1 + higrómetros suelo → riego sólo cuando humedad < 60 % y desde aljibe 2.

#### P4 — Bombeo sin demanda real (sobreproducción)
- **Síntoma:** la bomba activa cuando Tanque A < 24,000 L pero sin saber si la demanda lo justifica.
- **Consecuencia:** consumo eléctrico + desgaste mecánico innecesario.
- **Solución AguaMind:** relay SSR + lógica del agente (consultar histórico antes de decidir).

#### P5 — Acuífero sobreexplotado en horas pico
- **Síntoma:** sin medición del nivel freático, no se sabe si el acuífero se recupera.
- **Riesgo:** colapso del sistema en escenario de cooperación 0 % (modelo Vensim de la tesis Aristizábal/Largacha 2025 lo demostró).
- **Solución AguaMind:** transductor 4-20 mA en cada aljibe → nivel freático en tiempo real → reducción automática de extracción.

#### P6 — Tuberías de más de 10 años sin mantenimiento
- **Síntoma:** uniones de PVC/HG envejecidas con corrosión interna no visible.
- **Riesgo:** rotura súbita aguas adentro de pared o subterráneas.
- **Solución AguaMind:** SW-420 en codos críticos + hidrófonos para huella acústica + EV-A* para corte preventivo.

#### P7 — Tanques sin medición de nivel
- **Síntoma:** se ignora el nivel actual hasta inspección visual.
- **Riesgo:** desbordamiento (presión exceso → más fugas) o vaciado (servicio interrumpido).
- **Solución AguaMind:** JSN-SR04T en cada tanque con alerta automática.

#### P8 — Sin monitoreo de calidad del agua
- **Síntoma:** los filtros podrían estar saturados sin que nadie lo note.
- **Riesgo:** distribución de agua turbia → riesgo sanitario para 8,234 usuarios.
- **Solución AguaMind:** TSD-10 a la salida del filtro de carbón → suspende distribución si NTU > 4.

#### P9 — Sin alertas ni KPIs
- **Síntoma:** decisiones basadas en intuición o factura mensual.
- **Solución AguaMind:** dashboard con IEH, TPP, CPE, ICA + Telegram push + reporte diario PDF.

#### P10 — Aljibe 2 deriva directo a riego sin diferenciación operativa
- **Síntoma:** mezcla de uso productivo y de riego en una sola línea.
- **Solución AguaMind:** EV-RC1 con T-junction permite cortar el riego sin afectar el resto del sistema.

---

## 2. La PTAR — Planta de Tratamiento de Aguas Residuales

UNIAJC Sede Sur tiene **2 PTAR** trabajando en paralelo:

- **PTAR Alameda** (módulo 1) — atiende ~ 1,000 estudiantes
- **PTAR Entrada** (módulo 2) — atiende ~ 1,000 estudiantes

```
Aguas residuales del campus
   ├── Domésticas (baños, lavamanos, cafetería)
   └── Laboratorios (pequeño volumen pero variable)
                 │
                 ▼
     ┌──────────┴──────────┐
     ▼                     ▼
PTAR Alameda          PTAR Entrada
 (1,000 est)          (1,000 est)
     │                     │
     └──────────┬──────────┘
                ▼
        Río Cauca / Pance
        (Resolución 0631/2015)
```

### Problemas críticos PTAR

#### R1 — Capacidad subdimensionada
- **Población actual:** 8,234 usuarios totales (estudiantes + docentes + staff).
- **Capacidad PTAR:** 2,000 estudiantes (1,000 por módulo).
- **Brecha:** > 6,000 usuarios excedentes.
- **Riesgo:** descargas sin tratamiento adecuado → sanción ambiental.

#### R2 — Sin monitoreo de calidad del efluente
- **Normativa:** Resolución 0631 de 2015 fija límites de vertimientos:
  - DBO5 ≤ 90 mg/L
  - pH 6.0 – 9.0
  - Sólidos suspendidos ≤ 90 mg/L
  - Grasas y aceites ≤ 20 mg/L
- **Realidad UNIAJC:** ningún parámetro se mide en línea.
- **Solución AguaMind extendida:** sensores adicionales en salida PTAR (turbidez + pH + conductividad) → reporte automático a autoridad ambiental (CVC).

#### R3 — Impacto sobre cuenca río Pance y río Cauca
- **Magnitud:** ~ 30,000 L/día de aguas residuales.
- **Tesis Mosquera/Lozano (2024):** demostró el impacto de la comunidad académica sobre el ecosistema.
- **Solución AguaMind:** dashboard público "Pulso del río Pance" mostrando descargas tratadas vs. límites normativos.

#### R4 — Vínculo PTAP-PTAR no medido
- **Problema:** lo que entra (PTAP) y lo que sale (PTAR) no se comparan.
- **Consecuencia:** no se sabe el ratio uso real vs. evaporación/fugas.
- **Solución AguaMind:** balance hídrico institucional automático.

#### R5 — Mantenimiento reactivo
- **Síntoma:** los lodos de la PTAR se retiran cuando hay olores o desbordes.
- **Solución AguaMind extendida:** sensor de turbidez en cámara de lodos → alerta para purgas programadas.

---

## 3. Cómo AguaMind OS resuelve cada problema

| # | Problema | Sensor responsable | Acción del agente |
|---|----------|--------------------|-------------------|
| **PTAP** |||
| P1 | Ausencia medición | YF-S201 + JSN-SR04T + MPX5700AP | Visibilidad 100 % |
| P2 | Pérdidas no contabilizadas | Hidrófono + KPI TPP | Detección < 5 min + cierre EV |
| P3 | Riego con agua tratada | YF-DN50 + higrómetros | EV-RC1 desde aljibe 2 sin tratamiento |
| P4 | Bombeo sin demanda | JSN-SR04T + relay SSR | Bomba sólo cuando lo amerita |
| P5 | Acuífero sobreexplotado | Transductor 4-20mA | Reduce extracción automáticamente |
| P6 | Tuberías envejecidas | SW-420 vibración + acústico | EV cierra sector con anomalía |
| P7 | Tanques sin nivel | JSN-SR04T ×2 | Alerta + acción autónoma |
| P8 | Sin calidad agua | TSD-10 turbidez | Suspende distribución si > 4 NTU |
| P9 | Sin alertas/KPIs | dashboard + Telegram | KPIs en vivo + push automático |
| P10 | Aljibe 2 sin control | EV-RC1 + caudalímetro | Corte selectivo |
| **PTAR** |||
| R1 | Capacidad subdimensionada | balance hídrico | Reporte de uso vs. capacidad |
| R2 | Sin calidad efluente | TSD-10 + pH + cond. (extensión) | Reporte automático a CVC |
| R3 | Impacto cuenca | dashboard público | Transparencia comunitaria |
| R4 | PTAP-PTAR no medidos | balance entradas/salidas | Análisis ratio mensual |
| R5 | Mantenimiento reactivo | TSD-10 cámara lodos | Programación purgas |

---

## 4. Resumen — los 5 problemas más graves

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                    │
│   Top 5 problemas críticos (por impacto económico y ambiental):    │
│                                                                    │
│   1. Pérdidas 20-30% del caudal sin detectar     →  $19M/año      │
│      Solución: Nodo PTAP + hidrófono + EV         (Fase 1)         │
│                                                                    │
│   2. Bombeo sin demanda real                      →  desgaste      │
│      Solución: relay SSR + agente lógica           (Fase 1)         │
│                                                                    │
│   3. Calidad agua sin monitorear                  →  riesgo salud  │
│      Solución: TSD-10 + suspensión automática     (Fase 1)         │
│                                                                    │
│   4. Acuífero sobreexplotado                      →  colapso       │
│      Solución: 4-20mA + reducción extracción      (Fase 1)         │
│                                                                    │
│   5. PTAR descarga sin medir cumplimiento norma   →  sanción CVC   │
│      Solución: extensión sensores PTAR            (Fase 2-3)        │
│                                                                    │
└──────────────────────────────────────────────────────────────────┘
```

---

*Diagnóstico técnico · AguaMind OS · Hackathon UNIAJC 2026*
*Fuentes: tesis UNIAJC 2024-2025 + observación directa*
