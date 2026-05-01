from agentos_llm import LLMFactory

from ..language import instruction, resolve
from ..state import AgentState

ANALYST_SYSTEM = """You are an analyst agent. Given a query and findings, produce
a brief structured analysis (3-5 sentences) that highlights tradeoffs,
patterns, or recommendations. Be specific and avoid filler.
"""


async def analyst_node(state: AgentState, factory: LLMFactory) -> AgentState:
    query = state.get("query", "")
    findings = state.get("findings", [])
    findings_block = "\n".join(f"- {f}" for f in findings) or "(no prior findings)"
    language = resolve(state.get("language"), query)

    response = await factory.complete_with_fallback(
        messages=[
            {"role": "system", "content": f"{ANALYST_SYSTEM}\n\n{instruction(language)}"},
            {
                "role": "user",
                "content": f"Query: {query}\n\nFindings:\n{findings_block}\n\nProduce the analysis.",
            },
        ],
        cascade="reasoning",
        temperature=0.4,
        max_tokens=600,
    )
    return {"analysis": response.content.strip()}
