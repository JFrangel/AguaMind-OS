"""
WaterMind OS — Simulador PC del nodo ESP32
Permite probar el flujo completo SIN hardware físico:

  [Simulador PC] ──HTTP POST /water/ingest──▶ [FastAPI] ──▶ [Dashboard] + [Telegram]

Útil para:
  - Demo del hackathon (sin necesitar placa)
  - Desarrollo sin esperar al hardware
  - Validación de la lógica del agente multi-IA

Uso:
  python firmware/simulator_pc.py [--scenario normal|leak|peak|turbidity]
"""

import argparse
import json
import math
import random
import time
from datetime import datetime

import requests

BACKEND_URL = "http://localhost:8000"
INGEST_URL  = f"{BACKEND_URL}/water/ingest"
INTERVAL_S  = 5  # publicar cada N segundos (en producción: 30s)


# ── Generador de datos realistas (basado en datos PDF UNIAJC) ──────────────
def hour_factor(h: int) -> float:
    if 7 <= h <= 9:   return 1.6
    if 10 <= h <= 12: return 1.4
    if 13 <= h <= 14: return 0.8
    if 15 <= h <= 17: return 1.3
    if 6 <= h <= 18:  return 1.0
    return 0.25


def simulate_reading(scenario: str = "normal", t_s: float = 0) -> dict:
    """
    Simula los 6 sensores del ESP32 con datos realistas.
    Ejecuta una "rampa" suave para que parezca un sensor físico.
    """
    h = datetime.now().hour
    f = hour_factor(h)
    sine = math.sin(t_s / 30) * 0.05  # micro-oscilación tipo sensor
    noise = random.uniform(-0.05, 0.05)
    factor = f * (1 + sine + noise)

    # Sensor 1: Caudal (YF-S201) — 113.56 L/min total real
    flow1 = round(58.4 * factor, 2)
    flow2 = round(55.2 * factor, 2)

    # Sensor 3: Nivel tanques (JSN-SR04T)
    level_a = round(72 - factor * 8 + sine * 50, 1)
    level_b = round(78 - factor * 5 + sine * 30, 1)
    level_a = max(20, min(98, level_a))
    level_b = max(30, min(98, level_b))

    # Sensor 2: Presión (MPX5700AP)
    pump_active = level_a < 66.7
    pressure = round(280 + (80 if pump_active else 0) + noise * 30, 1)

    # Sensor 5: Nivel freático (4-20mA)
    phreatic = round(7.8 - factor * 0.6 + noise * 0.3, 2)

    # Sensor 6: Turbidez (TSD-10)
    turbidity = round(0.8 + random.uniform(0.0, 0.5), 2)

    # Sensor 4: Vibración (SW-420)
    vibration = False

    # Inyectar escenarios de demo
    if scenario == "leak":
        vibration = True
        pressure = round(pressure * 0.7, 1)   # caída por fuga
        flow1 = round(flow1 * 0.85, 2)         # caudal cae
    elif scenario == "peak":
        flow1 = round(flow1 * 1.8, 2)
        phreatic = round(phreatic - 1.5, 2)
        level_a = max(15, level_a - 20)
    elif scenario == "turbidity":
        turbidity = round(random.uniform(5.5, 7.5), 2)

    return {
        "flow1_lmin":    flow1,
        "flow2_lmin":    flow2,
        "level_a_pct":   level_a,
        "level_b_pct":   level_b,
        "pressure_kpa":  pressure,
        "phreatic_m":    phreatic,
        "turbidity_ntu": turbidity,
        "vibration":     vibration,
        "node_id":       "esp32-ptap-01-SIM",
    }


def post_reading(payload: dict) -> tuple[bool, dict]:
    """Envía la lectura al backend FastAPI."""
    try:
        r = requests.post(INGEST_URL, json=payload, timeout=10)
        if r.status_code == 200:
            return True, r.json()
        return False, {"error": f"HTTP {r.status_code}: {r.text}"}
    except requests.exceptions.ConnectionError:
        return False, {"error": "Backend no disponible — ¿corriendo uvicorn?"}
    except Exception as e:
        return False, {"error": str(e)}


def fmt_status(level: str) -> str:
    icons = {"critical": "🚨", "warning": "⚠️", "info": "ℹ️", "ok": "✅"}
    return icons.get(level, "•")


# ── Loop principal ─────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="WaterMind OS — Simulador PC del ESP32")
    parser.add_argument("--scenario", choices=["normal", "leak", "peak", "turbidity"],
                        default="normal", help="Escenario a simular")
    parser.add_argument("--interval", type=int, default=INTERVAL_S,
                        help="Intervalo entre publicaciones (segundos)")
    parser.add_argument("--once", action="store_true",
                        help="Publicar solo 1 lectura y salir")
    parser.add_argument("--backend", type=str, default=BACKEND_URL,
                        help="URL del backend (default: localhost:8000)")
    args = parser.parse_args()

    global INGEST_URL
    INGEST_URL = f"{args.backend}/water/ingest"

    print("╔══════════════════════════════════════════════════════════╗")
    print("║   WaterMind OS — Simulador ESP32 (Modo PC)               ║")
    print("║   UNIAJC Sede Sur · Hackathon 2026                       ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"  Backend:   {args.backend}")
    print(f"  Endpoint:  {INGEST_URL}")
    print(f"  Escenario: {args.scenario}")
    print(f"  Intervalo: {args.interval}s")
    print()

    cycle = 0
    t_start = time.time()
    try:
        while True:
            cycle += 1
            t = time.time() - t_start
            payload = simulate_reading(args.scenario, t)

            ok, resp = post_reading(payload)
            ts = datetime.now().strftime("%H:%M:%S")

            if ok:
                kpis   = resp["data"]["kpis"]
                alerts = resp["data"].get("alerts", [])
                ieh = kpis.get("IEH", {}).get("value", 0)
                tpp = kpis.get("TPP", {}).get("value", 0)
                cpe = kpis.get("CPE", {}).get("value", 0)
                ntu = payload["turbidity_ntu"]
                vib = "⚡VIB" if payload["vibration"] else "    "

                print(
                    f"[{ts}] #{cycle:3d} ✓ "
                    f"Q={payload['flow1_lmin']+payload['flow2_lmin']:.1f}L/min "
                    f"TA={payload['level_a_pct']:.1f}% "
                    f"P={payload['pressure_kpa']:.0f}kPa "
                    f"NTU={ntu:.1f} {vib} "
                    f"| IEH={ieh:.1f}% TPP={tpp:.1f}% CPE={cpe:.1f}"
                )

                # Mostrar alertas
                for a in alerts[:2]:
                    print(f"            {fmt_status(a['level'])} {a['zone']}: {a['message']}")
            else:
                print(f"[{ts}] #{cycle:3d} ✗ {resp.get('error', 'unknown')}")

            if args.once:
                break
            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\n[STOP] Simulador detenido por el usuario.")


if __name__ == "__main__":
    main()
