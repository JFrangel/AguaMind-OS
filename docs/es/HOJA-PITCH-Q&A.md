# WaterMind OS - Hoja de pitch · Q&A anticipado

> Hoja para llevar al pitch. Cada pregunta tiene:
> - **Respuesta corta** (15-25s) para decir en voz alta
> - **Datos de respaldo** (números concretos)
> - **Demo opcional** (qué mostrar en el dashboard si el jurado pide ver)
>
> Hackathon UNIAJC 2026 · 8 de mayo · v1.0

---

## P1 · "¿Por qué no usaron un SCADA tradicional?"

**Respuesta corta:**
> *"Un SCADA cuesta $50M+ COP, es cerrado, no aprende, no cumple normativa por sí solo y no involucra a la comunidad. WaterMind OS cuesta $1.4M COP, es open source, multi-agente y replicable a cualquier universidad pública."*

**Datos de respaldo:**
- SCADA Wonderware/Ignition: $50-150M COP licencia + integradores
- WaterMind OS Fase 1: $1,431,000 COP hardware (BOM detallado en master doc §14)
- Open source MIT en `github.com/JFrangel/WaterMind-OS`
- Multi-agente con 5 agentes coordinados (no un solo controlador)

**Demo:** Mostrar la pestaña Inteligencia → panel "Razonamiento en vivo" con los 5 agentes deliberando.

---

## P2 · "¿Qué pasa si el agente toma una decisión incorrecta?"

**Respuesta corta:**
> *"Triple salvaguarda. Primero, los 5 agentes votan y necesitan 3 de 5 para actuar. Segundo, hay alerta humana en menos de 30 segundos por Telegram + dashboard. Tercero, en Fase 1 piloto requerimos confirmación humana antes de cualquier acción crítica. Y todo queda con audit trail rastreable."*

**Datos de respaldo:**
- Voto consensual implementado en `services/api/app/routers/mitigation.py`
- Cada acción genera un OT con UUID rastreable + timestamp
- Tabla `mitigation_actions` registra: trigger, severity, voto por agente, acciones tomadas, impacto

**Demo:** Pestaña Inteligencia → panel "voto consensual · 4 de 5 ≥ critical" con barra de consenso.

---

## P3 · "¿Cómo aseguran la calidad de los datos?"

**Respuesta corta:**
> *"Cuatro líneas de defensa. SensorAgent valida cada lectura contra rangos físicos imposibles. Calibración pre-instalación con protocolos documentados (cubeta 20L para caudal, manómetro patrón para presión, soluciones Formazin para turbidez). Calibración trimestral programada. Y ADS1115 16-bit para alcanzar la precisión que la Resolución 2115/2007 exige."*

**Datos de respaldo:**
- Registry de sensores con calibración: [services/api/app/sensors/registry.py](../../services/api/app/sensors/registry.py)
- Quality flags: `ok | suspect | out_of_range | invalid` por cada lectura
- ADS1115 con gain=1: 0.125 mV de resolución → 0.05 NTU equivalente

**Demo:** `curl /water/ingest/universal` con valor fuera de rango → ver `quality: "out_of_range"`.

---

## P4 · "¿Y si los estudiantes que crearon esto se gradúan?"

**Respuesta corta:**
> *"El código está en GitHub público con licencia MIT. La documentación está en español, son 30+ documentos versionados. El Semillero SEGESTOP de UNIAJC puede continuar el desarrollo. La universidad gradúa más de 50 ingenieros al año que pueden mantenerlo. Y como WaterMind OS está construido sobre AgentOS — un framework reutilizable — el conocimiento se preserva más allá de un equipo."*

**Datos de respaldo:**
- Repo: `github.com/JFrangel/WaterMind-OS`
- 31 archivos `.md` en `docs/es/`
- Stack documentado: SvelteKit, FastAPI, ESP32, MicroPython — tecnologías estándar
- Roles definidos en master doc §18 para handoff a próximos equipos

---

## P5 · "¿Qué hacen los próximos 6 meses después del hackathon?"

**Respuesta corta:**
> *"Plan por fases con costos. Mes 1: instalar el primer nodo IoT en la PTAP — $1.43M. Meses 2-3: extender al Bloque A y la cancha de fútbol — $5.4M acumulado. Meses 4-6: sensores PTAR + reporte automático CVC — $9.2M acumulado. Mes 7 en adelante: replicación a Sede Norte y Centro de UNIAJC."*

