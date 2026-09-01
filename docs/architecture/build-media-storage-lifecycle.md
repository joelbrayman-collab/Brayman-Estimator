# Architecture pin — BUILD media compatibility and project-close storage lifecycle

| Attribute | Value |
|-----------|--------|
| Status | **Architecture pin.** Original Source custody exists under [FG-020](../feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) **CLOSED / OPERATIONAL FOR UAT**. Image-only Compatible Renditions (HEIC/HEIF → JPEG) **IMPLEMENTED**. Project Closeout / archive-and-purge **FUTURE / NOT IMPLEMENTED**. |
| Date | 2026-08-31 |
| Product | The Estimator / CalibAi |
| Canonical record | This document |
| Related | [ADR-042](../adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) **Accepted** · [FG-020](../feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) · [modules/build.md](../modules/build.md) · [ADR-023](../adr/ADR-023-field-evidence-provenance.md) **Accepted** |

This is a **storage-lifecycle and user-experience** pin. It does **not** change commercial policy. It does **not** implement Project Closeout. It does **not** start Field Web.

**Implemented (2026-08-31 increment; 2026-09-01 live-migrated):** local HEIC/HEIF → JPEG Compatible Renditions via `app/services/build_rendition.py`. Original Source bytes remain immutable. No new Alembic revision. Live current = head `c1d2e3f4a5b6`.

Do **not** frame ordinary construction photos primarily as legal evidence. Source preservation exists for quality, integrity, reversibility, compatibility, future processing, and reliable project records.

---

## Terminology

| Concept | Meaning |
|---------|---------|
| **Original Source / Original Capture** | The preserved original bytes (for example iPhone HEIC). Immutable. Canonical project source media. |
| **Compatible Rendition** | A regenerable presentation/cache artifact (for example JPEG preview). Not the Original Source. Not a business Derived Candidate. Not a permanent archive record. |
| **Active Project Storage** | Working storage while a Project is in active use. May hold Original Source **and** Compatible Rendition(s) plus metadata / provenance / SHA. |
| **Closed Project Archive** | Durable long-term location for closed-project material after a separately governed Project Closeout. |

---

## Active-project storage

While a Project is **ACTIVE**, CalibAi may retain:

1. Original Source
2. Compatible Rendition(s)
3. Metadata / provenance / SHA

Example: iPhone HEIC + automatic JPEG rendition.

This is appropriate because the Project is in use and desktop/Field interfaces need fast access. CalibAi should make uploaded media **automatically usable** without forcing the contractor to understand HEIC/JPEG/browser compatibility.

---

## Compatible Renditions are regenerable

JPEG previews, thumbnails, resized images, and other compatible display renditions are **not** permanent canonical project records.

Treat them as:

```text
REGENERABLE PRESENTATION / CACHE ARTIFACTS
```

They may be deleted and recreated from the Original Source.

Do **not** design permanent archive retention around keeping every rendition.

Do **not** confuse a Compatible Rendition with:

- a business **Derived Candidate**
- the **Original Source**
- a **permanent archive record**

---

## Media Compatibility / Rendition service

FG-020 now includes a reusable local:

```text
MEDIA COMPATIBILITY / RENDITION SERVICE
```

Code: `app/services/build_rendition.py`. Config: `BUILD_RENDITION_ROOT` (default `instance/build_renditions/`; tests use an isolated temp directory).

For HEIC/HEIF photographic Original Sources:

```text
Original Source (immutable HEIC/HEIF)
→ Compatible Rendition (JPEG display.jpg)
```

JPEG / PNG / GIF Originals remain browser-native; no rendition is created. Audio is unchanged (preserve Original; native playback where supported; authorized download otherwise). **Image-only increment.** No ffmpeg. No audio transcoding. No AI. No cloud conversion.

### Conversion mechanism (verified locally)

| Item | Value |
|------|--------|
| Libraries | `Pillow>=10.1.0` (venv **11.3.0**) and `pillow-heif>=0.18.0,<1` (venv **0.22.0**) in `requirements.txt` |
| Scope | BUILD media compatibility only. FG-017 Brand Profile still does **not** process logos with Pillow. |
| JPEG quality | **85** — visually faithful for desktop Event Detail without a second near-lossless photo |
| Max long edge | **2048 px** (LANCZOS; no upscale) — typical desktop/full-width review without keeping a 12MP working copy |
| Orientation | `ImageOps.exif_transpose` applied; EXIF is **not** copied into the JPEG after orientation |
| Filename | `display.jpg` |
| Sequence | Original Source is stored and SHA-governed **first**. Rendition generation is attempted afterward. Failure logs and continues; Original is never rolled back. |
| Regeneration | `ensure_compatible_rendition(original)` reuses a valid existing JPEG or regenerates from Original Source. Never mutates Original. |
| Schema | **None.** Presence is discovered from the deterministic path. No new Alembic revision. |

### Rendition storage path

```text
instance/build_renditions/<organization_id>/<project_id>/<event_id>/<original_id>/display.jpg
```

