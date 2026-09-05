# Architecture reconnaissance — Field Web / Today + Capture (Roadmap Item 12)

| Attribute | Value |
|-----------|--------|
| Status | **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT OPEN.** [ADR-043](../adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md) **Accepted**. [FG-021](../feature-gates/FG-021-field-web-v1-today-and-capture.md) **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT OPEN**. Gate **NOT CLOSED**. Bounded LAN iPhone Save Original UUID repair landed. Live current = head `d2e3f4a5b6c7`. |
| Date | 2026-09-01 |
| Product | The Estimator / CalibAi |
| Roadmap | Item 12 — Field Web / Today + Capture |
| Canonical record | This document |
| Prerequisites | Item 10 **COMPLETE** (FG-018 + FG-019). Item 11 / [FG-020](../feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) **CLOSED / OPERATIONAL FOR UAT**. [ADR-042](../adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) **Accepted**. [ADR-022](../adr/ADR-022-field-client-and-shared-api.md) **Accepted**. |
| Related | [modules/build.md](../modules/build.md) · [build-media-storage-lifecycle.md](build-media-storage-lifecycle.md) · [ADR-023](../adr/ADR-023-field-evidence-provenance.md) · [ADR-041](../adr/ADR-041-user-membership-and-office-authentication.md) · Native Signing is a **parallel** commercial-execution track (see §34) |
| Repository baseline | `main` @ `42b9c792b7c4fd968ed46be0ff15975cf3880eb5` = `origin/main`. Alembic current = heads **`c1d2e3f4a5b6`**. Full suite **538 passed** claimed from FG-020 close — **not rerun** this docs-only recon. |

This reconnaissance is **complete** as architecture. Subsequent 2026-09-01 governance draft: [ADR-043](../adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md) was **Proposed**; [FG-021](../feature-gates/FG-021-field-web-v1-today-and-capture.md) was **DRAFT FOR JOEL REVIEW / NOT APPROVED** (committed `6273fa4`). Subsequent 2026-09-02: ADR-043 is **Accepted**; FG-021 is **APPROVED / IMPLEMENTATION NOT STARTED**; implementation recon is **COMPLETE** ([fg-021-field-web-v1-implementation-reconnaissance.md](fg-021-field-web-v1-implementation-reconnaissance.md)). Subsequent 2026-09-02 product: FG-021 **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT PENDING**. **Current status (2026-09-05):** FG-021 **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT OPEN**. Gate **NOT CLOSED**. Text / screenshot PNG / Take Photo JPEG / voice Save / network retain-retry / browser-close IndexedDB recovery **PASS**. HEIC real-device remains **OPEN** (library Choose Photo **NOT EXERCISED** — Safari delivered JPEG). Mixed capture and Observation Delete remain **OPEN**. Live current = head `d2e3f4a5b6c7`. This architecture pin still does **not** authorize Native Signing production, transcription, PWA, MONITOR, Project Closeout, or Contract.

### 41-section report coverage (this pin is canonical)

Parent report sections 1–41 map here. Do **not** create a second architecture document.

| Report § | Topic | This pin |
|----------|-------|----------|
| 1 | Repository baseline | Header table + this recon inspect |
| 2 | Field Web purpose | §1 |
| 3 | Desktop/field boundary | §2 |
| 4 | V1 information architecture | §4 |
| 5 | Today | §5 |
| 6 | Project context | §6 |
| 7 | Capture flow | §7 |
| 8 | Voice / Safari MediaRecorder | §8 |
| 9 | Camera | §9 |
| 10 | Text | §10 |
| 11 | Multi-Original transaction | §11 |
| 12 | Poor-connectivity / ACK | §12 |
| 13 | Idempotency | §13 |
| 14 | Local-storage / privacy | §14 |
| 15 | Auth / session recovery | §15 |
| 16 | CSRF | §16 |
| 17 | API sufficiency / delta | §17 |
| 18 | Derived Candidates | §18 |
| 19 | Plan access | §20 |
| 20 | Change Order visibility | §19 |
| 21 | Media behavior | §21 |
| 22 | Technology (A Flask/Jinja vs B SPA vs C) | §22 |
| 23 | PWA | §23 |
| 24 | Route architecture | §24 |
| 25 | Job-site usability | §3 + §25 |
| 26 | Desktop continuity | §26 |
| 27 | `occurred_at` | §28 |
| 28 | Failure / recovery | §29 |
| 29 | Real-device UAT | §30 |
| 30 | Schema / migration | §13 + §31 |
| 31 | ADR-043 | §31 |
| 32 | FG-021 | §31 (now drafted; not approved) |
| 33 | Proposed scope | §31 |
| 34 | Non-goals | §31 + §33 |
| 35 | Acceptance criteria | §35 |
| 36 | Dedicated test plan | §36 |
| 37 | Item 12 completion rule | §32 |
| 38 | Native Signing dependency pin | §34 |
| 39 | Unresolved Joel decisions | §37 |
| 40 | Conflicts / stale docs | §38 |
| 41 | Next governed action | §39 |

