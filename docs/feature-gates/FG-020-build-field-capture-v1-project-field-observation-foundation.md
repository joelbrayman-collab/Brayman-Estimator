# Feature Gate FG-020: BUILD Field Capture V1 — Project Field Observation Foundation

| Attribute | Value |
|-----------|--------|
| Feature Gate ID | `FG-020` |
| Feature Name | BUILD Field Capture V1 — Project Field Observation Foundation |
| Target Milestone | **None.** FG-020 is the governing identifier. Do not assign a new M0xx number. |
| Module | **BUILD** owns Field Capture Events, Original Payloads, Derived Candidates, and BUILD binary original custody ([ADR-020](../adr/ADR-020-build-module-boundary.md) **Accepted**; [ADR-042](../adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) **Accepted**). **Office / platform** owns the `/api/v1` transport adapter (FG-019). **Projects** owns `projects` and the Project Hub. **Project Controls** owns Change Orders. |
| Date | 2026-08-31 |
| Status | **DRAFT FOR JOEL REVIEW / NOT APPROVED.** A committed draft does **not** approve implementation. |
| Architecture | [ADR-042](../adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) **Accepted** · [ADR-020](../adr/ADR-020-build-module-boundary.md) **Accepted** · [ADR-022](../adr/ADR-022-field-client-and-shared-api.md) **Accepted** · [ADR-023](../adr/ADR-023-field-evidence-provenance.md) **Accepted** · [ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md) **Accepted** · [ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) **Accepted** · [ADR-041](../adr/ADR-041-user-membership-and-office-authentication.md) **Accepted** · [CAR-001](../architecture/CAR-001-calibai-product-architecture-reconciliation.md) · [platform-roadmap.md](../platform-roadmap.md) item 11 · [modules/build.md](../modules/build.md) |
| Related ADRs | [ADR-042](../adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) **Accepted** · [ADR-008](../adr/ADR-008-supplier-price-snapshotting.md) **Proposed** (do **not** accept) · [ADR-010](../adr/ADR-010-build-versus-buy-document-processing.md) **Proposed** (do **not** accept) |
| Prerequisites | [FG-018](FG-018-organization-authentication-actor-identity-and-membership-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-019](FG-019-shared-api-foundation-v1.md) **CLOSED / OPERATIONAL FOR UAT**. Roadmap item 10 **COMPLETE**. **ADR-042 Accepted.** BUILD architecture reconnaissance 2026-08-31. |
| Approved baseline | Live Alembic current = head **`b0c1d2e3f4a5`**. Full suite **494 passed**. Dedicated FG-019 **34 passed**. Dedicated FG-018 **37 passed**. |

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **DRAFT FOR JOEL REVIEW / NOT APPROVED** |
| ADR-042 | **Accepted** (architecture only; not implementation) |
| Implementation | **NOT STARTED** |
| Schema / Alembic | **NO MIGRATION IN THIS PASS.** A later approved implementation requires an additive revision with `down_revision` **`b0c1d2e3f4a5`**. Do **not** run `flask db upgrade` now. |
| BUILD product code | **NOT STARTED** |
| Field Web (Item 12) | **BLOCKED / NOT AUTHORIZED.** FG-020 approval (later) still would **not** authorize Field Web. |

Joel has **not** approved this Feature Gate. Do not implement BUILD from this draft.

---

## Purpose

Establish the minimum lawful **BUILD server/domain foundation** required before Item 12 Field Web may be governed.

BUILD records **what happened on site** on the same authoritative `Project` used by PLAN / PRICE / CONTRACT.

FG-020 must create a durable BUILD system of record usable by **both**:

- **Desktop / office** (this gate: bounded Flask HTML review/create)
- **future Field / iPhone** (Item 12: purpose-built Field Web — **not this gate**)

without implementing the Field Web interface.

```text
CAPTURE FIRST → STRUCTURE SECOND → REVIEW / CONFIRM THIRD
```

Success is **BUILD Field Capture V1 foundation**, not Field Web, not transcription, not MONITOR, and not a construction-management suite.

---

