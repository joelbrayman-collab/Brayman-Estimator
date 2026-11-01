# AiRIA RDIMS → Calibrayt document records: reuse map

| Attribute | Value |
|-----------|-------|
| Status | Reference / planning. Nothing implemented. |
| Date | 2026-10-31 |
| Reference implementation | AiRIA `origin/main`, read-only copy at `/home/claude/airia-ref` ("AiRIAdocs" Records, V2) |
| Target | Calibrayt `/home/claude/tf`, live baseline `7087d0d0` (Alembic head `s6f7a8b9c0d1`) |
| Companion | [calibrayt-rdims-architecture-2026-10-31.md](calibrayt-rdims-architecture-2026-10-31.md) |
| Hard rule | Calibrayt stays fully standalone. Ideas, patterns, schema shapes and small pieces of code may be copied and rewritten into Calibrayt. Nothing may be imported from AiRIA, called at runtime or shared with it. |

"RDIMS" is an internal working name only. Users see **Documents** (on a project, person, equipment item, supplier,
subcontractor or customer) and **Company library**.

---

## 0. What AiRIA's RDIMS actually is (inventory)

| AiRIA file | Lines | What it does |
|------------|-------|--------------|
| `airiadocs/store.py` | 1–99 | One isolated SQLite file per runtime (`airiadocs.sqlite3`). Schema for `document`, `version` (content stored as a **BLOB** in SQLite), `audit_event`. Partial unique index "one current version" (`store.py:55-57`). Insert-only audit enforced by `BEFORE UPDATE/DELETE` triggers (`store.py:72-82`). |
| `airiadocs/service.py` | 1–627 | Identity, the minimum-save "Document Card", versions, audit. `save_minimum_card` (`:256`) refuses a caller-supplied id, refuses governed fields via `**forbidden`, needs actor + source + content, falls back from title to filename, hashes the content (SHA-256) and writes "created" + "version created" audit rows in one transaction. `add_version` (`:368`) supersedes the current version and appends a new one with two audit rows. `mark_current` (`:444`) refuses a second current version. `correct_card_field` (`:547`) allows only fields in `PERMITTED_CORRECTIONS` (`:38`), needs a reason, records previous/new value. `GOVERNED_FIELDS` (`:52`) can never be written by an ordinary save. `update_audit_event`/`delete_audit_event` (`:607`, `:620`) exist only so tests can prove they are refused. |
| `airiadocs/records.py` | 1–241 | Filing and search. `file_document` (`:41`) = minimum save + optional keywords. `search` (`:102`) is a **Python loop over every firm row**: metadata filters, then each term must match the card text or the decoded body of a *text-type* file (`TEXT_EXTENSIONS`, `:31`; capped at `MAX_TEXT_BYTES`, `:32`). No index, no PDF text, no pagination (only `limit=200`). `facet_values` (`:193`) = `SELECT DISTINCT` per facet column. `link_matter` (`:213`) stores a matter pointer only. |
| `airiadocs/lifecycle.py` | 1–1430 | Legal-grade records management: record classes (`:459`), retention rules with legal/policy approval families (`:519`, `:747`), jurisdictions, retention triggers (`:841`), legal holds (`:884`, `:1019`), eligibility resolver (`:1089-1192`) that fails closed, disposition queue, two-person destruction with an immutable certificate (`:1275`), insert-only `lifecycle_event` (`:240-263`), `import_source` provenance table with idempotency key (`:278-289`). The `Actor` value object (`:305-318`) carries capabilities resolved by the caller. |
| `airiadocs/errors.py` | 1–23 | Small typed error family (`MinimumSaveError`, `FirmAccessDenied`, `AuditMutationRejected`, `VersionLineageError`). |
| `airiadocs_web/routes.py` | 1–580 | Flask blueprint `/airiadocs/records`. `_context()` (`:106`) resolves firm + capabilities from AiRIA identity and Office DMS access; `_person_resolver()` (`:129`) shows names, never ids; `_run()` (`:194`) maps typed errors to 404 / flash; download (`:296`) returns 410 for destroyed records; firm scope failures become **404, not 403** (no existence leak). |
| `airiadocs_web/office_import.py` | 1–138 | Idempotent import from Office DMS: read-only on the source, unchanged bytes = no-op, changed bytes = new version of the same document, every run returns an `ImportReport` with counts and a `reconciled` property (`:26-42`), plus one summary lifecycle event. |
| `office_dms/paths.py` | 21–234 | Path safety: storage-key regex, `sanitize_filename` (`:73`), `resolve_contained_path` (`:133`) with symlink refusal and `commonpath` containment. |
| `case_files_dms/activity_privacy.py` | 1–562 | Audit/activity detail allowlist: user-typed strings (paths, filenames, notes) are never written into activity values; detail values are typed tokens or opaque hashed refs. |
| `identity/permissions.py` | 109–114, 273–296 | Six `records.*` firm capabilities with descriptions. |
| `security/route_classifications.py` | 188–210 | Every records endpoint registered with a class and a permission note. |
| `shell/nav_hierarchy.py` | 433–460 | "AiRIAdocs → Records" nav entry. |
| `review_preview/records_access.py` | 1–325 | UAT grant script with before/after table hashes proving nothing else changed. |
| `tests/test_airiadocs_f3_foundation.py` | 51–262 | Identity, lineage, fail-closed save, append-only correction, firm isolation, and **an AST import-boundary test** (`:227-261`). |
| `docs/strategy/airiadocs-rdims.md` | 235–470 | Document Card concept, "KNOWN / INFERRED / REQUIRED-BUT-UNKNOWN" capture states, consequence classes, three retrieval modes, "capture once, find many ways". |

