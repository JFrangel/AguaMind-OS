"""
WaterMind OS — Drivers de sensores para ESP32 (MicroPython).

Implementa lectura de los 6 sensores con acondicionamiento de señal:
  1. YF-S201        — caudal por interrupciones (pulse counter)
  2. MPX5700AP      — presión vía ADS1115 ADC
  3. JSN-SR04T      — nivel ultrasónico
  4. SW-420         — vibración digital
  5. 4-20mA loop    — nivel freático vía ADS1115 + shunt
  6. TSD-10         — turbidez vía ADS1115
"""

import time
import config as cfg
from machine import Pin, ADC, I2C
from micropython import const

try:
    # Librería ADS1115 (instalable en MicroPython con upip)
    from ads1x15 import ADS1115
except ImportError:
    ADS1115 = None     # fallback si no está instalada


# ── Variables globales para contadores de pulso (interrupciones) ─────────
_flow1_count = 0
_flow2_count = 0


def _flow1_isr(pin):
    global _flow1_count
    _flow1_count += 1


def _flow2_isr(pin):
    global _flow2_count
    _flow2_count += 1


# ── Sensor 1: Caudal YF-S201 ─────────────────────────────────────────────
class FlowSensor:
    def __init__(self, pin_num: int, channel: int = 1):
        self.pin = Pin(pin_num, Pin.IN, Pin.PULL_UP)
        self.channel = channel
        if channel == 1:
            self.pin.irq(trigger=Pin.IRQ_RISING, handler=_flow1_isr)
        else:
            self.pin.irq(trigger=Pin.IRQ_RISING, handler=_flow2_isr)

    def read_lmin(self, dt_ms: int) -> float:
        """Lee caudal en L/min basado en pulsos acumulados durante dt_ms."""
        global _flow1_count, _flow2_count
        if self.channel == 1:
            pulses = _flow1_count
            _flow1_count = 0
        else:
            pulses = _flow2_count
            _flow2_count = 0
        # YF-S201: F (Hz) = 7.5 × Q (L/min)
        # Q = pulses_per_second / 7.5
        if dt_ms <= 0:
            return 0.0
        pps = pulses * 1000 / dt_ms
        return round(pps / 7.5, 2)


# ── Sensor 3: Nivel tanque JSN-SR04T ─────────────────────────────────────
class UltrasonicSensor:
    def __init__(self, trig_pin: int, echo_pin: int, tank_height_cm: int):
        self.trig = Pin(trig_pin, Pin.OUT)
        self.echo = Pin(echo_pin, Pin.IN)
        self.tank_h = tank_height_cm
        self.trig.value(0)

    def _measure_distance_cm(self) -> float:
        """Mide distancia en cm usando ultrasonido."""
        self.trig.value(0)
        time.sleep_us(2)
        self.trig.value(1)
        time.sleep_us(10)
        self.trig.value(0)

        # Esperar pulso ECHO
        timeout = cfg.SR04_TIMEOUT_US
        t0 = time.ticks_us()
        while self.echo.value() == 0:
            if time.ticks_diff(time.ticks_us(), t0) > timeout:
                return -1
        start = time.ticks_us()
        while self.echo.value() == 1:
            if time.ticks_diff(time.ticks_us(), start) > timeout:
                return -1
        end = time.ticks_us()

        echo_us = time.ticks_diff(end, start)
        # Velocidad sonido = 343 m/s = 0.0343 cm/us, distancia ida y vuelta
        return (echo_us * 0.0343) / 2

    def read_pct(self) -> float:
        """Convierte distancia → % de llenado del tanque."""
        dist_cm = self._measure_distance_cm()
        if dist_cm < 0 or dist_cm > self.tank_h:
            return -1
        # Distancia desde tapa hasta agua: agua_h = tank_h - dist
        water_h = self.tank_h - dist_cm
        pct = max(0, min(100, (water_h / self.tank_h) * 100))
        return round(pct, 1)


# ── Sensor 4: Vibración SW-420 ───────────────────────────────────────────
class VibrationSensor:
    def __init__(self, pin_num: int, samples: int = 50):
        self.pin = Pin(pin_num, Pin.IN, Pin.PULL_UP)
        self.samples = samples

    def read(self) -> bool:
        """
        Lee N muestras y considera vibración anómala si > 30% son HIGH.
        Filtra ruido de vibraciones normales del entorno.
        """
        high_count = 0
        for _ in range(self.samples):
            if self.pin.value():
                high_count += 1
            time.sleep_us(200)
        return high_count > self.samples * 0.3


