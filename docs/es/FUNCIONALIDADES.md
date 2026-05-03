# Funcionalidades de AgentOS

Todo lo que AgentOS puede hacer, explicado en lenguaje claro. Cada sección tiene: qué es, cuándo te sirve, ejemplo concreto, y limitaciones honestas.

---

## 1. Chat con IA con failover automático

### ¿Qué hace?

Es lo más básico: el usuario escribe, la IA responde. Pero con una diferencia importante: **si la IA principal falla, automáticamente cambia a otra**, sin que el usuario se entere.

### ¿Cuándo te sirve?

Siempre. Es la base de cualquier app conversacional.

### Ejemplo

```
Usuario: "Explícame qué es PostgreSQL en 2 líneas"

AgentOS intenta con Groq → falla (rate limit)
AgentOS intenta con OpenRouter → responde en 800ms
Usuario ve: "PostgreSQL es una base de datos relacional de código abierto..."
```

El usuario nunca supo que Groq falló.

### Cómo funciona por dentro

Hay 5 "estrategias de cascada" que decidís según la necesidad:

| Estrategia | Orden | Cuándo usarla |
|-----------|-------|---------------|
| `speed` | Groq → OpenRouter → Gemini | Chat rápido, respuestas cortas |
| `reasoning` | Gemini → OpenRouter → Groq | Análisis, pensamiento profundo |
| `cheap` | OpenRouter → Groq → Gemini | Trabajo masivo en segundo plano |
| `multimodal` | Gemini | Cuando hay imágenes o audio |
| `quality` | OpenRouter (GLM 4.5 Air, gpt-oss-120b, DeepSeek, Qwen, Hermes-405B) → Gemini → Groq | Extraer detalle de un texto largo, comparar a fondo, armar tablas con muchas columnas |

**No tenés que elegir manualmente.** El chat usa `pick_cascade()` y se auto-ajusta por query:

- "hola", "qué hora es" → `speed` (rápido y barato)
- "compara langchain vs crewai", "explica paso a paso", "lista 10 frameworks", queries largas o multi-oración → `quality` (modelo más grande, mejor extracción)
- Cuando hay contexto web con artículo completo (~1500 chars extraídos) → `quality` (para que aproveche todo el detalle, no solo el snippet)

Vos no tocás nada — la cascade adecuada se elige sola.

### Limitación honesta

Los modelos gratuitos tienen límites. Groq te limita a algunas peticiones por minuto, Gemini a 15. Los modelos pesados de OpenRouter (`quality` cascade) a veces devuelven 429; cuando eso pasa, la cascade sigue cayendo a Gemini y Groq automáticamente. Para producción seria, vas a querer claves de pago.

---

## 2. Agentes que razonan en equipo

### ¿Qué hace?

En vez de que una sola IA responda todo, AgentOS arma un **equipo de agentes especializados**:

- **Router**: decide qué tipo de pregunta es (chat simple, investigación, análisis, redacción)
- **Investigador**: busca y reúne datos relevantes
- **Analista**: razona sobre los datos, encuentra patrones
- **Redactor**: convierte el análisis en una respuesta clara

Cada uno hace su parte y le pasa el resultado al siguiente.

### ¿Cuándo te sirve?

Cuando la pregunta es compleja y un solo paso no alcanza. Por ejemplo:

- "Compará pgvector contra FAISS y decime cuál uso para mi caso"
- "Analizá las ventas del último trimestre y dame recomendaciones"
- "Investigá las últimas tendencias en marketing digital y escribí un resumen"

### Ejemplo en vivo

```
Usuario pregunta: "¿Cuál es la diferencia entre LangGraph y CrewAI?"

[Router]      → "Esto es investigación con análisis"
[Investigador] → recolecta 5 datos clave
[Analista]    → identifica trade-offs y casos de uso
[Redactor]    → escribe la respuesta final palabra por palabra

Total: ~3 segundos. El usuario ve cada paso en vivo.
```

### Por qué es importante

Los modelos de IA dan mejores respuestas cuando **dividís la tarea**. Un solo prompt gigante "investigá, analizá y escribí" tiene menos calidad que tres prompts especializados encadenados.

### Modos disponibles

