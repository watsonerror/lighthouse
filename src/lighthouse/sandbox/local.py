"""A real, local-shell implementation of the sandbox interface.

``LocalSandbox`` runs commands inside an isolated temporary directory via ``subprocess``. It is a
genuine adapter (files are written, commands really execute, exit codes propagate), but it is *not*
a container: hard network/process isolation requires the future Docker/microVM adapter. To honor
spec 6 (Security Isolation) as far as a local process can, it runs with a scrubbed environment —
network-related variables (proxies) are stripped unless explicitly allow-listed.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from ..models import CommandResult, SandboxStatus
from .base import Sandbox

# Environment variables stripped from the sandbox to discourage network egress in the local
# adapter. Real isolation is the container adapter's job; this is a best-effort local guardrail.
_NETWORK_ENV_VARS = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "http_proxy",
    "https_proxy",
    "ALL_PROXY",
    "all_proxy",
    "NO_PROXY",
    "no_proxy",
)


class LocalSandbox(Sandbox):
    """Sandbox backed by a temp directory and local subprocess execution."""

    def __init__(
        self,
        sandbox_id: str,
        session_id: str,
        *,
        network_allowlist: list[str] | None = None,
        command_timeout: float = 60.0,
    ) -> None:
        self.sandbox_id = sandbox_id
        self.session_id = session_id
        self.status = SandboxStatus.PROVISIONING
        self.network_allowlist = list(network_allowlist or [])
        self.command_timeout = command_timeout
        self._root: Path | None = None

    @property
    def root(self) -> Path:
        if self._root is None:
            raise RuntimeError("Sandbox is not initialized; call initialize() first.")
        return self._root

    def initialize(self) -> None:
        self._root = Path(tempfile.mkdtemp(prefix=f"lighthouse-{self.sandbox_id}-"))
        self.status = SandboxStatus.IDLE

    def execute_command(self, cmd: str) -> CommandResult:
        if self._root is None:
            raise RuntimeError("Sandbox is not initialized; call initialize() first.")
        self.status = SandboxStatus.EXECUTING
        try:
            completed = subprocess.run(
                cmd,
                shell=True,
                cwd=self._root,
                env=self._build_env(),
                capture_output=True,
                text=True,
                timeout=self.command_timeout,
            )
            result = CommandResult(
                exit_code=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
            )
        except subprocess.TimeoutExpired as exc:
            partial = exc.stdout if isinstance(exc.stdout, str) else ""
            result = CommandResult(
                exit_code=124,
                stdout=partial,
                stderr=f"command timed out after {self.command_timeout}s",
            )
        finally:
            self.status = SandboxStatus.IDLE
        return result

    def inject_file(self, path: str, content: str) -> None:
        target = self._resolve(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)

    def destroy(self) -> None:
        self.status = SandboxStatus.TEARDOWN
        if self._root is not None:
            shutil.rmtree(self._root, ignore_errors=True)
            self._root = None

    def _resolve(self, path: str) -> Path:
        """Resolve ``path`` under the sandbox root, rejecting escapes outside it."""

        candidate = (self.root / path).resolve()
        root = self.root.resolve()
        if root != candidate and root not in candidate.parents:
            raise ValueError(f"path {path!r} escapes the sandbox root")
        return candidate

    def _build_env(self) -> dict[str, str]:
        env = {k: v for k, v in os.environ.items() if k not in _NETWORK_ENV_VARS}
        for allowed in self.network_allowlist:
            if allowed in os.environ:
                env[allowed] = os.environ[allowed]
        return env
