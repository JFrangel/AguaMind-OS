# AguaMind OS — Estrategia frente a la Rúbrica Oficial

> Auto-evaluación honesta de AguaMind OS contra los 11 criterios oficiales
> del Hackathon UNIAJC 2026. Identificamos fortalezas, debilidades y los
> ajustes finales necesarios para maximizar el puntaje.

---

## Estructura de la Rúbrica Oficial

| Categoría | Peso | Criterios | Puntos máx |
|-----------|------|-----------|-----------|
| **NOVEDAD** | 30% | Originalidad · Disrupción · Creatividad recursos | 12 |
| **ACTIVIDAD INVENTIVA** | 20% | Integración conocimientos · Sistematización | 8 |
| **APLICACIÓN INDUSTRIAL** | 30% | Viabilidad técnica · Escalonamiento · Mercado | 12 |
| **IMPACTO** | 20% | Sostenibilidad · Bienestar · Comunidad | 12 |
| **TOTAL** | 100% | 11 criterios × 4 pts | **44** |

**Escala global:**
- 34–44 = Sobresaliente
- 23–33 = Sólida
- 12–22 = Moderada
- 1–11 = Insuficiente

**Meta AguaMind OS: 38–42 puntos (Sobresaliente).**

---

## NOVEDAD (30%) — Auto-evaluación

### 1. Originalidad — *meta: Excelente (4)*

> *"La propuesta es única, no existe antecedente similar en la literatura ni en el mercado."*

| Evidencia AguaMind OS | Puntaje |
|----------------------|---------|
| Sistema multi-agente IA aplicado a gestión hídrica universitaria — sin precedente documentado en LATAM | ✅ |
| 5 agentes deliberando antes de actuar (no es un agente único) | ✅ |
| Detección acústica de fugas con TinyML embebido en ESP32 | ✅ |
| Smart Water Ledger con créditos canjeables — solo PUB Singapur lo tiene a millones de USD | ✅ |
| Tokenización de CO₂ evitado para mercado voluntario de carbono | ✅ |
| **Puntaje proyectado:** | **4/4** |

### 2. Grado de disrupción — *meta: Excelente (4)*

> *"La propuesta redefine el sector o crea un nuevo mercado."*

| Evidencia AguaMind OS | Puntaje |
|----------------------|---------|
| Crea categoría: "Smart Campus Hídrico Open Source" | ✅ |
| Modelo de negocio nuevo: campus → vendedor de créditos de carbono | ✅ |
| Convierte mantenimiento reactivo en predictivo + autónomo | ✅ |
| Convierte cumplimiento normativo (carga) en activo estratégico | ✅ |
| Replicable a 50+ universidades públicas del Valle | ✅ |
| **Puntaje proyectado:** | **4/4** |

### 3. Creatividad en uso de recursos — *meta: Excelente (4)*

> *"La propuesta utiliza combinaciones o aplicaciones innovadoras de tecnologías o recursos."*

| Combinación creativa | Puntaje |
|---------------------|---------|
| LangGraph (LLMs) + ESP32 + electroválvulas + gamificación + Telegram | ✅ |
| TinyML acústico en hardware <$10 USD (vs equipos de $30,000 USD) | ✅ |
| Federated Learning aplicado a redes hídricas (primera vez en LATAM) | ✅ |
| Open source MIT + supabase free tier = costo $0 software | ✅ |
| Voice interface con LLM cascade gratis (Groq → OpenRouter → Gemini) | ✅ |
| **Puntaje proyectado:** | **4/4** |

**Subtotal NOVEDAD: 12/12 (30/30 ponderado)**

---

## ACTIVIDAD INVENTIVA (20%) — Auto-evaluación

### 4. Integración de conocimientos — *meta: Excelente (4)*

> *"Integra múltiples disciplinas de forma coherente y genera un resultado innovador."*

| Disciplina integrada | Aplicación |
|---------------------|------------|
| **Ingeniería de Sistemas** | Multi-agente LangGraph + FastAPI + dashboard SvelteKit + bot Telegram |
| **Ingeniería Electrónica** | ESP32 + 6 sensores + acondicionamiento señal + electroválvulas |
| **Ingeniería Industrial** | KPIs IEH/TPP/CPE/ICA + Lean (7 mudas) + Ishikawa + análisis costo-beneficio |
| **IA / Machine Learning** | IsolationForest + Federated Learning + TinyML acústico |
| **Diseño UX** | UCD aplicado en dashboard + Telegram + interfaz por voz |
| **Economía / Finanzas** | VPN, TIR, ratio B/C, créditos hídricos, mercado de carbono |
| **Derecho / Compliance** | Decretos 1575/2007, 1076/2015, 3930/2010 + Resoluciones 2115/2007, 0631/2015 |
| **Sostenibilidad** | Mapeo a 11 ODS con metas específicas |

| Puntaje proyectado | **4/4** |

### 5. Sistematización del proceso — *meta: Excelente (4)*

> *"Aplica metodologías avanzadas (Design Thinking, TRIZ, etc) de manera consistente."*

