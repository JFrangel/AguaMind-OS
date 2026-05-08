"""
HidroTech - Esquemas canonicos para datos normalizados de sensores.

Toda lectura cruda (en cualquier formato de entrada) se convierte a este formato
canonico antes de entrar al sistema de analisis. Esto permite que los agentes,
KPIs y dashboards trabajen con UN solo schema sin importar el origen.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class SensorType(str, Enum):
    FLOW = "flow"
    PRESSURE = "pressure"
    LEVEL = "level"
    VIBRATION = "vibration"
    PHREATIC = "phreatic"
    TURBIDITY = "turbidity"
    PH = "ph"
    CONDUCTIVITY = "conductivity"
    CHLORINE = "chlorine"
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    CURRENT = "current"           # AQUA-ROI: corriente bombas (CT clamps)
    SOIL_HUMIDITY = "soil_humidity"  # AQUA-ROI: humedad de suelo (riego)
    UNKNOWN = "unknown"


class Quality(str, Enum):
    OK = "ok"
    SUSPECT = "suspect"
    OUT_OF_RANGE = "out_of_range"
    STALE = "stale"
    INVALID = "invalid"


class CanonicalReading(BaseModel):
    """Una lectura normalizada lista para analisis. Es el formato unico
    que el resto del sistema (agentes, KPIs, persistencia) consume."""

    timestamp: datetime
    node_id: str = Field(..., description="Identificador del nodo IoT (ej. 'esp32-ptap-01')")
    sensor_id: str = Field(..., description="Identificador unico del sensor en el nodo (ej. 'flow1')")
    sensor_type: SensorType
    value: float = Field(..., description="Valor en unidades SI normalizadas")
    unit: str = Field(..., description="Unidad SI (L/min, kPa, m, NTU, etc.)")
    raw: Any = Field(default=None, description="Valor crudo original (para auditoria)")
    quality: Quality = Quality.OK
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("timestamp", mode="before")
    @classmethod
    def _ensure_tz(cls, v: Any) -> datetime:
        if isinstance(v, datetime):
            return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(float(v), tz=timezone.utc)
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        return datetime.now(timezone.utc)


class IngestPayload(BaseModel):
    """Wrapper de transporte. Acepta una o mas lecturas en cualquier formato."""

    format: str = Field(
        default="auto",
        description="Hint del formato del payload: auto | json | csv | json_lines | "
                    "esp32_compact | modbus | mqtt | opcua | scada_struct",
    )
    node_id: Optional[str] = None
    payload: Any = Field(..., description="El dato crudo en el formato indicado")


class IngestResult(BaseModel):
    accepted: int
    rejected: int
    readings: list[CanonicalReading]
    errors: list[str] = Field(default_factory=list)
    detected_format: str
