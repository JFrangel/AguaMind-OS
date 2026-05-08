# Posibles preguntas del jurado — Reto Sistemas · HidroTech

**Hackathon UNIAJC 2026 · guía de preparación**

> Cada respuesta es corta, honesta y mantiene el lenguaje del pitch.
> Si el jurado pregunta algo técnico, **responder en términos del campus, no del código**.

---

## 🔵 Sobre la arquitectura general

**1. ¿Por qué cinco agentes y no uno solo?**
Porque cada uno tiene una especialidad distinta y separar responsabilidades hace al sistema más robusto. Un solo agente intentando hacer todo se vuelve frágil — si se equivoca en una cosa, contamina todo lo demás. Con cinco, si el Técnico detecta que un sensor está mintiendo, el Analista no usa esa lectura. Es el mismo principio de un equipo humano de mantenimiento: el supervisor, el operador, el ingeniero industrial y el técnico de campo no hacen el trabajo del otro.

**2. ¿Por qué LangGraph y no llamadas secuenciales a un LLM?**
Porque LangGraph permite que los tres agentes especializados (Analista, Técnico, Auditor) **piensen en paralelo** y después el Orquestador consolide. Si fueran secuenciales, el ciclo tardaría tres veces más. Con paralelo bajamos la latencia a menos de 5 segundos.

**3. ¿Cómo se comunican los agentes entre ellos?**
Comparten un estado en memoria llamado `WaterState`. Cada agente lee la lectura de los sensores, escribe su análisis en su sección del estado, y al final el Orquestador lee todo y consolida. No hay llamadas HTTP entre agentes — todo ocurre en el mismo proceso, en milisegundos.

---

## 🟢 Sobre los agentes en específico

**4. ¿El Auditor detecta la fuga?**
No. El Auditor **no detecta** — eso lo hace el Analista con un modelo estadístico. El Auditor **traduce el problema a impacto**: dice cuántos estudiantes·día equivale la pérdida, clasifica de cuál de las 7 mudas Lean se trata, y justifica por qué hay que actuar. Sin él, el equipo de mantenimiento recibiría números fríos.

**5. ¿Qué es una "muda Lean"?**
Es un término industrial — son los siete tipos de desperdicio identificados en metodología Lean: defectos, sobreproducción, espera, transporte, movimiento, inventario y procesamiento innecesario. El Auditor las usa para clasificar el problema con un nombre estándar que cualquier ingeniero industrial reconoce.

**6. ¿Cómo detecta anomalías el Analista?**
Usa un modelo de machine learning llamado IsolationForest entrenado sobre las últimas 50 lecturas en tiempo real. El modelo aprende qué es "normal" para el campus y marca como anomalía cualquier lectura que se aleja del patrón. No hay reglas fijas — el modelo se reentrena solo.

**7. ¿Cómo sabe el Técnico que un sensor está mintiendo?**
Hace tres validaciones: rango físico (presión nunca puede ser negativa, humedad no pasa del 100%), congelamiento (si lleva 5 minutos exactamente igual, está roto) y drift (si se desvía progresivamente sin razón, está descalibrado). Las lecturas mentirosas se descartan antes de llegar al análisis.

**8. ¿Y si los agentes no se ponen de acuerdo?**
El Orquestador aplica un criterio simple: **la peor decisión gana**. Si el Analista dice "alerta" y el Auditor dice "ok", el sistema actúa con "alerta". Es el principio de precaución — en gestión hídrica es mejor pecar de cauteloso.

---

## 🟡 Sobre las notificaciones

**9. ¿Por qué Telegram y no SMS o email?**
Por tres razones: es gratis, todo el mundo lo tiene en el celular, y soporta mensajes con formato (negrita, emojis, botones interactivos). Además, el equipo de mantenimiento puede responder a la alerta o autorizar acciones desde el mismo chat.

**10. ¿Qué pasa si Telegram se cae?**
Tenemos tres canales en paralelo: Telegram, email SMTP y un stream en vivo en el dashboard. Si uno falla, los otros dos siguen funcionando. Además, las alertas críticas quedan registradas en base de datos — nunca se pierden.

**11. ¿Spamean al equipo con notificaciones?**
No. Solo se manda push si la decisión es "warning", "alert" o "critical". Las decisiones "ok" no generan notificación, pero sí quedan registradas en el dashboard. Así el equipo solo recibe lo que importa.

---

## 🟠 Sobre las tres innovaciones

