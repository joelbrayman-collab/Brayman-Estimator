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
| Product status at capture | **IMPLEMENTED / TESTED / NOT LIVE-MIGRATED.** Additive **`f9b0c1d2e3f4`**. Live current remains **`f7f8a9b0c1d2`**. Do **not** capture screenshots until after live migrate + bounded UAT and later final V1. |
| 1. What new contractor capability exists? | The contractor can say which authorized Project work **comes after** other work. Work order does **not** move dates by itself. |
| 2. When would the contractor use it? | When one Element should wait until prior work is finished, or when the office needs a visible work-order reminder on Company Schedule / Project Hub Schedule. |
| 3. What workflow will the final Manual need to teach? | Open Company Schedule or Project Hub Schedule. Under **Work order**, choose prior work and the work that **must follow**. Add work order. Remove a work order when it no longer applies. If a **Schedule warning** appears: the contractor may **leave dates as they are**, **change dates** using the existing date form, or **review this project**. The contractor may also ignore the warning and continue. |
| 4. What contractor-facing terms must be used? | Work order. Comes after. Must follow. Add work order. Schedule warning. Scheduled before prior work is finished. Scheduled, but the prior work does not have dates yet. Leave dates as they are. Change dates. Review this project. This is information only. You can continue without changing anything. Avoid in the Manual: DAG, edge, node, graph, predecessor_id, successor_id. |
| 5. What screenshots / Print examples will eventually be needed? | Desktop Company Schedule warning in the same family as assignment conflicts, with optional Leave dates / Change dates / Review. Project Hub `#hub-schedule` work-order list and add form. Do **not** clutter Month with every work-order line. Print examples wait for the recorded Print workflow. Do **not** capture these now. |
| 6. What warnings / validation distinctions need explanation? | **Warning (informational):** successor dates start before prior work is finished; prior work has no dates while later work is scheduled. Warnings inform. Humans decide. A warning must not, by itself, block Save, require acknowledgement, or move dates. **Validation (fail-closed, not a warning):** cannot link work across organizations or Projects; cannot use inactive/missing work; a item cannot come after itself; the same active work order cannot be added twice; circular work order is rejected. Inclusive abut (later work starts on the prior work’s end date) is **not** a warning. |
| 7. Desktop / iPhone / Print relevance | **Desktop:** Company Schedule + Project Hub Schedule. **iPhone:** SCH-D Field Schedule is later; do not screenshot iPhone Schedule for SCH-C now. **Print:** later presentation of the same Schedule authority; not implemented. |

Do **not** teach automatic Schedule movement. SCH-C does not slide dates.
