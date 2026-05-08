# Pitch — Reto Sistemas · HidroTech

**Hackathon UNIAJC 2026 · 90 segundos**

---

## El problema

La PTAP de UNIAJC Sede Sur (instalada en 2011) **no tiene sensores ni alertas**. Pierde entre el 20% y el 30% del agua que bombea. Nadie se entera hasta que la fuga es visible.

---

## La solución: 5 agentes IA que piensan en equipo

**HidroTech** es un sistema multi-agente que detecta anomalías, delibera y notifica al equipo de mantenimiento por Telegram en menos de 5 segundos.

### Los 5 agentes

| Agente | Qué hace |
|---|---|
| 🎯 **Orquestador** | Coordina al equipo. Decide cuándo deliberar y consolida la decisión final ("la peor decisión gana"). |
| 📊 **Analista** | Calcula los KPIs en vivo (IEH · TPP · CPE) y detecta anomalías estadísticas con **IsolationForest** sobre las últimas 50 lecturas. |
| 🔧 **Técnico** | Valida la calidad de las señales: rango físico, congelamiento, drift. Si un sensor miente, lo descarta. |
| 📋 **Auditor** | Identifica las **7 mudas Lean**, calcula impacto monetario y proyección anual. Es el que justifica el ROI. |
| 🚨 **Mitigador** | Ejecuta la acción: abre o cierra electroválvulas, notifica por Telegram y registra todo en bitácora. |

### El ciclo (cada 30 segundos)

```
Detectar  →  Pensar en paralelo  →  Decidir  →  Notificar
  📡            🎯 📊 🔧 📋             ✅           📱
```

1. Lee los **5 sensores** (Q caudal, R riego, P presión, N nivel, H humedad).
2. Los 3 agentes especializados (Analista, Técnico, Auditor) trabajan **en paralelo** con LangGraph.
3. El Orquestador consolida sus análisis.
4. Si hay anomalía → el Mitigador dispara una notificación push al Telegram del equipo.

---

## Tres innovaciones del reto Sistemas

### 1. Universal Adapter — habla cualquier idioma de sensores

Los sensores reales mandan datos en formatos distintos: JSON, CSV, NDJSON, Modbus, OPC-UA, MQTT, SCADA tag-based o el formato compacto del ESP32. HidroTech tiene un **normalizador universal** que detecta el formato automáticamente y entrega lecturas canónicas al sistema. **Conectar un sensor nuevo es plug-and-play, sin tocar código.**

### 2. Cascada de LLMs — nunca falla

```
Gemini 2.0 Flash    (gratis · 1 M tokens/día)
     ↓ (si falla o no hay key)
Groq Llama 3.3 70B  (gratis · ultra rápido)
     ↓ (si falla)
Fallback determinista (14 intenciones · 0 ms · siempre disponible)
```

El chat del agente **siempre responde**, incluso sin internet o sin API keys configuradas. Garantiza demo robusta y operación 24/7 en el campus.

### 3. Plan ante fenómenos climáticos

HidroTech tiene **5 planes pre-configurados** que el Orquestador activa automáticamente:

- 🌵 **El Niño / sequía** → reduce presión nocturna 38→25 PSI, cierra riego, broadcast a 8,234 usuarios.
- 🌧️ **La Niña / lluvia intensa** → captura agua lluvia, suspende bombeo del aljibe.
- 🌊 **Sismo** → cierre total de electroválvulas, modo seguro.
- 🧪 **Contaminación** → aísla tanque afectado, reporta a la CVC.
- 📈 **Pico de demanda** → balanceo automático entre tanques A y B.

Cada plan es un trigger que combina hasta 6 acciones simultáneas. **El campus se adapta solo.**

---

## Por qué nos van a creer

✅ **Funciona en vivo:** dashboard `/agua` con datos en tiempo real, notificaciones Telegram que llegan al teléfono del jurado.
✅ **Latencia medida:** sensor → notificación ≤ **5 segundos**.
✅ **Stack 100% gratuito:** Vercel + Koyeb + Supabase + Gemini + Groq + HiveMQ free tier.
✅ **Replicable:** cualquier universidad colombiana lo despliega en una semana.

---

**HidroTech · UNIAJC Sede Sur · 2026**
*Caracteriza · Delibera · Actúa.*
