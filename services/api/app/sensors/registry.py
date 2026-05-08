"""
AguaMind OS - Registro de sensores fisicos: calibracion, unidades, rangos.

Cada sensor del mercado entrega su senal en una unidad/escala distinta. El
registry traduce esa senal cruda a unidades SI canonicas con calibracion
documentada y rangos validos para deteccion de outliers.

Para anadir un sensor nuevo: agregar una entrada al diccionario SENSORS y
opcionalmente registrar un converter.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from .schemas import SensorType


Converter = Callable[[float], float]


@dataclass
class SensorSpec:
    model: str                       # ej. "YF-S201", "MPX5700AP", generico "any-flow-pulse"
    type: SensorType
    unit_si: str                     # unidad SI canonica
    raw_unit: str = "raw"             # unidad de entrada esperada (Hz, V, mA, %, ...)
    range_min: Optional[float] = None  # min fisico aceptable (en unidad SI)
    range_max: Optional[float] = None  # max fisico aceptable
    convert: Optional[Converter] = None  # raw -> SI; None significa "ya viene en SI"
    notes: str = ""
    aliases: list[str] = field(default_factory=list)  # otros nombres aceptados


# ---- Conversiones tipicas ---------------------------------------------------

def yf_s201_hz_to_lmin(hz: float) -> float:
    """YF-S201: 7.5 Hz por L/min."""
    return hz / 7.5


def yf_dn50_hz_to_lmin(hz: float) -> float:
    """YF-DN50: 0.2 Hz por L/min (para caudales grandes)."""
    return hz / 0.2


def mpx5700_v_to_kpa(v: float) -> float:
    """MPX5700AP: 0-5V => 0-700 kPa, lineal."""
    return max(0.0, (v / 5.0) * 700.0)


def jsn_sr04t_us_to_cm(us: float) -> float:
    """JSN-SR04T: ancho de pulso us a distancia en cm (340 m/s, ida y vuelta)."""
    return (us * 0.0343) / 2.0


def loop_4_20ma_to_pct(ma: float, scale_min: float = 0.0, scale_max: float = 100.0) -> float:
    """Loop 4-20 mA estandar industrial -> escala (default 0..100%)."""
    if ma < 3.5:  # corriente fuera de rango => sensor desconectado
        return float("nan")
    pct = (ma - 4.0) / 16.0
    return scale_min + pct * (scale_max - scale_min)


def freatic_4_20ma_to_m(ma: float, max_depth_m: float = 10.0) -> float:
    """Transductor freatico 4-20mA: 4mA = 0m, 20mA = max_depth_m."""
    return loop_4_20ma_to_pct(ma, 0.0, max_depth_m)


def tsd10_v_to_ntu(v: float) -> float:
    """TSD-10: 4.5V (clara) -> 0V (turbia). Aproximacion lineal 0..10 NTU."""
    if v <= 0.0:
        return 10.0
    return max(0.0, 10.0 * (1.0 - min(v, 4.5) / 4.5))


def ph_v_to_ph(v: float) -> float:
    """Sonda pH analogica (DFRobot SEN0161): pH = 7 cuando V=2.5; -5.7 pH/V."""
    return 7.0 + (2.5 - v) * 5.7


def chlorine_orp_mv_to_ppm(mv: float) -> float:
    """ORP/redox: aproximacion empirica mV -> ppm cloro libre (>650 mV ~ 1 ppm)."""
    return max(0.0, (mv - 600.0) / 50.0)


def vibration_digital_to_bool(x: float) -> float:
    return 1.0 if x else 0.0


def conductivity_v_to_us(v: float, gain: float = 1000.0) -> float:
    """DFR0300 conductividad: V * gain -> uS/cm."""
    return v * gain


def passthrough(x: float) -> float:
    return float(x)


# ---- Registro principal -----------------------------------------------------

SENSORS: dict[str, SensorSpec] = {
    # --- caudal ---
    "YF-S201": SensorSpec(
        model="YF-S201", type=SensorType.FLOW, unit_si="L/min", raw_unit="Hz",
        range_min=0.0, range_max=30.0, convert=yf_s201_hz_to_lmin,
        notes="Caudalimetro pequeno 1/2 in. 7.5 Hz/L/min.",
        aliases=["yf-s201", "yfs201", "flow-small", "caudal-small"],
    ),
    "YF-DN50": SensorSpec(
        model="YF-DN50", type=SensorType.FLOW, unit_si="L/min", raw_unit="Hz",
        range_min=0.0, range_max=400.0, convert=yf_dn50_hz_to_lmin,
        notes="Caudalimetro grande 2 in. 0.2 Hz/L/min.",
        aliases=["yf-dn50", "flow-large", "caudal-large"],
    ),
    # --- presion ---
    "MPX5700AP": SensorSpec(
        model="MPX5700AP", type=SensorType.PRESSURE, unit_si="kPa", raw_unit="V",
        range_min=0.0, range_max=700.0, convert=mpx5700_v_to_kpa,
        notes="Sensor de presion 0-700 kPa, salida 0-5V.",
        aliases=["mpx5700", "pressure-700", "presion-700"],
    ),
    # --- nivel tanque ---
    "JSN-SR04T": SensorSpec(
        model="JSN-SR04T", type=SensorType.LEVEL, unit_si="cm", raw_unit="us",
        range_min=20.0, range_max=450.0, convert=jsn_sr04t_us_to_cm,
        notes="Ultrasonido impermeable 0-4.5m, ancho de pulso en us.",
        aliases=["jsn-sr04t", "ultrasonic", "nivel-ultrasonico"],
    ),
    # --- vibracion ---
    "SW-420": SensorSpec(
        model="SW-420", type=SensorType.VIBRATION, unit_si="bool", raw_unit="digital",
        range_min=0.0, range_max=1.0, convert=vibration_digital_to_bool,
        notes="Sensor de vibracion digital con LM393.",
        aliases=["sw-420", "vibration", "vibracion"],
    ),
    # --- nivel freatico ---
    "FREATIC-4-20MA": SensorSpec(
        model="FREATIC-4-20MA", type=SensorType.PHREATIC, unit_si="m", raw_unit="mA",
        range_min=0.0, range_max=10.0, convert=freatic_4_20ma_to_m,
        notes="Transductor industrial loop 4-20mA, profundidad maxima 10m.",
        aliases=["freatic", "phreatic", "loop-freatic"],
    ),
    # --- turbidez ---
    "TSD-10": SensorSpec(
        model="TSD-10", type=SensorType.TURBIDITY, unit_si="NTU", raw_unit="V",
        range_min=0.0, range_max=10.0, convert=tsd10_v_to_ntu,
        notes="Turbidimetro analogico 0-4.5V invertido.",
        aliases=["tsd-10", "turbidity"],
    ),
    # --- pH ---
    "SEN0161": SensorSpec(
        model="SEN0161", type=SensorType.PH, unit_si="pH", raw_unit="V",
        range_min=0.0, range_max=14.0, convert=ph_v_to_ph,
        notes="Sonda pH DFRobot SEN0161, V=2.5 en pH 7.",
        aliases=["ph-probe", "ph"],
    ),
    # --- cloro residual ---
    "ORP": SensorSpec(
        model="ORP", type=SensorType.CHLORINE, unit_si="ppm", raw_unit="mV",
        range_min=0.0, range_max=5.0, convert=chlorine_orp_mv_to_ppm,
        notes="Sonda ORP/redox para cloro libre.",
        aliases=["orp", "redox", "chlorine"],
    ),
    # --- conductividad ---
    "DFR0300": SensorSpec(
        model="DFR0300", type=SensorType.CONDUCTIVITY, unit_si="uS/cm", raw_unit="V",
        range_min=0.0, range_max=20000.0, convert=conductivity_v_to_us,
        notes="Sensor de conductividad analogico.",
        aliases=["dfr0300", "conductivity"],
    ),
    # --- generico para otros tipos ---
    "GENERIC": SensorSpec(
        model="GENERIC", type=SensorType.UNKNOWN, unit_si="", raw_unit="raw",
        convert=passthrough,
        notes="Sensor generico. Conversion identidad.",
    ),
}


def lookup(model_or_alias: str) -> SensorSpec:
    """Encuentra la spec de un sensor por su modelo o alias. Tolerante a mayusculas."""
    if not model_or_alias:
        return SENSORS["GENERIC"]
    key = model_or_alias.strip().upper()
    if key in SENSORS:
        return SENSORS[key]
    needle = model_or_alias.strip().lower()
    for spec in SENSORS.values():
        if needle in [a.lower() for a in spec.aliases]:
            return spec
    return SENSORS["GENERIC"]


def quality_for(spec: SensorSpec, value_si: float) -> str:
    """Evalua calidad fisica de la lectura contra rangos del spec."""
    import math
    if math.isnan(value_si) or math.isinf(value_si):
        return "invalid"
    if spec.range_min is not None and value_si < spec.range_min:
        return "out_of_range"
    if spec.range_max is not None and value_si > spec.range_max:
        return "out_of_range"
    return "ok"