# ── Sensores analógicos vía ADS1115 (Sensor 2, 5, 6) ─────────────────────
class ADS1115Reader:
    """Wrapper sobre ADS1115 para leer los 3 sensores analógicos."""

    def __init__(self):
        if ADS1115 is None:
            raise RuntimeError("ads1x15 library not installed")
        i2c = I2C(0, scl=Pin(cfg.I2C_SCL), sda=Pin(cfg.I2C_SDA), freq=400000)
        self.adc = ADS1115(i2c, address=cfg.ADS_ADDR, gain=1)
        # Gain=1 → rango ±4.096V

    def read_voltage(self, channel: int) -> float:
        raw = self.adc.read(channel=channel)
        return self.adc.raw_to_v(raw)

    # Sensor 2 — MPX5700AP (presión)
    def read_pressure_kpa(self) -> float:
        v = self.read_voltage(cfg.ADS_CH_PRESSURE)
        # Datasheet: V_out = Vs × (0.0012858 × P + 0.04)
        # Despeje: P = (V/Vs - 0.04) / 0.0012858
        kpa = (v / cfg.MPX5700_VS - 0.04) / 0.0012858
        return round(max(0, kpa), 1)

    # Sensor 5 — Nivel freático (4-20mA)
    def read_phreatic_m(self) -> float:
        v = self.read_voltage(cfg.ADS_CH_PHREATIC)
        # V = mA × shunt / 1000  →  mA = V × 1000 / shunt
        ma = v * 1000 / cfg.SHUNT_OHMS
        # 4mA → 0m, 20mA → max
        m = max(0, (ma - 4) / 16 * cfg.PHREATIC_DEPTH_M)
        return round(m, 2)

    # Sensor 6 — Turbidez TSD-10
    def read_turbidity_ntu(self) -> float:
        v = self.read_voltage(cfg.ADS_CH_TURBIDITY)
        # Curva calibración fabricante (DFRobot SEN0189)
        if v >= 4.2:
            return 0.0
        ntu = -1120.4 * v * v + 5742.3 * v - 4352.9
        return round(max(0, ntu), 2)


# ── Lector de los 6 sensores combinado ───────────────────────────────────
class SensorBoard:
    """Encapsula los 6 sensores en una sola interfaz."""

    def __init__(self):
        self.flow1 = FlowSensor(cfg.PIN_FLOW1, channel=1)
        self.flow2 = FlowSensor(cfg.PIN_FLOW2, channel=2)
        self.tank_a = UltrasonicSensor(cfg.PIN_TRIG_A, cfg.PIN_ECHO_A, cfg.TANK_A_HEIGHT_CM)
        self.tank_b = UltrasonicSensor(cfg.PIN_TRIG_B, cfg.PIN_ECHO_B, cfg.TANK_B_HEIGHT_CM)
        self.vibration = VibrationSensor(cfg.PIN_VIBRATION)
        try:
            self.ads = ADS1115Reader()
        except Exception as e:
            print(f"[WARN] ADS1115 no disponible: {e}")
            self.ads = None

        self.last_read_ms = time.ticks_ms()

    def read_all(self) -> dict:
        """Lee los 6 sensores y retorna dict con todas las lecturas."""
        now = time.ticks_ms()
        dt = time.ticks_diff(now, self.last_read_ms)
        self.last_read_ms = now

        flow1 = self.flow1.read_lmin(dt)
        flow2 = self.flow2.read_lmin(dt)
        level_a = self.tank_a.read_pct()
        level_b = self.tank_b.read_pct()
        vibration = self.vibration.read()

        if self.ads:
            pressure = self.ads.read_pressure_kpa()
            phreatic = self.ads.read_phreatic_m()
            turbidity = self.ads.read_turbidity_ntu()
        else:
            pressure = phreatic = turbidity = -1

        return {
            "flow1_lmin":    flow1,
            "flow2_lmin":    flow2,
            "level_a_pct":   level_a,
            "level_b_pct":   level_b,
            "vibration":     vibration,
            "pressure_kpa":  pressure,
            "phreatic_m":    phreatic,
            "turbidity_ntu": turbidity,
        }
