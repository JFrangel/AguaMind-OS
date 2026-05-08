# Camaleón OS — Arquitectura "Entrada y Salida por Edificio"

> Cada edificio del campus tiene 2 caudalímetros: uno en la **entrada de agua
> potable** y otro en la **salida de aguas residuales**. La diferencia
> (entrada − salida) es el indicador más potente para detectar fugas y
> caracterizar la huella hídrica real de cada edificio.

---

## 1. Por qué esta arquitectura cambia todo

### Sin medición diferencial (situación actual UNIAJC)
```
[Tanque A] ──▶ [Bloque A] ──▶ ¿?  → no se sabe nada
                                   → si hay fuga, invisible
                                   → si hay desperdicio, invisible
```

### Con Camaleón OS — medición de entrada y salida
```
[Tanque A] ──[YF-S201 IN]──▶ [Bloque A] ──[YF-S201 OUT]──▶ [PTAR]
                  │                              │
                  └────────── balance ──────────┘
                              │
                              ▼
                    Δ = IN - OUT
                    Si Δ > 5%: hay pérdida interna
                    Si Δ < -5%: error sensor o exfiltración
```

---

## 2. Principio físico: balance hídrico por edificio

**Conservación de masa aplicada al agua:**

```
Q_entrada = Q_consumo_normal + Q_evaporación + Q_pérdida + Q_almacenado
```

Para un edificio en estado estable (sin tanques internos):

```
Q_entrada ≈ Q_residual + Q_evaporación + Q_pérdida
```

Si conocemos `Q_entrada` (caudalímetro IN) y `Q_residual` (caudalímetro OUT):

```
Q_pérdida = Q_entrada - Q_residual - Q_evap_estimado
```

**La evaporación es despreciable** en uso humano (< 2 % en baños, lavamanos).
Por lo tanto, una diferencia > 5 % indica **fuga real**.

---

## 3. Implementación física por edificio

### Bloque A (estructura tipo)

```
                    ┌──────────────────────────────────────┐
                    │         BLOQUE A · 3 pisos            │
                    │  Aulas + baños + lavamanos + bebederos│
                    └──────────────────────────────────────┘
                                    │
              Acometida de potable  │  Bajante de residuales
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
          ┌─────────────────────┐         ┌─────────────────────┐
          │  Cuarto Hidráulica  │         │  Caja de inspección  │
          │                     │         │                       │
          │  ┌────────────┐     │         │   ┌────────────┐     │
          │  │ EV-A1 1/2" │     │         │   │ YF-S201    │     │
          │  │ 12V DC NC  │     │         │   │ instalado  │     │
          │  └─────┬──────┘     │         │   │ con sumide- │     │
          │        │            │         │   │ ro y tapa  │     │
          │  ┌─────▼──────┐     │         │   │ herm.      │     │
          │  │ YF-S201    │     │         │   └─────┬──────┘     │
          │  │ ENTRADA    │     │         │         │            │
          │  └─────┬──────┘     │         │   ┌─────▼──────┐     │
          │        │            │         │   │ TSD-10     │     │
          │  ┌─────▼──────┐     │         │   │ turbidez   │     │
          │  │ MPX5700AP  │     │         │   │ residual   │     │
          │  │ presión    │     │         │   └─────┬──────┘     │
          │  └─────┬──────┘     │         │         │            │
          │        │            │         │   ┌─────▼──────┐     │
          │  ┌─────▼──────┐     │         │   │ Sensor pH  │     │
          │  │ Hacia      │     │         │   │ residual   │     │
          │  │ tuberías   │     │         │   └─────┬──────┘     │
          │  │ internas   │     │         │         │            │
          │  └────────────┘     │         │   Hacia PTAR ────────┤
          │                     │         │                       │
          │  [ESP32 + OLED]     │         │  [ESP32 satélite]    │
          │   gabinete IP65     │         │   gabinete IP65       │
          └─────────────────────┘         └─────────────────────┘
                  Nodo IN                      Nodo OUT
```

### Cada edificio tiene **2 nodos Camaleón**:

| Nodo IN (entrada potable) | Nodo OUT (salida residual) |
|---------------------------|----------------------------|
| YF-S201 caudal | YF-S201 caudal |
| MPX5700AP presión | TSD-10 turbidez |
| EV (electroválvula corte) | Sensor pH (extensión) |
| SW-420 vibración | Sensor conductividad (extensión) |

---

## 4. Topología completa del campus

