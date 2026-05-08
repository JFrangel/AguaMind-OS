# AQUA-ROI Lite UNIAJC — integración con AguaMind OS

> Versión piloto del proyecto, aportada por el equipo de Electrónica.
> Documento original: `AQUA-ROI_Lite_UNIAJC_documento_entregable.docx`
>
> Filosofía: **"primero medir, luego ahorrar, después escalar"** — un piloto
> de bajo costo ($5.57M COP) que reemplaza una propuesta completa de $37M
> hasta tener evidencia para justificar inversiones mayores.

---

## Resumen ejecutivo

| Item | Valor |
|------|-------|
| Inversión piloto | **$5,570,000 COP** |
| Reducción vs propuesta completa | **85.1%** ($37,376,807 → $5,570,000) |
| Ahorro anual conservador | **$4,429,751 COP/año** |
| Recuperación estimada | **1.26 años** |
| Variables centrales | Caudal · Presión · Nivel · Corriente bombas · Humedad suelo |

---

## 1. Diagnóstico y oportunidad económica

La Sede Sur depende de la PTAP abastecida por aljibes conectados al río Pance. Reto institucional: **45,367 L/día consumo total estimado · sin medición completa · riego puede superar 13,000 L/día**.

### 1.1 Brechas actuales con efecto económico

| Brecha actual | Efecto económico | Respuesta del piloto |
|---------------|-------------------|----------------------|
| Ausencia de caudalímetros suficientes | No se puede saber con precisión cuánto entra/se trata/consume/pierde | Medidor de caudal en salida PTAP/red principal y punto de riego |
| Riego de alta demanda | Picos y uso excesivo si se activa sin considerar humedad | Sensores de humedad + reglas de riego por necesidad real |
| Bombas sin histórico eléctrico | No hay medidor eléctrico ni registro continuo de horas/ciclos | Transformadores de corriente (CT clamps) + conteo de arranques |
| Fugas no localizadas | Pérdidas en red, llaves, inodoros y tuberías | Comparación caudal nocturno + presión + nivel de tanque |
| Mantenimiento correctivo | Información histórica incompleta, poca trazabilidad | Alertas, registro digital y rutas de inspección priorizadas |

### 1.2 Datos base documentales aprovechados

| Fuente | Dato aprovechado | Uso en AQUA-ROI Lite |
|--------|-------------------|------------------------|
| Reto Hackathon UNIAJC 2026 | PTAP sin medición · riego alta demanda · 45,367 L/día | Define problema y entregables obligatorios |
| Arias Montoya et al. (2024) | Sistema ahorro · costos · riego goteo · sensores · CPE 14.04 | Compara piloto vs completa, prioriza fases |
| Gómez Mina (2022) | Inventario equipos · accesorios · rutas inspección · costos | Reutilización infraestructura + mantenimiento predictivo |
| Sánchez Sotelo (2021) | Prueba nocturna desperdicio · costos agua/operario/cloro · Lean | Cálculo ahorro por detección de fugas |
| Aristizábal & Largacha (2025) | Modelo dinámica sistemas · ausencia control interno | Justifica datos históricos para decisiones |

---

## 2. Solución propuesta

AQUA-ROI Lite es un sistema **modular** de monitoreo y decisión que inicia con una **fase piloto de bajo costo**. Mide variables físicas clave, registra datos históricos y genera alertas operativas comprensibles para el personal de mantenimiento.

### 2.1 Alcance de la fase piloto

- **NO se cambia** la PTAP ni la red principal — se instrumentan puntos críticos.
- **NO se controlan bombas de potencia directamente** desde el ESP32 — se monitorea y se emiten alertas. Cualquier maniobra eléctrica con contactores, protecciones y autorización técnica.
- Software libre + equipo institucional existente — evita comprar servidor.
- Automatización de riego como **bloqueo/alerta operativa**; válvula automática es opcional.
- Crecimiento futuro: LoRa, medidores por bloque, riego por goteo completo, dosificación proporcional.

### 2.2 Arquitectura propuesta — 5 capas

