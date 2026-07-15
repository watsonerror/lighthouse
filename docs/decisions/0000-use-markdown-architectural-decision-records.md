---
status: accepted
date: 2026-07-14
deciders: Lighthouse maintainers
---

# Use Markdown Architectural Decision Records

## Context and Problem Statement

The harness makes several architecture decisions that are currently captured only as prose in
module docstrings and the planning document. We want to record significant decisions durably, in a
lightweight, reviewable, version-controlled format, so future contributors understand *why* the
code is shaped the way it is. Which convention should we adopt?

## Considered Options

* MADR (Markdown Architectural Decision Records)
* Michael Nygard's original lightweight template
* No structured records (keep decisions in docstrings only)

## Decision Outcome

Chosen option: "MADR", because it is Markdown-native (diffs and reviews well in Git), provides
explicit sections for the options considered and their trade-offs, and is the format documented at
<https://adr.github.io/madr/>. Records live in `docs/decisions/`, one decision per file, numbered
sequentially (`NNNN-title.md`). Accepted records are immutable — a change of mind is captured by a
new record that supersedes the old one.

### Consequences

* Good, because the reasoning behind non-obvious choices is discoverable next to the code.
* Good, because the Considered Options / Pros and Cons sections force trade-offs to be explicit.
* Bad, because it adds a small documentation burden for each significant decision.

## More Information

Convention reference: <https://adr.github.io/> and <https://adr.github.io/madr/>.
