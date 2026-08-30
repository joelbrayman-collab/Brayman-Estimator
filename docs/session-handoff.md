# Session Handoff & Review Turnover Package — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | **FG-013 CLOSED / OPERATIONAL FOR UAT**. Material Catalogue architecture **documented** (not implemented; no Feature Gate). ADR-032 **Accepted**. **ADR-033 Accepted** (supplier channel; not implemented). FG-012 CLOSED / OPERATIONAL FOR UAT. ADR-021 **Accepted** (MONITOR not implemented). FG-011 / FG-008 / FG-009 / FG-010 **CLOSED / OPERATIONAL FOR UAT**. |
| Updated | 2026-08-30 |
| Protocol | [docs/governance/review-turnover-protocol.md](governance/review-turnover-protocol.md) — 22-point package |
| Complements | [current-state.md](current-state.md) · [chat-workflow-log.md](chat-workflow-log.md) · [project-state-report.md](project-state-report.md) · [milestones.md](milestones.md) |

Authority order for the next session: repository governance → current-state records → accepted ADRs / Feature Gates → implementation/migration/test evidence → conversation memory only as supplementary context.

**PRESERVE → SEARCH → VERIFY → EXECUTE.** Existing before new. No unauthorized redesign. No arbitrary policy invention. No context-drift changes. ChatGPT / Cursor memory is never corporate memory.

---

## 1. PROJECT / REPOSITORY

- **Product:** CalibAi / Brayman Estimator (The Estimator). Do not rename.
- **Path:** `/Users/joelbrayman/Desktop/Brayman-Estimator` (`~/Desktop/Brayman-Estimator`)
- **Environment:** local Flask office app; SQLite development/UAT DB (`sqlite:///brayman_estimator.db` → `instance/brayman_estimator.db`)
- **Chat titles:** must start with `BRAYMAN — <Topic>`

## 2. VERIFIED BASELINE

- Branch: `main`
- Starting HEAD / `origin/main` for this architecture-docs pass: `450cd39dea24c3e41d32defa39e9e74c00ae7c6d` (`docs: close FG-013 live migration and UAT`)
- This Material Catalogue architecture-docs commit is current after push — verify with `git log -1`
- Alembic graph head: **`c5d6e7f8a9b0`**. Live `flask db current`: **`c5d6e7f8a9b0`** (**VERIFIED APPLIED**; one graph head). Migration was **not** run by the reconciliation/UAT pass.
- Chain: `e1b2c3d4e5f6` → `f2c3d4e5f6a7` (FG-008) → `a3b4c5d6e7f8` (FG-009) → `b4c5d6e7f8a9` (FG-010) → `c5d6e7f8a9b0` (FG-013; live-applied before reconciliation)
- Tests (2026-08-30 FG-013 close): dedicated historical upload **27**; historical ingestion **11**; labour **25**; pricing **33**; full suite **310 passed**.
- Working tree: clean after this implementation commit/push
- Real external AI provider **NOT AUTHORIZED**. Phase D **NOT STARTED**.

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

