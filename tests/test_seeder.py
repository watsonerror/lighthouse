"""Tests for the Context Seeder."""

from __future__ import annotations

from tests.conftest import make_ledger

from lighthouse.models import CommandResult
from lighthouse.seeder import ContextSeeder


def test_seed_includes_objective_and_artifacts() -> None:
    ledger = make_ledger()
    ledger.add_artifact("scout", "scoped it")
    seed = ContextSeeder().build(ledger)
    assert "test objective" in seed.objective
    assert seed.artifacts["scout"] == "scoped it"
    rendered = seed.render()
    assert "# Objective" in rendered
    assert "scoped it" in rendered


def test_seed_surfaces_latest_error() -> None:
    ledger = make_ledger()
    ledger.record_tool_execution(
        "behaviour", "run tests", CommandResult(exit_code=1, stderr="boom")
    )
    seed = ContextSeeder().build(ledger)
    assert seed.latest_error is not None
    assert "boom" in seed.latest_error
    assert "boom" in seed.render()


def test_recent_history_bounded() -> None:
    ledger = make_ledger()
    for i in range(10):
        ledger.record_tool_execution(f"c{i}", f"cmd{i}", CommandResult(exit_code=0))
    seed = ContextSeeder(max_recent=3).build(ledger)
    assert len(seed.recent_history) == 3
    assert "c9" in seed.recent_history[-1]
