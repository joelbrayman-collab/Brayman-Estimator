# ADR-042 — BUILD Field Evidence, Original Observation Custody, Desktop Review, and iPhone-First Capture Architecture

| Field | Value |
|-------|--------|
| Title | ADR-042: BUILD Field Evidence, Original Observation Custody, Desktop Review, and iPhone-First Capture Architecture |
| Status | **Accepted** (2026-08-31). [FG-020](../feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) is **IMPLEMENTED / LIVE MIGRATION PENDING**. |
| Date | 2026-08-31 (Proposed); **Accepted 2026-08-31** |
| Related | [ADR-019](ADR-019-calibai-lifecycle-and-project-hub.md) **Accepted** · [ADR-020](ADR-020-build-module-boundary.md) **Accepted** · [ADR-021](ADR-021-monitor-commercial-baseline.md) **Accepted** · [ADR-022](ADR-022-field-client-and-shared-api.md) **Accepted** · [ADR-023](ADR-023-field-evidence-provenance.md) **Accepted** · [ADR-041](ADR-041-user-membership-and-office-authentication.md) **Accepted** · [FG-018](../feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) **CLOSED / OPERATIONAL FOR UAT** · [FG-019](../feature-gates/FG-019-shared-api-foundation-v1.md) **CLOSED / OPERATIONAL FOR UAT** · [FG-020](../feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) **IMPLEMENTED / LIVE MIGRATION PENDING** · [modules/build.md](../modules/build.md) · [modules/monitor.md](../modules/monitor.md) · [CAR-001](../architecture/CAR-001-calibai-product-architecture-reconciliation.md) · Constitution Articles 3, 4, 5, 8 |

**Current status (2026-08-31):** This ADR is **Accepted**. [FG-020](../feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) is **IMPLEMENTED / LIVE MIGRATION PENDING**. HEIC/HEIF originals are preserved (custody ≠ rendering). Live Alembic current remains **`b0c1d2e3f4a5`**; repository head is **`c1d2e3f4a5b6`**. Field Web, transcription, and live `flask db upgrade` were **not** run in the implementation prompt.

A committed Proposed ADR was not acceptance. This record is now **Accepted**. Live migration and office UAT remain a **separate** prompt. Do **not** start Field Web.

---

## Context

Roadmap item 10 is **COMPLETE** ([FG-018](../feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) + [FG-019](../feature-gates/FG-019-shared-api-foundation-v1.md)). Item 11 BUILD Field Capture V1 is **ELIGIBLE FOR SEPARATE GOVERNANCE / NOT AUTHORIZED**. BUILD has no models, routes, or UI.

[ADR-020](ADR-020-build-module-boundary.md) names BUILD as the owning module for field-execution records and keeps Change Orders with Project Controls. [ADR-022](ADR-022-field-client-and-shared-api.md) sequences Flask services → shared API → purpose-built Field Web → native iOS later, and rejects treating field as a shrunken desktop estimating UI. [ADR-023](ADR-023-field-evidence-provenance.md) requires ORIGINAL OBSERVATION plus SEPARATE DERIVED STRUCTURED RECORDS, human confirmation before authoritative business records, and forbids overloading `PlanDocument` for photos. ADR-023 Decision 5 correctly prohibited voice/photo **implementation** during the CAR-001 architecture phase and parked voice AI / photo AI outside V1.

The 2026-08-31 BUILD Field Capture V1 architecture reconnaissance, plus Joel’s iPhone-first / voice-first / desktop-first review clarification, identified decisions ADR-020/022/023 do not fully lock:

- two first-class BUILD surfaces (desktop review and iPhone capture) over **one** system of record
- capture-first (SAVE ORIGINAL is a complete evidence action)
- Field Capture Event with Original Payload children (`text` / `audio` / `image`) and generic Derived Candidates
- original audio vs AI transcript vs human-entered text
- `user_id` plus display-name snapshot on **new** BUILD tables only
- distinct `created_at` vs `occurred_at`
- Item 11 vs Item 12 ownership, including audio/image **upload API** in BUILD
- offline / poor-connectivity A / B / C sequencing
- useful desktop BUILD review as part of the first BUILD gate destination, without Field Web UI

This ADR is the subsequent architecture decision. It does **not** claim ADR-023 was historically wrong.