**Datos de respaldo:**
- Plan completo de 10 fases en master doc §13
- Cronograma con inversión y beneficio anual proyectado por fase
- Fase 2 (5 nodos): proyección $11.6M ahorro anual + protección legal

---

## P6 · "¿Cómo verifican conectividad WiFi en cada punto?"

**Respuesta corta:**
> *"Visita técnica pre-instalación con InSSIDer para medir RSSI en cada punto candidato. Si está bajo -75 dBm, instalamos repetidor. Plan B: módem 4G dedicado de $45K mensuales por nodo crítico. Plan C: LoRa entre nodos para comunicación local sin internet. Triple redundancia."*

**Datos de respaldo:**
- Protocolo de validación documentado en master doc §6.4
- 6 puntos candidatos identificados: PTAP, Bloque A, Alameda, Cancha, Cafetería, Labs
- Costo de contingencia 4G: ~$540K/año por nodo crítico

---

## P7 · "¿Qué pasa si se cae internet?"

**Respuesta corta:**
> *"El sistema sigue operando. El ESP32 tiene memoria NVS flash que almacena hasta 1,000 lecturas (8 horas de datos a 30 segundos). Cuando vuelve la conexión, reenvía todo el buffer. Y mientras tanto, el operador local ve el estado en el OLED de cada nodo: caudales, presión, niveles, alertas — sin internet, sin dashboard, sin nube. La planta no se detiene."*

**Datos de respaldo:**
- NVS flash 4 MB en ESP32-WROOM-32
- Capacidad: 1,000 lecturas × ~250 bytes = ~8h de respaldo
- OLED 0.96" + LED RGB + buzzer como interfaz local
- Máquina de estados del firmware visible en pestaña Arquitectura

**Demo:** Mostrar la máquina de estados FSM en pestaña Arquitectura (BOOT → WIFI_CONNECT → READY → HTTP_FALLBACK → NVS_BUFFER).

---

## P8 · "Pueden haber soluciones costo-beneficio más económicas" *(comentario directo del jurado del 7 de mayo)*

**Respuesta corta:**
> *"Totalmente de acuerdo, y de hecho UNIAJC ya tiene un método de costo cero que respetamos: dejan los tanques llenos al final del día, abren la escotilla superior en la mañana, y leen las marcas grabadas en la pared del tanque. La diferencia entre la marca de las 6 PM y la de las 7 AM es la pérdida nocturna. Eso ya funciona. WaterMind OS no lo reemplaza — lo digitaliza y lo cruza con los sensores. Si la medición visual y el sensor JSN-SR04T no coinciden, hay un problema (sensor descalibrado, marca borrada, fuga nueva). Triangulación de datos = más confianza, no menos."*

**Detalle del método actual de UNIAJC (costo cero):**

| Paso | Acción | Hora |
|------|--------|------|
| 1 | El operario llena los tanques A (36k L) y B (16k L) al cierre | ~5:30 PM |
| 2 | Anota en la bitácora la **marca de nivel** visible en la pared del tanque | ~6:00 PM |
| 3 | Cierra escotilla superior | — |
| 4 | A la mañana siguiente abre la escotilla y lee la nueva marca | ~7:00 AM |
| 5 | **Diferencia (cm) × área del tanque** = pérdida nocturna en litros | inmediato |
| 6 | Anota la pérdida en la bitácora — sirve para detectar fugas anormales | continuo |

**Por qué WaterMind OS lo complementa, no lo reemplaza:**

| Métrica | Método actual UNIAJC | WaterMind OS | Resultado al combinar |
|---------|----------------------|-------------|------------------------|
| Costo | $0 (escotilla + marcas + bitácora) | $30K por sensor JSN-SR04T | $0 mantiene + sensor agrega |
| Frecuencia | 1 lectura cada 12 horas | 1 cada 30 segundos | Detección 1,440 veces más rápida |
| Operación | Requiere operario presente | Automático 24/7 | Operario sigue, agente cubre noches/festivos |
| Granularidad | Promedio nocturno | Hora-a-hora con desviación | Identifica EL HORARIO exacto de la fuga |
| Validación cruzada | — | — | Si difieren > 5%, alerta de calibración |

