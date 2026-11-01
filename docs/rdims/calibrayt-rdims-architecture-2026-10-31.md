# Calibrayt Documents — architecture (one release)

| Attribute | Value |
|-----------|-------|
| Status | Proposed architecture. Not implemented. Needs a Feature Gate and Joel's approval of §18 decisions. |
| Date | 2026-10-31 |
| Baseline | Calibrayt live `7087d0d0`, Alembic head `s6f7a8b9c0d1` |
| Reference | AiRIA AiRIAdocs (read-only). Reuse decisions: [airia-rdims-reuse-map-2026-10-31.md](airia-rdims-reuse-map-2026-10-31.md) |
| Internal name | RDIMS (code and docs only). Users see **Documents** and **Company library**. |

---

## 1. Purpose and principles

One place to file, find and track the company's documents — company, project, person, equipment, supplier,
subcontractor and customer — **connected to the files Calibrayt already keeps**, without moving or duplicating them.

Flow: **upload in context → classify → extract useful dates → associate → index → track → surface in What needs
your attention.**

Principles:

1. **Standalone.** No runtime dependency on AiRIA of any kind (reuse map §3 lists the proving tests).
2. **Connect, don't copy.** Existing Calibrayt files stay where they are; documents reference them.
3. **Never silently overwrite.** New content = new version; old versions and their bytes remain.
4. **Deterministic.** Classification and date extraction are rules in code. No AI call, no external service, no
   cost per user.
5. **Proposed vs confirmed.** Extracted dates and suggested types are proposals until a person accepts them. Only
   confirmed dates create attention items.
6. **Lighter than AiRIA.** Active/Archived states, no retention schedules, holds or destruction in this release.
7. **One signature system.** CaliSIGN only.
8. **Existing access model.** Office wall, field-only restriction, supplier isolation, people-administrator rule.

---

## 2. Existing Calibrayt document stores (inventory)

