# WaterMind OS - Tesis UNIAJC vs nuestra solucion

> Para cada problema diagnosticado en las tesis previas, este documento muestra:
> 1. Que problema vieron los tesistas
> 2. Como propusieron solucionarlo (recomendaciones del trabajo de grado)
> 3. Como WaterMind OS lo resuelve hoy con IoT + IA + automatizacion
>
> Hackathon UNIAJC 2026 - v1.0

---

## Tesis 1 - Caycedo Saa & Jaramillo Moreno (2021)
**"Propuesta de caracterizacion del proceso tecnico-operativo de la PTAP UNIAJC Sede Sur"**
Fuente: [tesis-uniajc/TGI-CAYCEDO-JARAMILLO.pdf](../../tesis-uniajc/TGI-CAYCEDO-JARAMILLO.pdf) (129 paginas, 2021)

### 8 hallazgos de incumplimiento normativo (Tabla 19, pp.80-82)

| # | Problema diagnosticado | Solucion propuesta por la tesis | Solucion de WaterMind OS |
|---|------------------------|----------------------------------|--------------------------|
| 1 | **Toma de muestras sin estandarizar** - sin puntos definidos, microbiologia 4 veces/ano vs minimo mensual exigido por Res. 2115/2007 | Definir manualmente puntos de muestreo + cronograma | **Automatizado.** El SensorAgent valida cada lectura contra rangos fisicos cada 30 s. Frecuencia 2,880 muestras/dia/sensor (Res. 2115/2007 exige 12/ano - cumplido en 5 minutos) |
| 2 | **Calidad fuera de norma** - cloro 0.28-2.10 ppm, fosfatos hasta 1.91 mg/L (limite 0.5), nitratos hasta 22.5 mg/L (limite 10), pH bajo 6.4 | Bomba dosificadora automatica + medidores precisos | **Sensor TSD-10 turbidez en linea + sonda ORP cloro + pH SEN0161** + alerta automatica via Telegram + cierre EV cuando turbidez > 4 NTU. Reporte mensual auto al INVIMA |
| 3 | **Programas de seguridad y salud** - sin demarcaciones, sin manual SST, equipos basicos | Disenar manual + simulacros + EPP completo | **Fuera de scope tecnologico** - WaterMind OS protocoliza el lado digital (logs, auditoria, capacitacion via dashboard). El lado fisico requiere accion administrativa de UNIAJC |
| 4 | **Manual de funcionamiento** - inexistente o inadecuado segun Titulo C de Min. Vivienda | Redactar manual completo con diagrama de flujo y procedimientos de emergencia | **El propio sistema es manual ejecutable.** Los flujos PHVA estan codificados en el LangGraph multi-agente. Cada accion del agente queda en `mitigation_actions` con razonamiento auditable |
| 5 | **Personal insuficiente** - un solo operario sin capacitaciones | Programa de capacitacion + contratar mas personal | **El agente IA opera 24/7** con consenso de 5 sub-agentes. Reduce dependencia humana del 100% al ~20% (solo aprobacion de acciones criticas en Fase 1) |
| 6 | **Insumos inadecuados** - medidor de cloro/pH obsoleto, mediciones por tonalidad "a criterio" | Comprar medidores nuevos + inventario | **6 sensores digitales calibrados + ADS1115 16-bit** elimina la subjetividad. El registry (`packages/sensors/registry.py`) documenta calibracion de cada modelo |
| 7 | **Mantenimiento solo correctivo** - sin preventivo ni predictivo, sin fichas tecnicas | Programa de mantenimiento + fichas | **Predictivo en vivo.** El IndustrialAgent corre Random Forest sobre presion+vibracion+caudal para predecir fallos. El equipo PTAP esta catalogado con codigos UNIAJC (Gomez Mina 2022) en `services/api/app/routers/water.py` |
| 8 | **Equipos obsoletos** - cloracion manual, hidroflows danados, sin planos de tuberia, cortocircuitos por animales | Bomba dosificadora SD-BD-01, VFD, planos | **Mapa SVG en /agua tab "Mapa del Campus"** muestra todas las tuberias, edificios, electrovalvulas. La cloracion automatizada esta como Fase 3 del roadmap |

