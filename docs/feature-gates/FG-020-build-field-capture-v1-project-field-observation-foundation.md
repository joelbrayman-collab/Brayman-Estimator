# Feature Gate FG-020: BUILD Field Capture V1 — Project Field Observation Foundation

| Attribute | Value |
|-----------|--------|
| Feature Gate ID | `FG-020` |
| Feature Name | BUILD Field Capture V1 — Project Field Observation Foundation |
| Target Milestone | **None.** FG-020 is the governing identifier. Do not assign a new M0xx number. |
| Module | **BUILD** owns Field Capture Events, Original Payloads, Derived Candidates, and BUILD binary original custody ([ADR-020](../adr/ADR-020-build-module-boundary.md) **Accepted**; [ADR-042](../adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) **Accepted**). **Office / platform** owns the `/api/v1` transport adapter (FG-019). **Projects** owns `projects` and the Project Hub. **Project Controls** owns Change Orders. |
| Date | 2026-08-31 |
| Status | **CLOSED / OPERATIONAL FOR UAT** (2026-09-01). Live current = head **`c1d2e3f4a5b6`**. Office UAT **PASSED** on port **5013**. Item 12 is **ELIGIBLE FOR SEPARATE GOVERNANCE / NOT AUTHORIZED**. This is **not** Field Web authorization. |
| Architecture | [ADR-042](../adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) **Accepted** · [ADR-020](../adr/ADR-020-build-module-boundary.md) **Accepted** · [ADR-022](../adr/ADR-022-field-client-and-shared-api.md) **Accepted** · [ADR-023](../adr/ADR-023-field-evidence-provenance.md) **Accepted** · [ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md) **Accepted** · [ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) **Accepted** · [ADR-041](../adr/ADR-041-user-membership-and-office-authentication.md) **Accepted** · [CAR-001](../architecture/CAR-001-calibai-product-architecture-reconciliation.md) · [platform-roadmap.md](../platform-roadmap.md) item 11 · [modules/build.md](../modules/build.md) |
| Related ADRs | [ADR-042](../adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) **Accepted** · [ADR-008](../adr/ADR-008-supplier-price-snapshotting.md) **Proposed** (do **not** accept) · [ADR-010](../adr/ADR-010-build-versus-buy-document-processing.md) **Proposed** (do **not** accept) |
| Prerequisites | [FG-018](FG-018-organization-authentication-actor-identity-and-membership-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-019](FG-019-shared-api-foundation-v1.md) **CLOSED / OPERATIONAL FOR UAT**. Roadmap item 10 **COMPLETE**. **ADR-042 Accepted.** BUILD architecture reconnaissance 2026-08-31. |
| Approved baseline | Live Alembic current = head **`b0c1d2e3f4a5`**. Full suite **494 passed**. Dedicated FG-019 **34 passed**. Dedicated FG-018 **37 passed**. |

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **CLOSED / OPERATIONAL FOR UAT** |
| ADR-042 | **Accepted** |
| Implementation reconnaissance | **RECORDED 2026-08-31.** HEIC/HEIF original custody was **corrected at implementation** (see below). |
| Implementation | **IMPLEMENTED.** Foundation dedicated tests **33 passed** / full suite **527**. Compatible Rendition increment: dedicated **44 passed** (33 + 11); focused Hub+FG-018+FG-019+FG-020 **128 passed**; full suite **538 passed**. |
| Schema / Alembic | Repository revision **`c1d2e3f4a5b6`**, `down_revision` **`b0c1d2e3f4a5`**. **Live current = head `c1d2e3f4a5b6`.** One graph head. |
| BUILD product code | **IMPLEMENTED** (office HTML, BUILD service, storage, bounded `/api/v1`, UAT CLI). |
| Field Web (Item 12) | **ELIGIBLE FOR SEPARATE GOVERNANCE / NOT AUTHORIZED.** FG-020 close does **not** start Field Web. |
| Compatible Renditions / Media Compatibility service | **IMPLEMENTED** (2026-08-31 image-only increment). HEIC/HEIF → JPEG automatically after Original Source preservation. Regenerable. No schema. See [build-media-storage-lifecycle.md](../architecture/build-media-storage-lifecycle.md). |
| Project Closeout / archive-and-purge | **FUTURE / NOT AUTHORIZED.** FG-020 must not block that future path. Renditions remain independently purgeable. |

Live migration and office UAT closed this gate on **2026-09-01**. Do **not** start Field Web from this close.

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
| 12 | Migration? | **YES** when the implementation prompt runs. Additive only. Designed revision **`c1d2e3f4a5b6`**, `down_revision` **`b0c1d2e3f4a5`**. **Do not create it in this recon pass.** |

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

Exact table names are frozen in **Implementation reconnaissance** below. The concepts remain Event / Original Payload / Derived Candidate.

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

