# Camaleón OS — Estrategia de Mitigación y Acción Activa

> Cómo el agente IA pasa de **avisar** a **actuar**: cierra válvulas, reduce
> presiones, dispara campañas de gamificación y propone obras de infraestructura.
> Plan de despliegue por fases para un campus que **arranca sin sensores físicos**.

---

## 1. Filosofía: del aviso a la acción

| Generación | Lo que hace | Ejemplo |
|---|---|---|
| 1ª · Reactiva | Personal va al sitio cuando ve el recibo alto | "Llegó la factura de $20M, vayan a buscar la fuga" |
| 2ª · Monitoreo | Sensores muestran el problema | "El dashboard dice TPP 25%" |
| 3ª · Notificación | Sistema envía alertas | "Telegram avisó que hay vibración" |
| **4ª · Acción autónoma** | **El sistema actúa por sí solo** | **"Detecté fuga en zona 3 → cerré válvula → notifiqué al equipo + comunidad"** |

**Camaleón OS opera en la 4ª generación.**

---

## 2. ¿Qué exactamente vamos a mitigar?

Identificamos **8 problemas concretos** del campus UNIAJC Sede Sur que Camaleón OS ataca con acciones específicas:

| # | Problema | Sensor que detecta | Acción que mitiga |
|---|----------|-------------------|-------------------|
| 1 | **Fuga oculta en red** (20-30% pérdida invisible) | Hidrófono acústico + caudal + presión | Electroválvula cierra el sector afectado |
| 2 | **Grifos mal cerrados nocturnos** | Caudal + horario | Electroválvula reduce presión nocturna a 0 |
| 3 | **Sobreconsumo de riego** (>13.000 L/día) | Caudal zona riego + humedad suelo | Solenoide cierra riego, programa horario nocturno |
| 4 | **Tanque desbordado** (sobreproducción) | Nivel ultrasónico + electroválvula | Apaga bomba ANTES de que rebose |
| 5 | **Acuífero sobreexplotado** | Nivel freático 4-20mA | Reduce extracción + alerta crítica |
| 6 | **Agua turbia entrando a la red** | Turbidez TSD-10 | Cierra válvula salida tanque + alerta sanitaria |
| 7 | **Picos de demanda no esperados** | IA predictiva sobre histórico | Pre-llena tanque + ajusta presiones |
| 8 | **Conducta humana derrochadora** | Datos por edificio + reporte QR | Gamificación + ranking + créditos hídricos |

---

## 3. Sensores y Actuadores — Lista Completa

### Sensores (perciben)

| # | Sensor | Modelo | Costo | Mide |
|---|--------|--------|-------|------|
| 1 | Caudal Hall | YF-S201 ×2 | $25K c/u | Pulsos por flujo (1-30 L/min) |
| 2 | Presión piezo | MPX5700AP | $45K | 0-700 kPa en red |
| 3 | Nivel ultrasónico | JSN-SR04T ×2 | $30K c/u | Distancia en cm (0-450) |
| 4 | Vibración piezoeléctrica | SW-420 ×3 | $10K c/u | ON/OFF anomalía mecánica |
| 5 | Nivel freático | Transductor 4-20mA | $180K | Profundidad agua (0-10 m) |
| 6 | Turbidez óptica | TSD-10 | $55K | NTU calidad (0-10) |
| 7 | **🆕 Hidrófono acústico** | INMP441 / piezo + ESP32 ML | $35K c/u | **Huella acústica de fugas** |
| 8 | **🆕 Higrómetro suelo** | Capacitivo HW-080 | $8K c/u | **Humedad suelo (jardines)** |

### Actuadores (actúan)

| # | Actuador | Modelo | Costo | Acción |
|---|----------|--------|-------|--------|
| A | **🆕 Electroválvula 1/2"** | DC 12V solenoide | $80K c/u | Cierra/abre flujo (baños, riego) |
| B | **🆕 Variador de frecuencia bomba** | VFD pequeño 1HP | $450K | Reduce presión sin apagar |
| C | **🆕 Relay para bomba** | 30A SSR | $25K | ON/OFF bomba principal |
| D | LED RGB + Buzzer local | Stock | $8K | Alerta visual/sonora en sitio |
| E | OLED pantalla pública | SSD1306 + Pi Zero | $80K | "Pulso hídrico" en hall edificio |

### Nodo completo "Camaleón Action Node"