| Capa | Componentes | Función |
|------|-------------|---------|
| **Sensado** | Caudal, presión, nivel, corriente bombas, humedad suelo, flotador seguridad | Captura variables físicas |
| **Procesamiento embebido** | ESP32, módulo microSD, RTC DS3231 | Valida lecturas, calcula eventos, registro local |
| **Comunicación** | Wi-Fi institucional (primera opción) · LoRa opcional si no hay cobertura | Envía datos al dashboard o gateway local |
| **Datos** | InfluxDB · PostgreSQL · CSV local | Conserva históricos para fugas y mantenimiento |
| **Interfaz** | Dashboard web · semáforo local LED + buzzer | Traduce datos técnicos en alertas comprensibles |
| _Agente Aqua-ROI_ | Reglas en Python/Node-RED | Detecta fugas, riego innecesario, anomalías de bombas |

### 2.3 Equivalencia con la arquitectura de 7 capas de AguaMind OS

AguaMind OS = AQUA-ROI Lite + Capa Física (planos UNIAJC) + Inteligencia multi-agente.

| Capa AguaMind (7) | Capa AQUA-ROI (5) | Equivalencia |
|--------------------|--------------------|---------------|
| 1 · Física | — | implícita en AQUA-ROI |
| 2 · Sensado | 1 · Sensado | 1:1 |
| 3 · Edge / Embebida | 2 · Procesamiento embebido | 1:1 (ESP32 + RTC + microSD) |
| 4 · Comunicación | 3 · Comunicación | 1:1 (Wi-Fi + LoRa opcional) |
| 5 · Persistencia | 4 · Datos | 1:1 (InfluxDB / PostgreSQL / CSV) |
| 6 · Inteligencia | Agente Aqua-ROI | 5 agentes deliberan vs 1 agente reglas |
| 7 · Aplicación | 5 · Interfaz | 1:1 (Dashboard + semáforo) |

---

## 3. BOM completo · Fase piloto $5,570,000 COP

| # | Componente | Cant. | Justificación | Costo COP |
|---|-----------|-------|----------------|-----------|
| 1 | ESP32 DevKit | 2 | Wi-Fi, bajo costo, capacidad para sensado. Uno PTAP + uno respaldo/riego | 90,000 |
| 2 | Módulo microSD + RTC DS3231 | 1 | Datos con fecha/hora cuando no hay internet | 60,000 |
| 3 | Medidor de caudal con salida pulsos para línea principal | 1 | Mide agua entregada PTAP/red, detecta caudal nocturno | 650,000 |
| 4 | Sensor/medidor de caudal para riego piloto | 1 | Cuantifica consumo riego sin medidores en todos los sectores | 120,000 |
| 5 | Transductor de presión 0-100 psi, 4-20 mA | 2 | Rango suficiente para red e hidroflo, señal robusta | 320,000 |
| 6 | Transformadores corriente + acondicionamiento | 3 | Monitoreo no invasivo bombas, sobreconsumo, ciclos | 255,000 |
| 7 | Sensor de nivel impermeable + flotador | 1+1 | Medición + respaldo simple de seguridad | 115,000 |
| 8 | Sensores capacitivos de humedad | 2 | Evitan riego si suelo ya tiene humedad | 80,000 |
| 9 | Reles optoacoplados e interruptores | 1 set | Interfaz segura para alertas, no potencia directa | 100,000 |
| 10 | Semáforo LED + buzzer | 1 | Interfaz local para operario | 180,000 |
| 11 | Fuente 24 VDC, DC/DC, fusibles, borneras | 1 set | Alimentación segura sensores y controlador | 330,000 |
| 12 | Acondicionamiento 4-20 mA a ADC | 1 set | Permite leer presión industrial en ESP32 | 120,000 |
| 13 | Gabinete IP65 | 1 | Protección humedad y polvo en PTAP | 250,000 |
| 14 | Cableado, prensaestopas, conectores, canaleta | 1 lote | Instalación ordenada y mantenible | 650,000 |
| 15 | Adaptaciones hidráulicas | 1 lote | Tee, uniones, reducciones, válvulas, accesorios | 500,000 |
| 16 | Software libre | 1 | Node-RED/Grafana/InfluxDB o CSV local | 0 |
| 17 | Instalación, pruebas, calibración, capacitación | 1 | Puesta en marcha + entrenamiento operativo | 1,200,000 |
| 18 | Contingencia técnica (12%) | — | Imprevistos menores de instalación | 550,000 |
| | **TOTAL FASE 1 PILOTO** | | | **$5,570,000** |

