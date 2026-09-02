# Feature Gate FG-021: Field Web V1 — Today + Capture

| Attribute | Value |
|-----------|--------|
| Feature Gate ID | `FG-021` |
| Feature Name | Field Web V1 — Today + Capture |
| Target Milestone | **None.** FG-021 is the governing identifier. Do not assign a new M0xx number. Do **not** assign FG-021 to Native Signing. |
| Module | **Field Web is a client.** **BUILD** owns Field Capture Events, Original Payloads, Derived Candidates, and BUILD binary custody. **Office / platform** owns `/api/v1` adapters, cookie session, and CSRF. **Projects** owns `projects`. |
| Date | 2026-09-01 |
| Status | **DRAFT FOR JOEL REVIEW / NOT APPROVED.** Implementation **NOT AUTHORIZED**. |
| Architecture | [ADR-043](../adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md) **Proposed** · [ADR-042](../adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) **Accepted** · [ADR-022](../adr/ADR-022-field-client-and-shared-api.md) **Accepted** · [ADR-041](../adr/ADR-041-user-membership-and-office-authentication.md) **Accepted** · [architecture/field-web-today-and-capture.md](../architecture/field-web-today-and-capture.md) · [modules/build.md](../modules/build.md) · [architecture/build-media-storage-lifecycle.md](../architecture/build-media-storage-lifecycle.md) |
| Related ADRs | [ADR-043](../adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md) **Proposed** (must be **Accepted** before implementation) · [ADR-042](../adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) **Accepted** · [ADR-008](../adr/ADR-008-supplier-price-snapshotting.md) **Proposed** (do **not** accept) · [ADR-010](../adr/ADR-010-build-versus-buy-document-processing.md) **Proposed** (do **not** accept) |
| Prerequisites | [FG-020](FG-020-build-field-capture-v1-project-field-observation-foundation.md) **CLOSED / OPERATIONAL FOR UAT**. Item 11 **COMPLETE**. Item 12 reconnaissance **COMPLETE / NOT IMPLEMENTED**. [FG-018](FG-018-organization-authentication-actor-identity-and-membership-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-019](FG-019-shared-api-foundation-v1.md) **CLOSED / OPERATIONAL FOR UAT**. ADR-043 **Accepted** (not yet). This gate **Approved** (not yet). |
| Approved baseline | Live Alembic current = head **`c1d2e3f4a5b6`**. Full suite **538 passed** (FG-020 close claim; not rerun this draft). Dedicated FG-020 **44**. Focused **128**. |

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **DRAFT FOR JOEL REVIEW / NOT APPROVED** |
| ADR-043 | **Proposed / for Joel review** |
| ADR-042 | **Accepted** (dual-surface / original custody; unchanged) |
| Implementation | **NOT STARTED** |
| Schema / Alembic | Expected **one** additive revision after `c1d2e3f4a5b6`. **Not created.** |
| Field Web product | **NOT STARTED** |
| Native Signing | Parallel track. Development may proceed under **separate** governance. Production activation **blocked pending counsel**. Not this gate. |
| Project Closeout | **FUTURE / NOT AUTHORIZED** |

This draft does **not** authorize implementation, a migration, microphone/camera product UI, transcription, PWA, Native Signing, or Contract templates.

Joel must **Accept ADR-043** and **Approve FG-021** in a later prompt before any Field Web product code.

---

## Purpose

Deliver a purpose-built **iPhone Safari** field surface so a contractor can:

- sign in
- select/confirm the correct Project
- capture voice and/or photo and/or short text
- preserve the capture reliably
- see **SAVING / SAVED / NEEDS RETRY**
- retry without silent duplicate records
- have the **same** Event appear in desktop BUILD after ACK

Joel product decisions (memorialized):

```text
FIELD WEB V1 = TODAY + PROJECT CONFIRMATION + CAPTURE
Modalities = VOICE + PHOTO + SHORT TEXT
Technology = Flask/Jinja purpose-built Field routes + focused JavaScript + existing Shared API
NOT = office app merely resized, React/Vue SPA, PWA V1, native iOS V1
```