```
ESP32 + 8 sensores + 3 electroválvulas + 1 relay + display + acceso WiFi
Costo aproximado: $1,800,000 COP por nodo (inversión inicial)
Cobertura típica: 1 edificio completo o 1 punto crítico (PTAP)
```

---

## 4. El MitigationAgent — Quinto Agente del Sistema

Hasta ahora teníamos 4 agentes (Orchestrator + Systems + Sensor + Industrial). Añadimos el **MitigationAgent** que recibe la decisión consolidada y ejecuta acciones físicas/sociales.

```
              [Orchestrator]
                    │
       ┌────────────┼────────────┐
       ▼            ▼            ▼
   Systems      Sensor       Industrial
       │            │            │
       └────────┬───┴────────────┘
                ▼
            DECISIÓN
                ▼
       ┌────────────────────┐
       │ MitigationAgent    │  ← 5º agente: ejecuta acciones
       └─────────┬──────────┘
                 │
    ┌────────┬───┴────────┬────────┐
    ▼        ▼            ▼        ▼
  Físicas   Sociales    Comunitarias  Operativas
  ───────   ────────    ────────────  ──────────
  • Cerrar  • Telegram  • Ranking     • Programar
    válvula   alerta      edificios     mantto
  • Bajar   • Push      • Créditos    • Pre-llenar
    presión   masivo      hídricos      tanque
  • Apagar  • Reporte   • Campañas    • Ajustar
    bomba     QR público  awareness     horario
```

### Reglas de decisión del MitigationAgent

```python
SI (vibración OR caudal_anómalo > 30%) Y (presión_caída > 20%):
    ▶ ejecutar_accion("cerrar_valvula", zona=zona_afectada)
    ▶ notificar_telegram("crítica", incluir_action_taken=True)
    ▶ generar_orden_trabajo()

SI (es_horario_nocturno) Y (caudal_baño > 5 L/min):
    ▶ ejecutar_accion("reducir_presion", zona="baños", nivel=0)
    ▶ programar_apertura(hora="06:00")

SI (turbidez > 4 NTU sostenida 5 min):
    ▶ ejecutar_accion("cerrar_salida_tanque")
    ▶ notificar_sanidad()
    ▶ activar_protocolo_calidad()

SI (riego > expected × 2.5) Y (humedad_suelo > 70%):
    ▶ ejecutar_accion("cerrar_riego")
    ▶ replantear_horario_nocturno()

SI (consumo_edificio > meta_mensual):
    ▶ ejecutar_accion("publicar_ranking")
    ▶ enviar_telegram_grupo_edificio()
    ▶ ajustar_creditos_hidricos(restar=delta)
```

---

## 5. Estrategia "Smart Water Ledger" — Gamificación

Convertir cada gota ahorrada en valor tangible para la comunidad universitaria.

### Sistema de Créditos Hídricos

```
1 Crédito Hídrico = 1 m³ de agua ahorrada vs. línea base mensual

Cada edificio (Bloque A, Alameda, Cancha, etc.) acumula créditos.
Ranking mensual público en pantallas LED + dashboard.

Conversión a beneficios (presupuesto del ahorro real):
  100 créditos  →  $350,000 COP  →  Mejora zona común
  500 créditos  →  $1,750,000    →  Renovación cafetería
1,000 créditos  →  $3,500,000    →  Proyecto propuesto por estudiantes
```

### Reporte QR Comunitario

Pegar QR en baños, jardines, cafetería:

```
┌──────────────────────────────────┐
│   Camaleón OS — Reporte rápido    │
│                                    │
│   ┌──────────┐                    │
│   │   QR     │  Escanea para      │
│   │  CODE    │  reportar fuga     │
│   └──────────┘                    │
│                                    │
│   "Tu reporte = +20 puntos        │
│   bienestar universitario"         │
└──────────────────────────────────┘
```

Flujo:
1. Usuario escanea QR del baño X
2. Telegram bot abre con prefilled `/reportar bloque-A-baño-2`
3. Usuario describe en texto/foto
4. SensorAgent valida con datos de caudal en tiempo real
5. Si confirma anomalía → +20 puntos al usuario, ticket de mantenimiento
6. Si falsa alarma → +5 puntos por colaboración (no se penaliza)

---

## 6. Plan de Despliegue por Fases (campus que arranca SIN sensores)

UNIAJC Sede Sur **no tiene baños con sensores hoy**. El plan respeta esa realidad y avanza por fases con valor incremental.