---

## Decision

**Accepted.** Do **not** treat acceptance as product implementation, FG-020 approval, or Field Web authorization.

### 1. Two first-class BUILD surfaces, one system of record

CalibAi BUILD has **two first-class operating surfaces** over the **same** authoritative BUILD records and services:

1. **Desktop / office** — existing server-rendered Flask HTML.
2. **Field / iPhone** — purpose-built Field Web (Item 12), primarily iPhone Safari in the first Field Web release.

Neither surface is temporary scaffolding for the other. Neither is disposable.

There must **not** be a desktop BUILD datastore, a mobile BUILD datastore, separate field-note concepts by interface, duplicated business logic, or duplicated project evidence.

```text
DESKTOP / OFFICE:
  Flask HTML → authoritative Flask services → BUILD records

FIELD / IPHONE:
  Field Web → Shared API → the SAME Flask services → the SAME BUILD records
```

The office application continues to call Flask services **directly**. It is **not** required to consume `/api/v1` for architectural symmetry. Shared API exists primarily to support separate CalibAi clients such as Field Web ([FG-019](../feature-gates/FG-019-shared-api-foundation-v1.md)).

### 2. Desktop / office purpose

Desktop BUILD is a first-class product surface optimized for **review, management, context, history, confirmation, and investigation** — not rapid job-site capture.

The existing Project Hub (`/projects/<id>`) remains the natural desktop project anchor. BUILD field observations must appear **beside**, and **distinct from**, existing Change Orders. Change Orders remain the Project Controls commercial instrument; they are not field evidence.

The architectural destination for desktop (separately gated; **not** all required in the first Feature Gate) includes: chronological observations; `occurred_at` and `created_at`; authenticated actor provenance and display-name snapshot; original text, photos (thumbnails/viewing), and audio (playback); transcript/derived information when later authorized; proposed / confirmed / rejected derived status; human confirm/reject; supersession/history; evidence download; office-created typed observations; later filtering/search; later links to MONITOR **without** embedding MONITOR financial logic.

### 3. Field / iPhone purpose

The field experience is **not** “the office Flask application resized onto a phone” ([ADR-022](ADR-022-field-client-and-shared-api.md)).

It is designed around: one-handed use where practical; large touch targets; minimal typing and navigation; rapid capture; outdoor/job-site readability; camera-first capture; voice-first capture; weak/intermittent connectivity; seconds of attention rather than office-style form completion.

Office remains appropriate for dense PLAN / PRICE / CONTRACT / administrative work. Field remains appropriate for **fast capture**.

Job-site operating assumption: the contractor may be wearing gloves; in rain, snow, dust, or bright sunlight; surrounded by equipment/noise; moving; unable or unwilling to type paragraphs; on intermittent radio; able to devote only seconds to an observation.

### 4. Capture-first principle

```text
CAPTURE FIRST → STRUCTURE SECOND → REVIEW / CONFIRM THIRD
```

A field fact must be safely preservable **before** structured fields are required. **SAVE ORIGINAL** is a valid completed evidence-preservation action. Derived processing must never be a prerequisite for preserving the original.

### 5. Field Capture Event

BUILD owns a **Field Capture Event** (field observation event).

The Event:

- belongs to Organization (membership-derived; never caller-supplied `organization_id` as authority)
- belongs to the existing `Project` ([ADR-019](ADR-019-calibai-lifecycle-and-project-hub.md); no parallel Job)
- is attributed to the authenticated User
- preserves an actor display-name snapshot
- records `created_at` (when CalibAi recorded the Event)
- records `occurred_at` separately (when the field observation actually occurred)
- has immutable identity
- may have one or more Original Payload children
- may later have Derived Candidate children
- is corrected by **supersession**, not destructive overwrite

`occurred_at` supports delayed job-site entry and later synchronization. It must be governed in the future schema.

### 6. Actor provenance (new BUILD tables only)

New BUILD records store **both**:

1. nullable durable `user_id` provenance
2. human-readable actor display-name snapshot

`user_id` preserves the durable actor relationship. The display-name snapshot preserves what identity was shown/known at the time. Later User display-name changes must not rewrite historical evidence.

