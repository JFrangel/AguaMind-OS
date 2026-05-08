# Camaleón OS · Resumen para leer y entender todo

> Una hoja para entender el proyecto en 5 minutos. Después, navegar al doc específico
> según el rol o la pregunta. Para el jurado, equipo, asesor o cualquier persona
> nueva que llegue al proyecto.
>
> Hackathon UNIAJC 2026 · Cali, Colombia

---

## En 1 minuto · ¿qué es esto?

UNIAJC Sede Sur tiene una planta de tratamiento de agua del 2011 que **nunca tuvo medición**. Pierde 1,587 L/día sin saberlo. Tiene 4 químicos fuera de norma. Tiene 2 PTAR sobrecargadas 2.06×.

**4 tesis UNIAJC diagnosticaron el problema entre 2021 y 2025. Ninguna pasó a operación.**

**Camaleón OS** es un sistema que toma esos 4 diagnósticos y los lleva a operación con:
- 6 sensores IoT de bajo costo conectados a un ESP32
- 5 agentes de inteligencia artificial que deliberan en 5 segundos
- Un dashboard web con vista 3D del campus + bot de Telegram
- 5 estrategias automáticas ante fenómenos (sequía, lluvias, sismo, contaminación, pico demanda)

**Inversión Fase 1: $1.43M COP. Ahorro proyectado: $20.5M/año. ROI: 25 días. Open source MIT.**

---

## El problema en 5 puntos

1. **Sin medición desde 2011**: la PTAP no tiene caudalímetros, ni sensores de nivel, ni instrumentación para calidad. El operario opera "a ojo".
2. **Calidad fuera de norma** (Resolución 2115/2007): cloro residual, fosfatos, nitratos y pH miden sistemáticamente fuera de los límites legales.
3. **Pérdidas no contabilizadas**: Sánchez Sotelo (2021) midió 1,587 L/día perdidos por la noche con un método manual. Anuales: 579 m³ = $1.1M COP.
4. **Mantenimiento solo correctivo**: Gómez Mina (2022) catalogó 13 equipos sin programa preventivo. Cuando algo se daña, queda inutilizado por días.
5. **PTAR sobrecargado**: 2 PTAR × 2 módulos × 1,000 estudiantes = 4,000 cap, pero hay 8,234 usuarios reales (2.06× sobre).

**Exposición legal potencial: $16,900 millones COP** (suspensión IRCA + revocatoria CVC + multas vertimientos + multas Habeas Data).

---

## La solución en 5 puntos

1. **Caracterización en vivo, no más diagnósticos en PDF**: 6 sensores físicos miden cada 30 segundos lo que las tesis midieron una vez.
2. **Agente IA multi-agente que delibera 24/7**: 5 sub-agentes (Orchestrator, Systems, Sensor, Industrial, Mitigation) coordinados con LangGraph. Voto consensual 3-de-5 antes de actuar.
3. **Tres niveles de análisis encadenados**:
   - **Descriptivo**: ¿qué pasó? (KPIs, tendencias, heatmaps)
   - **Predictivo**: ¿qué va a pasar? (Random Forest, LSTM, ARIMA)
   - **Prescriptivo**: ¿qué hacemos? (cierra EV, reporta CVC, optimiza bombeo)
4. **Cumplimiento normativo automatizado**: reportes mensuales firmados con SHA-256 a INVIMA, CVC y Min. Vivienda. Trazabilidad legal sin trabajo manual.
5. **Híbrido con el método tradicional**: el operario sigue midiendo "tanques nocturnos" cada mañana. Camaleón cruza los datos. Si difieren > 5 cm hay un problema (sensor o marca dañados). Doble método independiente = más confianza.

---

## Números clave (memorizar)

| Concepto | Valor | De dónde |
|----------|-------|----------|
| Usuarios totales del campus | **8,234** | Caycedo & Jaramillo 2021 |
| Pérdida nocturna medida | **1,587 L/día** | Sánchez Sotelo 2021 |
| Equivalencia tanque | **1 cm = 160 L** | Sánchez Sotelo 2021 |
| Capacidad PTAR total | **4,000 est** (2×2×1,000) | RETO oficial PDF |
| Sobrecapacidad PTAR | **2.06×** | 8,234 ÷ 4,000 |
| Demo Fase 0 (backend mínimo) | **$1,431,000 COP** | BOM Camaleón OS |
| Piloto Fase 1 AQUA-ROI Lite | **$5,570,000 COP** | BOM compañero electrónica |
| Propuesta completa | **$37,376,807 COP** | Arias Montoya 2024 |
| Ahorro anual | **$20,536,425 COP** | Proyectado |
| Período recuperación | **~25 días** | Conservador |
| Relación B/C | **17.4×** | TIR > 1,000% |
| Exposición legal evitada | **$16,900M COP** | 4 sanciones combinadas |
| Agua recuperada 5 años | **16.5M L** | TPP 25→10% |
| CO₂ evitado 5 años | **7.6 ton** | Bombeo eficiente |
| Litros / minuto se pierden ahora | **~9 L/min** | Apertura del pitch |