Not found in AiRIAdocs: full-text index (no FTS anywhere in AiRIA's Python), PDF text extraction, duplicate
detection, previews, expiry/action dates, polymorphic context links. Calibrayt must build these itself; Calibrayt
already has better building blocks for several of them (below).

---

## 1. Reuse map by concern

Legend — **REUSE/ADAPT**: concept or code worth rewriting into Calibrayt. **AIRIA-SPECIFIC**: stays in AiRIA.
**CALIBRAYT-SPECIFIC**: construction need with no AiRIA counterpart (or a Calibrayt asset already does it).

### 1.1 Ingestion

| REUSE/ADAPT | AIRIA-SPECIFIC | CALIBRAYT-SPECIFIC |
|-------------|----------------|--------------------|
| Minimum-save contract (`service.py:256-365`): system assigns identity, actor + source + bytes required, title falls back to filename, hash at save, create + first version + audit rows in **one transaction**. Rewrite as a SQLAlchemy service. | Matter/client "required context" flag (`service.py:292-295`) tied to matter intake. | Upload **in context** (project, person, equipment, supplier, subcontractor, customer, company) so the context is *known*, not asked. Byte validation reuses Calibrayt's own magic-byte checks (`app/services/build_storage.py:183-275`, `app/plan_intelligence/services.py:47`). |
| Idempotent importer with reconciliation report (`office_import.py:26-42, 93-138`): adapt as the **backfill** of existing Calibrayt stores (counts: registered / unchanged / missing bytes / failed; `reconciled` property). | Office DMS as a source system. | Sources are Calibrayt tables (plan documents, signing artifacts, generated contracts, drawing sets, historical workbooks), connected by reference, not copied. |

### 1.2 Storage

| REUSE/ADAPT | AIRIA-SPECIFIC | CALIBRAYT-SPECIFIC |
|-------------|----------------|--------------------|
| Path-safety ideas (`office_dms/paths.py:21-234`): safe storage-key regex, filename sanitising, symlink refusal, `commonpath` containment. | Bytes as SQLite BLOBs (`store.py:42-53`), separate `airiadocs.sqlite3` file per runtime (`records.py:35`). Wrong for Calibrayt: production is one SQLite DB on a 1 GB-class Render disk; BLOBs bloat the DB and its backups. | **Use Calibrayt's own pattern**, already proven in production: org-segmented, SHA-256-named, write-once files under `instance/` with atomic temp-file + `os.replace` + `fsync`, refuse overwrite of mismatched bytes — `app/services/signing_artifact_storage.py:57-131`, same in `contract_artifact_storage.py:48-110` and `historical_ingestion/storage.py:39-75`. A new `document_storage.py` root `instance/documents/<org>/<sha[0:2]>/<sha>.<ext>`. |

### 1.3 Identity

| REUSE/ADAPT | AIRIA-SPECIFIC | CALIBRAYT-SPECIFIC |
|-------------|----------------|--------------------|
| Durable document id independent of filename/path; same filename twice = two documents (`test_airiadocs_f3_foundation.py:51`); caller cannot supply an id (`service.py:279-280`). | Firm key (`firm_key`), matter id. | Integer PK + `public_id` (32-hex) like other Calibrayt records; `organization_id` String(50) FK to `organizations.id`, as everywhere in Calibrayt. |

### 1.4 Metadata (the "Document Card")

| REUSE/ADAPT | AIRIA-SPECIFIC | CALIBRAYT-SPECIFIC |
|-------------|----------------|--------------------|
| Card = small fixed core + optional fields; capture states KNOWN / INFERRED / REQUIRED-BUT-UNKNOWN and "never silently invent consequential fields" (`docs/strategy/airiadocs-rdims.md:246-284`). Permitted-correction allowlist + mandatory reason + previous/new value in audit (`service.py:38-50, 547-587`). | `practice_group`, `office`, `custodian`, `business_function`, `confidentiality`, `finality`, `archive_tier`. | Construction card: title, document type, contexts, issuer/counterparty (free text), reference number (policy #, licence #, permit #, serial), dates (issue / effective / expiry / inspection due / renewal due / warranty end), status. |

### 1.5 Classification

| REUSE/ADAPT | AIRIA-SPECIFIC | CALIBRAYT-SPECIFIC |
|-------------|----------------|--------------------|
| "Provisional type is low-consequence and correctable; anything that drives a consequence needs confirmation" (`airiadocs-rdims.md:274-284`). Classification is an audited event with previous/new (`lifecycle.py:491-512`). | Record classes, retention families, records-role capability (`lifecycle.py:459-512`). | Deterministic keyword + extension + context rules in code (e.g. "wsib" + "clearance" → WSIB clearance certificate; "coi"/"certificate of insurance" → insurance certificate). No AI, no external call. The user sees and can change the suggested type before saving. |

### 1.6 Indexing / search

| REUSE/ADAPT | AIRIA-SPECIFIC | CALIBRAYT-SPECIFIC |
|-------------|----------------|--------------------|
| Three retrieval modes, Browse / Filter / Search (`airiadocs-rdims.md:418-428`); "capture once, find many ways" (`:432-438`). `matched_in` explanation (card vs text) (`records.py:86-100`). Facet lists from distinct values (`records.py:193-210`). | Boundary from litigation search, Discovery, Universal Find, privilege search. | **SQLite FTS5** (verified available in the Calibrayt venv: SQLite 3.45.1, `ENABLE_FTS5`; a prototype query with `bm25` + `snippet` + `organization_id UNINDEXED` worked). LIKE fallback when FTS5 is missing. SQL-level paging (`LIMIT/OFFSET`), never a Python loop over all rows as in `records.py:198-261`. PDF text via Calibrayt's own `app/plan_intelligence/extraction.py:27` (pypdf 6.21.1, already in `requirements-lock.txt`). Plan pages already carry `plan_pages.extracted_text`; index it, do not re-extract. |

### 1.7 Versioning / history

| REUSE/ADAPT | AIRIA-SPECIFIC | CALIBRAYT-SPECIFIC |
|-------------|----------------|--------------------|
| Append-only version chain, exactly one current version enforced by a **partial unique index** (`store.py:55-57`), prior bytes always retrievable (`service.py:512-544`), supersede writes two audit events (`service.py:416-436`). Refuse a second current (`service.py:444-473`). | — | Version may point to bytes owned by an existing Calibrayt record (e.g. a drawing revision's plan PDF, a CaliSIGN executed PDF) rather than to an uploaded file. A new upload identical (same SHA-256) to the current version is refused ("This file is already the current version"). |

### 1.8 Relationships

| REUSE/ADAPT | AIRIA-SPECIFIC | CALIBRAYT-SPECIFIC |
|-------------|----------------|--------------------|
| Links are pointers only, written by an explicit audited action (`records.py:213-241`). Removing a link is recorded, not deleted (pattern of `legal_hold_scope.removed_at`, `lifecycle.py:169-179`). | Matter link, `related_documents` free-text column. | **Polymorphic context links** (company / project / person / equipment / supplier / subcontractor / customer) with one FK column per kind and a CHECK that exactly the right one is set — Calibrayt's own pattern in `app/models/construction_drawing.py:67-80`. Optional business-record link (purchase order, change order, subcontract commitment, subcontract quote evidence, estimate version, proposal). |

### 1.9 Permissions

| REUSE/ADAPT | AIRIA-SPECIFIC | CALIBRAYT-SPECIFIC |
|-------------|----------------|--------------------|
| Every service call takes the tenant key and refuses other tenants' objects (`service.py:246-253`); out-of-tenant = **404** at the route (`routes.py:194-201`, `:255-256`). Capabilities resolved by the web seam and passed in; the core package never grants them (`lifecycle.py:24-27, 305-318`). | `records.*` firm grants (`identity/permissions.py:109-114`), matter authorization (`routes.py:271-293`). | Map onto what exists: office wall + `get_current_organization_id()`; **field-only** members are excluded (not in `FIELD_ONLY_ALLOWED_ENDPOINTS`, `app/services/access_domains.py:36-74`); supplier logins never pass the office wall (`app/__init__.py:369-386`); person documents restricted to people administrators (`app/services/people_access.py:161-170`, instance owner or System Administrator); financial documents follow `has_office_financial_access` (`access_domains.py:215`). No new capability system. |

### 1.10 Audit

| REUSE/ADAPT | AIRIA-SPECIFIC | CALIBRAYT-SPECIFIC |
|-------------|----------------|--------------------|
| Insert-only audit table enforced by DB triggers (`store.py:72-82`, `lifecycle.py:253-263`) plus a test that update/delete are refused (`service.py:607-627`). Event types are a closed set (`service.py:24-36`, `:211-212`). Detail JSON with `sort_keys` (`lifecycle.py:403-433`). Show names, not ids (`routes.py:129-154`). Keep user-typed text out of structured detail (`case_files_dms/activity_privacy.py:1-40`, simplified). | Disposition certificates, lifecycle events for holds/rules. | First DB-trigger-enforced audit table in Calibrayt (existing audit tables such as `plan_audit_events` are append-only by convention only). Actor = `users.id` + display name, as in `signing_events`. |

### 1.11 Extraction

| REUSE/ADAPT | AIRIA-SPECIFIC | CALIBRAYT-SPECIFIC |
|-------------|----------------|--------------------|
| Text body only for known text types, capped size (`records.py:31-32, 219-228`). | — | pypdf text layer (no OCR) via `extract_deterministic_pdf`; versioned extractor name/version recorded like `plan_processing_attempts` (`app/plan_intelligence/models.py:191-245`). Date regex for issue/expiry/inspection-due candidates, shown as **proposals** that a person confirms. |

### 1.12 Duplicate handling

| REUSE/ADAPT | AIRIA-SPECIFIC | CALIBRAYT-SPECIFIC |
|-------------|----------------|--------------------|
| Same-hash re-import = "unchanged", changed hash on same source key = new version (`office_import.py:94-109`); provenance unique key `(firm, source_system, source_key, sha256)` (`lifecycle.py:278-289`). | — | On upload, same SHA-256 already in the org: show "Already filed as *X* (on *Project Y*)" with **Link it here** (adds a context link, no second copy) or **File as a new document anyway** (new document, same stored file). Bytes are deduplicated automatically by content addressing. |

### 1.13 Previews

| REUSE/ADAPT | AIRIA-SPECIFIC | CALIBRAYT-SPECIFIC |
|-------------|----------------|--------------------|
| Download only from a verified, contained path; MIME by guess (`office_dms/operations.py:721-750`). | — | Inline PDF (as `site_plans` already serves `application/pdf`, `app/routes/site_plans.py:161`) and browser-displayable images (`build_storage.BROWSER_DISPLAYABLE_IMAGE`); everything else downloads. Plan documents keep opening in the existing plan viewer. No thumbnail generation in release 1. |

### 1.14 Retention / state

| REUSE/ADAPT | AIRIA-SPECIFIC | CALIBRAYT-SPECIFIC |
|-------------|----------------|--------------------|
| Small explicit state set with plain labels (`routes.py:80-92`); "archive, don't hard-delete once audit exists" (also Calibrayt's own rule, `plan_intelligence/services.py:229-259`). | Retention rules, jurisdictions, legal holds, disposition queue, two-person destruction, certificates (`lifecycle.py:106-289, 519-1414`). | States: **Active**, **Archived** (with reason). "Expired", "Expiring soon", "Inspection due" are *computed* from confirmed dates, never stored. No destruction in release 1. |

### 1.15 Action / expiry metadata

| REUSE/ADAPT | AIRIA-SPECIFIC | CALIBRAYT-SPECIFIC |
|-------------|----------------|--------------------|
| Fail-closed lifecycle resolver that explains itself in plain words (`lifecycle.py:1049-1192`) and "nothing happens until people decide" (`:1192`). Machine proposals never self-activate (`lifecycle.py:8-11`). | Retention end dates computed from triggers and periods. | Dated obligations construction cares about: insurance and WSIB clearance expiry, licence/certification expiry, equipment inspection due, registration renewal, warranty end. Only **confirmed** dates feed "What needs your attention". |

### 1.16 Document-to-record association

| REUSE/ADAPT | AIRIA-SPECIFIC | CALIBRAYT-SPECIFIC |
|-------------|----------------|--------------------|
| Reference, never move or copy evidence across a boundary (`records.py:287-292`). | Matter closeout bridge (`airiadocs-rdims.md:697-719`). | Version rows that **reference existing records** (`plan_documents`, `signing_executed_artifacts`, `signing_frozen_artifacts`, `project_generated_contracts`, `construction_drawing_sets`, `historical_source_workbooks`); bytes are read through each owner's own verified reader (e.g. `app/services/signing.py:220-241, 1468`, `app/plan_intelligence/services.py:206`). |

---

## 2. Deliberately not reused (and why)

| AiRIA element | Reason not reused |
|---------------|-------------------|
| Separate SQLite store file (`store.py`, `records.py:35`) | Calibrayt has one governed DB with Alembic and a release migration gate; a side database would escape migrations, backups and the post-release row check. |
| Content BLOBs in the database (`store.py:42-53`) | DB growth and backup size on Render; Calibrayt already stores immutable files on the instance disk. |
| Raw `sqlite3` + hand-written SQL schema with `CREATE TABLE IF NOT EXISTS` and `_add_columns` migrations (`lifecycle.py:352-364`) | Calibrayt uses SQLAlchemy models + additive Alembic migrations rehearsed by `tools/release/migration_check.py`. |
| Record classes, retention rules, rule families, jurisdictions, obligation sources (`lifecycle.py:50-104, 459-882`) | Legal-grade records management; a construction company needs expiry tracking, not retention schedules. Revisit only if Joel asks for records retention. |
| Legal holds (`lifecycle.py:884-1046`) | Litigation concept. |
| Disposition queue, two-person destruction, disposition certificates (`lifecycle.py:181-238, 1195-1412`) | No destruction in release 1; archive only. |
| `records.*` capabilities (`identity/permissions.py:109-114`) and the UAT grant script (`review_preview/records_access.py`) | Calibrayt maps onto its existing access model; no new capability family. |
| Office DMS folders / `.versions` archives (`office_dms/operations.py`, `paths.py:51-70`) | Calibrayt documents are found through contexts and filters, not a folder tree. |
| Matter link, client/matter facets, Bates, privilege, evidence, pleadings, discovery, custodian, practice group, confidentiality classes | Legal domain coupling. |
| Python-loop search (`records.py:174-262`) | Does not scale or paginate; replaced by FTS5 / SQL. |
| `_context()` web seam that imports `app`, `identity`, `office_dms` lazily (`routes.py:106-126`) | AiRIA wiring; Calibrayt uses Flask-Login + its own services. |
| AiRIA activity-privacy full schema (`case_files_dms/activity_privacy.py`, 562 lines) | Heavier than needed; Calibrayt keeps the one rule (no user-typed text or content in structured detail). |

---

## 3. Standalone operation statement

Calibrayt's document records are **Calibrayt code in the Calibrayt repository**, written against Calibrayt's own
models, database, storage roots, login and services. AiRIA was read as a reference only; any code that is adapted
is rewritten into Calibrayt modules (no vendored copy, no `airiadocs` package name, no shared library).

At runtime there is no shared database, file store, authentication, API, deployment, search engine, background
worker, configuration or document identifier with AiRIA. Calibrayt document ids are Calibrayt ids; nothing in
Calibrayt refers to an AiRIA document, firm or matter.

Independence is proven by tests that ship with the feature:

1. **Import boundary (AST) test** — modelled on AiRIA's `tests/test_airiadocs_f3_foundation.py:227-261`.
   Walk every `.py` file under `app/`, `migrations/`, `tools/` and `tests/` and fail if any `import` /
   `from … import` names a root module from AiRIA's top-level package list (`airiadocs`, `airiadocs_web`,
   `office_dms`, `case_files_dms`, `identity`, `security`, `shell`, `review_preview`, `practice_workspaces`,
   `universal_find`, `discovery_*`, `evidence_world`, `matter_workspace`, … frozen as a literal set in the
   test), and fail if the new document modules import anything outside `app.*`, the standard library and
   `requirements-lock.txt` packages.
2. **No AiRIA configuration** — grep test over `app/` and `requirements*.txt`: no `AIRIA_*` config key, no
   AiRIA host name or URL, no AiRIA package in the lock file.
3. **No network** — the document test suite runs with sockets blocked (monkeypatched `socket.socket.connect`
   raising) and still passes: upload, classify, extract, search, attention.
4. **Storage containment** — every stored path resolves under `DOCUMENT_ROOT` (default
   `instance/documents`); test that no path outside it is read or written.
5. **Own schema only** — the migration test asserts the new tables are created in the Calibrayt database and that
   no `ATTACH DATABASE` or second engine is used.
