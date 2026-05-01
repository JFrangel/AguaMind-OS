# ¿Qué es AgentOS?

AgentOS es una **plataforma base** para construir aplicaciones con inteligencia artificial. Te ahorra escribir desde cero todo el "plomería" que cualquier app de IA necesita, para que te enfoques en el problema que querés resolver.

Pensalo así: si quisieras abrir un restaurante, no construirías el horno, la heladera y la caja registradora vos mismo. AgentOS es ese conjunto de cosas listas, y vos pones la receta.

---

## El problema que resuelve

Cuando alguien quiere construir una app que use IA (un chatbot, un asistente, un analizador de datos), normalmente se enfrenta a estos dolores:

### Dolor 1: La IA falla y todo se cae

Los servicios de IA (OpenAI, Google, etc.) a veces no responden. Tienen "rate limits" (te frenan si pedís mucho), caídas, o simplemente fallan. Si tu app depende de uno solo, **un mal día tuyo es un mal día de tus usuarios**.

**Cómo lo resolvemos**: AgentOS conecta 3 proveedores de IA en paralelo (Groq, OpenRouter, Gemini). Si Groq falla, automáticamente cambia a OpenRouter. Si ese también, va a Gemini. Tu usuario nunca se entera. Es como tener tres caminos al trabajo: si hay tráfico en uno, tomás otro sin pensar.

### Dolor 2: La IA cuesta dinero

Llamar a estos servicios cuesta. Para un proyecto experimental, hackathon, o startup que recién empieza, pagar por cada respuesta puede frenar todo.

**Cómo lo resolvemos**: usamos exclusivamente los **planes gratuitos** de los tres proveedores. Groq tiene un plan gratis generoso, OpenRouter tiene modelos marcados `:free`, Gemini Flash es gratis hasta 15 consultas por minuto. AgentOS está pre-configurado para usar solo lo gratuito. Total: **$0 para empezar**.

### Dolor 3: El usuario no entiende qué está pasando

Cuando la IA piensa por 5 segundos, el usuario ve una pantalla en blanco. Eso se siente lento aunque sea rápido. Y si la IA toma una decisión rara, no hay forma de saber por qué.

**Cómo lo resolvemos**: AgentOS muestra **el razonamiento en vivo**, paso a paso. El usuario ve "Investigando...", "Analizando...", "Escribiendo respuesta..." mientras pasa. Y en un panel lateral se ve qué agente está activo y qué decidió. Nada de caja negra.

### Dolor 4: Desplegar es complicado

Sacar una app a internet implica configurar servidores, bases de datos, dominios, certificados. Para alguien que solo quiere validar una idea, es un mundo aparte.

**Cómo lo resolvemos**: AgentOS está pensado para **plataformas gratuitas**: Vercel para la web, Koyeb para el servidor, Supabase para la base de datos. Hay una guía paso a paso para tener tu app en internet en menos de 30 minutos.

### Dolor 5: La IA no conoce tus datos

Por defecto, una IA no sabe nada de tu negocio. Si tenés documentos internos, una base de datos con clientes, o un manual técnico, la IA no los ve.

**Cómo lo resolvemos**: AgentOS incluye dos mecanismos:
- **RAG** (Retrieval-Augmented Generation): subís tus documentos y la IA los puede consultar. Es como darle a la IA acceso a tu archivo personal.
- **Conexión a base de datos**: enchufás tu Postgres / MySQL / SQLite y la IA puede hacer consultas en lenguaje natural ("¿cuántos clientes nuevos hubo este mes?") y te devuelve la respuesta.

### Dolor 6: La IA te encuentra algo importante y vos no estás mirando

Si la IA detecta una anomalía a las 3 AM, ¿cómo te enterás? Estar pegado a la pantalla no es opción.

**Cómo lo resolvemos**: AgentOS tiene un sistema de notificaciones que te avisa por **Telegram** y **email** en paralelo. Vos configurás una vez tus canales, y los agentes pueden mandarte alertas cuando algo necesita tu atención.

---

## Cómo funciona, en una imagen

```
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│   USUARIO escribe:                                           │
│   "¿Cuántas ventas tuvimos esta semana?"                     │
│                                                              │
└──────────────────────────┬───────────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  EL CEREBRO (orquestador)                                    │
│  Decide qué agentes van a participar.                        │
└──────────────────────────┬───────────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  AGENTES TRABAJANDO EN VIVO (visible para el usuario)        │
│                                                              │
│  📊 Consultor SQL    →   "SELECT count(*) FROM ventas..."    │
│  🔍 Investigador     →   "Buscando contexto..."              │
│  ✍️ Redactor         →   "Esta semana tuvieron 142 ventas... │
│                                                              │
└──────────────────────────┬───────────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  RESPUESTA en streaming (texto que aparece letra por letra)  │
│                                                              │
│  "Esta semana tuvieron 142 ventas, un 12% más que la anterior│
│   ...                                                        │
└──────────────────────────────────────────────────────────────┘
```

Y por debajo de todo, los 3 proveedores de IA en cascada con failover automático.

---

## ¿Para quién es?

