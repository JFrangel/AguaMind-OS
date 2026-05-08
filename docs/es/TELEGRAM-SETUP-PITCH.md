# Telegram + Camaleón OS · setup en 3 minutos para el pitch

> Guía paso a paso para activar el flujo bidireccional dashboard ↔ Telegram
> antes del pitch. Si todo está listo, durante la demo al jurado:
>
> 1. Tu clic en el dashboard → llega un mensaje a tu Telegram (con botones)
> 2. Tu clic en el botón inline de Telegram → ejecuta una acción real en el sistema
> 3. El operador on-call también recibe alertas críticas sin abrir el dashboard

---

## Paso 1 · Crear el bot (1 min · solo tú puedes hacerlo)

1. Abrí Telegram y buscá el contacto **@BotFather** (oficial · check azul).
2. Mandale `/newbot`
3. Te pide nombre. Escribí: `Camaleón UNIAJC`
4. Te pide username (debe terminar en `bot`). Escribí: `camaleon_uniajc_bot` (o el que esté libre).
5. BotFather te devuelve un mensaje con un **token** del estilo:
   ```
   1234567890:AAFn-XYZ-aBcDeFgHiJkLmNoPqRsTuVwX
   ```
6. **Copia ese token** — vas a pegarlo en el siguiente paso.

## Paso 2 · Saber tu chat_id (30 seg)

1. Abrí tu bot recién creado en Telegram (busca el username, click en el contacto).
2. Mandale `/start` (cualquier mensaje sirve).
3. En tu navegador andá a:
   ```
   https://api.telegram.org/bot<TU-TOKEN>/getUpdates
   ```
   Reemplazá `<TU-TOKEN>` con el que copiaste.
4. Vas a ver un JSON. Buscá `"chat":{"id": ...}`. Ese número es tu **chat_id** (puede ser positivo si es tu cuenta personal, negativo si es un grupo).

> Atajo si está corriendo el backend: `python apps/telegram/get_chat_id.py` te lo imprime después de mandarle un mensaje al bot.

## Paso 3 · Pegar credenciales en `bot_secrets.json` (15 seg)

Abrí **`D:\descargas\Camaleón OS\bot_secrets.json`** (en la raíz del repo) y reemplazá:

```json
{
  "TELEGRAM_BOT_TOKEN": "1234567890:AAFn-XYZ-aBcDeFgHiJkLmNoPqRsTuVwX",
  "TELEGRAM_CHAT_ID": "123456789",
  "BACKEND_URL": "http://localhost:8000"
}
```

> **¿Por qué `bot_secrets.json` y no `.env`?** Más simple de copiar entre PCs (un solo archivo JSON), independiente del shell, y leído tanto por el backend (FastAPI) como por el bot (apps/telegram). Está en `.gitignore` — no se commitea.

> **Para correr en otra PC**: copiá únicamente `bot_secrets.json` a la misma ruta del repo en el otro equipo. Listo.

### Verificar de inmediato (10 seg)

```bash
python scripts/verify_telegram.py
```

Si todo está bien, vas a recibir en Telegram un mensaje "✅ *Credenciales validadas*" y el script imprime `[ok]` en cada paso. Si algún campo sigue siendo placeholder, el script te dice exactamente qué falta.

## Paso 4 · Reiniciar el backend (10 seg)

```bash
# si ya está corriendo, mátalo primero
netstat -ano | grep :8000
# luego en una terminal nueva:
cd "D:\descargas\Camaleón OS\services\api"
python demo_server.py
```

## Paso 5 · Probar el envío (10 seg)

Opción A · directo (no requiere backend levantado):
```bash
python scripts/verify_telegram.py
```

Opción B · vía endpoint del backend (requiere que el backend esté corriendo):
```bash
curl http://localhost:8000/water/notify/test
```

Si configuraste bien las credenciales, recibís en Telegram:

> 🔔 **Camaleón OS — Prueba de conexión**
> Hora: `12:34:56`
> Si recibís este mensaje, las notificaciones están operativas.

Si ves `"sent": false, "reason": "no_token"` → revisá el `.env` y reiniciá el backend.

## Paso 6 · Arrancar el bot (en otra terminal · 20 seg)

```bash
cd "D:\descargas\Camaleón OS\apps\telegram"
pip install -e .
python bot.py
```

El bot se queda escuchando. Vas a ver: `Application started`.

