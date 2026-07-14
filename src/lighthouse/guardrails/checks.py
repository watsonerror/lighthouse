"""Deterministic checks (spec 2 / 3.3).

A :class:`Check` is a hardcoded, zero-token validation block — a linter, type-checker, compiler, or
test suite — expressed as a shell command run inside the sandbox. ``token_cost_zero`` is carried
structurally as a reminder that these evaluate agent output with 100% predictability and spend no
LLM tokens.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..models import CommandResult


@dataclass(frozen=True, slots=True)
class Check:
    """One deterministic validation block."""

    name: str
    command: str
    token_cost_zero: bool = True


@dataclass(frozen=True, slots=True)
class CheckOutcome:
    """The result of running a :class:`Check`."""

    check: Check
    result: CommandResult

    @property
    def passed(self) -> bool:
        return self.result.ok