---

## Mapa de la documentación · qué leer según tu rol

### Si eres del jurado (1 documento)
**Lee:** [TESIS-CAMALEON-OS.md](TESIS-CAMALEON-OS.md)
Documento estilo tesis con 20 secciones formales. 30-40 minutos de lectura. Cubre el 100% de la rúbrica.

### Si eres del equipo y necesitas defender el pitch (3 documentos)
1. [HOJA-PITCH-Q&A.md](HOJA-PITCH-Q&A.md) — 8 preguntas anticipadas con respuestas listas
2. [PITCH-DEFINITIVO.md](PITCH-DEFINITIVO.md) — pitch 5 min cronometrado
3. [CAMALEON-OS-MASTER.md](CAMALEON-OS-MASTER.md) — doc maestro con números y datos

### Si eres dev y vas a tocar código (3 documentos)
1. [ANALISIS-Y-CAPAS-VISUALES.md](ANALISIS-Y-CAPAS-VISUALES.md) — arquitectura por capas
2. [IMPLEMENTACION-VISUAL-CAPAS.md](IMPLEMENTACION-VISUAL-CAPAS.md) — qué hace cada capa
3. [ALMACENAMIENTO-DE-DATOS.md](ALMACENAMIENTO-DE-DATOS.md) — schema SQL + estrategia de retención

### Si eres asesor y quieres ver compliance (2 documentos)
1. [AUDITORIA-RUBRICA.md](AUDITORIA-RUBRICA.md) — auditoría honesta vs los 11 criterios
2. [RETO-VS-CAMALEON.md](RETO-VS-CAMALEON.md) — mapeo línea por línea contra RETO PDF

### Si quieres validar la base académica (1 documento)
[TESIS-VS-CAMALEON.md](TESIS-VS-CAMALEON.md) — cómo cada hallazgo de las 6 tesis previas está reflejado en el código.

---

## Resumen de cada documento (1 párrafo)

### Documentos transversales

**[TESIS-CAMALEON-OS.md](TESIS-CAMALEON-OS.md)** · Documento estilo tesis con resumen, abstract, problemática, objetivos, justificación, marco referencial, marco teórico, marco legal, metodología, desarrollo, análisis, conclusiones, recomendaciones, referencias y anexos. Es el documento "todo en uno" para entrega académica formal.

**[CAMALEON-OS-MASTER.md](CAMALEON-OS-MASTER.md)** · Doc maestro post-asesoría jurado del 7 de mayo. 19 capítulos: feedback del jurado, problema, datos validados de 4 tesis, solución, estrategia de datos, sensores, modelo 3D, estrategias derivadas, multi-agente, mitigación, normativas, fases, costo-beneficio, ODS, pitch, Q&A, roles, referencias.

**[CAMALEON-OS-DOCUMENTACION.md](CAMALEON-OS-DOCUMENTACION.md)** · Doc técnico v1.0 explicando qué es, qué problema resuelve, qué hace de novedoso, arquitectura, los 3 retos cubiertos (Sistemas/Electrónica/Industrial), costo-beneficio, ODS, equipo.

### Documentos de pitch y defensa

**[HOJA-PITCH-Q&A.md](HOJA-PITCH-Q&A.md)** · Hoja para llevar al pitch. Las 8 preguntas anticipadas (¿por qué no SCADA?, ¿y si el agente decide mal?, ¿calidad de datos?, ¿estudiantes se gradúan?, ¿próximos 6 meses?, ¿WiFi?, ¿internet cae?, ¿soluciones más baratas?) con respuesta corta, datos respaldo y demo opcional. Apertura y cierre textuales del pitch. Cronómetro de 5 minutos. Checklist del día.

**[PITCH-DEFINITIVO.md](PITCH-DEFINITIVO.md)** · El pitch tal cual se va a decir, 5 minutos cronometrados.

### Documentos de auditoría