**Complete (2026-08-31).** See **Implementation reconnaissance** below. Plans, historical ingestion, and Brand Profile custody were inspected. MIME/size recommendations are recorded. No product files were changed.

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
GET  /api/v1/projects/<id>/field-events/<event_id>/originals
GET  /api/v1/projects/<id>/field-events/<event_id>/originals/<original_id>
GET  /api/v1/projects/<id>/field-events/<event_id>/originals/<original_id>/content
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

FG-020 is **CLOSED / OPERATIONAL FOR UAT**. Item 12 is **ELIGIBLE FOR SEPARATE GOVERNANCE / NOT AUTHORIZED**. FG-020 close still does **not** authorize Field Web.

---

## Implementation authorization

This Feature Gate is **CLOSED / OPERATIONAL FOR UAT**.

File-custody implementation reconnaissance is **recorded** in this document. Bounded product implementation ran from the 2026-08-31 implementation prompt.

Do **not** run live `flask db upgrade` from this implementation prompt. Do **not** start Field Web.

---

## Implementation reconnaissance (2026-08-31)

**Status:** Recorded 2026-08-31. **Not implemented.** Verdict: **READY FOR BOUNDED IMPLEMENTATION.**

Inspected (read-only): Project / Hub / Change Orders; FG-018 User / membership / CSRF / actor helpers; FG-019 `/api/v1`; Plan Intelligence storage; historical-ingestion storage; Brand Profile logo storage; `app/__init__.py` GET-only API lock; test fixtures; Alembic head `b0c1d2e3f4a5`; `requirements.txt`.

### 1. Existing custody patterns

| Pattern | Root | Path | SHA | Size | MIME / magic | Overwrite | Download |
|---------|------|------|-----|------|--------------|-----------|----------|
| **Plans** | `instance/plan_uploads/` (`PLAN_UPLOAD_ROOT`) | `<project_id>/<uuid>.pdf` | SHA-256 stored; filename is UUID | **25 MB** (`PLAN_UPLOAD_MAX_BYTES`) | `.pdf` only; magic `%PDF` | New UUID each upload; no SHA-path reuse | Login + org-scoped project 404; `send_file` attachment |
| **Historical** | `instance/historical_uploads/` (`HISTORICAL_UPLOAD_ROOT`) | `<org_id>/<sha256>.xlsx\|.xlsm` | SHA-256 **is** the filename | **25 MB** | `.xlsx`/`.xlsm`; ZIP magic `PK\x03\x04`; OpenXML member checks | Same SHA: reuse if bytes match; **refuse** if SHA path bytes differ | Office review; not a public URL |
| **Brand logos** | `instance/brand_logos/` (`BRAND_LOGO_ROOT`) | `<org_id>/<sha256><ext>` | SHA-256 filename | **5 MB** | `.png`/`.jpg`/`.jpeg`/`.gif`; PNG/JPEG/GIF magic | Same as historical | `GET /settings/brand-logo` inline `send_file`; org-scoped 404 |

Shared: org or project segment sanitization; `os.path.basename` / relative-path checks; resolve-within-root; no remote URLs (logos). Plans use UUID names (not content-addressed). Historical/logos are content-addressed at org level because the file **is** the identity.

BUILD originals are **evidence instances**, not org-level identity. Two identical photos on one Event are still two originals. Do **not** copy historical SHA-named global dedup.

### 2. Recommended BUILD storage

```text
instance/build_originals/<organization_id>/<project_id>/<event_id>/<original_id><ext>
```

Config: `BUILD_ORIGINAL_ROOT` (default `instance/build_originals`); `BUILD_ORIGINAL_MAX_BYTES` = **25 * 1024 * 1024** (plan/historical class — logos’ 5 MB is a brand-graphic limit, not a photo/audio limit).

- Sanitize org segment with the same `[A-Za-z0-9._-]{1,50}` regex as historical/logos.
- Project id and event id / original id are integers; reject non-digits.
- Controlled stored name: `{original_id}{extension}` after flush (id known).
- Write via tempfile + `os.replace` + fsync (historical/logo pattern).
- Never overwrite a path whose bytes differ. If the path exists and SHA matches, reuse (crash-retry). If it exists and SHA differs, fail closed.
- SHA-256 of bytes stored on the Original row for integrity; **not** used as the filename.
- Path traversal: `normpath` equality, no `..`, resolve-within-root.
- Tests use a temp `BUILD_ORIGINAL_ROOT` (same pattern as `BRAND_LOGO_ROOT` under TESTING).
- Alembic must **not** write or delete bytes. Downgrade drops tables only.

### 3. Image MIME / size (V1)

Reuse Brand Profile **magic + extension** family. Do **not** use the 5 MB logo cap.

