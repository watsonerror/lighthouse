---
status: accepted
date: 2026-07-14
deciders: Lighthouse maintainers
---

# Bound the guardrail loop with an iteration cap and a consecutive-failure cap

## Context and Problem Statement

Spec 6 forbids letting an agent loop freely on a failing verification step: after a hard-capped N
iterations — and specifically more than 5 consecutive failures — the harness must halt, dump the
container state log, and alert the human engineer. How should the engine express and enforce this?

## Considered Options

* Two independent bounds: `max_iterations` (hard cap N) and `consecutive_failure_limit`, halting on
  whichever trips first and raising a typed error carrying the dumped state log.
* A single total-iteration cap only.
* Wall-clock/time-based budget.

## Decision Outcome

Chosen option: "two independent bounds". `GuardrailEngine` takes both `max_iterations` (default 8)
and `consecutive_failure_limit` (default 5, matching the spec's "more than 5 consecutive"). When
either is reached it calls `_dump_state` (workspace listing + full tool-execution history + latest
error), invokes the optional `alert` callback (the engineer signal), and raises `GuardrailHaltError`
carrying `iterations`, `consecutive_failures`, and `state_log`. Keeping the two caps separate
preserves the spec's distinction between total attempts and a consecutive-failure streak, and leaves
room for future partial-progress semantics that reset the streak.

### Consequences

* Good, because runaway token spend on an unfixable build is structurally impossible.
* Good, because the halt is observable: a typed exception plus a state-log dump and an alert hook.
* Bad, because the two defaults are heuristics that may need per-pipeline tuning.

### Confirmation

`test_halts_after_consecutive_failures` asserts the streak cap trips at 3, that the alert receives
the state log, and that the log includes the tool-execution history; `test_hard_iteration_cap`
asserts the iteration cap trips independently.

## More Information

Implemented in `GuardrailEngine` and `GuardrailHaltError`
(`src/lighthouse/guardrails/engine.py`, `src/lighthouse/errors.py`).
