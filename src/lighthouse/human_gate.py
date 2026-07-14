"""The Human-in-the-Loop Gate (spec 2 / 4.1).

The engineer is constrained to the boundaries: prompting at initiation and review/validation before
persistence. Once deterministic checks pass, the diff is submitted here for a final approval merge.
The approver is injectable — the demo auto-approves; a real deployment blocks for human input.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from .models import AgentResponse


class GateDecision(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING = "pending"


@dataclass(frozen=True, slots=True)
class HumanReview:
    session_id: str
    diff: str
    decision: GateDecision


Approver = Callable[["HumanReview"], GateDecision]


def _auto_approve(review: HumanReview) -> GateDecision:
    return GateDecision.APPROVED


class HumanGate:
    """Computes a diff from the final changes and routes it to an approver."""

    def __init__(self, approver: Approver | None = None) -> None:
        self._approver = approver or _auto_approve

    def submit(self, session_id: str, response: AgentResponse) -> HumanReview:
        diff = self._render_diff(response)
        pending = HumanReview(session_id=session_id, diff=diff, decision=GateDecision.PENDING)
        decision = self._approver(pending)
        return HumanReview(session_id=session_id, diff=diff, decision=decision)

    @staticmethod
    def _render_diff(response: AgentResponse) -> str:
        blocks = []
        for change in response.proposed_changes:
            blocks.append(f"--- {change.path}\n+++ {change.path}\n{change.content.rstrip()}")
        return "\n\n".join(blocks) if blocks else "(no changes)"