## Feature Gate answers

| # | Question | Answer |
|---|----------|--------|
| 1 | What problem does this solve? | After commercial commit, CalibAi has no governed field-execution evidence. Hub BUILD today is Change Orders. Item 12 cannot start without a BUILD SoR. |
| 2 | Who is the user? | Office estimator / PM / principal / staff on the **desktop** BUILD surface. Future field crews use Item 12 against the **same** records. Not the customer. Not a public API consumer. Not native iOS. |
| 3 | Which module owns it? | **BUILD** owns Events, Original Payloads, Derived Candidates, and BUILD file custody. Projects owns `projects` and the Hub. Office/platform owns `/api/v1` transport. Project Controls owns Change Orders. |
| 4 | What data does it own? | Field Capture Event; Original Payload (`text` / `audio` / `image`); Derived Candidate (`PROPOSED` / `CONFIRMED` / `REJECTED`); BUILD private original bytes. |
| 5 | What data does it reference? | `organizations`, `projects`, `users` (nullable `user_id` on new BUILD tables only). Does **not** own Change Orders, estimates, proposals, plan PDFs, permit analysis, MONITOR snapshots. |
| 6 | What may implementation change? | Additive BUILD models/services/repository; Hub BUILD section **beside** COs; office event create/list/detail; `/api/v1` BUILD mutations/reads; private original custody; tests; docs; **one** additive Alembic revision after a **separate** file-custody implementation reconnaissance. |
| 7 | What must it not change? | Field Web UI; mic/camera chrome; transcription/AI; MONITOR/GM/actual cost; Estimate/Proposal/CO/Permit/take-off writes; PlanDocument; tokens; office-to-API migration of existing pages; RBAC; org-switcher; ADR-008/010 status; historical actor strings; Alembic history before the approved revision. |
| 8 | Acceptance criteria? | See **Acceptance criteria** below. **Not met** — implementation not started. |
| 9 | Tests required? | Proposed `tests/test_build_field_observation_fg020.py` plus listed regressions and full suite. Exact count deferred. |
| 10 | Documentation? | This gate; feature-gate index; BUILD module; current-state; session-handoff; project-state-report; roadmap; chat-workflow-log; milestones; docs/README. |
| 11 | ADR required? | **Yes — already Accepted:** [ADR-042](../adr/ADR-042-build-field-evidence-and-iphone-first-capture.md). Do **not** create another ADR in the implementation prompt unless scope changes. |
| 12 | Migration? | **YES** when implementation is approved. Additive only. `down_revision` **`b0c1d2e3f4a5`**. Exact tables/columns/indexes/FK/delete/supersedes/payload representation determined in **implementation reconnaissance**. Do **not** create the revision in this draft. |

---

## Owner

| Concern | Owner |
|---------|--------|
| Field Capture Event, Original Payload, Derived Candidate | **BUILD** |
| BUILD private original custody (audio/image) | **BUILD** |
| Project Hub BUILD section (beside Change Orders) | **BUILD** (Hub assembly remains Projects-owned read model; BUILD supplies BUILD facts) |
| `/api/v1` BUILD endpoints | **BUILD** services + existing office/platform `/api/v1` blueprint |
| Flask-Login session / CSRF | **Office / platform** (FG-018; unchanged) |
| User / UserMembership / Organization | **Organization subsystem** (referenced) |
| Change Orders | **Project Controls** (unchanged) |
| Plan PDFs | **Plan Intelligence** (do not store BUILD photos there) |
| MONITOR comparison / GM | **Out of this gate** |
| Field Web Today / Capture chrome | **Out of this gate** (Item 12) |

---

## Exact domain (three concepts)

Exact table names are **not** frozen in this draft. Implementation reconnaissance names them. The concepts are frozen.

### A. Field Capture Event

Parent: Organization + existing `Project` ([ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md)). No second Job.

Provenance: nullable `user_id`; actor display-name snapshot ([ADR-042](../adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) Decision 6). New BUILD tables only. No backfill. No repository-wide `user_id` conversion.