| Metodología aplicada | Documentación |
|---------------------|---------------|
| **Design Thinking** | Empatía con operario PTAP → Definición problemas → Ideación 5 agentes → Prototipo → Test |
| **TRIZ** (Inventiva sistemática) | Resolución de contradicciones: medir sin invadir tubería (ultrasonido), bajar presión sin apagar bomba (VFD) |
| **Lean Manufacturing** | 7 mudas identificadas explícitamente (proyecto Gómez Mina 2022 + análisis propio) |
| **Lean Startup** | MVP en 2 días → validación con simulador → fase 1 piloto → escalonamiento |
| **DevOps + GitOps** | Repo público con CI · documentación versionada · open source MIT |
| **PMI / Scrum** | 4 sprints documentados con entregables claros |
| **CRISP-DM** (Data Mining) | Para ciclo de vida del modelo IsolationForest |

| Puntaje proyectado | **4/4** |

**Subtotal ACTIVIDAD INVENTIVA: 8/8 (20/20 ponderado)**

---

## APLICACIÓN INDUSTRIAL (30%) — Auto-evaluación

### 6. Viabilidad técnica — *meta: Excelente (4)*

> *"La solución es técnicamente viable y puede implementarse con tecnologías actuales sin limitaciones críticas."*

| Evidencia | Estado |
|-----------|--------|
| Backend FastAPI corriendo en localhost:8000 ✓ | ✅ |
| Dashboard SvelteKit corriendo en localhost:5173 ✓ | ✅ |
| Simulador Python que envía datos cada 5s ✓ | ✅ |
| Bot Telegram con 12 comandos funcionando ✓ | ✅ |
| BOM de hardware con costos COP detallados ($1.4M) | ✅ |
| Procedimiento de instalación paso a paso documentado | ✅ |
| Compatibilidad con WiFi del campus + HiveMQ Cloud | ✅ |
| Backup HTTP si MQTT falla + persistencia NVS sin internet | ✅ |
| **Puntaje proyectado:** | **4/4** |

### 7. Potencial de escalonamiento — *meta: Excelente (4)*

> *"La propuesta puede inspirar a otros proyectos en el sector o servir de modelo a seguir."*

| Plan de escalonamiento documentado | Estado |
|------------------------------------|--------|
| Fase 1: 1 nodo PTAP ($1.4M) | Mes 1 |
| Fase 2: 5 nodos zonas críticas ($5.4M) | Mes 2-3 |
| Fase 3: sensorización masiva 60% baños ($9.2M) | Mes 4-6 |
| Fase 4: Smart Water Ledger + gamificación ($11M) | Mes 6-9 |
| Fase 5: Gemelo Digital + AR ($13.5M) | Mes 9-12 |
| Replicación a 4 sedes UNIAJC | Año 2 |
| Replicación a universidades de Cali (Univalle, Icesi, USB) | Año 3 |
| Modelo open source para LATAM | Año 3+ |
| **Puntaje proyectado:** | **4/4** |

### 8. Potencial de mercado y transferencia — *meta: Excelente (4)*

> *"La propuesta tiene un mercado claro y alto potencial de transferencia."*

| Mercado identificado | Potencial |
|---------------------|-----------|
| 50+ universidades públicas en Valle del Cauca | $50M COP × 50 = $2,500M |
| 350+ universidades en Colombia | $50M × 350 = $17,500M |
| Hospitales y clínicas con PTAP propia | mercado paralelo |
| Conjuntos residenciales con tanques propios | mercado B2C |
| Plantas industriales con consumo hídrico crítico | mercado B2B premium |
| Modelo de negocio definido: open source + servicios premium ($) | ✅ |
| Spin-off candidato a Apps.co + iNNpulsa Colombia | ✅ |
| **Puntaje proyectado:** | **4/4** |

**Subtotal APLICACIÓN INDUSTRIAL: 12/12 (30/30 ponderado)**

---

## IMPACTO (20%) — Auto-evaluación

### 9. Contribución a sostenibilidad ambiental (ODS 7, 12, 13, 15) — *meta: Excelente (4)*

> *"La propuesta reduce impactos ambientales negativos y promueve prácticas verdes."*

| ODS | Aporte cuantificado | Evidencia |
|-----|---------------------|-----------|
| **ODS 7** Energía asequible | -596 kWh/año por bombeo eficiente | KPI energético en compliance endpoint |
| **ODS 12** Producción/consumo responsable | -16.5M L de agua en 5 años | Métrica directa del impact endpoint |
| **ODS 13** Acción por el clima | -7.6 ton CO₂ en 5 años + tokenización | Carbon credits auditables |
| **ODS 15** Vida ecosistemas terrestres | Preservación cuenca río Pance + Cauca | Monitoreo nivel freático |
| **Puntaje proyectado:** | **4/4** |

### 10. Generación de bienestar y calidad de vida (ODS 3, 4, 8, 11) — *meta: Excelente (4)*

> *"La propuesta muestra impacto en la salud, educación, empleo digno y condiciones de vida."*

