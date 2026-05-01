# Guía Rápida de Uso

Levantá AgentOS en tu compu y probá las funciones principales en menos de 30 minutos. **Sin tarjeta de crédito**, todo gratis.

---

## Lo que vas a necesitar

Antes de empezar, asegurate de tener instalado:

- **Node.js 20 o más nuevo** — para los frontends. Bajalo de [nodejs.org](https://nodejs.org).
- **Python 3.12 o más nuevo** — para el backend. Bajalo de [python.org](https://python.org).
- **pnpm** — gestor de paquetes para Node. Una vez tenés Node:
  ```bash
  npm install -g pnpm
  ```
- **Git** — para clonar el repositorio.

Y al menos **una clave de API gratuita** de cualquiera de estos:

| Proveedor | Dónde sacar la clave | Costo |
|-----------|---------------------|-------|
| Groq | <https://console.groq.com/keys> | Gratis, sin tarjeta |
| Gemini | <https://aistudio.google.com/apikey> | Gratis, 15 RPM |
| OpenRouter | <https://openrouter.ai/keys> | Gratis con suffix `:free` |

**Consejo**: sacá las 3 si podés. Eso te da el failover completo. Pero con una sola alcanza para arrancar.

---

## Paso 1: Clonar y configurar

```bash
# 1. Clonar el repo (ajustá la URL a tu fork)
git clone https://github.com/tu-usuario/agentos.git
cd agentos

# 2. Copiar el archivo de variables de entorno
cp .env.example .env

# 3. Abrí .env con tu editor y pegá tu(s) clave(s) de API
#    Solo modificá las que tengas:
#    GROQ_API_KEY=gsk_...
#    GEMINI_API_KEY=AIza...
#    OPENROUTER_API_KEY=sk-or-...
```

⚠️ **Importante**: el archivo `.env` está en `.gitignore`, así que tus claves nunca se suben a Git. Si las pegás en otro archivo, asegurate de no commitearlas.

---

## Paso 2: Instalar dependencias

```bash
# Frontend (instala los 3 frontends + tipos compartidos)
pnpm install

# Backend Python (instala todos los paquetes en modo "editable")
pip install -e packages/llm
pip install -e packages/agents
pip install -e packages/rag
pip install -e packages/data
pip install -e packages/ml
pip install -e packages/geo
pip install -e packages/reports
pip install -e packages/notifications
pip install -e packages/database
pip install -e services/api
```

**Modo editable** (`-e`) significa que cuando modifiques el código de un paquete, los cambios se ven al instante sin reinstalar. Útil para desarrollo.

> ⏱ Esto puede tardar 3-5 minutos la primera vez. Sentence-transformers descarga un modelo de ~90MB.

---

## Paso 3: Arrancar el backend

```bash
cd services/api
uvicorn app.main:app --reload
```

Deberías ver:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

**Verifica que arrancó bien** abriendo otra terminal y corriendo:

```bash
curl http://localhost:8000/health
```

Si ves algo como esto, está todo bien:

```json
{
  "status": "ok",
  "providers": {
    "groq":       {"registered": true, "available": true, "failures": 0},
    "openrouter": {"registered": true, "available": true, "failures": 0},
    "gemini":     {"registered": true, "available": true, "failures": 0}
  }
}
```

`status: "ok"` = al menos un proveedor está UP. Si dice `degraded`, algunos están caídos pero la cascade sigue funcionando con los que estén disponibles.

---

## Paso 4: Arrancar el frontend (elegí uno)

En otra terminal:

```bash
# Opción A: SvelteKit (más liviano)
pnpm dev:svelte
# → abrí http://localhost:5173

# Opción B: Next.js (React)
pnpm dev:next
# → abrí http://localhost:3000

# Opción C: Nuxt 3 (Vue)
pnpm dev:vue
# → abrí http://localhost:3001
```

Vas a ver una interfaz de chat. En la esquina superior derecha hay un indicador del estado de los proveedores (debería decir "ok" en verde).

---

## Paso 5: Tu primera conversación

En la interfaz del navegador:

1. Hacé click en uno de los presets (por ejemplo "Research a topic")
2. O escribí tu propia pregunta en el campo inferior
3. Apretá Enter

Vas a ver:
- A la izquierda, el chat con la respuesta apareciendo carácter por carácter
- A la derecha (en pantalla grande), el "agent trace" mostrando los pasos del agente en vivo:
  - `router: classifying intent...`
  - `responder: generating response...`
  - tokens fluyendo

---

## Paso 6: Probar las funciones más interesantes

### A) Búsqueda en documentos (RAG)

Probá subir un documento y preguntar sobre él.

```bash
# Subí cualquier .txt (puede ser un README, manual, etc.)
curl -X POST http://localhost:8000/rag/ingest \
  -F "file=@README.md"

# → {"data": {"chunks_created": 8}, "error": null}
```

Ahora preguntá:

```bash
curl -X POST http://localhost:8000/rag/search \
  -H "Content-Type: application/json" \
  -d '{"query": "¿qué es AgentOS?", "top_k": 3}'
```

Te devuelve los 3 fragmentos más relevantes con su score de similaridad.

### B) Conectar tu base de datos

Si tenés una base SQLite, MySQL o PostgreSQL, podés conectarla.

**Ejemplo con SQLite** (lo más fácil para probar):

1. Crear una BD de prueba:
   ```python
   # Guardar como create_test_db.py y ejecutar
   import sqlite3
   conn = sqlite3.connect('mi_test.db')
   conn.execute('CREATE TABLE clientes (id INTEGER PRIMARY KEY, nombre TEXT, edad INTEGER)')
   conn.executemany(
       'INSERT INTO clientes (nombre, edad) VALUES (?, ?)',
       [('Ana', 28), ('Luis', 35), ('María', 42)]
   )
   conn.commit()
   ```

2. Agregar al `.env`:
   ```env
   DATABASE_URL_USER=sqlite+aiosqlite:///./mi_test.db
   ```

3. Reiniciar uvicorn (Ctrl+C y arrancar de nuevo)

4. Ver el esquema:
   ```bash
   curl http://localhost:8000/database/schema
   ```

5. Hacer una pregunta en español:
   ```bash
   curl -X POST http://localhost:8000/database/nl-query \
     -H "Content-Type: application/json" \
     -d '{"question": "¿Cuántos clientes tienen más de 30 años?"}'
   ```

Te va a generar el SQL automáticamente y devolver el resultado:
```json
{
  "data": {
    "sql": "SELECT COUNT(*) FROM clientes WHERE edad > 30",
    "rows": [{"COUNT(*)": 2}]
  }
}
```

### C) Configurar notificaciones

**Telegram**:

1. Abrí Telegram → buscá `@BotFather` → `/newbot` → seguí los prompts
2. Te da un token tipo `123456789:ABC-DEF...`
3. Para saber tu chat ID: hablá con `@userinfobot` y te dice tu ID
4. Agregá al `.env`:
   ```env
   TELEGRAM_BOT_TOKEN=123456789:ABC-DEF...
   TELEGRAM_CHAT_IDS=tu-chat-id
   ```
5. Reiniciá uvicorn
6. Probá:
   ```bash
   curl -X POST http://localhost:8000/notify/send \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Hola desde AgentOS",
       "body": "Esta notificación es de prueba",
       "severity": "info"
     }'
   ```

Deberías recibir el mensaje en Telegram en menos de 2 segundos.

**Email** (con Gmail como ejemplo):

1. Activar 2FA en tu cuenta de Google
2. Ir a <https://myaccount.google.com/apppasswords> → crear una "app password"
3. Agregar al `.env`:
   ```env
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=465
   SMTP_USER=tu-email@gmail.com
   SMTP_PASSWORD=la-app-password-que-acabás-de-crear
   SMTP_FROM=tu-email@gmail.com
   EMAIL_RECIPIENTS=destino@ejemplo.com
   ```
4. Reiniciá uvicorn
5. La misma curl de arriba ahora también te manda email

---

## Paso 7: Verificar que todo funciona (test E2E)

```bash
python scripts/e2e_smoke.py
```

Deberías ver:

```
AgentOS E2E smoke against http://localhost:8000

  [PASS] health                       2062 ms  status=ok providers=['groq', 'openrouter', 'gemini']
  [PASS] chat/stream                  2672 ms  events=10 got_tokens=True
  [PASS] agents/run (graph)           2703 ms  events=5 nodes=['responder', 'router']
  [PASS] agents/complete              2406 ms  provider=groq model=llama-3.3-70b-versatile

4/4 checks passed.
```

Si los 4 pasan, todo está bien conectado.

---

## Cosas opcionales (cuando ya estás cómodo)

### Levantar también el backend Go

El backend Python tiene todo. El backend Go es para casos donde necesitás latencia mínima en algunos endpoints (por ejemplo, si tu app móvil pega 1000 veces por segundo).

```bash
cd apps/api-go
go run cmd/server/main.go
# → http://localhost:8080
```

Por defecto, el Go API es un proxy del Python. Si activás `LLM_DIRECT=true` en `.env`, llama directo a Groq sin pasar por Python — más rápido pero pierde el failover automático.

### Levantar el bot de Telegram

```bash
cd apps/telegram
pip install -e .
python bot.py
```

Mientras corra, podés mandarle mensajes al bot que creaste con `@BotFather` y te responde usando AgentOS por debajo.

### Levantar Postgres con pgvector + PostGIS local

Si querés probar el RAG con persistencia (que no se pierdan los documentos al reiniciar):

```bash
docker compose up -d supabase-db
```

Esto levanta Postgres con pgvector y PostGIS instalados. Luego:

```env
# en .env
VECTOR_BACKEND=pgvector
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/agentos
```

Reiniciar uvicorn. Ahora los documentos persisten entre reinicios.

---

## Cuando algo no funciona

### El backend no arranca

**Síntoma**: `uvicorn` falla al iniciar.

**Causa típica**: faltan dependencias.

**Fix**: revisá que hayas corrido todos los `pip install -e packages/*`. Si todavía falla, decime qué error tira y vemos.

### El health dice "down"

**Síntoma**: `/health` devuelve `status: "down"` o todos los providers en `available: false`.

**Causa típica**: las claves de API no están bien cargadas.

**Fix**:
1. Verificá que `.env` esté en la raíz del proyecto (no dentro de `services/api/`).
2. Verificá que las claves no tengan espacios extra ni comillas alrededor.
3. Reiniciá uvicorn.

### El chat no responde

**Síntoma**: la pantalla queda con los puntos animados pero nunca llega texto.

**Causa típica**: el frontend no llega al backend.

**Fix**:
1. Abrí la consola del navegador (F12) → pestaña Network → ver si la request a `/api/chat` da 200 o 5xx.
2. Si da 5xx, mirá los logs de uvicorn — ahí está el error real.
3. Si da pending eternamente, probablemente el backend murió o cambió de puerto.

### "Cannot find module @agentos/shared-types"

**Síntoma**: el frontend no compila.

**Fix**: corré `pnpm install` desde la raíz (no desde `apps/web-svelte/`).

### WeasyPrint falla en Windows

**Síntoma**: error sobre `libgobject-2.0-0` al generar PDFs.

**Causa**: WeasyPrint requiere bibliotecas GTK que en Windows hay que instalar aparte.

**Fix opciones**:
- Opción A (rápida): no usar PDFs en local. Funciona en producción (Docker) sin problema.
- Opción B: instalar GTK3 desde <https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases>.

### "EADDRINUSE: address already in use :::8000"

**Síntoma**: uvicorn dice que el puerto 8000 está ocupado.

**Fix**: ya hay un proceso usando ese puerto. Para matarlo:

```bash
# Linux/Mac
lsof -ti:8000 | xargs kill -9

# Windows (PowerShell)
netstat -ano | findstr :8000
# Anotá el PID al final, luego:
taskkill /F /PID <pid>
```

---

## Comandos útiles para tener a mano

```bash
# Ver logs del backend en vivo
tail -f services/api/logs/*.log    # si los redirigís a archivo

# Correr todos los tests
python -m pytest packages/llm/tests packages/agents/tests/test_graph_runner.py packages/notifications/tests packages/database/tests packages/rag/tests -q

# Limpiar caches
pnpm clean

# Ver qué proceso usa el puerto 8000
netstat -ano | grep :8000  # Windows con git bash
lsof -i :8000              # Linux/Mac

# Smoke test contra producción
BACKEND_URL=https://agentos-api.koyeb.app python scripts/e2e_smoke.py
```

---

## Próximos pasos

Ya tenés AgentOS corriendo. Ahora:

| Querés... | Leé... |
|-----------|--------|
| Construir tu propia app encima | [IMPLEMENTACION.md](IMPLEMENTACION.md) |
| Ver todo lo que se puede hacer | [FUNCIONALIDADES.md](FUNCIONALIDADES.md) |
| Subirlo a internet (gratis) | [../DEPLOY.md](../DEPLOY.md) |
| Detalles técnicos profundos (en inglés) | [../USAGE.md](../USAGE.md) |

---

## Resumen rápido (cheat sheet)

```bash
# Setup (una vez)
git clone <repo> && cd agentos
cp .env.example .env  # editá con tus claves
pnpm install
pip install -e packages/llm packages/agents packages/rag packages/data \
            packages/ml packages/geo packages/reports \
            packages/notifications packages/database services/api

# Cada día
cd services/api && uvicorn app.main:app --reload &  # terminal 1
pnpm dev:svelte                                      # terminal 2
# → abrí http://localhost:5173

# Verificar que todo funciona
python scripts/e2e_smoke.py
```
