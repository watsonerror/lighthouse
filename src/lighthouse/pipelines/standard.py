"""Standard Pipeline (spec 4.1): Scout -> Plan -> Build loop -> Human Gate."""

from __future__ import annotations

from dataclasses import dataclass

from ..agents.base import AgentProvider
from ..guardrails.engine import GuardrailEngine, GuardrailResult
from ..human_gate import HumanGate, HumanReview
from ..ledger import ContextLedger
from ..models import AgentPersona
from ..sandbox.base import Sandbox
from ..seeder import ContextSeeder


@dataclass(slots=True)
class PipelineResult:
    """Aggregated outcome of a standard-pipeline run."""

    session_id: str
    scout_findings: str
    plan: str
    guardrail: GuardrailResult
    review: HumanReview


class StandardPipeline:
    """Feature / complex-bug pipeline."""

    def __init__(
        self,
        *,
        agents: AgentProvider,
        guardrail_engine: GuardrailEngine,
        human_gate: HumanGate,
        seeder: ContextSeeder,
    ) -> None:
        self.agents = agents
        self.guardrail_engine = guardrail_engine
        self.human_gate = human_gate
        self.seeder = seeder

    def run(self, ledger: ContextLedger, sandbox: Sandbox) -> PipelineResult:
        # Scout phase — map the scope of changes.
        ledger.seed = self.seeder.build(ledger)
        scout = self.agents.session(AgentPersona.SCOUT)
        scout_response = scout.engage(ledger)
        ledger.add_artifact("scout", scout_response.reasoning_chain)

        # Plan phase — generate a low-level implementation spec.
        ledger.seed = self.seeder.build(ledger)
        planner = self.agents.session(AgentPersona.PLANNER)
        plan_response = planner.engage(ledger)
        ledger.add_artifact("plan", plan_response.reasoning_chain)

        # Build loop — the deterministic guardrail engine drives build/test to green.
        builder = self.agents.session(AgentPersona.BUILDER)
        guardrail = self.guardrail_engine.run(builder, sandbox, ledger)

        # Human gate — submit the final approved diff.
        review = self.human_gate.submit(ledger.session_id, guardrail.response)
        return PipelineResult(
            session_id=ledger.session_id,
            scout_findings=scout_response.reasoning_chain,
            plan=plan_response.reasoning_chain,
            guardrail=guardrail,
            review=review,
        )
