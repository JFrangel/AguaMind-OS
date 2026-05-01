from typing import Any

from crewai import Agent, Crew, Process, Task

from .base import BaseCrew


class AnalysisCrew(BaseCrew):
    """Three-agent crew that researches, analyzes, and writes a final answer.

    Researcher → Analyst → Writer with sequential process. Each agent shares
    the same LLM cascade so failover applies uniformly.
    """

    def _agents(self) -> tuple[Agent, Agent, Agent]:
        researcher = Agent(
            role="Senior Researcher",
            goal="Surface accurate, relevant facts about the user's topic",
            backstory="A meticulous research analyst who values verified information.",
            llm=self.llm,
            verbose=False,
            allow_delegation=False,
        )
        analyst = Agent(
            role="Strategy Analyst",
            goal="Synthesize findings into clear insights, tradeoffs, and recommendations",
            backstory="A consultant who turns raw data into actionable conclusions.",
            llm=self.llm,
            verbose=False,
            allow_delegation=False,
        )
        writer = Agent(
            role="Technical Writer",
            goal="Produce a polished, well-structured response for the user",
            backstory="An experienced technical writer who values clarity and concision.",
            llm=self.llm,
            verbose=False,
            allow_delegation=False,
        )
        return researcher, analyst, writer

    def _tasks(self, query: str, agents: tuple[Agent, Agent, Agent]) -> list[Task]:
        researcher, analyst, writer = agents
        research = Task(
            description=f"Gather 3-5 key findings relevant to: {query}",
            expected_output="A bulleted list of findings, each one short and specific.",
            agent=researcher,
        )
        analyze = Task(
            description="Synthesize the findings into 3-5 sentences of analysis with tradeoffs and recommendations.",
            expected_output="A structured analysis paragraph.",
            agent=analyst,
            context=[research],
        )
        write = Task(
            description=f"Write the final user-facing response to: {query}\nUse the analysis as input. Markdown is fine.",
            expected_output="A polished response, no preamble, no apology.",
            agent=writer,
            context=[research, analyze],
        )
        return [research, analyze, write]

    def kickoff(self, inputs: dict[str, Any]) -> str:
        query = inputs.get("query", "")
        agents = self._agents()
        tasks = self._tasks(query, agents)
        crew = Crew(
            agents=list(agents),
            tasks=tasks,
            process=Process.sequential,
            verbose=False,
        )
        result = crew.kickoff(inputs={"query": query})
        return str(result)