| Allow | MIME | Ext | Magic |
|-------|------|-----|-------|
| JPEG | `image/jpeg` | `.jpg` | `\xff\xd8\xff` |
| PNG | `image/png` | `.png` | `\x89PNG` |
| GIF | `image/gif` | `.gif` | `GIF87a` / `GIF89a` |

- Max size: **25 MB**.
- Declared extension must match magic. Do not trust `Content-Type` alone.
- Stored MIME is the canonical mapping above, not the caller’s string.
- **Omit HEIC / HEIF / WebP** in FG-020. No repository pattern; no transcode allowed; desktop Chrome cannot reliably display HEIC. Item 12 can request JPEG (`accept="image/jpeg"` / camera capture). Camera-roll HEIC is **deferred**, not a V1 blocker.
- Fail closed: empty, oversize, unknown ext, magic mismatch → 400.

### 4. Audio MIME / size (V1)

No existing audio custody. `requirements.txt` has no ffmpeg / mutagen / pydub. Store original bytes only. No transcode. No waveform. No ASR.

| Allow | MIME | Ext | Magic (practical) |
|-------|------|-----|-------------------|
| iPhone / Safari | `audio/mp4`, `audio/x-m4a`, `audio/aac` | `.m4a` / `.aac` | `ftyp` at offset 4 |
| MPEG | `audio/mpeg` | `.mp3` | `ID3` or MPEG frame sync `\xff\xfb` / `\xff\xf3` / `\xff\xf2` |
| WAV | `audio/wav` | `.wav` | `RIFF`….`WAVE` |
| Chrome MediaRecorder | `audio/webm` | `.webm` | EBML `\x1a\x45\xdf\xa3` |

- Max size: **25 MB**.
- Reject `video/mp4` and other non-allow-listed types even if `ftyp` matches.
- Residual risk: an `audio/mp4` ftyp file might be a video container. Do **not** add media parsers. Fail closed on MIME allow-list + family magic only.
- Desktop playback: HTML5 `<audio>` with authorized content URL for these MIME types. If a browser cannot play WebM, authorized download remains available. No conversion.

### 5. Exact Event schema — `field_capture_events`

| Column | Type | Notes |
|--------|------|--------|
| `id` | Integer PK | Matches Project / User integer identity |
| `organization_id` | String(50) NOT NULL FK `organizations.id` | indexed; membership-derived; never caller authority |
| `project_id` | Integer NOT NULL FK `projects.id` | indexed |
| `user_id` | Integer NULL FK `users.id` **ON DELETE SET NULL** | indexed; durable provenance |
| `actor_display_name` | String(150) NOT NULL | snapshot at create; length matches `User.display_name` |
| `occurred_at` | DateTime NOT NULL | field occurrence (naive UTC) |
| `created_at` | DateTime NOT NULL | server record time; `datetime.utcnow` |
| `supersedes_id` | Integer NULL FK `field_capture_events.id` **ON DELETE RESTRICT** | indexed; UNIQUE where not null |

**Omit:** `updated_at` (Event identity is immutable). **Omit:** archive/status/commercial lifecycle columns. **Omit:** Change Order / plan / permit FKs.

**Constraints:** UNIQUE `supersedes_id` (at most one successor). Service: superseded Event must share `organization_id` + `project_id`; `supersedes_id != id`.

**FK delete:** `project_id` / `organization_id` **RESTRICT**. Do **not** add `cascade="all, delete-orphan"` from `Project`.

### 6. Exact Original schema — `field_capture_originals`

| Column | Type | Notes |
|--------|------|--------|
| `id` | Integer PK | |
| `field_event_id` | Integer NOT NULL FK `field_capture_events.id` **ON DELETE RESTRICT** | indexed |
| `kind` | String(16) NOT NULL | `text` / `audio` / `image` |
| `text_body` | Text NULL | required iff `kind=text` |
| `stored_relative_path` | String(512) NULL | required iff audio/image |
| `sha256_hex` | String(64) NULL | required iff audio/image |
| `byte_size` | Integer NULL | required iff audio/image |
| `mime_type` | String(100) NULL | required iff audio/image |
| `original_filename` | String(255) NULL | justified (PlanDocument / historical); sanitized basename |
| `user_id` | Integer NULL FK `users.id` **ON DELETE SET NULL** | |
| `actor_display_name` | String(150) NOT NULL | |
| `created_at` | DateTime NOT NULL | |

**Omit:** `updated_at`. No UPDATE API.

**CHECK (shape):**

```text
(kind = 'text' AND text_body IS NOT NULL AND stored_relative_path IS NULL
  AND sha256_hex IS NULL AND byte_size IS NULL AND mime_type IS NULL)
OR
(kind IN ('audio','image') AND stored_relative_path IS NOT NULL
  AND sha256_hex IS NOT NULL AND byte_size IS NOT NULL AND mime_type IS NOT NULL
  AND text_body IS NULL)
```