### Fase 0 — MVP de Hackathon (Ya ejecutado)
**Inversión: $0 · Tiempo: 2 días**

- ✅ Backend completo con simulador realista (datos de las tesis UNIAJC)
- ✅ Dashboard funcional con 4 tabs
- ✅ Multi-agente IA con decisiones autónomas
- ✅ Bot Telegram con 12 comandos
- ✅ Documentación profesional + PDF + diagramas
- ✅ Demo end-to-end inyectando escenarios de fuga

**Entrega al jurado:** todo el sistema corriendo, demostrando viabilidad sin necesidad de hardware físico.

### Fase 1 — Piloto en PTAP (Mes 1)
**Inversión: $1,800,000 · ROI: 21 días**

```
Objetivo: 1 nodo físico en la PTAP (entrada al sistema)
Sensores: 6 (caudal × 2 + presión + nivel × 2 + vibración)
Actuadores: 1 relay para bomba + 1 electroválvula salida
Cobertura: caudal de entrada + tanques A y B

Resultado esperado:
  • Visibilidad del 100% del agua que entra al campus
  • Detección de pérdidas en < 5 minutos
  • Activación bomba automatizada
```

### Fase 2 — Expansión a 5 puntos críticos (Meses 2-3)
**Inversión: $5,400,000 acumulada · Cobertura: 80% del campus**

```
Nodos adicionales:
  Nodo 2: Bloque A (entrada principal) — caudal + electroválvula
  Nodo 3: Cancha + jardines — caudal + higrómetro + solenoide riego
  Nodo 4: Cafetería + laboratorios — caudal + turbidez
  Nodo 5: Red distribución — hidrófono acústico + presión

Resultado esperado:
  • TPP de 25% a 12% (medible)
  • Detección de fugas por huella acústica
  • Riego automatizado fuera de hora pico
```

### Fase 3 — Sensorización masiva (Meses 4-6)
**Inversión: $9,200,000 acumulada · Cobertura: ~60% de baños**

```
Nodos adicionales:
  Nodos 6-15: 1 nodo por sub-circuito de baños
  10 baños críticos con caudal individual + electroválvula
  Hidrófonos en uniones críticas

Resultado esperado:
  • Cierre nocturno automático de baños sin uso
  • Detección de grifos mal cerrados en < 2 minutos
  • Datos de consumo individuales por edificio
  • TPP < 10% (meta hackathon alcanzada)
```

### Fase 4 — Smart Water Ledger (Meses 6-9)
**Inversión: $11,000,000 acumulada · Gamificación activa**

```
Software adicional:
  • Sistema de Créditos Hídricos por edificio
  • App móvil con QR para reportes ciudadanos
  • Pantallas LED en hall de edificios ("pulso hídrico")
  • Eco-competencia mensual entre facultades
  • Integración con bienestar universitario (puntos canjeables)

Resultado esperado:
  • 10-15% reducción adicional por cambio cultural
  • Engagement comunitario alto (>40% estudiantes participan)
  • Casos de éxito documentables para replicación
```

### Fase 5 — Gemelo Digital + AR (Meses 9-12)
**Inversión: $13,500,000 acumulada · Posicionamiento Smart Campus**

```
Tecnología avanzada:
  • Modelo 3D de toda la red hidráulica de la sede
  • Realidad Aumentada para mantenimiento (tabletas)
  • Dashboard avanzado con simulación predictiva
  • Publicación open-source y modelo replicable

Resultado esperado:
  • Tiempo de respuesta a fallos: minutos (no horas)
  • Posicionamiento como Smart Campus pionero
  • Replicación a otras sedes UNIAJC (Norte, Centro)
```

---

## 7. ¿Qué hace Camaleón OS sin baños sensorizados?

Pregunta clave: **"La universidad no tiene sensores en baños hoy. ¿Cómo arranca Camaleón OS?"**

Respuesta: **el sistema funciona de forma incremental, agregando valor desde el primer día.**

### Día 1 (sin sensores)
- Simulador realista con datos de las tesis UNIAJC
- Dashboard demuestra cómo se vería con datos reales
- Telegram envía alertas inyectadas para entrenar al personal
- Reporte QR ya activo para que la comunidad reporte fugas manualmente
- Generación de PDFs diarios con análisis Lean

### Mes 1 (1 nodo en PTAP)
- Datos REALES del caudal de entrada y tanques
- TPP medible por primera vez en la historia del campus
- IA aprende patrones del campus

