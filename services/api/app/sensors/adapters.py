"""
WaterMind OS - Adaptadores de formato de entrada.

Cada funcion acepta un payload en un formato distinto y devuelve una lista
de dicts con los campos minimos: sensor_id, model, value_raw, timestamp,
node_id, type (opcional). El normalizador despues los pasa por el registry
y los convierte a CanonicalReading.

Formatos soportados:
  - json_object        : un dict JSON plano {sensor_id: value} o estructurado
  - json_array         : lista de dicts ya con campos sueltos
  - json_lines (NDJSON): un dict por linea
  - csv                : "ts,node,sensor_id,model,value\\n..."
  - esp32_compact      : dict compacto del firmware (flow1/flow2/pressure/...)
  - modbus_holding     : lista de pares [(addr, valor), ...] con mapping
  - mqtt_topic         : topic + payload tipo "campus/uniajc/sensors/{node}/{sensor}"
  - opcua_struct       : dict con NodeId -> Variant simulado
  - scada_struct       : dict con tag-based naming (TT-101, FT-202, ...)
  - raw_bytes          : bytes -> intenta detectar via magic
"""
from __future__ import annotations

import csv
import io
import json
import re
from datetime import datetime, timezone
from typing import Any, Iterable


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def from_json_object(payload: dict, node_id: str | None = None) -> list[dict]:
    """Acepta un objeto JSON plano. Heuristica:
    - Si tiene claves 'sensor_id' y 'value' -> es UN registro.
    - Si tiene clave 'readings' o 'sensors' -> son varios.
    - De lo contrario asume {sensor_id: value, ...}.
    """
    if not isinstance(payload, dict):
        return []
    ts = payload.get("timestamp") or payload.get("ts") or _now_iso()
    nid = payload.get("node_id") or payload.get("node") or node_id or "unknown"

    if "sensor_id" in payload and ("value" in payload or "value_raw" in payload):
        return [{
            "timestamp": ts,
            "node_id": nid,
            "sensor_id": payload["sensor_id"],
            "model": payload.get("model") or payload.get("type") or "GENERIC",
            "value_raw": payload.get("value_raw", payload.get("value")),
            "type": payload.get("type"),
            "unit": payload.get("unit"),
        }]

    inner = payload.get("readings") or payload.get("sensors")
    if isinstance(inner, list):
        return from_json_array(inner, node_id=nid)
    if isinstance(inner, dict):
        return _flat_dict_to_records(inner, ts, nid)

    return _flat_dict_to_records(payload, ts, nid)


def _flat_dict_to_records(d: dict, ts: str, node_id: str) -> list[dict]:
    out: list[dict] = []
    skip = {"timestamp", "ts", "node_id", "node", "device", "_meta"}
    for k, v in d.items():
        if k in skip:
            continue
        if isinstance(v, (int, float, bool)):
            out.append({
                "timestamp": ts, "node_id": node_id,
                "sensor_id": k, "model": _model_hint_from_name(k), "value_raw": v,
            })
    return out


def from_json_array(payload: list, node_id: str | None = None) -> list[dict]:
    out: list[dict] = []
    for item in payload:
        if isinstance(item, dict):
            out.extend(from_json_object(item, node_id=node_id))
    return out


def from_ndjson(payload: str, node_id: str | None = None) -> list[dict]:
    out: list[dict] = []
    for line in payload.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                out.extend(from_json_object(obj, node_id=node_id))
        except json.JSONDecodeError:
            continue
    return out


def from_csv(payload: str, node_id: str | None = None) -> list[dict]:
    """CSV con header. Columnas reconocidas (cualquier orden, case-insensitive):
    timestamp/ts, node/node_id, sensor_id/sensor, model/type, value/value_raw, unit
    """
    out: list[dict] = []
    reader = csv.DictReader(io.StringIO(payload))
    for row in reader:
        norm = {k.lower().strip(): v for k, v in row.items() if k}
        sid = norm.get("sensor_id") or norm.get("sensor") or norm.get("tag")
        val = norm.get("value_raw") or norm.get("value") or norm.get("v")
        if sid is None or val is None:
            continue
        try:
            val_f = float(val)
        except (TypeError, ValueError):
            continue
        out.append({
            "timestamp": norm.get("timestamp") or norm.get("ts") or _now_iso(),
            "node_id":   norm.get("node_id") or norm.get("node") or node_id or "csv",
            "sensor_id": sid,
            "model":     norm.get("model") or norm.get("type") or _model_hint_from_name(sid),
            "value_raw": val_f,
            "unit":      norm.get("unit"),
        })
    return out


