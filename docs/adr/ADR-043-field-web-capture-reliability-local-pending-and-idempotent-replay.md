# ADR-043 — Field Web Capture Reliability, Local Pending Capture, and Idempotent Replay Architecture

| Field | Value |
|-------|--------|
| Title | ADR-043: Field Web Capture Reliability, Local Pending Capture, and Idempotent Replay Architecture |
| Status | **Proposed / for Joel review.** Not Accepted. Not implementation authorization. |
| Date | 2026-09-01 |
| Related | [ADR-042](ADR-042-build-field-evidence-and-iphone-first-capture.md) **Accepted** · [ADR-022](ADR-022-field-client-and-shared-api.md) **Accepted** · [ADR-023](ADR-023-field-evidence-provenance.md) **Accepted** · [ADR-041](ADR-041-user-membership-and-office-authentication.md) **Accepted** · [FG-018](../feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) **CLOSED / OPERATIONAL FOR UAT** · [FG-019](../feature-gates/FG-019-shared-api-foundation-v1.md) **CLOSED / OPERATIONAL FOR UAT** · [FG-020](../feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) **CLOSED / OPERATIONAL FOR UAT** · [FG-021](../feature-gates/FG-021-field-web-v1-today-and-capture.md) **DRAFT FOR JOEL REVIEW / NOT APPROVED** · [architecture/field-web-today-and-capture.md](../architecture/field-web-today-and-capture.md) · [modules/build.md](../modules/build.md) · [architecture/build-media-storage-lifecycle.md](../architecture/build-media-storage-lifecycle.md) |

This ADR is **Proposed**. It does **not** accept itself. It does **not** approve [FG-021](../feature-gates/FG-021-field-web-v1-today-and-capture.md). It does **not** authorize Field Web product code, a migration, Native Signing, transcription, or a PWA.

ADR-042 remains the dual-surface / original-custody ADR. This ADR covers **Field client capture reliability**: local pending hold, client operation identity, and server idempotent replay.

---

## Context

Item 11 / [FG-020](../feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) delivered the authoritative BUILD Field Capture Event, Original Payloads, and office review surface. Item 12 Field Web reconnaissance ([field-web-today-and-capture.md](../architecture/field-web-today-and-capture.md)) is **COMPLETE / NOT IMPLEMENTED**.

Joel’s product decisions for Field Web V1 (memorialized here; not implementation):

```text
TODAY + PROJECT CONFIRMATION + CAPTURE
VOICE / PHOTO / SHORT TEXT
Flask/Jinja purpose-built Field routes + focused JavaScript + existing Shared API
NOT: resized office app, React/Vue SPA, PWA V1, native iOS V1
```

Two first-class surfaces remain ([ADR-042](ADR-042-build-field-evidence-and-iphone-first-capture.md) Decision 1):

```text
DESKTOP: Flask HTML → BUILD services → BUILD records
FIELD:   Field Web → Shared API → SAME BUILD services → SAME BUILD records
```

No second Field datastore.

[ADR-042](ADR-042-build-field-evidence-and-iphone-first-capture.md) Decision 17 layer **B** requires Field Web to be online-first with a **minimal** local original hold / retry until server ACK. Layer **C** (full offline sync, durable queue, conflict management, native) remains later and separately governed.

Inspected FG-020 schema (`app/models/build.py`, revision `c1d2e3f4a5b6`): `field_capture_events` and `field_capture_originals` have **no** client UUID / idempotency key. Duplicate SHA bytes are lawful as separate Original rows. A naïve retry of POST Event or POST Original **will duplicate** commercial evidence when the HTTP response is lost.

That gap is the decision this ADR exists to lock.

---

## Decision

**Proposed.** Do **not** treat this file as Accepted, as FG-021 approval, or as product authorization.

### 1. Online-first; retain until ACK; not full offline sync

Field Web V1 is **online-first**. It is **not** full offline synchronization.

A contractor’s Original Capture must not be silently lost merely because connectivity fails before server acknowledgement.

Field Web may temporarily retain **unsent / unacknowledged** capture data locally until ACK or user discard.

Preferred V1 mechanism: **IndexedDB**. Do **not** use `localStorage` for binary media.