SAVE ORIGINAL remains a complete evidence action ([ADR-042](../adr/ADR-042-build-field-evidence-and-iphone-first-capture.md)).

---

## Feature Gate answers

| # | Question | Answer |
|---|----------|--------|
| 1 | What problem does this solve? | FG-020 has an office BUILD SoR but no job-site capture surface. Contractors cannot capture voice/photo/text on iPhone against the same Events without a purpose-built Field Web. Retry without server idempotency would duplicate evidence. |
| 2 | Who is the user? | Authenticated organization member on **iPhone Safari** (primary). Desktop Safari may open `/field` for support. Not the customer. Not a public API consumer. Not native iOS. |
| 3 | Which module owns it? | Field Web **client** owns Field HTML/JS and IndexedDB pending hold. **BUILD** owns Events/Originals/services/custody. **Office/platform** owns `/api/v1`, session, CSRF. **Projects** owns `projects`. |
| 4 | What data does it own? | None of the BUILD commercial records. It **temporarily** holds unsent capture blobs/UUIDs in IndexedDB until ACK. Optional `client_capture_uuid` / `client_original_uuid` columns are BUILD schema, not a Field datastore. |
| 5 | What data does it reference? | `projects` (FG-019 list/detail); Field Capture Events/Originals via `/api/v1`; session User/membership; CSRF token. Does **not** own Change Orders, plans, Derived review, MONITOR, Contract. |
| 6 | What may implementation change? | `/field` Flask/Jinja + CSS/JS; IndexedDB pending hold; BUILD service/API idempotent Event/Original replay; `/api/v1` Compatible Rendition display GET; **one** additive Alembic revision after `c1d2e3f4a5b6`; dedicated tests; docs. After ADR-043 Accepted **and** this gate Approved **and** a separate implementation prompt. |
| 7 | What must it not change? | Office Hub shell as Field; office-to-API migration of existing pages; tokens; RBAC; org-switcher; transcription/AI; PWA/service worker; Derived field review UI; plan viewer; CO UNSIGNED/AWAITING/SIGNED; Native Signing; Closeout; FG-019 `POST /api/v1/me` and `POST /api/v1/projects` (remain 405); CSRF exemption; historical actor strings; Alembic history before the approved revision. |
| 8 | Acceptance criteria? | See **Acceptance criteria** below. **Not met** — implementation not started. |
| 9 | Tests required? | Dedicated automated suite (see **Automated test plan**) plus **real iPhone UAT**. Desktop emulation cannot close this gate. Exact pytest count deferred to implementation. |
| 10 | Documentation? | This gate; ADR-043; field-web pin; feature-gate index; adr index; BUILD module; current-state; session-handoff; project-state-report; roadmap; chat-workflow-log; milestones. |
| 11 | ADR required? | **Yes.** [ADR-043](../adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md) **Proposed**. Must be **Accepted** before implementation. ADR-042 remains dual-surface / custody. |
| 12 | Migration? | **YES** when the implementation prompt runs. One additive revision after `c1d2e3f4a5b6`. Exact identifier deferred. **Do not create it in this draft.** No historical backfill. |

---

## Owner

| Concern | Owner |
|---------|--------|
| `/field` templates, Field CSS, page JS, IndexedDB | **Field Web (client)** |
| Field Capture Event, Original Payload, Derived Candidate | **BUILD** |
| Idempotent Event/Original create | **BUILD** services |
| `/api/v1` BUILD adapters + display rendition GET | **Office / platform** + BUILD services |
| Flask-Login session / CSRF | **Office / platform** (FG-018; unchanged) |
| Project list/detail | **Projects** via existing FG-019 API |
| Change Orders | **Project Controls** (out of this gate) |
| Plan PDFs | **Plan Intelligence** (out of this gate) |
| Native Signing | **Separately governed** (out of this gate) |