**Cardinality:** no unique-on-kind. One Event may have one or many text, audio, and image originals.

### 7. Exact Derived Candidate schema — `field_capture_derived_candidates`

| Column | Type | Notes |
|--------|------|--------|
| `id` | Integer PK | |
| `field_event_id` | Integer NOT NULL FK `field_capture_events.id` **ON DELETE RESTRICT** | indexed |
| `kind` | String(80) NOT NULL | generic label; **not** a frozen taxonomy CHECK |
| `payload_json` | Text NOT NULL | JSON **object** text |
| `status` | String(20) NOT NULL default `PROPOSED` | CHECK `PROPOSED` / `CONFIRMED` / `REJECTED` |
| `source` | String(40) NOT NULL | `TEST_FIXTURE` / `UAT_CLI` / later `PROCESSOR` |
| `proposer_user_id` | Integer NULL FK `users.id` **ON DELETE SET NULL** | |
| `proposer_display_name` | String(150) NOT NULL | |
| `created_at` | DateTime NOT NULL | proposed_at |
| `decided_by_user_id` | Integer NULL FK `users.id` **ON DELETE SET NULL** | set on confirm/reject |
| `decided_by_display_name` | String(150) NULL | |
| `decided_at` | DateTime NULL | |

**Omit:** `updated_at`. Only decision columns mutate.

**Payload representation:** `Text` storing `json.dumps` of a **dict** (object). Matches `ProcessingResult.raw_payload` / permit snapshot JSON text. `db.JSON` is used for take-off geometry that is queried as structure; V1 Derived payload is not queried by key.

Service rules: `json.loads` must return `dict` (reject array/scalar); UTF-8; no Python objects; kind stripped non-empty ≤80 chars. Do not freeze labour/RFI/CO columns.

### 8. Confirm / reject

Lawful transitions: `PROPOSED → CONFIRMED`, `PROPOSED → REJECTED` only. **CONFIRMED and REJECTED are terminal.** Reprocess = **new** candidate.

Confirm/reject may change **only** `status`, `decided_by_user_id`, `decided_by_display_name`, `decided_at`. Must **not** alter Event, Original, Estimate, Proposal, Change Order, Permit, take-off, labour actuals, or MONITOR records. Service must not import those write APIs.

### 9. Actor provenance

On Event create, Original create, Derived propose, confirm, and reject:

1. `user_id` = `current_user.id` when authenticated (nullable only if no user — office/API always have a user).
2. Display-name snapshot = `current_actor_display_name()` (`app/services/auth.py`), truncated to 150.

Do not backfill non-BUILD tables. Do not accept caller-supplied `user_id` or actor name as authority (ignore if present).

### 10. `occurred_at` rule

Repository convention: naive UTC `datetime.utcnow` (no timezone tables).

| Boundary | Rule |
|----------|------|
| Schema | `occurred_at` NOT NULL |
| Server `created_at` | always `datetime.utcnow()`; never caller-supplied |
| Office form / API omit | default `occurred_at = created_at` |
| If supplied | parse ISO-8601; if aware, convert to UTC and drop tzinfo; store naive UTC |
| Invalid / unparseable | 400 |
| Field Web (later) | should send capture time explicitly; FG-020 default still applies if omitted |

No timezone product. Do not invent DST tables.

### 11. BUILD service architecture

Single module `app/services/build.py` (authoritative). Storage helper `app/services/build_storage.py`. Desktop routes and `/api/v1` **must** call these functions — no duplicated rules.

| Function | Role |
|----------|------|
| `create_field_event(project, *, occurred_at=None, supersedes_id=None)` | Event + actor snapshot |
| `add_text_original(event, text)` | Immutable text Original |
| `add_binary_original(event, *, kind, data, filename)` | Validate + store + Original row |
| `create_event_with_text(...)` | Office convenience: Event + text Original, original-only |
| `list_field_events(organization_id, project_id)` | Chronological (`occurred_at` desc, `id` desc) |
| `get_field_event(organization_id, project_id, event_id)` | None if missing/cross-org (404) |
| `list_originals(event)` / `get_original(...)` | |
| `open_original_file(original)` | Authorized path or error |
| `list_derived_candidates(event)` / `get_derived_candidate(...)` | |
| `propose_derived_candidate(event, *, kind, payload, source)` | Tests + UAT CLI only |
| `confirm_derived_candidate(candidate)` / `reject_derived_candidate(candidate)` | Terminal |
| `supersede_event(prior, *, text, occurred_at=None)` | New Event + text Original, `supersedes_id=prior.id` |

Raise `BuildServiceError` for operator-facing 400s. Cross-org → `None` (404), never 403 existence leak.

### 12. Exact API endpoints

