# lighthouse

An **Agentic Workflow Harness**: a reference execution harness for AI workers that strictly
decouples **deterministic code execution** (zero-token linters, type-checkers, tests) from
**non-deterministic agent orchestration** (Scout / Planner / Builder personas), running work in
**ephemeral, isolated sandboxes** dispatched by a **Factory Router**.

This is a runnable Python reference scaffold. The deterministic core (Router, Session/Context
Ledger, Guardrail Engine) is real and fully tested; the sandbox is a real local-shell adapter;
agents are a pluggable, scripted provider. The interfaces are the seams where a production Docker /
microVM sandbox and a live LLM provider drop in later.

## Architecture

```
[ Prompting ] ─▶ ( Factory Router / Session Manager )
                          │  provisions Session + Context Ledger
                          ▼
              ( Context Seeder ) ── distils pertinent context ──▶ seed
                          │
                          ▼
   ( Scout ▸ Planner ▸ Builder agents )         [ Ephemeral Sandbox ]
                          │  emits change payload        ▲
                          ▼                              │ inject files / run checks
              ( Deterministic Guardrail Engine ) ◀───────┘
                 pass ─▶ Human Gate      fail ─▶ inject raw error ─▶ re-engage (same session)
```

| Spec subsystem | Module |
| --- | --- |
| Factory Router & Session Manager (3.1) | `lighthouse/router.py` |
| Context Engineering Ledger (3.1) | `lighthouse/ledger.py` |
| Context Seeder (3.1) | `lighthouse/seeder.py` |
| Ephemeral Sandbox `ISandboxEnvironment` (3.2, 5.1) | `lighthouse/sandbox/` |
| Deterministic Guardrail Engine (3.3, 6) | `lighthouse/guardrails/` |
| Agent interface `IAgentSession` (2, 5.2) | `lighthouse/agents/` |
| Standard Pipeline (4.1) | `lighthouse/pipelines/standard.py` |
| Human-in-the-Loop Gate (4.1) | `lighthouse/human_gate.py` |
| Session persistence / state decoupling (6) | `lighthouse/store.py` |

### The core loop (spec 3.3, 6)

The agent never executes code. The Guardrail Engine catches the agent's emitted change payload,
injects the files into the sandbox, and runs the deterministic checks (compile → behaviour → …):

- **pass** → proceed to the Human Gate for approval;
- **fail** → the raw terminal error is recorded on the ledger, the Context Seeder rebuilds the seed
  with that error leading, and the *same session* is re-engaged.

Token-optimization guardrails: the loop is bounded by `max_iterations` (hard cap N) and halts early
after `consecutive_failure_limit` consecutive failures, dumping the sandbox state log and alerting
the engineer via `GuardrailHaltError`.

## Run

```bash
python3 -m pip install -e ".[dev]"   # pytest, mypy, ruff
python -m lighthouse                 # demo: ingest a ticket, drive the standard pipeline
pytest                               # 19 behaviour tests
ruff check . && mypy src             # lint + types
```

The demo ingests a sample bug ticket and shows the guardrail feedback loop in action — the builder
ships a wrong operator, the behaviour check fails, the error is fed back through the seed, and the
second attempt passes and is approved at the Human Gate.

## Scope & extension points

- **Sandbox isolation** — `LocalSandbox` scrubs proxy/network env vars but is a process, not a
  container. Hard network/process isolation (spec 6) is the job of a future Docker/microVM adapter
  behind the same `Sandbox` ABC.
- **Live agents** — swap `ScriptedAgentProvider` for a real LLM-backed `AgentProvider`.
- **Hotfix race matrix** (spec 4.2) — `SandboxProvisioner.provision_many` seeds parallel sandboxes;
  the racing pipeline itself is left as a follow-up.
- **Durable persistence** — `SessionStore` is in-memory; back it with a database for production.
