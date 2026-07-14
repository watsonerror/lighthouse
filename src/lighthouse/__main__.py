"""Runnable demo: ingest a sample ticket and drive the standard pipeline end-to-end.

    python -m lighthouse

Prints the Scout/Plan artifacts, the deterministic check history (showing at least one
fail -> retry -> pass cycle driven by the seed's error context), and the approved diff.
"""

from __future__ import annotations

from .agents.mock import ScriptedAgentProvider
from .guardrails.checks import Check
from .guardrails.engine import GuardrailEngine
from .human_gate import HumanGate
from .ledger import ContextLedger
from .models import AgentPersona, AgentResponse, Issue, IssueCategory, ProposedChange
from .pipelines.standard import StandardPipeline
from .router import FactoryRouter
from .sandbox.provisioner import SandboxProvisioner
from .seeder import ContextSeeder
from .store import SessionStore

BEHAVIOUR_CHECK = (
    'python3 -c "from solution import add; '
    "assert add(2, 3) == 5; assert add(-1, 1) == 0; print('ok')\""
)


def _scout(ledger: ContextLedger) -> AgentResponse:
    return AgentResponse(
        reasoning_chain=(
            "Scope: single pure function add(a, b) in solution.py. No existing modules to "
            "refactor; validation via compile + behavioural assertions."
        ),
    )


def _planner(ledger: ContextLedger) -> AgentResponse:
    return AgentResponse(
        reasoning_chain=(
            "Implementation spec: create solution.py exposing add(a, b) returning the integer "
            "sum. Must satisfy add(2, 3) == 5 and add(-1, 1) == 0."
        ),
    )


def _builder(ledger: ContextLedger) -> AgentResponse:
    # Stateless: the first attempt (no prior error) ships a bug; once the deterministic loop feeds
    # the AssertionError back through the seed, the agent corrects the operator.
    if ledger.latest_error() is None:
        body = "def add(a, b):\n    return a - b  # bug: wrong operator\n"
        reasoning = "Initial implementation."
    else:
        body = "def add(a, b):\n    return a + b\n"
        reasoning = "Saw failing behavioural assertion in the seed; fixed the operator."
    return AgentResponse(
        proposed_changes=[ProposedChange(path="solution.py", content=body)],
        reasoning_chain=reasoning,
    )


def build_router() -> FactoryRouter:
    seeder = ContextSeeder()
    provider = ScriptedAgentProvider(
        {
            AgentPersona.SCOUT: _scout,
            AgentPersona.PLANNER: _planner,
            AgentPersona.BUILDER: _builder,
        }
    )
    checks = [
        Check("compile", "python3 -m py_compile solution.py"),
        Check("behaviour", BEHAVIOUR_CHECK),
    ]
    engine = GuardrailEngine(checks, seeder)
    pipeline = StandardPipeline(
        agents=provider,
        guardrail_engine=engine,
        human_gate=HumanGate(),
        seeder=seeder,
    )
    return FactoryRouter(
        standard_pipeline=pipeline,
        provisioner=SandboxProvisioner(),
        store=SessionStore(),
    )


def main() -> None:
    issue = Issue(
        id="LH-1",
        title="Add an add(a, b) helper",
        description="Provide a pure function that returns the sum of two integers.",
        category=IssueCategory.BUG,
    )
    router = build_router()
    result = router.run(issue)

    print(f"session         : {result.session_id}")
    print(f"scout           : {result.scout_findings}")
    print(f"plan            : {result.plan}")
    print(f"build iterations: {result.guardrail.iterations}")
    print("--- deterministic check history (guardrail feedback loop) ---")
    ledger = router.store.get(result.session_id)
    for execution in ledger.history:
        verdict = "PASS" if execution.ok else "FAIL"
        print(f"  [{verdict}] {execution.label} (exit {execution.result.exit_code})")
    print(f"gate decision   : {result.review.decision.value}")
    print("--- approved diff ---")
    print(result.review.diff)


if __name__ == "__main__":
    main()