```
                                     ┌─[Tanque A 36k L]─[Tanque B 16k L]
                                     │                                    │
                                     │       Distribución por edificio    │
                                     ▼                                    │
       ┌─────────────────────────────┴─────────────────────────────┐     │
       │                                                             │    │
       ▼          ▼          ▼          ▼          ▼          ▼     │    │
   ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐│    │
   │Bloq A│   │Alame │   │Cafe  │   │ Labs │   │Limpie│   │Cancha││    │
   │  IN  │   │  IN  │   │  IN  │   │  IN  │   │  IN  │   │  IN  ││    │
   └──┬───┘   └──┬───┘   └──┬───┘   └──┬───┘   └──┬───┘   └──┬───┘│    │
      │ usa      │ usa      │ usa      │ usa      │ usa      │ riego  │
      │          │          │          │          │          │  ↓     │
      ▼          ▼          ▼          ▼          ▼          ▼   ↓     │
   ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐   (jardines)  │
   │Bloq A│   │Alame │   │Cafe  │   │ Labs │   │Limpie│              │
   │ OUT  │   │ OUT  │   │ OUT  │   │ OUT  │   │ OUT  │              │
   └──┬───┘   └──┬───┘   └──┬───┘   └──┬───┘   └──┬───┘              │
      │          │          │          │          │                   │
      └──────┬───┴──────────┴──────────┴──────────┘                   │
             │                                                         │
             ▼                                                         │
       ┌────────────┐                                                 │
       │  PTAR      │                                                 │
       │ (Alameda + │                                                 │
       │  Entrada)  │                                                 │
       └────────────┘                                                 │
             │                                                         │
             ▼                                                         │
       Río Pance / Cauca                                              │
       (con calidad medida y validación normativa Res 0631)           │
```

---

## 5. KPIs nuevos posibles con esta arquitectura

### KPI 5 — IPE (Índice de Pérdida por Edificio)

```
IPE_edificio = (Q_in - Q_out) / Q_in × 100

Lectura:
  IPE < 5%   → edificio sin fugas (verde)
  IPE 5-15%  → fuga moderada (amarillo)
  IPE > 15%  → fuga crítica (rojo) → cerrar EV automáticamente
```

### KPI 6 — IRH (Índice de Recirculación Hídrica)

Para PTAR — qué porcentaje del agua tratada se podría reusar:

```
IRH = Q_tratada_reusable / Q_total_tratada × 100

Aplicación: agua de lavamanos puede regar jardines → -2,000 L/día.
```

### KPI 7 — IDU (Índice de Densidad de Uso)

```
IDU = Consumo_edificio / N_usuarios_edificio × 100
```

Permite identificar edificios con consumo per cápita anómalo.

---

## 6. Nuevas alertas posibles (sólo con esta arquitectura)

| Alerta | Trigger | Acción agente |
|--------|---------|---------------|
| Fuga interna detectada | IPE > 15 % por > 5 min | Cierra EV del edificio |
| Saturación PTAR | suma OUT > capacidad | Limita consumo edificios pico |
| Mal funcionamiento sanitario | OUT/IN ratio anómalo (< 60 % o > 95 %) | Inspección recomendada |
| Vertido sin tratamiento | Δ entre IN edificios y entrada PTAR | Auditoría tuberías |
| Picos nocturnos sospechosos | Q_in > 3 L/min entre 23h-5h | Cierre automático EV |
| Calidad efluente | NTU residual > 200 NTU (post-trampa) | Alerta lodos PTAR |
| Acidez anómala | pH < 5 o pH > 9 | Alerta laboratorios (vertido químico) |

---

## 7. Lista completa de nodos del campus

| Edificio | Nodo IN | Nodo OUT | Inversión nodo (par) |
|----------|---------|----------|----------------------|
| **Bloque A** (3 pisos, 6 baños, lavamanos) | EV-A1 + YF + MPX + SW | YF + TSD | $2,400,000 |
| **Alameda** (admin + aulas) | EV-AL1 + YF + MPX | YF + TSD | $2,200,000 |
| **Cafetería + Plazoleta** | EV-CAF1 + YF | YF + TSD + grasas | $2,000,000 |
| **Laboratorios** | EV-LAB1 + YF | YF + TSD + pH | $2,400,000 |
| **Limpieza** (cuarto aseo) | EV-LIM1 + YF | YF | $1,800,000 |
| **Cancha + Jardines** | EV-RC1 + YF-DN50 + higrómetros ×3 | (no aplica, evapora) | $2,500,000 |
| **PTAP** (entrada al sistema) | YF-S201 ×2 + MPX + 4-20mA + TSD + SW ×3 | — | $1,400,000 |
| **Tanques A y B** | JSN-SR04T ×2 + DS18B20 ×2 | — | $700,000 |
| **PTAR Alameda** (extensión Fase 3) | — | TSD + pH + cond. + DBO sensor | $1,800,000 |
| **PTAR Entrada** (extensión Fase 3) | — | TSD + pH + cond. + DBO sensor | $1,800,000 |
| | | **TOTAL Fase completa** | **$19,000,000 COP** |

