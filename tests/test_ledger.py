"""Tests for the Context Ledger."""

from __future__ import annotations

from tests.conftest import make_ledger

from lighthouse.models import CommandResult


def test_record_and_latest_error() -> None:
    ledger = make_ledger()
    ledger.record_tool_execution("compile", "py_compile", CommandResult(exit_code=0))
    assert ledger.latest_error() is None

    ledger.record_tool_execution(
        "behaviour", "run tests", CommandResult(exit_code=1, stderr="AssertionError")
    )
    error = ledger.latest_error()
    assert error is not None
    assert "AssertionError" in error
    assert "run tests" in error


def test_latest_error_returns_most_recent_failure() -> None:
    ledger = make_ledger()
    ledger.record_tool_execution("a", "cmd-a", CommandResult(exit_code=1, stderr="first"))
    ledger.record_tool_execution("b", "cmd-b", CommandResult(exit_code=2, stderr="second"))
    error = ledger.latest_error()
    assert error is not None
    assert "second" in error
    assert "first" not in error


def test_add_artifact() -> None:
    ledger = make_ledger()
    ledger.add_artifact("plan", "do the thing")
    assert ledger.artifacts["plan"] == "do the thing"
