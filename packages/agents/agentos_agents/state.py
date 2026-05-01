from typing import Annotated, TypedDict


def _append(left: list | None, right: list | None) -> list:
    return (left or []) + (right or [])


class AgentState(TypedDict, total=False):
    query: str
    intent: str
    plan: list[str]
    context: Annotated[list[dict], _append]
    findings: Annotated[list[str], _append]
    rag_context: list[dict]
    web_context: list[dict]
    fused_context: list[dict]
    analysis: str
    response: str
    cascade: str
    language: str
    use_rag: bool
    use_web: bool
    # When set, overrides WRITER_SYSTEM / RESPONDER_SYSTEM for this run.
    # Used by /apps/<slug> profiles to inject domain-specific behaviour
    # (medical, legal, retail, …) without forking the codebase.
    system_prompt_override: str | None
    error: str | None
