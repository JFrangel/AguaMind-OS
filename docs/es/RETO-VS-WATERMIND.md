# WaterMind OS - Reto oficial vs lo que entregamos

> Este documento mapea **palabra por palabra** los requisitos del PDF oficial
> *"HACKATHON-FACULTAD DE INGENIERIA UNIAJC-2026 - Gestion del agua en la sede sur"*
> contra lo que WaterMind OS implementa.
>
> Hackathon UNIAJC 2026 - v1.0

---

## 1. Realidad fisica del campus (segun el PDF oficial del reto)

### Sistema de abastecimiento (potable)

| Elemento | Cantidad | Capacidad / dato | Como lo modela WaterMind |
|----------|---------|------------------|--------------------------|
| Aljibes | 2 | 113.56 L/min combinado | A1 + A2 en el mapa, conectados a YF-S201 |
| PTAP | 1 | 3 etapas: grava+arena, antracita, carbon activado | Tres filtros SF-FT-01/02/03 catalogados |
| Tanques almacenamiento | 2 | 36,000 L + 16,000 L con control automatico | Tank A + Tank B con clip-path por nivel real |
| Edificios principales | 2 | Bloque A + Alameda | Cards en band 2 del mapa |
| Servicios secundarios | 3 | Cafeteria, Laboratorios, Cancha+Jardines | Cards en band 2 y 3 del mapa |
| Area campus | - | 38,755.88 m^2 | Header del mapa |
| Poblacion | - | 8,234 usuarios totales | Constante TOTAL_USERS en water.py |
| Consumo total | - | 45,367 L/dia (14.04 L/est/dia) | DAILY_CONSUMPTION_L = 45,367 |

### Sistema de tratamiento de aguas residuales (PTAR)

> Cita textual del PDF oficial, Figura 1:
> *"Dos (2) Sistemas de tratamiento de aguas residuales domesticas en la Universidad
> Antonio Jose Camacho. **Cada PTAR tiene dos modulos iguales trabajando en paralelo.
> Cada modulo esta en capacidad de atender a 1000 estudiantes.** Imagen derecha: PTAR
> Entrada. Imagen izquierda: PTAR Alameda."*

| PTAR | Modulos | Cap. por modulo | Cap. total PTAR | Reflejado en el mapa |
|------|---------|-----------------|-----------------|----------------------|
| PTAR Alameda | 2 paralelo | 1,000 est | 2,000 est | "PTAR Alameda · 2 mod. en paralelo · 2,000 est" |
| PTAR Entrada | 2 paralelo | 1,000 est | 2,000 est | "PTAR Entrada · 2 mod. en paralelo · 2,000 est" |
| **Capacidad total** | **4 modulos** | - | **4,000 est** | "Sobrecapacidad PTAR (2.06x): 4,000 est cap · 8,234 reales" |

**Conclusion:** la sobrecapacidad real es **2.06 veces** (8,234 / 4,000), no 4x como suponian
docs anteriores que usaban el dato erroneo de 2,000 cap. WaterMind ya esta corregido.

---

## 2. Cobertura de los retos minimos

### 2.1 Retos minimos de SISTEMAS

| Requisito del reto | Implementacion WaterMind | Donde verificarlo |
|--------------------|--------------------------|---------------------|
| Arquitectura de software con portabilidad, mantenibilidad, seguridad | Monorepo limpio: 1 frontend SvelteKit + 1 backend FastAPI + 1 bot Telegram. Pydantic en bordes, env vars para secretos | [package.json](../../package.json), [docs/es/ARQUITECTURA.md](ARQUITECTURA.md) |
| Arquitectura presentada en UML | Diagrama UML de componentes + UML de estados del agente | [docs/es/DIAGRAMAS-Y-DISEÑO.md](DIAGRAMAS-Y-DISEÑO.md) y [ANALISIS-Y-CAPAS-VISUALES.md](ANALISIS-Y-CAPAS-VISUALES.md) |
| Interfaces con principios de Diseno Centrado en el Usuario | Dashboard `/agua` con tabs por persona (operador / estudiante / admin), feedback inmediato, semaforos de severidad | [apps/web-svelte/src/routes/agua/+page.svelte](../../apps/web-svelte/src/routes/agua/+page.svelte) |
| **Al menos un agente** que monitoree y tome decision autonoma + diagrama de flujo o estados UML | **5 agentes** (Orchestrator, Systems, Sensor, Industrial, Mitigation) coordinados con LangGraph. Diagrama de estados en doc + sequence diagrams en analisis-capas | Ver [ANALISIS-Y-CAPAS-VISUALES.md](ANALISIS-Y-CAPAS-VISUALES.md) seccion 1.4 + 3.1 |

### 2.2 Retos minimos de ELECTRONICA