This is **new BUILD schema only**. Do **not** backfill old actor strings elsewhere. Do **not** start a repository-wide `user_id` conversion ([ADR-041](ADR-041-user-membership-and-office-authentication.md) / FG-018 boundary).

### 7. Original Payload

A single Event may own multiple Original Payloads. Kinds must architecturally support:

- `text` — human-entered observation text
- `audio` — original recorded audio
- `image` — original field photo

Original means **preserved evidence**. An Original Payload is **immutable**. Do not overwrite an original with transcript, AI interpretation, labels, structured fields, later image observations, or later correction.

Binary originals use governed private custody and provenance patterns (organization-scoped, project/event scoped, app-managed private storage, SHA/checksum, path-traversal protection, authorized download, immutable bytes, archive/supersede rather than destructive replacement). Do **not** overload `PlanDocument`. Field evidence belongs to BUILD ([ADR-023](ADR-023-field-evidence-provenance.md) Decision 4).

This ADR does **not** define arbitrary field MIME/size limits. A future FG-020 implementation reconnaissance must (1) search existing repository conventions, (2) reuse an established limit where technically and governance-appropriate, (3) return to Joel if no defensible field-evidence rule exists. Existing related caps (plans/historical 25 MB; brand logos 5 MB) are **not** automatically field-evidence limits.

### 8. Audio / transcript

| Artifact | Classification |
|----------|----------------|
| Original recorded audio | **Original evidence** |
| AI / ASR transcript | **Derived** |
| AI / ASR interpretation | **Derived** |
| Human-entered text recorded directly as the observation | **Original** `text` payload |
| Human-confirmed transcript text | May later be an **additional** governed text representation (Feature-Gated). Must **never** replace or delete the original audio |

Do not silently promote a machine transcript to original evidence. Re-transcription is a **new derived attempt** against the same original audio (ADR-015 analogue).

### 9. Photo

Original photo bytes are evidence. Preserve original bytes, checksum/SHA, size, and governed metadata/provenance. Do not overwrite the original image.

Any later AI observation, classification, issue suggestion, annotation, or derived crop/version is **separate** from the original.

Do **not** implement photo AI in BUILD V1.

### 10. Derived Candidate

A separate **Derived Candidate** concept is required. Initial architecture remains **generic**. Do not freeze a large taxonomy before processors exist.

Minimum:

- parent Capture Event
- kind
- governed payload
- status: `PROPOSED` / `CONFIRMED` / `REJECTED`
- created/proposed provenance
- confirmation/rejection actor
- confirmation/rejection timestamp

Kinds may **eventually** include labour observation, work progress, material need, delivery, deficiency, issue, follow-up, possible change issue, RFI/question, inspection observation. This ADR does **not** declare those processors implemented.

### 11. Human confirmation boundary

```text
Original observation → derived suggestion → human confirmation → governed BUILD structured fact
```

Machine interpretation must **not** silently: alter Estimate, Proposal, approved quantity, pricing, or contract scope; create or approve a Change Order; write Permit conclusions; write take-off quantities; write labour actual cost; write MONITOR financial actuals; change commercial approval state.

A confirmed Derived Candidate is authoritative **only** for the BUILD fact it represents. It is not authority for another module’s governed record.

### 12. BUILD vs Change Order

Project Controls remains owner of Change Orders ([ADR-020](ADR-020-build-module-boundary.md)). BUILD does not create a second Change Order entity.

A field observation may later suggest `possible_change_issue`. It must **not** automatically create, price, approve, or change scope of a Change Order.

No Change Order FK is required in first BUILD V1. Defer unless separately governed.

### 13. BUILD vs MONITOR

BUILD owns field evidence / actual facts. MONITOR later consumes governed actuals ([ADR-021](ADR-021-monitor-commercial-baseline.md)).

BUILD V1 must **not** implement Actual Direct Cost aggregation, GM calculation, profitability, variance, forecast, or financial actuals.

Voice may later suggest crew/time information. That does **not** automatically become labour-cost actuals or `LabourActualObservation`.

### 14. Plan / Permit / take-off

- Project relationship: **required**
- Plan/sheet FK: **defer** in first BUILD V1
- Change Order FK: **omit**
- Permit relationship: **not** first BUILD V1
- Take-off relationship: **not** first BUILD V1

BUILD photos must not be stored in `PlanDocument`. BUILD may later own post-issuance permit/inspection operational evidence; it does not own Permit Intelligence preflight analysis.

