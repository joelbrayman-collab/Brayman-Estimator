# Cursor Prompt Template — Bugfix

Copy this template. Prefer the **smallest safe fix**. Do not refactor unrelated code.

---

## Title

`<short bug name>`

## Observed behaviour

What actually happens (include errors, screenshots notes, or logs if available).

## Expected behaviour

What should happen.

## Reproduction steps

Numbered steps. Mark flaky or environment-dependent steps.

## Affected workflow

User journey / module.

## Suspected area (unverified)

Paths or modules believed relevant. Label clearly: **unverified until Cursor inspects**.

## Root-cause requirement

Cursor must identify and document root cause before or as part of the fix. Do not ship a speculative patch without explanation.

## Smallest safe fix

Describe the intended minimal change. No drive-by cleanups.

## Regression-test requirement

Add or update a test that fails before the fix and passes after, when practical.

## Prohibition against unrelated refactoring

Do not rename, reformat, or restructure unrelated files.

## Documentation impact

Update handoff / chat log / current-state if behaviour or known issues change. No false “fixed everywhere” claims.

## Validation

Exact commands and required pass criteria.

## Final report

Root cause · files changed · tests · residual risk · suggested commit message · **do not commit automatically**.

## Authoritative documents

`docs/platform-constitution.md`, relevant module docs, Feature Gate if product behaviour changes.

## Allowed / prohibited areas

Fill explicitly before approval.