---

## 1. Product purpose

Field Web is a **first-class** CalibAi operating surface.

It is **not**:

- the desktop Flask office application shrunk onto an iPhone
- a second BUILD datastore
- a generic construction-management app
- a native iOS app
- a replacement for the desktop office surface

Primary purpose:

```text
FAST, LOW-FRICTION JOB-SITE CAPTURE AND ACCESS
using the authoritative BUILD domain completed in Item 11.
```

SAVE ORIGINAL is a complete evidence action. Structure, Derived Candidates, Change Orders, and MONITOR are **not** Field V1 work.

---

## 2. Two first-class surfaces (preserve ADR-042)

| Surface | Optimized for | Path |
|---------|---------------|------|
| **Desktop / office** | Review, management, context, history, confirmation, investigation | Flask HTML → BUILD services → BUILD records |
| **Field / iPhone** | Capture, quick project context, minimal typing, voice, camera, one-handed use, outdoor conditions | Field Web → Shared API → **the same** BUILD services → **the same** BUILD records |

No duplicated domain logic. No field-note entity. No mobile BUILD tables.

Office HTML continues to call Flask services **directly**. Field Web consumes `/api/v1`. That split is already Accepted ([ADR-042](../adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) Decision 1; [FG-019](../feature-gates/FG-019-shared-api-foundation-v1.md)).

---

## 3. iPhone-first V1 target

Primary target: **current iPhone Safari**, portrait-first.

Architectural/UI implications (do not implement here):

| Constraint | V1 implication |
|------------|----------------|
| Viewport | Design for current iPhone logical widths (~390 CSS px class). Do not assume iPad or desktop density. |
| Portrait-first | Capture chrome is a vertical stack. Landscape is tolerated (preview/playback), not the design center. |
| Safe area / notch | `viewport-fit=cover` + `env(safe-area-inset-*)` on Field templates. Office `app.css` does **not** currently do this. |
| Touch | Minimum ~44×44 CSS px targets. Primary Capture control larger. |
| One-handed | Primary actions in the thumb zone. Shallow stack (Today → Project confirm → Capture). |
| Sunlight / gloves / dirt | High contrast; large type; few small icons; no hover-only affordances. |
| Seconds of attention | No desktop tables as the capture path. No sidebar shell. |
| Weak radio | Online-first with retain/retry-until-ACK ([ADR-042](../adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) Decision 17 layer B). |

Existing office CSS (`app/static/css/app.css`) has 1200 / 900 / 640 breakpoints and a collapsible sidebar. That is **office responsive**, not Field Web. Do not reuse the office shell as the Field product ([ADR-022](../adr/ADR-022-field-client-and-shared-api.md)).

---

## 4. Smallest useful V1 information architecture

Recommended primary navigation:

```text
TODAY · PROJECT · CAPTURE
```

**First screen after login:** **TODAY**.

Do not invent Schedule, Weather, Timesheets, Crew, MONITOR, profitability, or AI summary.

CAPTURE is the primary **action**, always reachable in one tap from Today when a Project is confirmed.

---

## 5. TODAY (smallest meaningful surface)

TODAY in V1 is **not** a calendar engine. It is the field home:

1. **Confirmed Project** (name + number) — or a prompt to select one
2. **CAPTURE** (primary)
3. **Needs retry** — local unsent captures (if any)
4. **Recent observations on the confirmed Project** — from `GET /api/v1/projects/<id>/field-events` (server truth)
5. **Switch Project**

Out of V1 Today:

- schedule / weather / timesheets / MONITOR / profitability / AI summary
- unsigned Change Order badges (reserved for a later Native Signing slice; see §19)
- org-wide observation inbox requiring a new API (client may fan-out later; not required for V1)

---

## 6. Project selection / context

Reuse:

- `GET /api/v1/projects`
- `GET /api/v1/projects/<id>`

Landed list is current-org projects ordered by `created_at` desc (`app/services/shared_api.py`). Fields: `id`, `name`, `project_number`, `status`, `client_id`, `client_name`. No org switcher. Membership-derived Organization only.

V1 rules:

| Concern | Recommendation |
|---------|----------------|
| Recent projects | Client-side recents (last confirmed Project ids) on the device. Server list is the authority for what may be captured. |
| Search | Not required until project count makes scrolling unusable. V1: scroll the existing list. |
| Active Project | **Client session concept** (confirmed Project id). Not a new server “active project” table. |
| Header | Always show confirmed Project name + number on Capture. |
| Wrong-project prevention | Capture is disabled until the user **confirms** the Project. Switching Project requires an explicit confirm if unsaved capture exists. |
| Organization switching | **Do not invent.** |