Narrow the FG-019 GET-only lock in `app/__init__.py` `reject_api_mutating_methods` so **POST is allowed only** on BUILD field-event paths below. `/api/v1/me` and `/api/v1/projects` mutations remain **405**. `tests/test_shared_api_fg019.py` mutating tests already target only those three paths — keep them.

```text
POST /api/v1/projects/<id>/field-events
GET  /api/v1/projects/<id>/field-events
GET  /api/v1/projects/<id>/field-events/<event_id>
POST /api/v1/projects/<id>/field-events/<event_id>/originals
GET  /api/v1/projects/<id>/field-events/<event_id>/originals
GET  /api/v1/projects/<id>/field-events/<event_id>/originals/<original_id>
GET  /api/v1/projects/<id>/field-events/<event_id>/originals/<original_id>/content
GET  /api/v1/projects/<id>/field-events/<event_id>/derived
POST /api/v1/projects/<id>/field-events/<event_id>/derived/<candidate_id>/confirm
POST /api/v1/projects/<id>/field-events/<event_id>/derived/<candidate_id>/reject
```

**Binary strategy:** metadata on JSON GET; **bytes on GET `.../content`** (cookie session; no filesystem path in JSON). Desktop HTML uses a parallel Flask route for `<img>` / `<audio>` cookie GET:

```text
GET /projects/<project_id>/field-events/<event_id>/originals/<original_id>
```

Same `open_original_file` service. `as_attachment=False` for display; `?download=1` for download. Do **not** expose stored paths.

Do not add PUT/PATCH/DELETE. No `/api/v1/build`, `/today`, `/field`.

### 13. API contracts (summary)

Auth: FG-018 cookie/session. Tenant: membership org only. Unauthenticated → **401 JSON**. 0 or >1 memberships → **403**. Cross-org project/event/original → **404** `"Not found."` CSRF: Flask-WTF; JSON/multipart POST requires `X-CSRFToken` (existing office JSON pattern in `tests/test_auth_fg018.py`). GET does not need CSRF. No tokens. Ignore caller `organization_id`.

| Endpoint | Input | Success allow-list | Errors |
|----------|-------|--------------------|--------|
| POST field-events | JSON `{ "text"?, "occurred_at"?, "supersedes_id"? }`. `text` optional (event may be originals-only via follow-up POST). | event fields + `originals` array (may be empty or one text) | 400 empty/invalid; 404 project; 409 supersede conflict |
| GET field-events | — | array of event summaries | 404 project |
| GET event | — | event + originals summaries + derived summaries | 404 |
| POST originals | JSON `{ "kind":"text","text":"..." }` **or** multipart `kind` + `file` | original metadata (no path) | 400 kind/MIME/size/magic; 404 event |
| GET originals / GET original | — | metadata; `text_body` only for text; never `stored_relative_path` | 404 |
| GET content | — | bytes + canonical MIME; 404 if text kind | 404 |
| GET derived | — | candidates (kind, payload object, status, provenance) | 404 |
| POST confirm/reject | empty JSON `{}` | candidate after decision | 404; **409** if not PROPOSED |

Original-only create: POST event with `text` **or** POST event without originals then POST originals. Do **not** require derived.

Event JSON allow-list: `id`, `project_id`, `organization_id`, `user_id`, `actor_display_name`, `occurred_at`, `created_at`, `supersedes_id`, `superseded_by_id` (nullable, derived). Original allow-list: `id`, `kind`, `text_body`, `sha256_hex`, `byte_size`, `mime_type`, `original_filename`, `user_id`, `actor_display_name`, `created_at`. Never password, never filesystem path.

ISO datetime strings in JSON (`...Z`).

### 14. Desktop Hub / routes

Keep `#hub-build` Change Orders panel **unchanged** except remove the inner Future “Field BUILD is not operational” note (`tests/test_project_hub.py` currently asserts that copy — **update those assertions** in implementation).

Add a sibling **Field Observations** `article.panel` under the same BUILD section (second panel in `dash-panels`), **not** a replacement for COs.

Hub list columns: occurred_at, created_at, actor, original-kind summary, current/superseded badge. Link to detail. “Add text observation” button.

| Route | Purpose |
|-------|---------|
| GET/POST `/projects/<id>/field-events/new` | Office text create (`occurred_at` optional datetime-local) |
| GET `/projects/<id>/field-events/<event_id>` | Detail / review |
| POST `/projects/<id>/field-events/<event_id>/supersede` | Correction: new Event + text, `supersedes_id` |
| POST `.../derived/<candidate_id>/confirm` and `/reject` | HTML forms, CSRF |
| GET `.../originals/<original_id>` | Inline evidence |

`assemble_project_hub` adds `field_events` via BUILD list service. No Field Web styling.