| Requisito del reto | Implementacion WaterMind |
|--------------------|--------------------------|
| Circuito de medicion + acondicionamiento (esquema sensado + acondicionamiento) | 6 sensores con acondicionamiento documentado: divisor 5V->3.3V (YF-S201, JSN-SR04T), shunt 150 ohm para 4-20 mA, ADS1115 16-bit I2C para analogos criticos. Especificado en [packages/sensors/registry.py](../../services/api/app/sensors/registry.py) y [docs/es/IMPLEMENTACION-TECNICA-SENSORES.md](IMPLEMENTACION-TECNICA-SENSORES.md) |
| Interfaz local + comunicacion con interfaz remota | Local: OLED 0.96" + LED RGB + buzzer en el ESP32. Remota: MQTT 8883 TLS a HiveMQ + HTTP fallback POST `/water/ingest` |
| Arquitectura embebida (sensado, procesamiento, comunicacion, alimentacion) | 4 modulos documentados: sensado (6 sensores + ADS1115), procesamiento (ESP32 dual-core), comunicacion (WiFi + MQTT + HTTP fallback + NVS), alimentacion (HLK-PM01 220->5V + bateria 18650 backup) |
| Especificacion de bloques + diagrama de flujo del firmware | Firmware MicroPython con 2 cores: Core 0 lee sensores 1 Hz + media movil N=10; Core 1 promedia 30 s y publica MQTT. Diagrama en [ANALISIS-Y-CAPAS-VISUALES.md seccion 2.2 (CAPA 3)](ANALISIS-Y-CAPAS-VISUALES.md) |

### 2.3 Retos minimos INDUSTRIAL

| Requisito del reto | Implementacion WaterMind | Resultado |
|--------------------|--------------------------|-----------|
| **Diagrama de proceso (flujo)** entradas + procesos + usos | SVG interactivo en `/agua` -> "Mapa del Campus" muestra aljibes -> PTAP -> tanques -> 6 zonas de uso -> PTAR -> rio | Visible en vivo |
| **Identificacion de variables clave** caudal, demanda, perdidas | 6 variables monitoreadas: caudal (YF-S201), presion (MPX5700AP), nivel (JSN-SR04T), vibracion (SW-420), freatico (4-20 mA), turbidez (TSD-10) | Endpoint `/water/reading` |
| **3 indicadores con formula y proposito** | Implementados **4 KPIs** (excede el minimo): IEH, TPP, CPE, ICA | Endpoint `/water/status` -> KPIs |
| Identificacion de mudas Lean (7 tipos) | Tabla completa en [TESIS-VS-WATERMIND.md](TESIS-VS-WATERMIND.md) seccion "Tesis 2" | Visible en tab "Gestion Industrial" |
| Diagrama de Ishikawa (causa-efecto) | 5 categorias: Medicion, Infraestructura, Personas, Procesos, Gestion. Causa raiz: falta de instrumentacion desde 2011 | [docs/es/WATERMIND-OS-DOCUMENTACION.md seccion 7.3](WATERMIND-OS-DOCUMENTACION.md) |
| **Minimo 2 acciones concretas + impacto** | Implementadas **5 estrategias automatizadas**: leak_response, peak_irrigation, turbidity, tank_overflow, phreatic_low | Botones interactivos en el dashboard |
| **Costo-beneficio** cuanto cuesta + cuanto ahorra + recuperacion | Inversion $1.43M COP / Ahorro $20.5M COP/ano / Recuperacion 25 dias / TIR > 1,000% | [TESIS-VS-WATERMIND.md seccion costo-beneficio](TESIS-VS-WATERMIND.md) |

### KPIs detallados con formula y proposito (>= 3 requeridos)

| KPI | Formula | Proposito | Estado actual |
|-----|---------|-----------|---------------|
| **IEH** Indice de Eficiencia Hidrica | `((Q_entrada - Perdidas) / Q_entrada) x 100` | Mide cuanta agua llega al uso real vs lo extraido | Meta > 90%, actual ~26% (critico) |
| **TPP** Tasa de Perdidas del Proceso | `Perdidas / Q_entrada x 100` | Cuantifica el desperdicio del sistema | Meta < 10%, actual ~74% (critico) |
| **CPE** Consumo Per Estudiante | `Consumo_diario / Estudiantes_activos` | Detecta abuso o ineficiencia per capita | Meta <= 14.04, actual 3.6 (optimo en demo) |
| **ICA** Indice de Calidad del Agua | `100 - (Turbidez_NTU / 4) x 30` | Cumplimiento Resolucion 2115/2007 (turbidez maxima 4 NTU) | Meta > 90 pts, actual 92.3 (optimo) |

---

## 3. Preguntas integradoras del reto - como las cubre WaterMind

### "Como disenar un sistema inteligente que mida, analice y optimice el uso del agua?"

**Cubierto.** Los **3 niveles de analisis** se ejecutan en cada ciclo de 30 s:
- **Descriptivo** (que paso): KPIs en vivo, tendencias, patrones por zona/hora
- **Predictivo** (que va a pasar): Random Forest + LSTM para fugas; ARIMA para demanda
- **Prescriptivo** (que hacemos): cierre EV automatico, optimizacion de bombeo, simulacion Vensim