**[AUDITORIA-RUBRICA.md](AUDITORIA-RUBRICA.md)** · Cumplimiento honesto vs los 11 criterios de la rúbrica oficial (Novedad 30%, Actividad Inventiva 20%, Aplicación Industrial 30%, Impacto 20%). Auto-evaluación 42-44/44. También riesgos reales donde podemos perder puntos.

**[RETO-VS-CAMALEON.md](RETO-VS-CAMALEON.md)** · Mapeo línea por línea de los 16 ítems mínimos del RETO oficial (4 Sistemas + 4 Electrónica + 8 Industrial). Cada uno con evidencia y archivo donde verificarlo.

**[TESIS-VS-CAMALEON.md](TESIS-VS-CAMALEON.md)** · Por cada una de las 6 tesis UNIAJC, qué problema vio, qué propuso, cómo lo resuelve Camaleón. Tabla resumen costo-beneficio: las tesis $16.5M consultoría vs Camaleón $1.4M operación.

### Documentos técnicos

**[ANALISIS-Y-CAPAS-VISUALES.md](ANALISIS-Y-CAPAS-VISUALES.md)** · Arquitectura por capas con diagramas Mermaid. Trinidad analítica del agente. Sequence diagrams del flujo end-to-end. Diagrama del flujo predictivo y prescriptivo. Mapa cruzado análisis × capas.

**[IMPLEMENTACION-VISUAL-CAPAS.md](IMPLEMENTACION-VISUAL-CAPAS.md)** · Qué se ve en cada capa cuando la abrís: ASCII del campus, mockup OLED, pseudocódigo MicroPython, topic MQTT, schema SQL, mockups por persona (operador, estudiante, admin, inspector). Tabla de "implementado HOY vs proyectado en fases".

**[AQUA-ROI-LITE.md](AQUA-ROI-LITE.md)** · Propuesta del compañero de Electrónica (versión piloto del proyecto). 5 capas, BOM detallado de 18 componentes ($5.57M COP), 3 escenarios costo-beneficio (1.07–1.84 años), 6 mudas Lean, 6M Ishikawa, 5 reglas del agente, plan a prueba de fallos, plan implementación 10 semanas. Integrado a Camaleón OS vía nuevos endpoints `/water/industrial/scenarios` y `/water/industrial/lean`.

**[ALMACENAMIENTO-DE-DATOS.md](ALMACENAMIENTO-DE-DATOS.md)** · Las 5 capas de storage (Edge NVS 1k lecturas → RAM 1h → Postgres 90d → Parquet 5y → PDF auditable). Schema SQL canónico. Frecuencias de muestreo. Volumetría proyectada. Backup ante caídas. Acceso por rol.

**[ARQUITECTURA.md](ARQUITECTURA.md)** · Arquitectura técnica de AgentOS (la plataforma base sobre la que corre Camaleón).

**[ARQUITECTURA-POR-EDIFICIO.md](ARQUITECTURA-POR-EDIFICIO.md)** · Detalle por edificio del campus: Bloque A, Alameda, Cafetería, Labs, Cancha+Jardines, Limpieza.

**[DIAGRAMAS-Y-DISEÑO.md](DIAGRAMAS-Y-DISEÑO.md)** · Diagramas UML profesionales para el reto de Sistemas (componentes, estados del agente, principios UCD, fases de implementación).

### Documentos de electrónica

**[IMPLEMENTACION-TECNICA-SENSORES.md](IMPLEMENTACION-TECNICA-SENSORES.md)** · Esquemático ESP32 + 6 sensores. Acondicionamiento de señal. Calibración pre-instalación con 4 protocolos. ADC ADS1115 16-bit.

### Documentos industriales

**[CUMPLIMIENTO-NORMATIVO-Y-SOLUCIONES.md](CUMPLIMIENTO-NORMATIVO-Y-SOLUCIONES.md)** · 17 normativas mapeadas a soluciones Camaleón. Sanciones potenciales y reportes automatizados.

**[MITIGACION-Y-ESTRATEGIA.md](MITIGACION-Y-ESTRATEGIA.md)** · 5 estrategias automáticas ante fenómenos. Triggers compuestos en backend. Acciones físicas reales (cierre EV, modo bomba, alertas).

**[IMPACTO-AMBIENTAL-Y-ODS.md](IMPACTO-AMBIENTAL-Y-ODS.md)** · 5 ODS directos + 9 indirectos con métricas cuantificadas.

**[INTEGRACION-TESIS-UNIAJC.md](INTEGRACION-TESIS-UNIAJC.md)** · Cómo cada tesis previa alimenta una constante o módulo del código.