### Mes 3 (5 nodos)
- 80% del agua bajo medición real
- Acciones de mitigación en tiempo real (válvulas)
- Reportes ciudadanos validados por IA

### Mes 6+ (sensorización masiva)
- Sistema completo con gamificación y créditos hídricos

---

## 8. Cómo el agente avisa sobre la mitigación

Cuando el MitigationAgent ejecuta una acción, **debe documentar y comunicar** automáticamente:

### Mensaje Telegram típico (acción ejecutada)

```
🛡️ Camaleón OS — Acción de Mitigación Ejecutada
─────────────────────────────────────────────────
Tipo:     CIERRE DE VÁLVULA AUTOMÁTICO
Trigger:  Vibración + caída de presión 28%
Zona:     Bloque A · Sub-circuito Baños 2do piso
Hora:     14:32:18 (07/05/2026)

Análisis del agente:
  • SystemsAgent: TPP saltó 18% en 90 segundos
  • SensorAgent:  Hidrófono detectó huella acústica de fuga
  • IndustrialAgent: Coincide con muda Defectos histórica

Acción ejecutada:
  ✓ Electroválvula EV-A2 cerrada (corte de flujo)
  ✓ Bomba pasó a modo standby
  ✓ Generada orden de trabajo OT-2026-0142
  ✓ Notificado al equipo de mantenimiento
  ✓ Pantalla LED Bloque A muestra "Mantenimiento en curso"

Impacto evitado:
  ~14,500 L que se habrían perdido en las próximas 6 horas
  ~$50,750 COP en costo de agua
  ~0.012 ton CO₂ por bombeo innecesario

Próximo paso recomendado:
  Inspección física del tramo entre uniones J7 y J8
  Tiempo estimado de reparación: 2-3 horas

[Ver dashboard →]  [Marcar como atendida]
```

### En el Dashboard

Tab nuevo: **"Mitigación"** con:
- Acciones recientes ejecutadas (timeline)
- Válvulas controladas remotamente (estado on/off)
- Órdenes de trabajo generadas
- Impacto acumulado (litros + dinero + CO₂ evitados)
- Comandos manuales (cerrar/abrir válvula con confirmación)

---

## 9. ODS Profundizado (no solo etiquetas)

Cómo cada acción de Camaleón OS aporta a un ODS específico:

| ODS | Meta concreta | Cómo Camaleón aporta | Métrica medible |
|-----|---------------|----------------------|------------------|
| **6** Agua limpia | 6.4 Aumentar eficiencia uso agua | TPP de 25% a 10% en 6 meses | Litros recuperados/año |
| **6** Agua limpia | 6.b Apoyar gestión comunitaria | Reportes QR + créditos hídricos | # reportes/mes ciudadanos |
| **4** Educación calidad | 4.7 Educación para sostenibilidad | Modelo educativo open-source | # estudiantes participantes |
| **9** Industria, innovación | 9.4 Modernizar infraestructura | Sensorización IoT+IA | # nodos activos |
| **9** Industria, innovación | 9.5 Investigación científica | Datos abiertos para tesis UNIAJC | # papers publicados |
| **11** Ciudades sostenibles | 11.6 Reducir impacto ambiental | Reducción extracción acuífero | m³ menos extraídos/año |
| **12** Producción responsable | 12.5 Reducir desperdicios | Lean + automatización válvulas | # acciones de mitigación |
| **13** Acción climática | 13.3 Mejorar capacidad adaptación | Resiliencia ante sequía | Días autonomía acuífero |

---

## 10. Resumen ejecutivo de la mitigación

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                   │
│   Camaleón OS NO solo monitorea — ACTÚA.                         │
│                                                                   │
│   Cuando el agente detecta un problema, en menos de 30s:         │
│                                                                   │
│   1. Cierra la válvula del sector afectado                       │
│   2. Notifica por Telegram con detalle de la acción tomada       │
│   3. Genera orden de trabajo automática                          │
│   4. Calcula impacto evitado (litros + dinero + CO₂)             │
│   5. Activa la pantalla LED del edificio                         │
│   6. Resta créditos hídricos del edificio responsable            │
│                                                                   │
│   Resultado: 30-40% reducción de pérdidas en el primer año.      │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

*Documento técnico de mitigación · Camaleón OS · Hackathon UNIAJC 2026*
