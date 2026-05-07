#!/usr/bin/env python3
"""
AguaMind OS — Helper para obtener tu Chat ID de Telegram.

Uso:
    1. Crea tu bot con @BotFather y guarda el TOKEN
    2. Envía /start a tu bot recién creado
    3. Ejecuta:  python apps/telegram/get_chat_id.py <TOKEN>
       o pon TELEGRAM_BOT_TOKEN en .env y ejecuta sin args
"""

import os
import sys
import json
from pathlib import Path

import urllib.request
import urllib.error


def load_env() -> dict:
    """Carga variables del .env más cercano."""
    env = {}
    here = Path(__file__).resolve()
    for parent in here.parents:
        envfile = parent / ".env"
        if envfile.is_file():
            for line in envfile.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip().strip("'\"")
            break
    return env


def main():
    token = sys.argv[1] if len(sys.argv) > 1 else None
    if not token:
        env = load_env()
        token = env.get("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")

    if not token:
        print("✗ Falta el token. Uso:")
        print("    python apps/telegram/get_chat_id.py <TOKEN>")
        print("  o pon TELEGRAM_BOT_TOKEN en .env")
        sys.exit(1)

    url = f"https://api.telegram.org/bot{token}/getUpdates"
    print(f"⚙ Consultando {url}…")

    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f"✗ HTTP {e.code}: {e.reason}")
        if e.code == 401:
            print("  → Token inválido. Verifica con @BotFather.")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

    if not data.get("ok"):
        print(f"✗ API error: {data}")
        sys.exit(1)

    updates = data.get("result", [])
    if not updates:
        print("⚠ No hay mensajes recientes.")
        print("  → Envía /start a tu bot en Telegram primero.")
        sys.exit(0)

    seen_chats = {}
    for u in updates:
        msg = u.get("message") or u.get("channel_post") or {}
        chat = msg.get("chat", {})
        if chat.get("id") and chat.get("id") not in seen_chats:
            seen_chats[chat["id"]] = chat

    print(f"\n✓ Encontrados {len(seen_chats)} chat(s):\n")
    for chat_id, chat in seen_chats.items():
        name = " ".join(filter(None, [chat.get("first_name"), chat.get("last_name")]))
        print(f"  Chat ID: {chat_id}")
        print(f"     Tipo: {chat.get('type')}")
        print(f"   Nombre: {name or '(sin nombre)'}")
        if chat.get("username"):
            print(f"     User: @{chat.get('username')}")
        print()

    if len(seen_chats) == 1:
        cid = list(seen_chats.keys())[0]
        print(f"→ Añade en .env:\n    TELEGRAM_CHAT_ID={cid}")


if __name__ == "__main__":
    main()