---

## Two first-class surfaces

Preserve [ADR-042](../adr/ADR-042-build-field-evidence-and-iphone-first-capture.md).

| Surface | Optimized for | Path |
|---------|---------------|------|
| Desktop / office | Review, management, history, confirmation, investigation | Flask HTML → BUILD services → BUILD records |
| Field / iPhone | Fast capture, quick Project context, voice, camera, minimal typing, one-handed use | Field Web → Shared API → **same** BUILD services → **same** BUILD records |

No second Field datastore. No duplicated business logic.

---

## Today

Today is the field home after login.

V1 contents:

- confirmed/current Project (name + number), or a prompt to select
- prominent **Capture**
- **Needs Retry**
- recent observations for the current Project (`GET /api/v1/projects/<id>/field-events`)
- **Switch Project**

Do **not** add: schedule, weather, timesheets, MONITOR, profitability, AI summary, Change Order signing status.

---

## Project

Reuse existing `GET /api/v1/projects` and `GET /api/v1/projects/<id>`.

Capture is **disabled** until the Project is explicitly confirmed. The Field user must always see which Project receives the capture.

No Organization switching. No new Project model. Recents may be client-side.

---

## Capture

One Event may contain short text, Original audio, and one or more Original photos.

Minimum lawful capture: **confirmed Project + at least one Original**.

Do **not** require title, cost code, category, structured extraction, or an `occurred_at` picker.

```text
OPEN FIELD WEB
→ SELECT / CONFIRM PROJECT
→ TAP CAPTURE
→ SPEAK / TYPE / PHOTO
→ SAVE ORIGINAL
→ DONE
```

---

## Voice

Voice is **CORE V1**. Transcription is **not**.

```text
getUserMedia → MediaRecorder → visible recording state → stop → playback → discard/re-record → save Original audio
```

Runtime `MediaRecorder.isTypeSupported` must determine supported format. Prefer Safari-produced `audio/mp4` where FG-020 already accepts it (`audio/mp4` / `.m4a` / `.mp4` in `app/services/build_storage.py`).

No transcription, ASR, voice AI, waveform, or client audio transcode.

Exact blob MIME on target iPhones is **To be verified** in implementation reconnaissance / real-device UAT.

---

## Camera

Camera/photo is **CORE V1**.

Support: take photo; select existing photo where appropriate; preview; remove before save; multiple photos; Original upload.

Server retains HEIC/HEIF Original Source + JPEG Compatible Rendition (`app/services/build_rendition.py`). No user format selection. No client HEIC conversion in V1 unless real-device implementation reconnaissance proves unavoidable.

---

## Text

Short text only. Native iPhone dictation remains usable (that is not CalibAi AI). Do not build a desktop-style observation form.

---

## Multi-Original transaction

```text
create/reuse Event → upload Originals individually
```

Each Original is independently ACK’d. Partial failure does not destroy prior successful Originals. Retry failed Originals with the same `client_original_uuid` ([ADR-043](../adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md)).

---

## API delta

Minimum additions only:

1. Idempotent Event POST/replay (`client_capture_uuid`)
2. Idempotent Original POST/replay (`client_original_uuid`)
3. Compatible Rendition display GET over `/api/v1`

Preserve FG-019:

```text
POST /api/v1/me       → 405
POST /api/v1/projects → 405
```

No token API. No speculative endpoint expansion. Derived confirm/reject remain **not** Field V1 UI.

Existing sufficient reads: `GET /api/v1/me`, `GET /api/v1/projects`, `GET /api/v1/projects/<id>`, field-events and originals list/detail/content.

---

## Compatible Rendition Field access

Field Web should render HEIC/HEIF using the existing server JPEG rendition (`open_display_rendition`). Add only a governed authenticated `/api/v1` display path. Reuse Original authorization. No filesystem path exposure. Cross-org: **404**. No second rendition service.

JPEG/PNG/GIF may use `/content`. Audio: browser-native playback where supported.