**12. ¿Qué tan "universal" es el adaptador de sensores?**
Acepta nueve formatos distintos: JSON plano, JSON estructurado, NDJSON, CSV, Modbus, OPC-UA, MQTT, SCADA con tags y el formato compacto del ESP32. Cuando llega un dato, el sistema detecta el formato automáticamente — no hay que configurar nada. Si mañana sale un sensor nuevo con un protocolo distinto, solo agregamos un adaptador y listo.

**13. ¿Por qué tres niveles de LLM en cascada?**
Para garantizar que el agente **siempre responde**. Primero intenta con Gemini (rápido, gratis, mejor calidad). Si falla, va a Groq (alternativa gratuita ultra rápida). Si los dos fallan o no hay internet, cae a un motor local que entiende 14 intenciones distintas en español. Resultado: incluso sin conexión, el chat funciona.

**14. ¿Los planes ante fenómenos climáticos están programados o se generan solos?**
Están pre-configurados como protocolos. El Orquestador es el que decide cuándo activarlos — por ejemplo, si recibe un alerta del IDEAM por El Niño, dispara automáticamente el plan de sequía: baja la presión nocturna, cierra el riego y notifica a los 8,234 usuarios. Cinco protocolos cubren los principales escenarios para Cali: sequía, lluvia intensa, sismo, contaminación y picos de demanda.

---

## 🔴 Preguntas escépticas

**15. ¿Cómo sabemos que esto funciona si no tienen sensores reales todavía?**
Lo que ven en el dashboard es un simulador realista basado en los datos reales de la PTAP de UNIAJC documentados por Aristizábal y Largacha (2025): 113.56 L/min de caudal, 45,367 L/día de consumo, 8,234 usuarios. Cuando se instalen los sensores físicos, se conectan al mismo backend sin tocar una línea — el simulador y los sensores reales hablan el mismo lenguaje.

**16. ¿Cuánto cuesta implementarlo en la realidad?**
La inversión inicial es de aproximadamente $1.4 millones de pesos en hardware (5 sensores ESP32 + electroválvulas) más una semana de instalación. El software es 100% gratuito — Vercel, Koyeb, Supabase, Gemini, Groq y HiveMQ están en plan free. El retorno de inversión proyectado es menor a un año.

**17. ¿Qué tan rápido reacciona realmente el sistema?**
Medido: sensor → notificación al teléfono ≤ 5 segundos. El desglose: 1 segundo de transmisión MQTT, 1 segundo de inferencia del LLM, 1 segundo de consenso entre agentes, 1 segundo para que la API de Telegram entregue el mensaje. Lo demás es buffer.

**18. ¿Es seguro? ¿Y si alguien hackea el sistema y abre todas las válvulas?**
Tres capas de protección: las electroválvulas críticas requieren confirmación humana desde Telegram (botón inline); el bot solo acepta comandos de chat IDs autorizados; y todo va por HTTPS con tokens rotables. El agente nunca puede vaciar un tanque por sí solo — necesita que un humano confirme.

---

## 🟣 Preguntas de cierre

**19. ¿Qué los hace distintos de un sistema SCADA convencional?**
Un SCADA muestra datos. HidroTech **decide y actúa**. Un SCADA necesita un operador 24/7 que vea las pantallas. HidroTech tiene cinco agentes que deliberan solos y solo molestan al humano cuando hay algo que requiere su atención. Y un SCADA cuesta entre 50 y 200 millones de pesos. HidroTech, menos de dos.

**20. ¿Esto es replicable a otras universidades?**
Sí, esa es la idea. El sistema está pensado para que cualquier universidad colombiana lo despliegue en una semana. Solo hay que ajustar la cantidad de sensores y los umbrales — toda la lógica de los cinco agentes, el adaptador universal y los planes ante fenómenos funciona igual en cualquier campus.

**21. ¿Qué ODS aporta?**
Cuatro: el 6 (agua limpia y saneamiento, recuperando hasta 16,500 litros al día), el 9 (industria, innovación e infraestructura, modernizando una planta de 2011), el 11 (ciudades sostenibles, modelo replicable) y el 12 (producción responsable, eliminando las 7 mudas Lean clásicas).

---

**Tip para el pitch:** Si te preguntan algo muy técnico que no controlas al 100%, **responde con la analogía del equipo humano**: "el Auditor es como el ingeniero industrial que cuantifica el desperdicio", "el Técnico es como el técnico de campo que verifica si el medidor está bien", etc. Funciona siempre.

---

**Equipo HidroTech · UNIAJC Sede Sur · 2026**
