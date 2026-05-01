# Despliegue — AgentOS a producción free-tier

Guía completa para llevar AgentOS de localhost a producción 100% gratuita: Supabase + Koyeb + Vercel + PocketHost.

**Tiempo total**: ~30 minutos para tener todo en línea.

---

## Mapa de servicios

| Componente | Plataforma | URL final | Free tier |
|-----------|------------|-----------|-----------|
| `services/api` (FastAPI) | Koyeb | `https://agentos-api.koyeb.app` | 1 instancia nano (512MB) |
| `apps/api-go` (Go Gin) | Koyeb | `https://agentos-go.koyeb.app` | 1 instancia nano |
| `apps/telegram` (worker) | Koyeb | sin URL pública | 1 worker nano |
| `apps/web-svelte` | Vercel | `https://agentos-svelte.vercel.app` | 100GB / 100 deploys/día |
| `apps/web-next` | Vercel | `https://agentos-next.vercel.app` | igual |
| `apps/web-vue` | Vercel o Netlify | `https://agentos-vue.vercel.app` | igual |
| `apps/pocketbase` | PocketHost | `https://<name>.pockethost.io` | 1 instancia |
| Postgres + pgvector + PostGIS | Supabase | `https://<ref>.supabase.co` | 500MB DB, 2 proyectos |

---

## Paso 1 — Crear los recursos (una vez por proyecto)

### 1.1 Supabase

1. Crear proyecto en <https://supabase.com>
2. Anotar de **Project Settings → API**:
   - `Project URL` → será `SUPABASE_URL`
   - `anon public key` → `SUPABASE_ANON_KEY`
   - `service_role key` → `SUPABASE_SERVICE_KEY` (¡no exponer al frontend!)
   - `JWT Secret` (en **API → JWT Settings**) → `SUPABASE_JWT_SECRET`
3. Anotar la cadena de conexión (Settings → Database → Connection string → URI) → `DATABASE_URL`
4. Aplicar migraciones:
   ```bash
   # Opción A — Supabase CLI
   supabase link --project-ref <ref>
   supabase db push

   # Opción B — SQL editor
   # Pegá el contenido de cada archivo en supabase/migrations/ en orden
   ```

### 1.2 Koyeb (3 apps)

1. Crear cuenta en <https://www.koyeb.com>
2. Conectar tu GitHub repo
3. **Crear App `agentos-api`**:
   - Source: GitHub repo
   - Builder: Dockerfile en `services/api/Dockerfile`
   - Instance: Nano (free)
   - Port: 8000
   - Health check: GET `/health`
   - Variables de entorno (todas las que aparecen en `services/api/koyeb.yaml`):
     ```
     ENVIRONMENT=production
     GROQ_API_KEY=...
     OPENROUTER_API_KEY=...
     GEMINI_API_KEY=...
     SUPABASE_URL=...
     SUPABASE_SERVICE_KEY=...
     DATABASE_URL=...
     VECTOR_BACKEND=pgvector
     AUTH_REQUIRED=false
     RATE_LIMIT_PER_MINUTE=120
     ```
4. **Crear App `agentos-go`**: Dockerfile en `apps/api-go/Dockerfile`, port 8080, env: `BACKEND_URL=https://agentos-api.koyeb.app`, `SUPABASE_JWT_SECRET=...`
5. **Crear App `agentos-telegram`**: tipo *worker*, Dockerfile en `apps/telegram/Dockerfile`, env: `TELEGRAM_BOT_TOKEN=...`, `BACKEND_URL=https://agentos-api.koyeb.app`
6. Anotar de **Account Settings → API**:
   - Personal Access Token → `KOYEB_TOKEN`
   - Cada App ID/Name → `KOYEB_API_NAME`, `KOYEB_GO_NAME`, `KOYEB_TELEGRAM_NAME`

### 1.3 Vercel (3 frontends)