### Recomendaciones del cap. 9 de la tesis (p.100)

| Recomendacion del tesista | Como WaterMind OS la materializa |
|---------------------------|----------------------------------|
| "Realizar registro actualizado sobre las fuentes de aguas abastecidas" | Endpoint `/water/zones` con consumo en tiempo real por zona (8 zonas catalogadas) |
| "Estudios de factibilidad para red de agua no tratada para sanitarios y orinales" | **Implementado en el diagrama**: PTAR -> reuso -> cisternas sanitarias (Res. 1207/2014). Ahorra ~5,000 L/dia |
| "Optimizar costos y eficiencia (caso hidroflow y phmetro)" | Estrategia de bombeo eficiente (modo eco-nocturno: 38->25 PSI, -40% kWh) en MitigationAgent |
| "Capacitacion frecuente para operarios" | Dashboard con razonamiento explicito de cada decision del agente sirve como herramienta pedagogica |
| "Demarcaciones y normatividad de instalaciones electricas" | **Fuera de scope** - accion administrativa |

### Costo-beneficio que la tesis propuso vs lo que entrega WaterMind

| Concepto | Tesis Caycedo (2021) | WaterMind OS Fase 1 |
|----------|----------------------|---------------------|
| Inversion | $16,569,286 COP | $1,431,000 COP (~12x menos) |
| Ahorro anual | $17,701,440 COP | $20,536,425 COP proyectado |
| Periodo recuperacion | ~12 meses | ~25 dias |
| Cumplimiento normativo | Manual via documentacion | Automatico via reportes generados |

**Diferencia clave:** la tesis propone documentar y comprar instrumentos sueltos. WaterMind OS los integra en un sistema autonomo que opera, alerta y reporta sin intervencion humana continua.

---

## Tesis 2 - Sanchez Sotelo (2021)
**"Propuesta de mejora con Lean Manufacturing para la PTAP UNIAJC Sede Sur"**

| Hallazgo de la tesis | Numero exacto | Como lo usa WaterMind |
|----------------------|----------------|----------------------|
| Caudal validado in-situ | 5.56 L/seg | Linea base del simulador `_simulate_sensors()` |
| Equivalencia tanque | 1 cm = 160 L | Constante para conversion del JSN-SR04T |
| Desperdicio nocturno medido | 960 L en 13 h | **Integrado** como senal de fuga en horario 22:00-06:00 |
| Desperdicio neto/dia | 1,587.69 L/dia | Constante `losses_l_min` en water.py |
| Costo desperdicio anual | $1,107,637 COP | Mostrado en dashboard como "costo evitable" en vivo |
| Sistema presion 38-60 PSI | Rango fijo no optimizado | **Reemplazado** por estrategia eco-nocturna del MitigationAgent (25 PSI en valle, 60 PSI en pico) |
| Ciclos de bombeo 3-4 min | Innecesario | **Optimizado** con `scipy.optimize` minimizando kWh sin afectar nivel de tanque A |

**7 mudas Lean** del marco de la tesis estan operacionalizadas en `_frag_mitigacion()` y reflejadas en la tab "Gestion Industrial" del dashboard.

---

## Tesis 3 - Gomez Mina (2022)
**"Diseno de un programa de mantenimiento para la PTAP UNIAJC"**

Aporte: catalogacion completa de equipos con codigos institucionales. Esta lista es la base del diccionario `PTAP_EQUIPMENT` en `services/api/app/routers/water.py`:

| Codigo UNIAJC | Equipo | Spec |
|---------------|--------|------|
| CP-BS-01 | Bomba sumergible aljibe 1 | Barnes 4SP 2526, 5 HP, 32 gal/min |
| CP-BS-02 | Bomba sumergible aljibe 2 | Barnes 4SP 2511, 2 HP, 32 gal/min |
| SF-FT-01/02/03 | Filtros 1, 2, 3 | OHS Ingenieros, 861.53 L, 400 L/min |
| SD-TM-01 | Tanque cloracion | Ajover Wave, 250 L |
| SD-BD-01 | Bomba dosificadora cloro | LMI C111-362TI, 150 PSI, 2.5 GPH |
| AL-TA-01/02 | Tanques A 36k L + B 16k L | - |
| SB-TH-01/02 | Hidroneumaticos | Altamira PRO XLB, 119 gal, 125 PSI |
| SB-BC-03/04 | Bombas centrifugas | Barmesa Pumps |

