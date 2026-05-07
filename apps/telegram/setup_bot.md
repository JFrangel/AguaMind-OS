# 🤖 AguaMind OS — Configuración del Bot de Telegram

## Para José F. (+57 318 293 6639)

### Paso 1 — Crear el bot con @BotFather

1. Abre Telegram → busca **@BotFather**
2. Envía `/newbot`
3. Nombre del bot: `AguaMind OS UNIAJC`
4. Username: `aguamind_uniajc_bot` (o el que esté disponible)
5. **@BotFather te dará un TOKEN** (formato: `1234567890:ABCdefGhIJKlmnOpQrStUvWxYz`)
6. Copia ese token y pégalo en `.env`:

```bash
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGhIJKlmnOpQrStUvWxYz
```

### Paso 2 — Obtener tu Chat ID

1. Busca tu bot recién creado en Telegram (@aguamind_uniajc_bot)
2. Envíale `/start`
3. Abre en tu navegador (reemplazando `<TOKEN>` con tu token):
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
4. Verás un JSON, busca `"chat": {"id": 123456789, ...}`
5. Pega ese número en `.env`:

```bash
TELEGRAM_CHAT_ID=123456789
```

### Paso 3 — Correr el bot

```bash
cd apps/telegram
python bot.py
```

### Paso 4 — Probar comandos

En Telegram envíale a tu bot:

```
/start              ← Bienvenida
/agua               ← Estado completo del sistema
/zonas              ← Consumo por zona
/kpis               ← Indicadores con semáforos
/reporte_agua       ← Reporte diario
/alerta             ← Demo: simular fuga
/riego              ← Demo: pico de riego
/normal             ← Reset a estado normal
/agente_start       ← Iniciar agente IA autónomo
/agente_stop        ← Detener agente
/agente_status      ← Ver ciclo actual
```

### Paso 5 — Recibir alertas automáticas del agente

Cuando el agente detecta una anomalía crítica, envía PUSH automáticamente al `TELEGRAM_CHAT_ID` configurado.

Para iniciar el agente desde Telegram:
```
/agente_start
```

---

## Comando rápido para conseguir tu chat ID

Después de crear el bot y mandarle `/start`, ejecuta:

```bash
# Reemplaza TOKEN por el real
curl -s "https://api.telegram.org/bot<TOKEN>/getUpdates" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for u in data.get('result', []):
    chat = u.get('message', {}).get('chat', {})
    print(f\"Chat ID: {chat.get('id')} · Tipo: {chat.get('type')} · Nombre: {chat.get('first_name', '')} {chat.get('last_name', '')}\")"
```

---

## Estructura de mensajes que recibirás

### Push de alerta crítica (cuando hay fuga)

```
🚨 AguaMind OS — UNIAJC Sede Sur
Estado: CRITICAL | 14:32

💧 Caudal: 78.4 L/min
🪣 Tanque A: 31.2%  |  Tanque B: 65.0%
📊 IEH: 72%  TPP: 28%
🔬 Turbidez: 1.8 NTU  |  Freático: 6.2 m

🚨 Alertas críticas:
  • Vibración anómala detectada en tuberías
  • TPP crítica: 28% de pérdidas
  • Posible fuga en red de distribución

→ Inspección inmediata del tramo afectado
```

### Reporte diario automático (18:00)

```
📊 AguaMind OS — Reporte Diario
07/05/2026

✓ Consumo total: 45,367 L
⚠ Pérdidas: 9,073 L (20%)
📈 Eficiencia: 80.0%

KPIs del día:
  IEH: 80% (warning)
  TPP: 20% (warning)
  CPE: 14.04 L/est (ok)

Hora pico: 09:30 (5,420 L)

[Ver dashboard →]
```
