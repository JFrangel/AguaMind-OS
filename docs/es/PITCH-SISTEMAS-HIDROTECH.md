# Pitch — Reto Sistemas · HidroTech

**Hackathon UNIAJC 2026 · 90 segundos · guion para hablar en voz alta**

---

> *Buenas tardes. Les voy a contar cómo funciona el cerebro de **HidroTech**, nuestra propuesta para el reto de Sistemas.*

> *El problema es claro: la planta de tratamiento de UNIAJC Sede Sur está instalada desde 2011 y **no tiene un solo sensor ni una sola alerta**. Pierde entre el 20% y el 30% del agua que bombea, y nadie se entera hasta que la fuga es visible.*

> *Nuestra solución es un **sistema multi-agente con inteligencia artificial**. No es un agente, son cinco, y trabajan en equipo como si fueran un grupo de ingenieros virtuales.*

> *El primero es el **Orquestador**. Él es el jefe del equipo: decide cuándo hay que deliberar, escucha a los demás y consolida la decisión final con un criterio simple — la peor decisión gana, porque en gestión hídrica es mejor pecar de cauteloso.*

> *El segundo es el **Analista**. Es el cerebro estadístico: calcula los indicadores en vivo —eficiencia hídrica, pérdidas y consumo por estudiante— y aplica un modelo de machine learning, IsolationForest, sobre las últimas cincuenta lecturas para detectar anomalías que el ojo humano no vería.*

> *El tercero es el **Técnico**. Su trabajo es desconfiar de los sensores: revisa que los valores sean físicamente posibles, detecta cuando un sensor se congeló o tiene drift, y descarta lecturas mentirosas antes de que contaminen el análisis.*

> *El cuarto es el **Auditor**. Mira el sistema con ojos de ingeniero industrial: identifica las siete mudas Lean, calcula cuánta agua se está perdiendo y cuánto se ahorraría con cada acción. Es el que justifica el retorno de inversión.*

> *Y el quinto es el **Mitigador**. Es el que actúa: abre o cierra electroválvulas, dispara la notificación al Telegram del equipo de mantenimiento, y deja todo registrado en bitácora.*

> *El ciclo es muy simple y se repite cada treinta segundos: los sensores **detectan**, los tres agentes especializados **piensan en paralelo** usando LangGraph, el Orquestador **decide**, y el Mitigador **notifica**. Si hay una anomalía, en menos de cinco segundos llega un mensaje al teléfono del equipo con la alerta, los datos clave y la acción recomendada.*

> *Pero queremos contarles tres cosas que, para nosotros, hacen que esta propuesta sea distinta.*

> *La primera es el **Universal Adapter**. Los sensores reales no hablan todos el mismo idioma — algunos mandan JSON, otros CSV, otros Modbus, otros OPC-UA, otros formato compacto del ESP32. HidroTech tiene un normalizador que detecta el formato automáticamente y traduce todo a un lenguaje común. Conectar un sensor nuevo es plug-and-play, sin tocar una sola línea de código.*

> *La segunda es el **sistema de LLMs en cascada**. El chat del agente intenta primero con Gemini 2.0, si falla se va a Groq con Llama 3.3, y si todo falla cae a un motor determinista local que entiende catorce intenciones distintas. El resultado es que el agente **siempre responde**, incluso sin internet, incluso sin API keys configuradas. Garantiza una demo robusta hoy y una operación veinticuatro siete en el campus mañana.*

> *Y la tercera son los **planes ante fenómenos climáticos**. HidroTech tiene cinco protocolos pre-configurados que el Orquestador activa solo: ante una sequía o fenómeno del Niño, baja la presión nocturna y cierra el riego automáticamente; ante lluvias intensas o La Niña, captura agua lluvia y suspende el bombeo; ante un sismo, cierra todas las válvulas en modo seguro; ante contaminación, aísla el tanque afectado y reporta a la CVC; y ante un pico de demanda, balancea entre tanques. **El campus se adapta solo, sin que nadie tenga que estar pendiente.***

> *Para cerrar: esto **funciona en vivo**, lo pueden ver ustedes ahora mismo en el dashboard, e incluso pueden recibir las notificaciones en su propio Telegram. La latencia desde sensor hasta alerta es menor a cinco segundos. El stack es cien por ciento gratuito —Vercel, Koyeb, Supabase, Gemini, Groq, HiveMQ— y cualquier universidad colombiana lo puede desplegar en una semana.*

> *HidroTech caracteriza, delibera y actúa. Gracias.*

---

**Equipo HidroTech · UNIAJC Sede Sur · 2026**