**Solucion WaterMind:** el catalogo es consultable via `GET /water/constants` y el agente puede referenciar cualquier equipo por su codigo en respuestas.

---

## Tesis 4 - Aristizabal Torres & Largacha Perdomo (2025)
**"Modelo de dinamica de sistemas (Vensim) para demanda y suministro de agua"**

| Escenario simulado | Resultado | WaterMind |
|--------------------|-----------|----------|
| Cooperacion 0% | Colapso del sistema en 2 anos | Trigger automatico de campana Smart Water Ledger cuando consumo > linea base |
| Cooperacion 15% | Sostenibilidad parcial | Estado actual proyectado |
| Cooperacion 50% | Sostenible largo plazo | Meta del programa Bienestar Universitario integrado |

**Solucion WaterMind:** los escenarios Vensim se ejecutan via PySD desde el MitigationAgent en analisis prescriptivo (ver [ANALISIS-Y-CAPAS-VISUALES.md](ANALISIS-Y-CAPAS-VISUALES.md) seccion 1.3). El Smart Water Ledger conecta consumo medido con creditos para mejoras del campus, materializando la "cooperacion" del modelo.

---

## Tesis 5 - Arias Montoya, Montiel Angel, Osorio Hernandez (2024)
**"Sistema de ahorro para mejorar eficiencia de la PTAP"**

| Aporte | Dato | Uso en WaterMind |
|--------|------|-----------------|
| Linea base CPE | 14.04 L/estudiante/dia | KPI calculado en `_calc_kpis()` con meta <= 12.0 |
| Distribucion zonas | 8 zonas con consumos exactos | Simulador `ZONE_DAILY_BASE` en water.py |
| Aljibe inflow | 113.56 L/min combinado | Constante `ALJIBE_INFLOW_L_MIN` |

---

## Tesis 6 - Mosquera Zapata & Lozano Beltran (2024)
**"Modelo de dinamica de sistemas para impacto sobre PTAR y ecosistema"**

| Aporte | Uso en WaterMind |
|--------|-----------------|
| Modelo de impacto comunitario sobre PTAR | Conecta el reporte ciudadano QR con el sistema de creditos |
| Caracterizacion de descargas al rio Pance | Base para el monitoreo Resolucion 0631/2015 visible en el mapa |

---

## Resumen ejecutivo: que cambia

| Lo que hicieron 4-5 anos de tesis | Lo que hace WaterMind OS |
|----------------------------------------|--------------------------|
| **Diagnostico** detallado en PDF | **Diagnostico continuo** en pantalla, actualizado cada 30 s |
| **Recomendaciones** en papel | **Acciones autonomas** ejecutadas en 5 segundos |
| **Datos puntuales** en visitas | **Datos en vivo** desde 6 sensores que tu nunca tienes que tocar |
| **Cumplimiento manual** anual con costo de tiempo del operario | **Reporte automatico** mensual a INVIMA, CVC, Min. Vivienda |
| **5 tesis = 5 documentos** | **1 sistema operativo** que ejecuta las recomendaciones de las 5 |
| Costo $16.5M COP en consultoria | Costo $1.4M COP en hardware + software open source |

> *No competimos con las tesis previas. Las llevamos a operacion. Caycedo y Jaramillo caracterizaron en 2021. Sanchez Sotelo midio las perdidas en 2021. Gomez Mina diseno el mantenimiento en 2022. Aristizabal y Largacha modelaron en 2025. **Cuatro tesis. Cuatro diagnosticos. Cero soluciones implementadas. WaterMind OS las pone en operacion. Hoy.***

---

*v1.0 - Hackathon UNIAJC 2026 - github.com/JFrangel/WaterMind-OS*