| Modo | Qué hace |
|------|---------|
| `chat` | Solo responde directo (router → respondedor) |
| `research` | Pipeline completo (investigador → analista → redactor) |
| `crew` | CrewAI: equipo más estructurado, mejor para outputs largos |

---

## 3. Búsqueda en tus documentos (RAG)

### ¿Qué hace?

Le subís documentos a AgentOS (PDFs, textos, manuales, FAQs), y la IA puede **consultarlos al responder**. Si tu documento dice "el horario es de 9 a 18hs", la IA lo va a usar cuando alguien pregunte por horarios.

RAG significa "Retrieval-Augmented Generation" — generación aumentada por recuperación. La IA recupera fragmentos relevantes de tus docs y los usa para responder.

### ¿Cuándo te sirve?

- **Atención al cliente**: subí tu FAQ, manuales, políticas. La IA responde dudas con info real.
- **Asistente legal**: subí contratos, leyes, jurisprudencia. La IA te ayuda a encontrar precedentes.
- **Manual técnico**: subí documentación interna. Tu equipo pregunta en lenguaje natural.
- **Estudio**: subí tus apuntes y la IA te ayuda a repasar.

### Cómo funciona

1. Subís un documento (`POST /rag/ingest`)
2. AgentOS lo divide en pedazos manejables (chunks de ~500 palabras, respetando oraciones)
3. Cada pedazo se convierte en un "vector matemático" (un conjunto de números que representa el significado)
4. Los vectores se guardan en una base de datos especial
5. Cuando alguien pregunta, su pregunta también se convierte en vector
6. AgentOS busca los pedazos más parecidos (semánticamente, no por palabras exactas)
7. Esos pedazos se le pasan a la IA junto con la pregunta

### Ejemplo

```bash
# Subís tu manual de empleados
curl -X POST http://localhost:8000/rag/ingest -F "file=@manual_empleados.pdf"
# → "12 chunks creados"

# Alguien pregunta:
"¿Cuántos días de vacaciones tengo después de 5 años?"

# AgentOS busca en el manual los fragmentos relevantes
# y la IA responde:
"Según el manual de empleados, después de 5 años de antigüedad
 corresponden 21 días de vacaciones por año..."
```

### Características avanzadas

- **Filtros por metadata**: podés etiquetar documentos (`tenant: "empresa-A"`) y filtrar al buscar. Útil para multi-tenant.
- **Borrado por origen**: si actualizás un documento, podés borrar todos sus chunks viejos antes de subir la nueva versión.
- **Sentence-aware chunking**: en vez de cortar a media palabra, respeta el final de oración. Mejora mucho la calidad.

### Modelos de embedding disponibles

Por defecto AgentOS usa **`all-MiniLM-L6-v2`** (~80 MB, corre en CPU, sin API key, 384 dimensiones, inglés-oriented). Es la opción "funciona donde sea sin pensar".

Si querés más calidad — sobre todo para multilingüe (español + inglés mezclados) — podés cambiar a **`gemini-embedding-001`** vía API gratuita:

```bash
# en .env
EMBEDDING_MODEL=gemini-embedding-001
EMBEDDING_DIM=3072  # o 768 / 1536 si querés ahorrar storage
```

Ventajas de Gemini:
- **0 MB de descarga** (es API, no modelo local)
- **Multilingüe nativo** (100+ idiomas)
- **Free tier ~1500 RPD** en AI Studio — sobra para hackathon
- **Reusa la `GEMINI_API_KEY`** que ya tenés para el LLM (no es otra key)
- **3072 dimensiones** (configurable a 1536 / 768 con Matryoshka truncation — la calidad baja muy poco)

Limitación: si superás los rate limits del free tier te tira 429. Si querés todo offline, quedate con MiniLM (o BGE-M3 self-hosted, pero pesa 2 GB y rompe el "deploy en free tier").

### Limitación honesta

- En desarrollo local usa **FAISS** (en memoria). Si reiniciás el servidor, **se pierde todo**.
- Para producción se conecta a Supabase con pgvector. Ahí sí persiste.
- Si cambiás `EMBEDDING_MODEL` después de tener docs ingestados, hay que re-embeddearlos (los vectores viejos no son compatibles con el nuevo modelo) y hacer `ALTER TABLE documents ALTER COLUMN embedding TYPE vector(3072)`.