### 15. Item 11 vs Item 12

**Item 11 — BUILD Field Capture domain** owns:

- Capture Event model
- Original Payload model
- text / audio / image original kinds
- binary evidence custody
- Derived Candidate model
- confirm/reject state
- original-first service behavior
- complete bounded desktop/office BUILD surface
- BUILD API create/read/review operations
- authenticated Project / Organization / actor scoping
- **original audio/image upload API** (Joel decision: Item 11 establishes evidence custody and SAVE ORIGINAL semantics so Item 12 does not invent server-side storage)

Item 11 does **not** own microphone UI, camera UI, transcription, or AI interpretation.

**Item 12 — Field Web** owns:

- iPhone-first Today / Capture UX
- TAP CAPTURE workflow
- microphone/browser recording interaction
- camera interaction
- one-handed UI and outdoor readability
- minimal typing/navigation
- plan-access **presentation** (Plan Intelligence owns PDFs)
- Field Web retry/resilience behavior

Item 12 must consume Item 11 domain/services/API. It must not invent another BUILD datastore.

### 16. FG-020 direction (not creation)

Expected next Feature Gate candidate (report only; **do not create in this pass**):

```text
FG-020 — BUILD Field Capture V1 — Project Field Observation Foundation
```

A future FG-020 must include enough **desktop** functionality to prove BUILD is operational for an office user, not merely database UAT. Evaluate at minimum: Project Hub BUILD section; event list; event detail/review; office text-observation create; original evidence visibility/download where supported; derived candidate review/confirm/reject where supported; supersession/history visibility sufficient for UAT.

Do **not** require iPhone capture UI in FG-020.

Expected future gate boundary may include: additive BUILD schema; Capture Events; Original Payloads; Derived Candidates; text original office create; audio/image kinds; binary original custody/upload API; supersession/immutability; useful desktop Project Hub BUILD section; BUILD `/api/v1` create/read/confirm/reject; cookie/session auth; CSRF; tests; migration.

Explicitly **not**: Field Web UI; mic UI; camera UI; transcription; external AI; full offline sync; MONITOR; actual cost; Change Order automation.

### 17. Offline / poor-connectivity sequencing

Unreliable job-site connectivity is a real field requirement. Full offline-first sync is **not** the first BUILD gate.

| Layer | Owner | Rule |
|-------|--------|------|
| **A. Item 11 BUILD** | Server | Authoritative record. Original-first persistence. No client offline queue required. |
| **B. Item 12 Field Web** | iPhone Safari Field Web | Online-first. Architected so an Original can be retained/retried until the server acknowledges preservation. A **minimal** local original hold / retry belongs to Field Web. Do not require full conflict/sync infrastructure in the first Field Web gate. |
| **C. Later separately governed** | Later gate | Durable offline queue, replay, conflict management, background synchronization, native-device behavior, token auth if native later requires it |

When a processor later exists: preserve original → server ACK → then derive → then human review. Never derive before the original is safe.

### 18. Field Web vs native

Current direction remains ([ADR-022](ADR-022-field-client-and-shared-api.md)):

```text
Flask authoritative services → Shared API → purpose-built Field Web → native iOS only later if warranted
```

Field Web must be excellent on iPhone. Native deferral is **not** permission for a poor iPhone web experience. Do not design native architecture in this ADR.

### 19. AI boundary

This ADR does **not** authorize a transcription provider, external AI, runtime web lookup, photo AI, voice AI, or automatic extraction.

It governs the data/evidence boundary those future processors must obey.

External AI remains separately governed. [ADR-010](ADR-010-build-versus-buy-document-processing.md) remains **Proposed**. Do **not** accept it here. Do **not** accept [ADR-008](ADR-008-supplier-price-snapshotting.md).

### 20. Relationship to ADR-023

[ADR-023](ADR-023-field-evidence-provenance.md) remains **Accepted**. Its 2026-08-28 Decision is **not** rewritten.

ADR-023 correctly prohibited voice/photo **implementation** in the earlier architecture phase (Decision 5) and established original-versus-derived provenance (Decisions 1–4).

This subsequent decision governs **original audio/photo custody** as part of BUILD domain readiness, while continuing to prohibit until separately gated:

