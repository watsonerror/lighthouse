"""Tests for the Factory Router & Session Manager."""

from __future__ import annotations

import pytest

from lighthouse.errors import RoutingError
from lighthouse.models import Issue, IssueCategory
from lighthouse.router import FactoryRouter
from lighthouse.sandbox.provisioner import SandboxProvisioner


class _StubPipeline:
    pass


def _router() -> FactoryRouter:
    return FactoryRouter(
        standard_pipeline=_StubPipeline(),  # type: ignore[arg-type]
        provisioner=SandboxProvisioner(),
    )


def _issue(category: IssueCategory) -> Issue:
    return Issue(id="X", title="t", description="d", category=category)


def test_ingest_provisions_unique_sessions_and_persists() -> None:
    router = _router()
    s1 = router.ingest(_issue(IssueCategory.BUG))
    s2 = router.ingest(_issue(IssueCategory.CHORE))
    assert s1.session_id != s2.session_id
    assert router.store.has(s1.session_id)
    assert router.store.get(s1.session_id).systemic_context["status"] == "in_progress"


def test_chore_and_bug_route_to_standard() -> None:
    router = _router()
    for category in (IssueCategory.CHORE, IssueCategory.BUG):
        session = router.ingest(_issue(category))
        assert router.route(session) is router.standard_pipeline


def test_hotfix_not_implemented() -> None:
    router = _router()
    session = router.ingest(_issue(IssueCategory.HOTFIX))
    with pytest.raises(RoutingError):
        router.route(session)