FG-008 / FG-009 / FG-010 / FG-011 / FG-012 / **FG-013** files: **CLOSED / OPERATIONAL FOR UAT**. [ADR-032](adr/ADR-032-app-managed-historical-workbook-storage.md) **Accepted**. [ADR-033](adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted** (architecture only). ADR-010 **Proposed**. **ADR-021 Accepted** (MONITOR not implemented). Do not bulk-accept remaining Proposed ADRs.

## 4. APPROVED PRODUCT VISION

PLAN → PRICE → CONTRACT → BUILD → MONITOR → LEARN on one `Project`. No rename. Office and field complementary. CalibAi owns methodology; each organization owns commercial intelligence. Brayman Construction is `ORG-001`, not the universal CalibAi default.

## 5. CURRENT CALIBAI LIFECYCLE STATE

- **ORGANIZATION:** implemented (M011)
- **HISTORICAL EVIDENCE:** Phase B implemented (FG-006)
- **PLAN:** partial — M005–M010 implemented; **M012 / FG-010 foundation CLOSED / OPERATIONAL FOR UAT**; Phase D mapping **NOT STARTED**
- **PRICE:** partial — builder + commercial gate; Labour Engine Phase B **CLOSED / OPERATIONAL FOR UAT**; Pricing Engine **CLOSED / OPERATIONAL FOR UAT**; FG-012 internal breakdown + Proposal consistency **CLOSED / OPERATIONAL FOR UAT**
- **CONTRACT:** partial (proposals are the customer-facing estimate; FG-012 reconciles snapshot totals; Ontario templates future)
- **BUILD:** partial (change orders; field capture future)
- **MONITOR:** future implementation (ADR-021 **Accepted**; composed frozen baseline; Project Gross Margin; not coded)
- **LEARN:** future (ADR-024 boundary accepted; no ML)

## 6. COMPLETED CODED MILESTONES

M001, M005, M007, M008 (docs), M009 (`5dc4b09`), M010 (`6b969fe`), M011 (`cb38d93`), FG-006 (`690d755`), FG-008 (`0569f25`; integrity `ff5d856`), FG-009 (`8e11179`; not a numbered M0xx), **M012 / FG-010** (`9665295`; live-migrate docs `316cc9f`).

## 7. CURRENT MILESTONE

**FG-013 CLOSED / OPERATIONAL FOR UAT.** Live current=head `c5d6e7f8a9b0`. [Material Catalogue architecture](architecture/material-catalogue-architecture.md) **documented** (not implemented). [ADR-032](adr/ADR-032-app-managed-historical-workbook-storage.md) **Accepted**. [FG-012](feature-gates/FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT**.

## 8. LAST AUTHORIZED DELTA

This session: **Material Catalogue architecture governance** (docs only). Canonical materials are CalibAi-seeded; CostItem is not identity; living supplier evidence (prices, promotions, inventory) is not the identity row; first FG identity-only; Phase D after identity; ADRs next. No Feature Gate. No product code. Tests not rerun.

Prior: FG-013 **migration-state reconciliation + UAT closure**. Live DB was **already** at `c5d6e7f8a9b0`. **ADR-033 Accepted**.

## 9. IMPLEMENTATION STATUS

- Labour Engine: `LabourTask`, `LabourTaskMapping`, `ProductionRateStandard`, `DirectLabourCostRateStandard`, `LabourCalibrationCandidate`, `EstimateLabourSnapshot`, `LabourAuditEvent`. Office `/labour-engine/`.
- Pricing Engine: `OrganizationPricingPolicy`, `EstimatePricingSnapshot`, `PricingAuditEvent`. Methods `TRUE_GROSS_MARGIN` / `COST_PLUS_MARKUP` / `COST_PLUS_MARKUP_STACK`. Office `/pricing-engine/`.
- Take-off: `TakeoffExtractionRun`, `TakeoffCandidate`, `TakeoffPackage`, `TakeoffPackageItem`. Provider-neutral architecture; **`calibai-mock` only**. Office `/projects/<id>/plans/takeoff`. Initial element `INTERIOR_DOOR_OPENING`. COUNT dimensionless (no scale). Linear / polyline / area / perimeter remain scale-governed. Approved package immutable. No automatic estimate insertion.
- Project Hub: `/projects/<id>` (`app/services/project_hub.py`) reads stored facts and links. PLAN / PRICE / CONTRACT operational from stored records; BUILD = existing Change Orders; field BUILD / MONITOR / LEARN Future labels only.
- FG-012: `app/services/estimate_output.py`; `GET /estimates/<id>/versions/<version_id>/internal-breakdown`; named-method proposal snapshot totals from frozen `EstimatePricingSnapshot`; customer PDF Subtotal / Tax / Grand Total.

## 10. TEST / UAT / MIGRATION STATUS

- Live current = `c5d6e7f8a9b0`. Graph head = `c5d6e7f8a9b0`. **VERIFIED APPLIED.** One Alembic head. This pass did **not** upgrade.
- Dedicated: FG-013 upload 27; FG-012 19; Project Hub 13; take-off 18; Plan Intelligence 56; Pricing 33; Labour 25; Historical 11.
- Full suite: **310 passed**.
- Bounded browser UAT: Flask **5004**; labeled `FG-013-UAT-*` mixed six-file + duplicate. No customer operating data.
- Synthetic UAT for FG-008 / FG-009 / FG-010 / FG-012 is in the live development/UAT DB (labeled; not deleted).

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

002, 005, 006, 007, 009, 011, 017, 018, 019, 020, **021**, 022, 023, 024, 025, 026, 027, 028, 029, 030, 031, **032**, **033**.

## 13. PROPOSED / OPEN ADRs

001, 003, 004, 008, **010**, 012–016. **ADR-010 remains Proposed** (OCR, CAD, real external AI provider). Do not bulk-accept.

## 14. FEATURE GATES

- **FG-001:** Draft for Joel approval (preserve)
- **FG-002:** Approved for Phase A (M005 implemented)
- **FG-003:** CONDITIONAL PASS — architecture only
- **FG-004 / FG-005 / FG-006 / FG-007:** APPROVED, IMPLEMENTED & VERIFIED
- **FG-008 / FG-009 / FG-010 / FG-011 / FG-012:** **CLOSED / OPERATIONAL FOR UAT**
- **FG-013:** **CLOSED / OPERATIONAL FOR UAT**. Multi-file UX **LOCKED**. Folder/OS-drag native pickers **not live-browser verified**. ADR-032 **Accepted**. No durable `UploadBatch`. Revision `c5d6e7f8a9b0` live current=head.
- No later gate approved for implementation.

## 15. CHAT → REPOSITORY DELTA LEDGER RESULT

29 Aug conversational decisions for FG-008 / FG-009 / FG-010 architecture, implementation, live migrate, UAT, and integrity stabilization are in Git (pins above) and governed docs. 30 Aug FG-012 is closed; ADR-021 **Accepted**. ADR-033 **Accepted**. This pass **closes FG-013** after verifying live current=`c5d6e7f8a9b0` (applied before this pass) and bounded UAT. Supplier integration is **not started**.

**Completeness test:** Is any material approved fact only in this chat? **NO** after this documentation update.

## 16. OPEN DECISIONS

- Real external AI provider / ADR-010 (not authorized)
- Phase D reviewed quantity → estimate mapping (not started; requires its own gate)
- Project Hub UX (roadmap item 8; **CLOSED / OPERATIONAL FOR UAT**)
- Estimate-output consistency (roadmap item 9 / FG-012; **CLOSED / OPERATIONAL FOR UAT**)
- Actor-string reviewer identity until authentication
- ARCH-only take-off eligibility
- Cancelled extraction-run status modeled; no cancel operation
- ORG-001 optional overhead/profit treatments `UNSPECIFIED`; contingency visibility `UNSPECIFIED`; `contingency_source` / `contingency_pricing_treatment` unset (NULL) — distinct from org-approved `NOT_APPLIED`
- Labour-snapshot Direct Labour Cost not included in estimate basis by default (ADR-021 records the GM comparability issue; does not correct it)
- [FG-013](feature-gates/FG-013-contractor-calibration-onboarding-historical-upload-ux.md) is **CLOSED / OPERATIONAL FOR UAT**. **LOCKED:** one user action may load many workbooks; no durable `UploadBatch`. Do **not** `flask db upgrade` again.
- [ADR-033](adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted** (docs only). BMR / Winchester / Darcy are **not exclusive**. Winchester is launch/reference. Contractor procurement (A) ≠ CalibAi channel (B). Darcy commercial terms **unset**. Supplier Feature Gate **not authorized**.

## 17. KNOWN RISKS / UNRESOLVED PRODUCT ITEMS

**FG-008 (evidence defects — do not repair as product bugs):** 0.13 hourly-rate cluster (43/120); material SKUs classified as labour; historical crew/duration inconsistencies.

**FG-009 carry-forward:** Optional layers unspecified as above. Labour-snapshot Direct Labour Cost not in estimate basis by default.

**FG-012 residual:** Office proposal create/detail still lists Overhead/Profit amounts (zero when named method governs). Customer preview/PDF do not. Live FG-009 UAT estimates have no Allowance lines and no labour snapshots; dedicated tests cover those cases. Synthetic UAT residue including `PROP-FG012-UAT-GM`.

**FG-010:** 6 `takeoff.candidate.accept` PlanAuditEvent rows vs 4 accepted candidate rows (duplicate submit residue; do not invent a cleanup). Leftover suggested candidates on runs 2–3.

**Platform:** office app authentication not implemented. Unauthenticated office app remains the current operating model.

No product-code defects were opened for repair in this turnover. Do not fix them here.

## 18. DEFERRED ITEMS

Phase D estimate mapping; Crew Template catalog; payroll burden; `LabourActualObservation`; field/mobile; QuickBooks API; Ontario contract/warranty; four-output outputs 3–4; TBD/PLACEHOLDER durable state; OCR/CAD; multi-trade extraction; real external AI provider; BUILD/MONITOR/LEARN **implementation**; supplier / Winchester POC; Darcy channel economics; industry benchmarking; auth; Material Catalogue **ADRs** then Feature Gate (architecture documented; not implemented).

## 19. EXPLICITLY PROHIBITED NEXT ACTIONS

Do not start Phase D. Do not enable an external AI provider. Do not start auth, BUILD/MONITOR/LEARN **implementation**, QuickBooks, or contract/warranty work. Do **not** run `flask db upgrade` again (FG-013 already at `c5d6e7f8a9b0`). Do not treat ADR-021 acceptance as a MONITOR Feature Gate. Do not treat ADR-033 as a supplier Feature Gate or Winchester POC. Do not grant supplier exclusivity. Do not set Darcy percentages. Do not reopen FG-008 / FG-009 / FG-010 / FG-011 / FG-012 / FG-013. Do not insert estimate lines from take-off. Do not create a new document module, Customer Estimate entity, or a second Alembic head. Do not copy Dashboard unscoped counts. Do not rewrite historical labour facts. Do not move/recopy/delete the legacy Desktop corpus. Do not delete synthetic UAT or append-only audit history. Do not implement Material Catalogue. Do not create a Material Catalogue Feature Gate until ADRs are accepted. Do not accept ADR-008 in the identity pass.

## 20. NEXT AUTHORIZED ACTION

**Next governed action:** **Material Catalogue ADRs** (documentation) when separately authorized. Architecture: [material-catalogue-architecture.md](architecture/material-catalogue-architecture.md). Do **not** implement. Do **not** open a Feature Gate yet. Do **not** `flask db upgrade`. Do not start Phase D. **Do not start supplier integration / Winchester POC.** Do not accept ADR-008 in the identity pass.

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

Expected: branch `main`; HEAD = `origin/main`; working tree clean; Alembic graph head **and** live current `c5d6e7f8a9b0`; FG-013 27; FG-012 19; Project Hub 13; take-off 18; Plan Intelligence 56; Pricing 33; Labour 25; Historical 11; full suite **310 passed**. Do **not** `flask db upgrade`.

## 22. FRESH CHAT STARTUP PROMPT

Paste into a new ChatGPT or Cursor conversation:

```text
BRAYMAN — RESUME FROM REVIEW TURNOVER
CONTINUITY / REPOSITORY-FIRST INITIALIZATION

You are resuming work on the Brayman-Estimator (CalibAi / The Estimator) platform following FG-013 **CLOSED / OPERATIONAL FOR UAT** and Material Catalogue **architecture documented** (not implemented; no Feature Gate). Canonical materials are CalibAi-seeded; CostItem is not identity; living supplier evidence is not the identity row.
The prior conversation has been discarded. The repository is the ONE SOURCE OF TRUTH.
The prior conversation has been discarded. The repository is the ONE SOURCE OF TRUTH.
ChatGPT memory is not corporate memory.

Conversation titles in this workspace must start with: BRAYMAN — <Topic>.

1. ANTI-DRIFT PREFLIGHT
Read and comply with:
- AGENTS.md
- docs/platform-constitution.md
- docs/governance/continuity-and-anti-drift.md
- docs/governance/review-turnover-protocol.md
- docs/current-state.md
- docs/project-state-report.md
- docs/session-handoff.md
- docs/platform-roadmap.md
- docs/feature-gates/README.md
- docs/adr/README.md

2. VERIFY BASELINE (Cursor Terminal)
cd /Users/joelbrayman/Desktop/Brayman-Estimator
git status
git branch --show-current
git log -1 --oneline
git rev-parse HEAD
git rev-parse origin/main
./venv/bin/flask db current
./venv/bin/flask db heads

Confirm:
- branch = main
- HEAD = origin/main
- working tree clean
- Alembic current = head = c5d6e7f8a9b0 (one head)

3. CONFIRM TEST BASELINE (if you will change product code later)
./venv/bin/python -m pytest -q
Expected: 310 passed

4. RECONSTRUCT AUTHORITATIVE STATE FROM THE REPO
Independently reconstruct:
- FG-008 / FG-009 / FG-010 / FG-011 / FG-012 CLOSED / OPERATIONAL FOR UAT
- FG-013 CLOSED / OPERATIONAL FOR UAT (graph head and live current c5d6e7f8a9b0; migration verified applied before reconciliation; that pass did not upgrade)
- Material Catalogue architecture documented (docs/architecture/material-catalogue-architecture.md): CalibAi-seeded identity; CostItem is not identity; living supplier evidence is not the identity row; not implemented; no Feature Gate
- Next docs: Material Catalogue ADRs (not implementation). Do not accept ADR-008 in the identity pass.
- ADR-032 Accepted (app-managed immutable historical workbook custody; legacy Desktop corpus not moved)
- ADR-021 Accepted (composed frozen MONITOR baseline; Project Gross Margin; MONITOR not implemented; no Feature Gate)
- FG-012 internal breakdown + named-method Proposal consistency (Estimating owner; existing Proposal is the customer-facing estimate; outputs 1–2 only; SCHEMA NO)
- M012 AI take-off foundation OPERATIONAL FOR UAT
- FG-011 Project Hub UX CLOSED / OPERATIONAL FOR UAT (evolve /projects/<id> only; no schema)
- Protected ORG-001 labour $65 CAD/man-hour; pricing TRUE_GROSS_MARGIN 15% (Direct Cost / 0.85); Ontario HST 13%; optional OH/profit UNSPECIFIED
- ADR-010 Proposed; real external AI NOT AUTHORIZED
- Phase D NOT STARTED
- Synthetic FG-008 / FG-009 / FG-010 UAT residue is labeled and must not be treated as customer operating data

Do NOT rely on AI memory. Do NOT guess missing product rules.
Do NOT start Phase D. Do NOT enable external AI.
Do NOT start auth, BUILD / MONITOR / LEARN implementation, QuickBooks, or contract/warranty work.
Do NOT treat ADR-021 as a MONITOR Feature Gate.
Do NOT flask db upgrade FG-013 again (already at c5d6e7f8a9b0).
Do NOT implement Material Catalogue or open its Feature Gate until ADRs are accepted.
Do NOT begin supplier integration or Winchester POC.

PRESERVE → SEARCH → VERIFY → EXECUTE.
Existing before new. No unauthorized redesign. No arbitrary policy invention.
```

---

## Live development/UAT database snapshot (read-only, 2026-08-30)

| Table | Count |
|-------|------:|
| organizations | 1 |
| clients | 3 |
| projects | 3 |
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
| drawing_packages | 1 |
| drawing_revisions | 1 |
| plan_documents | 2 |
| plan_pages | 2 |
| plan_sheets | 1 |
| plan_sheet_pages | 1 |
| plan_sheet_suggestions | 0 |
| plan_scale_calibrations | 0 |
| plan_measurements | 1 |
| plan_audit_events | 41 |
| takeoff_extraction_runs | 3 |
| takeoff_candidates | 12 |
| takeoff_packages | 1 |
| takeoff_package_items | 3 |

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
- Draft proposal `PROP-FG012-UAT-GM` (id 1) from `EST-FG009-UAT-GM` — **not Accepted**

**FG-013 — LABELED / NON-OPERATING**

- Workbooks/estimates ids 21–24: `FG-013-UAT-recognized-slab.xlsx`, `-b.xlsx`, `.xlsm`, `unknown-adhoc.xlsx`
- Upload attempts 1–7 (INGESTED ×3, QUARANTINED, UNSUPPORTED, FAILED, DUPLICATE)
- Stored bytes under `instance/historical_uploads/ORG-001/<sha256>.xlsx|.xlsm`

No UAT residue is real customer operating data. No archive/delete lifecycle exists yet (**NEEDS FUTURE LIFECYCLE SUPPORT**). Default ORG-001 $65 / 15% GM policies are **OPERATING POLICY**.

### Stranded artifacts

Untracked Git files: **none**. Intended FG-008/009/010 product results are in Git + live DB + governed docs. Gitignored `instance/` DB and synthetic PDFs are expected local UAT storage, not missing Git product.

### Durable-storage checklist

A–J: FG-013 **CLOSED / OPERATIONAL FOR UAT**; Alembic current=head `c5d6e7f8a9b0`; Material Catalogue **architecture documented**; next development boundary is **STOP** then **Material Catalogue ADRs**. Phase D unauthorized. Do not `flask db upgrade` again.
