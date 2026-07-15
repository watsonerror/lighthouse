# Architecture Decision Records

This directory records significant architecture decisions for the Lighthouse harness using the
[MADR](https://adr.github.io/madr/) format. One decision per file, numbered sequentially. Accepted
records are immutable — supersede a decision with a new record rather than editing it.

| ADR | Decision | Status |
| --- | --- | --- |
| [0000](0000-use-markdown-architectural-decision-records.md) | Use Markdown Architectural Decision Records | accepted |
| [0001](0001-synchronous-interfaces.md) | Render the async spec interfaces as synchronous Python | accepted |
| [0002](0002-local-shell-sandbox-adapter.md) | Ship a local-shell sandbox adapter rather than a container | accepted |
| [0003](0003-fail-fast-deterministic-checks.md) | Run deterministic checks fail-fast within a guardrail iteration | accepted |
| [0004](0004-stateless-agents-ledger-and-seed.md) | Keep agents stateless; hold state in the ledger and reseed each engagement | accepted |
| [0005](0005-guardrail-halt-caps.md) | Bound the guardrail loop with an iteration cap and a consecutive-failure cap | accepted |
