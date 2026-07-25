# Cursor Prompt Template — Migration

Copy this template **only** when Joel has approved a schema change. Migration safety is mandatory (Constitution Article 11).

---

## Title

`<migration name>`

## Approved model / schema change

Exact approved change. Link ADR / Feature Gate. **Stop if approval is missing.**

## Current migration heads

Record output of inspection commands (ScriptDirectory / `flask db heads`). Do not invent.

## Live / local DB state

Record `flask db current` (or equivalent). If unknown: **To be verified** — verify before applying.

## Dependency review

Models, services, and tests affected by the schema change.

## Generated migration inspection

Review autogenerate output before commit. Confirm upgrade/downgrade intent.

## Explicit prohibitions

- Do **not** drop unrelated tables or columns
- Do **not** stamp, merge, delete, or rewrite migration history without **explicit Joel approval**
- Do **not** expand schema beyond the approved feature

## Upgrade and downgrade review

Document both directions; note irreversible steps.

## Data backfill

Required? Strategy? Idempotent?

## Nullability and default strategy

Nullable vs NOT NULL; server defaults; backfill order.

## Test database validation

Run migrations against test DB; run pytest.

## Commands and exact results

Paste commands and results. No claims without runs.

## Stop conditions

Stop if migration history is inconsistent, multiple unexpected heads, or live DB state conflicts with plan.

## Final report

Revision IDs · files · upgrade/downgrade notes · tests · risks · suggested commit · **do not commit automatically**.
