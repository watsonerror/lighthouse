---
status: accepted
date: 2026-07-14
deciders: Lighthouse maintainers
---

# Run deterministic checks fail-fast within a guardrail iteration

## Context and Problem Statement

Spec 3.3/4.1 runs native linter, type-checker, and test suites; if any block fails, the raw error is
fed back to the build agent. Within a single guardrail iteration, should all checks run and report
collectively, or should the loop stop at the first failing check?

## Considered Options

* Fail-fast: stop at the first failing check; its raw error becomes the feedback.
* Run all checks every iteration and aggregate every failure into the feedback.

## Decision Outcome

Chosen option: "fail-fast", because it keeps the error context the agent re-engages on focused on a
single, ordered failure (compile before behaviour before …), which matches how the Context Seeder
surfaces `latest_error`, mirrors common CI gating, and avoids spending sandbox time on downstream
checks that a still-broken build would fail anyway.

### Consequences

* Good, because each re-engagement carries one clear, actionable error.
* Good, because ordering checks cheapest-first (compile, then behaviour) minimizes wasted execution.
* Bad, because the agent sees only the first failure per iteration, so independent failures are
  fixed across successive iterations rather than in one shot.

## More Information

Implemented in `GuardrailEngine._run_checks` (`src/lighthouse/guardrails/engine.py`); ordering is
defined by the `checks` list passed to the engine.
