from dataclasses import dataclass, field
from typing import Any


@dataclass
class NormalizedDocument:
    """Single normalized representation any agent or RAG ingestor can consume.

    `text` is always populated (the universal substrate). `tabular` is a list
    of records when the source had structured rows (CSV/XLSX/JSON-of-records).
    `metadata` carries provenance: filename, mime, page count, sheet names, etc.
    """

    text: str
    tabular: list[dict[str, Any]] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict:
        return {
            "text": self.text,
            "tabular": self.tabular,
            "metadata": self.metadata,
        }


class UnsupportedFormatError(ValueError):
    """Raised when no adapter can handle the supplied file extension/mime."""