---

## Field routes / technology

Direction (implementation reconnaissance may minimize exact routes):

```text
/field → /field/today
/field/today
/field/projects
/field/projects/<id>
/field/projects/<id>/capture
```

Use Flask/Jinja + focused page JavaScript.

Do **not** introduce React, Vue, a new frontend build system, or the office sidebar shell (`app/static/css/app.css` 1200/900/640 is office responsive, not Field).

---

## Job-site UX

Require:

- iPhone Safari primary; portrait-first; landscape tolerated
- `viewport-fit=cover` + `env(safe-area-inset-*)`
- touch targets ≥ 44 CSS px; Capture control larger
- thumb-friendly actions; high contrast; no hover-only; no horizontal tables as the capture path
- minimal keyboard use; visible Project context
- obvious recording state, photo state, SAVING/SAVED/NEEDS RETRY
- safe discard confirmation
- basic VoiceOver labels on Capture / Record / Save

---

## `occurred_at`

No normal `occurred_at` picker in Field V1. Server defaults to **NOW** when omitted. Office remains the surface for delayed/manual observation timestamp entry.

---

## Out of FG-021

| Topic | Rule |
|-------|------|
| Derived Candidate review | Desktop owns confirm/reject. Field V1 is capture-only. |
| Plan access | Defer purpose-built plan viewing. Do not duplicate Plan Intelligence. |
| Change Order visibility | Do **not** implement UNSIGNED / AWAITING SIGNATURE / SIGNED. Native Signing is separately governed. |

---

## Migration direction

FG-021 is expected to require **one** additive migration after `c1d2e3f4a5b6`.

**Do not create it in this draft.**

Implementation reconnaissance must determine exact:

- Event client UUID column
- Original client UUID column
- nullability
- indexes
- unique constraints
- migration revision identifier
- downgrade

No historical backfill. Office rows without client UUIDs remain lawful ([ADR-043](../adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md) Decision 4).

---

## Implementation reconnaissance (required after approval, before/during code)

Do **not** run as product work from this draft.

Required later:

- runtime `MediaRecorder.isTypeSupported` on current and one older supported iPhone Safari
- take-photo path (`<input capture>` vs `getUserMedia`)
- IndexedDB quota vs `BUILD_ORIGINAL_MAX_BYTES` (25 MB)
- CSRF token refresh mid-capture
- exact unique-index form on SQLite
- whether Field HTML needs any route beyond the family above

---

## Automated test plan

Dedicated tests for at least:

- Field unauthenticated redirect / login `next`
- Today
- Project confirmation
- Capture disabled without Project
- Event idempotency and Event replay
- Original idempotency and Original replay
- same UUID returns same row
- different UUID / same SHA remains a lawful separate Original
- cross-org 404
- API 401 JSON
- CSRF required
- expired/retried CSRF path
- multi-Original partial success
- compatible rendition API
- HEIC display JPEG
- desktop Hub continuity
- caller actor ignored
- caller Organization ignored
- FG-019 mutation locks remain (`POST /api/v1/me` and `POST /api/v1/projects` stay 405)
- office BUILD still works (Hub, office text create, supersession, derived confirm/reject)

JavaScript/browser behavior requires separate client / real-device coverage. Pytest cannot replace iPhone mic/camera/HEIC/retry.

Proposed dedicated file name is deferred to implementation (`tests/test_field_web_fg021.py` or equivalent). Existing `tests/test_build_field_observation_fg020.py`, FG-018, and FG-019 suites must still pass.

---

## Real iPhone UAT

**FG-021 closure requires real-device testing.** Desktop emulation alone cannot close this gate.

Current iPhone Safari **MUST** cover:

- login
- Project confirmation
- microphone permission
- voice record
- playback
- discard/re-record
- audio upload
- camera permission
- photo capture
- photo selection where supported
- multiple photos
- HEIC upload
- orientation
- JPEG rendition display
- IndexedDB pending capture
- network interruption
- retry
- duplicate replay protection
- background/foreground
- session expiry
- CSRF recovery
- SAVING / SAVED / NEEDS RETRY
- portrait
- one-handed operation
- outdoor readability

