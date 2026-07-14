"""Agent interaction interface (spec 5.2 ``IAgentSession`` / ``AgentResponse``).

Agents are the non-deterministic compute of the harness. They are **stateless**: every engagement
receives the full context through the ledger (and its distilled seed); no task state persists inside
an agent between calls. The harness catches the emitted :class:`~lighthouse.models.AgentResponse`
and hands it to the deterministic Guardrail Engine — the agent never executes code itself.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..ledger import ContextLedger
from ..models import AgentPersona, AgentResponse


class AgentSession(ABC):
    """A single agent persona engagement surface."""

    agent_persona: AgentPersona
    model_target: str
    system_prompt_template: str

    @abstractmethod
    def engage(self, ledger: ContextLedger) -> AgentResponse:
        """Reason over the ledger (via ``ledger.seed``) and emit a change payload."""


class AgentProvider(ABC):
    """Factory that yields a stateless :class:`AgentSession` for a persona."""

    @abstractmethod
    def session(self, persona: AgentPersona) -> AgentSession:
        """Return an agent session configured for ``persona``."""
