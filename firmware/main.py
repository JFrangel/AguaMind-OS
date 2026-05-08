"""
Camaleón OS — Firmware ESP32 (MicroPython)
Loop principal del nodo IoT en la PTAP UNIAJC.

Flujo:
  1. Conectar WiFi + MQTT (HiveMQ Cloud)
  2. Inicializar 6 sensores + OLED + LED RGB + Buzzer
  3. Loop infinito:
       a. Cada 1s: leer los 6 sensores
       b. Cada 30s: procesar buffer + publicar MQTT + actualizar OLED/LED
"""

import time
import gc
import network

import config as cfg
from sensors import SensorBoard
from mqtt_client import CamaleónMQTT
from display import LocalDisplay


# ── Conexión WiFi ────────────────────────────────────────────────────────
def connect_wifi() -> bool:
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    if sta.isconnected():
        return True
    sta.connect(cfg.WIFI_SSID, cfg.WIFI_PASS)
    print(f"[WiFi] Conectando a {cfg.WIFI_SSID}...")

    timeout = cfg.WIFI_TIMEOUT_S
    while not sta.isconnected() and timeout > 0:
        time.sleep(1)
        timeout -= 1

    if sta.isconnected():
        print(f"[WiFi] OK · IP={sta.ifconfig()[0]}")
        return True
    print("[WiFi] Falló")
    return False


# ── Evaluación local de umbrales (sin LLM) ───────────────────────────────
def evaluate_local_status(r: dict) -> str:
    """Evalúa el peor estado local basado en los 6 sensores."""
    if r.get("vibration"):
        return "critical"
    if r.get("turbidity_ntu", 0) > cfg.THRESHOLD_TURBIDITY_MAX_NTU:
        return "critical"
    if r.get("phreatic_m", 10) < cfg.THRESHOLD_PHREATIC_MIN_M:
        return "critical"
    if r.get("level_a_pct", 100) < cfg.THRESHOLD_TANK_A_CRITICAL:
        return "critical"

    if r.get("pressure_kpa", 300) > cfg.THRESHOLD_PRESSURE_MAX_KPA:
        return "warning"
    if r.get("pressure_kpa", 300) < cfg.THRESHOLD_PRESSURE_MIN_KPA:
        return "warning"
    flow_total = r.get("flow1_lmin", 0) + r.get("flow2_lmin", 0)
    if flow_total < cfg.THRESHOLD_FLOW_MIN_LMIN:
        return "warning"

    return "ok"


def aggregate_buffer(buffer: list[dict]) -> dict:
    """Calcula el promedio de las muestras en el buffer."""
    if not buffer:
        return {}
    keys_num = ["flow1_lmin", "flow2_lmin", "level_a_pct", "level_b_pct",
                "pressure_kpa", "phreatic_m", "turbidity_ntu"]
    avg = {}
    n = len(buffer)
    for k in keys_num:
        vals = [b.get(k, 0) for b in buffer if b.get(k, -1) >= 0]
        avg[k] = round(sum(vals) / len(vals), 2) if vals else 0
    # Vibración: si AL MENOS 1 muestra detectó vibración
    avg["vibration"] = any(b.get("vibration") for b in buffer)
    return avg


# ── Loop principal ───────────────────────────────────────────────────────
def main():
    print("=" * 50)
    print(f"Camaleón OS · ESP32 Firmware v{cfg.FIRMWARE_VERSION}")
    print(f"Node: {cfg.NODE_ID} @ {cfg.NODE_LOCATION}")
    print("=" * 50)

    # Inicializar interfaz local
    display = LocalDisplay()
    display.show_message("Camaleón OS", "Iniciando...", "v" + cfg.FIRMWARE_VERSION)
    display.set_status("info")

    # WiFi
    wifi_ok = False
    for i in range(cfg.WIFI_RETRY_MAX):
        if connect_wifi():
            wifi_ok = True
            break
        display.show_message("WiFi", f"Reintentando", f"{i+1}/{cfg.WIFI_RETRY_MAX}")
        time.sleep(3)

    if not wifi_ok:
        display.show_message("ERROR", "Sin WiFi", "Modo local")
        display.set_status("warning")

    # MQTT
    mqtt = CamaleónMQTT()
    if wifi_ok:
        mqtt.connect()

    # Sensores
    try:
        board = SensorBoard()
    except Exception as e:
        print(f"[ERROR] Inicializando sensores: {e}")
        display.show_message("ERROR", "Sensores", str(e)[:16])
        display.set_status("critical")
        return

    print("[INIT] Sistema operacional · entrando al loop principal")
    display.show_message("Camaleón OS", "Operacional", "Loop activo")
    display.set_status("ok")

    buffer = []
    last_publish = time.ticks_ms()
    cycle = 0

    while True:
        try:
            # ── TASK 0: Leer sensores cada 1s ──
            r = board.read_all()
            buffer.append(r)
            if len(buffer) > cfg.BUFFER_SIZE:
                buffer.pop(0)

            # ── TASK 1: Cada 30s, procesar + publicar ──
            now = time.ticks_ms()
            if time.ticks_diff(now, last_publish) >= cfg.PROCESS_INTERVAL_MS:
                cycle += 1
                last_publish = now

                # Promedio del buffer
                avg = aggregate_buffer(buffer)

                # Evaluar estado local
                status = evaluate_local_status(avg)

                # Actualizar interfaz local
                display.show_reading(avg, status.upper())
                display.set_status(status)
                if status == "critical":
                    display.beep_critical()
                elif status == "warning":
                    display.beep_warning()

                # Publicar a MQTT (o HTTP fallback)
                ok = mqtt.publish_reading(avg)

                if cfg.DEBUG:
                    print(
                        f"[CYCLE {cycle}] {status.upper()} "
                        f"Q={avg.get('flow1_lmin',0):.1f}+{avg.get('flow2_lmin',0):.1f} "
                        f"TA={avg.get('level_a_pct',0):.1f}% "
                        f"P={avg.get('pressure_kpa',0):.0f}kPa "
                        f"NTU={avg.get('turbidity_ntu',0):.1f} "
                        f"published={ok}"
                    )

                # Reconectar MQTT si se cayó
                if not mqtt.connected and wifi_ok:
                    mqtt.connect()

                gc.collect()

            time.sleep_ms(cfg.SENSOR_READ_INTERVAL_MS)

        except KeyboardInterrupt:
            print("[STOP] Interrupción del usuario")
            break
        except Exception as e:
            print(f"[ERROR] Loop: {e}")
            display.show_message("ERROR loop", str(e)[:16], "Reintentando...")
            time.sleep(5)

    mqtt.disconnect()
    display.show_message("Camaleón OS", "Detenido", "")
    display.set_status("info")


# ── Entry point ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
