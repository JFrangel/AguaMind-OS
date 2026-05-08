"""
Camaleón OS — Interfaz local del ESP32.
OLED SSD1306 + LED RGB + Buzzer para mostrar estado sin internet.
"""

import time
import config as cfg
from machine import Pin, PWM, I2C

try:
    from ssd1306 import SSD1306_I2C
except ImportError:
    SSD1306_I2C = None


class LocalDisplay:
    def __init__(self):
        # OLED 128x64
        self.oled = None
        if SSD1306_I2C is not None:
            try:
                i2c = I2C(0, scl=Pin(cfg.I2C_SCL), sda=Pin(cfg.I2C_SDA), freq=400000)
                self.oled = SSD1306_I2C(128, 64, i2c, addr=cfg.OLED_ADDR)
            except Exception as e:
                print(f"[OLED] No disponible: {e}")

        # LED RGB
        self.led_r = Pin(cfg.PIN_LED_R, Pin.OUT)
        self.led_g = Pin(cfg.PIN_LED_G, Pin.OUT)
        self.led_b = Pin(cfg.PIN_LED_B, Pin.OUT)

        # Buzzer PWM
        self.buzzer = PWM(Pin(cfg.PIN_BUZZER), freq=2000, duty=0)

    def show_reading(self, r: dict, status: str = "OK"):
        """Actualiza OLED con lecturas resumidas."""
        if not self.oled:
            return
        try:
            self.oled.fill(0)
            self.oled.text("Camaleón OS", 0, 0)
            self.oled.text(f"Q: {r.get('flow1_lmin',0):.1f}+{r.get('flow2_lmin',0):.1f}", 0, 12)
            self.oled.text(f"TA:{r.get('level_a_pct',0):.0f}% TB:{r.get('level_b_pct',0):.0f}%", 0, 24)
            self.oled.text(f"P:{r.get('pressure_kpa',0):.0f}kPa", 0, 36)
            self.oled.text(f"NTU:{r.get('turbidity_ntu',0):.1f}", 0, 48)
            self.oled.text(f"[{status}]", 80, 56)
            self.oled.show()
        except Exception:
            pass

    def show_message(self, line1: str, line2: str = "", line3: str = ""):
        if not self.oled:
            return
        try:
            self.oled.fill(0)
            self.oled.text(line1[:16], 0, 8)
            if line2: self.oled.text(line2[:16], 0, 24)
            if line3: self.oled.text(line3[:16], 0, 40)
            self.oled.show()
        except Exception:
            pass

    def set_status(self, status: str):
        """Enciende LED RGB según estado: OK/WARNING/CRITICAL."""
        # Apagar todos primero
        self.led_r.value(0)
        self.led_g.value(0)
        self.led_b.value(0)

        if status == "ok":
            self.led_g.value(1)
        elif status == "warning":
            self.led_r.value(1)
            self.led_g.value(1)   # = amarillo
        elif status == "critical":
            self.led_r.value(1)
        else:
            self.led_b.value(1)

    def beep_critical(self):
        """3 pulsos cortos del buzzer = alerta crítica."""
        for _ in range(3):
            self.buzzer.duty(512)
            time.sleep_ms(120)
            self.buzzer.duty(0)
            time.sleep_ms(80)

    def beep_warning(self):
        """1 pulso largo = advertencia."""
        self.buzzer.duty(384)
        time.sleep_ms(300)
        self.buzzer.duty(0)
