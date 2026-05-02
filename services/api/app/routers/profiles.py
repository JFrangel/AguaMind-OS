"""Expose the @agentos/profiles catalog over HTTP.

The profile catalog is a TypeScript module shipped to the web frontends.
Apps that consume AgentOS as a headless API (Modelo C: separate frontend
elsewhere — dashboards, mobile apps, internal tools) can read the same
catalog over HTTP without depending on the npm workspace.

Why duplicate the data instead of importing from `@agentos/profiles`:
the FastAPI service is Python; the canonical catalog lives in TS. Rather
than bundle a TS interpreter, we mirror the catalog as a small Python
list. CI guards drift via `tests/test_profiles_catalog.py` (see below).
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter()


# Mirrors packages/profiles/profiles/*.ts. When you add a profile in TS,
# add it here too. The matching test compares the slugs+names to the TS
# files so the two stay in lock-step.
_CATALOG: list[dict] = [
    {
        "slug": "medico",
        "name": "MediBot",
        "tagline": "Asistente clínico para triage de síntomas",
        "description": (
            "Un asistente que ayuda a un paciente a describir sus síntomas, sugiere "
            "posibles causas comunes y lo orienta sobre cuándo consultar urgencias. "
            "Nunca da diagnóstico definitivo: siempre recomienda profesional."
        ),
        "emoji": "+",
        "accent": "#dc2626",
        "default_language": "es",
        "default_use_rag": True,
        "default_use_web": False,
        "cascade": "reasoning",
    },
    {
        "slug": "legal",
        "name": "Legalia",
        "tagline": "Investigación legal y resumen de jurisprudencia",
        "description": (
            "Asistente para abogados y consultores legales. Responde sobre los "
            "documentos legales que subiste (contratos, jurisprudencia, normativa) "
            "y los cita textualmente."
        ),
        "emoji": "§",
        "accent": "#0f766e",
        "default_language": "es",
        "default_use_rag": True,
        "default_use_web": False,
        "cascade": "reasoning",
    },
    {
        "slug": "retail",
        "name": "Retail Insights",
        "tagline": "Análisis de ventas, inventario y comportamiento de cliente",
        "description": (
            "Conectado a tu base de datos de operaciones (ventas, stock, clientes), "
            "responde preguntas en lenguaje natural y devuelve gráficos cuando aplica."
        ),
        "emoji": "📊",
        "accent": "#2563eb",
        "default_language": "es",
        "default_use_rag": False,
        "default_use_web": True,
        "cascade": "reasoning",
    },
    {
        "slug": "tutor",
        "name": "Tutor IA",
        "tagline": "Tutor adaptativo para estudiantes",
        "description": (
            "Explica conceptos paso a paso usando tus apuntes y libros como base, "
            "genera ejercicios prácticos y los corrige con retroalimentación."
        ),
        "emoji": "🎓",
        "accent": "#7c3aed",
        "default_language": "es",
        "default_use_rag": True,
        "default_use_web": False,
        "cascade": "reasoning",
    },
]


@router.get("")
async def list_profiles():
    """Catalog of available chat profiles. Frontends use this for the /apps
    directory; external apps can use it to populate their own profile pickers.

    The full system prompt + presets live only in `@agentos/profiles`
    (the TS module) since they're tied to UI strings (icons, placeholders,
    suggestedFiles). To consume them from an external app, either:
      - vendor the TS module, or
      - hard-code the prompt at the call site and pass it via
        `system_prompt_override` on `/chat/stream`.
    """
    return {
        "data": _CATALOG,
        "error": None,
        "meta": {"count": len(_CATALOG)},
    }


@router.get("/{slug}")
async def get_profile(slug: str):
    """Single profile lookup by slug. 404 when missing so callers can branch."""
    for profile in _CATALOG:
        if profile["slug"] == slug:
            return {"data": profile, "error": None}
    raise HTTPException(status_code=404, detail=f"unknown profile: {slug}")