1. Crear cuenta en <https://vercel.com>
2. Importar el repo y crear **3 proyectos** (uno por frontend):
   - **agentos-svelte** — root: `apps/web-svelte`
   - **agentos-next** — root: `apps/web-next`
   - **agentos-vue** — root: `apps/web-vue`
3. En cada uno, configurar Environment Variables:
   ```
   BACKEND_URL=https://agentos-api.koyeb.app
   ```
4. Anotar de **Account Settings → Tokens**:
   - Crear un token → `VERCEL_TOKEN`
   - **Account Settings** → Team ID o User ID → `VERCEL_ORG_ID`
   - En cada proyecto → **Settings → General** → Project ID → `VERCEL_SVELTE_PROJECT_ID`, etc.

### 1.4 PocketHost (opcional)

1. <https://pockethost.io> → New instance → anotar URL `https://<name>.pockethost.io`
2. Subir vía panel: `apps/pocketbase/pb_migrations/*.js` y `apps/pocketbase/pb_hooks/*.js`
3. Reiniciar la instancia → migraciones se aplican

### 1.5 Telegram bot (opcional)

1. Hablar con `@BotFather` en Telegram → `/newbot` → seguir prompts
2. Anotar el token → `TELEGRAM_BOT_TOKEN`

---

## Paso 2 — Configurar GitHub Secrets y Variables

GitHub separa **secrets** (encriptados, no se ven) y **variables** (visibles, no sensibles). Usá `gh` CLI para hacerlo en una sola sesión:

```bash
# Login (una vez)
gh auth login

# --- Secrets (encriptados) ---
gh secret set KOYEB_TOKEN --body "<koyeb-pat>"
gh secret set VERCEL_TOKEN --body "<vercel-token>"
gh secret set VERCEL_ORG_ID --body "<vercel-org-id>"

# --- Variables (visibles) ---
gh variable set KOYEB_API_NAME       --body "agentos-api"
gh variable set KOYEB_GO_NAME        --body "agentos-go"
gh variable set KOYEB_TELEGRAM_NAME  --body "agentos-telegram"
gh variable set VERCEL_SVELTE_PROJECT_ID --body "prj_..."
gh variable set VERCEL_NEXT_PROJECT_ID   --body "prj_..."
gh variable set VERCEL_VUE_PROJECT_ID    --body "prj_..."
```

Verificá:
```bash
gh secret list
gh variable list
```

> **Importante**: las API keys de LLMs (`GROQ_API_KEY`, etc.) **NO van en GitHub** — viven en Koyeb (donde corre la API). El workflow solo dispara redeploys; las apps leen sus propios env vars en runtime.

---

## Paso 3 — Deploy

### Automático (recomendado)

Cualquier push a `main` dispara `.github/workflows/deploy.yml`:

```bash
git push origin main
gh run watch  # ver progreso en CLI
```

El workflow tiene 4 jobs paralelos:
- `api` → redeploy de Koyeb FastAPI
- `go-api` → redeploy de Koyeb Go
- `vercel-svelte` → build + deploy a Vercel
- `vercel-next` → build + deploy a Vercel

Cada job tiene `if: vars.<NAME> != ''` así que si no configuraste un servicio, ese job se skipea automáticamente.

### Manual

```bash
# Disparar workflow sin push
gh workflow run deploy.yml

# Ver logs en vivo
gh run watch
```

### Por servicio individual

```bash
# Solo redeploy del API Python
curl -X POST \
  -H "Authorization: Bearer $KOYEB_TOKEN" \
  https://app.koyeb.com/v1/apps/agentos-api/redeploy

# Solo deploy del frontend SvelteKit
cd apps/web-svelte
vercel --prod --token=$VERCEL_TOKEN
```

---

## Paso 4 — Verificar deploy

```bash
# Health del backend Python
curl https://agentos-api.koyeb.app/health
# → {"status":"ok","providers":{...}}

# Health del backend Go
curl https://agentos-go.koyeb.app/health
# → {"status":"ok","service":"agentos-go",...}

# Smoke test E2E contra prod
BACKEND_URL=https://agentos-api.koyeb.app python scripts/e2e_smoke.py
# → 4/4 checks passed.

# Frontends
open https://agentos-svelte.vercel.app
open https://agentos-next.vercel.app
```

