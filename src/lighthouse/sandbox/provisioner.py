"""Sandbox Provisioner (spec 3.2).

Instantiates ephemeral, isolated sandboxes for a session. The concrete sandbox class is injectable
so a real Docker/microVM adapter can replace :class:`LocalSandbox` without touching the pipeline.
``provision_many`` supports the parallel race-matrix use case (spec 4.2) as an extension point.
"""

from __future__ import annotations

from collections.abc import Callable
from itertools import count

from .base import Sandbox
from .local import LocalSandbox


class SandboxProvisioner:
    """Creates and initializes ephemeral sandboxes."""

    def __init__(self, factory: Callable[[str, str], Sandbox] | None = None) -> None:
        self._factory = factory or (
            lambda sandbox_id, session_id: LocalSandbox(sandbox_id, session_id)
        )
        self._counter = count(1)

    def provision(self, session_id: str) -> Sandbox:
        """Provision and initialize a single sandbox for ``session_id``."""

        sandbox_id = f"{session_id}-sbx-{next(self._counter)}"
        sandbox = self._factory(sandbox_id, session_id)
        sandbox.initialize()
        return sandbox

    def provision_many(self, session_id: str, n: int) -> list[Sandbox]:
        """Provision ``n`` identical sandboxes (race-matrix / parallelism extension point)."""

        return [self.provision(session_id) for _ in range(n)]
