---
status: accepted
date: 2026-07-14
deciders: Lighthouse maintainers
---

# Keep agents stateless; hold state in the ledger and reseed each engagement

## Context and Problem Statement

Spec 6 requires agents to be stateless with all state in the harness, and spec 3.1 defines a Context
Engineering Ledger passed explicitly between components plus a Context Seeder that distils the
pertinent context. How should an agent receive what it needs to act, and where does memory live?

## Considered Options

* Stateless agents that read a `ContextSeed` rebuilt from the ledger before each engagement.
* Agents that retain conversation/task memory internally across engagements.
* Pass the entire raw ledger to the agent on every engagement.

## Decision Outcome

Chosen option: "stateless agents + reseed each engagement". The `ContextLedger` is the single source
of truth (issue, env, artifacts, full tool-execution history); the `ContextSeeder` distils it into a
compact `ContextSeed` (objective, environment summary, artifacts, latest error, recent history) that
is rebuilt before *every* engagement — including each re-engagement inside the guardrail loop — so
the freshest error context always leads. The scripted builder decides what to emit purely from
`ledger.latest_error()`, proving the agents hold no task state of their own.

### Consequences

* Good, because sessions are reproducible and resumable: replaying the ledger reproduces behaviour.
* Good, because reseeding keeps engagements focused and token-lean instead of re-sending raw history.
* Good, because statelessness lets identical sandboxes/agents be spun up in parallel (spec 3.2).
* Bad, because the seeder's distillation rules are now a component that must be maintained and can
  omit context if mis-tuned (mitigated by `max_recent` and always surfacing `latest_error`).

## More Information

Affects `src/lighthouse/ledger.py`, `src/lighthouse/seeder.py`, `src/lighthouse/agents/*`, and the
`ledger.seed = seeder.build(ledger)` step in `GuardrailEngine.run` and the standard pipeline.