---

## 4. Conexión a tu base de datos + consultas en lenguaje natural

### ¿Qué hace?

Conectás AgentOS a tu base de datos existente (Postgres, MySQL, SQLite) y los usuarios pueden hacer preguntas en español. La IA traduce a SQL, ejecuta, y devuelve la respuesta.

Es probablemente **la feature más impresionante** del boilerplate.

### ¿Cuándo te sirve?

- **Dashboard ejecutivo**: "¿cuántas ventas hubo este trimestre por región?"
- **Soporte interno**: "¿cuándo fue el último login del usuario juan@ejemplo.com?"
- **Análisis ad-hoc**: "¿qué productos tienen stock bajo?"
- **Reportes self-service**: equipos no técnicos hacen consultas sin saber SQL

### Ejemplo real (verificado funcionando)

**Setup**: una base SQLite con tablas `users` (id, email, name, age) y `orders` (id, user_id, total).

```bash
# El usuario pregunta en español:
curl -X POST http://localhost:8000/database/nl-query \
  -d '{"question":"¿Qué usuario tiene el mayor total de compras? Mostrar nombre y total."}'

# AgentOS:
# 1. Lee el esquema de la BD (tablas, columnas, foreign keys)
# 2. Le pasa el esquema + la pregunta al LLM
# 3. El LLM genera SQL:
#    SELECT u.name, SUM(o.total) FROM users u
#    JOIN orders o ON u.id = o.user_id
#    GROUP BY u.id ORDER BY SUM(o.total) DESC LIMIT 1
# 4. Validador de seguridad la revisa
# 5. La ejecuta
# 6. Devuelve: { name: "Carol", total: 1500 }
```

### La pieza crítica: seguridad

El validador bloquea SQL peligroso **antes** de ejecutar:

| Tipo de SQL | ¿Pasa? |
|-------------|--------|
| `SELECT * FROM users` | ✅ Sí |
| `WITH t AS (...) SELECT * FROM t` | ✅ Sí (con CTE) |
| `INSERT INTO ...` | ❌ Bloqueado |
| `UPDATE ... SET ...` | ❌ Bloqueado |
| `DROP TABLE users` | ❌ Bloqueado |
| `SELECT *; DROP TABLE x` | ❌ Bloqueado (multi-statement) |

Por defecto está en modo **read-only**. Si necesitás permitir escritura (raro), podés activarlo, pero solo desde código, nunca desde el endpoint público.

### Funciona con

- PostgreSQL (incluyendo Supabase, Neon, RDS)
- MySQL / MariaDB
- SQLite (ideal para desarrollo)

### Endpoints

| Endpoint | Para qué |
|----------|----------|
| `GET /database/schema` | Ver qué tablas y columnas hay |
| `POST /database/query` | Ejecutar SQL directo (con safety check) |
| `POST /database/nl-query` | Pregunta en lenguaje natural → SQL → resultado |

### Limitación honesta

- El LLM no es perfecto generando SQL. Para consultas complejas con muchos JOINs puede equivocarse.
- Funciona mejor con esquemas de hasta 30-40 tablas. Más allá, el contexto del LLM se vuelve grande y caro.
- No reemplaza un BI tool real (Metabase, Tableau). Es para preguntas rápidas en lenguaje natural, no para reportes complejos guardados.

---

## 5. Sistema de notificaciones (Telegram + Email)

### ¿Qué hace?

Permite que tus agentes (o tu app en general) **te avisen** cuando algo importante pasa. Telegram y email son los canales actuales; está diseñado para agregar Slack o Discord fácilmente.

### ¿Cuándo te sirve?

- **Alertas de anomalías**: el agente detectó algo raro en tus datos → te llega un Telegram
- **Tareas largas**: un análisis tarda 10 minutos → te avisa cuando termina
- **Aprobación humana**: el agente necesita que vos decidas algo → te manda email con el contexto
- **Reportes periódicos**: cada lunes te llega el resumen de la semana al mail

### Ejemplo

```bash
curl -X POST http://localhost:8000/notify/send \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Anomalía detectada",
    "body": "12 transacciones sospechosas en la última hora",
    "severity": "warning",
    "channels": ["telegram", "email"]
  }'
```