Physically separate from Original Source (`instance/build_originals/...`). Path-traversal protected. Safe overwrite of the **rendition only**. Org / project / event / original scoped. No public bucket. No filesystem path exposed to the UI.

The rendition is a working/display artifact. It must **never** replace or mutate Original Source bytes.

Authorized desktop route: `GET /projects/<id>/field-events/<event_id>/originals/<original_id>/display` (JPEG). Original download remains `.../originals/<original_id>?download=1`. Same authorization chain as Original Source. Cross-org / missing: **404**. Unauthenticated: login redirect.

---

## Project-close archive principle

When a Project is formally **CLOSED** under a future separately governed **Project Closeout** capability:

CalibAi should create or confirm a durable **Project Archive** containing the required project records and source media.

The Project Archive should become the durable long-term location for closed project material.

**Do not design FG-020 as Project Closeout.** FG-020 (and later media-compatibility work) must merely preserve a clean future path to this lifecycle. Architecture must **not** prevent future archive-and-purge.

---

## Original media in the Project Archive

The Project Archive should preserve the **Original Source** file where practical (for example HEIC original, rather than only its generated JPEG rendition).

Reason:

- preserves maximum source quality
- avoids irreversible conversion
- allows future regeneration
- avoids duplicate permanent copies

If a Project Archive also contains rendered project documents/PDFs, that does **not** automatically mean embedded/compressed photos replace Original Source media.

**Do not decide the final closed-Project archive format here.** Future Project Closeout governance must evaluate a structured archive containing project documents, source media, metadata/manifest, and checksums/references. Do **not** assume a PDF containing compressed images is sufficient preservation of source photos.

---

## Verified archive before purge

Do **not** delete an active-storage Original merely because a Project status changes to Closed.

Cleanup must require verification. Future closeout architecture should require, at minimum:

1. Project Archive successfully created
2. required Original Sources copied/contained
3. archived source identity verified
4. checksum/SHA verified where applicable
5. archive location/reference committed
6. cleanup then permitted

If archive verification fails: **retain the active source**. Fail safe.

---

## Post-close cleanup order

After Project Archive verification:

1. **First:** delete/purge regenerable Compatible Renditions from working storage.
2. **Then,** where the Original Source has been safely archived and verified: remove the duplicate active-storage Original Source.

Retain only the minimum operational metadata/reference needed for the closed Project.

Do **not** retain duplicate binary files indefinitely without a governed reason.

---

## Closed-project access

A closed Project should remain understandable and retrievable.

The application may retain lightweight metadata/index references allowing a user to know:

- what source files existed
- which Project/Event they belonged to
- archive location/reference
- source MIME/type
- SHA/checksum where governed

Do **not** require duplicate active binary storage merely for listing history.

---

## Reopen / rehydration

Future architecture should permit a closed Project or archived Original to be reopened/rehydrated if necessary.

If a browser-compatible rendition has been purged:

```text
retrieve archived Original Source → regenerate temporary/working Compatible Rendition
```

Renditions are regenerable. Do **not** make the presence of an old rendition a permanent archive dependency.

---

## HEIC example

**ACTIVE**

- Original: `photo.heic`
- Automatic compatible rendition: `photo.jpg`
- Desktop uses `photo.jpg` transparently

**PROJECT CLOSES — ARCHIVE**

- Retain: `photo.heic` and required project metadata/index

**AFTER ARCHIVE VERIFICATION**

- Delete active duplicate: `photo.heic`
- Delete regenerable: `photo.jpg`

**IF LATER BROWSER DISPLAY IS NEEDED**

- Retrieve archived `photo.heic` → regenerate temporary/working `photo.jpg`

---

## Storage objective

Optimize for:

```text
USER FRIENDLINESS DURING ACTIVE WORK
+
ONE DURABLE PROJECT ARCHIVE AFTER CLOSE
```

not:

```text
PERMANENT DUPLICATION OF EVERY SOURCE AND RENDITION
```

Storage growth is a lifecycle concern.

---

## FG-020 boundary

FG-020 remains responsible for:

- active-project Original Source custody
- automatic compatible rendition capability (HEIC/HEIF → JPEG **implemented** in this increment)
- metadata / SHA / provenance
- authorized access
- clean Original Source / Compatible Rendition separation

FG-020 does **not** implement:

- Project Closeout
- final archive package generation
- automatic post-close purge
- archival storage tiering
- retention schedules
- audio conversion
- Field Web
- multiple rendition sizes

Those remain later separately governed capabilities.

Landed FG-020 product (2026-08-31) implements Original Source custody **and** image-only Compatible JPEG Renditions. Closeout remains unimplemented. Live migration of `c1d2e3f4a5b6` remains pending.

---

## Explicit non-goals of this pin

- Field Web
- Project Closeout implementation
- New Alembic revision
- Changing ADR-042 from **Accepted**
- Rewinding FG-020 to **IMPLEMENTATION NOT STARTED**
- Treating a Compatible Rendition as a Derived Candidate
- Audio conversion / ffmpeg / transcription
- Accepting ADR-008 or ADR-010
