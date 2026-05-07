"""
AguaMind OS — Cliente MQTT para ESP32 (MicroPython).
Publica lecturas a HiveMQ Cloud o broker local cada 30 segundos.
Si MQTT falla, hace fallback a HTTP POST /water/ingest.
"""

import json
import time
import config as cfg

try:
    from umqtt.simple import MQTTClient
except ImportError:
    MQTTClient = None

try:
    import urequests as requests
except ImportError:
    requests = None


class AguaMindMQTT:
    def __init__(self):
        self.client = None
        self.connected = False
        self._failed_buffer: list[dict] = []

    def connect(self) -> bool:
        if MQTTClient is None:
            print("[MQTT] umqtt.simple no disponible")
            return False
        try:
            self.client = MQTTClient(
                client_id=cfg.NODE_ID,
                server=cfg.MQTT_BROKER,
                port=cfg.MQTT_PORT,
                user=cfg.MQTT_USER or None,
                password=cfg.MQTT_PASS or None,
                keepalive=cfg.MQTT_KEEPALIVE_S,
            )
            self.client.connect()
            self.connected = True
            print(f"[MQTT] Conectado a {cfg.MQTT_BROKER}:{cfg.MQTT_PORT}")
            # Publicar evento de "online"
            self._publish_status("online")
            return True
        except Exception as e:
            print(f"[MQTT] Error conexión: {e}")
            self.connected = False
            return False

    def _publish_status(self, status: str):
        if not self.connected:
            return
        try:
            payload = json.dumps({
                "node_id":   cfg.NODE_ID,
                "status":    status,
                "version":   cfg.FIRMWARE_VERSION,
                "timestamp": time.time(),
            })
            self.client.publish(f"{cfg.MQTT_TOPIC}/status", payload)
        except Exception:
            pass

    def publish_reading(self, reading: dict) -> bool:
        """Publica lectura de sensores. Si falla MQTT, intenta HTTP."""
        payload_dict = {
            "node_id":   cfg.NODE_ID,
            "location":  cfg.NODE_LOCATION,
            "timestamp": time.time(),
            **reading,
        }
        payload = json.dumps(payload_dict)

        # Intento 1: MQTT
        if self.connected:
            try:
                self.client.publish(cfg.MQTT_TOPIC, payload)
                if cfg.DEBUG:
                    print(f"[MQTT] Publicado a {cfg.MQTT_TOPIC} ({len(payload)} bytes)")
                # Reenviar buffer pendiente si existe
                if self._failed_buffer:
                    self._flush_buffer()
                return True
            except Exception as e:
                print(f"[MQTT] Publish failed: {e}")
                self.connected = False

        # Intento 2: HTTP fallback
        if requests is not None:
            try:
                r = requests.post(
                    cfg.BACKEND_URL + cfg.INGEST_ENDPOINT,
                    json=payload_dict,
                    timeout=10,
                )
                ok = r.status_code == 200
                r.close()
                if ok and cfg.DEBUG:
                    print("[HTTP] Fallback OK → /water/ingest")
                return ok
            except Exception as e:
                print(f"[HTTP] Fallback error: {e}")

        # Si todo falla: guardar en buffer
        self._failed_buffer.append(payload_dict)
        if len(self._failed_buffer) > 100:
            self._failed_buffer = self._failed_buffer[-100:]
        return False

    def publish_alert(self, level: str, message: str):
        if not self.connected:
            return
        try:
            payload = json.dumps({
                "node_id":   cfg.NODE_ID,
                "level":     level,    # "critical" | "warning" | "info"
                "message":   message,
                "timestamp": time.time(),
            })
            self.client.publish(cfg.MQTT_TOPIC_ALERT, payload)
        except Exception:
            pass

    def _flush_buffer(self):
        """Reenvía mensajes que fallaron cuando volvió la conexión."""
        if not self._failed_buffer or not self.connected:
            return
        sent = 0
        while self._failed_buffer:
            item = self._failed_buffer.pop(0)
            try:
                self.client.publish(cfg.MQTT_TOPIC, json.dumps(item))
                sent += 1
            except Exception:
                self._failed_buffer.insert(0, item)
                break
        if sent and cfg.DEBUG:
            print(f"[MQTT] {sent} mensajes pendientes reenviados")

    def disconnect(self):
        if self.client and self.connected:
            try:
                self._publish_status("offline")
                self.client.disconnect()
            except Exception:
                pass
        self.connected = False
