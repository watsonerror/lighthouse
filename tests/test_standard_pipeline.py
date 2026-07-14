"""End-to-end test of the standard pipeline via the demo wiring."""

from __future__ import annotations

from lighthouse.__main__ import build_router
from lighthouse.human_gate import GateDecision
from lighthouse.models import Issue, IssueCategory


def test_pipeline_ingest_to_approved_diff() -> None:
    router = build_router()
    issue = Issue(
        id="LH-1",
        title="Add an add(a, b) helper",
        description="Return the sum of two integers.",
        category=IssueCategory.BUG,
    )
    result = router.run(issue)

    assert result.scout_findings
    assert result.plan
    assert result.guardrail.success
    assert result.guardrail.iterations == 2  # fail once, then pass
    assert result.review.decision is GateDecision.APPROVED
    assert "return a + b" in result.review.diff

    # State persisted in the harness (agents stateless); history shows the feedback loop.
    ledger = router.store.get(result.session_id)
    verdicts = [ex.ok for ex in ledger.history if ex.label == "behaviour"]
    assert verdicts == [False, True]
