"""Core value types shared across the harness.

These mirror the interface declarations in the spec (`CommandResult`, `AgentResponse`,
`ProposedChange`) as immutable Python dataclasses, plus the enumerations that drive routing
and sandbox state transitions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class IssueCategory(StrEnum):
    """Ticket classification the Factory Router uses to pick a pipeline."""

    CHORE = "chore"
    BUG = "bug"
    HOTFIX = "hotfix"


class SandboxStatus(StrEnum):
    """Lifecycle of an ephemeral sandbox (mirrors ``ISandboxEnvironment.status``)."""

    PROVISIONING = "provisioning"
    IDLE = "idle"
    EXECUTING = "executing"
    TEARDOWN = "teardown"


class AgentPersona(StrEnum):
    """Specialized LLM personas (mirrors ``IAgentSession.agentPersona``)."""

    SCOUT = "scout"
    PLANNER = "planner"
    BUILDER = "builder"
    HOTFIX = "hotfix"


@dataclass(frozen=True, slots=True)
class Issue:
    """An ingested ticket payload."""

    id: str
    title: str
    description: str
    category: IssueCategory


@dataclass(frozen=True, slots=True)
class CommandResult:
    """Result of a deterministic command run inside a sandbox.

    Mirrors the spec's ``CommandResult``. ``token_cost_zero`` is a structural reminder that
    code execution spends no LLM tokens.
    """

    exit_code: int
    stdout: str = ""
    stderr: str = ""
    token_cost_zero: bool = True

    @property
    def ok(self) -> bool:
        return self.exit_code == 0


@dataclass(frozen=True, slots=True)
class ProposedChange:
    """A single file change emitted by an agent (mirrors ``AgentResponse.proposedChanges[]``)."""

    path: str
    content: str


@dataclass(frozen=True, slots=True)
class AgentResponse:
    """A non-deterministic agent's output payload (mirrors the spec's ``AgentResponse``)."""

    proposed_changes: list[ProposedChange] = field(default_factory=list)
    reasoning_chain: str = ""