No service worker. No installable PWA. No durable offline project archive.

### 2. Client capture identity is operation identity, not authority

Before the first server Event POST, Field Web creates a durable:

```text
client_capture_uuid
```

This identifies the **client operation**.

It is **not**:

- Event authority
- Organization authority
- Project authority
- actor authority

Organization remains membership-derived (FG-018). Project remains server-validated (existing `projects` row; FG-019/020). Actor remains the authenticated session (`_actor_snapshot()` in `app/services/build.py`). Caller `organization_id` and caller-supplied actor identity remain ignored as authority.

The server must make **lawful replay** of the same `client_capture_uuid` idempotent: return/reuse the existing Event; do not create a second Event.

### 3. Client Original identity

Each client Original receives:

```text
client_original_uuid
```

before first upload.

Repeated lawful replay of the **same** `client_original_uuid` to the **same** Event must return/reuse the existing Original. It must not create a duplicate merely because the HTTP response was lost.

Different UUIDs may contain identical bytes. **SHA equality alone does not establish duplicate operation identity.** FG-020’s lawful duplicate-SHA behavior remains for distinct operations.

Do **not** overload historical-ingestion `idempotency_key`.

### 4. Server uniqueness (direction; exact schema in implementation reconnaissance)

Tenant-safe uniqueness direction:

| Record | Direction |
|--------|-----------|
| Event | Unique `(organization_id, client_capture_uuid)` where `client_capture_uuid` is present |
| Original | Unique involving the Event (and organization as required) and `client_original_uuid` where present. Recommended: unique `(field_capture_event_id, client_original_uuid)` where `client_original_uuid` is present |

Exact column names, types, indexes, partial-unique SQLite syntax, and constraint names remain **subject to implementation reconnaissance**. Do **not** create the migration in this pass.

Office-created Events/Originals must remain lawful without client UUIDs. Client UUID fields should therefore be **nullable** for non-Field records unless later reconnaissance proves another bounded design is better.

No historical backfill.

### 5. Partial success

Transaction model: **create/reuse Event, then upload Originals individually.**

Example:

```text
audio:   ACK
photo 1: ACK
photo 2: FAIL
```

Result: Event remains. Audio remains server-saved. Photo 1 remains server-saved. Photo 2 remains local **NEEDS RETRY** and retries with the **same** `client_original_uuid`.

Do **not** roll back acknowledged Originals.

### 6. SAVING / SAVED / NEEDS RETRY are Field client UX states

These are **Field client** states. Do **not** create new BUILD commercial/domain statuses merely to represent them.

| Client state | Meaning |
|--------------|---------|
| **SAVING** | One or more required server operations pending |
| **SAVED** | All required Event/Original operations ACK’d |
| **NEEDS RETRY** | One or more operations failed or unacknowledged |

BUILD Event/Original rows remain FG-020 records. No Field-only parallel lifecycle.

### 7. Local data lifecycle

IndexedDB may contain only the **minimum** pending-capture data: project id, client UUIDs, Original kind + bytes/text, created-local timestamp, retry state.

| Moment | Rule |
|--------|------|
| Before ACK | Retain required pending Event metadata / Original blobs / UUIDs |
| After each Original ACK | Delete that Original’s local binary payload immediately |
| After complete capture ACK | Remove completed pending capture state |
| Logout | Wipe pending local capture data. Warn before logout where practical if pending data exists |
| IndexedDB unavailable or full | Do **not** claim safe capture. Block or fail visibly |
| Permanent local Project archive | **Forbidden** |

### 8. Auth / CSRF recovery

Reuse FG-018 / FG-019 / FG-020. Cookie/session authentication. **No tokens.**

If the session expires during pending upload:

1. retain local pending capture
2. surface NEEDS RETRY / login requirement
3. governed office login
4. `safe_next_url` back to Field
5. resume the same idempotent operations

CSRF remains **mandatory**. No broad exemption. Field JS submits the existing CSRF token using `X-CSRFToken` on every POST, including multipart.

Expired CSRF: refresh lawfully (same-origin Field GET / meta tag) and replay the **same** idempotent operation.

Field HTML unauthenticated = 302 `/login`. `/api/v1` unauthenticated = **401 JSON**. Do not weaken either.

