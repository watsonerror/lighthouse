"""The Context Engineering Ledger (spec 3.1).

A centralized, explicitly-passed thread state. It holds the full systemic context, environment
variables, artifacts produced by earlier phases (scout findings, plan), and the complete history
of deterministic tool executions. State lives here, not inside any agent — agents are stateless
and receive context via the ledger (and its distilled :class:`~lighthouse.seeder.ContextSeed`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .models import CommandResult, Issue

if TYPE_CHECKING:
    from .seeder import ContextSeed


@dataclass(frozen=True, slots=True)
class ToolExecution:
    """One deterministic command execution recorded on the ledger."""

    label: str
    command: str
    result: CommandResult

    @property
    def ok(self) -> bool:
        return self.result.ok


@dataclass(slots=True)
class ContextLedger:
    """Mutable per-session thread state, passed explicitly between components."""

    session_id: str
    issue: Issue
    systemic_context: dict[str, str] = field(default_factory=dict)
    env: dict[str, str] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)
    history: list[ToolExecution] = field(default_factory=list)
    seed: ContextSeed | None = None

    def record_tool_execution(self, label: str, command: str, result: CommandResult) -> None:
        """Append a deterministic tool-execution output to the ledger."""

        self.history.append(ToolExecution(label=label, command=command, result=result))

    def add_artifact(self, key: str, value: str) -> None:
        """Store a phase artifact (e.g. scout findings, implementation plan)."""

        self.artifacts[key] = value

    def latest_error(self) -> str | None:
        """Return the raw error context of the most recent failing execution, if any.

        This is the payload that gets fed back to the agent by the guardrail loop.
        """

        for execution in reversed(self.history):
            if not execution.ok:
                parts = [
                    f"$ {execution.command}",
                    f"exit_code={execution.result.exit_code}",
                ]
                if execution.result.stdout:
                    parts.append(f"stdout:\n{execution.result.stdout.rstrip()}")
                if execution.result.stderr:
                    parts.append(f"stderr:\n{execution.result.stderr.rstrip()}")
                return "\n".join(parts)
        return None
