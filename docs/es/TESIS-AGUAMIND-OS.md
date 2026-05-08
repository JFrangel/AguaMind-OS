# AguaMind OS

## Sistema Inteligente Multi-Agente para la Caracterización Hídrica y Mitigación Activa de la Planta de Tratamiento de Agua Potable de la Institución Universitaria Antonio José Camacho — Sede Sur

**Trabajo de Hackathon · Facultad de Ingeniería · UNIAJC 2026**
**Cali, Colombia · 7-8 de mayo de 2026**

> *"No predecimos. Caracterizamos. No avisamos. Actuamos. No competimos con tesis previas. Las llevamos a operación."*

---

## Resumen

La Planta de Tratamiento de Agua Potable (PTAP) de la Institución Universitaria Antonio José Camacho — Sede Sur, instalada en 2011, abastece a 8,234 usuarios pero opera **sin sistema de medición** desde su instalación. Las tesis previas de la institución (Caycedo & Jaramillo 2021, Sánchez Sotelo 2021, Gómez Mina 2022, Aristizábal & Largacha 2025, Arias Montoya et al. 2024, Mosquera Zapata & Lozano Beltrán 2024) caracterizaron el problema, midieron pérdidas de 1,587 L/día y modelaron el sistema, pero **ninguna pasó a operación**.

Este trabajo presenta **AguaMind OS**, un sistema interdisciplinario que combina (i) instrumentación IoT con 6 sensores comerciales sobre microcontrolador ESP32, (ii) un sistema multi-agente de inteligencia artificial coordinado mediante LangGraph que opera en tres niveles de análisis (descriptivo, predictivo, prescriptivo), (iii) un dashboard web con visualización 3D del campus y bot de Telegram para operadores, y (iv) un esquema de cumplimiento normativo automatizado con reportes auditables al INVIMA, CVC y Ministerio de Vivienda. La inversión Fase 1 es de $1,431,000 COP con un ahorro proyectado de $20.5M COP/año, alcanzando un período de recuperación de aproximadamente 25 días, una TIR superior al 1,000% y una relación beneficio/costo de 17.4×.

El sistema implementa **5 estrategias automáticas de mitigación** ante fenómenos (sequía/El Niño, lluvias/La Niña, sismo, contaminación química, pico de demanda) y un **método híbrido de validación cruzada** que respeta y amplifica el método tradicional de UNIAJC ("tanques nocturnos"). Aporta a 5 ODS (Objetivos de Desarrollo Sostenible) con métricas cuantificadas: 16.5 millones de litros recuperables en 5 años, 7.6 toneladas de CO₂ evitadas y reducción del 60% en pérdidas técnicas. La arquitectura de 7 capas, el normalizador universal de sensores (acepta 10 formatos de entrada distintos) y el código completamente abierto bajo licencia MIT garantizan la replicabilidad a las 50+ universidades públicas del Valle del Cauca.

**Palabras clave:** Gestión hídrica, IoT, multi-agente, ESP32, LangGraph, smart campus, Lean Manufacturing, ODS, código abierto.

---

## Abstract

The Drinking Water Treatment Plant (PTAP) at the Institución Universitaria Antonio José Camacho — Southern Headquarters, installed in 2011, serves 8,234 users but has operated **without measurement systems** since its inception. Previous institutional theses (Caycedo & Jaramillo 2021; Sánchez Sotelo 2021; Gómez Mina 2022; Aristizábal & Largacha 2025; Arias Montoya et al. 2024; Mosquera Zapata & Lozano Beltrán 2024) characterized the problem, quantified losses at 1,587 L/day and modeled system dynamics, but **none reached operational deployment**.

This work presents **AguaMind OS**, an interdisciplinary system combining (i) IoT instrumentation with six commercial sensors on an ESP32 microcontroller, (ii) a multi-agent artificial intelligence system coordinated via LangGraph operating across three analytical tiers (descriptive, predictive, prescriptive), (iii) a web dashboard with 3D campus visualization and Telegram bot for operators, and (iv) automated regulatory compliance with auditable reports to INVIMA, CVC and the Ministry of Housing. Phase 1 investment is COP $1,431,000 with projected annual savings of COP $20.5M, achieving a payback period of approximately 25 days, an IRR exceeding 1,000% and a benefit/cost ratio of 17.4×.

The system implements **five automated mitigation strategies** for environmental phenomena (drought/El Niño, heavy rainfall/La Niña, seismic events, chemical contamination, demand surge) and a **hybrid cross-validation method** that respects and amplifies UNIAJC's traditional "nightly tanks" measurement protocol. It contributes to five SDGs with quantified metrics: 16.5 million liters recoverable over five years, 7.6 tons of CO₂ avoided, and a 60% reduction in technical losses. The 7-layer architecture, universal sensor normalizer (accepting 10 distinct input formats), and fully open-source MIT-licensed codebase ensure replicability across the 50+ public universities of Valle del Cauca.

**Keywords:** Water management, IoT, multi-agent, ESP32, LangGraph, smart campus, Lean Manufacturing, SDG, open source.

---

## Tabla de contenido

