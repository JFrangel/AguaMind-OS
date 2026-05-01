import json

from agentos_llm import LLMFactory

from ..language import instruction, resolve
from ..state import AgentState

ROUTER_SYSTEM = """You classify a user request into one of these intents:
- "chat": casual conversation, greetings, simple Q&A
- "research": needs gathering external information, definitions, or facts
- "analysis": requires reasoning over data, comparisons, recommendations
- "writing": producing a structured artifact (summary, report, email)

Respond with ONLY a JSON object: {"intent": "<intent>", "plan": ["step 1", "step 2", ...]}
Plan must be 1-4 short steps describing the path to a useful answer.
"""


async def router_node(state: AgentState, factory: LLMFactory) -> AgentState:
    query = state.get("query", "")
    language = resolve(state.get("language"), query)
    response = await factory.complete_with_fallback(
        messages=[
            {"role": "system", "content": f"{ROUTER_SYSTEM}\n\n{instruction(language)}"},
            {"role": "user", "content": query},
        ],
        cascade="speed",
        temperature=0.0,
        max_tokens=300,
    )
    intent, plan = _parse(response.content)
    return {"intent": intent, "plan": plan, "language": language}


def _parse(content: str) -> tuple[str, list[str]]:
    text = content.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            data = json.loads(text[start : end + 1])
            return str(data.get("intent", "chat")), [str(s) for s in data.get("plan", [])]
        except json.JSONDecodeError:
            pass
    return "chat", []
