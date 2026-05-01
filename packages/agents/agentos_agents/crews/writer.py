from typing import Any

from crewai import Agent, Crew, Process, Task

from .base import BaseCrew


class WriterCrew(BaseCrew):
    """Two-agent crew for content production: outliner → writer.

    Optimized for blog posts, summaries, emails, or any single-author
    artifact. Lighter than AnalysisCrew because no separate research step
    is needed when the user already has the input.
    """

    def _agents(self) -> tuple[Agent, Agent]:
        outliner = Agent(
            role="Content Strategist",
            goal="Produce a tight outline that covers the user's intent in 3-5 bullets",
            backstory="A senior content strategist who values structure over decoration.",
            llm=self.llm,
            verbose=False,
            allow_delegation=False,
        )
        writer = Agent(
            role="Senior Writer",
            goal="Turn the outline into a clean, well-paced piece in the requested style",
            backstory="An experienced writer who matches voice to the brief and avoids fluff.",
            llm=self.llm,
            verbose=False,
            allow_delegation=False,
        )
        return outliner, writer

    def _tasks(self, brief: str, style: str, agents: tuple[Agent, Agent]) -> list[Task]:
        outliner, writer = agents
        outline = Task(
            description=f"Write an outline for: {brief}",
            expected_output="3-5 bullet points covering the entire piece.",
            agent=outliner,
        )
        write = Task(
            description=f"Write the final piece in a {style} style. Brief: {brief}",
            expected_output="A finished piece, no preamble, no apology.",
            agent=writer,
            context=[outline],
        )
        return [outline, write]

    def kickoff(self, inputs: dict[str, Any]) -> str:
        brief = inputs.get("brief") or inputs.get("query", "")
        style = inputs.get("style", "concise and professional")
        agents = self._agents()
        tasks = self._tasks(brief, style, agents)
        crew = Crew(agents=list(agents), tasks=tasks, process=Process.sequential, verbose=False)
        return str(crew.kickoff(inputs={"brief": brief, "style": style}))