def from_esp32_compact(payload: dict, node_id: str | None = None) -> list[dict]:
    """Formato del firmware ESP32 actual de WaterMind. Mapea claves a sensores."""
    nid = payload.get("node_id") or node_id or "esp32-1"
    ts = payload.get("timestamp") or _now_iso()
    mapping = {
        "flow1_lmin":    ("YF-S201",         "flow1"),
        "flow2_lmin":    ("YF-S201",         "flow2"),
        "pressure_kpa":  ("MPX5700AP",       "pressure"),
        "tank_a_pct":    ("JSN-SR04T",       "level_a"),
        "tank_b_pct":    ("JSN-SR04T",       "level_b"),
        "vibration":     ("SW-420",          "vibration"),
        "phreatic_m":    ("FREATIC-4-20MA",  "phreatic"),
        "turbidity_ntu": ("TSD-10",          "turbidity"),
    }
    out = []
    for key, (model, sid) in mapping.items():
        if key in payload:
            out.append({
                "timestamp": ts, "node_id": nid, "sensor_id": sid,
                "model": model, "value_raw": float(payload[key]),
                "_already_si": True,  # estos vienen ya en SI desde el firmware
            })
    return out


# Mapping ejemplo de Modbus holding registers a tags. En produccion seria
# configurable por el usuario; esta version ilustra el principio.
DEFAULT_MODBUS_MAP = {
    40001: ("FT-101",  "YF-S201",   "flow1_hz"),
    40002: ("FT-102",  "YF-S201",   "flow2_hz"),
    40003: ("PT-201",  "MPX5700AP", "pressure_v"),
    40004: ("LT-301",  "JSN-SR04T", "tank_a_us"),
    40005: ("LT-302",  "JSN-SR04T", "tank_b_us"),
    40006: ("VT-401",  "SW-420",    "vibration_digital"),
    40007: ("LT-402",  "FREATIC-4-20MA", "phreatic_ma"),
    40008: ("AT-501",  "TSD-10",    "turbidity_v"),
}


def from_modbus(payload: list[tuple[int, float]], node_id: str | None = None,
                mapping: dict[int, tuple[str, str, str]] | None = None) -> list[dict]:
    """Lista de (address, valor). Mapping default trae la convencion estandar."""
    m = mapping or DEFAULT_MODBUS_MAP
    nid = node_id or "modbus-1"
    ts = _now_iso()
    out = []
    for addr, val in payload:
        spec = m.get(addr)
        if not spec:
            continue
        sid, model, _raw = spec
        out.append({
            "timestamp": ts, "node_id": nid, "sensor_id": sid,
            "model": model, "value_raw": float(val),
        })
    return out


def from_mqtt(topic: str, payload: Any) -> list[dict]:
    """topic="campus/uniajc/sensors/<node>/<sensor>" + payload JSON o numero."""
    parts = [p for p in (topic or "").split("/") if p]
    nid = parts[-2] if len(parts) >= 2 else "mqtt"
    sid = parts[-1] if len(parts) >= 1 else "unknown"

    if isinstance(payload, (int, float)):
        return [{
            "timestamp": _now_iso(), "node_id": nid, "sensor_id": sid,
            "model": _model_hint_from_name(sid), "value_raw": float(payload),
        }]
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            try:
                return [{
                    "timestamp": _now_iso(), "node_id": nid, "sensor_id": sid,
                    "model": _model_hint_from_name(sid), "value_raw": float(payload),
                }]
            except (TypeError, ValueError):
                return []
    if isinstance(payload, dict):
        rec = from_json_object(payload, node_id=nid)
        for r in rec:
            r.setdefault("sensor_id", sid)
        return rec
    return []


# Tag-based SCADA: TT-101 (temperature), FT-201 (flow), PT-301 (pressure)...
SCADA_TAG_RE = re.compile(r"^([A-Z]{2})-?(\d+)$")
SCADA_TAG_TYPES: dict[str, tuple[str, str]] = {
    "FT": ("YF-S201",        "flow"),
    "PT": ("MPX5700AP",      "pressure"),
    "LT": ("JSN-SR04T",      "level"),
    "VT": ("SW-420",         "vibration"),
    "AT": ("TSD-10",         "turbidity"),
    "TT": ("GENERIC",        "temperature"),
    "QT": ("ORP",            "chlorine"),
    "PH": ("SEN0161",        "ph"),
    "CT": ("DFR0300",        "conductivity"),
}


def from_scada(payload: dict, node_id: str | None = None) -> list[dict]:
    """SCADA con nomenclatura tag-based. Las llaves son tags estilo 'FT-101'."""
    out = []
    ts = payload.get("timestamp") or _now_iso()
    nid = payload.get("node_id") or node_id or "scada-1"
    for k, v in payload.items():
        if k in {"timestamp", "ts", "node_id", "node"}:
            continue
        if not isinstance(v, (int, float)):
            continue
        m = SCADA_TAG_RE.match(k.upper())
        if not m:
            continue
        prefix = m.group(1)
        model, _typ = SCADA_TAG_TYPES.get(prefix, ("GENERIC", "unknown"))
        out.append({
            "timestamp": ts, "node_id": nid, "sensor_id": k,
            "model": model, "value_raw": float(v),
        })
    return out