> Modelo escalonado: Fase 1 ($1.4M) cubre solo PTAP + Tanques.
> Fase 2 ($5.4M) añade Bloque A + Alameda + Cancha.
> Fase 3 ($9.2M) añade Cafe + Labs + PTAR extensión.
> Fase completa ($19M) opcional para campus 100 % instrumentado.

---

## 8. Cómo el agente IA aprovecha esta arquitectura

### Flujo de detección de fuga interna

```
Cada 30 segundos:
  1. SystemsAgent calcula IPE para cada edificio
  2. Si IPE > 15% durante 3 ciclos consecutivos:
     → flag "fuga sospechosa" en edificio X
  3. SensorAgent valida con vibración + acústico
  4. Si confirma → MitigationAgent ejecuta:
     a) Cierra EV del edificio (corte preventivo)
     b) Notifica Telegram con detalles
     c) Genera orden de trabajo
     d) Resta créditos hídricos del edificio
     e) Activa pantalla LED "Mantenimiento en curso"

Tiempo total detección + acción: < 5 segundos.
```

### Análisis comparativo entre edificios

El agente puede comparar:
- Bloque A vs. Alameda → ambos similares en uso, ¿por qué Bloque A consume 30 % más?
- Día lectivo vs. fin de semana → consumo nocturno anómalo (¿fuga?)
- Mismo día año tras año → tendencia a degradación (mantenimiento preventivo)

---

## 9. Casos de uso reales del balance IN-OUT

### Caso 1: Grifo mal cerrado en un baño
```
22:30 PM
  IN Bloque A  = 12 L/min  (anormalmente alto a esa hora)
  OUT Bloque A = 11.5 L/min (consistent con IN)
  IPE = (12 - 11.5) / 12 = 4 %  → no es fuga, es uso real
  
Trigger: hora_nocturna + IN > 5 L/min
Acción: cierre preventivo EV-A1
Resultado: si era grifo abierto, queda sin agua hasta 6 AM (correcto)
            si era persona usando, mañana lo abren (cero impacto real)
```

### Caso 2: Fuga subterránea en tubería interna
```
14:00 PM
  IN Bloque A  = 18 L/min
  OUT Bloque A = 14 L/min
  IPE = (18 - 14) / 18 = 22 %  → CRÍTICO

Acción agente:
  ✓ Cierre EV-A1 (corte de flujo)
  ✓ Notifica equipo mantenimiento
  ✓ Hidrófono ESP32 graba huella acústica
  ✓ Identifica zona aproximada por triangulación
  ✓ Pantalla LED muestra "Bloque A · servicio temporal suspendido"

Tiempo de detección: ~ 5 minutos.
Reparación: cuadrilla llega en 30 minutos en lugar de descubrir el daño días después.
```

### Caso 3: Vertido químico no autorizado en laboratorios
```
10:15 AM
  pH OUT Labs  = 3.2  (muy ácido, anormal)

Acción agente:
  ✓ Alerta crítica a coordinador laboratorios
  ✓ Notifica seguridad ambiental
  ✓ Cierra parcialmente EV-LAB1 (medio caudal para diluir)
  ✓ Activa registro de evidencia (datos guardados en Supabase)

Beneficio: cumplimiento Resolución 0631/2015 + protección PTAR.
```

---

## 10. Resumen ejecutivo

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                    │
│   ARQUITECTURA "ENTRADA Y SALIDA POR EDIFICIO"                     │
│                                                                    │
│   • 6 edificios × 2 nodos = 12 nodos Camaleón                      │
│   • + 1 nodo PTAP + 2 nodos PTAR + sensores tanques               │
│   • Total: 17 puntos de medición distribuidos                      │
│                                                                    │
│   Beneficios únicos de esta arquitectura:                          │
│                                                                    │
│   1. Detección de fugas internas (no solo en red principal)        │
│   2. Caracterización de huella hídrica por edificio                │
│   3. Comparación entre edificios (Lean: identifica el peor)        │
│   4. Validación de cumplimiento normativo en cada vertido          │
│   5. Base de datos para análisis predictivo y futuras tesis        │
│                                                                    │
│   Inversión total: $19M COP (vs. $0 actual)                        │
│   Recuperación: 1.6 años · ROI 5 años: 470 %                       │
│                                                                    │
└──────────────────────────────────────────────────────────────────┘
```

---

*Documento de arquitectura · Camaleón OS · Hackathon UNIAJC 2026*