| Si sos... | Te sirve para... |
|-----------|------------------|
| **Equipo de hackathon** | Tener un demo profesional en horas, no días |
| **Startup early-stage** | Validar una idea de IA sin gastar en infraestructura |
| **Estudiante o curioso** | Aprender cómo se construye un sistema de agentes real |
| **Consultor / freelance** | Entregar prototipos a clientes sin reinventar la rueda |
| **Equipo interno de empresa** | Construir herramientas con IA sin depender de SaaS pagos |

---

## ¿Qué tiene incluido?

Una lista honesta:

**Frontends listos** (interfaz que usa el usuario final):
- Versión en SvelteKit
- Versión en Next.js (React)
- Versión en Nuxt (Vue)

Eligís la que más te guste o conozcas. Las tres tienen exactamente la misma funcionalidad.

**Backends listos** (servidor que procesa):
- Servidor principal en Python (FastAPI)
- Servidor secundario en Go (más rápido para algunas cosas)
- Versiones alternativas en Express y NestJS por si las preferís
- PocketBase como base de datos liviana opcional

**Capacidades del agente**:
- Chat con razonamiento visible
- Investigación automática (busca, analiza, escribe)
- Trabajo en equipo entre agentes (un experto investigador + uno analista + uno redactor)
- Búsqueda en documentos que vos subiste (RAG)
- Consulta a tu base de datos en lenguaje natural
- Detección de anomalías en datos
- Geocodificación (convertir direcciones en coordenadas)
- Generación de reportes en PDF
- Notificaciones por Telegram + email
- Bot de Telegram listo para usar

**Operación**:
- Failover automático entre 3 IAs (Groq → OpenRouter → Gemini)
- Circuit breaker (si una IA falla seguido, la sacamos por 60 segundos para no perder tiempo)
- Rate limiting (protección contra abuso)
- Autenticación opcional con tokens (JWT)
- Tests automatizados (66+ tests por paquete que validan failover, RAG, file adapter, agentes, multi-idioma, NL→SQL, notificaciones)
- Despliegue automático con GitHub Actions

---

## ¿Qué NO es?

Para evitar malentendidos:

- **No es una IA que aprende sola**. Usa modelos de IA existentes (Groq, OpenRouter, Gemini), no entrena los suyos.
- **No es un producto terminado**. Es una base. Vos le ponés el problema concreto.
- **No es magia**. Si los 3 proveedores caen al mismo tiempo, no hay respuesta. Pero la probabilidad es bajísima.
- **No reemplaza a un equipo de ingeniería senior**. Te ahorra 70% del trabajo inicial; el 30% restante es tu lógica de dominio.

---

## Las 3 grandes ideas detrás del diseño

### 1. Modularidad real

Si borrás `packages/geo` (el módulo geográfico), nada más se rompe. Cada parte es una pieza independiente. Esto es valioso porque podés:
- Eliminar lo que no usás (apps más liviana, deploy más rápido)
- Reemplazar una pieza por otra (cambiar el motor de búsqueda, por ejemplo)
- Agregar piezas nuevas sin tocar el resto

### 2. Razonamiento visible

La IA no es una caja negra. Cada paso que da el agente se muestra:
- Qué decidió hacer
- Qué información usó
- Qué le pasa al siguiente agente

Esto **construye confianza** con el usuario y te ayuda a debuggear cuando algo sale mal.

### 3. Streaming desde el primer segundo

La respuesta empieza a aparecer **antes** de que la IA termine de pensar. El usuario ve la primera letra en menos de medio segundo. Esto cambia totalmente la sensación de la app: se siente viva, no congelada.

---

## ¿Por dónde sigo?

Según qué quieras hacer:

| Querés... | Leé... |
|-----------|--------|
| Probarlo en tu computadora ahora | [GUIA-RAPIDA.md](GUIA-RAPIDA.md) |
| Ver todo lo que puede hacer | [FUNCIONALIDADES.md](FUNCIONALIDADES.md) |
| Construir tu propia app encima | [IMPLEMENTACION.md](IMPLEMENTACION.md) |
| Subirlo a internet | [../DEPLOY.md](../DEPLOY.md) (en inglés, pero los comandos son universales) |
| Detalles técnicos profundos | [../USAGE.md](../USAGE.md) (en inglés) |

---

## Una pregunta honesta

> "¿Esto realmente me ahorra tiempo o voy a terminar peleando con el código de otro?"

Es una pregunta válida. La respuesta corta: **te ahorra tiempo si tu app cae dentro de los patrones que el boilerplate cubre** (chat con IA, agentes que razonan, búsqueda en documentos, consultas a base de datos, notificaciones).

Si tu app es algo muy distinto (procesamiento de video en tiempo real, simulaciones físicas, análisis de imágenes médicas), AgentOS te servirá menos. No fue diseñado para eso.

El test rápido para saber si te sirve:

✅ **Te sirve** si tu app tiene este patrón:
> "El usuario escribe algo, la IA piensa con ayuda de [datos/documentos/herramientas], y devuelve una respuesta"

❌ **No tanto** si tu app es:
> "El usuario sube un video y queremos detectar caras en tiempo real"

---

Hecho. Ya sabés qué es AgentOS. Si querés probarlo, [empezá por la guía rápida](GUIA-RAPIDA.md).