**Text:** show `text_body`. **Image:** bounded `<img src>` to authorized original URL (browser-native). **Audio:** `<audio controls src>` for supported MIME; plus download link. No transcription, waveform, or conversion.

**Supersession UX:** prior Event remains listed with “Superseded” and link to successor. Successor shows “Correction of event #n”. No destructive edit.

**Derived UAT without AI:** no fake AI UI. `propose_derived_candidate` is **service + Flask CLI** (`flask build propose-derived-candidate`) with `source=UAT_CLI` or `TEST_FIXTURE`. Office detail **displays and confirm/rejects** if candidates exist.

### 15. Private download authorization

Every binary open must verify: authenticated active User; exactly one active membership; `organization_id` match; project in that org; event belongs to that project; original belongs to that event. Any miss → **404**. Do not leak paths. Reuse plan/logo fail-closed 404.

### 16. Migration design — do not create now

| Field | Value |
|-------|--------|
| Revision | **`c1d2e3f4a5b6`** |
| `down_revision` | **`b0c1d2e3f4a5`** |
| Filename | `migrations/versions/c1d2e3f4a5b6_add_build_field_capture_fg020.py` |
| Upgrade | create three tables + indexes + CHECKs + unique `supersedes_id` |
| Downgrade | drop tables/indexes only; **do not** delete `instance/build_originals` |
| Seed | **none** |

Continuing the existing 12-hex rotate (`a9b0c1d2e3f4` → `b0c1d2e3f4a5` → `c1d2e3f4a5b6`).

### 17. Implementation files (later prompt only)

**NEW:** `app/models/build.py`; `app/services/build.py`; `app/services/build_storage.py`; `app/routes/build.py`; `app/cli/build.py`; `app/templates/build/event_detail.html`; `app/templates/build/event_form.html`; `migrations/versions/c1d2e3f4a5b6_add_build_field_capture_fg020.py`; `tests/test_build_field_observation_fg020.py`.

**CHANGED:** `app/models/__init__.py`; `app/__init__.py` (register blueprint + CLI; `BUILD_ORIGINAL_*` config; TESTING temp root; **narrow** API mutating-method lock); `app/routes/api_v1.py`; `app/services/project_hub.py`; `app/templates/projects/detail.html`; `tests/test_project_hub.py` (Field Observations present; CO section remains; drop Future Field BUILD assertion).

**Likely unchanged:** `tests/test_shared_api_fg019.py` (405 tests already scoped to `/me` and `/projects`); `tests/test_auth_fg018.py`.

### 18. Dedicated tests — `tests/test_build_field_observation_fg020.py`

Reuse `tests/auth_fixtures.py` + autouse login. CSRF dedicated app like FG-018/019. Cover: Event/text/original-only; actor `user_id` + snapshot; `occurred_at` default vs supplied vs distinct from `created_at`; supersession + unique successor + same-project; Original immutability (no update path / refuse overwrite); kinds; SHA; MIME/magic; size; storage path segments; traversal; authorized download; unauthenticated 401/302; cross-org 404; derived PROPOSED/confirm/reject/terminal 409; no Estimate/Proposal/CO/Permit/take-off/MONITOR/labour-actual writes; API 401/403/404; API CSRF; caller org ignored; Hub list; office create; detail; evidence display; CO section remains. Exact count deferred.

### 19. Regression

`tests/test_auth_fg018.py`; `tests/test_shared_api_fg019.py`; `tests/test_project_hub.py` (**will change**); `tests/test_change_orders.py`; `tests/test_plan_upload.py` / `tests/test_plan_indexing.py` / `tests/test_sheet_intelligence.py` / `tests/test_scale_measurement.py` / `tests/test_takeoff.py`; `tests/test_labour_engine.py`; `tests/test_pricing_engine.py`; `tests/test_permit_foundation_fg015.py`; `tests/test_permit_intelligence_fg016.py`; `tests/test_estimates.py`; `tests/test_proposals.py`; `tests/test_organization_foundation.py`; `tests/test_historical_upload_fg013.py`; `tests/test_brand_profile_fg017.py`. Then `./venv/bin/python -m pytest -q`. Baseline **494 passed**.

### 20. Security / failure matrix

| Case | Behavior |
|------|----------|
| Unauthenticated API | 401 JSON |
| Unauthenticated office | 302 `/login` |
| Inactive User | session loader returns None → 401/302 |
| 0 or >1 memberships | API 403; office 403 |
| Cross-org project/event/original | 404 |
| Malformed event / unsupported kind / MIME mismatch / oversize / empty / bad magic | 400 |
| Duplicate upload (same bytes, new original) | **allowed** (separate evidence rows) |
| Duplicate SHA path crash-retry | reuse if bytes match; refuse if differ |
| Missing event/candidate | 404 |
| Confirm/reject terminal | 409 |
| Supersede foreign / wrong-project Event | 404 |
| Unique supersede conflict | 409 |
| Missing CSRF on POST | 400 CSRF |
| Traversal in stored path | ValueError → 404 |
| Caller `organization_id` | ignored |