## Paso 7 · Probar el flujo completo (20 seg)

### Flujo 1 — Dashboard → Telegram (notificación de ciclo)
1. En el dashboard, tab **Inteligencia**, click **"Ejecutar ciclo único"**
2. En Telegram recibís: 🚨 **Camaleón OS — Agente IA · Ciclo #N · decisión critical**
3. Mensaje incluye 2 botones inline: "📊 Ver dashboard" y "🔄 Otro ciclo"

### Flujo 2 — Dashboard → Telegram → Backend (sugerencia de fenómeno)
1. En el dashboard, tab **Inteligencia**, en una card de fenómeno (ej. Sequía/El Niño) click **"✈ Avisar operador"**
2. En Telegram recibís: 🌵 **Alerta de fenómeno · Sequía/El Niño · pronóstico 30 días + sugerencia del agente**
3. Mensaje incluye 3 botones inline: "✅ Activar plan" · "❌ Ignorar" · "📊 Ver evidencia"
4. Click en "✅ Activar plan" → el bot llama al backend, ejecuta la mitigación, edita el mensaje con la confirmación del impacto (litros ahorrados, COP, OT generada)

### Flujo 3 — Dashboard → Backend → Telegram (mitigación ejecutada)
1. En el dashboard, click **"Activar"** directamente en una card de fenómeno
2. El backend ejecuta la mitigación
3. En Telegram recibís: ✅ **Mitigación ejecutada · trigger drought_mode · 10,400 L ahorrados · $36,400 COP · OT-XXXXX**

---

## Para el pitch · guion de la demo

> *"Voy a mostrarles un flujo crítico: la coordinación dashboard-operador-backend en tiempo real."*

1. **Setup**: dashboard abierto en proyector + Telegram en tu celular conectado al proyector con espejo.
2. Click en "Ejecutar ciclo único" → vibra tu celular con la alerta. Mostrar al jurado.
3. Click en "✈ Avisar operador" en una card de fenómeno → en Telegram aparece la alerta con botones.
4. **Click el botón inline "✅ Activar plan"** → el bot edita el mensaje en vivo mostrando: "Modo SEQUÍA ACTIVADO · 10,400 L · $36,400 · CO₂ 4.78 kg".
5. Volver al dashboard → la electroválvula EV-RC1 aparece como CLOSED. La acción quedó grabada.

> *"Acabo de mostrar 5 segundos de respuesta autónoma del sistema, validada por un humano on-call desde Telegram, con audit trail completo. Eso es lo que el reto pidió: agente que toma decisiones autónomas con supervisión humana cuando es crítico."*

---

## Troubleshooting rápido

| Problema | Solución |
|----------|----------|
| `"sent": false, "reason": "no_token"` | `bot_secrets.json` tiene el placeholder. Reemplazá con el token real y reiniciá el backend. |
| `"sent": false, "reason": "no_chat_id"` | Falta `TELEGRAM_CHAT_ID` en `bot_secrets.json`. Mandale `/start` al bot y volvé a `getUpdates`. |
| Mensaje llega pero los botones no hacen nada | El bot (`apps/telegram/bot.py`) no está corriendo. Iniciálo en una terminal aparte. |
| Click en "Activar plan" da error | El bot no puede llegar al backend. Verificá que el backend esté en `:8000` y `BACKEND_URL=http://localhost:8000` en el entorno donde corre el bot. |
| El mensaje sale con caracteres raros | Es Markdown — verificá que `parse_mode` esté en "Markdown" en el código. |

---

## Endpoints disponibles para integrar en otros lugares

| Endpoint | Método | Body | Cuándo se llama |
|----------|--------|------|------------------|
| `/water/notify/test` | GET | — | Test inicial de conexión |
| `/water/notify/agent_cycle` | POST | `{cycle, decision, issues}` | Tras ejecutar 1 ciclo del agente |
| `/water/notify/phenomenon` | POST | `{phenomenon, severity, forecast_days, suggestion}` | Cuando el operador quiere validación humana |
| `/water/notify/mitigation_executed` | POST | `{trigger, impact_l, cop_saved, summary, ot_id}` | Tras ejecutar una mitigación automática |
| `/water/notify/callback` | POST | `{callback_data}` | Lo invoca el bot al recibir un click inline |

---

*v1.0 · 8 de mayo de 2026 · Camaleón OS · UNIAJC Hackathon*
