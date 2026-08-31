# Session Handoff & Review Turnover Package — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | **FG-019 CLOSED / OPERATIONAL FOR UAT.** Item 10 **COMPLETE**. FG-018 **CLOSED / OPERATIONAL FOR UAT**. ADR-041 **Accepted**. [ADR-042](adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) **Accepted**. [FG-020](feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) **DRAFT FOR JOEL REVIEW / NOT APPROVED**. Live current = head `b0c1d2e3f4a5`. Full suite **494 passed**. Dedicated FG-019 **34 passed**. Dedicated FG-018 **37 passed**. API UAT port **5012**. Office UAT port **5011**. FG-008–FG-019 **CLOSED / OPERATIONAL FOR UAT**. Do **not** start BUILD. Next authorized action: **STOP**. Item 11 **governance in progress / NOT AUTHORIZED**. Item 12 **BLOCKED**. ADR-008 / ADR-010 **Proposed**. |
| Updated | 2026-08-31 |
| Protocol | [docs/governance/review-turnover-protocol.md](governance/review-turnover-protocol.md) — 22-point package |
| Complements | [current-state.md](current-state.md) · [chat-workflow-log.md](chat-workflow-log.md) · [project-state-report.md](project-state-report.md) · [milestones.md](milestones.md) |

Authority order for the next session: repository governance → current-state records → accepted ADRs / Feature Gates → implementation/migration/test evidence → conversation memory only as supplementary context.

**ALL-CHAT TURNOVER:** After this package is committed, every active CalibAi development chat may be abandoned. A new chat has **zero reliable conversation memory**. Chat history is supplemental only. No new chat may continue from a pasted old Cursor prompt without first running the required repository preflight/review.

**PRESERVE → SEARCH → VERIFY → EXECUTE.** Existing before new. No unauthorized redesign. No arbitrary policy invention. No context-drift changes. ChatGPT / Cursor memory is never corporate memory.

---

## 1. PROJECT / REPOSITORY

- **Product:** CalibAi / Brayman Estimator (The Estimator). Do not rename.
- **Path:** `/Users/joelbrayman/Desktop/Brayman-Estimator` (`~/Desktop/Brayman-Estimator`)
- **Environment:** local Flask office app; SQLite development/UAT DB (`sqlite:///brayman_estimator.db` → `instance/brayman_estimator.db`)
- **Chat titles:** must start with `BRAYMAN — <Topic>`

## 2. VERIFIED BASELINE

- Branch: `main`
- FG-017 close SHA: `620dec1a9612e87a1ede20cfa6aa46c6d72a8dd5` (`docs: close FG-017 live migration and office UAT`). Docs-reconciliation content: `dd30d752190e56ed687e270950df9bf9a06d7a26`. SHA-pin: `07cb46c501d968542dff567943044dc1db870f01`. Live `HEAD` / `origin/main`: verify `git rev-parse HEAD` and `git rev-parse origin/main` (do not treat as a circular this-commit reference). Implementation parent `00ca492e28118d75757e9a9c82384978b5decd92`. FG-016 close `fa591f14b2eb99db75c4e3720fdeb30d14a8f77a`.
- FG-016 implementation commit: `a709829d32d94ab2baf36f142ad0095254ba3d3a` (`feat: implement FG-016 Ontario Ottawa Permit Intelligence POC`)
- Alembic graph head (repository): **`b0c1d2e3f4a5`**. Live `flask db current`: **`b0c1d2e3f4a5`**. One graph head.
- Chain: … → **`f8a9b0c1d2e3` (FG-016)** → **`a9b0c1d2e3f4` (FG-017)** → **`b0c1d2e3f4a5` (FG-018; live current = head)**
- Governed full suite: **494 passed**. Dedicated FG-019 **34**. Dedicated FG-018 **37**. Pre-FG-019 baseline **460**. Pre-FG-018 baseline **423**. Dedicated FG-017 **22**. FG-016 **37**; FG-015 **19**; FG-014 **35**; FG-013 **27**; FG-012 **19**; Project Hub **13**; take-off **18**; Plan Intelligence **56**; Pricing **33**; Labour **25**; Historical **11**.
- Working tree: clean after post-FG-018 docs reconciliation; live DB unchanged this pass
- Real external AI provider **NOT AUTHORIZED**. Phase D **NOT STARTED**. Runtime permit web lookup **NOT AUTHORIZED**.

### 29 Aug commit chain (all ancestors of `main`)

| Gate | Role | SHA | Subject |
|------|------|-----|---------|
| FG-008 | governance | `820f54afc179279d2435ad3a426b3037548bb45e` | docs: approve FG-008 labour engine architecture |
| FG-008 | implementation | `0569f25e7ff496ab637d52437d48cf815522afa1` | feat: implement FG-008 labour engine foundation |
| FG-008 | live-migrate docs | `abf41ad7d5d69039b02f2cc6bf447bb0142181a2` | docs: record FG-008 live migration verification |
| FG-008 | integrity | `ff5d856d52433832c8b3099cb5a17ba72fb73db3` | fix: close FG-008 UAT integrity gaps |
| FG-009 | governance | `41bfb2e032c0386fc785b733ea5789fae9e248ef` | docs: approve FG-009 pricing engine architecture |
| FG-009 | implementation | `8e11179fb5abb42a68805fe011e84c15e866ea04` | feat: implement FG-009 pricing engine foundation |
| FG-009 | live-migrate docs | `bc37463a15dbb3a97e6250686ba5b0a4d78f1955` | docs: record FG-009 live migration verification |
| FG-010 | governance | `5bd6c772a093e9ca3ad506e17f0629eabe86f53c` | docs: approve FG-010 AI take-off architecture |
| FG-010 | implementation | `9665295ace673a46a8c645ed0598e5e91d41931c` | feat: implement FG-010 AI take-off foundation |
| FG-010 | live-migrate docs | `316cc9f11c141d806737bb7caebdb7c37c5bda9b` | docs: record FG-010 live migration verification |

No additional 29 Aug CalibAi commits exist on `main`. FG-010 live-migrate docs are dated 30 Aug. `origin/main` had no ahead/behind commits at pre-turnover inspect.

### Local branches (do not delete)

