"""Harness exception hierarchy."""

from __future__ import annotations


class LighthouseError(Exception):
    """Base class for all harness errors."""


class RoutingError(LighthouseError):
    """Raised when the Factory Router cannot route a payload to a pipeline."""


class GuardrailHaltError(LighthouseError):
    """Raised when the Guardrail Engine gives up on a failing verification loop.

    Carries the dumped sandbox state log so the human engineer has the full context
    required by the spec's token-optimization rule.
    """

    def __init__(
        self,
        message: str,
        *,
        iterations: int,
        consecutive_failures: int,
        state_log: str,
    ) -> None:
        super().__init__(message)
        self.iterations = iterations
        self.consecutive_failures = consecutive_failures
        self.state_log = state_log