### 21. Field Web boundary

FG-020 implementation **must not** include Today, iPhone Capture chrome, microphone UI, camera UI, outdoor styling, one-handed field nav, or local retry. Item 11 must leave Event/Original/Derived + custody + API so Item 12 can build those without a second datastore.

### 22. Readiness

**READY FOR BOUNDED IMPLEMENTATION.**

HEIC/WebP omitted with repository rationale (not a Joel blocker). Residual audio-in-video `ftyp` risk accepted without new parsers. GET-only API lock must be **narrowed**, not repealed.

---

## Implementation result (2026-08-31)

**Status:** **IMPLEMENTED / LIVE MIGRATION PENDING.** Not closed. Live `flask db upgrade` was **not** run.

### HEIC/HEIF original-custody correction

Recon §3 omitted HEIC/HEIF so desktop Chrome could preview JPEG/PNG/GIF. Joel’s implementation prompt corrected that.

**Custody and rendering are separate.** CalibAi is iPhone-first. Original photographic bytes are evidence. FG-020 **preserves** HEIC/HEIF originals in addition to JPEG, PNG, and GIF.

- Do **not** transcode the original.
- Do **not** replace an HEIC/HEIF original with JPEG.
- Do **not** modify original bytes.
- Store original bytes, SHA-256, byte size, canonical MIME, original filename where permitted, and provenance.
- Validation uses narrow ISO-BMFF `ftyp` brand recognition (`heic` / `heif` / `mif1` / related still-image brands). Generic `mp41`/`mp42`/`isom` and AVIF are **not** accepted as HEIC.
- Desktop: if the browser cannot natively preview HEIC/HEIF, render the Compatible JPEG Rendition when present. If generation failed, show a photo placeholder plus authorized Original download. Do **not** present a broken `<img>`. A Compatible Rendition is regenerable working/display storage, **not** Original Source. See [build-media-storage-lifecycle.md](../architecture/build-media-storage-lifecycle.md).
- **WebP remains out.**

### File-custody rules (implemented)

Root: `instance/build_originals/<organization_id>/<project_id>/<event_id>/<original_id><ext>` (`BUILD_ORIGINAL_ROOT`, `BUILD_ORIGINAL_MAX_BYTES` default **25 MB**). SHA-256 is evidence metadata on the row, not the filename. Duplicate bytes are allowed as separate Original records. Tempfile + fsync + `os.replace`. Path-traversal and org-segment checks. Alembic does **not** touch stored bytes. Tests use a temp `BUILD_ORIGINAL_ROOT`.

**Audio known limitation:** ISO-BMFF `ftyp` inspection cannot prove an audio stream is present without a media parser. FG-020 does not add a parser. Residual audio-in-video `ftyp` risk remains. Caller `Content-Type` is not authority. Canonical MIME comes from extension + family magic. `video/mp4` is not a stored MIME.

### Live current vs repository head

| Kind | Revision |
|------|----------|
| Live `flask db current` | **`c1d2e3f4a5b6`** (after 2026-09-01 close) |
| Repository Alembic head | **`c1d2e3f4a5b6`** |
| Graph heads | one (`c1d2e3f4a5b6`) |

**Subsequent status (2026-09-01):** live current = head. See Live migration / office UAT close above.

### Tests

| Suite | Result |
|-------|--------|
| Dedicated `tests/test_build_field_observation_fg020.py` | **33 passed** |
| Dedicated `tests/test_build_media_compatibility_fg020.py` | **11 passed** (HEIC/HEIF → JPEG increment) |
| Combined dedicated FG-020 | **44 passed** |
| Focused (Hub + FG-018 + FG-019 + both FG-020 files) | **128 passed** |
| Full suite `./venv/bin/python -m pytest -q` | **538 passed** (pre-increment governed baseline **527**; pre-FG-020 **494**) |

`tests/test_auth_fg018.py::test_testing_secret_allowed` now unsets env `SECRET_KEY` so the TESTING fallback assertion is isolated (same pattern as the sibling debug-secret test).

### Live migration / office UAT close (2026-09-01)

**Status:** **CLOSED / OPERATIONAL FOR UAT.**

