"""Behaviour tests for the real local-shell sandbox adapter."""

from __future__ import annotations

import pytest

from lighthouse.models import SandboxStatus
from lighthouse.sandbox.local import LocalSandbox


def test_inject_and_execute_roundtrip() -> None:
    sandbox = LocalSandbox("sbx-1", "sess-1")
    sandbox.initialize()
    try:
        assert sandbox.status is SandboxStatus.IDLE
        sandbox.inject_file("hello.txt", "world")
        result = sandbox.execute_command("cat hello.txt")
        assert result.ok
        assert result.stdout.strip() == "world"
        assert result.token_cost_zero is True
    finally:
        sandbox.destroy()


def test_exit_code_propagates() -> None:
    sandbox = LocalSandbox("sbx-2", "sess-1")
    sandbox.initialize()
    try:
        result = sandbox.execute_command("exit 3")
        assert result.exit_code == 3
        assert not result.ok
    finally:
        sandbox.destroy()


def test_destroy_removes_root() -> None:
    sandbox = LocalSandbox("sbx-3", "sess-1")
    sandbox.initialize()
    root = sandbox.root
    assert root.exists()
    sandbox.destroy()
    assert not root.exists()
    assert sandbox.status is SandboxStatus.TEARDOWN


def test_path_escape_rejected() -> None:
    sandbox = LocalSandbox("sbx-4", "sess-1")
    sandbox.initialize()
    try:
        with pytest.raises(ValueError):
            sandbox.inject_file("../escape.txt", "nope")
    finally:
        sandbox.destroy()


def test_network_env_scrubbed() -> None:
    sandbox = LocalSandbox("sbx-5", "sess-1")
    sandbox.initialize()
    try:
        # HTTPS_PROXY is set in this environment; the sandbox must strip it by default.
        result = sandbox.execute_command("printenv HTTPS_PROXY || echo MISSING")
        assert "MISSING" in result.stdout
    finally:
        sandbox.destroy()
