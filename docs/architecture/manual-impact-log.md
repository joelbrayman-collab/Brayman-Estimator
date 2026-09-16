# CalibraytAI User Guide — Manual Impact log

| Attribute | Value |
|-----------|--------|
| Status | **FRAMEWORK / IMPACT CAPTURE.** Not the User Guide. Not Interactive Help. Not Voice. **NOT IMPLEMENTATION-AUTHORIZED.** |
| Updated | 2026-09-16 |
| Governing record | [interactive-help-voice-and-user-manual-future-record.md](interactive-help-voice-and-user-manual-future-record.md) **FUTURE / RECORDED / MANDATORY PRE-UAT V1 / NOT IMPLEMENTATION-AUTHORIZED** |
| Framework | [calibraytai-v1-user-guide-framework.md](calibraytai-v1-user-guide-framework.md) **MANUAL FRAMEWORK: START NOW.** **Manual Audience Law** controlling. |
| Policy | **Append-only.** Newest entry first under Entries. Do not rewrite historical entries except to correct factual error (note the correction). |

This file is **not** the professional CALIBRAYTAI V1 USER GUIDE. It is a lightweight close-time capture so later Manual authoring has contractor-facing impact notes from the actual product.

Do **not** write final Manual prose here.
Do **not** capture screenshots against unfinished surfaces.
Do **not** implement Help / Voice / Manual from this file.

**Final authoring sequence** remains: remaining functional V1 → Contractor Language + UX E2E Audit → one User Help Content authority → User Guide from the finished product → procedure cross-check → final desktop/iPhone screenshots → Help → Voice → internal E2E → task-based UAT package → **give the completed Guide to Kevin and Ben (and already-recorded Ben’s father-in-law) BEFORE platform access** → allow Guide review → then platform access and realistic task-based UAT without coaching.

Kevin / Ben platform access: **NOT YET**.

V1 **not rescored** from this file.

---

## When to add an entry

Add one entry at each **material feature / slice close** that creates or changes a contractor-facing capability.

Do not backfill earlier slices from this recording. Capture begins with current development (SCH-C).

## Template (copy)

```markdown
### MANUAL IMPACT — <SLICE> (YYYY-MM-DD)

| Field | Content |
|-------|---------|
| Slice | |
| Product status at capture | |
| 1. What new contractor capability exists? | |
| 2. When would the contractor use it? | |
| 3. What workflow will the final Manual need to teach? | |
| 4. What contractor-facing terms must be used? | |
| 5. What screenshots / Print examples will eventually be needed? | |
| 6. What warnings / validation distinctions need explanation? | |
| 7. Desktop / iPhone / Print relevance | |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. |
```

---

## Entries

### MANUAL IMPACT — SCH-C (2026-09-16)

| Field | Content |
|-------|---------|
| Slice | FG-035 SCH-C Lightweight Element dependencies + sequence warnings |
| Status | **CURRENT** — SCH-C **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS.** Additive **`f9b0c1d2e3f4`**. Live current = repository head. Live UAT on Project **47** confirmed this contractor copy. No workflow/copy change from UAT. |
| CONTRACTOR CAPABILITY | Set which major work should come before other work. Under **Work order**, say which work **comes after** other work. This does not move dates by itself. |
| WHEN USED | When planning the order of major Project work. |
| FINAL MANUAL WORKFLOW TO TEACH | Add a **Comes after** / **Must follow** relationship. Remove it. Understand a **Schedule warning** when work is scheduled before prior work is finished. Understand a **Schedule warning** when work is scheduled but the prior work does not have dates yet. Optionally **Change dates** or **Review this project**. **Leave dates as they are**, or ignore the warning and continue. |
| CONTRACTOR-FACING TERMS | Work order. Comes after. Must follow. Add work order. Prior work. Schedule warning. Scheduled before prior work is finished. Scheduled, but the prior work does not have dates yet. Leave dates as they are. Change dates. Review this project. This is information only. You can continue without changing anything. Do **not** use: DAG, edge, node, graph, ProjectWorkDependency, dependency_id. |
| WARNINGS / VALIDATION | **Warning:** informational only; does not block work. **Validation:** an invalid relationship or a loop cannot be saved. |
| DESKTOP | YES — Company Schedule and Project Hub Schedule. |
| IPHONE | SCH-D / future. |
| PRINT | Future relevance; do not implement. |
| SCREENSHOTS NEEDED LATER | Work-order / sequence controls. Sequence warning. Project Schedule / Hub context. Do **not** capture now. |
| EVERYDAY TASKS | How do I tell CalibraytAI what work comes first? What does this Schedule warning mean? How do I move work after reviewing a warning? |
| HELP / VOICE | Future topics only. |
| Do not | Final Manual prose. Unstable screenshots. Help / Voice / Manual product. Automatic date movement. |