def from_opcua(payload: dict, node_id: str | None = None) -> list[dict]:
    """OPC-UA en su forma JSON-like: {nodeid: {Value: x, SourceTimestamp: t}}."""
    out = []
    nid = node_id or "opcua-1"
    for nodeid, val in payload.items():
        if isinstance(val, dict):
            v = val.get("Value")
            ts = val.get("SourceTimestamp") or _now_iso()
        else:
            v = val
            ts = _now_iso()
        if v is None or not isinstance(v, (int, float)):
            continue
        sid = nodeid.split(";")[-1] if ";" in nodeid else nodeid
        out.append({
            "timestamp": ts, "node_id": nid, "sensor_id": sid,
            "model": _model_hint_from_name(sid), "value_raw": float(v),
        })
    return out


# ----- Heuristica para inferir modelo desde el nombre del sensor ------------

def _model_hint_from_name(name: str) -> str:
    if not name:
        return "GENERIC"
    n = name.lower()
    if any(s in n for s in ["flow", "caudal", "yfs", "yf-s", "yf_s"]):
        return "YF-S201"
    if "yf-dn50" in n or "ydn50" in n or "flow-large" in n:
        return "YF-DN50"
    if any(s in n for s in ["press", "presion", "kpa", "mpx"]):
        return "MPX5700AP"
    if any(s in n for s in ["level", "nivel", "tank", "tanque", "ultrasonic", "jsn"]):
        return "JSN-SR04T"
    if any(s in n for s in ["vib", "shock", "sw420", "sw-420"]):
        return "SW-420"
    if any(s in n for s in ["phreatic", "freatic", "freatico"]):
        return "FREATIC-4-20MA"
    if any(s in n for s in ["turbid", "ntu", "tsd"]):
        return "TSD-10"
    if name.lower() == "ph" or "ph-" in n or "ph_" in n:
        return "SEN0161"
    if any(s in n for s in ["cloro", "chlorin", "orp", "redox"]):
        return "ORP"
    if any(s in n for s in ["conduct", "us/cm"]):
        return "DFR0300"
    if any(s in n for s in ["current", "corriente", "ct-clamp", "sct"]):
        return "SCT-013-030"
    if any(s in n for s in ["soil", "humedad-suelo", "humedad_suelo", "ground-moist"]):
        return "CAPACITIVE-SOIL-V1.2"
    return "GENERIC"


# ----- Detector automatico de formato ---------------------------------------

def detect_format(payload: Any) -> str:
    """Heuristica para auto-detectar el formato cuando no viene declarado."""
    if isinstance(payload, bytes):
        try:
            payload = payload.decode("utf-8")
        except UnicodeDecodeError:
            return "raw_bytes"

    if isinstance(payload, str):
        stripped = payload.strip()
        if stripped.startswith("{") or stripped.startswith("["):
            try:
                obj = json.loads(stripped)
                return _detect_from_obj(obj)
            except json.JSONDecodeError:
                pass
        if "\n" in stripped:
            first = stripped.splitlines()[0]
            if first.startswith("{"):
                return "json_lines"
            if "," in first:
                return "csv"
        if "," in stripped:
            return "csv"
        return "csv"

    if isinstance(payload, list):
        if payload and isinstance(payload[0], (list, tuple)) and len(payload[0]) == 2:
            return "modbus_holding"
        return "json_array"

    if isinstance(payload, dict):
        return _detect_from_obj(payload)

    return "unknown"


def _detect_from_obj(obj: Any) -> str:
    if isinstance(obj, list):
        return "json_array"
    if not isinstance(obj, dict):
        return "json_object"
    keys = set(obj.keys())
    if any(k in keys for k in ["flow1_lmin", "flow2_lmin", "pressure_kpa", "tank_a_pct", "turbidity_ntu"]):
        return "esp32_compact"
    if any(SCADA_TAG_RE.match(str(k).upper()) for k in keys):
        return "scada_struct"
    if any("ns=" in str(k) or ";i=" in str(k) for k in keys):
        return "opcua_struct"
    if "readings" in keys or "sensors" in keys:
        return "json_object"
    return "json_object"


# Mapeo nombre -> adaptador para uso desde normalizer.py
ADAPTERS = {
    "json_object":     from_json_object,
    "json_array":      from_json_array,
    "json_lines":      from_ndjson,
    "csv":             from_csv,
    "esp32_compact":   from_esp32_compact,
    "modbus_holding":  from_modbus,
    "mqtt":            from_mqtt,
    "scada_struct":    from_scada,
    "opcua_struct":    from_opcua,
}