Detalle: [ANALISIS-Y-CAPAS-VISUALES.md](ANALISIS-Y-CAPAS-VISUALES.md)

### "Como reducir consumo sin afectar actividades academicas ni bienestar?"

**Cubierto.** Estrategia de bombeo eco-nocturno (38 -> 25 PSI en horario 22:00-06:00) ahorra 40% kWh sin afectar nivel de tanque. Riego automatico solo cuando humedad de suelo < 60% y fuera del rango 10:00-16:00 (alta evaporacion). Resultado proyectado: -45% riego (4,000 -> 2,200 L/dia) sin afectar la cancha.

### "Como transformar datos en decisiones operativas y cambios de comportamiento?"

**Cubierto.** Smart Water Ledger conecta consumo medido por edificio con creditos del Bienestar Universitario:
- 100 creditos -> mejora zona comun
- 500 -> renovacion cafeteria
- 1,000 -> presupuesto proyecto estudiantil

Ranking publico mensual. QR en banos para reportes ciudadanos (+20 pts si confirma sensor).

### "Que soluciones permiten reutilizar el agua (aguas grises) dentro del campus?"

**Cubierto.** Esquema visible en el mapa:
- Aguas tratadas en PTAR Alameda y PTAR Entrada (Resolucion 1207/2014) -> riego de Cancha + Jardines (objetivo 2,200 L/dia desde 4,000)
- Aguas tratadas -> cisternas sanitarias del Bloque A (descarga de inodoros)
- Solo el excedente va a vertimiento al rio Pance

Ahorro: ~1,800 L/dia recuperados = 657 m^3/ano.

### "Como anticipar problemas de abastecimiento considerando crecimiento poblacional 2030?"

**Cubierto.** Plan por fases a 15 anos en [WATERMIND-OS-MASTER.md seccion 13](WATERMIND-OS-MASTER.md). El modelo Vensim de Aristizabal & Largacha (2025) integrado: con cooperacion 0% colapsa en 2 anos; con cooperacion 50% es sostenible a largo plazo. Smart Water Ledger materializa la "cooperacion".

---

## 4. Lo que el reto NO pide pero WaterMind aporta extra

| Plus | Por que importa |
|------|-----------------|
| **Normalizador universal de sensores** | Acepta JSON, CSV, NDJSON, Modbus, OPC-UA, SCADA tag-based, MQTT, ESP32 compacto. Si manana se cambia el proveedor de sensores, no se reescribe nada del backend |
| **Cumplimiento Resolucion 055/2025 UNIAJC** | Auditoria de accesos + logs estructurados + pseudonimizacion (Habeas Data Ley 1581/2012) ya integrados en el plan de almacenamiento |
| **5 agentes en lugar de 1** | El reto pide "al menos un agente". Tenemos voto consensual de 3-de-5, lo que reduce falsos positivos en acciones autonomas criticas |
| **Cascade LLM con failover automatico** | Groq -> OpenRouter -> Gemini con circuit breaker. Si una API falla, otra responde sin que el operador note nada |
| **Reuso documentado** | Diagrama explicito + ahorro cuantificado, no solo mencion |
| **Dashboard publico (Ley 1712/2014)** | Transparencia institucional - cualquier estudiante puede ver el estado del sistema sin login |

---

## 5. Entregables checklist

| Reto | Entregable solicitado | Donde esta en el repo | Estado |
|------|------------------------|------------------------|--------|
| Sistemas | UML componentes | DIAGRAMAS-Y-DISEÑO.md | OK |
| Sistemas | UML estados agente | ANALISIS-Y-CAPAS-VISUALES.md secc 3 | OK |
| Sistemas | Interfaces DCU | apps/web-svelte/src/routes/agua | OK |
| Electronica | Esquema sensado + acondicionamiento | IMPLEMENTACION-TECNICA-SENSORES.md | OK |
| Electronica | Interfaz local + remota | Documentacion + firmware MicroPython | OK |
| Electronica | Arquitectura embebida 4 modulos | ANALISIS-Y-CAPAS-VISUALES.md CAPA 3 | OK |
| Electronica | Diagrama flujo firmware | DIAGRAMAS-Y-DISEÑO.md | OK |
| Industrial | Diagrama proceso | Mapa SVG + ARQUITECTURA-POR-EDIFICIO.md | OK |
| Industrial | Variables clave | water.py + endpoint /water/reading | OK |
| Industrial | 3 indicadores | 4 KPIs (IEH, TPP, CPE, ICA) | OK |
| Industrial | Mudas Lean | TESIS-VS-WATERMIND.md | OK |
| Industrial | Ishikawa | WATERMIND-OS-DOCUMENTACION.md | OK |
| Industrial | 2 acciones de mejora | 5 estrategias automatizadas en mitigation.py | OK |
| Industrial | Costo-beneficio + ROI | Tabla en TESIS-VS-WATERMIND.md | OK |

---

*v1.0 - Hackathon UNIAJC 2026 - github.com/JFrangel/WaterMind-OS*
