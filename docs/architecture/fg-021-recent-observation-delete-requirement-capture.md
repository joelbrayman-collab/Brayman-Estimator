# Requirement capture — Recent Observation Delete / UAT cleanup

| Attribute | Value |
|-----------|--------|
| Status | **CAPTURED / QUEUED / NOT AUTHORIZED.** Do **not** implement while FG-021 IndexedDB photo-put repair re-UAT is open. |
| Date | 2026-09-02 |
| Product | The Estimator / CalibAi |
| Captured from | Joel — Field Web Recent Observations Delete / test cleanup; iPhone **swipe left → Delete** UX (2026-09-02) |
| Related | [ADR-042](../adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) **Accepted** · [ADR-043](../adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md) **Accepted** · [FG-020](../feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) **CLOSED / OPERATIONAL FOR UAT** · [FG-021](../feature-gates/FG-021-field-web-v1-today-and-capture.md) **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT OPEN** · [build-media-storage-lifecycle.md](build-media-storage-lifecycle.md) |

This document **captures a requirement**. It does **not** authorize implementation. It does **not** choose a deletion model. It does **not** create a Feature Gate, ADR, or migration.

**Do not delete any existing Field Observations from this capture.**

---

## Current priority (do not skip)

1. Finish FG-021 IndexedDB photo-put repair **small-JPEG iPhone re-UAT**.
2. Joel/ChatGPT review this capture.
3. Only then: architecture recon → Feature Gate answers → approved Cursor prompt.

FG-021 remains **OPEN**. Do **not** close it from this capture.

---

## User requirement

Joel has accumulated numerous test Field Observations during FG-020 / FG-021 UAT.

Recent Observations should have an **obvious Delete** capability so test clutter can leave the list.

### iPhone Field UX (Joel confirmed 2026-09-02)

The CalibAi Field Web should mimic familiar/native iPhone interaction patterns **where they fit the task**. Field Web should feel natural to an iPhone user, not like a desktop web app compressed onto a phone.

```text
Normal tap     → OPEN OBSERVATION
Swipe left     → REVEAL DELETE (does not delete)
Tap DELETE     → simple confirmation
After confirm  → governed deletion action
```

- Do **not** delete merely because the user swiped.
- Swipe only **reveals** the destructive action.
- Delete treatment must be unmistakable / consistent with normal iPhone expectations.
- Do **not** invent unusual custom gestures.

**Accessibility:** swipe cannot be the **only** way to delete. Provide an equivalent for VoiceOver, keyboard/support use, and users who cannot perform the gesture. Visible iPhone UI may prioritize swipe-left while retaining that alternate.

**Desktop:** do **not** require swipe. Use conventional Delete or More → Delete once deletion is governed. Desktop and Field operate on the **same Event**.

This UX decision does **not** choose hard delete vs soft delete vs UAT cleanup vs another mechanism.

### Item-12 Field UX principle (record)

Where a well-established native iPhone interaction fits the task, CalibAi Field Web should generally follow that interaction rather than invent a CalibAi-specific mobile pattern. Apply carefully later to swipe actions, touch targets, camera/photo selection, destructive confirmations, bottom/thumb-oriented primary actions, and familiar navigation. This does **not** authorize arbitrary redesign or imitation of unrelated iOS features.

Do **not** make deletion unnecessarily difficult merely because the record may contain photos/audio.

Do **not** add unrestricted hard-delete without reconciling BUILD Original Source / immutability / supersession architecture.

Preserve governed record integrity for **real operating** observations.

---

## Reconciliation required before any implementation

Inspect (not done as a design decision in this capture):

- ADR-042, ADR-043, FG-020, FG-021
- `FieldCaptureEvent`, `FieldCaptureOriginal`, `FieldCaptureDerivedCandidate`
- supersession (`supersedes_id` / `ON DELETE RESTRICT` in FG-020)
- private Original storage and Compatible Rendition storage
- desktop Event Detail and Field Recent Observations
- existing deletion/archive patterns elsewhere in CalibAi
- UAT / test-data conventions

Evaluate the **smallest lawful** model:

| Option | Meaning |
|--------|---------|
| A | True Event deletion with governed cascading cleanup |
| B | Soft delete / tombstone |
| C | UAT-only cleanup mechanism |
| D | Another existing repository-supported pattern |

**No option is selected here.** Do not invent policy before that inspect.

Visible tension already in Accepted docs (recon must resolve, not ignore):

- ADR-042: Originals are immutable; Events are **superseded, not destructively edited**.
- FG-020: `supersedes_id` **ON DELETE RESTRICT**; archive/status columns were **omitted**.
- Project Closeout / archive-and-purge is **FUTURE / NOT AUTHORIZED**.
- Compatible Renditions are regenerable cache, not Original Source.

---

## Rules that may differ (to be determined)

Determine whether deletion rules should differ for:

- clearly labelled UAT/test observations
- ordinary operating observations
- superseded observations
- observations with Derived Candidates
- observations containing Original media (text / image / audio, including HEIC/HEIF)

---

## Associated data (lawful behavior TBD)

Event; text/image/audio Originals; Derived Candidates; Original binary files; HEIC/HEIF sources; Compatible Renditions; SHA/provenance; supersession relationships.

Hard bounds already stated by Joel:

- Do not leave orphan binary files.
- Do not delete another Event accidentally.

---

## Security (non-negotiable if later authorized)

Authenticated; membership / Organization scoped; Project scoped; CSRF protected; cross-org fail-closed. No public deletion endpoints.

---

## Bulk UAT cleanup (recommendation only)

Also determine whether a **bounded bulk cleanup** is appropriate for clearly identified FG-020 / FG-021 UAT observations so Joel is not required to delete dozens of known UAT records by hand.

**Do not implement bulk delete from this capture.** Return it as a recommendation after recon.

---

## Explicitly not done

- No product-code change for Delete
- No observation rows deleted
- No migration
- No CSRF/auth change
- FG-021 not closed