---

## Rollback

### Vercel
Cada deploy es inmutable y queda en el historial:
```bash
vercel ls
vercel rollback <deployment-url>
```
O desde el dashboard → Deployments → click en la versión anterior → "Promote to Production".

### Koyeb
```bash
# Ver historial
curl -H "Authorization: Bearer $KOYEB_TOKEN" \
  https://app.koyeb.com/v1/apps/agentos-api/deployments

# Hacer rollback a un deployment específico
curl -X POST -H "Authorization: Bearer $KOYEB_TOKEN" \
  https://app.koyeb.com/v1/apps/agentos-api/deployments/<id>/promote
```
O desde el dashboard → Activity → Redeploy en una entry anterior.

### Supabase migrations
```bash
supabase migration list
supabase db reset --linked   # destructivo, solo dev
```
Para rollback de prod: revertir la migración y aplicar una nueva con la operación inversa.

---

## Costos en free tier (verificado mayo 2026)

| Plataforma | Límite | Cuándo te golpea |
|-----------|--------|------------------|
| Koyeb nano | 512MB RAM, sleep tras 15min sin tráfico | Si la API se duerme, primer request demora ~5s en cold-start |
| Vercel Hobby | 100GB bandwidth, 100 deploys/día | Casi imposible llegar en demo |
| Supabase | 500MB DB, 2 proyectos, RLS limitado | Si guardás todos los embeddings: usar pgvector con índice IVFFLAT y `lists=100` para mantener < 100MB |
| Groq | RPM variable según modelo | Failover a OpenRouter cuando se rate-limita |
| OpenRouter | El default `:free` no consume créditos | Si querés un modelo pago, sobreescribí `MODEL_OPENROUTER` y empieza a debitar |
| Gemini | 15 RPM en gemini-2.5-flash free | Failover desde Groq/OpenRouter cubre |
| PocketHost | 1 instancia, sin límite estricto | — |

---

## Troubleshooting

| Síntoma | Causa probable | Fix |
|---------|----------------|-----|
| `health` devuelve `degraded` con todos los providers `available: false` | Las keys no están en Koyeb env vars | Settings → Environment variables → agregar y redeploy |
| `health` 502 Bad Gateway | El proceso uvicorn murió por OOM (sentence-transformers carga ~200MB) | Pasar a Koyeb Standard ($5/mes) o cambiar `VECTOR_BACKEND=pgvector` y embeddings via Gemini |
| Vercel build falla con "Cannot find module @agentos/shared-types" | El root del proyecto está mal | Project Settings → General → Root Directory = `apps/web-svelte` (con esa ruta exacta) y `Build command` = el de `vercel.json` |
| SSE no llega al frontend en prod | Algún proxy de la stack está bufferando | Confirmar que `X-Accel-Buffering: no` viaja en la respuesta. Vercel y Koyeb lo respetan |
| Telegram bot no responde | `BACKEND_URL` apunta a localhost | En Koyeb env vars: `BACKEND_URL=https://agentos-api.koyeb.app` (no `http://localhost:8000`) |
| `agents/complete` 503 `all_providers_failed` | Los 3 providers están caídos o sin keys | Revisar `/health` para ver cuál y por qué |

---

## Checklist final pre-demo

- [ ] `curl https://agentos-api.koyeb.app/health` → `status: ok`
- [ ] `BACKEND_URL=... python scripts/e2e_smoke.py` → `4/4 checks passed`
- [ ] Abrir el frontend principal en incógnito → enviar mensaje → ver streaming
- [ ] Forzar fallo de Groq (key inválida temporalmente) → ver failover automático en logs
- [ ] Telegram `/start` → `/ask hola` → recibir respuesta
- [ ] Subir un CSV en `/data/upload` → ver summary
- [ ] Generar un PDF en `/reports/generate` → descargarlo y abrirlo