**Datos de respaldo:**
- Tesis **Sánchez Sotelo 2021** usó este método para medir 960 L en 13 horas nocturnas → 66.15 L/h → 1,587 L/día
- Equivalencia documentada: **1 cm de altura del tanque = 160 L**
- Los tanques de UNIAJC son verticales con escotilla superior (visita técnica · plano hidráulico Gómez Mina 2022)
- El sensor JSN-SR04T mide la misma magnitud (nivel cm) con la misma equivalencia → comparación directa

**Mensaje a transmitir:**
> *"Escuchamos al jurado del 7 de mayo. La propuesta es híbrida y respetuosa: el método actual sigue, WaterMind OS lo digitaliza y lo cruza. Si la marca del operario y el sensor no coinciden, sabemos que algo cambió. Es un piso de bajo costo cubierto por dos métodos independientes."*

**Demo opcional:** mostrar la pestaña Operación → niveles de tanques A 73% y B 78% en vivo, y explicar: *"esto es lo que el operario ve cada mañana al abrir la escotilla, pero ahora con datos cada 30 segundos para detectar fugas durante el día también."*

---

## Apertura textual del pitch (memorizar)

> *"Antes de empezar, una pregunta para el jurado: ¿cuántos litros de agua perdió esta universidad mientras yo decía estas palabras? La respuesta es 9 litros. Y nadie en UNIAJC se ha enterado todavía. Cada minuto, en silencio, esta planta del 2011 deja escapar agua que nadie mide. Lleva 13 años haciéndolo."*

## Cierre textual del pitch (memorizar)

> *"WaterMind OS no es un proyecto. Es la culminación de 5 años de investigación en UNIAJC sobre la PTAP, llevada a operación. Caycedo y Jaramillo caracterizaron en 2021. Sánchez Sotelo midió las pérdidas en 2021. Gómez Mina diseñó mantenimiento en 2022. Aristizábal y Largacha modelaron en 2025. Cuatro tesis. Cuatro diagnósticos. Cero soluciones implementadas. WaterMind OS las toma todas y las pone en operación. Hoy."*

---

## Cronómetro del pitch (5 minutos exactos)

| Tiempo | Sección | Mensaje clave | Demo |
|--------|---------|---------------|------|
| 0:00–0:30 | Apertura | "9 litros perdidos mientras hablo" | — |
| 0:30–1:15 | Problema | UNIAJC pierde 1,587 L/día medidos · agua fuera de norma · sanción $16,900M | tab Operación |
| 1:15–2:30 | Solución | Modelo 3D + 5 agentes deliberando + cierre EV automático | tab Inteligencia + Mapa 3D |
| 2:30–3:30 | Diferenciadores | Estrategias derivadas de datos · 5 fenómenos cubiertos | tab Inteligencia (5 cards) |
| 3:30–4:15 | Impacto | $1.4M inversión · 25 días ROI · 5 ODS · 16.5M L recuperados | panel monetización en vivo |
| 4:15–4:45 | Validación académica | 4 tesis UNIAJC integradas | tab Arquitectura · trinidad analítica |
| 4:45–5:00 | Cierre | "4 tesis · 4 diagnósticos · 0 soluciones implementadas · WaterMind OS las pone en operación · hoy" | — |

---

## Lista de cosas a tener en la mesa el día del pitch

- [ ] Laptop con backend `:8000` corriendo (verificar `curl http://localhost:8000/water/agent/status`)
- [ ] Laptop con frontend `:5173` corriendo (verificar `curl http://localhost:5173/agua`)
- [ ] Conexión a internet estable (para el LLM si configuramos GROQ_API_KEY real)
- [ ] BOM impreso ([master doc §14.1](WATERMIND-OS-MASTER.md))
- [ ] Esta hoja Q&A impresa
- [ ] Cable HDMI/USB-C para proyector
- [ ] Adaptador VGA por si acaso
- [ ] Backup del repo en USB (por si falla internet)
- [ ] Cronómetro / timer en el celular para los 5 minutos
- [ ] Botella de agua (irónicamente importante)

---

*v1.0 · 2026-05-08 · Pitch UNIAJC Hackathon*