Time: `created_at` (when CalibAi recorded the Event) **and** `occurred_at` (when the field fact occurred). Both required in schema.

Correction: optional `supersedes` Event relationship. Identity stable. No commercial Draft/Approved lifecycle.

### B. Original Payload

Child of Event. Kinds: `text` | `audio` | `image`.

Must support human-entered text, privately stored original audio, privately stored original image. **Immutable.** Do not overwrite with transcript, AI, labels, or later correction.

Binary originals: private app-managed custody; SHA/checksum; size; MIME metadata; authorized access/download; no silent overwrite; org/project/event scoped; path-traversal protection. **Not** `PlanDocument`.

MIME/size limits are **not** invented in this draft. See **File-custody implementation reconnaissance**.

### C. Derived Candidate

Child of Event. Generic: `kind`; governed payload; status `PROPOSED` / `CONFIRMED` / `REJECTED`; proposer/source provenance as required; confirmed/rejected actor + timestamp.

Do **not** freeze labour/progress/material/issue/CO/RFI taxonomies in FG-020. A later processor may use kinds such as `possible_change_issue`; that is **not** a Change Order.

An Event with one or more Originals is **valid with zero Derived Candidates**.

---

## Original-first invariant

```text
SAVE ORIGINAL is a completed evidence-preservation action.
```

Create must **not** require transcription, AI, structured extraction, confirmation, or commercial workflow. Derived processing, when it later exists, runs **after** original preservation.

---

## Audio / transcript boundary

FG-020 **may** store original audio. FG-020 does **not** implement a transcription provider, ASR, voice AI, or external AI.

Original audio is evidence. Any future machine transcript is **derived**. Machine transcript must never replace or delete original audio. Human-entered text may be an Original `text` payload.

---

## Photo boundary

FG-020 **may** store original photos. FG-020 does **not** implement photo AI, image interpretation, automatic issue detection, or classification.

Original bytes remain preserved. Later AI/image interpretation is separate derived data.

---

## File-custody implementation reconnaissance (required before code)

Do **not** invent final MIME/size limits in this draft.

Before product implementation, a **separate implementation reconnaissance** must inspect:

- Plan storage
- historical-ingestion storage ([ADR-032](../adr/ADR-032-app-managed-historical-workbook-storage.md))
- Brand Profile storage
- existing MIME validation
- existing file-size limits (plans/historical 25 MB; brand logos 5 MB are **not** automatically BUILD limits)
- SHA / path-traversal / private-download patterns

Then recommend the smallest defensible BUILD audio/image rules. If no repository convention is appropriate: **return to Joel**. Do not guess.

---

## Desktop / office surface

FG-020 **must** include a real, useful bounded desktop BUILD surface. It is **not** a test harness.

Project Hub remains the office project anchor. BUILD exists **beside** Change Orders, not instead of them.

Minimum proposed desktop scope:

- BUILD / Field Observations section on Project Hub
- chronological Event list (actor, `occurred_at`, `created_at`)
- event detail/review
- office create of a **text** observation
- display of Original Payload metadata/content as applicable
- authorized binary evidence visibility/download where implemented
- Derived Candidate list if present
- confirm/reject if candidates exist
- supersession/history visibility sufficient for UAT

Desktop is optimized for review, management, context, history, confirmation, investigation. Do **not** design it as an iPhone field interface.

Office HTML continues to call Flask services **directly**. Do not migrate existing office pages onto `/api/v1`.

---

## Field / iPhone boundary

FG-020 does **not** implement Item 12 Field Web.

Do **not** implement: Today; field Capture chrome; microphone/browser recording UI; camera UI; one-handed field navigation; outdoor field styling; Field Web local retry.

FG-020 **must** create the server/domain/API foundation Item 12 can consume without another BUILD datastore.

---

## BUILD API direction

Bounded same-origin `/api/v1` extension. Exact path set to be verified in implementation reconnaissance. Do not over-expand.

Illustrative direction:

```text
POST /api/v1/projects/<id>/field-events
GET  /api/v1/projects/<id>/field-events
GET  /api/v1/projects/<id>/field-events/<event_id>
POST /api/v1/projects/<id>/field-events/<event_id>/originals
GET  /api/v1/projects/<id>/field-events/<event_id>/derived
POST /api/v1/projects/<id>/field-events/<event_id>/derived/<candidate_id>/confirm
POST /api/v1/projects/<id>/field-events/<event_id>/derived/<candidate_id>/reject
```

Requirements:

- FG-018 cookie/session authentication
- membership-derived Organization
- cross-org fail closed (404; do not leak existence)
- no caller-supplied `organization_id` as authority
- CSRF on JSON mutation (`X-CSRFToken`; no CSRF exemptions)
- no tokens
- same authoritative BUILD services as desktop
- unauthenticated `/api/v1` → **401 JSON** (not 302 `/login`)
- 0 or >1 active memberships → **403**

POST event/originals must succeed **without** Derived Candidates.

Existing FG-019 GET `/me` and `/projects` remain. Do not change their allow-lists in this gate except as required to avoid breakage.

---

## One system of record

```text
DESKTOP:
  Flask HTML → authoritative Flask services → BUILD records

FIELD (later Item 12):
  Field Web → Shared API → SAME Flask services → SAME BUILD records
```

Do **not** create interface-specific records.

---

## BUILD / Change Order boundary

Project Controls remains owner of Change Orders. FG-020 must **not**: create a second CO entity; auto-create, auto-price, or approve a CO; mutate a CO from a Derived Candidate; start Change Order document-family work.

**No Change Order FK** in FG-020.

---

## BUILD / MONITOR boundary

FG-020 must **not** implement Actual Direct Cost, GM, profitability, variance, forecast, or financial actuals.

Voice/text may later yield proposed crew/time facts. Confirming a Derived Candidate must **not** write labour-cost actuals or `LabourActualObservation`. MONITOR remains separately governed ([ADR-021](../adr/ADR-021-monitor-commercial-baseline.md)).

---

## Plan / Permit / take-off boundary

| Relationship | FG-020 |
|--------------|--------|
| Project | **Required** |
| Plan/sheet FK | **Defer** |
| Change Order FK | **Omit** |
| Permit | **Not FG-020** |
| Take-off | **Not FG-020** |

BUILD photos must remain separate from `PlanDocument`.

---

## Immutability / correction

| Record | Rule |
|--------|------|
| Original Payload | Immutable |
| Derived Candidate | Confirm/reject; reprocess = new candidate/attempt |
| Event | Identity stable |
| Correction | New Event supersedes prior Event |

No destructive rewriting of field evidence.

---

## Offline boundary

| Layer | FG-020 |
|-------|--------|
| **A. BUILD** | Server-side original-first SoR only. No client queue. |
| **B. Item 12** | Online-first iPhone Field Web with minimal retain/retry-until-ACK — **separately governed**. |
| **C. Later** | Durable offline queue / replay / conflicts / native sync. |

Do **not** implement offline client code in FG-020.

---

## Migration direction

FG-020 **will** require an additive Alembic migration. **Do not create it in this docs-only pass.**

Later implementation reconnaissance must determine: exact table names; columns; constraints; indexes; FK delete behavior; supersedes constraint; payload storage metadata; Derived Candidate payload representation; revision identifier.

Expected `down_revision`: **`b0c1d2e3f4a5`**.

Do **not** run `flask db upgrade` now.

---

## Acceptance criteria (draft)

**Not met.** Implementation not started.