Resultado:
- Telegram: te llega el mensaje al chat configurado, con prefijo `[WARN]`
- Email: igual, en paralelo, en menos de 1 segundo

### Cómo configurar

Solo dos cosas en el `.env`:

**Para Telegram**:
```env
TELEGRAM_BOT_TOKEN=123456:ABC...   # Lo creás hablando con @BotFather en Telegram
TELEGRAM_CHAT_IDS=123456789        # Tu chat ID (lo obtenés mandando /start a @userinfobot)
```

**Para email** (funciona con Gmail, Brevo, SendGrid, Resend, cualquier SMTP):
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=tu@gmail.com
SMTP_PASSWORD=tu-app-password     # No tu contraseña real, una "app password" de Gmail
EMAIL_RECIPIENTS=destino@ejemplo.com
```

Si no configurás un canal, simplemente se omite — la app no falla.

### Niveles de severidad

| Nivel | Cuándo usarlo |
|-------|---------------|
| `info` | Información rutinaria. "Reporte diario listo" |
| `warning` | Algo a revisar, no urgente. "Stock bajo" |
| `error` | Algo falló, atención necesaria. "Pago rechazado" |
| `critical` | Acción inmediata requerida. "Servidor caído" |

### Limitación honesta

- Telegram y email NO son tiempo real estricto. Pueden tardar segundos. Para alertas críticas de milisegundos, necesitás algo tipo PagerDuty.
- Los emails pueden caer en spam si tu SMTP no está bien configurado (DKIM, SPF). Para producción seria, usá un proveedor profesional como Resend o SendGrid.

---

## 6. Detección de anomalías

### ¿Qué hace?

Subís un archivo CSV con datos numéricos y AgentOS te dice cuáles filas son **outliers** (valores raros, fuera de patrón).

Usa dos algoritmos clásicos de machine learning:
- **Isolation Forest**: rápido, bueno en general
- **LOF (Local Outlier Factor)**: bueno cuando los outliers están en zonas densas

### ¿Cuándo te sirve?

- **Fraude**: transacciones con patrones raros
- **Calidad de datos**: detectar entradas erróneas en bases grandes
- **Monitoreo**: identificar comportamiento anómalo en logs
- **Mantenimiento predictivo**: detectar lecturas raras en sensores

### Ejemplo

```bash
curl -X POST "http://localhost:8000/ml/anomalies?method=isolation_forest&contamination=0.1" \
  -F "file=@transacciones.csv"

# Respuesta:
{
  "total_rows": 5000,
  "anomalies_found": 487,
  "results": [
    {"index": 12, "score": -0.42, "is_anomaly": true},
    {"index": 13, "score": 0.15, "is_anomaly": false},
    ...
  ]
}
```

`contamination: 0.1` significa "esperá que el 10% de los datos sean anómalos". Ajustalo según tu caso.

### Limitación honesta

- Solo trabaja con columnas numéricas. Si tus datos son texto puro, este módulo no aplica.
- No te dice **por qué** algo es anómalo, solo que lo es. Para explicabilidad necesitarías combinarlo con el agente analista.

---

## 7. Geocodificación (direcciones ↔ coordenadas)

### ¿Qué hace?

- **Geocoding**: dirección → latitud/longitud
- **Reverse geocoding**: latitud/longitud → dirección

Usa Nominatim (el servicio gratuito de OpenStreetMap).

### ¿Cuándo te sirve?

- App de delivery: convertís direcciones de clientes en coordenadas para asignar repartidores
- Mapa de sucursales: convertís lat/lon en direcciones legibles
- Filtros geográficos: "buscá clientes en un radio de 5km"

### Ejemplo

```bash
curl -X POST http://localhost:8000/geo/geocode \
  -d '{"address": "Avenida Corrientes 1234, Buenos Aires"}'

