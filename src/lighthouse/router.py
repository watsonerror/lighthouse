"""Factory Router & Session Manager (spec 3.1).

Ingests an issue payload, provisions a unique global session id, builds the Context Ledger, persists
it, and routes to a pipeline tailored to the issue category — balancing state-of-the-art planners
against cheaper workhorse build models.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass

from .errors import RoutingError
from .ledger import ContextLedger
from .models import Issue, IssueCategory
from .pipelines.standard import PipelineResult, StandardPipeline
from .sandbox.provisioner import SandboxProvisioner
from .store import SessionStore


def _default_session_id() -> str:
    return uuid.uuid4().hex


@dataclass(frozen=True, slots=True)
class Session:
    """A provisioned session: its id and its ledger."""

    session_id: str
    ledger: ContextLedger


class FactoryRouter:
    """Gateway of the harness: ingest -> provision session -> route -> run."""

    def __init__(
        self,
        *,
        standard_pipeline: StandardPipeline,
        provisioner: SandboxProvisioner,
        store: SessionStore | None = None,
        session_id_factory: Callable[[], str] | None = None,
    ) -> None:
        self.standard_pipeline = standard_pipeline
        self.provisioner = provisioner
        self.store = store or SessionStore()
        self._session_id_factory = session_id_factory or _default_session_id

    def ingest(self, issue: Issue) -> Session:
        """Provision a session and register it on the store (status -> in_progress)."""

        session_id = self._session_id_factory()
        ledger = ContextLedger(session_id=session_id, issue=issue)
        ledger.systemic_context["status"] = "in_progress"
        ledger.systemic_context["category"] = issue.category.value
        self.store.save(ledger)
        return Session(session_id=session_id, ledger=ledger)

    def route(self, session: Session) -> StandardPipeline:
        """Select the pipeline for the session's issue category."""

        category = session.ledger.issue.category
        if category in (IssueCategory.CHORE, IssueCategory.BUG):
            return self.standard_pipeline
        if category == IssueCategory.HOTFIX:
            raise RoutingError(
                "hotfix pipeline (spec 4.2) is not implemented in this reference scaffold"
            )
        raise RoutingError(f"unroutable issue category: {category!r}")

    def run(self, issue: Issue) -> PipelineResult:
        """End-to-end: ingest, route, provision a sandbox, and execute the pipeline."""

        session = self.ingest(issue)
        pipeline = self.route(session)
        sandbox = self.provisioner.provision(session.session_id)
        try:
            result = pipeline.run(session.ledger, sandbox)
        finally:
            sandbox.destroy()
        self.store.save(session.ledger)
        return result
