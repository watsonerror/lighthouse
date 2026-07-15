"""Lighthouse — Agentic Workflow Harness.

Deterministic guardrails wrapped around non-deterministic agents, running in ephemeral sandboxes,
dispatched by a Factory Router. See the module docstrings for the spec-section mapping.
"""

from __future__ import annotations

from .errors import GuardrailHaltError, LighthouseError, RoutingError
from .guardrails.checks import Check, CheckOutcome
from .guardrails.engine import GuardrailEngine, GuardrailResult
from .human_gate import GateDecision, HumanGate, HumanReview
from .ledger import ContextLedger, ToolExecution
from .models import (
    AgentPersona,
    AgentResponse,
    CommandResult,
    Issue,
    IssueCategory,
    ProposedChange,
    SandboxStatus,
)
from .pipelines.standard import PipelineResult, StandardPipeline
from .router import FactoryRouter, Session
from .sandbox import LocalSandbox, Sandbox, SandboxProvisioner
from .seeder import ContextSeed, ContextSeeder
from .store import SessionStore

__all__ = [
    "AgentPersona",
    "AgentResponse",
    "Check",
    "CheckOutcome",
    "CommandResult",
    "ContextLedger",
    "ContextSeed",
    "ContextSeeder",
    "FactoryRouter",
    "GateDecision",
    "GuardrailEngine",
    "GuardrailHaltError",
    "GuardrailResult",
    "HumanGate",
    "HumanReview",
    "Issue",
    "IssueCategory",
    "LighthouseError",
    "LocalSandbox",
    "PipelineResult",
    "ProposedChange",
    "RoutingError",
    "Sandbox",
    "SandboxProvisioner",
    "SandboxStatus",
    "Session",
    "SessionStore",
    "StandardPipeline",
    "ToolExecution",
]
