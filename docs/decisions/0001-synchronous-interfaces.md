---
status: accepted
date: 2026-07-14
deciders: Lighthouse maintainers
---

# Render the async spec interfaces as synchronous Python

## Context and Problem Statement

The specification declares `ISandboxEnvironment` and `IAgentSession` with `Promise`-returning
methods (`initialize()`, `executeCommand()`, `engage()`, …). Python offers both synchronous and
`async`/`await` styles. Which should the reference scaffold expose?

## Decision Drivers

* The scaffold must be trivially runnable and testable without an event loop.
* The interfaces are seams; a production adapter may need real concurrency later.
* Readability for a reference implementation.

## Considered Options

* Synchronous methods on the `Sandbox` / `AgentSession` ABCs.
* `async def` methods mirroring the spec's Promises.

## Decision Outcome

Chosen option: "synchronous methods", because the deterministic guardrail loop, the local-shell
sandbox, and the scripted agents all execute inline, and synchronous code keeps the core loop and
its tests free of event-loop boilerplate. The ABCs remain the isolation seam: an async adapter
(real Docker/microVM or a live LLM client) can implement the same contract with coroutine methods
and an async engine variant without changing the pipeline's shape.

### Consequences

* Good, because tests and the `python -m lighthouse` demo run with no asyncio scaffolding.
* Good, because control flow in the guardrail engine reads top-to-bottom.
* Bad, because true parallelism (e.g. the spec 4.2 hotfix race matrix) will need an async or
  thread/process-pool variant layered on later.

## More Information

Affects `src/lighthouse/sandbox/base.py` and `src/lighthouse/agents/base.py`.
