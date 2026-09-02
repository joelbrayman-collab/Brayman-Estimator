# FG-021 Field Web V1 — Implementation reconnaissance

| Attribute | Value |
|-----------|--------|
| Status | **COMPLETE / NOT IMPLEMENTED.** [ADR-043](../adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md) **Accepted**. [FG-021](../feature-gates/FG-021-field-web-v1-today-and-capture.md) **APPROVED / IMPLEMENTATION NOT STARTED**. |
| Date | 2026-09-02 |
| Product | The Estimator / CalibAi |
| Canonical record | This document |
| Related | [field-web-today-and-capture.md](field-web-today-and-capture.md) · [ADR-043](../adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md) · [FG-021](../feature-gates/FG-021-field-web-v1-today-and-capture.md) · [FG-020](../feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) · [build-media-storage-lifecycle.md](build-media-storage-lifecycle.md) |

This reconnaissance freezes implementation design for FG-021. It does **not** authorize product code, a migration, or `flask db upgrade`.

Readiness: **READY FOR BOUNDED IMPLEMENTATION** after a separate Joel/ChatGPT implementation prompt.

---

## Landed inventory (do not change here)

| Area | Path |
|------|------|
| App factory / CSRF / session gate | `app/__init__.py` (`CSRFProtect`; `login_manager.login_view = "auth.login"`; API unauthenticated **401 JSON**; HTML **302** `/login`; mutating `/api/v1` 405 except FG-020 BUILD POST allow-list) |
| Login / `safe_next_url` | `app/routes/auth.py` — relative same-host paths only; login form copies `next` |
| Shared API | `app/routes/api_v1.py`, `app/services/shared_api.py` |
| BUILD API | `POST .../field-events` and `POST .../originals` already **201** on first create |
| Models | `app/models/build.py` — no client UUID columns |
| Services | `app/services/build.py` — `create_field_event`, `add_text_original`, `add_binary_original`; actor from session |
| Storage / MIME / 25 MB | `app/services/build_storage.py` — audio includes `audio/mp4`, `.m4a`, `.webm`; images JPEG/PNG/GIF/HEIC/HEIF |
| Rendition | `app/services/build_rendition.py` `open_display_rendition`; office HTML `GET .../originals/<id>/display` in `app/routes/build.py` |
| Hub | `app/services/project_hub.py`, `app/templates/projects/` |
| Office CSS / JS | `app/static/css/app.css`, `app/static/js/shell.js` (injects `csrf_token` from meta) |
| Tests | `tests/test_auth_fg018.py`, `tests/test_shared_api_fg019.py`, `tests/test_build_field_observation_fg020.py`, `tests/test_build_media_compatibility_fg020.py`, `tests/test_project_hub.py` |

No `app/routes/field.py`. No Field templates. JS organization is office-only (`shell.js`, `sheet-measurement.js`).

---

## Event UUID schema (do not create)

Table: `field_capture_events`

| Item | Decision |
|------|----------|
| Column | `client_capture_uuid` |
| Type | `sa.String(36)` / `db.String(36)` |
| Nullable | **Yes** (office-created rows omit it) |
| Default | none |
| Backfill | **None** |
| Unique | `UNIQUE (organization_id, client_capture_uuid)` name `uq_field_capture_events_org_client_capture_uuid` |
| Extra index | none beyond the unique constraint |
| NULL behavior | SQLite UNIQUE treats distinct NULLs as allowed. Multiple office rows with `client_capture_uuid IS NULL` remain lawful. Do **not** invent a partial unique index unless implementation proves SQLite uniqueness of NULLs is wrong (it is not). |

`client_capture_uuid` is **not** organization, project, or actor authority.

---

## Original UUID schema (do not create)

Table: `field_capture_originals`

Originals have `field_event_id`, not `organization_id`. Do **not** add a denormalized org column for V1.

| Item | Decision |
|------|----------|
| Column | `client_original_uuid` |
| Type | `sa.String(36)` / `db.String(36)` |
| Nullable | **Yes** |
| Unique | `UNIQUE (field_event_id, client_original_uuid)` name `uq_field_capture_originals_event_client_original_uuid` |
| Why not org-scoped | Replay is defined as same UUID **to the same Event**. Event is already org+project bound. Adding `organization_id` on originals is extra schema without V1 need. |