### 9. Privacy

Pending local media exists only to protect unfinished capture.

Do **not** add geolocation, device fingerprint, biometrics, permanent local caching, or hidden background collection.

Shared-device risk is why logout clears pending media.

### 10. PWA / offline boundary

V1 remains **ordinary mobile web**.

No service worker required. No installable PWA requirement. No full offline synchronization.

Later separately governed capability may add PWA, offline shell, durable queue, conflict/replay architecture, or a native client. Do **not** pre-implement those decisions.

---

## Alternatives considered

- **Client-only retry without server unique keys** — Rejected. Lost HTTP ACK plus retry duplicates evidence. FG-020 has no Event/Original idempotency column.
- **SHA-only duplicate detection** — Rejected. Distinct photos can share no SHA; two retries of an empty Event have no SHA; identical bytes from two genuine operations must remain lawful.
- **Single multipart “all Originals in one request”** — Rejected as the V1 transaction model. Partial failure would force all-or-nothing or a new batch protocol. Event-then-Originals matches the landed API.
- **localStorage for media** — Rejected. Quota is too small for 25 MB Originals.
- **PWA / service worker V1** — Rejected. IndexedDB retry-until-ACK does not require an offline shell.
- **SPA / React / Vue** — Rejected for V1 (Joel). Flask/Jinja Field family + page JS reuses cookie session and CSRF meta.
- **New BUILD domain statuses for SAVING/SAVED/NEEDS RETRY** — Rejected. Those are client UX states.
- **Tokens for Field** — Rejected. FG-018/019/020 cookie/session remains.

---

## Consequences

Positive: Field capture can survive ordinary job-site radio loss without silent duplicate Events/Originals. Office-created records stay lawful. ADR-042 dual-surface / original-custody rules stay intact.

Negative: FG-021 needs an additive schema + API replay semantics + IndexedDB client complexity + real-device UAT. Implementation reconnaissance must still freeze column names and SQLite unique-index form.

---

## Module ownership impact

| Concern | Owner |
|---------|--------|
| Field Capture Event / Original / Derived Candidate / BUILD custody | **BUILD** (unchanged) |
| Idempotent Event/Original create in BUILD services | **BUILD** |
| `/api/v1` adapters (including display rendition GET) | **Office / platform** transport + BUILD services |
| Field HTML/JS, IndexedDB pending hold, client UX states | **Field Web (client)** — proposed FG-021 |
| Cookie session / CSRF | **Office / platform** (FG-018; unchanged) |
| Project | **Projects** (referenced; no new Project model) |

Field Web does **not** own BUILD records.

---

## Data ownership impact

Adds **optional** client operation identifiers on BUILD Event/Original rows. Does **not** transfer ownership. Does **not** create a Field datastore. Compatible Renditions remain regenerable working artifacts ([build-media-storage-lifecycle.md](../architecture/build-media-storage-lifecycle.md)).

---

## Migration impact

**Required** for FG-021 implementation (one additive revision after `c1d2e3f4a5b6`). **Not created in this pass.** No historical backfill. Exact revision identifier deferred to implementation reconnaissance.

---

## Testing impact

See [FG-021](../feature-gates/FG-021-field-web-v1-today-and-capture.md). Dedicated automated replay tests plus real iPhone UAT. Desktop emulation cannot close Field Web.

---

## Documentation impact

This ADR; FG-021; field-web pin subsequent status; adr index; feature-gate index; BUILD module; current-state; session-handoff; roadmap; project-state-report; chat-workflow-log; milestones.

---

## Native Signing pin

This ADR does **not** govern Native Signing.

```text
NATIVE SIGNING DEVELOPMENT:
MAY PROCEED UNDER SEPARATE GOVERNANCE

NATIVE SIGNING PRODUCTION ACTIVATION / REAL CUSTOMER USE:
BLOCKED PENDING ONTARIO COUNSEL APPROVAL OF THE SIGNING PROCESS
```

Counsel review is **not** a Field Web hold. Legal Content Gate for Ontario Contract / Warranty templates remains in force and is separate.

---

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | | |
| ChatGPT review | | |
| Cursor implementation note | Proposed only. Not Accepted. Not implemented. |