**[ESTRATEGIA-RUBRICA.md](ESTRATEGIA-RUBRICA.md)** · Auto-evaluación inicial vs rúbrica oficial. Áreas donde podemos perder puntos. Mitigaciones.

### Documentos de implementación

**[GUIA-RAPIDA.md](GUIA-RAPIDA.md)** · Setup local en 30 minutos. Cómo correr el sistema completo en tu máquina.

**[IMPLEMENTACION.md](IMPLEMENTACION.md)** · Cómo construir TU app encima de AgentOS. Casos reales, código, anti-patrones.

**[FUNCIONALIDADES.md](FUNCIONALIDADES.md)** · Catálogo completo de capacidades del sistema con ejemplos.

**[USO.md](USO.md)** · Referencia API con curl, patrones por framework, cómo extender.

**[DESPLIEGUE.md](DESPLIEGUE.md)** · Despliegue paso a paso a Vercel + Koyeb + Supabase con `gh` CLI.

**[SIMULACION-Y-CONEXION.md](SIMULACION-Y-CONEXION.md)** · Cómo el simulador se conecta al backend. Datos sintéticos realistas.

**[QUE-ES-AGENTOS.md](QUE-ES-AGENTOS.md)** · Qué es la plataforma base AgentOS sobre la que corre Camaleón.

### Documentos de planificación

**[PLAN-CAMALEON.md](PLAN-CAMALEON.md)** · Plan de implementación a 15 años en 10 fases.

**[PLAN-HACKATHON.md](PLAN-HACKATHON.md)** · Plan específico para el hackathon: 90 min para shippear demo.

**[HACKATHON.md](HACKATHON.md)** · Camino MVP en 90 minutos. Patrones de customización.

**[INNOVACION-RADICAL.md](INNOVACION-RADICAL.md)** · 10 diferenciadores que justifican calificación de "Excelente" en novedad.

**[PROBLEMAS-PTAP-PTAR.md](PROBLEMAS-PTAP-PTAR.md)** · Diagnóstico detallado de los problemas físicos por equipo.

**[PREGUNTAS-ASESORIA.md](PREGUNTAS-ASESORIA.md)** · Preguntas formuladas durante asesoría con stakeholders UNIAJC.

**[SYSTEM-PROMPT.md](SYSTEM-PROMPT.md)** · Prompt de ingeniero senior para trabajar el proyecto con cualquier LLM.

---

## Mapa visual del flujo de la información

```
                          CAMALEON OS
                              |
        +---------------------+---------------------+
        |                                          |
   PROBLEMA                                  SOLUCIÓN
        |                                          |
   - PTAP 2011 sin medición                  - 6 sensores IoT
   - 1,587 L/día perdidos                    - 5 agentes IA
   - 4 químicos fuera de norma               - 5 fenómenos
   - 2 PTAR sobrecargados 2.06×              - Validación cruzada
   - $16,900M exposición legal               - $1.43M inversión
        |                                          |
   Documentado en:                          Implementado en:
   - PROBLEMAS-PTAP-PTAR.md                  - 31 docs en docs/es/
   - 6 tesis UNIAJC integradas               - Repo público MIT
        |                                          |
        +---------------------+---------------------+
                              |
                       VALIDACIÓN
                              |
        - 16/16 retos mínimos cumplidos (RETO PDF)
        - 42-44/44 rúbrica oficial (Sobresaliente)
        - 6 tesis previas validadas
        - Método tradicional UNIAJC respetado y amplificado
                              |
                          PITCH 5 MIN
                              |
        - Apertura: "9 litros perdidos mientras hablo"
        - Cierre: "4 tesis · 4 diagnósticos · 0 soluciones · Camaleón las pone en operación · hoy"
```

---

## Si solo tenés 30 segundos para entender

> *"UNIAJC tiene una planta de agua del 2011 sin medición. Pierde 1,587 litros por día sin saberlo y tiene 4 químicos fuera de norma legal. Cuatro tesis lo diagnosticaron pero ninguna pasó a operación. Camaleón OS es el primer sistema multi-agente de IA aplicado a gestión hídrica universitaria en Colombia: 6 sensores IoT + 5 agentes que deliberan + dashboard + bot Telegram. $1.43 millones de inversión, ahorra $20.5 millones al año, recuperación en 25 días, y protege a la universidad de $16,900 millones de exposición legal. Open source. Replicable a 50 universidades del Valle."*

---

*Resumen v1.0 · 8 de mayo de 2026 · UNIAJC Hackathon*
*Repositorio: github.com/JFrangel/Camaleón-OS*