- transcription implementation
- voice AI
- photo AI
- Field Web capture UI

Original custody is not interpretation. Voice AI / photo AI remain later Feature Gates (roadmap later list; CAR-001 later list).

---

## Alternatives Considered

- **Text-only “project note” as BUILD V1** — Rejected as insufficient to preserve voice-first / camera-first. Item 12 would be forced to invent original-payload architecture.
- **Treat Field Web as responsive office Flask** — Rejected (already rejected by ADR-022; reaffirmed here).
- **Separate field database or field-note entity by client** — Rejected: splits the authoritative project record.
- **Office must call `/api/v1` for symmetry** — Rejected: FG-019 already keeps office HTML on Flask services.
- **Put audio/image upload API in Item 12** — Rejected: Item 12 must not invent server-side evidence storage.
- **Full offline-first sync in Item 11** — Rejected: CAR-001 later list; server SoR first.
- **Labour hours as V1 actual cost** — Rejected: crosses into MONITOR / `LabourActualObservation`.
- **Auto-create Change Orders from field issues** — Rejected (ADR-020).
- **Store field photos on `PlanDocument`** — Rejected (ADR-023 Decision 4).
- **Silently rewrite ADR-023 Decision 5** — Rejected: additive subsequent ADR instead.
- **Accept this ADR in the same pass as drafting** — Rejected at draft (2026-08-31 Proposed commit). **Accepted** in a later governance pass the same day. Still does **not** authorize implementation.

---

## Consequences

**Positive:** BUILD can be Feature-Gated without painting into a text-blob corner; desktop review and iPhone capture share one SoR; original evidence remains auditable when processors arrive; ADR-023 history is preserved.

**Negative:** First BUILD Feature Gate is larger than a single note table (event + originals + derived + desktop UAT + upload API). Binary custody and MIME/size remain for FG-020 reconnaissance. Derived taxonomy remains generic until a processor gate.

---

## Module Ownership Impact

BUILD (`docs/modules/build.md`) gains intended ownership of Field Capture Events, Original Payloads, Derived Candidates, and BUILD binary original custody. Project Controls retains Change Orders. Plan Intelligence retains plan PDFs. Permit Intelligence retains preflight analysis. MONITOR remains a comparison/read layer. Shared API remains platform transport (FG-019); BUILD **extends** it when gated. Field Web (Item 12) is a client, not an owning module of BUILD records.

Ownership of future BUILD records is named here. Implementation remains unauthorized until FG-020 is **approved** and a Cursor implementation prompt is issued.

---

## Data Ownership Impact

Future BUILD-owned: Capture Event, Original Payload (text/audio/image), Derived Candidate (proposed/confirmed/rejected). Referenced: `projects`, `organizations`, `users` (nullable FK on new BUILD tables only). Not owned: Change Orders, estimates, proposals, plan binaries, permit analysis, MONITOR snapshots, labour actual-cost records.

Originals are immutable. Events are superseded, not destructively edited.

---

## Migration Impact

**None in this ADR.** Additive BUILD schema is owned by [FG-020](../feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) (revision **`c1d2e3f4a5b6`**, `down_revision` `b0c1d2e3f4a5`). **Subsequent status (2026-08-31):** FG-020 is **IMPLEMENTED / LIVE MIGRATION PENDING**. Live current remains `b0c1d2e3f4a5`. This ADR still does **not** itself generate Alembic.

---

## Testing Impact

None in this acceptance pass (documentation only). Future FG-020 tests (when the gate is approved and implemented) must cover original-only create, original immutability, org isolation, CSRF on mutating `/api/v1`, and confirm/reject that does not write Estimate / CO / MONITOR.

---

## Documentation Impact

This ADR; ADR index; CAR-001 subsequent status; modules/build.md; current-state; session-handoff; chat-workflow-log; architecture.md; platform-roadmap Item 11 note; [FG-020](../feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) **IMPLEMENTED / LIVE MIGRATION PENDING**.

---

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Joel Brayman | 2026-08-31 |
| ChatGPT review | Architecture reconnaissance + dual-surface / original-custody review | 2026-08-31 |
| Cursor implementation note | Documentation / governance only. ADR Accepted. FG-020 drafted **NOT APPROVED**. No BUILD code. No migration. | 2026-08-31 |
