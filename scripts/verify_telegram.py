"""
HidroTech — verificador de credenciales de Telegram.

Uso:
    python scripts/verify_telegram.py

Lee bot_secrets.json en la raíz del repo, valida formato, manda un mensaje
de prueba al chat configurado y reporta si el flujo end-to-end funciona.
"""
from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path


PLACEHOLDERS = {
    "", "REEMPLAZAR_CON_TOKEN_DE_BOTFATHER",
    "REEMPLAZAR_CON_TU_CHAT_ID", "changeme",
}


def find_secrets() -> Path | None:
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        candidate = parent / "bot_secrets.json"
        if candidate.is_file():
            return candidate
    return None


def main() -> int:
    path = find_secrets()
    if not path:
        print("[ERROR] bot_secrets.json no encontrado en la raíz del repo.")
        return 1
    print(f"[ok] bot_secrets.json hallado: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[ERROR] No pude parsear el JSON: {e}")
        return 1

    token = str(data.get("TELEGRAM_BOT_TOKEN", "")).strip()
    chat_id = str(data.get("TELEGRAM_CHAT_ID", "")).strip()

    if token in PLACEHOLDERS:
        print("[ERROR] TELEGRAM_BOT_TOKEN sigue siendo el placeholder. Pegá el token real de @BotFather.")
        return 1
    if chat_id in PLACEHOLDERS:
        print("[ERROR] TELEGRAM_CHAT_ID sigue siendo el placeholder. Conseguilo en /getUpdates después de mandarle /start al bot.")
        return 1

    print(f"[ok] Token leído (longitud {len(token)}, formato {'OK' if ':' in token else 'sospechoso'})")
    print(f"[ok] Chat ID leído: {chat_id}")

    # Probar el endpoint de Telegram directamente
    payload = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": "✅ *HidroTech — Credenciales validadas*\n\nEl bot puede enviarte mensajes desde esta PC (o cualquier otra que tenga `bot_secrets.json`).",
        "parse_mode": "Markdown",
    }).encode()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        req = urllib.request.Request(url, data=payload, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            if body.get("ok"):
                print("[ok] Mensaje enviado. Revisá tu Telegram — debería estar el mensaje de validación.")
                return 0
            print(f"[ERROR] Telegram respondió ok=false: {body}")
            return 1
    except Exception as e:
        print(f"[ERROR] Falló la conexión a la API de Telegram: {e}")
        print("       Verificá: 1) Token correcto, 2) chat_id correcto, 3) le mandaste /start al bot al menos una vez.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
