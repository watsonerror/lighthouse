"""Ephemeral sandbox interface (spec 5.1 ``ISandboxEnvironment``).

The spec's methods return Promises; this reference harness renders them synchronously for
testability. An async adapter (real Docker/microVM) can implement the same ABC with coroutine
methods — the pipeline treats the sandbox purely through this seam.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import CommandResult, SandboxStatus


class Sandbox(ABC):
    """A fully isolated runtime for a single workflow execution."""

    sandbox_id: str
    session_id: str
    status: SandboxStatus

    @abstractmethod
    def initialize(self) -> None:
        """Provision the runtime and move to ``IDLE``."""

    @abstractmethod
    def execute_command(self, cmd: str) -> CommandResult:
        """Run a shell command in the sandbox and capture its result (zero LLM tokens)."""

    @abstractmethod
    def inject_file(self, path: str, content: str) -> None:
        """Write a file into the sandbox at ``path`` (relative to the sandbox root)."""

    @abstractmethod
    def destroy(self) -> None:
        """Tear down the runtime and release all resources."""