| Store | Table / model | Bytes kept | Tenant key | Integrity | How RDIMS connects |
|-------|---------------|-----------|------------|-----------|--------------------|
| Plan PDFs (uploaded + generated) | `plan_documents` (`app/plan_intelligence/models.py:88`), pages `plan_pages` (text in `extracted_text`) | File: `PLAN_UPLOAD_ROOT` or `instance/plan_uploads/<project_id>/<stored_filename>` (`app/plan_intelligence/storage.py:11-42`). **Not content-addressed.** | `project_id` only (no `organization_id`; derive through `projects.organization_id`) | `sha256_hex` column | Version references `plan_documents.id`; type *Drawing / plan*; project link; `archived_at` → Archived. Text reused from `plan_pages`. |
| Drawing packages / revisions | `drawing_packages`, `drawing_revisions`, association `drawing_revision_documents` (`models.py:13-86`) | None (groups plan documents) | project | — | Revision label shown on the plan document; a newer revision's plan doc is registered as a **new version** of the same RDIMS document only when the user says so (§11.3). |
| Generated construction drawings | `construction_drawing_sets` (`app/models/construction_drawing.py:27`) | **DB BLOBs** `pdf_bytes`, `dxf_bytes` + SHA-256; write-once | `organization_id`, `project_id` | `pdf_sha256`, `dxf_sha256` | Version references the set; if `plan_document_id` is set the plan document already covers it (skip, avoid a duplicate). |
| Drawing attachments | `construction_drawing_attachments` (`:67`) | None | org | — | Pattern reused for the polymorphic CHECK (§3.3). Not registered. |
| Generated contracts (DOCX) | `project_generated_contracts` (`app/models/project_contract.py:20`) | File: `CONTRACT_ARTIFACT_ROOT` or `instance/generated_contracts/<org>/<sha>.docx` (`contract_artifact_storage.py:26-110`) | org, project, client | `artifact_sha256` | Version references the contract; type *Contract (unsigned)*; project + customer links. |
| CaliSIGN frozen PDFs | `signing_frozen_artifacts` (`app/models/signing.py:142`) | File: `SIGNING_ARTIFACT_ROOT` or `instance/signing_artifacts/<org>/<sha>.pdf` (`signing_artifact_storage.py:26-131`) | org | `sha256`, verified read `app/services/signing.py:220-241` | Not registered on its own (pre-sign copy); shown in the executed document's history. |
| CaliSIGN executed PDFs | `signing_executed_artifacts` (`signing.py:180`) | Same root, write-once | org (+ request → project, client) | `sha256`, `retrieve_executed_artifact_bytes` (`signing.py:1468`) | Version references the executed artifact; type from `document_family` (Signed contract / change order / subcontract / purchase order / delivery change); project + customer (or supplier/subcontractor) links. |
| Proposals | `proposals`, `proposal_brand_snapshots` | **Not stored**; PDF rendered on demand (`app/services/proposal_pdf.py:415`) | org | — | Not registered in release 1 (no retained bytes). An issued proposal can be filed by "Save a copy to Documents" (renders once, stores the bytes as an upload with record link `proposal`). |
| Supplier quote files | `supplier_quote_files` (`app/models/supplier_quote.py:98`) | DB BLOB | **Supplier tenant** (`supplier_quotes.supplier_id`; the supplier's own walk-in customers) | `sha256` | **Not connected.** This is the supplier's data, not the contractor's. Out of scope. |
| Subcontract quote evidence | `subcontract_quote_evidence` (`app/models/subcontractor.py:91`) | **No file** (reference, amount, dates only) | org, project, subcontractor | — | User attaches the quote PDF as a document with record link `subcontract_quote_evidence`. |
| Field captures (photos, audio) and receipts | `field_capture_events`, `field_capture_originals` (`app/models/build.py:27, 94`), `field_receipts` (`field_operations.py:65`) | File: `BUILD_ORIGINAL_ROOT` or `instance/build_originals/<org>/<project>/<event>/<original>.<ext>` (`build_storage.py:97-389`) | org, project | `sha256_hex` | **Release 1: not backfilled** (volume, and receipts are financial with their own inbox). The project Documents page shows a "Site photos" link to the existing Build view. Later: register on request. |
| Historical source workbooks | `historical_source_workbooks` (`app/models/historical_estimates.py:10`) | File: `instance/historical_uploads/<org>/<sha>.<ext>` (`historical_ingestion/storage.py:17-75`) | org | `sha256`, `idempotency_key` | Version references the workbook; type *Historical estimate workbook*; company context. |
| Closeout records | `project_closeout_records` (`app/models/closeout.py:10`) | JSON report only | org, project | — | Not a file. Closeout documents (warranties, manuals, as-builts) are uploaded under project context with types in the *Closeout* family. |
| Transactional messages | `transactional_messages` (`app/models/transactional_message.py:59`) | Metadata only (mail capture files in test/dev) | — | — | Not connected. |
| Training content | `app/training/*.py` (code), `training_*` tables | Code / DB rows | — | — | Not connected (product content, not company documents). Company training *records* are person documents. |
| Estimating cases | `docs/estimating-cases/2026/*` | Repository files | — | — | Not runtime data. Not connected. |
| Brand logos, QuickBooks packages, deck takeoff, build renditions | own roots under `instance/` | Files | org | varies | Not connected (derived/working files). |

Other facts that shape the design:

* **Organizations:** `organizations.id` is `String(50)` (e.g. `ORG-001`); every tenant table carries
  `organization_id` FK `ondelete=RESTRICT`.
* **People:** `organization_people` (`app/models/person.py:12`) is worker identity with **no office page today**
  (managed by CLI, `app/cli/auth.py`). The People & Access pages work on `user_memberships`
  (`app/routes/people_access.py:342-503`). There is no link between the two tables.
* **Equipment:** **no model exists.** "Equipment" is only a cost-item category (`app/models/cost_item.py:9`).
* **Suppliers** are global (`suppliers` has no `organization_id`); a contractor's relationship is
  `contractor_supplier_accounts` (`app/models/supplier_catalogue.py:109`). Supplier users have
  `supplier_user_memberships` and their own login wall.
* **Subcontractors** are org-scoped (`subcontractors`), but `subcontract_commitments.subcontractor_name` is free
  text with no FK (`app/models/procurement_governance.py:61`). No subcontractor or supplier detail page exists.
* **Customers** are `clients` (org-scoped), page `/clients/<id>`.
* **Access:** office members see all org projects; field-only members reach only `field.*` + an allowlist
  (`app/services/access_domains.py:30-74`) and their visible projects (`:382`); `COMPANY_MANAGEMENT` access
  domain; people administrators = instance owner or System Administrator (`people_access.py:161`);
  `has_office_financial_access` = active non-field-only office member (`access_domains.py:215`).
* **What needs your attention** (`app/services/needs_attention.py:113-361`) is derived live from records each time,
  stores nothing, office members only, items built with `_item(kind, what, who, status, when, href, action,
  urgency, sort_date)`. Shown on Home (`app/routes/main.py:28`) and `/operations/attention`.
* **Navigation** already has a **"Company library"** section (`app/navigation.py:153-162`, title in
  `app/presentation/contractor_copy.py:108`) containing *Past jobs*.
* **Text extraction:** `pypdf==6.21.1` in `requirements-lock.txt`; `app/plan_intelligence/extraction.py:27`
  `extract_deterministic_pdf` (no OCR). `python-docx==1.2.0`, `Pillow`, `pillow-heif` also present.
* **FTS5:** available in the Calibrayt venv (Python 3.13.16, SQLite 3.45.1, compile option `ENABLE_FTS5`).
  Production's SQLite build must be probed at release (§9.4, §19).

---

## 3. Data model

Module: `app/models/documents.py` (+ `app/models/equipment.py`). All tables carry `organization_id String(50) NOT
NULL FK organizations.id ON DELETE RESTRICT, index`. Timestamps `DateTime` UTC (`datetime.utcnow`, as elsewhere).
Actor columns follow `signing_events`: `*_user_id Integer FK users.id ON DELETE RESTRICT` + `*_name String(150)`.

### 3.1 `documents` — the document card

| Column | Type | Constraints / notes |
|--------|------|---------------------|
| `id` | Integer | PK |
| `public_id` | String(32) | NOT NULL, UNIQUE; `uuid4().hex`; used in URLs |
| `organization_id` | String(50) | NOT NULL, FK, index |
| `title` | String(255) | NOT NULL; falls back to filename |
| `document_type` | String(60) | NOT NULL; code from the type registry (§7), default `OTHER` |
| `type_basis` | String(20) | NOT NULL; `SUGGESTED` \| `CONFIRMED` (CHECK) |
| `type_rule` | String(60) | NULL; rule code that suggested the type |
| `status` | String(20) | NOT NULL default `ACTIVE`; CHECK `IN ('ACTIVE','ARCHIVED')` |
| `sensitivity` | String(20) | NOT NULL default `STANDARD`; CHECK `IN ('STANDARD','PEOPLE','FINANCIAL')` (§10) |
| `origin` | String(20) | NOT NULL; CHECK `IN ('UPLOAD','LINKED_RECORD','BACKFILL')` |
| `reference_number` | String(120) | NULL; policy #, licence #, permit #, serial, certificate # |
| `counterparty` | String(200) | NULL; issuer / insurer / authority (free text) |
| `description` | Text | NULL |
| `keywords` | String(500) | NULL |
| `created_by_user_id`, `created_by_name` | Integer / String(150) | NOT NULL |
| `created_at`, `updated_at` | DateTime | NOT NULL |
| `archived_at`, `archived_by_user_id`, `archived_by_name`, `archive_reason` | | NULL; reason required when archiving |

Indexes: `(organization_id, status, created_at)`, `(organization_id, document_type)`.

### 3.2 `document_versions` — immutable content chain

| Column | Type | Constraints / notes |
|--------|------|---------------------|
| `id` | Integer | PK |
| `organization_id` | String(50) | NOT NULL |
| `document_id` | Integer | NOT NULL FK `documents.id` RESTRICT, index |
| `version_number` | Integer | NOT NULL, `>= 1`; UNIQUE `(document_id, version_number)` |
| `is_current` | Boolean | NOT NULL; **partial unique index** `uq_document_versions_one_current ON (document_id) WHERE is_current = 1` (AiRIA `store.py:55-57`) |
| `source_kind` | String(40) | NOT NULL; CHECK `IN ('UPLOAD','PLAN_DOCUMENT','SIGNING_EXECUTED','GENERATED_CONTRACT','DRAWING_SET','HISTORICAL_WORKBOOK')` |
| `source_id` | Integer | NULL for `UPLOAD`, NOT NULL otherwise (CHECK) |
| `storage_key` | String(255) | NOT NULL for `UPLOAD` (CHECK), NULL otherwise; `<org>/<aa>/<sha>.<ext>` |
| `sha256` | String(64) | NOT NULL, index |
| `byte_size` | Integer | NOT NULL `>= 0` |
| `media_type` | String(120) | NOT NULL |
| `original_filename` | String(255) | NOT NULL (sanitised) |
| `availability` | String(20) | NOT NULL default `AVAILABLE`; CHECK `IN ('AVAILABLE','MISSING')` — set by backfill when a source's bytes are not on disk (§11.4) |
| `note` | String(500) | NULL; "what changed" |
| `created_by_user_id`, `created_by_name`, `created_at` | | NOT NULL |

Additional unique: partial `uq_document_versions_source ON (organization_id, source_kind, source_id) WHERE source_kind != 'UPLOAD'` — one registration per existing record, makes backfill and hooks idempotent.

Rules (service-enforced, tested): no UPDATE of content columns; superseding = set old `is_current=0` then insert new
`is_current=1` in one transaction; a new upload whose `sha256` equals the current version's is refused.

### 3.3 `document_links` — contexts and business records

| Column | Type | Constraints / notes |
|--------|------|---------------------|
| `id` | Integer | PK |
| `organization_id` | String(50) | NOT NULL |
| `document_id` | Integer | NOT NULL FK, index |
| `context_kind` | String(20) | NOT NULL; CHECK `IN ('COMPANY','PROJECT','PERSON','EQUIPMENT','SUPPLIER','SUBCONTRACTOR','CUSTOMER')` |
| `project_id` | Integer | NULL FK `projects.id` RESTRICT |
| `membership_id` | Integer | NULL FK `user_memberships.id` RESTRICT (person; §18 D1) |
| `equipment_id` | Integer | NULL FK `organization_equipment.id` RESTRICT |
| `supplier_id` | Integer | NULL FK `suppliers.id` RESTRICT (validated against an ACTIVE `contractor_supplier_accounts` row for the org) |
| `subcontractor_id` | Integer | NULL FK `subcontractors.id` RESTRICT |
| `client_id` | Integer | NULL FK `clients.id` RESTRICT |
| `record_kind` | String(40) | NULL; CHECK `IN ('PURCHASE_ORDER','CHANGE_ORDER','SUBCONTRACT_COMMITMENT','SUBCONTRACT_QUOTE','ESTIMATE_VERSION','PROPOSAL','SIGNING_REQUEST')` |
| `record_id` | Integer | NULL; NOT NULL iff `record_kind` set (CHECK) |
| `is_primary` | Boolean | NOT NULL default false; partial unique `(document_id) WHERE is_primary = 1 AND unlinked_at IS NULL` |
| `linked_by_user_id`, `linked_by_name`, `linked_at` | | NOT NULL |
| `unlinked_at`, `unlinked_by_user_id`, `unlinked_by_name`, `unlink_reason` | | NULL — links are ended, never deleted |

CHECK `ck_document_links_context` (same shape as `ck_construction_drawing_attachments_target`): exactly the FK
column for the `context_kind` is NOT NULL and the other five are NULL; `COMPANY` has all six NULL.
Partial unique: one active link per `(document_id, context_kind, <fk>)` — implemented as six partial indexes
`WHERE unlinked_at IS NULL AND context_kind = '…'`.
Indexes: `(organization_id, context_kind, project_id)`, and one per FK column.

### 3.4 `document_dates` — action / expiry metadata

| Column | Type | Constraints / notes |
|--------|------|---------------------|
| `id` | Integer | PK |
| `organization_id` | String(50) | NOT NULL |
| `document_id` | Integer | NOT NULL FK, index |
| `version_id` | Integer | NOT NULL FK `document_versions.id` — the version the date belongs to |
| `date_kind` | String(20) | NOT NULL; CHECK `IN ('ISSUED','EFFECTIVE','EXPIRES','INSPECTION_DUE','RENEWAL_DUE','WARRANTY_ENDS')` |
| `value` | Date | NOT NULL |
| `basis` | String(20) | NOT NULL; CHECK `IN ('EXTRACTED','ENTERED')` |
| `status` | String(20) | NOT NULL; CHECK `IN ('PROPOSED','CONFIRMED','REJECTED')` |
| `evidence_text` | String(240) | NULL; the matched phrase (e.g. "valid until March 31, 2027"), for the person confirming |
| `evidence_page` | Integer | NULL (0-based) |
| `extractor_version` | String(40) | NULL |
| `remind_days_before` | Integer | NOT NULL default 30, `0..365` |
| `proposed_at` | DateTime | NOT NULL |
| `decided_by_user_id`, `decided_by_name`, `decided_at` | | NULL until confirmed/rejected |

Partial unique `uq_document_dates_confirmed ON (version_id, date_kind) WHERE status = 'CONFIRMED'`.
`ENTERED` dates are written as `CONFIRMED` directly (a person typed them). Only `CONFIRMED` dates **on the current
version** of an **ACTIVE** document drive attention; a new version therefore starts its own date set and the old
reminder stops automatically, with nothing rewritten.

### 3.5 `document_events` — append-only audit

| Column | Type | Constraints / notes |
|--------|------|---------------------|
| `id` | Integer | PK |
| `organization_id` | String(50) | NOT NULL, index |
| `document_id` | Integer | NOT NULL FK, index |
| `version_id` | Integer | NULL FK |
| `event_type` | String(40) | NOT NULL; closed set: `CREATED, VERSION_ADDED, VERSION_SUPERSEDED, FIELD_CORRECTED, TYPE_CONFIRMED, LINK_ADDED, LINK_ENDED, DATE_PROPOSED, DATE_CONFIRMED, DATE_REJECTED, DATE_ENTERED, TEXT_EXTRACTED, ARCHIVED, RESTORED, DUPLICATE_LINKED, REGISTERED_FROM_RECORD, SIGNATURE_REQUESTED, DOWNLOADED` |
| `field_name` | String(40) | NULL (for corrections) |
| `previous_value`, `new_value` | Text | NULL (card fields only; never file content or extracted text) |
| `reason` | String(500) | NULL; required for corrections, archive, link end |
| `detail_json` | JSON | NULL; ids and codes only |
| `actor_user_id`, `actor_name` | Integer / String(150) | `actor_user_id` NULL only for `system:backfill` |
| `at` | DateTime | NOT NULL |

DB triggers `document_events_no_update` / `document_events_no_delete` (`RAISE(ABORT, 'document events are
insert-only')`), created by the migration and by a SQLAlchemy `DDL` `after_create` listener so `db.create_all()` in
tests gets them too (AiRIA `store.py:72-82`).

### 3.6 `document_text` — extracted text (rebuildable index input)

| Column | Type | Constraints / notes |
|--------|------|---------------------|
| `id` | Integer | PK |
| `organization_id` | String(50) | NOT NULL |
| `version_id` | Integer | NOT NULL FK, UNIQUE |
| `extractor_name`, `extractor_version` | String(60) / String(40) | NOT NULL |
| `status` | String(20) | NOT NULL; CHECK `IN ('EXTRACTED','NO_TEXT','UNSUPPORTED','FAILED','FROM_SOURCE')` |
| `page_count` | Integer | NULL |
| `char_count` | Integer | NOT NULL default 0 |
| `body` | Text | NULL; capped at 1,000,000 characters |
| `extracted_at` | DateTime | NOT NULL |

### 3.7 `document_search` — FTS5 virtual table (conditional)

```sql
CREATE VIRTUAL TABLE document_search USING fts5(
    organization_id UNINDEXED, sensitivity UNINDEXED, status UNINDEXED,
    title, filename, keywords, labels, body,
    tokenize = 'unicode61 remove_diacritics 2', prefix = '2 3'
);
-- rowid = documents.id; one row per document = card + context labels + current version text
```

Maintained by the service in the same transaction as the change (no triggers on it), rebuilt by
`flask documents reindex`. Excluded from Alembic autogenerate by an `include_object` filter in `migrations/env.py`
(names `document_search` and `document_search_*`). Created only if the FTS5 probe succeeds (§9.4).

### 3.8 `organization_equipment` (new — none exists)

| Column | Type | Constraints / notes |
|--------|------|---------------------|
| `id` | Integer | PK |
| `organization_id` | String(50) | NOT NULL FK, index |
| `name` | String(160) | NOT NULL ("Kubota KX040", "Truck 3") |
| `category` | String(40) | NOT NULL; CHECK `IN ('VEHICLE','TRAILER','HEAVY_EQUIPMENT','TOOL','LIFT','OTHER')` |
| `unit_number` | String(40) | NULL; partial unique `(organization_id, unit_number) WHERE unit_number IS NOT NULL` |
| `make`, `model` | String(80) | NULL |
| `serial_number` | String(80) | NULL |
| `plate_or_registration` | String(40) | NULL |
| `year` | Integer | NULL, CHECK 1900..2100 |
| `purchased_on` | Date | NULL |
| `status` | String(20) | NOT NULL default `ACTIVE`; CHECK `IN ('ACTIVE','RETIRED')` |
| `notes` | Text | NULL |
| `created_by_user_id`, `created_at`, `updated_by_user_id`, `updated_at` | | |

### 3.9 `organization_equipment_events` — append-only

`id, organization_id, equipment_id FK, event_type (CREATED, UPDATED, RETIRED, RESTORED), field_name, previous_value,
new_value, actor_user_id, actor_name, at`. Same insert-only triggers.

**New tables: 8 + 1 conditional virtual table.** No existing table is altered.

---

## 4. Storage layout

New module `app/services/document_storage.py`, a sibling of `signing_artifact_storage.py` (same rules, own root):

```
<DOCUMENT_ROOT or instance/documents>/
    <organization_id>/            # _ORG_SEGMENT_RE ^[A-Za-z0-9._-]{1,50}$
        <sha[0:2]>/
            <sha256>.<ext>        # ext from an allowlist, lower-case
```

* Write-once: temp file in the target dir → `fsync` → `os.replace`; an existing file with the same name is
  re-hashed and must match, else refuse (copy of `signing_artifact_storage.store_immutable_bytes`, `:90-122`).
* `absolute_stored_path()` validates the key shape and `root in path.parents`; symlinks refused.
* Same bytes uploaded twice in one org → one file, any number of versions/documents may reference it. Bytes are
  never shared across organizations (org segment).
* Allowed extensions (release 1): `.pdf .jpg .jpeg .png .gif .heic .heif .docx .xlsx .xlsm .csv .txt`; max size
  `DOCUMENT_MAX_BYTES` default 25 MB; magic-byte check for PDF/images (reuse
  `plan_intelligence.services._validate_pdf_magic`, `build_storage.validate_image_bytes`).
* `create_app` gives tests a temp `DOCUMENT_ROOT` (as for the other roots, `app/__init__.py:476-499`).
* Disk: production disk is mounted at `instance/` (`docs/operations/signing-artifact-inventory.md:13`), so files
  survive deploys. Release gate adds `instance/documents` to the post-release check.
* Files are never deleted in release 1 (archive only).

---

## 5. Ingestion flow (upload in context)

`app/services/documents/ingest.py: file_document(org, actor, *, upload, context, title=None, type_code=None,
link_record=None)`

1. **Validate** bytes (size, extension, magic) → SHA-256.
2. **Duplicate check** (§6). If a match exists the page offers *Link it here* / *File as new anyway*.
3. **Classify** (§7): suggested type + rule code; the upload form shows it pre-selected and editable.
4. **Store** bytes (§4).
5. **Write in one transaction:** `documents` + `document_versions(v1, is_current)` + primary `document_links` row
   for the context (+ optional record link) + events `CREATED`, `VERSION_ADDED`, `LINK_ADDED`.
6. **Extract** (§8) synchronously for files ≤ 10 MB / ≤ 200 pages, else on first open of the document page (no
   background worker exists; none is added). Writes `document_text`, proposed `document_dates`, event
   `TEXT_EXTRACTED` / `DATE_PROPOSED`.
7. **Index** the FTS row (§9).
8. Redirect to the document page, which shows "We found these dates — confirm or change" when proposals exist.

Add version: `add_version(document, upload, note)` — refuse identical SHA; supersede; events; extract; reindex.
Correct card: allowlist `title, document_type, reference_number, counterparty, description, keywords,
sensitivity` (sensitivity changes only by a people administrator / office financial rule); reason required;
`FIELD_CORRECTED` with previous/new (AiRIA `service.py:547-587`).

---

## 6. Duplicate handling

* Key: `(organization_id, sha256)` over `document_versions`.
* On upload with a match on an ACTIVE document's **current** version: "This file is already filed as *Title*
  (*context labels*)." Buttons: **Link it here** (adds a `document_links` row + `DUPLICATE_LINKED` event; no new
  document) · **File as a new document** (new document; same stored file) · **Cancel**.