---

## 7. Capture — primary field action

```text
OPEN FIELD WEB
→ SELECT / CONFIRM PROJECT
→ TAP CAPTURE
→ SPEAK / TYPE / PHOTO
→ SAVE ORIGINAL
→ DONE
```

Preserve over forms. One Field Capture Event may contain **text + audio + image(s)** in one session. That is already FG-020 (`FieldCaptureEvent` + multiple `FieldCaptureOriginal` children). Do **not** invent another note entity.

Minimum required fields for a valid save: **confirmed Project** + **at least one Original** (text, audio, or image). No title. No cost codes. No occurred-at picker in V1 (see §29).

---

## 8. Voice-first (no transcription)

Voice recording is **core** Field V1. Transcription is **not**.

Smallest browser architecture:

1. Start recording (getUserMedia + MediaRecorder)
2. Obvious recording state (color, elapsed time, accessible name)
3. Stop
4. Playback before save
5. Discard / re-record before save
6. Upload Original `audio` via existing multipart `POST .../originals`
7. Server ACK → clear local hold

Published Safari / WebKit constraints (not a substitute for real-device UAT):

- MediaRecorder exists in Safari on iOS **14.5+** ([Can I use](https://caniuse.com/mdn-api_mediarecorder_mimetype); [WebKit MediaRecorder](https://webkit.org/blog/11353/mediarecorder-api/)).
- Historical WebKit Cocoa path: `audio/mp4` (AAC) / `video/mp4` (H.264) via `MediaRecorder.isTypeSupported` ([WebKit r267825](https://trac.webkit.org/changeset/267825/webkit)).
- Public reports: iOS **14.5–18.3** typically **audio/mp4 only**; Safari **18.4+** (2025) also reports `audio/webm;codecs=opus` on some devices. **Always** `MediaRecorder.isTypeSupported(...)` at runtime. Do not hard-code one MIME for all iPhones.
- `getUserMedia` requires a **secure context** (HTTPS or localhost) and a **user gesture** to start recording.
- Still **To be verified on a real device at implementation:** permission copy, lock-screen / background tab, maximum clip vs `BUILD_ORIGINAL_MAX_BYTES` (25 MB), and the exact blob MIME the device emits.

FG-020 already accepts audio including `audio/mp4` / `.m4a` / `.mp4` (`app/services/build_storage.py`). Prefer uploading Safari `audio/mp4` as-is. **Do not** transcode in the browser unless a later implementation recon proves Safari cannot produce an accepted type.

---

## 9. Camera-first

Smallest iPhone photo workflow:

- Take photo (`<input type="file" accept="image/*" capture="environment">` and/or `getUserMedia` — implementation recon chooses the reliable Safari path)
- Optionally pick an existing library photo
- Preview + remove before save
- Upload Original `image` as captured bytes
- Server generates HEIC/HEIF JPEG Compatible Rendition ([build-media-storage-lifecycle.md](build-media-storage-lifecycle.md))
- No user format picker. Contractor never sees HEIC vs JPEG.

Do **not** convert HEIC on the client unless later device testing proves upload is impossible without it. FG-020 already preserves HEIC Originals and builds the JPEG rendition.

---

## 10. Text

Available, not dominant.

- One short note field
- OS keyboard / iOS dictation is enough (that is not CalibAi AI)
- Optional alongside voice/photo
- No desktop long form

---

## 11. Multi-Original transaction pattern

**Recommendation: A — create Event first, then upload Originals individually.**

This matches landed API:

```text
POST /api/v1/projects/<id>/field-events     → Event
POST /api/v1/projects/<id>/field-events/<event_id>/originals  → each Original
```

Partial failure: Event + successfully ACK’d Originals remain valid evidence (original-first). Failed Originals stay in local NEEDS RETRY against **that** Event id. Do not roll back ACK’d Originals.

Do **not** require a single multipart “all originals in one request” (not in the landed API; not needed).

---

## 12. Poor connectivity / ACK (ADR-042 layer B)

V1 is **online-first**, not full offline sync. No native app. No enterprise sync engine.

User-visible states:

| State | Meaning |
|-------|---------|
| **SAVING** | Upload in flight |
| **SAVED** | Server ACK for that Event/Original |
| **NEEDS RETRY** | Local bytes retained; user can retry |

Mechanism: **IndexedDB** for binary Originals (photos/audio up to 25 MB). `localStorage` is not large enough. A service worker is **not** required for this hold.

When the Event has been ACK’d, retries upload remaining Originals to that Event. When the Event has **not** been ACK’d, retry must not create a second Event — see §13.

---

## 13. Idempotency — major finding

Inspected schema (`app/models/build.py`, revision `c1d2e3f4a5b6`):

- `field_capture_events` has **no** client UUID / idempotency key
- `field_capture_originals` has **no** client UUID / idempotency key
- FG-020 **allows duplicate SHA bytes as separate Original rows**

Therefore a naïve retry of `POST` Event or `POST` Original **will duplicate** commercial evidence.

**Item 12 requires server-side duplicate protection.** Not inventable as client-only hope.

Recommended (for a future Feature Gate / ADR — **not created here**):

1. Client-generated **capture UUID** (Event) and **original UUID**
2. Persist unique keys (org+key / event+key)
3. Replay of the same key returns the existing row (idempotent ACK)

This is:

| Layer | Implication |
|-------|-------------|
| API | Idempotency on Event create and Original create |
| Schema | Additive columns + unique constraints |
| Migration | **Yes**, in the Field Web Feature Gate if that gate owns the keys |
| ADR | **Yes**, before implementation — schema/idempotency policy is not fully locked by ADR-042 |
| Feature Gate | [FG-021](../feature-gates/FG-021-field-web-v1-today-and-capture.md) **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT OPEN** (historical recon: APPROVED / IMPLEMENTATION NOT STARTED) |

Do not silently add columns. Do not treat SHA-only matching as Event idempotency (two photos can share no SHA; two retries of empty Event have no SHA).

Existing historical-ingestion `idempotency_key` is a **different** module. Do not overload it.

---

## 14. Local data / privacy

Store **only** unsent capture payloads:

- confirmed `project_id`
- capture UUID
- Original kind + bytes (or text)
- created-local timestamp
- retry state

Delete each Original from IndexedDB **immediately after that Original’s server ACK**. Delete the capture session after all Originals ACK (or user discard).

| Topic | V1 rule |
|-------|---------|
| Duration | Until ACK or explicit discard. No local archive. |
| Logout | **Wipe** unsent IndexedDB for this origin (shared-device risk). Warn if NEEDS RETRY exists. |
| Shared iPhone | Same browser profile = same unsent queue. Fail closed: logout clears. |
| Quota | If IndexedDB is full/unavailable: refuse Capture with a visible error; do not pretend SAVED. |
| Sensitivity | Unsent photos/audio are project evidence on-device. Minimum retention. No cloud backup design in V1. |

---

## 15. Authentication

Reuse FG-018 cookie/session. `remember=False` today (`app/routes/auth.py`). No tokens. No native auth. No RBAC. No org switcher.

| Case | Behavior |
|------|----------|
| Already logged in | Open Field routes |
| Unauthenticated Field URL | Office login, then `safe_next_url` back to `/field/...` (already exists) |
| API 401 during upload | Pause as NEEDS RETRY; send user to login with `next`; resume retry after session restored |
| HTML Field page unauthenticated | 302 `/login` (office pattern), not JSON |

Field HTML must not weaken API 401 JSON for `/api/v1`.

---

## 16. CSRF

BUILD mutations require CSRF. Tests use header `X-CSRFToken` (`tests/test_build_field_observation_fg020.py`). Office templates expose `<meta name="csrf-token">`.

Field Web: same-origin pages include the meta tag; JS sends `X-CSRFToken` on every `POST`. Multipart Original uploads must include the token (header and/or form field). **No CSRF exemption.** If the token expires mid-capture: refresh from a GET of the Field page or a dedicated same-origin GET that returns the token in HTML/meta — do not invent a token API unless implementation recon proves it necessary.

---

## 17. Landed API inventory vs Field V1

| Endpoint | Methods | Field V1 |
|----------|---------|----------|
| `/api/v1/me` | GET | Yes (identity display) |
| `/api/v1/projects` | GET | Yes (select) |
| `/api/v1/projects/<id>` | GET | Yes (confirm header) |
| `/api/v1/projects/<id>/field-events` | GET, POST | Yes (list + create Event) |
| `.../field-events/<id>` | GET | Yes (optional confirmation of save) |
| `.../originals` | GET, POST | Yes (upload/list) |
| `.../originals/<id>` | GET | Yes |
| `.../originals/<id>/content` | GET | Yes (audio/image Original bytes) |
| `.../derived` | GET | **Not in Field V1 UI** |
| `.../derived/<id>/confirm\|reject` | POST | **Not in Field V1 UI** |
| `POST /api/v1/me` | — | Must remain **405** |
| `POST /api/v1/projects` | — | Must remain **405** |

**Missing for Field V1 (not speculative extras):**

1. **Idempotent Event/Original create** — required for retry (see §13). Schema + API.
2. **Compatible Rendition display over `/api/v1`** — office HTML has `GET .../originals/<id>/display`; the JSON API does **not**. Field Web cannot reuse office HTML display routes as its architecture path. Add a bounded GET display adapter in the Field Web gate (same `open_display_rendition` service). JPEG/PNG/GIF can use `/content`; HEIC needs display JPEG.

Do not add: org switch, tokens, Today-aggregation endpoint, Change Order signing, plan PDF JSON, unless a later slice authorizes them.

---

## 18. Derived Candidates in Field V1

**None.** Desktop already owns confirm/reject. Field’s job is capture. Lightweight field review is a **later** gate.

---

## 19. Change Order visibility

**Not in Item 12 V1.** Do not implement signing. Do not implement UNSIGNED / AWAITING SIGNATURE / SIGNED. Do not add a Field Change Order list.

Architecture reservation (not UI in FG-021): a later separately governed Native Signing / Commercial Execution slice may show those three **customer-authorization** labels on the job site. They are not a replacement for the existing office CO lifecycle. Do not invent placeholder badges that imply signing exists.

Existing office Change Order **read-only** access is **deferred** from Field V1. Capture is the V1 job. A later Field slice may add a read-only CO list after Native Signing is gated — not before.

---

## 20. Plan access

Roadmap item 12 is named “Today + Capture + plan access.” Plan Intelligence already owns PDFs. Do not duplicate storage.

**Smallest V1 boundary:** **defer plan viewing** to a later Field Web slice.

Reason: Field V1 succeeds if capture works. Opening office sheet/measure UI on a phone recreates the “shrunken desktop” failure ([ADR-022](../adr/ADR-022-field-client-and-shared-api.md)). A purpose-built plan viewer is real work (PDF.js, sheets, safe-area) and is not required to prove SAVE ORIGINAL.

Later slice (not this recon’s Feature Gate): Project plan list + open latest Drawing Package PDF in a Field-safe viewer, still reading Plan Intelligence records.

---

## 21. Media display (Field)

| Kind | Rule |
|------|------|
| JPEG / PNG / GIF | `/content` or display as-is |
| HEIC / HEIF | Server JPEG Compatible Rendition (API display once added). Original remains downloadable. |
| Audio | Browser `<audio>` when playable; else Original open/download. No waveform. No transcription. No client conversion. |

---

## 22. UI architecture recommendation

**A — separate Flask/Jinja Field route family + purpose-built CSS/JS.**

Not a React/Vue SPA (B) as the V1 default. Not a new front-end platform (C).

Reasons:

- Same Flask deployment
- Cookie session + CSRF meta tag already exist
- Capture JS calls `/api/v1` (no duplicated BUILD rules)
- Purpose-built templates avoid the office sidebar/shell
- Maintainable by the current stack

JS is required for MediaRecorder, file preview, IndexedDB retry, and save-state. That is a **page module**, not a second application.

Office users **may** open `/field` on desktop Safari/Firefox/Chrome for support/testing. Visual language stays Field (large capture), not office Hub. A small “Office Hub” link is enough to avoid trapping testers.

---

## 23. PWA

**Defer.** V1 is ordinary mobile web.

Home-screen install, standalone display, and service-worker offline shell are not required for IndexedDB retry-until-ACK. A PWA would add install prompts, cache invalidation, and Safari service-worker quirks without unlocking capture.

Revisit PWA only if real-device UAT shows that ordinary Safari cannot retain unsent Originals across a tab discard **and** a later gate accepts that complexity.

---

## 24. Routing

Recommended Field family (not implemented):

```text
/field                          → redirect to /field/today
/field/today
/field/projects                 → select
/field/projects/<id>            → confirm + recent list + Capture
/field/projects/<id>/capture
```

Desktop `/projects/<id>` Hub remains intact. Field routes must not replace Hub BUILD.

Login `next=/field/today` is already compatible with `safe_next_url`.

---

## 25. Accessibility / usability acceptance (objective, not pixel-perfect)

- Touch targets ≥ 44 CSS px; Capture larger
- Readable type and contrast outdoors
- Keyboard not required for the happy path
- SAVING / SAVED / NEEDS RETRY always visible
- Discard recording / delete photo: confirm
- Recording state obvious (visual + accessible name)
- Photo preview before save
- Retry state names the Project
- No horizontal office tables on Capture/Today
- Basic VoiceOver labels on Capture / Record / Save

---

## 26. Desktop continuity

Field-created Events **are** FG-020 Events. They appear immediately on:

```text
Project Hub → Field Observations → Event Detail
```

Same ids, Originals, actor snapshot, hashes. No sync job. No second model.

Item 12 must not regress office Hub, office text create, supersession, derived confirm/reject, or rendition display.

---

## 27. Actor provenance

Field Web **must not** send actor identity as authority.

Landed BUILD services stamp `user_id` + `actor_display_name` from the authenticated session (`app/services/build.py` `_actor_snapshot()`). Caller `organization_id` is ignored as authority (FG-020). Preserve that.

---

## 28. Timing

| Clock | V1 Field |
|-------|----------|
| `occurred_at` | Omit from UI. Server default **NOW** (already lawful when omitted). |
| `created_at` | Server only. |

No date/time form on the job site. Office remains the place to record delayed observations with explicit `occurred_at` if needed.

---

## 29. Failure cases

| Failure | Class | Expected product behavior |
|---------|--------|---------------------------|
| No network before save | Product | Do not claim SAVED. Hold locally → NEEDS RETRY |
| Drop during audio/image upload | Product | Event may already exist; retry that Original only |
| Partial multi-photo | Product | ACK’d photos stay; rest retry |
| Session expires | Product | 401 → login `next` → retry |
| CSRF expires | Product | Refresh token; retry; never disable CSRF |
| Project gone / 404 | Product | Fail closed; do not capture |
| MIME / size reject | Product | Keep local file; show server error; user discards or retries after fix |
| HEIC rendition fails, Original OK | Product (already FG-020) | Original valid; Field shows fallback + Original access |
| Duplicate retry | **Requires §13** | Same UUID → same row, not a second Event/Original |
| Browser close before ACK | Product | IndexedDB hold; Today shows NEEDS RETRY |
| Navigate away unsaved | Product | Confirm; retain if they leave mid-SAVING |
| IndexedDB full/unavailable | Product | Block Capture with explicit error |
| Camera/mic denied | Product | Explain; still allow the other modalities |
| Safari MediaRecorder unavailable | Implementation recon + product fallback to file-input / text |
| Over 25 MB | Product | Reject before/at server; do not truncate silently |

---

## 30. Device / UAT matrix

Keep it small.

| Device | Role |
|--------|------|
| Current iPhone Safari | **Required** real-device: mic, camera, HEIC, orientation, permissions, retain/retry, background/foreground |
| One older supported iPhone Safari | **Required** smoke of the same |
| Desktop Safari | Support/testing Field routes; not the job-site proof |
| Desktop Firefox or Chrome | CSRF/API regression; not a substitute for iPhone capture |

Automated pytest cannot replace real-device mic/camera/HEIC/retry. FG-021 must include a real-device UAT checklist.

---

## 31. Feature Gate shape

**Subsequent status (2026-09-01):** [FG-021](../feature-gates/FG-021-field-web-v1-today-and-capture.md) was **DRAFTED** as **DRAFT FOR JOEL REVIEW / NOT APPROVED**. [ADR-043](../adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md) was **Proposed**. Implementation remained **NOT AUTHORIZED**.

**Subsequent status (2026-09-02):** ADR-043 is **Accepted**. FG-021 is **APPROVED / IMPLEMENTATION NOT STARTED**. Implementation recon is **COMPLETE**. Product implementation remains **NOT AUTHORIZED** until a separate implementation prompt.

**Subsequent status (2026-09-04):** FG-021 **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT OPEN**. Gate **NOT CLOSED**. Live current = head `d2e3f4a5b6c7`.

| Question | Answer from repository indexes |
|----------|--------------------------------|
| Next Feature Gate id | **FG-021** — [FG-021-field-web-v1-today-and-capture.md](../feature-gates/FG-021-field-web-v1-today-and-capture.md) **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT OPEN**. Native Signing must **not** consume FG-021. |
| Proposed title | **Field Web V1 — Today + Capture** |
| New ADR required? | **Accepted.** [ADR-043](../adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md). ADR-042 remains the dual-surface / original-custody ADR. |
| Owner | Field Web is a **client**. BUILD remains owner of Events/Originals. Office/platform owns `/api/v1` adapters. |
| Scope | `/field` templates+JS; iPhone Safari Today/Project/Capture; voice/photo/text Originals via FG-020 API; IndexedDB retry; CSRF; idempotent Event/Original API + additive schema; API display rendition GET; desktop Hub continuity tests |
| Non-goals | Transcription; AI; PWA/service worker; native iOS; tokens; RBAC; org-switcher; Derived review UI; Change Order signing or UNSIGNED/AWAITING/SIGNED badges; MONITOR; Closeout; plan viewer; full offline sync; office shell reuse as Field; Native Signing production activation |
| Migration | Designed revision **`d2e3f4a5b6c7`**. **Applied live.** Gate still **NOT CLOSED**. |
| Implementation recon | **COMPLETE** — [fg-021-field-web-v1-implementation-reconnaissance.md](fg-021-field-web-v1-implementation-reconnaissance.md) |
| Tests | Dedicated Field Web + API idempotency + CSRF + isolation + Hub continuity; real-device UAT |

---

## 32. Item 12 smallest completion rule

Item 12 V1 is complete when:

```text
A contractor can, on iPhone Safari:
  sign in,
  confirm the correct Project,
  capture voice and/or photo and/or a short text note,
  see SAVING → SAVED (or NEEDS RETRY that actually retries without silent duplicates),
  and find that same Field Capture Event with the same Originals
  on the desktop Project Hub Field Observations / Event Detail.
```

That is the destination. FG-021 is **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT OPEN**. ADR-043 is **Accepted**. Remaining real-device UAT is still required to close.

---

## 33. Explicit non-goals of this recon

- Implementation, Feature Gate file, ADR file, migration
- Field Web UI, PWA, native iOS
- Transcription, voice AI, photo AI, runtime web lookup
- MONITOR, Closeout, Native Signing, Contract, Change Order signing
- Weakening CSRF or inventing tokens

---

## Related current code (do not change under this recon)

- [`app/routes/api_v1.py`](../../app/routes/api_v1.py)
- [`app/models/build.py`](../../app/models/build.py)
- [`app/services/build.py`](../../app/services/build.py)
- [`app/services/build_rendition.py`](../../app/services/build_rendition.py)
- [`app/routes/build.py`](../../app/routes/build.py)
- [`app/templates/build/`](../../app/templates/build/)
- [`app/static/css/app.css`](../../app/static/css/app.css)
- [`app/routes/auth.py`](../../app/routes/auth.py)

---

## Related

- [ADR-042](../adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) **Accepted**
- [ADR-043](../adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md) **Accepted**
- [ADR-022](../adr/ADR-022-field-client-and-shared-api.md) **Accepted**
- [FG-020](../feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) **CLOSED / OPERATIONAL FOR UAT**
- [FG-021](../feature-gates/FG-021-field-web-v1-today-and-capture.md) **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT OPEN**
- [fg-021-field-web-v1-implementation-reconnaissance.md](fg-021-field-web-v1-implementation-reconnaissance.md) **COMPLETE**; product **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT OPEN**
- [FG-019](../feature-gates/FG-019-shared-api-foundation-v1.md) **CLOSED / OPERATIONAL FOR UAT**
- [legal/native-signing-process-counsel-review.md](../legal/native-signing-process-counsel-review.md) — parallel track; counsel does **not** block Field Web

---

## 34. Native Signing dependency pin (Joel 2026-09-01)

Ontario counsel review of the proposed Native Signing **process** is **not** a general development hold. It does **not** block Item 12.

```text
NATIVE SIGNING DEVELOPMENT:
MAY PROCEED UNDER SEPARATE GOVERNANCE

NATIVE SIGNING PRODUCTION ACTIVATION / REAL CUSTOMER USE:
BLOCKED PENDING ONTARIO COUNSEL APPROVAL OF THE SIGNING PROCESS
```

Separately governed Native Signing architecture, Feature Gate drafting, implementation, testing, and **non-production** UAT may proceed when Joel authorizes that track.

Do **not** enable Native Signing for real customer / commercial use until counsel decisions are reconciled and approved.

The [Legal Content Gate](../governance/legal-content-and-templates.md) for Ontario Contract / Warranty **templates** remains in force and is **separate** from this signing-process counsel review.

This Item 12 reconnaissance does **not** implement Native Signing, create its Feature Gate, change counsel-review questions, or enable real customer signing.

---

## 35. Proposed acceptance criteria (FG-021 — **drafted / not approved**)

A future Field Web gate is acceptable only when all of the following are true. This recon does **not** authorize that gate.

1. On current iPhone Safari, an authenticated contractor can confirm a Project, Capture voice and/or photo and/or short text, and see **SAVING → SAVED** (or **NEEDS RETRY** that retries).
2. Server ACK creates a `FieldCaptureEvent` plus the intended `FieldCaptureOriginal` rows via `app/services/build.py` — same records the office Hub reads.
3. Retry of the same client capture UUID / original UUID returns the existing row and does **not** create a second Event or Original.
4. CSRF remains required (`X-CSRFToken`). No CSRF exemption. API 401 remains JSON for `/api/v1`; Field HTML 302 remains `/login` with `safe_next_url`.
5. The same Event and Originals appear on desktop `Project Hub → Field Observations → Event Detail` immediately. No second datastore. No sync job.
6. HEIC Originals remain Original Source; Field display uses Compatible Rendition over `/api/v1` once that GET exists. JPEG/PNG/GIF may use `/content`.
7. Logout wipes unsent IndexedDB. IndexedDB full/unavailable refuses Capture (does not claim SAVED).
8. Dedicated automated tests plus the real-device UAT checklist in §30 / §36 pass. Office Hub, office text create, supersession, derived confirm/reject, and FG-019 mutation lock do not regress.
9. Non-goals in §31 / §33 remain out of the gate (transcription, PWA, Native Signing production, plan viewer, Derived field review, CO signing badges).

---

## 36. Dedicated test plan (FG-021 — **drafted / not approved**)

Automated (pytest; office + API; no real-device substitute):

| Suite | Must prove |
|-------|------------|
| Field HTML routes | `/field` family login-required; `next` returns to Field; office Hub routes unchanged |
| Capture API | Event-then-Originals; multipart audio/image; text Original; CSRF required |
| Idempotency | Replay Event UUID / Original UUID → same ids; no duplicate evidence |
| Isolation | Cross-org 404; unauthenticated API 401 JSON; Field HTML 302 `/login` |
| Hub continuity | Field-created Event visible on office Field Observations / Event Detail |
| Rendition display API | HEIC uses display JPEG; Original `/content` unchanged |
| FG-019 lock | `POST /api/v1/me` and `POST /api/v1/projects` remain 405 |
| Regression | Existing FG-018 / FG-019 / FG-020 dedicated files still pass |

Real-device UAT (required; not replaceable by pytest):

| Device | Must prove |
|--------|------------|
| Current iPhone Safari | Mic, camera, HEIC, permissions, orientation, SAVING/SAVED/NEEDS RETRY, background/foreground retain |
| One older supported iPhone Safari | Same smoke |
| Desktop Safari | Field routes usable for support; not the job-site proof |
| Desktop Firefox or Chrome | CSRF/API regression only |

**To be verified on device at implementation:** exact MediaRecorder blob MIME, lock-screen/background tab, IndexedDB quota vs 25 MB, CSRF-token refresh mid-capture.

---

## 37. Unresolved Joel decisions

This recon recommends; it does **not** decide:

1. Whether to **Accept ADR-043** and **Approve FG-021** (Field Web V1). Drafted 2026-09-01; **not accepted/approved**. Implementation **NOT AUTHORIZED**.
2. Whether to authorize a **separate Native Signing development** track. Production activation / real customer use remains **blocked pending counsel** regardless.
3. Confirm V1 = Today + Project confirm + Capture; **plan access deferred** (recon recommendation).
4. Confirm technology **A** (Flask/Jinja Field family + page JS), not SPA, not PWA.
5. Confirm idempotency keys + unique constraints ship **inside FG-021** (recon recommendation) rather than a later schema gate.
6. Confirm Change Order field visibility remains **out of Item 12** (recon recommendation).

Counsel answers to [native-signing-process-counsel-review.md](../legal/native-signing-process-counsel-review.md) remain open and do **not** block these Joel decisions.

---

## 38. Conflicts / stale docs found during this completion pass

Replace leftover language that treated counsel as a **general development hold**. Do **not** rewrite historical closed-milestone text.

| Location | Issue | Disposition |
|----------|-------|-------------|
| Session handoff last-delta / §22 | “WAITING FOR COUNSEL”; “Field Web BLOCKED”; Item 12 “ELIGIBLE”; step 4 wait-only | Corrected this pass |
| `current-state.md` duplicate recommended-next 3–7 | Accidental leftover copy | Corrected this pass |
| Roadmap CURRENT vs “Next recommended milestones” | Stale “do not mark FG-020 closed” / “Item 12 BLOCKED” | Corrected this pass |
| Indexes saying Native Signing “implementation NOT AUTHORIZED” as a **blanket** | Stale vs Joel pin | Corrected this pass |
| FG-020 close row in [milestones.md](../milestones.md) | “Native Signing waiting for counsel” | **Left** — historical close record; this pass **appended** |
| [FG-020](../feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) commercial-execution close note | Historical close wording | **Left** — do not rewrite closed-gate history |
| [CAR-001](CAR-001-calibai-product-architecture-reconciliation.md) subsequent-status boxes | Historical “Field Web BLOCKED” at earlier FG-020 states | **Left** — dated subsequent status |

---

## 39. Recommended next governed action

```text
STOP. Do not implement product code from this architecture pin.

ADR-043 is Accepted. FG-021 is IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT OPEN.
Gate NOT CLOSED.

Joel/ChatGPT reviews remaining FG-021 real-iPhone closure UAT versus
separately governed reusable-template extraction. Do not choose here.
Do not close FG-021. Do not implement Observation Delete.
Native Signing DEVELOPMENT MAY PROCEED UNDER SEPARATE GOVERNANCE.
Native Signing PRODUCTION ACTIVATION / REAL CUSTOMER USE
remains BLOCKED PENDING ONTARIO COUNSEL APPROVAL OF THE SIGNING PROCESS.

Do not implement Project Closeout.
Do not weaken the Legal Content Gate for Ontario Contract / Warranty templates.
Do not assign FG-021 to Native Signing.
```

**ROADMAP SEQUENCE ≠ IMPLEMENTATION AUTHORIZATION.** Item 12 is **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT OPEN**. That does **not** close FG-021 or authorize MONITOR, Closeout, or template extraction.
