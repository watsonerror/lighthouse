"""Shared fixtures/helpers for the test suite."""

from __future__ import annotations

from lighthouse.ledger import ContextLedger
from lighthouse.models import Issue, IssueCategory


def make_ledger(session_id: str = "sess-test") -> ContextLedger:
    issue = Issue(
        id="LH-T",
        title="test objective",
        description="a test ticket",
        category=IssueCategory.BUG,
    )
    return ContextLedger(session_id=session_id, issue=issue)