* Match only on an older version or an archived document: show it as information and continue (no block).
* Matches are only searched inside the organization; existence in another organization is never revealed.
* Existing-record registrations are de-duplicated by `uq_document_versions_source`.
* Same filename, different bytes = different documents (AiRIA test `test_same_filename_creates_distinct_documents`).

---

## 7. Classification (deterministic)

`app/services/documents/types.py` — a frozen registry, no DB table in release 1:

```python
DocumentType(code="WSIB_CLEARANCE", label="WSIB clearance certificate", family="Compliance",
             contexts={"COMPANY", "SUBCONTRACTOR"}, expects=("EXPIRES",),
             keywords=(("wsib", "clearance"), ("workplace safety", "clearance")))
```

Families and example types (labels are what users see):

| Family | Types (code → label) | Typical contexts | Expected dates |
|--------|----------------------|------------------|----------------|
| Compliance | `INSURANCE_CERT` Certificate of insurance; `WSIB_CLEARANCE` WSIB clearance; `LICENCE` Licence; `PERMIT` Permit | company, subcontractor, supplier, project | Expires |
| Company | `POLICY` Policy; `PROCEDURE` Procedure; `FORM_TEMPLATE` Form / template; `SAFETY` Safety document; `TRAINING_MATERIAL` Training material | company | Effective |
| People | `EMPLOYMENT` Employment document; `CERTIFICATION` Certification / ticket (Working at Heights, WHMIS, first aid); `TRAINING_RECORD` Training record; `SIGNED_POLICY` Signed policy acknowledgement | person | Expires (certifications) |
| Equipment | `MANUAL` Manual; `PURCHASE` Purchase record; `INSPECTION` Inspection report; `MAINTENANCE` Maintenance record; `REGISTRATION` Registration; `EQUIPMENT_CERT` Equipment certification | equipment | Inspection due, Renewal due, Expires |
| Project | `DRAWING` Drawing / plan; `SPECIFICATION` Specification; `ESTIMATE` Estimate; `PROPOSAL` Proposal; `CONTRACT` Contract; `SIGNED_CONTRACT` Signed contract; `CHANGE_ORDER` Change order; `SUPPLIER_QUOTE` Supplier quote; `PURCHASE_ORDER` Purchase order; `SUBCONTRACT` Subcontract; `SCHEDULE` Schedule; `INVOICE` Invoice; `PHOTO` Photo; `CLOSEOUT` Closeout document | project, customer, supplier, subcontractor | — |
| Warranty | `WARRANTY` Warranty | project, equipment, supplier, customer | Warranty ends |
| Agreements | `AGREEMENT` Agreement; `APPROVAL` Customer approval; `PRODUCT_INFO` Product information | supplier, subcontractor, customer | Expires (agreements) |
| — | `OTHER` Other | any | — |