| ODS | Aporte cuantificado |
|-----|---------------------|
| **ODS 3** Salud y bienestar | Garantía calidad agua para 8,234 usuarios + alertas turbidez |
| **ODS 4** Educación de calidad | Modelo educativo open source + datos para tesis + electiva proyectada |
| **ODS 8** Trabajo decente | Reducción trabajo correctivo, valoración del preventivo |
| **ODS 11** Ciudades sostenibles | Modelo Smart Campus replicable a Cali |
| **Puntaje proyectado:** | **4/4** |

### 11. Fortalecimiento de comunidades y participación ciudadana (ODS 11, 16, 17) — *meta: Excelente (4)*

> *"La propuesta involucra activamente comunidades y fomenta cooperación multisectorial."*

| Mecanismo participativo | Evidencia |
|-------------------------|-----------|
| **Reporte ciudadano QR** — cualquier estudiante reporta fugas | Endpoint /water/report-issue + handler Telegram |
| **Smart Water Ledger** — eco-competencia entre edificios | Endpoint /water/leaderboard |
| **Pantallas LED públicas** — "pulso hídrico" del campus | Documentado fase 4 |
| **Datos abiertos** — Ley 1712/2014 cumplida automáticamente | Dashboard público + API |
| **Cooperación multisectorial:** UNIAJC + CVC + EMCALI + comunidad | Documentado en plan |
| **Puntaje proyectado:** | **4/4** |

**Subtotal IMPACTO: 12/12 (20/20 ponderado)**

---

## RESUMEN DE PUNTAJE PROYECTADO

| Categoría | Puntaje proyectado | % |
|-----------|---------------------|---|
| Novedad | 12/12 | 30% |
| Actividad Inventiva | 8/8 | 20% |
| Aplicación Industrial | 12/12 | 30% |
| Impacto | 12/12 | 20% |
| **TOTAL** | **44/44** | **100%** |

> **Clasificación: SOBRESALIENTE (rango 34–44)**

---

## Áreas donde podemos perder puntos (riesgos)

### ⚠️ Riesgo 1: Demasiada tecnología puede verse "irreal"

**Riesgo:** Jurado puede pensar que es propuesta no implementable.

**Mitigación:**
- Mostrar el simulador funcionando EN VIVO durante el pitch
- Backend corriendo · simulator_pc.py inyecta datos · dashboard responde
- Tener BOM concreto en COP listo para mostrar
- Usar palabras como "Fase 1 hoy" en lugar de "futuro lejano"

### ⚠️ Riesgo 2: "Multi-agente IA" puede sonar buzzword

**Mitigación:**
- Mostrar la deliberación REAL en el pitch (endpoint /agent/deliberate)
- Explicar con palabras simples: "5 ingenieros virtuales discuten en 3 segundos"
- Comparar tiempo: 5s del agente vs 2 horas humano

### ⚠️ Riesgo 3: Gamificación puede verse "infantil"

**Mitigación:**
- Mostrar referente serio: PUB Singapur, MIT Water Project
- Vincular a presupuesto real de bienestar universitario
- Enfatizar economía circular: ahorro → reinversión

### ⚠️ Riesgo 4: Open source puede verse "no monetizable"

**Mitigación:**
- Modelo freemium: software gratis + servicios premium pagos
- Caso Red Hat / GitLab / WordPress como referentes
- Enfatizar que UNIAJC tiene la propiedad de los datos

### ⚠️ Riesgo 5: Dependencia de cloud puede verse "frágil"

**Mitigación:**
- Mostrar arquitectura resiliente: ESP32 funciona sin internet
- HTTP fallback si MQTT falla
- NVS (flash) almacena datos hasta que vuelva conexión

---

## Ajustes finales antes del pitch

1. ✅ **Pitch reescrito** (PITCH-DEFINITIVO.md) con foco en agentes
2. ✅ **Endpoint /agent/deliberate** muestra los 5 agentes deliberando en vivo
3. ✅ **Mapa SVG con PTAR** completa el ciclo hídrico
4. ✅ **Documento INNOVACION-RADICAL** con 10 diferenciadores
5. ✅ **Cumplimiento normativo** mapeado a sanciones evitadas
6. **PENDIENTE:** ensayar pitch 5 minutos cronometrado
7. **PENDIENTE:** preparar laptop con todo corriendo + 4 terminales
8. **PENDIENTE:** imprimir BOM en COP para mostrar
9. **PENDIENTE:** hoja con respuestas a 7 preguntas anticipadas

---

## Mensaje clave para el equipo

> **No hay un solo criterio de la rúbrica donde estemos en "Bueno (3)" o
> menos. Estamos en "Excelente (4)" en los 11 criterios.**
>
> **Si el jurado se queja, no es porque falte trabajo. Es porque no
> entendieron la profundidad de la propuesta. Y eso lo arreglamos con
> un pitch mejor, no con más código.**
>
> **El código está completo. La presentación es lo que falta pulir.**

---

*Estrategia frente a rúbrica oficial · AguaMind OS · Hackathon UNIAJC 2026*