| Item | Evidence |
|------|----------|
| Live Alembic | `flask db current` = `flask db heads` = **`c1d2e3f4a5b6`**. One graph head. Upgrade `b0c1d2e3f4a5` → `c1d2e3f4a5b6` was already applied on the live UAT DB before this close pass; this pass **verified** current=head and did **not** re-run upgrade or create a second revision. |
| Office UAT port | **5013** (existing listener reused; CSRF enabled; debug off; gitignored `.env` `SECRET_KEY`) |
| UAT project | Project **12** `FG-018 UAT Actor Project` / ORG-001 |
| Prior UAT events (2026-08-31) | Events **1–8** (text default/explicit, JPEG, HEIC, stub HEIC, supersession 8→7, derived 1 CONFIRMED / 2 REJECTED) |
| This-pass events (2026-09-01) | **9** text default (later superseded); **10** text explicit; **11** JPEG; **12** HEIC; **14** WAV audio; **15** correction of 9; **16** org-override ignored (still ORG-001); **17** undecodable HEIC stub |
| Originals (this pass) | JPEG **12** SHA `bc1895be…1355`; HEIC **13** SHA `fb82c4ea…9c3a` (bytes intact; JPEG rendition 64×96; long edge ≤ 2048; no upscale); audio **14**; stub **17** SHA `25d6b18d…4ad5` |
| Rendition regen | Deleted `display.jpg` for original 13; display GET regenerated JPEG; Original SHA unchanged |
| Conversion failure | Event 17 / original 17: Original kept; `/display` **404**; Event Detail fallback + Original link; no broken HEIC `<img>` |
| Supersession | 15 supersedes 9; 9 preserved Current→Superseded; API second successor **409** |
| Derived | CLI `propose-derived-candidate` candidates **3** CONFIRMED / **4** REJECTED on event 10; actor snapshot Joel Brayman; terminal re-decision API **409** |
| Cross-module | Estimate / Proposal / Change Order / Brand / Permit fingerprints **unchanged** after BUILD writes |
| Auth / tenant | Office unauth **302** `/login`; API unauth **401** JSON; cross-org project 4 **404** office and API |
| BUILD API | Event create/list/detail; Original create/list/detail/content; Derived list/confirm/reject; cookie session; membership org; caller `organization_id` ignored; mutation CSRF required (**400** if missing); no path serialization |
| FG-019 lock | `POST /api/v1/me` **405**; `POST /api/v1/projects` **405** |
| Desktop usability | Authenticated Project Hub HTML: Change Orders remain; Field Observations beside them; actor / occurred_at / created_at / original kinds / Current vs Superseded; Add text observation; PLAN / PRICE / CONTRACT intact; HEIC Event Detail labeled Photo and served via JPEG `/display`; Original download; audio `<audio>` no waveform/transcription; no filesystem path leak. Interactive Cursor browser tab could not be created this session; usability is from authenticated rendered office HTML, not HTTP status alone. |
| Tests | Dedicated **44 passed**; focused **128 passed**; full suite **538 passed** |
| Item 11 | **COMPLETE** |
| Item 12 | **ELIGIBLE FOR SEPARATE GOVERNANCE / NOT AUTHORIZED** |
| Closeout | **FUTURE / NOT AUTHORIZED.** Active storage remains Original Source + regenerable Compatible Rendition. Renditions remain independently purgeable. |
| Commercial Execution | Native Signing remains **WAITING FOR COUNSEL / IMPLEMENTATION NOT AUTHORIZED**. No signing Feature Gate. Counsel spec unchanged. |

**Operational note:** CLI `flask auth reset-password` was used on the existing placeholder office user so this pass could authenticate. The original bootstrap password is not in the repository. Reset again if a different office password is required. Do not commit credentials.

Do **not** start Field Web. Do **not** implement Native Signing, mail, Contract, or Project Closeout from this close.

### Subsequent status (2026-08-31 media storage lifecycle)

Joel clarified Original Source vs Compatible Rendition vs Closed Project Archive. Canonical pin: [build-media-storage-lifecycle.md](../architecture/build-media-storage-lifecycle.md).

This clarification does **not** rewind FG-020 to **IMPLEMENTATION NOT STARTED**. Landed FG-020 Original Source custody stands.

### Subsequent status (2026-08-31 Compatible Rendition increment)

Authorized FG-020 increment implemented **before** live migration / office UAT:

- HEIC/HEIF Original Source remains immutable and SHA-governed
- Automatic JPEG Compatible Rendition after Original preservation (`Pillow` + `pillow-heif`, quality **85**, max long edge **2048 px**)
- Storage: `instance/build_renditions/<org>/<project>/<event>/<original_id>/display.jpg`
- No new Alembic revision
- Image-only. Audio conversion **not** added
- Project Closeout **not** started
- Field Web **not** started
- Live `flask db upgrade` **not** run

**Subsequent status (2026-09-01):** live-migration / office UAT **closed** this gate. Do **not** implement Closeout. Do **not** start Field Web.

---

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Joel Brayman | 2026-08-31 |
| ChatGPT review | FG-020 approval + implementation reconnaissance authorization | 2026-08-31 |
| Cursor implementation note | Gate **APPROVED**. Recon **recorded**. BUILD product code **not started**. No migration. | 2026-08-31 |
