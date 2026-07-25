# Cursor Prompt Template — Refactor

Copy this template. Externally observable behaviour must not change unless Joel separately approves a product change.

---

## Title

`<short refactor name>`

## Reason for refactor

Why the change is needed (maintainability, clarity, duplication, boundary alignment).

## Current problem

Concrete pain in the codebase (cite paths).

## Required externally observable behaviour

Must remain identical: UI, APIs, calculations, permissions, persisted data semantics.

## Invariant preservation

List invariants from module docs / Constitution that must hold.

## Architecture boundary preservation

No ownership transfer or cross-module leakage without ADR + Joel approval.

## Schema change

**None** unless separately approved via [cursor-migration-template.md](cursor-migration-template.md) and ADR. Default: no model/migration edits.

## Tests

- Focused tests for touched areas
- Full regression: `./venv/bin/python -m pytest -q` (or approved equivalent)
- Report exact results

## Measurable completion criteria

e.g. named module extracted; cyclomatic complexity reduced in X; duplicate removed with tests green.

## Rollback considerations

How to revert safely (git revert, feature flag, etc.).

## Allowed / prohibited files

Explicit lists.

## Final report

What changed · behaviour unchanged evidence · tests · risks · suggested commit · **do not commit automatically**.