# → {"lat": -34.6037, "lon": -58.3816, "label": "Avenida Corrientes 1234..."}
```

### Limitación honesta

- Nominatim es gratis pero **lento**. ~1 segundo por consulta. Para volumen alto, usá Google Maps API o Mapbox (pagos).
- Tiene rate limits estrictos: 1 request/segundo. Para batch, usá cache agresivo.

---

## 8. Generación de reportes en PDF

### ¿Qué hace?

Tomás datos (métricas, tablas, gráficos) y los convertís en un PDF descargable, con diseño limpio.

### ¿Cuándo te sirve?

- Reportes ejecutivos automatizados
- Facturas / cotizaciones generadas por IA
- Resúmenes de análisis con gráficos
- Cualquier cosa que el cliente quiera "para imprimir"

### Ejemplo

```bash
curl -X POST http://localhost:8000/reports/generate \
  -H "Content-Type: application/json" \
  -o reporte.pdf \
  -d '{
    "title": "Análisis de Ventas Q4",
    "summary": "Crecimiento del 12% YoY...",
    "metrics": [
      {"label": "Ingresos", "value": "$1.2M"},
      {"label": "Clientes", "value": "847"}
    ],
    "table_columns": ["Región", "Ventas"],
    "table_data": [
      {"Región": "Norte", "Ventas": "$500K"},
      {"Región": "Sur", "Ventas": "$700K"}
    ]
  }'
```

Te baja un PDF con título grande, métricas en cards, tabla, y footer.

### Bajo el capó

- **WeasyPrint**: convierte HTML+CSS a PDF (calidad de impresión)
- **Jinja2**: motor de templates para componer el HTML
- **Matplotlib**: para gráficos embebidos como imágenes base64

### Limitación honesta

- En **Windows local** WeasyPrint requiere instalar bibliotecas GTK. Es molesto. En el Docker de producción ya viene incluido.
- Los templates son básicos. Para diseño pixel-perfect (estilo Adobe), querrás un servicio como APITemplate o Carbone.

---

## 9. Bot de Telegram listo

### ¿Qué hace?

Un bot completo que conecta Telegram con AgentOS. Tus usuarios chatean con el bot como si fuera la app.

### Comandos disponibles

| Comando | Qué hace |
|---------|----------|
| `/start` | Mensaje de bienvenida con la lista de comandos |
| `/ask <pregunta>` | Chat normal con el agente |
| `/research <tema>` | Pipeline completo de investigación |
| `/report <tema>` | Genera un reporte y te lo manda como PDF |
| `/status` | Te dice qué proveedores de IA están UP |
| (texto cualquiera) | Lo trata como `/ask` |

### Ejemplo de uso

```
Usuario: /research el impacto de la IA en el empleo

Bot:
  Thinking...    [se actualiza en vivo]
  ▼
  La inteligencia artificial está transformando...
  [el texto crece carácter por carácter en el chat]