Algorithm (pure function, unit-tested with a fixture table):

1. Normalise filename (+ first 2,000 chars of extracted text when available, + PDF title) to lower-case words.
2. Score each type whose `contexts` contains the upload context: +3 per keyword tuple fully present in the
   filename, +1 if present in text; extension hints (`.jpg/.heic` → `PHOTO` +2; `.xlsm` → `ESTIMATE` +1).
3. Highest score ≥ 3 wins; ties broken by registry order; else `OTHER`. Store `type_basis=SUGGESTED`,
   `type_rule=<code>:<keyword>`. A person choosing or keeping it on the form sets `CONFIRMED`.
4. Registered existing records get a fixed type from their source (`SIGNING_EXECUTED` + `CONTRACT` family →
   `SIGNED_CONTRACT`, etc.) with `type_basis=CONFIRMED`.

Type never drives sensitivity silently: `EMPLOYMENT`, `CERTIFICATION`, `TRAINING_RECORD`, `SIGNED_POLICY` default
`sensitivity=PEOPLE` because they are uploaded in a person context (known, not inferred); `INVOICE` → `FINANCIAL`.

---

## 8. Metadata extraction

`app/services/documents/extract.py`, extractor `calibrayt-docs-text` v1:

* **PDF:** `app.plan_intelligence.extraction.extract_deterministic_pdf` (pypdf text layer, no OCR). Scanned PDFs →
  `NO_TEXT`; the page says "No readable text in this file; enter the dates by hand."