Also require one older supported iPhone/Safari smoke test where practical.

---

## Completion rule

A contractor can, on iPhone Safari:

1. sign in;
2. confirm the correct Project;
3. capture voice and/or photo and/or short text;
4. preserve pending capture locally until server ACK;
5. see SAVING → SAVED or NEEDS RETRY;
6. retry without silent duplicate Event/Original creation;
7. view HEIC photos through compatible server rendition;
8. have the SAME Event/Originals appear immediately in desktop BUILD after ACK.

No transcription or AI required.

---

## Acceptance criteria

Not met until implementation + tests + real-device UAT. Draft bar:

1. On current iPhone Safari, an authenticated contractor can confirm a Project, Capture voice and/or photo and/or short text, and see SAVING → SAVED (or NEEDS RETRY that retries).
2. Server ACK creates a `FieldCaptureEvent` plus the intended `FieldCaptureOriginal` rows via `app/services/build.py` — the same records the office Hub reads.
3. Replay of the same `client_capture_uuid` / `client_original_uuid` returns the existing row and does not create a second Event or Original.
4. CSRF remains required (`X-CSRFToken`). No CSRF exemption. API 401 remains JSON for `/api/v1`; Field HTML 302 remains `/login` with `safe_next_url`.
5. The same Event and Originals appear on desktop Project Hub → Field Observations → Event Detail immediately. No second datastore. No sync job.
6. HEIC Originals remain Original Source; Field display uses Compatible Rendition over `/api/v1`. JPEG/PNG/GIF may use `/content`.
7. Logout wipes unsent IndexedDB. IndexedDB full/unavailable refuses Capture (does not claim SAVED).
8. Dedicated automated tests plus the real-device UAT checklist pass. Office Hub, office text create, supersession, derived confirm/reject, and FG-019 mutation lock do not regress.
9. Non-goals below remain out of the gate.

---

## Non-goals

Explicitly exclude:

- transcription, ASR, voice AI, photo AI, OCR
- external AI, runtime web lookup
- PWA, service worker, full offline sync, native iOS
- tokens, RBAC, org switcher
- Derived review, plan viewer, Change Order field status
- Native Signing, Contract
- MONITOR, profitability, actual cost, schedule, weather, timesheets
- Project Closeout, archive/purge
- desktop redesign

---

## Native Signing pin

This gate does **not** implement Native Signing and must **not** be reassigned to it.

```text
NATIVE SIGNING DEVELOPMENT:
MAY PROCEED UNDER SEPARATE GOVERNANCE

NATIVE SIGNING PRODUCTION ACTIVATION / REAL CUSTOMER USE:
BLOCKED PENDING ONTARIO COUNSEL APPROVAL OF THE SIGNING PROCESS
```

Counsel review is **not** a Field Web hold. The [Legal Content Gate](../governance/legal-content-and-templates.md) for Ontario Contract / Warranty templates remains in force and is separate.

---

## Closure rule

Joel Approves this gate **and** Accepts ADR-043 **and** a later implementation prompt completes the completion rule **and** dedicated tests **and** real iPhone UAT pass **and** live current remains a single graph head after the approved additive migration.

This draft closes **nothing**.

---

## Related current code (do not change under this draft)

- [`app/routes/api_v1.py`](../../app/routes/api_v1.py)
- [`app/models/build.py`](../../app/models/build.py)
- [`app/services/build.py`](../../app/services/build.py)
- [`app/services/build_rendition.py`](../../app/services/build_rendition.py)
- [`app/routes/build.py`](../../app/routes/build.py)
- [`app/templates/build/`](../../app/templates/build/)
- [`app/static/css/app.css`](../../app/static/css/app.css)
- [`app/routes/auth.py`](../../app/routes/auth.py)