### 3.1 Comparación de inversiones

| Comparación | Valor | Lectura económica |
|-------------|-------|---------------------|
| Inversión propuesta completa de ahorro (Arias Montoya 2024) | $37,376,807 | Captación lluvias + medidores + mecanismos hidráulicos + goteo + sensores + mano obra |
| Inversión AQUA-ROI Lite | $5,570,000 | Piloto medición + alertas + decisión operativa |
| Diferencia | $31,806,807 | Capital aplazado hasta tener datos reales |
| Reducción | **85.1%** | Menor barrera financiera para iniciar |

### 3.2 Elementos aplazados a Fase 2

| Elemento | Decisión | Razón |
|----------|----------|-------|
| Riego por goteo completo | Aplazado | Estima 49.54% reducción pero requiere inversión mayor — Fase 1 controla con humedad |
| Cambio masivo sanitarios/lavamanos | Aplazado | Solo si datos demuestran que ese punto tiene mayor retorno |
| Captación aguas lluvias | Aplazado | Sostenible, pero no resuelve primero la falta de medición |
| Servidor dedicado | Aplazado | Se usa PC o servidor institucional existente |
| LoRa | Opcional | Solo si la prueba de Wi-Fi no es satisfactoria |

---

## 4. Reglas del Agente Aqua-ROI

| Regla | Condición | Acción |
|-------|-----------|--------|
| Fuga nocturna | caudal > umbral entre 20:00–05:00 + presión estable | Alerta amarilla: revisar baños, pilas y red principal |
| Falla de bomba | corriente alta + presión baja o tiempo recuperación alto | Alerta naranja/roja: revisar bomba, filtros, válvulas, cavitación |
| Filtro saturado | diferencial de presión creciente | Programar retrolavado por condición real |
| Riego innecesario | humedad suficiente o tanque bajo | Bloquear riego automático o avisar no regar |
| Sensor incoherente | lectura fuera de rango o sin cambio prolongado | Usar último dato válido + marcar dudoso + pedir inspección |

---

## 5. Plan a prueba de fallos

| Falla | Respuesta segura |
|-------|---------------------|
| Sin internet | Sigue midiendo localmente y guarda en microSD |
| Sin Wi-Fi humedal/captación | Mantiene registro local + evalúa LoRa opcional |
| Falla sensor de nivel | No autorizar decisiones automáticas de bombeo · usar flotador + modo manual |
| Falla sensor de presión | Conserva lectura visual de manómetros + alerta de sensor |
| Lectura incoherente | Descartar dato + último valor válido + avisar revisión |
| Bloqueo del microcontrolador | Watchdog reinicia el sistema |
| Mantenimiento de PTAP | Modo manual físico con registro de evento |

---

## 6. Indicadores propuestos

| Indicador | Fórmula | Propósito |
|-----------|---------|-----------|
| Índice de pérdidas hidráulicas (IPH) | `((Q_producida − Q_consumida) / Q_producida) × 100` | Detectar fugas y priorizar reparaciones |
| Eficiencia energética | `kWh / m³ bombeado` | Comparar rendimiento bombas y anticipar fallas |
| Consumo nocturno mínimo | `L/min entre horas baja actividad` | Evidenciar fugas ocultas |
| Ahorro de riego | `((L_base − L_actual) / L_base) × 100` | Validar efecto humedad y horario |
| Disponibilidad de PTAP | `(Horas disponible / Horas programadas) × 100` | Medir continuidad del servicio |
| Retorno de inversión | `Inversión / Ahorro_anual` | Defender viabilidad financiera |

---

## 7. Análisis costo-beneficio · 3 escenarios

### 7.1 Fuentes de ahorro (escenario conservador)

| Fuente | Ahorro anual | Supuesto |
|--------|--------------|----------|
| Recuperación fugas y pérdidas | $2,129,751 | 70% costos tangibles: agua + operario + cloro desperdiciado |
| Riego inteligente fase 1 | $900,000 | Reducción conservadora por humedad/horario |
| Alertas mantenimiento/bombas | $1,100,000 | Evita parte de correctivos · diferencias preventivo vs correctivo |
| Menos recorridos · mejor registro | $300,000 | Menos inspecciones manuales no priorizadas |
| **Total ahorro conservador** | **$4,429,751** | |

### 7.2 3 escenarios