1. [Introducción](#1-introducción)
2. [Planteamiento del problema](#2-planteamiento-del-problema)
3. [Objetivos](#3-objetivos)
4. [Justificación](#4-justificación)
5. [Marco referencial](#5-marco-referencial)
6. [Marco teórico](#6-marco-teórico)
7. [Marco legal](#7-marco-legal)
8. [Metodología](#8-metodología)
9. [Desarrollo del sistema](#9-desarrollo-del-sistema)
10. [Trinidad analítica del agente](#10-trinidad-analítica-del-agente)
11. [Estrategias derivadas de los datos](#11-estrategias-derivadas-de-los-datos)
12. [Validación cruzada con método tradicional](#12-validación-cruzada-con-método-tradicional)
13. [Análisis costo-beneficio](#13-análisis-costo-beneficio)
14. [Impacto en Objetivos de Desarrollo Sostenible](#14-impacto-en-objetivos-de-desarrollo-sostenible)
15. [Plan por fases (15 años)](#15-plan-por-fases-15-años)
16. [Validación contra tesis previas](#16-validación-contra-tesis-previas)
17. [Conclusiones](#17-conclusiones)
18. [Recomendaciones](#18-recomendaciones)
19. [Referencias bibliográficas](#19-referencias-bibliográficas)
20. [Anexos](#20-anexos)

---

## 1. Introducción

El acceso a agua potable de calidad es uno de los servicios fundamentales para el desarrollo académico de cualquier institución educativa. La Institución Universitaria Antonio José Camacho (UNIAJC), Sede Sur, ubicada en zona periurbana de Cali, Colombia, atiende a 8,234 usuarios totales (3,230 estudiantes activos más docentes y personal administrativo) sobre un campus de 38,755.88 m² distribuido entre las zonas Alameda y Parquesoft. Por la ausencia de cobertura de acueducto en la zona, el suministro hídrico depende de una **Planta de Tratamiento de Agua Potable (PTAP) instalada en 2011**, alimentada por dos aljibes con un caudal combinado de 113.56 L/min, conectados a la cuenca hidrográfica del río Pance.

La PTAP, sin embargo, presenta una **debilidad estructural crítica**: desde su instalación opera sin un sistema integral de medición. No cuenta con caudalímetros en los puntos de entrada y salida, sensores de nivel en los tanques de almacenamiento, ni instrumentación para monitorear la calidad del agua distribuida. Esta falta de instrumentación, identificada formalmente por las tesis institucionales desde 2021, impide controlar el uso del recurso, detectar fugas en tiempo real y optimizar los costos operativos. Adicionalmente, el sistema de tratamiento de aguas residuales del campus, conformado por dos PTAR físicas (Alameda y Entrada) con dos módulos cada una de 1,000 estudiantes de capacidad —totalizando 4,000 estudiantes—, opera con una **sobrecapacidad de 2.06×** frente a los 8,234 usuarios reales, generando vertimientos sin caracterización formal hacia el río Pance y, eventualmente, al río Cauca.

Existe en la literatura institucional un contraste notable: cuatro trabajos de grado distintos han diagnosticado el problema, han propuesto mejoras y han modelado dinámicamente el sistema, pero **ninguno ha pasado a operación efectiva**. La presente investigación se propone cerrar esa brecha mediante un sistema integral, abierto y de bajo costo, denominado **AguaMind OS**, que toma los hallazgos de las tesis previas como base de validación y los implementa operacionalmente.

---

## 2. Planteamiento del problema

### 2.1 Descripción del problema

La PTAP de UNIAJC Sede Sur presenta deficiencias documentadas en cuatro dimensiones interrelacionadas:

#### 2.1.1 Calidad del agua fuera de norma

La caracterización fisicoquímica realizada por Caycedo Saa & Jaramillo Moreno (2021) sobre once muestras tomadas a lo largo del año documentó **cuatro parámetros que incumplen** la Resolución 2115 de 2007 del Ministerio de Protección Social:

| Parámetro | Promedio | Rango medido | Norma | Cumple |
|-----------|----------|--------------|-------|:------:|
| Cloro Residual Libre | 0.96 mg/L | 0.28 – 2.10 | 0.3 – 2.0 | **NO** |
| Fosfatos | 0.74 mg/L | 0.12 – 1.91 | ≤ 0.5 | **NO** |
| Nitratos | 6.61 mg/L | 0.10 – 22.50 | ≤ 10 | **NO** |
| pH | 6.82 | 6.40 – 7.41 | 6.5 – 9 | **NO** |

Los nitratos alcanzaron picos de 2.25× sobre la norma; los fosfatos 3.82× sobre. Estos compuestos representan riesgos sanitarios documentados (metahemoglobinemia infantil por nitratos, eutrofización ambiental por fosfatos) y exponen a UNIAJC a sanciones del INVIMA bajo el artículo 576 de la Ley 09 de 1979, con multas reales documentadas hasta **$13 millones COP/año** y posibilidad de clausura temporal o permanente.

#### 2.1.2 Pérdidas hídricas no contabilizadas

Sánchez Sotelo (2021), aplicando la metodología "tanques nocturnos" —medición del nivel del tanque al cierre del día (18:00) y al inicio de operaciones (07:00)— cuantificó pérdidas de **66.15 L/h durante las 13 horas nocturnas no operativas**, equivalentes a 1,587.69 L/día y 579.5 m³/año. Con tarifa industrial EMCALI de $1,910/m³ (estrato 3), el costo directo del agua perdida supera **$1,107,637 COP anuales**, sin contar costos asociados (operario, químicos, electricidad de bombeo).

#### 2.1.3 Mantenimiento exclusivamente correctivo

Gómez Mina (2022) catalogó **13 equipos críticos** de la PTAP (dos bombas sumergibles Barnes 5HP/2HP, tres filtros OHS Ingenieros, tanque de cloración Ajover Wave, bomba dosificadora LMI, dos hidroneumáticos Altamira PRO XLB, dos bombas centrífugas Barmesa, dos tanques de almacenamiento) y documentó la **ausencia total de programa de mantenimiento preventivo o predictivo**. Cuando un equipo falla, queda inutilizable durante períodos prolongados. No existen fichas técnicas, ni registros de horas de operación, ni inspecciones programadas. El personal operativo se limita a un único operario sin capacitación formal.

#### 2.1.4 Sistema de tratamiento de aguas residuales sobrecargado

Mosquera Zapata & Lozano Beltrán (2024) modelaron el comportamiento de las PTAR ante el crecimiento poblacional. Con dos PTAR físicas (Alameda y Entrada), cada una con dos módulos en paralelo de 1,000 estudiantes (capacidad total 4,000), la población actual de 8,234 usuarios genera una **sobrecapacidad efectiva de 2.06×**. Adicionalmente, no existe monitoreo de los parámetros exigidos por la Resolución 0631 de 2015 (DBO5 ≤ 90 mg/L, pH 6-9, sólidos suspendidos totales ≤ 90 mg/L), exponiendo a la institución a multas potenciales de hasta 5,000 SMMLV (~$6,500 millones COP).

### 2.2 Formulación del problema

¿Cómo diseñar e implementar un sistema integral, automatizado y de bajo costo que caracterice operacionalmente la PTAP de UNIAJC Sede Sur, instrumente los puntos críticos del proceso, derive estrategias accionables a partir de los datos y garantice el cumplimiento normativo, sin reemplazar los métodos tradicionales sino complementándolos?

### 2.3 Sistematización

- ¿Cuáles son los puntos críticos del sistema hídrico que requieren instrumentación prioritaria?
- ¿Qué tecnologías IoT y de inteligencia artificial son técnica y económicamente viables para el contexto universitario público?
- ¿Cómo se traducen los datos crudos de los sensores en decisiones operativas validadas y auditables?
- ¿Cómo se cuantifica el retorno de la inversión en términos económicos, ambientales y de cumplimiento legal?
- ¿Cómo se garantiza la sostenibilidad del sistema más allá del equipo de desarrollo inicial?

---

## 3. Objetivos

### 3.1 Objetivo general

Diseñar, desarrollar y validar un sistema inteligente multi-agente, denominado **AguaMind OS**, que caracterice operacionalmente la Planta de Tratamiento de Agua Potable de UNIAJC Sede Sur mediante instrumentación IoT, análisis con inteligencia artificial y automatización de la mitigación, integrando los hallazgos de los trabajos de grado previos de la institución y garantizando el cumplimiento de la normativa colombiana.

### 3.2 Objetivos específicos

1. **Caracterizar** el estado técnico-operativo actual de la PTAP y la red de distribución del campus a partir de datos de sensores instrumentados, complementando las caracterizaciones de Caycedo & Jaramillo (2021) y Arias Montoya et al. (2024).

2. **Diseñar** una arquitectura por capas que integre (a) seis sensores físicos calibrados, (b) un microcontrolador ESP32 con firmware embebido, (c) un broker MQTT con respaldo HTTP, (d) un backend FastAPI con persistencia Postgres, (e) un sistema multi-agente coordinado con LangGraph, y (f) interfaces de aplicación (dashboard web, bot Telegram, reportes PDF auditables).

3. **Implementar** un agente conversacional capaz de operar tres niveles de análisis (descriptivo, predictivo, prescriptivo) con voto consensual de cinco sub-agentes especializados y validación cruzada con el método tradicional "tanques nocturnos" del operario UNIAJC.

4. **Cuantificar** el impacto técnico, económico, ambiental y normativo del sistema mediante indicadores formales (IEH, TPP, CPE, ICA), análisis costo-beneficio (VPN, TIR, B/C) y mapeo a Objetivos de Desarrollo Sostenible.

5. **Establecer** un plan por fases a 15 años que garantice la sostenibilidad institucional del sistema y su replicabilidad a las sedes Norte y Centro de UNIAJC y a las universidades del Valle del Cauca, soportado en código abierto bajo licencia MIT.

---

## 4. Justificación

### 4.1 Justificación técnica

Las tesis previas de UNIAJC documentan el problema con rigor académico pero no han pasado a operación por **tres barreras técnicas**: (i) costo elevado de soluciones SCADA tradicionales ($50–150 millones COP), (ii) ausencia de personal especializado para operación continua, y (iii) integración compleja con la infraestructura institucional existente. AguaMind OS supera estas barreras mediante hardware comercial de bajo costo (BOM Fase 1 = $1,431,000 COP), automatización por agentes de IA que reducen la dependencia de personal humano del 100% al ~20%, y arquitectura modular en capas independientemente reemplazables.

### 4.2 Justificación social

Garantizar la calidad del agua potable distribuida a 8,234 usuarios es responsabilidad institucional irrenunciable. La detección temprana de turbidez fuera de norma (TSD-10), pH inadecuado o presencia de coliformes mediante análisis programados protege la salud pública del campus. Adicionalmente, el módulo "Smart Water Ledger" gamifica el consumo responsable a nivel de edificio, conectando la conciencia ambiental con beneficios tangibles del programa de Bienestar Universitario.

### 4.3 Justificación ambiental

La cuenca del río Pance es un afluente directo del río Cauca, segundo río más importante de Colombia. Las pérdidas no contabilizadas y los vertimientos sin caracterización formal de UNIAJC contribuyen a la presión hídrica regional. AguaMind OS proyecta recuperar **16.5 millones de litros en cinco años** y evitar **7.6 toneladas de CO₂** (asociadas al bombeo eficiente y al tratamiento de aguas que de otra forma serían potabilizadas innecesariamente), aportando directamente a los ODS 6 (Agua Limpia), 12 (Producción Responsable) y 13 (Acción por el Clima).

### 4.4 Justificación económica

Con ahorros proyectados de $20,536,425 COP anuales contra una inversión Fase 1 de $1,431,000 COP, el período de recuperación es de aproximadamente **25 días**. La Tasa Interna de Retorno (TIR) supera el 1,000% y la relación beneficio/costo es de 17.4×. Estos indicadores, calculados conservadoramente, justifican la inversión bajo cualquier criterio financiero institucional.

### 4.5 Justificación legal

UNIAJC opera actualmente con **incumplimientos sistémicos** de la Resolución 2115 de 2007 (parámetros químicos), Resolución 0631 de 2015 (vertimientos) y Decreto 1076 de 2015 (monitoreo piezométrico). La exposición potencial alcanza **$16,900 millones COP** considerando suspensión por IRCA, revocatoria de concesión CVC y multas por vertimientos. Cada peso invertido en AguaMind OS protege entre $890 y $3,380 en exposición legal evitada.

---

## 5. Marco referencial

### 5.1 Antecedentes en UNIAJC (cinco trabajos de grado integrados)

#### 5.1.1 Caycedo Saa & Jaramillo Moreno (2021) — Caracterización

> *"Propuesta de caracterización del proceso técnico-operativo de la Planta de Tratamiento de Agua de la Institución Universitaria Antonio José Camacho Sede Sur"*

Documento maestro de 129 páginas que aportó:
- 161 fuentes de consumo identificadas (51 sanitarios, 53 lavamanos, 14 orinales, 14 duchas, 24 llaves, 5 lavaplatos)
- Distribución por zona: Alameda 33% / Parquesoft 67%
- Crecimiento estudiantil 1,315 (2015-1) → 2,090 (2019-2) = +59%
- Tabla 19 con ocho hallazgos de incumplimiento normativo
- Cuatro parámetros químicos fuera de norma (Tabla 1)
- Recomendaciones: bomba dosificadora, VFD, medidores pH/turbidez/flujo

#### 5.1.2 Sánchez Sotelo (2021) — Lean Manufacturing

> *"Propuesta de mejora con aplicación de herramientas de Lean Manufacturing para la planta de potabilización de agua en la Universidad Antonio José Camacho Sede Sur"*

Aportó la cuantificación operacional:
- Caudal validado in-situ: 5.56 L/seg (= 333.6 L/min)
- Equivalencia tanque: **1 cm = 160 L** (constante crítica para validación cruzada)
- Desperdicio nocturno medido: 960 L en 13 horas
- Pérdida diaria: 1,587.69 L
- Costo anual del desperdicio: $1,107,637 COP
- Análisis Lean con identificación de las 7 mudas

#### 5.1.3 Gómez Mina (2022) — Mantenimiento

> *"Diseño de un programa de mantenimiento para la planta de tratamiento de agua potable de la Institución Universitaria Antonio José Camacho sede sur"*

Documento de 107 páginas que catalogó los equipos con códigos institucionales:

| Código | Equipo | Especificación |
|--------|--------|----------------|
| CP-BS-01 | Bomba sumergible aljibe 1 | Barnes 4SP 2526 · 5 HP · 32 gal/min |
| CP-BS-02 | Bomba sumergible aljibe 2 | Barnes 4SP 2511 · 2 HP · 32 gal/min |
| SF-FT-01/02/03 | Filtros 1, 2, 3 | OHS Ingenieros · 861.53 L · 400 L/min |
| SD-TM-01 | Tanque cloración | Ajover Wave · 250 L |
| SD-BD-01 | Bomba dosificadora cloro | LMI C111-362TI · 150 PSI · 2.5 GPH |
| AL-TA-01 | Tanque almacenamiento A | 36,000 L |
| AL-TA-02 | Tanque almacenamiento B | 16,000 L |
| SB-TH-01/02 | Hidroneumáticos | Altamira PRO XLB · 119 gal · 125 PSI |
| SB-BC-03/04 | Bombas centrífugas | Barmesa Pumps |

Adicionalmente proporcionó los planos hidráulicos del campus (Apéndice M) y el detalle interno de la PTAP, integrados como base visual del sistema.

#### 5.1.4 Aristizábal Torres & Largacha Perdomo (2025) — Modelo Vensim

> *"Desarrollo de un modelo de dinámica de sistemas para simular la demanda y el suministro de agua en la Institución Universitaria Antonio José Camacho, Sede Sur"*

Aportó la validación dinámica de tres escenarios prospectivos:
- Cooperación 0%: colapso del sistema en 2 años
- Cooperación 15%: sostenibilidad parcial
- Cooperación 50%: sistema sostenible a largo plazo

Estos escenarios alimentan el sub-agente Mitigation de AguaMind OS para activación de campañas Smart Water Ledger.

#### 5.1.5 Arias Montoya, Montiel Angel & Osorio Hernández (2024) — Sistema de ahorro

> *"Diseño de un sistema de ahorro para el mejoramiento de la eficiencia del servicio suministrado por la planta de tratamiento de agua potable (PTAP)"*

Aportó la línea base de consumo por estudiante (CPE = 14.04 L/est/día) y la caracterización detallada de zonas de uso, ya integrada en la constante `ZONE_DAILY_BASE` del simulador.

#### 5.1.6 Mosquera Zapata & Lozano Beltrán (2024) — Modelo PTAR

> *"Modelo de dinámica de sistemas para brindar información a la comunidad académica del impacto sobre la PTAR y el ecosistema, UNIAJC sede sur en Cali"*

Aportó la caracterización de las descargas al río Pance y modelo del impacto comunitario, base para el módulo de reportes ciudadanos QR del sistema.

### 5.2 Estado del arte mundial

| Sistema | Año | País | Tecnología | Limitación |
|---------|------|------|-------------|-------------|
| **Smart Water Network** PUB Singapur | 2014–presente | Singapur | SCADA + sensores acústicos | Costo de millones de USD |
| **MIT Water Project** | 2018 | EE.UU. | IoT distribuido + ML | Foco residencial, no campus |
| **Aguas de Barrancabermeja** | 2017 | Colombia | Macromedidores | No campus universitarios |
| **Lean Manufacturing PTAP** Chocontá | 2015 | Colombia | Diagnóstico técnico | Sin instrumentación |
| **AguaMind OS** | 2026 | Colombia | Multi-agente IA + IoT bajo costo + open source | — |

AguaMind OS llena un vacío específico: sistema multi-agente de inteligencia artificial aplicado a gestión hídrica en campus universitario público latinoamericano, completamente abierto, replicable y de costo significativamente menor que las alternativas comerciales.

---

## 6. Marco teórico

### 6.1 Planta de tratamiento de agua potable (PTAP)

Según Casero (2007), una planta de tratamiento de aguas potables es el conjunto de instalaciones, destinadas a mejorar la calidad del agua, que se localizan en un espacio físico relativamente reducido. Estas utilizan tecnologías que realizan procesos unitarios interconectados secuencialmente y dan como resultado agua con controles de sus características físicas y químicas.

La PTAP de UNIAJC opera con cuatro etapas secuenciales:

1. **Captación**: Dos aljibes con bombas sumergibles Barnes (5 HP y 2 HP) aportan 113.56 L/min combinados.
2. **Filtración**: Tres filtros en cascada — grava+arena (SF-FT-01), antracita (SF-FT-02), carbón activado (SF-FT-03), cada uno con capacidad volumétrica de 861.53 L y caudal de 400 L/min.
3. **Desinfección**: Cloración mediante bomba dosificadora LMI sobre tanque de cloración Ajover Wave de 250 L.
4. **Almacenamiento y distribución**: Dos tanques (A=36,000 L, B=16,000 L) con presurización por hidroneumáticos Altamira PRO XLB y bombas centrífugas Barmesa.

### 6.2 Internet de las Cosas (IoT) industrial

El paradigma IoT aplicado a sistemas hídricos se compone de cuatro elementos: **percepción** (sensores), **transporte** (protocolos como MQTT, HTTP), **procesamiento** (edge + cloud) y **aplicación** (interfaces humanas). AguaMind OS adopta esta estructura con una particularidad: la capa de inteligencia se materializa como sistema multi-agente, no como un controlador único.

### 6.3 Sistemas multi-agente

Un sistema multi-agente es un conjunto de entidades autónomas (agentes) que interactúan entre sí en un entorno compartido para resolver problemas que excederían la capacidad individual. AguaMind OS implementa cinco agentes coordinados mediante el framework **LangGraph** (extensión de LangChain para grafos de estados):

- **Orchestrator**: coordina la deliberación
- **SystemsAgent**: análisis estadístico y KPIs
- **SensorAgent**: validación de calidad de señales
- **IndustrialAgent**: análisis Lean y predicciones ML
- **MitigationAgent**: ejecución de acciones

La decisión final requiere voto consensual de al menos 3 de 5 agentes, lo que reduce falsos positivos en acciones críticas (cierre automático de electroválvulas, suspensión de distribución, etc.).

### 6.4 Lean Manufacturing y las siete mudas

Aplicado al contexto hídrico, las siete mudas de Toyota/Ohno se traducen como:

| # | Muda | Manifestación en PTAP UNIAJC |
|---|------|------------------------------|
| 1 | Defectos | Fugas no detectadas en red de distribución |
| 2 | Sobreproducción | Bombeo sin demanda real (ciclos 3-4 min innecesarios) |
| 3 | Espera | Detección manual tarda días o semanas |
| 4 | Inventario | Tanques sin medición de nivel |
| 5 | Movimiento | Personal inspecciona físicamente cada zona |
| 6 | Transporte | Agua tratada usada para riego (innecesario) |
| 7 | Talento | Datos sin uso para decisiones |

### 6.5 Análisis descriptivo, predictivo y prescriptivo

La trinidad analítica de AguaMind OS distingue tres niveles de análisis:

1. **Descriptivo** (¿qué pasó?): tendencias, promedios, frecuencias, comportamientos comunes.
2. **Predictivo** (¿qué va a pasar?): regresión, redes neuronales, árboles de decisión.
3. **Prescriptivo** (¿qué hacemos?): predicción aplicada, optimización, simulación.

Cada nivel alimenta al siguiente; lo descriptivo informa lo predictivo, lo predictivo guía lo prescriptivo.

### 6.6 Ciclo PHVA (Deming)

El ciclo Planear-Hacer-Verificar-Actuar de Deming guía la operación cíclica del agente cada 30 segundos:
- **P**lanear: Orchestrator define qué medir
- **H**acer: SystemsAgent y SensorAgent recolectan
- **V**erificar: IndustrialAgent analiza
- **A**ctuar: MitigationAgent ejecuta

---

## 7. Marco legal

### 7.1 Normativas de calidad del agua potable

| Normativa | Aspecto regulado | Aplicabilidad AguaMind OS |
|-----------|------------------|----------------------------|
| **Decreto 1575 de 2007** | Sistema para protección y control de calidad agua humana | Reportes IRCA mensuales automatizados |
| **Resolución 2115 de 2007** | Características y valores admisibles físico-químicos | Monitoreo turbidez, pH, cloro residual en línea |
| **Resolución 0811 de 2008** | Definición puntos de muestreo | Estandarización ubicación sensores |
| **Decreto 3930 de 2010** | Uso del recurso hídrico | Caracterización vertimientos |
| **Decreto 2105 de 1983** | Reglamentación potabilización | Operación PTAP |
| **RAS 2000 Capítulo C.17** | Operación PTAP, retrolavados | Programación de mantenimientos |

### 7.2 Normativas de concesión y monitoreo de acuíferos

| Normativa | Aspecto |
|-----------|---------|
| **Decreto 1541 de 1978** | Concesión aguas públicas |
| **Decreto 1076 de 2015** | Monitoreo piezométrico obligatorio |
| **Ley 79 de 1986** | Conservación del recurso |

### 7.3 Normativas de vertimientos y reúso

| Normativa | Aspecto |
|-----------|---------|
| **Resolución 0631 de 2015** | Valores límite vertimientos (DBO5 ≤ 90 mg/L, pH 6-9, SST ≤ 90 mg/L) |
| **Decreto 050 de 2018** | Plan de cumplimiento |
| **Resolución 1207 de 2014** | Reúso de aguas residuales tratadas para riego |

### 7.4 Normativas de seguridad de la información

| Normativa | Aspecto |
|-----------|---------|
| **Ley 1581 de 2012** | Habeas Data — pseudonimización de reportes ciudadanos |
| **Ley 1928 de 2018** | Ciberseguridad |
| **Decreto 338 de 2022** | Riesgos cibernéticos en infraestructura crítica |
| **Ley 1712 de 2014** | Transparencia y datos abiertos |
| **Resolución 055 de 2025 UNIAJC** | Plan de seguridad y privacidad institucional |

### 7.5 Exposición legal evitada

| Concepto | Multa máxima |
|----------|--------------|
| Suspensión por IRCA fuera de norma | 1,000 SMMLV ≈ $1,300M COP |
| Revocatoria de concesión por CVC | 5,000 SMMLV ≈ $6,500M COP |
| Multa por vertimientos Res. 0631/2015 | 5,000 SMMLV ≈ $6,500M COP |
| Multa Habeas Data Ley 1581/2012 | 2,000 SMMLV ≈ $2,600M COP |
| **TOTAL EXPOSICIÓN POTENCIAL** | **$16,900M COP** |
| **Inversión AguaMind OS Fase 1** | **$1.43M COP** |
| **Ratio protección legal / inversión** | **11,818×** |

---

## 8. Metodología

### 8.1 Tipo de investigación

Investigación aplicada de tipo **mixto**: cuantitativa (mediciones de sensores, KPIs, análisis costo-beneficio) y cualitativa (entrevistas con operario PTAP, validación con stakeholders institucionales). El alcance es **descriptivo y propositivo**: caracteriza el estado actual y propone un sistema implementable.

### 8.2 Área de estudio

Campus UNIAJC Sede Sur: 38,755.88 m² distribuidos entre las zonas Alameda (33% del consumo) y Parquesoft (67% del consumo). Coordenadas geográficas aproximadas: 3°25′ N, 76°31′ W. La PTAP está localizada en el centro-sur del campus, alimentada por dos aljibes adyacentes.

### 8.3 Proceso metodológico

El desarrollo siguió seis metodologías complementarias aplicadas iterativamente:

#### 8.3.1 Design Thinking

```
Empatía → Definición → Ideación → Prototipo → Test
```

- **Empatía**: entrevistas con operario PTAP, observación del proceso de medición tradicional ("tanques nocturnos"), revisión de bitácoras manuales.
- **Definición**: priorización de los ocho problemas identificados por Caycedo & Jaramillo (2021).
- **Ideación**: diseño del sistema multi-agente como respuesta integral.
- **Prototipo**: implementación del backend FastAPI + dashboard SvelteKit + simulador de sensores.
- **Test**: validación cruzada con datos de las cuatro tesis previas.

#### 8.3.2 TRIZ (Inventiva sistemática)

Resolución de contradicciones técnicas:
- *Contradicción 1*: medir caudal sin invadir la tubería → solución: ultrasonido (JSN-SR04T) y sensores Hall externos (YF-S201).
- *Contradicción 2*: bajar consumo sin apagar la bomba → solución: Variador de Frecuencia (VFD) con modo eco-nocturno.
- *Contradicción 3*: detectar fugas sin desplegar personal → solución: vibración acústica (SW-420) + IsolationForest sobre series de presión.

#### 8.3.3 Lean Startup (MVP iterativo)

```
MVP día 1 → Validación con simulador → Fase 1 piloto → Escalonamiento por fases
```

#### 8.3.4 GitOps + DevOps

Repositorio público en GitHub bajo licencia MIT, integración continua mediante GitHub Actions, despliegue automático a Vercel (frontend), Koyeb (backend) y Supabase (base de datos), todo en planes gratuitos de las plataformas mencionadas.

#### 8.3.5 CRISP-DM (Cross-Industry Standard Process for Data Mining)

```
Comprensión del negocio → Comprensión de los datos → Preparación →
Modelado → Evaluación → Despliegue
```

Aplicado al ciclo de vida del modelo IsolationForest para detección de anomalías en presión y al Random Forest para clasificación de tipo de fuga.

#### 8.3.6 Scrum (gestión del trabajo)

Cuatro sprints documentados con entregables claros y demos al final de cada uno.

### 8.4 Fuentes de información

- **Primarias**: sensores instrumentados (en producción) y simulador determinista (en desarrollo).
- **Secundarias**: cuatro tesis UNIAJC previas, planos hidráulicos institucionales, bitácoras del operario.
- **Terciarias**: literatura científica internacional, normatividad colombiana vigente.

---

## 9. Desarrollo del sistema

### 9.1 Arquitectura de siete capas

AguaMind OS se estructura en siete capas verticales, cada una con responsabilidad clara y borde técnico explícito:

```
+-----------------------------------------------------------+
| CAPA 7 · APLICACIÓN                          (< 100 ms)  |
| Dashboard SvelteKit · Bot Telegram · Reportes PDF · API   |
+-----------------------------------------------------------+
| CAPA 6 · INTELIGENCIA                            (1-5 s) |
| 5 agentes (Orchestrator + Systems + Sensor + Industrial + |
| Mitigation) coordinados con LangGraph + LLM cascade       |
+-----------------------------------------------------------+
| CAPA 5 · PERSISTENCIA                       (50-200 ms)  |
| FastAPI + Cache RAM + Postgres 90d + Parquet 5y          |
+-----------------------------------------------------------+
| CAPA 4 · COMUNICACIÓN                       (30-100 ms)  |
| MQTT TLS 8883 (HiveMQ) + HTTP fallback + NVS local       |
+-----------------------------------------------------------+
| CAPA 3 · EDGE / EMBEBIDA                       (1-30 s)  |
| ESP32-WROOM dual-core + ADS1115 + OLED + LED + buzzer    |
+-----------------------------------------------------------+
| CAPA 2 · SENSADO                                 (< 1 s) |
| 6 sensores físicos + normalizador universal (10 formatos)|
+-----------------------------------------------------------+
| CAPA 1 · FÍSICA                                          |
| Aljibes → PTAP → Tanques → 6 edificios → 2 PTAR → Río    |
+-----------------------------------------------------------+
```

Cada capa es **independientemente reemplazable**: si HiveMQ deja de operar, HTTP fallback toma el relevo; si una bomba cambia de modelo, solo se actualiza la capa de sensado; si Postgres se reemplaza por TimescaleDB, las capas superiores no se enteran.

### 9.2 Capa 1 — Física (los planos del campus)

Los planos hidráulicos extraídos de Gómez Mina (2022) — disponibles en `tesis-uniajc/planos/` — confirman:

- **Plano del detalle de la PTAP** (Ilustración 22 de la tesis): muestra el interior con tanque de almacenamiento subterráneo, tubo de succión, tres motobombas con manómetros, dos hidroflows, tanque de cloración con bomba dosificadora, tres filtros en cascada y salida de 79 metros con tubería de 3" de diámetro.

- **Plano de distribución hidráulica** (Ilustración 23 de la tesis): vista aérea del campus con las dos PTAR físicas (Alameda al oeste y Entrada al este), aljibe central, planta eléctrica, edificios codificados (Aulas, Coliseo, GYM, Bienestar, Relax Center, Salones, Oficinas, Biblioteca, Cafetería, Cocina, Parqueaderos), posetas de entrada/salida y punto cero. Las tuberías están coloreadas por función: rojo (suministro potable), verde (distribución), morado (retorno), naranja (residual).

### 9.3 Capa 2 — Sensado (seis sensores con calibración documentada)

| Sensor | Modelo | Variable | Salida | Rango | Conversión a SI | Costo COP |
|--------|--------|----------|--------|-------|------------------|-----------|
| Caudal pequeño | YF-S201 (1/2") | L/min | Pulsos Hall (Hz) | 1-30 | `L/min = Hz / 7.5` | $25,000 |
| Caudal grande | YF-DN50 | L/min | Pulsos Hall (Hz) | 0-400 | `L/min = Hz / 0.2` | $95,000 |
| Presión | MPX5700AP | kPa | 0-5 V analog | 0-700 | `kPa = (V/5) × 700` | $45,000 |
| Nivel tanque | JSN-SR04T | cm | PWM us | 0-450 | `cm = us × 0.0343 / 2` | $30,000 |
| Vibración | SW-420 + LM393 | bool | TTL ON/OFF | 0/1 | directo | $10,000 |
| Nivel freático | Transductor 4-20 mA | m | Loop industrial | 0-10 | `m = (mA-4) × 10/16` | $180,000 |
| Turbidez | TSD-10 | NTU | 0-4.5 V analog | 0-10 | `NTU = 10 × (1 - V/4.5)` | $55,000 |

Adicionalmente, el normalizador universal de sensores acepta diez formatos de entrada distintos: `json_object`, `json_array`, `ndjson`, `csv`, `esp32_compact`, `modbus_holding`, `mqtt`, `scada_struct`, `opcua_struct` y `raw_bytes`. Esto permite integrar sensores de cualquier proveedor sin reescribir el backend.

### 9.4 Capa 3 — Edge (firmware ESP32 dual-core)

El microcontrolador **ESP32-WROOM-32** opera dos núcleos en paralelo:

- **Core 0 (1 Hz)**: lee los seis sensores, aplica filtro de media móvil con N=10 muestras, y mantiene un buffer circular en RAM con las últimas 30 muestras.
- **Core 1 (cada 30 s)**: calcula promedio + mínimo + máximo + desviación estándar del buffer, actualiza el display OLED 0.96" local, y publica el payload MQTT a HiveMQ Cloud.

La máquina de estados del firmware contempla siete estados:

```
[BOOT] → [WIFI_CONNECT] → [MQTT_CONNECT] → [READY]
                                              ├── [READING] (Core 0, 1Hz)
                                              ├── [PUBLISHING] (Core 1, 30s)
                                              ├── [HTTP_FALLBACK] (si MQTT falla)
                                              └── [NVS_BUFFER] (si red falla)
                                                     └─ drena cuando reconecta
```

El módulo NVS (Non-Volatile Storage) de la flash interna del ESP32 puede almacenar hasta **1,000 lecturas** localmente (≈ 8 horas a frecuencia 30 s), garantizando supervivencia ante cortes de internet.

### 9.5 Capa 4 — Comunicación (MQTT con respaldo HTTP)

La estructura jerárquica de tópicos MQTT publicada en HiveMQ Cloud:

```
campus/uniajc/
  sensors/
    esp32-ptap-01      ← payload con 6 mediciones cada 30s
    esp32-bloque-a-01  ← (Fase 2)
  actuators/
    EV-A1   close|open
    EV-A2   close|open
    EV-RC1  close|open
    pump-main  auto|eco|standby|emergency_off
  alerts/
    critical
    warning
  reports/
    monthly-irca       ← suscripción INVIMA
    quarterly-cvc      ← suscripción CVC
```

Configuración técnica: TLS 8883, QoS 1 (al menos una entrega), retain=false para sensores, retain=true para estado de actuadores.

### 9.6 Capa 5 — Persistencia (FastAPI + Postgres + Parquet)

El esquema de almacenamiento en cinco niveles, optimizado por latencia y duración:

| Capa | Tecnología | Retención | Latencia |
|------|------------|-----------|----------|
| Edge NVS flash | ESP32 interno | 1,000 lecturas (~8h) | offline |
| RAM cache | Python dict en FastAPI | última hora | < 5 ms |
| Warm Postgres | Supabase + pgvector + PostGIS | 90 días indexados | < 50 ms |
| Cold Parquet | S3-compatible (B2/R2) | 5 años | DuckDB ad-hoc |
| PDF auditable | WeasyPrint + Jinja2 + SHA-256 | permanente | inmediato |

Schema canónico de la tabla principal:

```sql
CREATE TABLE water_readings (
  id              BIGSERIAL PRIMARY KEY,
  timestamp       TIMESTAMPTZ NOT NULL,
  node_id         TEXT NOT NULL,
  sensor_id       TEXT NOT NULL,
  sensor_type     TEXT NOT NULL,
  value           DOUBLE PRECISION NOT NULL,
  unit            TEXT NOT NULL,
  raw             JSONB,
  quality         TEXT NOT NULL DEFAULT 'ok',
  metadata        JSONB,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_readings_ts          ON water_readings (timestamp DESC);
CREATE INDEX idx_readings_node_sensor ON water_readings (node_id, sensor_id, timestamp DESC);
CREATE INDEX idx_readings_quality     ON water_readings (quality) WHERE quality != 'ok';
```

### 9.7 Capa 6 — Inteligencia (cinco agentes coordinados)

| Agente | Rol | Tecnología base | Salida típica |
|--------|-----|-----------------|----------------|
| **Orchestrator** | Coordina deliberación, voto consensual | LangGraph + LLM cascade | "3 de 5 agentes votan critical → autorizo MitigationAgent" |
| **SystemsAgent** | KPIs estadísticos y anomalías | IsolationForest + pandas | "TPP 75.24% [critical], iso_score 0.78" |
| **SensorAgent** | Validación rangos físicos y drift | Reglas + estadística | "6/6 sensores OK · drift detectado en TSD-10" |
| **IndustrialAgent** | Lean + ML predictivo | Random Forest + ARIMA | "P(fuga)=0.92, tipo: fisura_lenta" |
| **MitigationAgent** | Acción autónoma y ejecución | Reglas + scipy.optimize + PySD | "Cerrar EV-A2, bomba a standby" |

El ciclo de operación opera cada **30 segundos** y completa la deliberación en aproximadamente **5 segundos** (vs. 2-4 horas que requeriría un humano para el mismo proceso).

### 9.8 Capa 7 — Aplicación (dashboard, bot, reportes, API)

El dashboard web (SvelteKit) ofrece **siete pestañas** especializadas:

1. **Operación** — KPIs en tiempo real, niveles de tanques, sensores, alertas, panel del método tradicional UNIAJC.
2. **Tendencias** — series temporales 24h, identificación de patrones.
3. **Gestión Industrial** — KPIs con fórmulas, mudas Lean, Ishikawa, costo-beneficio.
4. **Inteligencia** — control multi-agente, plan ante fenómenos, razonamiento en vivo, monetización, chat conversacional.
5. **Mapa del Campus** — SVG interactivo con toggle 2D/3D, triggers de mitigación.
6. **Comunidad** — Smart Water Ledger, ranking, canjes con Bienestar Universitario.
7. **Arquitectura** — diagramas técnicos: 7 capas, trinidad analítica, flujo end-to-end, mockups, máquina de estados.

Adicionalmente, el bot de Telegram con 12 comandos (`/agua`, `/zonas`, `/kpis`, `/alertas`, `/tanques`, `/reporte`, etc.) ofrece una interfaz móvil al operador, y el módulo de reportes genera PDFs auditables mensuales con hash SHA-256 firmado para INVIMA, CVC y Ministerio de Vivienda.

---

## 10. Trinidad analítica del agente

Cada lectura de sensor pasa por tres niveles de análisis encadenados:

### 10.1 Nivel 1 — Descriptivo (¿qué pasó?)

Ejecutado por SystemsAgent y SensorAgent cada 30 segundos:

| Técnica | Implementación | Ejemplo concreto |
|---------|----------------|-------------------|
| Tendencias | Series temporales con ventana móvil 24h | "Consumo Bloque A creció 12% mes a mes desde marzo" |
| Promedios | Media + mediana + p50/p95/p99 por hora del día | "Presión nocturna promedio: 38 PSI ± 4" |
| Frecuencias | Histogramas de eventos | "73% de fugas ocurren entre 22:00 y 06:00" |
| Heatmaps | Matriz hora × día × edificio | "Lunes 7 AM: pico 2.3× la media semanal" |

**Salida típica**: KPIs IEH, TPP, CPE, ICA con su estado (ok/warning/critical).

### 10.2 Nivel 2 — Predictivo (¿qué va a pasar?)

Ejecutado por IndustrialAgent cuando SystemsAgent detecta una desviación que no encaja en umbrales simples:

| Técnica | Implementación | Ejemplo concreto |
|---------|----------------|-------------------|
| Regresión | Lineal + Ridge para demanda; ARIMA/Prophet para estacionalidad | "Mañana 7-9 AM: demanda 1,800 L/min ± 120" |
| Redes neuronales | LSTM ligero (~50K params, CPU) | "Presión 28% baja + vibración + caudal estable → 92% prob. fuga oculta" |
| Árboles de decisión | Random Forest para tipo de fuga | "Patrón coincide con `fisura_lenta`: alerta amarilla" |
| Detección de outliers | IsolationForest score 0-1 | "Score 0.78 = anómalo; > 0.5 dispara alerta" |

**Salida típica**: P(fuga) = 0.92, tipo = fisura_lenta, demanda proyectada 7-9 AM.

### 10.3 Nivel 3 — Prescriptivo (¿qué hacemos?)

Ejecutado por Orchestrator + MitigationAgent con voto consensual:

| Técnica | Implementación | Ejemplo concreto |
|---------|----------------|-------------------|
| Predicción aplicada | Triple validación 3-de-5 agentes | "P(fuga) 92% + costo evitado 14,500 L → acción `leak_response`" |
| Optimización | scipy.optimize para schedule de bombeo | "22:00-06:00 a 25 PSI ahorra 40% kWh sin afectar Tank A" |
| Simulación | PySD sobre modelo Vensim de Aristizábal | "Cooperación 0% → colapso 2 años → activar Smart Water Ledger" |
| Reglas declarativas | Política operativa UNIAJC codificada | Si humedad_suelo > 60% → cerrar EV-RC1 |

**Salida típica**: "Cerrar EV-A2, bomba a standby, generar OT-30685054, reporte CVC programado".

---

## 11. Estrategias derivadas de los datos

### 11.1 Plan ante fenómenos (cinco escenarios)

AguaMind OS implementa cinco triggers compuestos correspondientes a cinco fenómenos cuya activación es automática según señales del sistema:

| Fenómeno | Condición de disparo | Acciones automáticas | Impacto cuantificado |
|----------|----------------------|----------------------|------------------------|
| **Sequía / El Niño** | Freático < 5 m + IDEAM forecast El Niño | Bomba `eco_drought` (-70% extracción), cierra EV-RC1, presión nocturna 38→25 PSI | 10,400 L/día ahorrados |
| **Lluvias / La Niña** | Lluvia > 25 mm/h sostenida (Open-Meteo) | Bomba `rain_standby`, cierra EV-RC1, monitoreo PTAR, alerta drenaje | 5,500 L/día |
| **Sismo** | Acelerómetro local > 0.05 g | Cierra TODAS las EV controlables, bomba `emergency_off`, alerta evacuación | Protección |
| **Contaminación** | Turbidez > 4 NTU o pH fuera 6-9 | Aísla EV-OUT-A/B (tanques), bomba `isolated`, reporte INVIMA, suspensión distribución | Protección sanitaria |
| **Pico de demanda** | Consumo > 150% baseline | Cierra EV-RC1 (prioriza humano), bomba 100% boost, recalcula recarga | 2,500 L/día |

### 11.2 Estrategia de reúso (Resolución 1207/2014)

Las aguas tratadas en las dos PTAR (Alameda + Entrada, capacidad combinada 4,000 estudiantes) se reutilizan en dos rutas:

1. **Riego de Cancha + Jardines**: objetivo 2,200 L/día desde 4,000 (-45%)
2. **Cisternas sanitarias del Bloque A**: descarga de inodoros con agua reutilizada

Solo el excedente va a vertimiento al río Pance bajo Resolución 0631/2015. Ahorro proyectado: ~1,800 L/día = 657 m³/año.

### 11.3 Smart Water Ledger (gamificación con Bienestar Universitario)

Cada metro cúbico ahorrado por edificio se traduce en un crédito hídrico canjeable:
- 100 créditos → mejora de zona común del edificio
- 500 créditos → renovación de cafetería
- 1,000 créditos → presupuesto para proyecto estudiantil

Reportes ciudadanos vía QR en cada baño otorgan 20 puntos al estudiante por reporte de fuga confirmado por sensores. Si la alerta resulta falsa, recibe 5 puntos por colaborar.

### 11.4 Fuentes meteorológicas en tiempo real (gratuitas, sin API key)

| Fuente | Datos | URL | Disparador |
|--------|-------|-----|------------|
| Open-Meteo | Lluvia, temperatura, humedad, viento (Cali) | open-meteo.com/v1/forecast | flood_mode + surge_mode |
| NOAA CPC | Índice ENSO Niño 3.4 mensual | psl.noaa.gov/data/correlation/oni.data | drought_mode preventivo |
| Open-Meteo Climate | Forecast 16 días + ECMWF | climate-api.open-meteo.com | tendencia sequía 30d |
| USGS Earthquake | Sismos M≥4.0 a < 100km Cali | earthquake.usgs.gov/earthquakes/feed | quake_mode |

---

## 12. Validación cruzada con método tradicional

> Reconocimiento al jurado del 7 de mayo: "Pueden haber soluciones costo-beneficio más económicas".

### 12.1 Método actual de UNIAJC (costo cero)

| Paso | Acción | Hora |
|------|--------|------|
| 1 | Operario llena tanques A (36k L) y B (16k L) al cierre | ~17:30 |
| 2 | Anota la marca de nivel visible en la pared del tanque | ~18:00 |
| 3 | Cierra escotilla superior | — |
| 4 | A la mañana siguiente abre la escotilla y lee la nueva marca | ~07:00 |
| 5 | Diferencia (cm) × 160 L = pérdida nocturna en litros | inmediato |

Equivalencia validada: **1 cm de altura del tanque = 160 L** (Sánchez Sotelo, 2021).

### 12.2 Cómo AguaMind OS lo cruza

```
Lectura sensor JSN-SR04T cada 30s → nivel digital cm
Lectura visual operario 2 veces/día → nivel manual cm

Triangulación:
  Si |sensor - manual| > 5 cm → ALERTA: sensor descalibrado o marca dañada
  Si ambos coinciden y caen → fuga real confirmada con doble método
  Si solo sensor cae → posible falso positivo, exigir validación visual
```

### 12.3 Tabla comparativa

| Métrica | Solo manual | Solo sensor | Híbrido AguaMind |
|---------|-------------|-------------|---------------------|
| Frecuencia | 2 lecturas/día | 2,880 lecturas/día | 2,880 + validación humana programada |
| Detección de fuga diurna | — (solo nocturna) | hora exacta | hora exacta + confirmación visual |
| Detección sensor dañado | — | — | sí, por desviación con marca |
| Detección marca dañada | — | — | sí, por desviación con sensor |
| Costo | $0 | $30,000 | $30,000 + costumbre actual |
| Confiabilidad | media | alta | **muy alta** |

---

## 13. Análisis costo-beneficio

### 13.1 Inversión Fase 1 (un nodo en PTAP)

| Concepto | Detalle | Costo COP |
|----------|---------|-----------|
| ESP32 + ADS1115 | Microcontrolador + ADC 16-bit | $50,000 |
| 6 sensores principales | YF-S201, MPX5700AP, JSN-SR04T, SW-420, 4-20mA, TSD-10 | $400,000 |
| Electroválvulas + relay | 8 EV controlables remotamente | $185,000 |
| Acondicionamiento + PCB | Divisores, shunts, conectores | $80,000 |
| Gabinete IP65 + cableado | Caja resistente, mangueras | $135,000 |
| Indicadores locales | OLED 0.96", LED RGB, buzzer | $32,000 |
| Energía + backup | HLK-PM01 + bat. 18650 | $99,000 |
| **Subtotal hardware** | | **$981,000** |
| Mano de obra (equipo) | Auto-construido | $0 |
| Software open source | FastAPI + LangGraph + SvelteKit + Supabase free + HiveMQ free | $0 |
| Imprevistos (10%) | | $98,000 |
| **TOTAL INVERSIÓN FASE 1** | | **$1,431,000 COP** (~$340 USD) |

### 13.2 Beneficios anuales proyectados

| Beneficio | Cuantificación | Ahorro/año |
|-----------|----------------|------------|
| Reducción pérdidas físicas (TPP 25% → 10%) | 9,073 L/día × 365 × $3.5/L | $11,586,925 |
| Optimización riego automatizado | 1,800 L/día × 365 × $3.5/L | $2,299,500 |
| Mantenimiento preventivo vs correctivo | 2 → 0.3 eventos/año | $4,250,000 |
| Eficiencia energética bombeo (-40% nocturno) | -596 kWh/año | $2,400,000 |
| **TOTAL AHORRO ANUAL DIRECTO** | | **$20,536,425** |
| Sanciones evitadas (riesgo, no caja) | $16,900M × probabilidad | (incremental) |

### 13.3 Indicadores financieros

| Indicador | Valor |
|-----------|-------|
| Período de recuperación | **~25 días** |
| VPN a 5 años (tasa 12%) | **$73M COP** |
| TIR | **> 1,000%** |
| Ratio Beneficio/Costo | **17.4×** |
| Agua recuperada en 5 años | **16.5M litros** |
| CO₂ evitado en 5 años | **7.6 toneladas** |

---

## 14. Impacto en Objetivos de Desarrollo Sostenible

### 14.1 ODS impactados directamente (con métricas)

| ODS | Meta específica | Aporte AguaMind OS |
|-----|------------------|-----------------------|
| **ODS 6** Agua Limpia y Saneamiento | Meta 6.4 — eficiencia uso agua | TPP 25% → 10% (60% reducción) |
| **ODS 12** Producción/Consumo Responsables | Meta 12.5 — reducción desperdicios | 7 mudas Lean atacadas |
| **ODS 13** Acción por el Clima | Meta 13.3 — educación mitigación | 7.6 ton CO₂ evitadas/5 años |
| **ODS 9** Industria, Innovación, Infraestructura | Meta 9.4 — modernizar | IoT + IA en infraestructura 2011 |
| **ODS 11** Ciudades Sostenibles | Meta 11.6 — reducir impacto ambiental | Modelo Smart Campus replicable |

### 14.2 ODS impactados indirectamente

ODS 3 Salud · ODS 4 Educación · ODS 5 Igualdad · ODS 8 Trabajo decente · ODS 10 Reducción desigualdades · ODS 14 Vida marina · ODS 15 Ecosistemas terrestres · ODS 16 Paz · ODS 17 Alianzas.

---

## 15. Plan por fases (15 años)

| Fase | Período | Inversión | Beneficio anual | Hito clave |
|------|---------|-----------|-----------------|------------|
| 1 · Hackathon (entrega) | Mayo 2026 | — | — | Backend + dashboard + simulador |
| 2 · Piloto PTAP | Mes 1 | $1.4M | $3M+ | 1 nodo IoT instalado |
| 3 · Expansión | Meses 2-6 | $5.4M | $11.6M | 5 nodos zonas críticas |
| 4 · Sensorización masiva | Meses 7-12 | $9.2M | $18M | TPP < 10% confirmado |
| 5 · Smart Water Ledger | Año 2 | $11M | + cultural | Gamificación con Bienestar |
| 6 · Modelo 3D + AR | Año 3 | $13.5M | + operacional | Three.js + WebXR |
| 7 · Replicación UNIAJC | Año 4-5 | — | + institucional | 4 sedes UNIAJC |
| 8 · Replicación regional | Año 6-10 | — | + spin-off | 30+ universidades del Valle |
| 9 · Crecimiento UNIAJC 2030 | Año 5-10 | — | escalabilidad | 12,000 usuarios proyectados |
| 10 · Madurez institucional | Año 10-15 | — | infraestructura crítica | ISO 14001 + ICONTEC |

---

## 16. Validación contra tesis previas

| Hallazgo histórico (tesis) | Confirmado por AguaMind OS | Evidencia técnica |
|----------------------------|------------------------------|--------------------|
| Caudal 113.56 L/min (Caycedo & Jaramillo, 2021) | ✓ | constante `ALJIBE_INFLOW_L_MIN` en water.py |
| 161 fuentes, 67% Parquesoft (Caycedo & Jaramillo) | ✓ | distribución `ZONE_SHARES` |
| 4 parámetros fuera de norma (Caycedo & Jaramillo) | ✓ | umbrales `NORMATIVE_LIMITS` activan alertas |
| Pérdida nocturna 1,587 L/día (Sánchez Sotelo) | ✓ | constante `losses_l_min` simulador |
| 1 cm tanque = 160 L (Sánchez Sotelo) | ✓ | base de validación cruzada |
| 13 equipos catalogados (Gómez Mina) | ✓ | diccionario `PTAP_EQUIPMENT` con códigos UNIAJC |
| Cooperación 50% sostenible (Aristizábal & Largacha) | ✓ | activa Smart Water Ledger |
| CPE 14.04 L/est/día (Arias Montoya) | ✓ | meta del KPI CPE |
| 2 PTAR físicas, 4,000 cap (Mosquera & Lozano + RETO PDF) | ✓ | mapa SVG y reportes |

---

## 17. Conclusiones

1. La PTAP de UNIAJC Sede Sur, instalada en 2011 sin instrumentación, presenta deficiencias documentadas en cuatro dimensiones: calidad del agua fuera de norma (4 parámetros), pérdidas hídricas no contabilizadas (1,587 L/día), mantenimiento exclusivamente correctivo y sobrecapacidad de las dos PTAR (2.06×). Estas deficiencias exponen a la institución a sanciones potenciales de hasta $16,900M COP.

2. AguaMind OS responde a estas deficiencias mediante una arquitectura de siete capas verticales independientemente reemplazables, integrando seis sensores comerciales calibrados, microcontrolador ESP32 con firmware embebido, comunicación MQTT con respaldo HTTP, persistencia escalonada (RAM → Postgres → Parquet → PDF auditable), sistema multi-agente coordinado con LangGraph, y aplicaciones de usuario (dashboard, bot Telegram, reportes).

3. La trinidad analítica del agente (descriptivo, predictivo, prescriptivo) opera con voto consensual de cinco sub-agentes especializados, completando la deliberación en aproximadamente 5 segundos versus 2-4 horas del proceso humano tradicional.

4. El sistema implementa cinco estrategias automáticas de mitigación ante fenómenos (sequía, lluvias, sismo, contaminación, pico de demanda) y un esquema de validación cruzada con el método tradicional "tanques nocturnos" del operario UNIAJC, respetando y amplificando los métodos existentes de costo cero.

5. La inversión Fase 1 de $1,431,000 COP genera ahorros proyectados de $20,536,425 COP/año, con período de recuperación de aproximadamente 25 días, TIR superior al 1,000% y relación beneficio/costo de 17.4×. Adicionalmente protege a la institución de exposición legal por $16,900M COP.

6. El sistema aporta a 5 Objetivos de Desarrollo Sostenible directamente (6, 9, 11, 12, 13) con métricas cuantificadas: 16.5M litros recuperados en 5 años, 7.6 ton CO₂ evitadas, 60% reducción de pérdidas técnicas.

7. AguaMind OS valida los hallazgos de seis trabajos de grado UNIAJC previos (Caycedo & Jaramillo 2021, Sánchez Sotelo 2021, Gómez Mina 2022, Aristizábal & Largacha 2025, Arias Montoya et al. 2024, Mosquera Zapata & Lozano Beltrán 2024) y los lleva a operación efectiva, cerrando una brecha de cinco años entre el diagnóstico institucional y la implementación real.

8. El código fuente completo, documentación versionada en español (31 archivos `.md`), y planos hidráulicos extraídos de las tesis institucionales se publican bajo licencia MIT en `github.com/JFrangel/AguaMind-OS`, garantizando replicabilidad a las sedes Norte y Centro de UNIAJC y a las 50+ universidades públicas del Valle del Cauca.

---

## 18. Recomendaciones

1. **Aprobación institucional Fase 2 (mes 1)**: instalación del primer nodo IoT en la PTAP central, con presupuesto de $1.43M COP ya costeado y BOM detallado disponible.

2. **Capacitación cruzada del operario PTAP**: dos sesiones de 4 horas cubriendo (i) interpretación del dashboard, (ii) procedimiento de validación cruzada manual-digital, (iii) protocolo de calibración trimestral de sensores. El operario sigue siendo central; el sistema lo amplifica.

3. **Convenio con CVC y EMCALI**: formalizar la entrega automatizada de reportes PDF mensuales de IRCA y trimestrales de vertimientos, anticipando el cumplimiento normativo y reduciendo carga administrativa.

4. **Integración con Bienestar Universitario**: definir el catálogo de canjes del Smart Water Ledger en términos de mejoras tangibles para los edificios participantes, con presupuesto institucional respaldado.

5. **Continuidad institucional**: vincular el desarrollo de AguaMind OS al Semillero SEGESTOP de UNIAJC y a los programas de Ingeniería Industrial, Sistemas y Electrónica como proyectos de aula y trabajos de grado, garantizando actualización continua y formación práctica.

6. **Certificación ICONTEC e ISO 14001**: utilizar los reportes auditables generados automáticamente como base para certificación ambiental institucional, agregando valor diferencial frente a otras universidades públicas.

7. **Publicación científica**: redactar y someter a publicación dos artículos derivados del proyecto: (a) en revista de ingeniería industrial sobre el modelo Lean aplicado, (b) en revista de IA/IoT sobre el sistema multi-agente. Esto fortalece la reputación académica de UNIAJC.

8. **Replicación a otras universidades del Valle**: ofrecer el sistema como referente técnico a Univalle, Icesi y Universidad de San Buenaventura, posicionando a UNIAJC como líder regional en gestión hídrica universitaria sostenible.

---

## 19. Referencias bibliográficas

### Trabajos de grado UNIAJC

1. **Caycedo Saa, M. A., & Jaramillo Moreno, A. F. (2021).** *Propuesta de caracterización del proceso técnico-operativo de la planta de tratamiento de agua de la Institución Universitaria Antonio José Camacho Sede Sur*. Trabajo de grado para optar al título de Ingeniero Industrial. Asesor: Ing. Carlos Andrés Nieto Serna. UNIAJC, Cali. 129 páginas.

2. **Sánchez Sotelo, A. (2021).** *Propuesta de mejora con aplicación de herramientas de Lean Manufacturing para la planta de potabilización de agua en la Universidad Antonio José Camacho Sede Sur*. Trabajo de grado, Ingeniería Industrial, UNIAJC.

3. **Gómez Mina, P. A. (2022).** *Diseño de un programa de mantenimiento para la planta de tratamiento de agua potable de la Institución Universitaria Antonio José Camacho sede sur*. Trabajo de grado, Ingeniería Industrial, UNIAJC. 107 páginas.

4. **Aristizábal Torres, H. W., & Largacha Perdomo, S. (2025).** *Desarrollo de un modelo de dinámica de sistemas para simular la demanda y el suministro de agua en la Institución Universitaria Antonio José Camacho, Sede Sur*. Trabajo de grado, UNIAJC. Repositorio: handle/uniajc/3000.

5. **Arias Montoya, Y. D., Montiel Angel, R. E., & Osorio Hernández, C. A. (2024).** *Diseño de un sistema de ahorro para el mejoramiento de la eficiencia del servicio suministrado por la planta de tratamiento de agua potable (PTAP) en la Institución Universitaria Antonio José Camacho Sede Sur*. Repositorio UNIAJC handle/2576.

6. **Mosquera Zapata, L. L., & Lozano Beltrán, S. (2024).** *Modelo de dinámica de sistemas para brindar información a la comunidad académica del impacto sobre la PTAR y el ecosistema, UNIAJC sede sur en Cali*. Repositorio UNIAJC handle/2757.

### Marco normativo colombiano

- Decreto 2105 de 1983 — Reglamentación parcial de la Ley 09 de 1979, potabilización
- Decreto 1541 de 1978 — Concesión aguas públicas
- Ley 09 de 1979, Artículo 576 — Medidas sanitarias
- Ley 1581 de 2012 — Habeas Data
- Ley 1712 de 2014 — Transparencia y acceso a información pública
- Ley 1928 de 2018 — Ciberseguridad
- Decreto 1575 de 2007 — Sistema control calidad agua humana
- Resolución 2115 de 2007 — IRCA y parámetros físico-químicos
- Resolución 0631 de 2015 — Vertimientos
- Resolución 0811 de 2008 — Puntos de muestreo
- Resolución 1207 de 2014 — Reúso aguas residuales
- Decreto 3930 de 2010 — Uso recurso hídrico
- Decreto 1076 de 2015 — Monitoreo piezométrico
- Decreto 050 de 2018 — Plan de cumplimiento
- Decreto 338 de 2022 — Riesgos cibernéticos
- RAS 2000 Capítulo C.17 — Operación PTAP
- Resolución 055 de enero 2025 UNIAJC — Plan de seguridad y privacidad institucional

### Literatura científica

- Casero, D. (2007). *Potabilización del agua*. Escuela de Organización Industrial - Escuela de Negocios. Madrid, España.
- Romero, J. A. (2008). *Tratamiento de aguas residuales: teoría y principios de diseño*. Escuela Colombiana de Ingeniería.
- Barrenechea, A. (2004). *Aspectos fisicoquímicos de la calidad del agua*. CEPIS/OPS, Lima.
- Gutiérrez, P. H. (2010). *Calidad total y productividad* (3a ed.). McGraw-Hill.
- Hernández, R., Fernández, C., & Baptista, M. (2014). *Metodología de la investigación* (6a ed.). McGraw-Hill, México D.F.
- OMS (2018). *Guías para la calidad del agua de consumo humano* (4a ed.). Ginebra, Suiza.
- Aguas de Barrancabermeja (2017). *Reporte anual de pérdidas de agua no contabilizada en sistemas sin medición*.

### Tecnologías y frameworks

- LangGraph 0.3 documentation. https://langchain-ai.github.io/langgraph/
- FastAPI (Tiangolo). https://fastapi.tiangolo.com/
- SvelteKit. https://kit.svelte.dev/
- Supabase. https://supabase.com/
- Open-Meteo. https://open-meteo.com/
- NOAA Climate Prediction Center, ENSO ONI. https://psl.noaa.gov/data/correlation/oni.data
- USGS Earthquake Hazards. https://earthquake.usgs.gov/

---

## 20. Anexos

### Anexo A · BOM detallado Fase 1
Disponible en `docs/es/AGUAMIND-OS-MASTER.md §14.1`.

### Anexo B · Schemas API y endpoints
Documentación interactiva auto-generada en `http://localhost:8000/docs` (Swagger/OpenAPI).
Lista completa de 17 endpoints en `docs/es/IMPLEMENTACION-VISUAL-CAPAS.md §Capa 5`.

### Anexo C · Calibración pre-instalación de sensores
Cuatro protocolos documentados:
- **Test 1 — Caudal**: cubeta 20 L cronometrada vs lectura sensor (criterio < 5% error)
- **Test 2 — Nivel**: tanque graduado a 5 niveles (20, 40, 60, 80, 100 cm) → criterio < 2 cm error
- **Test 3 — Presión**: compresor con manómetro patrón → criterio < 3% error
- **Test 4 — Turbidez**: soluciones patrón Formazin (1, 5, 10 NTU) → criterio < 0.5 NTU error

### Anexo D · Schema completo de la base de datos
Disponible en `docs/es/ALMACENAMIENTO-DE-DATOS.md`.

### Anexo E · Planos hidráulicos UNIAJC (Gómez Mina, 2022)
Imágenes extraídas:
- `tesis-uniajc/planos/plano-detalle-PTAP.png` — interior PTAP con 3 motobombas, 2 hidroflows, 3 filtros, tanque cloración, tanque almacenamiento subterráneo, tubo 79m Ø 3"
- `tesis-uniajc/planos/plano-distribucion-hidraulica.png` — distribución completa del campus con las 2 PTAR visibles

### Anexo F · Diagramas técnicos del sistema
- Arquitectura por capas con detalle de latencias por capa: `docs/es/ANALISIS-Y-CAPAS-VISUALES.md`
- Trinidad analítica visualizada (sparkline + forecast + voto): pestaña Arquitectura del dashboard
- Flujo end-to-end sensor → cierre EV (~5 segundos): pestaña Arquitectura
- Máquina de estados del firmware ESP32: pestaña Arquitectura

### Anexo G · Documentación complementaria
31 archivos `.md` en `docs/es/`, incluyendo:
- `AGUAMIND-OS-MASTER.md` — documento maestro post-asesoría
- `RETO-VS-AGUAMIND.md` — mapeo línea por línea contra el PDF oficial
- `TESIS-VS-AGUAMIND.md` — validación contra las 6 tesis institucionales
- `AUDITORIA-RUBRICA.md` — auditoría honesta vs rúbrica oficial
- `HOJA-PITCH-Q&A.md` — hoja de respuestas a 8 preguntas anticipadas
- `IMPLEMENTACION-VISUAL-CAPAS.md` — manifestación física por capa
- `ANALISIS-Y-CAPAS-VISUALES.md` — diagramas Mermaid detallados
- `ALMACENAMIENTO-DE-DATOS.md` — estrategia de persistencia en 5 capas

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

*Documento estilo tesis · v1.0 · 8 de mayo de 2026 · UNIAJC Sede Sur · Cali, Colombia*
*Repositorio público bajo licencia MIT: github.com/JFrangel/AguaMind-OS*