```

### Cómo activarlo

1. Hablá con `@BotFather` en Telegram → `/newbot` → guardá el token
2. Poné el token en `.env`: `TELEGRAM_BOT_TOKEN=123:ABC...`
3. `python apps/telegram/bot.py`

### Limitación honesta

- Telegram corta los mensajes a 4096 caracteres. Para respuestas más largas, el bot las divide en partes.
- Solo lleva el contexto de **un** mensaje a la vez. No tiene memoria conversacional. Eso es agregable pero no viene por defecto.

---

## 10. Análisis de datos tabulares

### ¿Qué hace?

Cargás un CSV o Excel y AgentOS te devuelve estadísticas básicas (count, mean, min, max, percentiles, valores nulos por columna).

### ¿Cuándo te sirve?

- Primer paso al recibir datos nuevos
- Validar que un archivo subido se ve bien antes de procesarlo
- Generar resúmenes para mostrar en un dashboard

### Ejemplo

```bash
curl -X POST http://localhost:8000/data/upload -F "file=@ventas.csv"
```

Devuelve:
- Forma del dataset (filas × columnas)
- Tipos de cada columna
- Cantidad de nulos
- Estadísticas por columna numérica

### Bajo el capó

- pandas para manipulación
- numpy para cálculos
- scipy para estadísticas avanzadas (regresión, SVD, PCA, interpolación) cuando las pidas

---

## 11. Tres frontends a elegir

Misma app, tres tecnologías. Elegís la que prefieras:

| Frontend | Stack | Cuándo elegirlo |
|----------|-------|-----------------|
| `web-svelte` | SvelteKit + Svelte runes + Tailwind | Si te gusta lo simple y rápido |
| `web-next` | Next.js + React + Zustand + Tailwind | Si tu equipo conoce React |
| `web-vue` | Nuxt 3 + Pinia + Tailwind | Si tu equipo conoce Vue |

Los tres tienen exactamente la misma UX:
- Chat con streaming
- Panel lateral con razonamiento de los agentes en vivo
- Indicador de salud de los proveedores
- Historial de la conversación

### Limitación honesta

- No tienen autenticación de usuario por defecto. Es agregable con Supabase Auth en ~30 minutos.
- No persisten la conversación si recargás la página. Eso requiere conectar PocketBase o Supabase para historial.

---

## 12. Despliegue 100% gratuito

### Plataformas que usamos

| Para | Plataforma | Plan gratis |
|------|-----------|-------------|
| Frontends | Vercel | 100GB bandwidth, 100 deploys/día |
| Backend principal | Koyeb | 1 instancia nano, 512MB RAM |
| Backend Go | Koyeb | igual |
| Base de datos | Supabase | 500MB DB, 2 proyectos |
| PocketBase | PocketHost | 1 instancia |
| Telegram bot | Koyeb (worker) | comparte instancia |

**Costo total para arrancar: $0**.

### CI/CD incluido

Hay 2 workflows de GitHub Actions configurados:

- `ci.yml`: corre tests automáticamente en cada push (Python, Go, frontends en paralelo)
- `deploy.yml`: cuando merges a main, despliega automáticamente a Vercel + Koyeb

Configurás los secrets una vez (`gh secret set ...`) y después es push & forget.

---

## 13. Tests automatizados (suite completa por paquete)

| Paquete | Qué validan |
|---------|-------------|
| `packages/llm` | Failover, circuit breaker, cascadas |
| `packages/agents` | Pipeline de agentes (router/researcher/analyst/writer), language helper, RAG/Web tools |
| `packages/notifications` | Dispatcher multi-canal con stubs |
| `packages/database` | Safe SQL executor, introspector |
| `packages/rag` | Sentence-aware chunking + FAISS store (upsert, search, filters, delete sin perder docs) |
| `packages/files` | Universal adapter para PDF/DOCX/CSV/XLSX/JSON/MD/HTML/TXT/... |

El número exacto se mueve cuando agregás tests; al momento de escribir esto la suite está alrededor de **66 tests verdes**. Para ver el conteo en vivo:

```bash
python -m pytest packages/llm/tests packages/rag/tests \
  packages/notifications/tests packages/database/tests \
  packages/files/tests packages/agents/tests --collect-only -q | tail -1
```

Más un script E2E (`scripts/e2e_smoke.py`) que valida health, chat streaming, agents, completion contra un backend en vivo.

### Por qué importa

Cuando agregás features nuevas o tocás algo, corrés `pytest` y sabés en 15 segundos si rompiste algo. Sin tests, cada cambio es ruleta rusa.

---

## Resumen: ¿qué tengo a disposición?

```
┌─────────────────────────────────────────────────────────┐
│                                                          │
│  CONVERSACIÓN                                            │
│  • Chat con razonamiento visible                         │
│  • Multi-agente (investigador + analista + redactor)    │
│  • Bot de Telegram                                       │
│                                                          │
│  CONOCIMIENTO                                            │
│  • RAG: tus documentos consultables                      │
│  • Conexión a tu base de datos (con NL→SQL)              │
│                                                          │
│  ANÁLISIS                                                │
│  • Resumen de CSVs                                       │
│  • Detección de anomalías (Isolation Forest, LOF)       │
│  • Geocodificación                                       │
│                                                          │
│  COMUNICACIÓN                                            │
│  • Notificaciones por Telegram + Email                   │
│  • Reportes en PDF                                       │
│                                                          │
│  OPERACIÓN                                               │
│  • 3 IAs con failover (Groq → OpenRouter → Gemini)      │
│  • Rate limiting + JWT auth opcional                     │
│  • CI/CD a producción gratis                             │
│  • Suite de tests por paquete (66+ y creciendo)          │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Próximos pasos

| Querés... | Leé... |
|-----------|--------|
| Probarlo en tu compu | [GUIA-RAPIDA.md](GUIA-RAPIDA.md) |
| Construir tu propia app | [IMPLEMENTACION.md](IMPLEMENTACION.md) |
| Subirlo a producción | [../DEPLOY.md](../DEPLOY.md) |