1. Authenticated in-org office user can create a Field Event with a text Original.
2. Event stores Project + Organization scope.
3. `user_id` provenance and actor display-name snapshot are preserved.
4. `created_at` and `occurred_at` remain distinct.
5. API can preserve Original(s) without Derived Candidates.
6. Original Payload cannot be overwritten.
7. `text` / `audio` / `image` kinds are supported by the governed model.
8. Binary evidence uses private org/project/event-scoped custody.
9. Unauthorized / cross-org evidence access fails closed.
10. Event correction uses supersession.
11. Derived Candidate can be proposed / confirmed / rejected.
12. Derived confirmation cannot mutate Estimate.
13. Derived confirmation cannot mutate Proposal.
14. Derived confirmation cannot create or mutate Change Order.
15. Derived confirmation cannot mutate Permit / take-off.
16. Derived confirmation cannot write MONITOR / actual-cost records.
17. JSON mutation requires CSRF.
18. Auth/tenant semantics remain FG-018/019 compliant.
19. Project Hub shows BUILD events separately from Change Orders.
20. Desktop can create/list/review enough to be useful for office operation.
21. No Field Web UI exists.
22. No microphone/camera UI exists.
23. No transcription / external AI exists.
24. No MONITOR implementation exists.
25. Dedicated tests and full suite pass.
26. One Alembic graph head after later implementation / migration / UAT.

---

## Test plan (draft)

Proposed dedicated file: `tests/test_build_field_observation_fg020.py`

At minimum cover: Event creation; text Original creation; original-only create; actor snapshot; `user_id` provenance; `occurred_at` vs `created_at`; supersession; original immutability; text/audio/image kinds; binary SHA/storage validation; cross-org evidence denial; unauthorized download denial; Derived Candidate states; confirm/reject; no Estimate mutation; no Proposal mutation; no CO mutation; no MONITOR mutation; API 401/403/404; API CSRF mutation; Project Hub list; office event create/review; CO section remains separate.

Exact test count **deferred**.

---

## Regression plan (draft)

At minimum: FG-018 auth; FG-019 shared API; Project Hub; Change Orders; Plans / Plan Intelligence; Labour Engine; Pricing Engine; Permit; Estimates; Proposals; Organization isolation; private-file access.

Then full:

```text
./venv/bin/python -m pytest -q
```

Current governed baseline: **494 passed**.

---

## Non-goals

Field Web; Today; iPhone capture chrome; microphone UI; camera UI; transcription; ASR provider; voice AI; photo AI; external AI; runtime web lookup; native iOS; full offline sync; MONITOR; GM; profitability; actual-cost computation; labour actual cost; LEARN; auto-CO; Change Order documents; Phase D; supplier integration; Permit branding; QuickBooks; Ontario Contract / Warranty; RBAC; org switching; tokens; invitations; SSO; self-registration; SaaS billing; weather module; safety module.

Do **not** accept ADR-008. Do **not** accept ADR-010.

---

## Item-11 completion rule

Roadmap Item 11 is complete enough for Item 12 to become **ELIGIBLE FOR SEPARATE GOVERNANCE / NOT AUTHORIZED** when **all** of the following are true after an **approved** implementation close:

- Event model exists
- Original Payload is first-class
- audio / image / text kinds exist
- original binary custody exists
- original-only create works
- Derived Candidate + confirm/reject exists
- immutability / supersession works
- desktop BUILD surface is operational
- BUILD API is operational
- auth / tenant / CSRF tests pass
- no commercial / MONITOR cross-write exists
- migration / UAT / tests close cleanly
- this Feature Gate is **CLOSED / OPERATIONAL FOR UAT**

FG-020 closure must **not** authorize Field Web code. Item 12 remains a later gate.

---

## Item-12 status after a future FG-020 close

**ELIGIBLE FOR SEPARATE GOVERNANCE / NOT AUTHORIZED** (same pattern as Item 10 → 11).

Until FG-020 is approved, implemented, and closed, Item 12 remains **BLOCKED / NOT AUTHORIZED**.

---

## Implementation authorization

This document is **DRAFT FOR JOEL REVIEW / NOT APPROVED**.

Do **not** implement BUILD until:

1. Joel **approves** this Feature Gate, and
2. a **separate** implementation Cursor prompt is issued, and
3. file-custody implementation reconnaissance has recommended MIME/size rules (or Joel has decided).

---

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | | **Not approved** — DRAFT FOR JOEL REVIEW |
| ChatGPT review | | |
| Cursor implementation note | Docs/governance draft only. ADR-042 **Accepted**. FG-020 **not approved**. No BUILD code. No migration. | 2026-08-31 |
