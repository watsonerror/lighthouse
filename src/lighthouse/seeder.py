"""The Context Seeder (spec 3.1).

Agents should not sift the entire raw ledger on every engagement — that wastes tokens and dilutes
focus. The :class:`ContextSeeder` distills the *pertinent* context for all tasks from the ledger
into a compact :class:`ContextSeed`: the objective, an environment summary, the artifacts produced
by earlier phases (scout findings, plan), the most recent deterministic error, and a short tail of
recent execution outcomes. The seed is rebuilt before every agent engagement (including each
re-engagement in the guardrail loop) so the freshest error context always leads.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .ledger import ContextLedger


@dataclass(frozen=True, slots=True)
class ContextSeed:
    """The distilled, pertinent context handed to an agent for a task."""

    objective: str
    environment_summary: str
    artifacts: dict[str, str] = field(default_factory=dict)
    latest_error: str | None = None
    recent_history: list[str] = field(default_factory=list)

    def render(self) -> str:
        """Render the seed as a plain-text block an agent persona can consume."""

        sections = [f"# Objective\n{self.objective}"]
        if self.environment_summary:
            sections.append(f"# Environment\n{self.environment_summary}")
        for key, value in self.artifacts.items():
            sections.append(f"# Artifact: {key}\n{value}")
        if self.recent_history:
            sections.append("# Recent checks\n" + "\n".join(self.recent_history))
        if self.latest_error:
            sections.append(f"# Latest error (fix this)\n{self.latest_error}")
        return "\n\n".join(sections)


class ContextSeeder:
    """Builds a :class:`ContextSeed` from a :class:`ContextLedger`."""

    def __init__(self, *, max_recent: int = 5) -> None:
        self.max_recent = max_recent

    def build(self, ledger: ContextLedger) -> ContextSeed:
        issue = ledger.issue
        objective = f"[{issue.category.value}] {issue.title}\n{issue.description}"
        environment_summary = self._summarize_env(ledger.env)
        recent = [
            f"{'PASS' if ex.ok else 'FAIL'} {ex.label}: {ex.command} (exit {ex.result.exit_code})"
            for ex in ledger.history[-self.max_recent :]
        ]
        return ContextSeed(
            objective=objective,
            environment_summary=environment_summary,
            artifacts=dict(ledger.artifacts),
            latest_error=ledger.latest_error(),
            recent_history=recent,
        )

    @staticmethod
    def _summarize_env(env: dict[str, str]) -> str:
        if not env:
            return ""
        return ", ".join(sorted(env.keys()))