| Branch | Classification |
|--------|----------------|
| `main` | **ACTIVE / REQUIRED** |
| `cursor/constructos-branding-engine` | STALE / HISTORICAL |
| `cursor/estimate-sections-line-items` | STALE / HISTORICAL |
| `cursor/project-controls-change-orders` | STALE / HISTORICAL |
| `cursor/proposal-templates-pdf-generation` | STALE / HISTORICAL |
| `cursor/sidebar-navigation-refinement` | STALE / HISTORICAL |
| `milestone-005-plan-intelligence-phase-a` | STALE / HISTORICAL |
| `milestone-007-document-indexing` | STALE / HISTORICAL |
| `milestone-008-sheet-intelligence` | STALE / HISTORICAL |

## 3. GOVERNING DOCUMENTS

Read first: `AGENTS.md`; [platform-constitution.md](platform-constitution.md); [governance/continuity-and-anti-drift.md](governance/continuity-and-anti-drift.md); [governance/review-turnover-protocol.md](governance/review-turnover-protocol.md); [platform-governance.md](platform-governance.md); this file; [current-state.md](current-state.md); [project-state-report.md](project-state-report.md); [platform-roadmap.md](platform-roadmap.md); [feature-gates/README.md](feature-gates/README.md); [adr/README.md](adr/README.md).