* **DOCX:** `python-docx` paragraphs + tables. **TXT/CSV:** UTF-8 decode, capped. **Images, XLSX:** `UNSUPPORTED`
  (no text) in release 1.
* **Plan documents:** text taken from existing `plan_pages.extracted_text` (`FROM_SOURCE`), not re-extracted.
* **Dates** (`dates.py`): regexes for ISO `2027-03-31`, `31/03/2027`, `03/31/2027` (ambiguous d/m flagged and both
  shown), `March 31, 2027`, `31 March 2027`, `Mar 31 2027`; each match takes the 60 characters before it and
  classifies by cue words:
  * EXPIRES: `expir`, `valid until`, `valid to`, `valid thru`, `policy period … to`, `end date`, `clearance … valid`
  * ISSUED: `issued`, `date of issue`, `issue date`
  * EFFECTIVE: `effective`, `valid from`, `start date`
  * INSPECTION_DUE: `next inspection`, `inspection due`, `re-inspect`
  * RENEWAL_DUE: `renew`, `renewal`
  * WARRANTY_ENDS: `warranty … (until|expires|ends)`, `warranty period`
  At most 2 proposals per kind (latest EXPIRES date first). Dates more than 1 year past or 25 years ahead dropped.
* Proposals are written `PROPOSED` with `evidence_text` and page. **Nothing reaches attention until a person
  confirms.** Confirm / change date / reject are one click each, audited.

---

## 9. Search

### 9.1 Modes (from AiRIA's three retrieval modes)

* **Browse:** each context page lists its documents (type family groups, newest first).
* **Filter:** type, family, context kind (+ chosen project / person / equipment / supplier / subcontractor /
  customer), status (Active / Archived), date state (Expired, Expiring in 30 days, Inspection due, No dates),
  uploaded between, uploaded by.
* **Search:** words over title, filename, keywords, context labels and file text.

### 9.2 Query (FTS5 path)

```sql
SELECT d.id, bm25(document_search, 0,0,0, 10,5,3,2,1) AS rank,
       snippet(document_search, 7, '<mark>', '</mark>', '…', 10) AS snip
FROM document_search
JOIN documents d ON d.id = document_search.rowid
WHERE document_search MATCH :q
  AND document_search.organization_id = :org
  AND d.organization_id = :org                 -- second, authoritative tenant filter
  AND d.sensitivity IN (:allowed_sensitivities)
  AND (:status IS NULL OR d.status = :status)
  [AND EXISTS (SELECT 1 FROM document_links l WHERE l.document_id = d.id AND l.unlinked_at IS NULL AND …)]
ORDER BY rank, d.created_at DESC
LIMIT :page_size OFFSET :offset;               -- page_size 25; offset capped at 2,000
```