Same SHA + **different** `client_original_uuid` remains a **new** Original (FG-020).

---

## UUID contract

Canonical **UUID v4** string, 36 characters, lowercase, hyphenated:

```text
xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

| Rule | Decision |
|------|----------|
| Client generate | `crypto.randomUUID()` (v4) before first POST |
| Server parse | `uuid.UUID(value)` then require `.version == 4` |
| Normalize | strip; lowercase; store hyphenated form (`str(parsed)`) |
| Reject | missing hyphens, URN `urn:uuid:`, braces, uppercase-only accepted only after normalize; invalid → **400** `BuildServiceError` |
| Max length | 36 |
| Office | omit field; server stores NULL; **201** as today |
| Field | **must** send UUID on Event and each Original |
| Authority | UUID never overrides membership org, URL/project, or session actor |

---

## Idempotent Event POST

`POST /api/v1/projects/<id>/field-events`

Body may include `client_capture_uuid`. Existing `occurred_at` / `supersedes_id` / optional `text` remain.

| Case | Status | Body |
|------|--------|------|
| First create with UUID | **201** | `serialize_event_detail` (add `client_capture_uuid` to serializer) |
| Replay same org + UUID | **200** | same Event detail |
| Omit UUID (office) | **201** | new Event (today) |
| Invalid UUID | **400** | |
| UUID exists, `project_id` ≠ URL project | **409** | no mutation |
| UUID exists, `supersedes_id` provided and differs | **409** | |
| UUID exists, `occurred_at` provided and parsed value ≠ stored | **409** | Field V1 **omits** `occurred_at`; omit ⇒ no occurred_at conflict |
| IntegrityError on unique | look up existing; if project matches treat as replay **200**; else **409** |

Do not silent-update `occurred_at`, project, or actor on replay.

---

## Idempotent Original POST

`POST /api/v1/projects/<id>/field-events/<event_id>/originals`

`client_original_uuid` via JSON (text) or multipart form field.

| Case | Status |
|------|--------|
| First create | **201** |
| Replay same Event + UUID, same payload | **200** |
| Omit UUID (office) | **201** new Original |
| Invalid UUID | **400** |
| UUID exists, different `kind` | **409** |
| Binary: UUID exists, `sha256_hex` differs | **409** |
| Text: UUID exists, `text_body` differs | **409** |
| Binary: UUID exists, `mime_type` differs | **409** |
| Filename differs, SHA/kind/MIME match | **200** replay (browser blob names may change) |
| Same UUID on a **different** Event | new row if that Event has no such UUID; do not overwrite the first Event’s Original |

Do **not** overwrite bytes, kind, or text.

---

## Central retry sequence

1. Client creates `client_capture_uuid`; writes IndexedDB **before** network.
2. POST Event with that UUID.
3. Store `server_event_id` from 201/200.
4. For each Original: create `client_original_uuid`; POST; on ACK delete that local Original.
5. Failed Original stays **NEEDS RETRY** with same UUIDs.
6. Lost Event response: retry **same** `client_capture_uuid` → **same** Event. No duplicate.

---

## IndexedDB

Database name: `calibai-field-v1`. Version 1.

**Store `pending_captures`** key `client_capture_uuid`:

- `client_capture_uuid`
- `project_id`
- `capture_started_at` (ISO local)
- `server_event_id` (nullable)
- `state` (`draft_local` | `saving` | `needs_retry`)
- `text` (nullable string; also mirrored as a pending original of kind text)

**Store `pending_originals`** key `client_original_uuid`:

- `client_original_uuid`
- `client_capture_uuid`
- `kind` (`text` | `audio` | `image`)
- `blob` (Blob/File; omit for text)
- `text_body` (text kind only)
- `filename`
- `mime`
- `state` (`pending` | `saving` | `needs_retry`)

Do **not** store passwords, session cookies, CSRF secrets, org ids as authority, or a project catalogue.

Last-confirmed `project_id` may live in `sessionStorage` (session) plus a single `localStorage` key `calibai-field-last-project-id` as a **hint**, not an archive.

---

## Cleanup

| Event | Action |
|-------|--------|
| Original ACK | delete that `pending_originals` row (binary gone) |
| All Originals ACK | delete `pending_captures` row; show **SAVED** |
| Original fail | keep row `needs_retry` |
| Logout | if any pending: confirm, then wipe both stores, then POST `/logout` |
| IndexedDB unavailable/full | block Capture; copy: cannot safely keep this capture on this phone; try photo/text later or free storage. Do **not** show SAVED |

---

## Safari lifecycle

| Situation | V1 guarantee |
|-----------|----------------|
| IndexedDB while Safari not private | Persist across tab close / reopen **when Safari allows it** |
| Active upload | May abort when backgrounded |
| Background tab / screen lock | **No** background-upload promise |
| Browser killed | Recover pending on **next open** of Field |
| Private/ITP wipe | User may lose pending; Today empty of retry; do not claim otherwise |

V1 is **reopen/retry**, not background sync.

---

## Voice

```text
getUserMedia({ audio: true }) → MediaRecorder → stop → <audio> playback → discard/re-record → upload
```

`isTypeSupported` preference (first supported):

1. `audio/mp4`
2. `audio/mp4;codecs=mp4a.40.2`
3. `audio/aac`
4. `audio/webm;codecs=opus` (FG-020 already accepts `audio/webm`)

No transcode, ffmpeg, waveform, ASR.

**Fallback if MediaRecorder/getUserMedia missing or mic denied:** disable Record; keep Take Photo / Choose Photo / short text. Visible explanation. Not a blocker for the other modalities.

---

## Camera

Two obvious controls (not a custom camera engine):

1. **Take Photo** — `<input type="file" accept="image/*" capture="environment">`
2. **Choose Photo** — `<input type="file" accept="image/*" multiple>`

Multiple photos: append to a local list; remove before save. No client HEIC conversion.

---

## Text

One `<textarea>` (short, ~4 rows, no rich editor). Optional. Posted as Original `kind=text` via existing API.

---

## Multi-Original (V1 UI vs server)

Server: Event may have many Originals of any kind (FG-020).

V1 UI:

- 0 or 1 text
- 0 or 1 audio clip
- 0 to N photos
- **at least one** Original to Save

Do not add a second audio recorder in V1 UI. Do not cap photos in the API.

---

## Routes

```text
/field                         → 302 /field/today
/field/today
/field/projects                select / switch
/field/projects/<id>           confirm + recent + Capture
/field/projects/<id>/capture
```

Blueprint `field_bp` in `app/routes/field.py`. No office sidebar. Same FG-018 login.

---

## Templates / static

**NEW:**

- `app/routes/field.py`
- `app/templates/field/base.html` — viewport-fit=cover, csrf meta, no `app-shell`
- `app/templates/field/today.html`
- `app/templates/field/projects.html`
- `app/templates/field/capture.html`
- `app/static/css/field.css`
- `app/static/js/field.js` (one module: MediaRecorder, inputs, IndexedDB, save/retry)

May reuse brand logo and IBM Plex via Field base. Must **not** include `partials/sidebar.html` or `shell.js` navigation.

**CHANGED:** `app/__init__.py` register `field_bp` only.

---

## Today / Project

Current Project: `sessionStorage` `calibai-field-project-id` after explicit confirm. Hint from `localStorage` last-project-id; still require confirm if not this session.

Capture disabled until confirmed. Capture URL without confirm → redirect to project confirm.

Recent: `GET /api/v1/projects/<id>/field-events` (existing order).

Needs Retry: IndexedDB `needs_retry` / leftover `saving`.

---

## Project switch vs pending

Pending capture is **bound** to its `project_id`. Switching Project does **not** rewrite that id.

If user opens Capture on Project B while pending exists for Project A: do not start a second capture; prompt Finish retry / Discard A’s pending, or go to A. Silent reassignment is forbidden.

---

## Client state machine

| State | User-visible |
|-------|----------------|
| `draft_local` | Internal while composing; composer is the UI (no “DRAFT” badge required) |
| `saving` | **SAVING** |
| `needs_retry` | **NEEDS RETRY** + Retry |
| `saved` | **SAVED** only after Event ACK **and** every intended Original ACK |

Today shows retry count from IndexedDB. No false SAVED.

---

## Auth / CSRF

Unauthenticated `/field/...` → Flask-Login 302 `/login?next=/field/...` (`safe_next_url` already allows `/field`).

API 401 during upload → keep IndexedDB → NEEDS RETRY → login with `next` back to Field → replay same UUIDs.

Field `base.html`: `<meta name="csrf-token">`. JS: `X-CSRFToken` on every POST (JSON and multipart). **No exemption.**

Expired CSRF (400): `GET` current Field page, read new meta token, replay same idempotent POST. Do not add a token JSON API unless implementation recon-on-device proves GET-HTML is unusable.

Logout: Field JS intercepts; wipe IndexedDB after confirm; POST `/logout` with CSRF.

---

## Display rendition API

**NEW GET** (not a mutating allow-list change):

```text
GET /api/v1/projects/<project_id>/field-events/<event_id>/originals/<original_id>/display
```

Reuse `open_display_rendition`. Image-only (404 otherwise), same as office.

**Client contract:** Field **always** uses `/display` for image preview. Server:

- JPEG/PNG/GIF → original bytes, original MIME (or JPEG if that is what `open_display_rendition` already returns for displayable types — follow `ensure_compatible_rendition`: displayable types skip conversion)
- HEIC/HEIF → JPEG rendition, `image/jpeg`

Audio/text: `/content` or JSON `text_body`. Cross-org 404. No filesystem paths.

---

## Field media on Today

Not a gallery. Per recent Event: actor/`occurred_at`; text excerpt (truncate); one photo via `/display` if any image; audio indicator if any audio. Capture remains the primary action.

---

## CSS / a11y / PWA

`field.css` only. `viewport-fit=cover`; `env(safe-area-inset-*)`; ≥44px targets; larger Capture; portrait-first; high contrast; no hover-only; no tables; thumb-zone primary actions.

Semantics, VoiceOver names (Capture, Record, Stop, Save, Retry), `aria-live` for SAVING/SAVED/NEEDS RETRY, visible focus, status not color-only.

**PWA: no.** Ordinary mobile web + IndexedDB is sufficient. No service worker, no manifest. If device UAT proves IndexedDB cannot retain Blobs across Safari close, **return to Joel** before adding a PWA.

---

## Migration (do not create)

One additive revision after `c1d2e3f4a5b6`.

| Item | Value |
|------|--------|
| Revision id | **`d2e3f4a5b6c7`** |
| down_revision | `c1d2e3f4a5b6` |
| Filename (when authorized) | `migrations/versions/d2e3f4a5b6c7_add_field_capture_client_uuids_fg021.py` |
| Upgrade | add `client_capture_uuid` String(36) nullable on `field_capture_events`; unique `(organization_id, client_capture_uuid)`; add `client_original_uuid` String(36) nullable on `field_capture_originals`; unique `(field_event_id, client_original_uuid)` |
| Downgrade | drop those two unique constraints and two columns |
| Backfill | none |
| New tables | none |

---

## Implementation files

**NEW**

- `app/routes/field.py`
- `app/templates/field/base.html`
- `app/templates/field/today.html`
- `app/templates/field/projects.html`
- `app/templates/field/capture.html`
- `app/static/css/field.css`
- `app/static/js/field.js`
- `migrations/versions/d2e3f4a5b6c7_add_field_capture_client_uuids_fg021.py` (implementation prompt only)
- `tests/test_field_web_fg021.py`

**CHANGED**

- `app/models/build.py`
- `app/services/build.py` (create/replay, serialize UUID fields)
- `app/routes/api_v1.py` (UUID in/out; display GET)
- `app/__init__.py` (`register_blueprint(field_bp)` only; POST allow-list unchanged if Field uses existing POST paths)
- docs as required by that implementation prompt

Office `app/routes/build.py` / Hub templates: **no functional change** unless serializer fields appear in office JSON unused by HTML.

---

## Automated tests

New `tests/test_field_web_fg021.py` (pytest, Flask test client — same style as FG-018/019/020):

- Field HTML 302 `/login` + `next=/field/today`
- Today / project confirm / capture-without-project redirect
- Event UUID create **201** / replay **200** / conflict **409**
- Original UUID create **201** / replay **200** / conflict **409**
- same SHA different UUID → two Originals
- office omit UUID still **201**
- API 401 JSON; cross-org 404
- CSRF required; replay after fresh token
- GET `/display` HEIC → JPEG; JPEG original
- `POST /api/v1/me` and `POST /api/v1/projects` remain 405
- FG-020 office create/detail/Hub still pass (run existing dedicated files)

**JS:** no new frontend framework. Optional tiny Node-less checks are **not** required. IndexedDB/MediaRecorder are **real-iPhone** tests.

---

## Real iPhone checks

Current iPhone Safari **required** during implementation smoke and FG-021 close UAT: mic permission, MediaRecorder MIME, playback, re-record, audio upload, camera, picker, HEIC, multiple photos, orientation, IndexedDB Blob persist, close/reopen, background/foreground (upload may fail — retry must work), quota, permission denial, session expiry, CSRF refresh, network drop, duplicate replay, one-handed, outdoor readability.

One older supported iPhone Safari smoke. Desktop emulation is **not** closure.

---

## Failure matrix

| Failure | Class | Handling |
|---------|--------|----------|
| Event POST response lost | **V1 MUST HANDLE** | Retry same capture UUID → 200 same Event |
| Original POST response lost | **V1 MUST HANDLE** | Retry same original UUID → 200 |
| Same UUID, different content | **V1 MUST HANDLE** | 409; keep local; do not overwrite server |
| IndexedDB write failure | **V1 MUST HANDLE** | Block Capture; no SAVED |
| IndexedDB quota exceeded | **V1 MUST HANDLE** | Block Capture; explicit error |
| No network | **V1 MUST HANDLE** | NEEDS RETRY; hold blobs |
| Drop mid-upload | **V1 MUST HANDLE** | NEEDS RETRY that Original |
| Microphone denied | **SAFE FALLBACK** | Record disabled; photo/text remain |
| Camera denied / no file | **SAFE FALLBACK** | That control fails; others remain |
| MediaRecorder unavailable | **SAFE FALLBACK** | Voice disabled; photo/text remain |
| Oversize / bad MIME | **V1 MUST HANDLE** | Keep local; show server/client error; no truncate |
| Session expired | **V1 MUST HANDLE** | IndexedDB stays; login next; replay |
| CSRF expired | **V1 MUST HANDLE** | Refresh meta; replay |
| Project inaccessible | **V1 MUST HANDLE** | Fail closed; 404; do not capture |
| HEIC rendition fails, Original OK | **SAFE FALLBACK** | Original valid; preview fallback (FG-020) |
| Project switch while pending | **V1 MUST HANDLE** | Bound to original project; no silent reassign |
| Logout with pending | **V1 MUST HANDLE** | Warn; wipe |
| Browser closed before ACK | **V1 MUST HANDLE** | Reopen Today NEEDS RETRY |
| Background upload | **DEFERRED** | No promise; retry on foreground |
| PWA / service worker | **DEFERRED** | Out of V1 |

---

## Native Signing pin

```text
NATIVE SIGNING DEVELOPMENT:
MAY PROCEED UNDER SEPARATE GOVERNANCE