FG-008 / FG-009 / FG-010 / FG-011 / FG-012 / **FG-013** files: **CLOSED / OPERATIONAL FOR UAT**. [FG-014](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-015](feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-016](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **CLOSED / OPERATIONAL FOR UAT**. [ADR-037](adr/ADR-037-project-location-and-jurisdiction-resolution.md) / [ADR-038](adr/ADR-038-permit-intelligence-authority-and-rules-library.md) / [ADR-039](adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md) **Accepted**. [ADR-032](adr/ADR-032-app-managed-historical-workbook-storage.md) **Accepted**. [ADR-033](adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted** (architecture only). ADR-010 **Proposed**. **ADR-021 Accepted** (MONITOR not implemented). Do not bulk-accept remaining Proposed ADRs. [ADR-040](adr/ADR-040-organization-brand-profile.md) is **Accepted**. [FG-017](feature-gates/FG-017-organization-brand-profile-v1.md) is **CLOSED / OPERATIONAL FOR UAT**. [ADR-041](adr/ADR-041-user-membership-and-office-authentication.md) is **Accepted**. [FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) is **CLOSED / OPERATIONAL FOR UAT**. [FG-019](feature-gates/FG-019-shared-api-foundation-v1.md) is **CLOSED / OPERATIONAL FOR UAT**. Organization Brand Profile is **operational for office UAT**. Change Order document family is a **future pin only**.

## 4. APPROVED PRODUCT VISION

PLAN → PRICE → CONTRACT → BUILD → MONITOR → LEARN on one `Project`. No rename. Office and field complementary. CalibAi owns methodology; each organization owns commercial intelligence. Brayman Construction is `ORG-001`, not the universal CalibAi default.

## 5. CURRENT CALIBAI LIFECYCLE STATE

- **ORGANIZATION:** implemented (M011)
- **HISTORICAL EVIDENCE:** Phase B implemented (FG-006)
- **PLAN:** partial — M005–M010 implemented; **M012 / FG-010 foundation CLOSED / OPERATIONAL FOR UAT**; FG-015 Permit Foundation **CLOSED / OPERATIONAL FOR UAT**; FG-016 Pass 2 **CLOSED / OPERATIONAL FOR UAT**; Phase D mapping **NOT STARTED**
- **PRICE:** partial — builder + commercial gate; Labour Engine Phase B **CLOSED / OPERATIONAL FOR UAT**; Pricing Engine **CLOSED / OPERATIONAL FOR UAT**; FG-012 internal breakdown + Proposal consistency **CLOSED / OPERATIONAL FOR UAT**
- **CONTRACT:** partial (proposals are the customer-facing estimate; FG-012 reconciles snapshot totals; Ontario templates future)
- **BUILD:** partial (change orders operational; field capture **not implemented**; [ADR-042](adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) **Accepted**; [FG-020](feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) **DRAFT / NOT APPROVED**)
- **MONITOR:** future implementation (ADR-021 **Accepted**; composed frozen baseline; Project Gross Margin; not coded)
- **LEARN:** future (ADR-024 boundary accepted; no ML)

## 6. COMPLETED CODED MILESTONES

M001, M005, M007, M008 (docs), M009 (`5dc4b09`), M010 (`6b969fe`), M011 (`cb38d93`), FG-006 (`690d755`), FG-008 (`0569f25`; integrity `ff5d856`), FG-009 (`8e11179`; not a numbered M0xx), **M012 / FG-010** (`9665295`; live-migrate docs `316cc9f`).

## 7. CURRENT MILESTONE

**FG-019 CLOSED / OPERATIONAL FOR UAT**. Roadmap item 10 is **COMPLETE**. [FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) remains **CLOSED / OPERATIONAL FOR UAT**. Live current = head `b0c1d2e3f4a5`. API UAT port **5012**. Office UAT port **5011**. [ADR-041](adr/ADR-041-user-membership-and-office-authentication.md) **Accepted**. [ADR-042](adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) **Accepted**. [FG-020](feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) **DRAFT / NOT APPROVED**. Material Catalogue **ADR-034 / ADR-035 / ADR-036 Accepted**. Permit Intelligence **ADR-037 / ADR-038 / ADR-039 Accepted**.

## 8. LAST AUTHORIZED DELTA

**Last authorized delta:** docs-only **accept ADR-042** and **draft FG-020** (**NOT APPROVED**). No BUILD code. No migration.

Prior: docs-only [ADR-042](adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) **Proposed / FOR JOEL REVIEW**. No BUILD code. No FG-020. No migration.

Prior: **approve and implement FG-019 Shared API Foundation V1**. GET-only `/api/v1`. Dedicated **34**. Focused **326**. Full suite **494**. API UAT port **5012**. No migration. No BUILD. Item 10 **COMPLETE**.

Prior: **draft FG-019 Shared API Foundation V1**. Docs only. Status was **DRAFT FOR JOEL REVIEW / NOT APPROVED**. No product code. No tests. No migration.

Prior: **post-FG-018 current-state documentation reconciliation**. Docs only. No product code. No Feature Gate. No ADR created or accepted. No migration. No database mutation. Repaired stale CURRENT language so the repository matches FG-018 **CLOSED / OPERATIONAL FOR UAT** and item 10 **PARTIALLY COMPLETE**.

Prior: **FG-018 live migration + CLI bootstrap + bounded office UAT**. Applied `a9b0c1d2e3f4` → `b0c1d2e3f4a5`. First ORG-001 user bootstrapped. Office UAT **PASSED** on port **5011**. Dedicated **37** / focused **460** / full suite **460**. Status **CLOSED / OPERATIONAL FOR UAT**. Shared API deferred. BUILD remains blocked.

Prior: **Implement FG-018**. Product code, dedicated tests, revision `b0c1d2e3f4a5`. Implementation SHA `0d7af3e93a9d6c4f27eb2136f915297620be59ed`. Live upgrade was not run in that pass.

Prior: **post-FG-017 roadmap documentation reconciliation**. Docs only. No product code. No Feature Gate. No ADR. No migration. No database mutation. Repaired stale CURRENT/FUTURE/NEXT language so the repository matches FG-017 **CLOSED / OPERATIONAL FOR UAT**.

Prior: **FG-017 live migration + bounded office UAT**. Status **CLOSED / OPERATIONAL FOR UAT**. Applied `f8a9b0c1d2e3` → `a9b0c1d2e3f4`. Office UAT on port **5010**. Product-code changes: none. Ensure + backfill via governed services. Labeled UAT proposals 2–4. Full suite **423 passed**. Close SHA `620dec1a9612e87a1ede20cfa6aa46c6d72a8dd5`.

Prior: **FG-017 product implementation**. Status was **IMPLEMENTED / LIVE MIGRATION PENDING** at that time. Implementation `00ca492e28118d75757e9a9c82384978b5decd92`. Superseded by live-migrate/UAT close.

Prior: **post-FG-016 full documentation / governance turnover**. Docs only. No product code. No Feature Gate. No ADR. No migration. No database mutation. FG-016 remains **CLOSED / OPERATIONAL FOR UAT**.

Prior: **FG-016 live migration + Mike Pratt office UAT**. Status **CLOSED / OPERATIONAL FOR UAT**. Applied `e7f8a9b0c1d2` → `f8a9b0c1d2e3`. Pratt project **id 9** on port **5009**. Product-code changes: none. Close commit `fa591f14b2eb99db75c4e3720fdeb30d14a8f77a`.

Prior: **FG-016 Feature Gate governance**. Status **APPROVED FOR IMPLEMENTATION** / **IMPLEMENTATION NOT STARTED**. Docs only.

Prior: **FG-015 live migration + office UAT**. Status **CLOSED / OPERATIONAL FOR UAT**. Office UAT **PASSED** on port **5008**. Product-code changes: none. FG-014 remains **CLOSED / OPERATIONAL FOR UAT**.

Prior: FG-014 office re-UAT and closure. Port **5007**. Dedicated tests **35**; full suite **345** (not rerun). ADR-008 remains Proposed.

Prior: FG-014 **APPROVED FOR IMPLEMENTATION** (`273803b`). Material Catalogue ADR-034 / ADR-035 / ADR-036 **Accepted** (`130b3fd`). FG-013 closed.

## 9. IMPLEMENTATION STATUS

- Labour Engine: `LabourTask`, `LabourTaskMapping`, `ProductionRateStandard`, `DirectLabourCostRateStandard`, `LabourCalibrationCandidate`, `EstimateLabourSnapshot`, `LabourAuditEvent`. Office `/labour-engine/`.
- Pricing Engine: `OrganizationPricingPolicy`, `EstimatePricingSnapshot`, `PricingAuditEvent`. Methods `TRUE_GROSS_MARGIN` / `COST_PLUS_MARKUP` / `COST_PLUS_MARKUP_STACK`. Office `/pricing-engine/`.
- Take-off: `TakeoffExtractionRun`, `TakeoffCandidate`, `TakeoffPackage`, `TakeoffPackageItem`. Provider-neutral architecture; **`calibai-mock` only**. Office `/projects/<id>/plans/takeoff`. Initial element `INTERIOR_DOOR_OPENING`. COUNT dimensionless (no scale). Linear / polyline / area / perimeter remain scale-governed. Approved package immutable. No automatic estimate insertion.
- Project Hub: `/projects/<id>` (`app/services/project_hub.py`) reads stored facts and links. PLAN includes FG-015 foundation plus FG-016 report available / last analysis / attention / recheck.
- FG-014: `CanonicalMaterial`; optional `CostItem.canonical_material_id`; office `/material-catalogue/` (`app/services/material_catalogue.py`). Identity only. No live supplier data.
- FG-015: `ProjectLocation`; `JurisdictionDefinition` / `JurisdictionAlias`; versioned `PermitProfile`; `app/services/jurisdiction.py`; `app/services/permit_foundation.py`; `/projects/<id>/location/edit`.
- FG-016: `PermitRule`, `ProjectPermitFact`, `PermitAnalysis`, `PermitFinding`; `app/services/permit_intelligence.py`; `/projects/<id>/permit-report` (+ PDF). 10 APPROVED Ottawa coach-house rules. Pratt live UAT project **id 9**.
- FG-017: `OrganizationBrandProfile`; `ProposalBrandSnapshot`; `app/services/brand_profile.py`; `app/services/brand_logo_storage.py`; Settings `/settings/brand-profile`; Proposal preview/PDF consume snapshot-or-current. Office UAT port **5010**.
- FG-019: GET-only `/api/v1/me`, `/api/v1/projects`, `/api/v1/projects/<id>`; `app/services/shared_api.py`; JSON 401/403/404/405. No migration. API UAT port **5012**.
- FG-018: `User`; `UserMembership`; `app/services/auth.py`; `/login` `/logout`; CSRFProtect; membership org context; CLI bootstrap/reset. Live current = head `b0c1d2e3f4a5`. Office UAT port **5011**.

## 10. TEST / UAT / MIGRATION STATUS

- Graph head `b0c1d2e3f4a5`. Live current `b0c1d2e3f4a5`. Applied `a9b0c1d2e3f4` → `b0c1d2e3f4a5`. One head.
- Dedicated: FG-019 **34**; FG-018 **37**; FG-017 **22**; FG-016 **37**; FG-015 permit foundation **19**; FG-014 material catalogue **35**; FG-013 upload 27; FG-012 19; Project Hub 13; take-off 18; Plan Intelligence 56; Pricing 33; Labour 25; Historical 11.
- Full suite: **494 passed**.
- Live API FG-019 UAT **PASSED** on port **5012**. Live office FG-018 UAT **PASSED** on port **5011**. FG-017 UAT remains **PASSED** on port **5010**. Pratt Permit Report UAT remains **PASSED** on port **5009** (project id 9).

## 11. PROTECTED STATE

- Constitution Articles 1–12
- Accepted proposal immutability; live DB has labeled Draft `PROP-FG012-UAT-GM` (not Accepted)
- PlanDocument bytes / SHA-256 immutability; historical workbook content and hashes outside Git (`~/Desktop/CalibAi Historical Estimates`) — **legacy corpus not modified**. Productized FG-013 bytes (when implemented) live under ADR-032 app-managed storage, not Git.
- `HistoricalLabourItem` source facts **not rewritten** (120 rows; 43 with stored `hourly_rate = 0.13` remain evidence defects)
- Human review is authoritative; AI confidence advisory only
- ORG isolation; no cross-org pooling; ORG-001 $65 / 15% GM are org-specific, not CalibAi defaults
- Legal Content Gate for Ontario contract/warranty
- Append-only audit history (including ORG-999 probe row and UAT reconciliation)

## 12. ACCEPTED ADRs

002, 005, 006, 007, 009, 011, 017, 018, 019, 020, **021**, 022, 023, 024, 025, 026, 027, 028, 029, 030, 031, **032**, **033**, **034**, **035**, **036**, **037**, **038**, **039**, **040**, **041**.

## 13. PROPOSED / OPEN ADRs

001, 003, 004, 008, **010**, 012–016. **ADR-010 remains Proposed** (OCR, CAD, real external AI provider). Do not bulk-accept.

## 14. FEATURE GATES

- **FG-001:** Draft for Joel approval (preserve)
- **FG-002:** Approved for Phase A (M005 implemented)
- **FG-003:** CONDITIONAL PASS — architecture only
- **FG-004 / FG-005 / FG-006 / FG-007:** APPROVED, IMPLEMENTED & VERIFIED
- **FG-008 / FG-009 / FG-010 / FG-011 / FG-012:** **CLOSED / OPERATIONAL FOR UAT**
- **FG-013:** **CLOSED / OPERATIONAL FOR UAT**. Multi-file UX **LOCKED**. Folder/OS-drag native pickers **not live-browser verified**. ADR-032 **Accepted**. No durable `UploadBatch`. Revision `c5d6e7f8a9b0` (**gate-at-close** live current=head; later superseded).
- **FG-014:** **CLOSED / OPERATIONAL FOR UAT**. Identity-only dimensional lumber + sheet goods. **Gate-at-close** live current=head `d6e7f8a9b0c1` (later superseded). Catalogue-link flash repaired. No supplier schema, bulk onboarding, Winchester, Phase D, or ADR-008.
- **FG-015:** **CLOSED / OPERATIONAL FOR UAT**. **Gate-at-close** live current = head `e7f8a9b0c1d2` (later superseded by FG-016 `f8a9b0c1d2e3`). No live lookup.
- **FG-016:** **CLOSED / OPERATIONAL FOR UAT**. **Gate-at-close** live current = head `f8a9b0c1d2e3` (later superseded by FG-017). Pratt UAT project 9 port 5009. 10 APPROVED Ottawa coach-house rules. No runtime web. No external AI.
- **FG-017:** **CLOSED / OPERATIONAL FOR UAT**. **Gate-at-close** current = head `a9b0c1d2e3f4`. Office UAT port **5010**. ADR-040 **Accepted**. Change Order / Permit branding **not** in this gate. Live head today is `b0c1d2e3f4a5`.
- **FG-018:** **CLOSED / OPERATIONAL FOR UAT**. [ADR-041](adr/ADR-041-user-membership-and-office-authentication.md) **Accepted**. Live current = head `b0c1d2e3f4a5`. Office UAT port **5011**. Shared API **out of this gate**. Not production-security certification.
- **FG-019:** **CLOSED / OPERATIONAL FOR UAT**. Shared API Foundation V1. GET-only `/api/v1`. No migration. API UAT port **5012**. Does **not** authorize BUILD.

## 15. CHAT → REPOSITORY DELTA LEDGER RESULT

29 Aug–31 Aug FG-008 through FG-018 architecture, implementation, live migrate, UAT, and closure are in Git and governed docs. This pass records the FG-019 **draft** only. Chat history is not the system of record.

**Completeness test:** Is any material approved fact only in this chat? **NO** after this documentation update.

## 16. OPEN DECISIONS

- Real external AI provider / ADR-010 (not authorized)
- Phase D reviewed quantity → estimate mapping (not started; requires its own gate)
- Project Hub UX (roadmap item 8; **CLOSED / OPERATIONAL FOR UAT**)
- Estimate-output consistency (roadmap item 9 / FG-012; **CLOSED / OPERATIONAL FOR UAT**)
- Actor-string reviewer identity on **historical** rows remains a snapshot ([ADR-041](adr/ADR-041-user-membership-and-office-authentication.md) **Accepted**; [FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) **CLOSED / OPERATIONAL FOR UAT**)
- ARCH-only take-off eligibility
- Cancelled extraction-run status modeled; no cancel operation
- ORG-001 optional overhead/profit treatments `UNSPECIFIED`; contingency visibility `UNSPECIFIED`; `contingency_source` / `contingency_pricing_treatment` unset (NULL) — distinct from org-approved `NOT_APPLIED`
- Labour-snapshot Direct Labour Cost not included in estimate basis by default (ADR-021 records the GM comparability issue; does not correct it)
- [FG-013](feature-gates/FG-013-contractor-calibration-onboarding-historical-upload-ux.md) is **CLOSED / OPERATIONAL FOR UAT**. **LOCKED:** one user action may load many workbooks; no durable `UploadBatch`. Do **not** `flask db upgrade` again.
- [ADR-033](adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted** (docs only). BMR / Winchester / Darcy are **not exclusive**. Winchester is launch/reference. Contractor procurement (A) ≠ CalibAi channel (B). Darcy commercial terms **unset**. Supplier Feature Gate **not authorized**. Governed **bulk supplier onboarding** is **FUTURE / NOT IMPLEMENTED** (not one-product-at-a-time; does not expand FG-014).
- **Permit Intelligence** Pass 2 is **CLOSED / OPERATIONAL FOR UAT**. [FG-016](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **CLOSED / OPERATIONAL FOR UAT**. Architecture **Accepted** ([ADR-037](adr/ADR-037-project-location-and-jurisdiction-resolution.md) / [ADR-038](adr/ADR-038-permit-intelligence-authority-and-rules-library.md) / [ADR-039](adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md)). [FG-015](feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **CLOSED / OPERATIONAL FOR UAT** (foundation). Advisory preflight. AHJ remains final. **PASS** means no issue identified against governed checks performed — never AHJ approved. No live lookup. No external AI. Mike Pratt Coach House at 2562 Church Street, North Gower, Ontario is the **FG-016 UAT reference** — live project **id 9** (`FG016-UAT-PRATT`) on port **5009**.
- **Organization Brand Profile** is **CLOSED / OPERATIONAL FOR UAT** ([organization-brand-profile.md](architecture/organization-brand-profile.md)). [ADR-040](adr/ADR-040-organization-brand-profile.md) **Accepted**. [FG-017](feature-gates/FG-017-organization-brand-profile-v1.md). Settings at `/settings/brand-profile`. Proposal preview/PDF consume snapshot-or-current. **Gate-at-close** current = head `a9b0c1d2e3f4`. Office UAT port **5010**. Live head today is `b0c1d2e3f4a5`.
- **Authentication / actor identity + shared API** — [ADR-041](adr/ADR-041-user-membership-and-office-authentication.md) **Accepted**. [FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-019](feature-gates/FG-019-shared-api-foundation-v1.md) **CLOSED / OPERATIONAL FOR UAT**. Roadmap item 10 is **COMPLETE**. [ADR-042](adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) **Accepted**. [FG-020](feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) **DRAFT / NOT APPROVED**. Item 11 is **governance in progress / NOT AUTHORIZED**.
- **Change Order document family** is **FUTURE / NOT IMPLEMENTED** ([change-order-document-family.md](architecture/change-order-document-family.md)). Existing Change Order record remains authoritative. Do not create a second entity. Not email. Not field UX.

## 17. KNOWN RISKS / UNRESOLVED PRODUCT ITEMS

**FG-008 (evidence defects — do not repair as product bugs):** 0.13 hourly-rate cluster (43/120); material SKUs classified as labour; historical crew/duration inconsistencies.

**FG-009 carry-forward:** Optional layers unspecified as above. Labour-snapshot Direct Labour Cost not in estimate basis by default.

**FG-012 residual:** Office proposal create/detail still lists Overhead/Profit amounts (zero when named method governs). Customer preview/PDF do not. Live FG-009 UAT estimates have no Allowance lines and no labour snapshots; dedicated tests cover those cases. Synthetic UAT residue including `PROP-FG012-UAT-GM`.

**FG-010:** 6 `takeoff.candidate.accept` PlanAuditEvent rows vs 4 accepted candidate rows (duplicate submit residue; do not invent a cleanup). Leftover suggested candidates on runs 2–3.

**Platform:** office authentication is **operational for UAT** (FG-018). Shared API Foundation V1 is **operational for UAT** (FG-019). RBAC and org-switcher are **not implemented**. This is not production-security certification.

No product-code defects were opened for repair in this turnover. Do not fix them here.

## 18. DEFERRED ITEMS

Phase D estimate mapping; Crew Template catalog; payroll burden; `LabourActualObservation`; field/mobile; QuickBooks API; Ontario contract/warranty; four-output outputs 3–4; TBD/PLACEHOLDER durable state; OCR/CAD; multi-trade extraction; real external AI provider; BUILD/MONITOR/LEARN **implementation**; native/token auth; supplier / Winchester POC; bulk supplier catalogue onboarding; Darcy channel economics; industry benchmarking; RBAC / org-switcher / invitations / SSO; national Permit Rules expansion; Change Order document family.

## 19. EXPLICITLY PROHIBITED NEXT ACTIONS

Do not start Phase D. Do not enable an external AI provider. Do not start BUILD, Field Web, tokens, RBAC, org-switcher, invitations, SSO, or password-reset email. Do not treat Item-10 completion as BUILD authorization. Do not treat ADR-042 acceptance as FG-020 approval or BUILD code authorization. Do not **implement** MONITOR/LEARN, QuickBooks, or contract/warranty work. Do **not** create another migration. Do not treat ADR-021 acceptance as a MONITOR Feature Gate. Do not treat ADR-033 as a supplier Feature Gate or Winchester POC. Do not implement bulk supplier onboarding. Do not grant supplier exclusivity. Do not set Darcy percentages. Do not reopen FG-008 / FG-009 / FG-010 / FG-011 / FG-012 / FG-013 / FG-014 / **FG-015** / **FG-016** / **FG-017** / **FG-018**. Do not insert estimate lines from take-off. Do not create a new document module, Customer Estimate entity, or a second Alembic head. Do not copy Dashboard unscoped counts. Do not rewrite historical labour facts. Do not move/recopy/delete the legacy Desktop corpus. Do not delete synthetic UAT or append-only audit history. Do not implement supplier pricing. Do not accept ADR-008. Do not accept ADR-010. Do not begin national permit expansion. Do not implement live regulatory AI, in-product web lookup, automatic permit conclusions, or municipal submissions. Do not implement Change Order document-family rewrite, client email, or a second Change Order entity until Joel separately Approves the gate and authorizes an implementation prompt.

## 20. NEXT AUTHORIZED ACTION

**Next governed action:** **STOP.** [ADR-042](adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) is **Accepted**. [FG-020](feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) is **DRAFT FOR JOEL REVIEW / NOT APPROVED**. Do not implement BUILD. Do not start Field Web. [FG-019](feature-gates/FG-019-shared-api-foundation-v1.md) is **CLOSED / OPERATIONAL FOR UAT**. [FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) is **CLOSED / OPERATIONAL FOR UAT**. Roadmap item 10 is **COMPLETE**. Item 11 is **governance in progress / NOT AUTHORIZED**. Item 12 is **BLOCKED / NOT AUTHORIZED**.

**Roadmap direction (not authorization):** After Joel **approves FG-020**, a separate implementation prompt (including file-custody reconnaissance) is required. **ROADMAP SEQUENCE ≠ IMPLEMENTATION AUTHORIZATION.**

## 21. EXACT REPOSITORY RESUME COMMANDS

Run in **Cursor Terminal**:

```bash
cd /Users/joelbrayman/Desktop/Brayman-Estimator
pwd
git status
git branch --show-current
git log -1 --oneline
git rev-parse HEAD
git rev-parse origin/main
git diff --check
./venv/bin/flask db current
./venv/bin/flask db heads
./venv/bin/python -m pytest -q tests/test_estimate_output_consistency.py
./venv/bin/python -m pytest -q tests/test_project_hub.py
./venv/bin/python -m pytest -q tests/test_takeoff.py
./venv/bin/python -m pytest -q tests/test_plan_upload.py tests/test_plan_indexing.py tests/test_sheet_intelligence.py tests/test_scale_measurement.py
./venv/bin/python -m pytest -q tests/test_pricing_engine.py
./venv/bin/python -m pytest -q tests/test_labour_engine.py
./venv/bin/python -m pytest -q tests/test_historical_ingestion.py
./venv/bin/python -m pytest -q tests/test_historical_upload_fg013.py
./venv/bin/python -m pytest -q
```

Expected: branch `main`; HEAD = `origin/main`; working tree clean; Alembic **current = head = `b0c1d2e3f4a5`**; one graph head; FG-019 34; FG-018 37; FG-017 22; FG-016 37; FG-015 19; FG-014 35; FG-013 27; FG-012 19; Project Hub 13; take-off 18; Plan Intelligence 56; Pricing 33; Labour 25; Historical 11; full suite **494 passed**. Non-development `flask` CLI requires local-only `SECRET_KEY` (gitignored `.env`).

## 22. FRESH CHAT STARTUP PROMPT

Canonical location for the next conversation. Paste into a **new** ChatGPT or Cursor chat. Do **not** continue from an old prompt without preflight.

```text
BRAYMAN — CONTINUE CALIBAI DEVELOPMENT — FG-019 CLOSED / OPERATIONAL FOR UAT

You are starting a FRESH conversation on the Brayman-Estimator (CalibAi / The Estimator) platform.

The prior development chats have been discarded. You have ZERO reliable conversation memory.
Chat history is supplemental only. The repository is the ONE SOURCE OF TRUTH.
ChatGPT / Cursor memory is never corporate memory.

Conversation titles in this workspace must start with: BRAYMAN — <Topic>.

DO NOT start BUILD.
DO NOT start Field Web.
DO NOT add tokens or API keys.
DO NOT start RBAC or an org-switcher.
DO NOT start Change Order document work.
DO NOT start Phase D.
DO NOT start supplier integration.
DO NOT enable external AI or runtime web lookup.

ROADMAP SEQUENCE ≠ IMPLEMENTATION AUTHORIZATION.
Item 10 is COMPLETE (FG-018 + FG-019 both CLOSED / OPERATIONAL FOR UAT).
Item 11 BUILD is governance in progress / NOT AUTHORIZED.
ADR-042 is Accepted. FG-020 is DRAFT FOR JOEL REVIEW / NOT APPROVED.
Item 12 Field Web is BLOCKED / NOT AUTHORIZED.
Current authorized state = STOP. Do not implement BUILD. Do not start Field Web.

1. REVIEW REPOSITORY GOVERNANCE FIRST
Read and comply with:
- AGENTS.md
- docs/platform-constitution.md
- docs/governance/continuity-and-anti-drift.md
- docs/governance/review-turnover-protocol.md
- docs/platform-governance.md
- docs/session-handoff.md
- docs/current-state.md
- docs/project-state-report.md
- docs/platform-roadmap.md
- docs/feature-gates/README.md
- docs/adr/README.md
- docs/adr/ADR-042-build-field-evidence-and-iphone-first-capture.md
- docs/feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md
- docs/adr/ADR-041-user-membership-and-office-authentication.md
- docs/feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md
- docs/feature-gates/FG-019-shared-api-foundation-v1.md
- docs/adr/ADR-022-field-client-and-shared-api.md
- docs/adr/ADR-020-build-module-boundary.md

2. VERIFY BASELINE (Cursor Terminal)
cd /Users/joelbrayman/Desktop/Brayman-Estimator
git status
git branch --show-current
git log -1 --oneline
git rev-parse HEAD
git rev-parse origin/main
git diff --check
./venv/bin/flask db current
./venv/bin/flask db heads

Confirm:
- branch = main
- HEAD = origin/main
- working tree clean
- Alembic current = b0c1d2e3f4a5
- Alembic heads = b0c1d2e3f4a5 (one graph head)

3. IDENTIFY CURRENT STOP STATE
Independently reconstruct from the repository:
- FG-008 through FG-019 CLOSED / OPERATIONAL FOR UAT
- Live current = head b0c1d2e3f4a5
- Full suite 494 passed; dedicated FG-019 34; dedicated FG-018 37
- Pratt UAT project id 9 / FG016-UAT-PRATT / analysis v3 / advisory only
- FG-018 office UAT PASSED on port 5011
- FG-019 API UAT PASSED on port 5012
- ADR-040 Accepted
- ADR-041 Accepted
- ADR-042 Accepted
- FG-020 DRAFT FOR JOEL REVIEW / NOT APPROVED
- FG-018 CLOSED / OPERATIONAL FOR UAT
- FG-019 CLOSED / OPERATIONAL FOR UAT
- Roadmap item 10 COMPLETE
- Item 11 BUILD governance in progress / NOT AUTHORIZED
- FG-020 DRAFT / NOT APPROVED
- Field Web BLOCKED until separately gated
- ADR-008 and ADR-010 remain Proposed
- Phase D NOT STARTED / NOT AUTHORIZED
- Real external AI NOT AUTHORIZED
- Runtime permit web lookup NOT AUTHORIZED

4. RETURN A CONCISE CURRENT STATE REVIEW
Then WAIT for Joel to authorize BUILD architecture / a Feature Gate, or a different task.
Do NOT start BUILD.

Do NOT rely on AI memory. Do NOT guess missing product rules.
Do NOT create another migration.

PRESERVE → SEARCH → VERIFY → EXECUTE.
Existing before new. No unauthorized redesign. No arbitrary policy invention.
```

---

## Live development/UAT database snapshot (read-only, 2026-08-30 post FG-016 UAT)

Historical snapshot taken after FG-016 Pratt UAT and **before** FG-017 Brand Profile tables. Table counts below are **not** the live post-FG-017 schema (Brand Profile / snapshot tables were added later). FG-017 residue is listed under Synthetic residue. Do not treat this count table as the live Alembic head.

FG-015-era counts (clients 4 / projects 8) are **superseded**. Verified read-only after Pratt UAT:

| Table | Count |
|-------|------:|
| organizations | 2 |
| clients | 5 |
| projects | 11 |
| estimates | 5 |
| estimate_versions | 5 |
| estimate_line_items | 4 |
| proposal_templates | 1 |
| proposals | 1 |
| change_orders | 3 |
| historical_source_workbooks | 20 |
| historical_estimates | 20 |
| historical_labour_items | 120 |
| historical_cost_line_items | 661 |
| historical_subcontract_items | 7 |
| historical_source_observations | 665 |
| historical_data_quality_flags | 19 |
| labour_tasks | 1 |
| labour_task_mappings | 4 |
| production_rate_standards | 1 |
| direct_labour_cost_rate_standards | 1 |
| labour_calibration_candidates | 1 |
| estimate_labour_snapshots | 0 |
| labour_audit_events | 25 |
| organization_pricing_policies | 2 |
| estimate_pricing_snapshots | 3 |
| pricing_audit_events | 20 |
| drawing_packages | 2 |
| plan_documents | 3 |
| drawing_revisions | 2 |
| plan_pages | 14 |
| plan_sheets | 1 |
| plan_sheet_pages | 1 |
| plan_sheet_suggestions | 0 |
| plan_scale_calibrations | 0 |
| plan_measurements | 1 |
| plan_audit_events | 45 |
| takeoff_extraction_runs | 3 |
| takeoff_candidates | 12 |
| takeoff_packages | 1 |
| takeoff_package_items | 3 |
| jurisdiction_definitions | 3 |
| jurisdiction_aliases | 7 |
| project_locations | 8 |
| permit_profiles | 10 |
| permit_rules | 10 |
| project_permit_facts | 14 |
| permit_analyses | 5 |
| permit_findings | 32 |
| canonical_materials | 27 |

**ORG-001 operating policies (verified):** DLCRS id 1 = **$65 CAD/man-hour**, `APPROVED`. Default pricing policy id 1 = **TRUE_GROSS_MARGIN** 15%, tax CA-ON **13%**, `ORG_APPROVED`, `is_default=1`. Overhead/profit treatments **UNSPECIFIED**. Contingency visibility **UNSPECIFIED**; `contingency_source` / `contingency_pricing_treatment` unset.

Customer project `Estimator Project` (client Michelle Steele) was not used as FG-008/009/010 synthetic UAT.

### Synthetic residue (leave labeled; do not delete)

**FG-008 — LABELED / NON-OPERATING + IMMUTABLE AUDIT/EVIDENCE**

- Archived task `UAT-FG008-001` / `FG-008 UAT Test Task`
- Mapping 1 **REVOKED**; mappings 2–4 **REJECTED**
- Production standard id 1 **WITHDRAWN** (rate 999.000001)
- Calibration candidate id 1 **WITHDRAWN**
- Labour audit event 16 **ORG-999** probe (preserved); event 23 ORG-001 `uat.integrity.reconciliation`

**FG-009 — LABELED / NON-OPERATING + IMMUTABLE AUDIT/EVIDENCE; withdrawn policy is NON-OPERATING**

- Client `FG-009 UAT Client` (id 2); project `FG-009 UAT Test` / `FG-009-UAT` (id 2)
- Estimates `EST-FG009-UAT-*` (ids 1–5)
- COs `FG-009 UAT CO TRUE_GM` / `Markup` / `Legacy`
- Policy id 2 `FG-009-UAT-MARKUP-15` **WITHDRAWN**
- Snapshots 1–3; pricing audit history retained

**FG-010 — LABELED / NON-OPERATING + IMMUTABLE AUDIT/EVIDENCE**

- Client `FG-010 UAT Client` (id 3); project `FG-010 UAT` / `FG-010-UAT` (id 3)
- Documents `FG-010-UAT-A-101.pdf` (searchable) and `FG-010-UAT-no-text.pdf` (no text layer); gitignored files under `instance/plan_uploads/3/`
- Runs 1–3 `calibai-mock` / `succeeded` / `INTERIOR_DOOR_OPENING`
- Candidates: run 1 = 3 accepted + 1 duplicate; run 2 = 4 suggested; run 3 = 1 accepted + 3 suggested (12 total)
- Approved package 1 total **3** count; 3 frozen package items
- COUNT measurement 1, no scale calibration
- PlanAuditEvent take-off history retained (`takeoff.candidate.accept` count **6** vs **4** accepted candidate rows)

**FG-012 — LABELED / NON-OPERATING**

- Proposal template `FG-012 UAT Template` (id 1, default)
- Draft proposal `PROP-FG012-UAT-GM` (id 1) from `EST-FG009-UAT-GM` — **not Accepted**; no brand snapshot (Draft)

**FG-017 — LABELED / NON-OPERATING + OPERATING BRAND PROFILE**

- ORG-001 CURRENT Brand Profile **v4** (legal `Brayman Construction Inc.`; customer-facing `Brayman Construction`; address 411 St. John Street; phone empty; logo in `instance/brand_logos/ORG-001/`)
- ORG-001 SUPERSEDED v1–v3 retained as CURRENT-on-save evidence (`FG017-UAT` / `FG017-UAT-POST-ISSUE`)
- `ORG-FG014-UAT` CURRENT v1 — **no** Brayman logo
- `PROP-FG017-UAT-ISSUE` (id 2) **Accepted**; snapshot `ISSUED` phone `FG017-UAT`; totals `$132.94`
- `PROP-FG017-UAT-ACCEPT-DIRECT` (id 3) **Accepted**; snapshot `ACCEPTED` phone `FG017-UAT-POST-ISSUE`
- `PROP-FG017-UAT-ISO` (id 4) Draft on isolation project 4; **no** snapshot
- Estimate `EST-FG017-UAT-ISO`; template `FG-017 UAT Isolation Template`

**FG-014 — LABELED / NON-OPERATING**

- CostItems: `FG014-UAT-MAT` (id 4, Material, linked to `CAL-LUM-2X6-12`), `FG014-UAT-LAB` (5), `FG014-UAT-EQP` (6), `FG014-UAT-SUB` (7), `FG014-UAT-ALL` (8), `FG014-UAT-OTH` (9)
- Isolation org `ORG-FG014-UAT` with Material `FG014-UAT-CROSS` (id 10; unit_cost 999.99; supplier `DO-NOT-LEAK-SUPPLIER-TEXT`) — must not appear in ORG-001 catalogue
- Assembly `FG014-UAT-ASM` (id 1) with component CostItem 4 (read-through `CAL-LUM-2X6-12`); waste 10% on AssemblyItem only

**FG-016 — LABELED UAT / REFERENCE (PRESERVE)**

- Client `Mike Pratt (FG-016 UAT)` (id 5)
- Project `FG-016 UAT — Mike Pratt Coach House` / `FG016-UAT-PRATT` (id 9, ORG-001)
- Location id 6: 2562 Church Street, North Gower, Ontario, Canada — LOCATION COMPLETE; City of Ottawa `CA-ON-OTTAWA`
- PermitProfile id 8: PRELIMINARY_FOUNDATION v1; permit context Additional dwelling/coach house; PRELIMINARY / FOUNDATION ONLY
- PlanDocument id 3 `Pratt-04-01-2026-Signed.pdf`; DrawingRevision A id 2
- Current facts: 13 current (fact 2 superseded); analyses ids 1–3 (v1/v2 stale; **v3 current**); 10 findings each
- Finding-status summary (v3): **PASS 1** (OTT-CH-002 same-lot applicability only) · **VERIFY 3** (OTT-CH-003 dual-compliance; OTT-CH-006 height 6.096 m vs 6.1 m ceiling; OTT-CH-007 ambiguous setback) · **MISSING_INFORMATION 4** (OTT-CH-004 servicing/lot area; OTT-CH-008 septic class; OTT-CH-009 grading; OTT-CH-010 bounded site-plan completeness) · **POTENTIAL_NON_CONFORMANCE 1** (OTT-CH-005 footprint 121.35 m² vs 95 m² ceiling — **advisory only**; not a municipal refusal or variance determination) · **ADDITIONAL_APPROVAL_LIKELY 1** (OTT-CH-001 building-permit application evidence absent) · **NOT_APPLICABLE 0**
- Do **not** convert advisory findings into AHJ / zoning / variance determinations.
- Unsupported synthetics: project 10 Toronto Commercial analysis 4 `RULE_COVERAGE_NOT_AVAILABLE`; project 11 North Gower Garage/accessory analysis 5 `RULE_COVERAGE_NOT_AVAILABLE`
- HTML `/projects/9/permit-report`; PDF `/projects/9/permit-report.pdf`. Advisory only. Not a permit determination.

**FG-015 — LABELED / NON-OPERATING**

- Client `FG015-UAT Isolation Client` (id 4) in `ORG-FG014-UAT`
- Project `FG015-UAT-ISO-OTHER-ORG` / `FG015-ISO-001` (id 4, other-org isolation; no location/profile)
- Project `FG015-UAT-COMPLETE` / `FG015-UAT-C1` (id 5); free-text address `FG015 free-text address keep`; location street later `101 FG015 Civic Street CHANGED`; profiles v1–v3 (v1/v2 stale/recheck; v3 current permit context Renovation; commercial type still New Build)
- Project `FG015-UAT-INCOMPLETE` / `FG015-UAT-I1` (id 6); LOCATION INCOMPLETE / JURISDICTION UNRESOLVED
- Project `FG015-UAT-UNKNOWN` / `FG015-UAT-U1` (id 7); Toronto municipality; complete location; JURISDICTION UNRESOLVED (no Ottawa fallback)
- Project `FG015-UAT-GOWER` / `FG015-UAT-G1` (id 8); North Gower alias → City of Ottawa
- Existing `FG-009 UAT Test` (id 2) received explicit location review: street `50 FG015 Existing Civic`; permit context Garage/accessory; address remains None; commercial type still Renovation
- `FG-010 UAT` (id 3) still has no ProjectLocation / PermitProfile (no auto-backfill)
- Platform seed unchanged: Canada / Ontario / City of Ottawa; aliases include Ottawa, City of Ottawa, North Gower

**FG-013 — LABELED / NON-OPERATING**

- Workbooks/estimates ids 21–24: `FG-013-UAT-recognized-slab.xlsx`, `-b.xlsx`, `.xlsm`, `unknown-adhoc.xlsx`
- Upload attempts 1–7 (INGESTED ×3, QUARANTINED, UNSUPPORTED, FAILED, DUPLICATE)
- Stored bytes under `instance/historical_uploads/ORG-001/<sha256>.xlsx|.xlsm`

No UAT residue is real customer operating data. No archive/delete lifecycle exists yet (**NEEDS FUTURE LIFECYCLE SUPPORT**). Default ORG-001 $65 / 15% GM policies are **OPERATING POLICY**.

### Stranded artifacts

Untracked Git files: **none**. Intended FG-008/009/010 product results are in Git + live DB + governed docs. Gitignored `instance/` DB and synthetic PDFs are expected local UAT storage, not missing Git product.

### Durable-storage checklist

A–J: FG-019 **CLOSED / OPERATIONAL FOR UAT**; FG-018 **CLOSED / OPERATIONAL FOR UAT**; item 10 **COMPLETE**; live current = head `b0c1d2e3f4a5`; full suite **494 passed**; dedicated FG-019 **34**; dedicated FG-018 **37**; API UAT port **5012**; office UAT port **5011**. [ADR-042](adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) **Accepted**. [FG-020](feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) **DRAFT / NOT APPROVED**. **STOP — do not implement BUILD. Do not start Field Web.** Item 11 **governance in progress / NOT AUTHORIZED**. Item 12 **BLOCKED**. Phase D unauthorized. Change Order document family **FUTURE / NOT IMPLEMENTED**.