* User text is tokenised and each token quoted (`"term"*`), so FTS syntax (`NEAR`, `-`, `:`, quotes) cannot be
  injected; maximum 8 tokens.
* `snippet` output is HTML-escaped except the `<mark>` markers (escape first, then insert markers by offsets, or
  use private-use sentinels and replace after escaping).
* Count for the pager: same query `SELECT count(*)` (bounded by org).

### 9.3 Fallback (no FTS5)

Same filters; `LIKE` over `documents.title/keywords/reference_number/counterparty`, `document_versions.
original_filename` and `document_text.body` (lower-cased, `%term%`, every term must match); ordered by
`created_at DESC`; same paging. Slower but correct; the page says "Searching titles and file text."

### 9.4 Availability

`app/services/documents/fts.py: fts5_available()` = try `CREATE VIRTUAL TABLE temp.__probe USING fts5(x)`; cached
per process. The migration creates `document_search` only when the probe passes; the service checks
`sqlite_master` for the table and otherwise uses §9.3. `flask documents reindex` (re)creates and fills it when
FTS5 becomes available. Verified: FTS5 present in the Calibrayt venv (SQLite 3.45.1); **production must be probed
in the release rehearsal** (§17 step 1).

### 9.5 Permission filter

Applied in SQL (never by post-filtering a page of results): tenant (`organization_id`), sensitivity set for the
viewer (§10), and context restrictions. Result counts never include documents the viewer cannot open.

---

## 10. Permission model (mapped to what exists)

| Viewer | Documents routes | Sees | Can change |
|--------|------------------|------|-----------|
| Signed out | Office wall → login | — | — |
| Supplier portal user | Never (supplier login wall; documents blueprint is office) | — | — |
| Field-only member | **No** (endpoints not added to `FIELD_ONLY_ALLOWED_ENDPOINTS`); keeps Site Plans for drawings | — | — |
| Office member | Yes | `STANDARD` + `FINANCIAL` (`has_office_financial_access`) in their organization | Upload, add version, correct card, confirm dates, link, archive own-org `STANDARD`/`FINANCIAL` |
| People administrator (instance owner / System Administrator) | Yes | + `PEOPLE` | + person documents; change sensitivity |

* Every lookup is `filter_by(organization_id=current_org, public_id=…)`; wrong org or no permission → **404**
  (AiRIA `routes.py:194-201`), never 403, so existence is not revealed.
* Person context pages require people administrator (as People & Access does). A `PEOPLE` document linked also to
  a project is still hidden from non-admins on the project page (sensitivity wins over context).
* Supplier documents: the contractor's own records about a supplier; never shown to that supplier's users.
* Archive requires a reason; restore allowed; no hard delete.
* New endpoints are covered automatically by `tests/test_security_route_sweep.py` (office wall); a field-only
  sweep test asserts every `documents.*` endpoint redirects/403s for field-only.
* CSRF: global `CSRFProtect` (`app/__init__.py:17, 197`).

---

## 11. Connecting existing project documents (no files moved)

### 11.1 Registration service

`register_existing(source_kind, source_id, *, actor=SYSTEM)` — idempotent (unique source index):

| source_kind | Reads bytes through | Type | Links |
|-------------|--------------------|------|-------|
| `PLAN_DOCUMENT` | `plan_intelligence.services.open_plan_document_file` (`:206`) | `DRAWING` | PROJECT (+ CUSTOMER via `projects.client_id`) |
| `SIGNING_EXECUTED` | `signing.retrieve_executed_artifact_bytes` (`:1468`, SHA-verified) | by `document_family` | PROJECT + CUSTOMER (client families); SUPPLIER for supplier families; SUBCONTRACTOR when resolvable; record link `SIGNING_REQUEST` |
| `GENERATED_CONTRACT` | `contract_artifact_storage.read_retained_docx` | `CONTRACT` | PROJECT + CUSTOMER |
| `DRAWING_SET` | `construction_drawing_sets.pdf_bytes` (only when `plan_document_id IS NULL`) | `DRAWING` | PROJECT |
| `HISTORICAL_WORKBOOK` | `historical_ingestion.storage.absolute_stored_path` | `ESTIMATE` | COMPANY |

`sha256`, `byte_size`, `media_type`, `original_filename` are copied from the source row (metadata only). Reading
bytes for download/preview/extraction always goes through the owner's reader and re-verifies the SHA-256.

### 11.2 Going forward (hooks)

One-line calls after the owning transaction commits, wrapped so a failure is logged and never breaks the owner
flow: `upload_plan_pdf` / `store_generated_plan_pdf` (`plan_intelligence/services.py:90, 164`),
`_retain_executed_artifact` (`signing.py:1156`), contract generation (`contract_generation.py`), historical
ingestion. A reconciliation check (`flask documents reconcile`) reports any source row with no registration and
registers it; it also runs at the end of backfill.

### 11.3 Drawing revisions

Registration creates one document per plan document. On the plan register page, when a plan document is added to
a newer revision of the same package, the user may choose "This replaces *Sheet set A*" → it becomes version 2 of
that document. Never inferred automatically.

### 11.4 Backfill (additive)

`flask documents backfill [--dry-run] [--organization ORG-001]`, run after the migration in the release:
* Inserts only into the new tables; reads existing tables; writes nothing else.
* Per source row: register; if bytes are not on disk (known case: 14 frozen + 5 executed synthetic UAT signing
  records whose files never reached the live disk, `docs/operations/signing-artifact-inventory.md:11`), register
  with `availability=MISSING` so the gap is visible ("This file is not available"), and count it.
* Prints an `ImportReport`-style reconciliation (AiRIA `office_import.py:26-42`): per source kind `rows / registered /
  already registered / missing bytes / failed`, and `reconciled = rows == registered + already + missing`.
* Re-running is a no-op. Dry run on the production backup copy is part of the rehearsal.
* Archived plan documents → document `ARCHIVED` with reason "Archived in the plan register".

---

## 12. What needs your attention

New block in `app/services/needs_attention.assemble` (`needs_attention.py:113`), placed before the final sort
(`:357`), kind `documents`, using `_item(...)` and `_urgency(...)`:

Governed basis (all must hold):
1. `document_dates.status = 'CONFIRMED'` (extracted-and-confirmed, or entered by a person);
2. the date's `version_id` is the document's **current** version;
3. `documents.status = 'ACTIVE'`;
4. `date_kind IN ('EXPIRES','INSPECTION_DUE','RENEWAL_DUE','WARRANTY_ENDS')`;
5. `value <= today + remind_days_before` (overdue included; overdue items stay until a new version, archive, or the
   date is corrected);
