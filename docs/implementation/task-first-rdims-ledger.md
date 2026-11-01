# Task-First UX, Guided Tasks and standalone RDIMS — progress ledger (from 31 Oct 2026)

Mandate: Joel, 31 Oct 2026 ("CALIBRAYTAI — TASK-FIRST UX + GUIDED TASKS + RDIMS TRANSFORMATION"). One development
cycle through deployment; no routine approval stops (Joel: "all tasks and access are approved").

## Baseline (protected)
- Live: `7087d0d0`, Render `dep-dbj4bnff3r2c73eu4qvg`, database revision `s6f7a8b9c0d1`.
- Verification: 3,732 tests, no skips; 302/302 browser checks; migration rehearsal and production migration passed;
  post-release integrity explained; signed-out Live smoke passed.
- Branch: `feature/task-first-rdims-2026-10-31` (worktree), from main `7087d0d0`.

## Steps
1. Baseline recorded; branch created. AiRIA reference = read-only copy of `Discovery-Search` origin/main `b1ec1d1e`.
2. Tooling follow-up from e2p1 (done): `release_migrate.sh` records the rows the migration seeded
   (`MIGRATION_SEEDED=t=n,...` in the release state); `postrelease_check.sh` reads the seeded tables' counts on the
   live database (read-only) and `migration_check.py postcheck-rows` proves live = backup + new tables + exactly the
   declared seed, table by table; anything else still stops. Tests: `tests/test_release_postcheck_seed.py`.
3. Audits (done, durable): `docs/ux/task-first-ux-audit-2026-10-31.md` (333 templates / 237 screens, 636 routes,
   28 office nav destinations, 4 wizards / 44 steps of which 28 can be automated, removed or merged, 21 attention
   events not surfaced); `docs/rdims/airia-rdims-reuse-map-2026-10-31.md` and
   `docs/rdims/calibrayt-rdims-architecture-2026-10-31.md`.

## Implementation plan (internal; not an approval gate)
- Slice A (branch `task-first/ux`): design tokens + Task Screen macros; navigation to ~6 primary items + More +
  Admin; one attention list built from a provider registry with the missing events, each linking to the exact
  task; project page rebuilt as a Task Screen with a state-driven Next step; internal terms renamed in visible text.
- Slice B (branch `task-first/rdims`, in parallel): standalone documents layer — the release's ONE migration
  `t7a8b9c0d1e2` (additive tables only, no backfill rows), content-addressed storage, versions, links to every
  context, connect-existing (no file moves), FTS5 search with fallback, contextual Documents pages, Company Library,
  equipment, confirmed-date attention items, CaliSIGN links, standalone proof.
- Slice C (after A and B merge): Guided Tasks — Price This Job (one screen), Review This Estimate (one governed
  Approve action), Set Up This Project (software-only fields filled automatically, review step removed), wizard
  retirement/merging per the audit, field Today simplification, supplier hub CaliSIGN-awaiting item.
- Then: role/phone walks, full regression, whole-branch review, fixes, gate, release.

## Rulings
- Only one migration in the release (the gate allows exactly one added migration file): it lives in Slice B; any
  later schema need is folded into it before the gate.
- No backfill rows inside the migration: existing documents are connected by an idempotent service (lazy + CLI),
  so the release rehearsal stays "existing rows identical, new tables empty".
