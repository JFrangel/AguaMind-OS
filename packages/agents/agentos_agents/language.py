from __future__ import annotations

import re

# Default UI/agent language. Can be overridden per request via state["language"]
# or AGENTOS_DEFAULT_LANGUAGE env.
DEFAULT_LANGUAGE = "es"

SUPPORTED = {
    "es": "Español",
    "en": "English",
    "pt": "Português",
    "fr": "Français",
    "de": "Deutsch",
    "it": "Italiano",
}

# Heuristic detector. Cheap, deterministic, no extra deps. We only need to
# decide whether the user wrote Spanish/English/etc. — not full LID.
_HINTS = {
    "es": re.compile(r"\b(qué|cuál|cómo|dónde|por qué|también|aunque|siguiente|"
                     r"hola|gracias|hacer|ahora|hoy|ayer|mañana)\b", re.IGNORECASE),
    "en": re.compile(r"\b(what|which|how|where|why|also|although|next|"
                     r"hello|thanks|today|yesterday|tomorrow|the|and|with)\b", re.IGNORECASE),
    "pt": re.compile(r"\b(qual|como|onde|por que|também|embora|olá|obrigado)\b",
                     re.IGNORECASE),
    "fr": re.compile(r"\b(quoi|quel|comment|où|pourquoi|aussi|bonjour|merci)\b",
                     re.IGNORECASE),
    "de": re.compile(r"\b(was|wie|wo|warum|auch|hallo|danke|heute|morgen)\b",
                     re.IGNORECASE),
    "it": re.compile(r"\b(cosa|come|dove|perché|anche|ciao|grazie|oggi|ieri)\b",
                     re.IGNORECASE),
}


def detect(text: str) -> str | None:
    """Best-effort language guess from a short user message.

    Returns the ISO-639-1 code with the most keyword hits, or `None` if no
    keyword fired (caller falls back to its configured default).
    """
    if not text or not text.strip():
        return None
    scores = {code: len(rx.findall(text)) for code, rx in _HINTS.items()}
    best_code, best_score = max(scores.items(), key=lambda kv: kv[1])
    return best_code if best_score > 0 else None


def resolve(state_language: str | None, query: str | None = None) -> str:
    """Resolve the effective language for an agent run.

    Order: explicit state value → query auto-detection → DEFAULT_LANGUAGE.
    """
    if state_language and state_language in SUPPORTED:
        return state_language
    detected = detect(query or "")
    if detected:
        return detected
    return DEFAULT_LANGUAGE


def name(code: str) -> str:
    return SUPPORTED.get(code, SUPPORTED[DEFAULT_LANGUAGE])


def instruction(code: str) -> str:
    """Single-line directive injected into every system prompt to lock the
    output language. Putting it last in the system prompt is the cheapest
    way to make the model obey across providers."""
    return f"Always respond in {name(code)} ({code}). Do not switch languages."


# === Status messages (i18n) ===
# The agent trace panel mirrors the runner's status events. Hard-coded English
# strings made the panel feel inconsistent with a Spanish chat. This dict is
# the single source of truth — `status_text(key, language, **fmt)` formats
# any of the runner's status keys in the requested language.

_STATUS = {
    "router.classify": {
        "es": "Clasificando intención y planificando los pasos",
        "en": "Classifying intent and planning next steps",
        "pt": "Classificando intenção e planejando os passos",
        "fr": "Classification de l'intention et planification",
        "de": "Klassifiziere Absicht und plane nächste Schritte",
        "it": "Classificazione dell'intento e pianificazione",
    },
    "router.intent": {
        "es": "intención: {intent} · {language}",
        "en": "intent: {intent} · {language}",
        "pt": "intenção: {intent} · {language}",
        "fr": "intention : {intent} · {language}",
        "de": "Absicht: {intent} · {language}",
        "it": "intento: {intent} · {language}",
    },
    "rag.search": {
        "es": "Buscando en la base de conocimiento interna",
        "en": "Searching internal knowledge base",
        "pt": "Buscando na base de conhecimento interna",
        "fr": "Recherche dans la base de connaissances interne",
        "de": "Suche in der internen Wissensbasis",
        "it": "Cercando nella base di conoscenza interna",
    },
    "rag.result": {
        "es": "{n} fragmentos recuperados",
        "en": "{n} chunks retrieved",
        "pt": "{n} trechos recuperados",
        "fr": "{n} extraits récupérés",
        "de": "{n} Fragmente abgerufen",
        "it": "{n} frammenti recuperati",
    },
    "web.search": {
        "es": "Buscando en la web",
        "en": "Searching the web",
        "pt": "Buscando na web",
        "fr": "Recherche sur le web",
        "de": "Suche im Web",
        "it": "Cercando sul web",
    },
    "web.result": {
        "es": "{n} resultados web",
        "en": "{n} web results",
        "pt": "{n} resultados da web",
        "fr": "{n} résultats web",
        "de": "{n} Web-Ergebnisse",
        "it": "{n} risultati web",
    },
    "researcher.start": {
        "es": "Reuniendo hallazgos relevantes",
        "en": "Gathering relevant findings",
        "pt": "Reunindo descobertas relevantes",
        "fr": "Collecte des éléments pertinents",
        "de": "Sammle relevante Erkenntnisse",
        "it": "Raccogliendo i risultati rilevanti",
    },
    "researcher.result": {
        "es": "{n} hallazgos recopilados",
        "en": "{n} findings collected",
        "pt": "{n} descobertas coletadas",
        "fr": "{n} éléments collectés",
        "de": "{n} Erkenntnisse gesammelt",
        "it": "{n} risultati raccolti",
    },
    "analyst.start": {
        "es": "Razonando sobre los hallazgos",
        "en": "Reasoning over findings",
        "pt": "Raciocinando sobre as descobertas",
        "fr": "Raisonnement sur les éléments",
        "de": "Schließe aus den Erkenntnissen",
        "it": "Ragionando sui risultati",
    },
    "analyst.result": {
        "es": "análisis listo",
        "en": "analysis ready",
        "pt": "análise pronta",
        "fr": "analyse prête",
        "de": "Analyse bereit",
        "it": "analisi pronta",
    },
    "writer.start": {
        "es": "Componiendo la respuesta final",
        "en": "Composing the final response",
        "pt": "Compondo a resposta final",
        "fr": "Composition de la réponse finale",
        "de": "Verfasse die finale Antwort",
        "it": "Componendo la risposta finale",
    },
    "responder.start": {
        "es": "Generando respuesta",
        "en": "Generating response",
        "pt": "Gerando resposta",
        "fr": "Génération de la réponse",
        "de": "Erzeuge Antwort",
        "it": "Generando la risposta",
    },
}


def status_text(key: str, lang: str | None = None, /, **fmt) -> str:
    """Look up a runner status string in the requested `lang`, formatting
    `{n}` / `{intent}` / `{language}` tokens when present. `lang` is
    positional-only so a `language=` kwarg can flow through to .format()
    without colliding with this parameter. Falls back to Spanish → English →
    bare key. Never raises."""
    code = lang if lang and lang in SUPPORTED else DEFAULT_LANGUAGE
    table = _STATUS.get(key)
    if not table:
        return key
    template = table.get(code) or table.get("es") or table.get("en") or key
    try:
        return template.format(**fmt)
    except (KeyError, IndexError):
        return template
