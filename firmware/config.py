"""
AguaMind OS — ESP32 Firmware
Config: pines GPIO, umbrales, credenciales
UNIAJC Sede Sur · Hackathon 2026

Este archivo NO contiene secretos en producción.
En despliegue real cargar SSID/PASS/MQTT_PASS desde NVS o /secrets.json.
"""

# ── Identificador del nodo ────────────────────────────────────────────────
NODE_ID = "esp32-ptap-01"            # único por instalación
NODE_LOCATION = "PTAP-Aljibes"
FIRMWARE_VERSION = "1.0.0"

# ── WiFi ──────────────────────────────────────────────────────────────────
WIFI_SSID = "UNIAJC-Sede-Sur"
WIFI_PASS = "*** cargar desde NVS ***"
WIFI_TIMEOUT_S = 30
WIFI_RETRY_MAX = 10

# ── MQTT (HiveMQ Cloud free tier) ────────────────────────────────────────
MQTT_BROKER  = "broker.hivemq.com"   # gratis sin auth · cambiar a cluster propio en prod
MQTT_PORT    = 1883
MQTT_USER    = ""
MQTT_PASS    = ""
MQTT_TOPIC   = "campus/uniajc/sensors/ptap"
MQTT_TOPIC_ALERT = "campus/uniajc/alerts/ptap"
MQTT_KEEPALIVE_S = 60

# Backend HTTP fallback (si falla MQTT)
BACKEND_URL = "https://aguamind-os.up.koyeb.app"
INGEST_ENDPOINT = "/water/ingest"

# ── Pines GPIO ESP32 ──────────────────────────────────────────────────────
# Sensor 1 — Caudal (YF-S201 × 2)
PIN_FLOW1   = 34         # Aljibe 1 (input only)
PIN_FLOW2   = 35         # Aljibe 2 (input only)

# Sensor 3 — Nivel tanques (JSN-SR04T × 2)
PIN_TRIG_A  = 25         # Tanque A trigger (output)
PIN_ECHO_A  = 26         # Tanque A echo (input)
PIN_TRIG_B  = 27         # Tanque B trigger
PIN_ECHO_B  = 14         # Tanque B echo

# Sensor 4 — Vibración tuberías (SW-420)
PIN_VIBRATION = 33

# Sensor 2/5/6 — Analógicos vía ADS1115 (I2C)
I2C_SDA = 21
I2C_SCL = 22
ADS_ADDR = 0x48
ADS_CH_PRESSURE  = 0    # Sensor 2 — MPX5700AP
ADS_CH_PHREATIC  = 1    # Sensor 5 — 4-20mA submersible
ADS_CH_TURBIDITY = 2    # Sensor 6 — TSD-10

# Indicadores locales
PIN_LED_R     = 32       # LED RGB rojo
PIN_LED_G     = 4        # LED RGB verde
PIN_LED_B     = 2        # LED RGB azul
PIN_BUZZER    = 5        # Buzzer PWM
OLED_ADDR     = 0x3C     # SSD1306 I2C

# ── Calibración sensores ──────────────────────────────────────────────────
# YF-S201: F (Hz) = 7.5 × Q (L/min)  →  Q = pulses_per_sec / 7.5
YFS201_PULSES_PER_LITER = 450        # 7.5 Hz/(L/min) × 60s

# JSN-SR04T: distancia (cm) = (echo_us × 0.0343) / 2
TANK_A_HEIGHT_CM = 180               # altura interna Tanque A
TANK_B_HEIGHT_CM = 120               # altura interna Tanque B
SR04_TIMEOUT_US = 30000

# MPX5700AP: V_out = V_s × (0.0012858 × P + 0.04)
# Despeje P (kPa): P = (Vout/Vs - 0.04) / 0.0012858
MPX5700_VS = 5.0

# 4-20mA shunt 150Ω: V = mA × 150 / 1000
# 4mA = 0.6V → 0m | 20mA = 3.0V → 10m
SHUNT_OHMS = 150
PHREATIC_DEPTH_M = 10                # rango sensor 0–10m WC

# TSD-10: V → NTU (curva calibración fabricante)
# NTU ≈ -1120.4 × V² + 5742.3 × V - 4352.9
TURBIDITY_VREF = 5.0

# ── Umbrales (alertas locales en el ESP32) ────────────────────────────────
THRESHOLD_FLOW_MIN_LMIN     = 50.0
THRESHOLD_TANK_A_CRITICAL   = 33.3   # %
THRESHOLD_TANK_A_PUMP_ON    = 66.7   # %
THRESHOLD_PRESSURE_MAX_KPA  = 500.0
THRESHOLD_PRESSURE_MIN_KPA  = 100.0
THRESHOLD_TURBIDITY_MAX_NTU = 4.0
THRESHOLD_PHREATIC_MIN_M    = 2.0

# ── Tiempos del loop ──────────────────────────────────────────────────────
SENSOR_READ_INTERVAL_MS  = 1000      # leer cada 1 segundo
PROCESS_INTERVAL_MS      = 30000     # procesar + publicar cada 30 segundos
BUFFER_SIZE = 30                     # 30 muestras = 30 segundos

# Modo debug (imprime por Serial)
DEBUG = True
