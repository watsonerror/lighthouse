---
status: accepted
date: 2026-07-14
deciders: Lighthouse maintainers
---

# Ship a local-shell sandbox adapter rather than a container

## Context and Problem Statement

Spec 3.2 requires every workflow execution to occur in a fully isolated, containerized environment
(Docker or microVM). Building real container provisioning requires infrastructure and credentials
and cannot be exercised hermetically in this scaffold. How do we honor the interface and the intent
without that infrastructure?

## Considered Options

* A `LocalSandbox` that runs commands in an isolated temp directory via `subprocess`, behind the
  `Sandbox` ABC.
* A real Docker/microVM provisioner wired in now.
* An in-memory fake that records commands without executing them.

## Decision Outcome

Chosen option: "`LocalSandbox`", because it is a *genuine* adapter — files are really written,
commands really execute, exit codes really propagate — so the deterministic checks are meaningful,
while it needs no external infrastructure. It is provisioned through `SandboxProvisioner`, whose
sandbox factory is injectable, so a real container adapter drops in behind the same ABC without
touching the pipeline.

### Consequences

* Good, because deterministic checks run against real process output, not a mock.
* Good, because `SandboxProvisioner.provision_many` already seeds the parallelism the hotfix race
  matrix (spec 4.2) will need.
* Bad, because a local process is not a container: hard network/process isolation (spec 6) is not
  fully enforced — mitigated, not solved, by the scrubbed environment described under Confirmation.

### Confirmation

`LocalSandbox._build_env` strips proxy/network environment variables unless explicitly
allow-listed, and `test_network_env_scrubbed` asserts `HTTPS_PROXY` is absent inside the sandbox.
The limitation is documented in the module docstring and README so it is not mistaken for real
isolation.

## More Information

Affects `src/lighthouse/sandbox/local.py` and `src/lighthouse/sandbox/provisioner.py`.