NATIVE SIGNING PRODUCTION ACTIVATION / REAL CUSTOMER USE:
BLOCKED PENDING ONTARIO COUNSEL PROCESS APPROVAL
```

Counsel is not a Field Web hold. Legal Content Gate unchanged.

---

## Unresolved Joel decisions

None that block bounded implementation, provided the implementation prompt accepts this recon.

Open (non-blocking): whether login page copy should say “CalibAi” vs “Office sign in” for Field `next` (out of FG-021 unless Joel asks). Safari 18.4+ `audio/webm` is already an allowed fallback in FG-020.

---

## Conflicts

FG-020 close text still says Item 12 “ELIGIBLE / NOT AUTHORIZED” in places — **historical**. Current indexes must say FG-021 **APPROVED / IMPLEMENTATION NOT STARTED**.

Login lede “Office sign in” is slightly Field-awkward; do **not** redesign login in FG-021.

---

## Next governed action

```text
STOP product implementation in this pass.

Joel/ChatGPT may next issue a separate FG-021 IMPLEMENTATION prompt
that authorizes: migration d2e3f4a5b6c7, Field routes/templates/JS/CSS,
idempotent BUILD API, display GET, dedicated tests.
Do not implement until that prompt.
Do not implement Closeout or Native Signing production.
```