6. the viewer may see the document (sensitivity rule §10; `PEOPLE` only for people administrators).

| Event | What | Who | Status | When | Action |
|-------|------|-----|--------|------|--------|
| Expiry ahead / passed | "WSIB clearance expires" | "Acme Framing (subcontractor)" | "Expires in 12 days" / "Expired" | "Mar 31" | "Open the document" → `/documents/<public_id>` (upload the new one there) |
| Inspection due | "Kubota KX040 inspection due" | equipment name | "Due in 5 days" | date | same |
| Renewal due | "Trailer registration renewal" | equipment / company | … | | |
| Warranty ending | "Roof membrane warranty ends" | project / customer | … | | |
| Dates waiting to be confirmed | "3 documents have dates to confirm" (one rolled-up item) | — | "Found in the file, not confirmed" | — | "Review dates" → library filtered `dates=proposed` |

Urgency: `_urgency()` (overdue / today / soon ≤2 days) plus "soon" for ≤ 14 days. Nothing is stored; a resolved
item simply disappears (consistent with the module's rule, `needs_attention.py:3-6`).
Proposed dates never create a per-document item (rule 1) — only the single roll-up prompting a person to look.

---

## 13. CaliSIGN association

* **Executed artifacts become documents automatically** (§11.1, `SIGNING_EXECUTED`). The document page shows the
  CaliSIGN status and history read from `app/services/calisign.py` (`office_view`, `timeline`) — no copy of signing
  state. The frozen (pre-signature) artifact is listed in that history, not as a separate document.
* **"Send for signature" on a document** (release 1): offered only when the document's version source is a record
  CaliSIGN already signs — generated contract (`create_contract_signing_request`, `signing.py:602`), change order
  (`:537`), subcontract (`app/services/subcontract_signing.py`), supplier order (`supplier_signing.py`). The button
  links to that record's existing signing screen. No new signing code path, no second signature system.
* **Signing an arbitrary uploaded document** (e.g. an employee's policy acknowledgement) is **not in release 1**:
  `signing_requests` requires `project_id` and `client_id` NOT NULL and `document_family` is a CHECK-constrained
  list of five families (`app/models/signing.py:22-26, 245-270`), and there is no employee participant role. Doing
  it needs a CaliSIGN Feature Gate decision (new family `COMPANY_DOCUMENT`, nullable project/client for that
  family, participant role `PERSON`), see §18 D4.

---

## 14. UX placement (users never see "RDIMS")

| Where | What |
|-------|------|
| **Project hub → Documents** (new `id="hub-documents"` section on the project page, plus `/projects/<id>/documents`) | Grouped by family: Drawings & specs (includes registered plan documents, opens the existing plan viewer), Estimates & proposals, Contracts & signatures (with CaliSIGN status), Suppliers & subcontractors, Change orders, Invoices, Photos (link to Build), Closeout & warranties. Upload button pre-sets the project context. |
| **People & Access → person → Documents** (`/settings/people/<membership_id>/documents`) | People administrators only. Certifications with expiry badges. |
| **Company → Equipment** (new nav link) → equipment item → Documents | Equipment register (add / edit / retire) + its documents and next due dates. |
| **Company → Suppliers** → supplier → Documents | Small new page per supplier the org has an account with (none exists today). |
| **Subcontractors** → subcontractor → Documents | Small new page (none exists today); reachable from the Suppliers page header and from subcontract quote evidence. |
| **Clients → client → Documents** (`/clients/<id>` section) | Agreements, approvals, customer-level records + the customer's project documents (read-through). |
| **Company library → Documents** (new first link in the existing section, `app/navigation.py:153`) | All documents the viewer may see: search box, filters (§9.1), paging, "Expiring soon" quick filter; company-context upload (policies, insurance, WSIB, licences, forms, templates, safety, training). |
| Document page `/documents/<public_id>` | Card, preview (PDF/image inline, else download), versions (download any), dates (confirm/reject/enter), links (add/end), CaliSIGN panel, history (audit, names not ids). |

Wording: "Documents", "Upload a document", "New version", "Confirm date", "Linked to", "History". No "record
class", "RDIMS", "card", "disposition".

---

## 15. Code layout

```
app/models/documents.py            Document, DocumentVersion, DocumentLink, DocumentDate, DocumentEvent, DocumentText
app/models/equipment.py            OrganizationEquipment, OrganizationEquipmentEvent
app/services/document_storage.py   content-addressed write-once files
app/services/documents/
    __init__.py
    ingest.py        file_document, add_version, correct_field, archive, restore, link, unlink
    sources.py       register_existing, read_version_bytes (dispatch per source_kind), reconcile
    types.py         type registry + classify()
    extract.py       text extraction per media type
    dates.py         date candidates + cue classification
    fts.py           probe, index_document, remove, rebuild, search(), like_search()
    access.py        allowed_sensitivities(viewer, org), require_document(org, public_id, viewer)
    attention.py     attention_items(org, viewer, today)   (called from needs_attention.assemble)
app/services/equipment.py
app/routes/documents.py            blueprint "documents": /documents, /documents/<public_id>, …
app/routes/equipment.py            blueprint "equipment": /equipment, /equipment/<id>
app/cli/documents.py               backfill, reconcile, reindex
app/templates/documents/*.html, app/templates/equipment/*.html
```

---

## 16. Alembic migration outline (one migration, additive)

Revision `t7a8b9c0d1e2_company_documents` (name illustrative), `down_revision = "s6f7a8b9c0d1"`.

`upgrade()`:
1. `create_table` in FK order: `organization_equipment`, `organization_equipment_events`, `documents`,
   `document_versions`, `document_links`, `document_dates`, `document_events`, `document_text` — with all CHECKs,
   FKs (`ondelete="RESTRICT"`), indexes, and partial unique indexes (`sqlite_where=`).
2. `op.execute` the four insert-only triggers (`document_events_*`, `organization_equipment_events_*`).
3. FTS: probe in the migration connection; if available `op.execute(CREATE VIRTUAL TABLE document_search …)`;
   otherwise print "FTS5 not available: search uses the fallback" (not an error).
4. No data migration, no `batch_alter_table`, no change to any existing table or row.

`downgrade()`: drop in reverse order (rehearsal only; production never downgrades with data).

Rehearsal (existing release gate, `tools/release/migration_check.py`): on a copy of the fresh production backup —
upgrade; assert the new table list (`NEW = "documents,document_versions,document_links,document_dates,
document_events,document_text,organization_equipment,organization_equipment_events"` + `document_search` if FTS5);
assert **every pre-existing table's row count and content hash unchanged**; run `flask documents backfill
--dry-run` and record the reconciliation; then real backfill on the copy; reconciled must be true. Post-release
check adds the new tables to the "row total explained table by table" step.

---

## 17. Test plan

Release steps that are tests:
1. **Production FTS5 probe** — read-only `python -c` on the Render shell (or a tiny admin-only diagnostic endpoint
   reporting `sqlite_version` + FTS5 yes/no) before choosing the search path. Recorded in the release record.

Unit / service tests (`tests/test_documents_*.py`, synthetic data):

| Area | Tests |
|------|-------|
| Identity | system assigns `public_id`; same filename twice → two documents; title falls back to filename |
| Versions | v1 current; add_version supersedes, old bytes still downloadable; identical SHA refused; DB refuses a second `is_current` (partial unique index) |
| Audit | every action writes the right event; `UPDATE`/`DELETE` on `document_events` raise (trigger); corrections need a reason and record previous/new; no file content or extracted text in event values |
| Storage | write-once; mismatched existing file refused; path traversal / bad org segment / symlink refused; root containment; same bytes → one file |
| Duplicates | same SHA in org → offer; *Link it here* adds a link only; other org's identical file is not revealed |
| Classification | fixture table filename → expected type (≥ 40 cases incl. WSIB, COI, tickets, manuals, inspection reports, warranties); context restricts candidates; tie and no-match → `OTHER` |
| Extraction | text PDF, scanned PDF (`NO_TEXT`), DOCX, oversize, corrupt PDF (`FAILED`, upload still succeeds) |
| Dates | fixture phrases → kind + date; ambiguous d/m shows both; out-of-range dropped; proposals never create attention items |
| Attention | confirmed EXPIRES within window → item; proposed → only roll-up; archived → none; new version → old date stops; PEOPLE item hidden from non-admin; field-only → hidden; overdue ordering |
| Search | FTS path and LIKE path return the same documents for a fixture set; paging stable; FTS syntax injection (`"`, `NEAR`, `-`, `*`, `:`) is harmless; tenant isolation (two orgs, same words); sensitivity filter applied in SQL (counts exclude hidden) |
| Permissions | wrong org → 404; field-only → blocked on every `documents.*` / `equipment.*` endpoint; supplier user → supplier login wall; non-admin cannot open person pages or PEOPLE documents; route sweep passes with the new endpoints |
| Existing stores | register each source kind; idempotent; bytes read through owner reader with SHA check; missing bytes → `MISSING` and a clear page; plan doc archived → document archived; drawing set with `plan_document_id` not double-registered |
| CaliSIGN | executed artifact registers with family-derived type and links; document page shows `calisign.office_view` status; "Send for signature" only for signable sources and links to the existing flow; no new `signing_*` rows written by documents code |
| Equipment | create / edit / retire with events; unit number unique per org; documents attach |
| Migration | upgrade from `s6f7a8b9c0d1` on a synthetic DB with data in existing tables: new tables exist, existing table hashes unchanged, triggers present, FTS present iff probe passes; downgrade clean |
| Backfill | dry run writes nothing; real run reconciled; second run no-op |
| Standalone | AST import-boundary test, no-AiRIA-config test, sockets-blocked suite, storage containment (reuse map §3) |
| Wording | no user-facing template contains "RDIMS", "record class", "disposition" |

Browser evidence (existing `tools/release/evidence_*.mjs` pattern): upload a WSIB clearance on a subcontractor,
confirm the extracted expiry, see it on Home's attention list, upload the renewal as a new version, see the item
disappear; field-only account cannot reach Documents.

---

## 18. Decisions for Joel (before implementation)

| # | Decision | Recommendation |
|---|----------|----------------|
| D1 | Person documents anchor to the People & Access record (`user_memberships`) or to `organization_people` (worker identity with no office page, no link to logins) | **`user_memberships`** for release 1 (it has the page and the admin rule). Add `organization_people` as a second FK later if workers without a login need documents. |
| D2 | Field crew access to documents | **None in release 1** (they keep Site Plans). Later: a "Crew can see this" flag surfaced on Site Plans for safety sheets. |
| D3 | Default reminder lead time | **30 days**, editable per date. |
| D4 | Signing an uploaded company/employee document through CaliSIGN | **Defer** to a CaliSIGN Feature Gate (new family + nullable project/client + person role). |
| D5 | Field photos / receipts in Documents | **Link only** (to Build / Receipts Inbox); no backfill in release 1. |
| D6 | Subcontractor identity: commitments use free-text names | Documents link to `subcontractors` rows; a later slice links commitments to subcontractor ids. |

---

## 19. Risks

| Risk | Mitigation |
|------|-----------|
| Production SQLite lacks FTS5 | Probe at rehearsal; LIKE fallback is built and tested to return the same results; `reindex` creates FTS later. |
| Disk space on Render (1 GB-class disk used elsewhere) | 25 MB cap; content-addressed dedupe; existing files referenced not copied; release check reports `instance/documents` size. |
| Synchronous extraction latency on large PDFs | Size/page threshold; deferred extraction on first open; no background worker added. |
| Registration hooks touching signing / plan code | Post-commit, try/except + log only; `reconcile` command catches gaps; tests prove owner flows unchanged. |
| Missing signing bytes for 19 synthetic records | Registered as `MISSING`, visible, counted in reconciliation. |
| Wrong date extracted (d/m ambiguity) | Proposed only; both readings shown; nothing acts until confirmed. |
| `PEOPLE` documents leaking via project/customer pages or search | Sensitivity filter in SQL on every list/search/attention query; dedicated tests. |
| Global suppliers table | Links validated against the org's `contractor_supplier_accounts`; never shown to supplier users. |
| FTS virtual table vs `db.create_all()` / autogenerate | Created by migration and by an `after_create` DDL listener; excluded via `include_object`. |
| Scope creep (retention, holds, OCR, AI classification) | Out of scope for this release; listed as not reused in the reuse map §2. |

---

## 20. Out of scope (this release)

OCR; AI classification or summarisation; retention schedules, holds, destruction; document sharing with
customers/suppliers by link; field-crew document access; generic CaliSIGN signing of uploaded documents; thumbnails;
folder trees; email-in; bulk upload/zip; supplier-portal documents; anything involving AiRIA.
