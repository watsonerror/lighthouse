"""A scripted, deterministic agent provider for tests and the demo.

Real agents call an LLM; these call a pure Python ``responder`` function of the ledger. Because the
responder reads only the ledger (and its seed / latest error), the agents remain genuinely
stateless — the builder decides what to emit purely from whether an error is present in the seed,
which is exactly how the guardrail feedback loop is meant to drive re-engagement.
"""

from __future__ import annotations

from collections.abc import Callable

from ..ledger import ContextLedger
from ..models import AgentPersona, AgentResponse
from .base import AgentProvider, AgentSession

Responder = Callable[[ContextLedger], AgentResponse]


class ScriptedAgent(AgentSession):
    """An :class:`AgentSession` whose output is produced by a pure ``responder`` callable."""

    def __init__(
        self,
        persona: AgentPersona,
        responder: Responder,
        *,
        model_target: str = "scripted",
        system_prompt_template: str = "",
    ) -> None:
        self.agent_persona = persona
        self.model_target = model_target
        self.system_prompt_template = system_prompt_template
        self._responder = responder

    def engage(self, ledger: ContextLedger) -> AgentResponse:
        return self._responder(ledger)


class ScriptedAgentProvider(AgentProvider):
    """Maps personas to scripted responders."""

    def __init__(self, responders: dict[AgentPersona, Responder]) -> None:
        self._responders = responders

    def session(self, persona: AgentPersona) -> AgentSession:
        try:
            responder = self._responders[persona]
        except KeyError as exc:
            raise KeyError(f"no scripted responder registered for persona {persona}") from exc
        return ScriptedAgent(persona, responder)
