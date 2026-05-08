"""
WaterMind OS - Normalizador universal de sensores.

Pipeline:
  payload (cualquier formato) -> detector -> adapter -> registry -> CanonicalReading

Uso programatico:
    >>> from app.sensors.normalizer import normalize
    >>> result = normalize(payload, format="auto", node_id="esp32-ptap-01")

Uso HTTP:
    POST /water/ingest/universal
    {
      "format": "auto",   # o "json"|"csv"|"modbus"|"esp32_compact"|"scada"|"mqtt"|"opcua"
      "node_id": "esp32-ptap-01",
      "payload": {...}    # cualquier estructura
    }
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

from .adapters import ADAPTERS, detect_format, from_json_object, from_mqtt
from .registry import lookup, quality_for
from .schemas import CanonicalReading, IngestPayload, IngestResult, Quality


# Alias amigables para los nombres de formato
FORMAT_ALIASES = {
    "auto":     None,
    "json":     "json_object",
    "ndjson":   "json_lines",
    "esp32":    "esp32_compact",
    "modbus":   "modbus_holding",
    "scada":    "scada_struct",
    "opcua":    "opcua_struct",
}


def _resolve_format(name: str | None, payload: Any) -> str:
    if not name or name == "auto":
        return detect_format(payload)
    canon = FORMAT_ALIASES.get(name, name)
    return canon or detect_format(payload)


def normalize(payload: Any, format: str = "auto", node_id: str | None = None,
              mqtt_topic: str | None = None) -> IngestResult:
    """Convierte cualquier payload a una lista de CanonicalReading."""
    if mqtt_topic:
        records = from_mqtt(mqtt_topic, payload)
        fmt = "mqtt"
    else:
        fmt = _resolve_format(format, payload)
        adapter = ADAPTERS.get(fmt, from_json_object)
        try:
            records = adapter(payload, node_id=node_id)  # type: ignore[arg-type]
        except TypeError:
            records = adapter(payload)  # type: ignore[arg-type]

    readings: list[CanonicalReading] = []
    errors: list[str] = []
    rejected = 0

    for rec in records:
        try:
            reading = _record_to_canonical(rec)
            readings.append(reading)
        except Exception as e:
            rejected += 1
            errors.append(f"{rec.get('sensor_id', '?')}: {e}")

    return IngestResult(
        accepted=len(readings),
        rejected=rejected,
        readings=readings,
        errors=errors[:10],
        detected_format=fmt,
    )


def _record_to_canonical(rec: dict[str, Any]) -> CanonicalReading:
    model = rec.get("model") or "GENERIC"
    spec = lookup(model)
    raw_value = rec["value_raw"]

    # Si el firmware ya entrega valor en SI, no convertir
    if rec.get("_already_si"):
        value_si = float(raw_value)
    elif spec.convert is not None:
        try:
            value_si = float(spec.convert(float(raw_value)))
        except (TypeError, ValueError):
            value_si = float("nan")
    else:
        value_si = float(raw_value)

    quality_str = quality_for(spec, value_si)
    if math.isnan(value_si):
        quality_str = "invalid"

    return CanonicalReading(
        timestamp=rec.get("timestamp") or datetime.now(timezone.utc),
        node_id=rec.get("node_id") or "unknown",
        sensor_id=rec.get("sensor_id") or "unknown",
        sensor_type=spec.type,
        value=value_si,
        unit=rec.get("unit") or spec.unit_si,
        raw=raw_value,
        quality=Quality(quality_str),
        metadata={"model": spec.model, "raw_unit": spec.raw_unit},
    )


def normalize_payload(p: IngestPayload) -> IngestResult:
    return normalize(p.payload, format=p.format, node_id=p.node_id)