| Escenario | Ahorro anual | Recuperación |
|-----------|--------------|---------------|
| Conservador | $4,429,751 | 1.26 años |
| Medio | $5,200,000 | 1.07 años |
| Prudente sin mantenimiento | $3,030,000 | 1.84 años |

---

## 8. Plan de implementación · 10 semanas

| Tiempo | Actividad | Resultado |
|--------|-----------|-----------|
| Sem 1 | Levantamiento final | Verificar diámetros, ubicación tablero, Wi-Fi, puntos corte, seguridad eléctrica |
| Sem 2 | Compra y banco de pruebas | Probar sensores, acondicionamiento, almacenamiento, dashboard en mesa |
| Sem 3 | Instalación piloto | Montaje gabinete, caudalímetro, presión, corriente, nivel, humedad |
| Sem 4 | Calibración | Comparar lecturas con manómetros, medición manual de tanque, observaciones operario |
| Sem 5–8 | Línea base | Recolectar datos consumo normal, riego, horario nocturno, ciclos bombas |
| Sem 9 | Ajuste de reglas | Definir umbrales reales de fuga, corriente, presión, riego |
| Sem 10 | Entrega | Dashboard, informe ahorros, plan escalamiento, capacitación |

---

## 9. Roles del equipo

| Rol | Responsabilidad |
|-----|------------------|
| Equipo Electrónica | Sensores, acondicionamiento, alimentación, montaje en gabinete |
| Equipo Sistemas | Dashboard, base de datos, agente de software, seguridad de acceso |
| Equipo Industrial | Indicadores, Lean, costo-beneficio, rutas de inspección, estandarización |
| Mantenimiento UNIAJC | Validación operativa, permisos, seguridad, ubicación equipos, uso final |

---

## 10. Matriz de cumplimiento de la rúbrica

| Criterio | Peso | Cómo lo cumple AQUA-ROI Lite (+ AguaMind) | Meta |
|----------|------|--------------------------------------------|------|
| Viabilidad técnica | 30% | Sensores accesibles + PTAP existente + software libre + modo manual | Excelente |
| Aplicación industrial | 30% | Entradas, procesos, usos, variables, indicadores, mudas, Ishikawa, mejoras, costo-beneficio | Excelente |
| Actividad inventiva | 20% | Cruza caudal + presión + nivel + corriente + humedad + horarios para decisiones autónomas | Excelente |
| Impacto | 20% | Reduce pérdidas, protege acuífero, mejora mantenimiento, hace visibles datos a la comunidad | Excelente |

---

## 11. Cómo se integra en AguaMind OS

AQUA-ROI Lite no es un proyecto separado — es la **versión piloto realista** del proyecto integrado. AguaMind OS es la plataforma que recibe los datos del piloto AQUA-ROI Lite. El backend de AguaMind:

- **Acepta los 2 sensores nuevos** que AQUA-ROI introduce (corriente SCT-013-030, humedad capacitiva) vía el normalizador universal de sensores en `services/api/app/sensors/registry.py`.
- **Calcula los 2 KPIs nuevos** (kWh/m³ y disponibilidad PTAP) en `_calc_kpis()` de `water.py`.
- **Expone los 3 escenarios costo-beneficio** vía `GET /water/industrial/scenarios`.
- **Expone las 6 mudas, 6M Ishikawa y 5 reglas del agente** vía `GET /water/industrial/lean`.
- **Visualiza todo** en la pestaña Industrial del dashboard SvelteKit.

---

## 12. Pitch de 60 segundos (anexo del documento original)

> *"AQUA-ROI Lite convierte la PTAP de la UNIAJC Sede Sur en un sistema medible y financieramente sostenible. En lugar de invertir más de 37 millones en una renovación completa, proponemos un piloto de 5.57 millones que mide caudal, presión, nivel, corriente de bombas y humedad del suelo. Con esos datos el sistema detecta fugas nocturnas, evita riego innecesario, anticipa fallas de bombas y genera alertas fáciles de entender para mantenimiento. La inversión se recupera aproximadamente en 1.26 años y deja una base de datos real para decidir futuras mejoras. Primero medimos, luego ahorramos y después escalamos con evidencia."*

---

*v1.0 · 8 de mayo de 2026 · entregado por equipo Electrónica · integrado a AguaMind OS por equipo Sistemas*
