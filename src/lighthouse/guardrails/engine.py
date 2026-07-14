"""The Deterministic Guardrail Engine (spec 3.3, 6) — the core loop.

Agents are decoupled from code execution. The engine catches an agent's emitted change payload,
closes the agent interaction loop, injects the files into the sandbox, and hands the assets to
native, deterministic check runners. On pass, control returns to the pipeline (-> human review). On
fail, the raw terminal error is recorded on the ledger and the same session is re-engaged with the
error surfaced through a freshly-rebuilt seed.

Token-optimization guardrails (spec 6): the loop is bounded by ``max_iterations`` (hard cap N) and
halts early after ``consecutive_failure_limit`` consecutive failures, dumping the sandbox state log
and alerting the human engineer via :class:`~lighthouse.errors.GuardrailHaltError`.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from ..agents.base import AgentSession
from ..errors import GuardrailHaltError
from ..ledger import ContextLedger
from ..models import AgentResponse
from ..sandbox.base import Sandbox
from ..seeder import ContextSeeder
from .checks import Check, CheckOutcome


@dataclass(slots=True)
class GuardrailResult:
    """Outcome of a full guardrail run."""

    success: bool
    iterations: int
    response: AgentResponse
    outcomes: list[CheckOutcome] = field(default_factory=list)


class GuardrailEngine:
    """Runs the deterministic verification loop around a stateless build agent."""

    def __init__(
        self,
        checks: list[Check],
        seeder: ContextSeeder,
        *,
        max_iterations: int = 8,
        consecutive_failure_limit: int = 5,
        alert: Callable[[str], None] | None = None,
    ) -> None:
        if max_iterations < 1:
            raise ValueError("max_iterations must be >= 1")
        if consecutive_failure_limit < 1:
            raise ValueError("consecutive_failure_limit must be >= 1")
        self.checks = checks
        self.seeder = seeder
        self.max_iterations = max_iterations
        self.consecutive_failure_limit = consecutive_failure_limit
        self._alert = alert

    def run(
        self,
        agent_session: AgentSession,
        sandbox: Sandbox,
        ledger: ContextLedger,
    ) -> GuardrailResult:
        consecutive_failures = 0
        for iteration in range(1, self.max_iterations + 1):
            # Rebuild the distilled seed so the freshest error context leads the re-engagement.
            ledger.seed = self.seeder.build(ledger)
            response = agent_session.engage(ledger)

            # Interceptor: the harness applies the payload; the agent never executes code itself.
            for change in response.proposed_changes:
                sandbox.inject_file(change.path, change.content)

            outcomes = self._run_checks(sandbox, ledger)
            if outcomes and all(outcome.passed for outcome in outcomes):
                return GuardrailResult(
                    success=True,
                    iterations=iteration,
                    response=response,
                    outcomes=outcomes,
                )

            consecutive_failures += 1
            if (
                consecutive_failures >= self.consecutive_failure_limit
                or iteration >= self.max_iterations
            ):
                state_log = self._dump_state(sandbox, ledger)
                if self._alert is not None:
                    self._alert(state_log)
                raise GuardrailHaltError(
                    f"guardrail loop halted after {iteration} iteration(s) "
                    f"({consecutive_failures} consecutive failure(s))",
                    iterations=iteration,
                    consecutive_failures=consecutive_failures,
                    state_log=state_log,
                )
        # Unreachable: the loop either returns on success or raises on halt.
        raise AssertionError("guardrail loop exited without a decision")

    def _run_checks(self, sandbox: Sandbox, ledger: ContextLedger) -> list[CheckOutcome]:
        """Run checks fail-fast; the first failing check's raw error becomes the feedback."""

        outcomes: list[CheckOutcome] = []
        for check in self.checks:
            result = sandbox.execute_command(check.command)
            ledger.record_tool_execution(check.name, check.command, result)
            outcomes.append(CheckOutcome(check=check, result=result))
            if not result.ok:
                break
        return outcomes

    def _dump_state(self, sandbox: Sandbox, ledger: ContextLedger) -> str:
        """Collect a container state log for the human engineer."""

        listing = sandbox.execute_command("ls -la")
        lines = [
            f"session_id={ledger.session_id}",
            f"sandbox_id={sandbox.sandbox_id} status={sandbox.status.value}",
            "--- workspace listing ---",
            listing.stdout.rstrip() or "(empty)",
            "--- tool execution history ---",
        ]
        for execution in ledger.history:
            verdict = "PASS" if execution.ok else "FAIL"
            lines.append(
                f"[{verdict}] {execution.label}: {execution.command} "
                f"(exit {execution.result.exit_code})"
            )
        latest = ledger.latest_error()
        if latest:
            lines.append("--- latest error ---")
            lines.append(latest)
        return "\n".join(lines)
