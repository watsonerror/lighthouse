"""Tests for the Deterministic Guardrail Engine — the core loop."""

from __future__ import annotations

import pytest
from tests.conftest import make_ledger

from lighthouse.agents.mock import ScriptedAgent
from lighthouse.errors import GuardrailHaltError
from lighthouse.guardrails.checks import Check
from lighthouse.guardrails.engine import GuardrailEngine
from lighthouse.ledger import ContextLedger
from lighthouse.models import AgentPersona, AgentResponse, ProposedChange
from lighthouse.sandbox.local import LocalSandbox
from lighthouse.seeder import ContextSeeder

CHECKS = [
    Check("compile", "python3 -m py_compile solution.py"),
    Check("behaviour", 'python3 -c "from solution import add; assert add(2, 3) == 5"'),
]


def _builder(ledger: ContextLedger) -> AgentResponse:
    """Stateless builder: buggy until the seed carries an error, then correct."""

    if ledger.latest_error() is None:
        body = "def add(a, b):\n    return a - b\n"
    else:
        body = "def add(a, b):\n    return a + b\n"
    return AgentResponse(proposed_changes=[ProposedChange("solution.py", body)])


def _always_broken(ledger: ContextLedger) -> AgentResponse:
    body = "def add(a, b):\n    return a - b\n"
    return AgentResponse(proposed_changes=[ProposedChange("solution.py", body)])


def _run(engine: GuardrailEngine, responder, ledger: ContextLedger):
    sandbox = LocalSandbox("sbx", ledger.session_id)
    sandbox.initialize()
    agent = ScriptedAgent(AgentPersona.BUILDER, responder)
    try:
        return engine.run(agent, sandbox, ledger)
    finally:
        sandbox.destroy()


def test_passes_first_try() -> None:
    ledger = make_ledger()
    engine = GuardrailEngine(CHECKS, ContextSeeder())

    def _correct(_: ContextLedger) -> AgentResponse:
        return AgentResponse(
            proposed_changes=[ProposedChange("solution.py", "def add(a, b):\n    return a + b\n")]
        )

    result = _run(engine, _correct, ledger)
    assert result.success
    assert result.iterations == 1


def test_fail_then_pass_via_seed_feedback() -> None:
    ledger = make_ledger()
    engine = GuardrailEngine(CHECKS, ContextSeeder())
    result = _run(engine, _builder, ledger)
    assert result.success
    assert result.iterations == 2
    # The ledger recorded the failing behaviour check that drove the re-engagement.
    labels = [(ex.label, ex.ok) for ex in ledger.history]
    assert ("behaviour", False) in labels
    assert ("behaviour", True) in labels


def test_halts_after_consecutive_failures() -> None:
    ledger = make_ledger()
    alerts: list[str] = []
    engine = GuardrailEngine(
        CHECKS,
        ContextSeeder(),
        max_iterations=10,
        consecutive_failure_limit=3,
        alert=alerts.append,
    )
    with pytest.raises(GuardrailHaltError) as excinfo:
        _run(engine, _always_broken, ledger)
    err = excinfo.value
    assert err.consecutive_failures == 3
    assert err.iterations == 3
    assert "tool execution history" in err.state_log
    # The human engineer was alerted with the dumped state log.
    assert alerts and alerts[0] == err.state_log


def test_hard_iteration_cap() -> None:
    ledger = make_ledger()
    engine = GuardrailEngine(
        CHECKS, ContextSeeder(), max_iterations=2, consecutive_failure_limit=99
    )
    with pytest.raises(GuardrailHaltError) as excinfo:
        _run(engine, _always_broken, ledger)
    assert excinfo.value.iterations == 2
