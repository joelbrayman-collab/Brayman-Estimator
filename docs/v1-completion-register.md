# CalibraytAI V1 Completion Register

| Attribute | Value |
|-----------|--------|
| Status | **GOVERNING PRODUCT-COMPLETION INSTRUMENT** (2026-09-11). V1-01 / FG-026 **COMPLETE**. V1-02 / [FG-027](feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) **COMPLETE**. V1-03 / [FG-029](feature-gates/FG-029-bmr-supplier-workflow-v1.md) **COMPLETE** (**CLOSED / OPERATIONAL FOR UAT**). V1-05 / [FG-032](feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) **COMPLETE** (**CLOSED / OPERATIONAL FOR UAT**; Option A). Readiness **60%** (V1-05 factor **1.00**; 55.05 − 0.9 + 6.0 = 60.15 → **60%**). **4 / 11** COMPLETE. BMR DEMO READY **NO**. BRAYMAN REAL-LIFE UAT READY **NO**. [ADR-046](adr/ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) **Accepted**. ADR-008 remains **Proposed**. Does **not** authorize FG-024, FG-030 implementation, or V1-04 product work. [FG-031](feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) **CLOSED / OPERATIONAL FOR UAT** (supporting gate; **not** a 12th package; does **not** rescore). [FG-032](feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) **CLOSED / OPERATIONAL FOR UAT**. FG-028 **CLOSED / OPERATIONAL FOR UAT** (does **not** rescore this register). |
| Product | CalibraytAI / The Estimator (formerly CalibAi) |
| Date | 2026-09-08 |
| Parent SHA | `73253c46b5fcb54a96345107ac49fe1162063369` (`docs: establish CalibAi V1 completion register`) |
| Authority | Completeness of **CalibraytAI V1** as a product outcome. Feature Gates / ADRs remain the implementation-governance mechanism underneath this register. Does **not** replace [platform-roadmap.md](platform-roadmap.md), [current-state.md](current-state.md), Feature Gates, milestones, or module ownership. Current vs former product name: [governance/product-identity.md](governance/product-identity.md). |

```text
CALIBRAYTAI V1 READINESS: 60%

MAJOR PACKAGES:
4 / 11 COMPLETE

CURRENT V1 PACKAGE:
V1-04

CRITICAL PATH:
V1-04
V1-06 (parallel) → Ontario legal approval → V1-07 production for contracts
V1-10 before real Brayman projects
V1-11 last

BMR DEMO READY:
NO

BRAYMAN REAL-LIFE UAT READY:
NO

ROADMAP SEQUENCE ≠ IMPLEMENTATION AUTHORIZATION
THIS REGISTER DOES NOT AUTHORIZE FG-024, FG-030 IMPLEMENTATION, OR V1-04 PRODUCT WORK
FG-031 IS A SUPPORTING GATE — NOT A 12TH MAJOR PACKAGE — DOES NOT RESCORE
FG-032 CLOSED / OPERATIONAL FOR UAT — V1-05 COMPLETE — OPTION A
FG-028 CLOSED / OPERATIONAL FOR UAT — DOES NOT RESCORE THIS REGISTER
```

---

## 1. Governing V1 outcome

CalibraytAI V1 is complete when:

1. all development required for the first **operational** product is complete;
2. CalibraytAI is ready for a **credible end-to-end BMR demonstration**;
3. Brayman Construction can begin entering **REAL** projects and using CalibraytAI as the first real-world operational / UAT organization.

Brayman Construction (`ORG-001`) is the first real-life UAT environment. Ben Brayman and Brayman Construction users must be able to be trained on the tool and operate real projects through the V1 workflow.

V1 is **not** a technical prototype.

```text
V1 MEANS:
BMR DEMO READY
AND
BRAYMAN REAL-LIFE UAT READY
```

Lifecycle is unchanged:

```text
PLAN → PRICE → CONTRACT → BUILD → MONITOR → LEARN
```

Do not rename the lifecycle.

---

## 2. How this register relates to other authority

| Instrument | Role |
|------------|------|
| This register | Top-level **product-completion** definition, package status, weighting, BMR/UAT readiness |
| [platform-roadmap.md](platform-roadmap.md) | Sequence / program direction (**not** implementation authorization) |
| Feature Gates | Implementation authorization, ownership, acceptance |
| ADRs | Durable architecture decisions |
| [current-state.md](current-state.md) / [session-handoff.md](session-handoff.md) | Verified snapshot and immediate resume |
| [project-state-report.md](project-state-report.md) | Milestone-level state |
| [milestones.md](milestones.md) / [chat-workflow-log.md](chat-workflow-log.md) | History |

If this register and a Feature Gate disagree on **implementation authorization**, the Feature Gate wins. If they disagree on **whether a capability is in V1**, this register wins until Joel revises it.

---

## 3. Classification and scoring

### 3.1 Status labels

| Label | Meaning |
|-------|---------|
| **COMPLETE** | V1 package accepted as done in product (tests/docs/UAT as required by its gate) |
| **SUBSTANTIALLY COMPLETE** | Core V1 capability exists; bounded remainder is not the package’s primary remaining work |
| **PARTIAL** | Material product foundation exists; major V1 work remains |
| **ARCHITECTURE COMPLETE / NOT IMPLEMENTED** | Governing architecture/preflight exists; no V1 product capability yet |
| **NOT STARTED** | No meaningful V1 product or architecture for this package |
| **BLOCKED** | Further progress depends on counsel, legal content, or an unresolved Joel decision |
| **POST-V1** | Explicitly outside V1 (must not be silently moved from a V1 commitment) |

### 3.2 Package completion factor (for the 100% rollup)

| Status | Factor applied to package weight |
|--------|----------------------------------|
| COMPLETE | 1.00 |
| SUBSTANTIALLY COMPLETE | 0.75 |
| PARTIAL | 0.40 unless a package table states a different evidence-based factor |
| ARCHITECTURE COMPLETE / NOT IMPLEMENTED | 0.15 |
| NOT STARTED | 0.00 |
| BLOCKED | Score the implemented/architecture portion only; do not treat the blocker as completion |
| POST-V1 | Excluded from the 100% (not a major package) |

Future reports must cite this table. Do not invent a new percentage without updating the package rows.

---

## 4. LEARN at V1 vs post-launch

[ADR-024](adr/ADR-024-learn-recommendation-boundary.md) **Accepted**: early V1 may **capture** structured project results; sophisticated recommendation / ML is later and separately Feature-Gated. LEARN must not silently modify pricing policy, cost library, approved estimates, or historical actuals.

**V1 LEARN minimum (required):** capture the governed evidence needed for later learning and calibration:

- approved take-off packages and citations (PLAN);
- estimate / pricing snapshots (PRICE);
- issued/signed commercial documents when those exist (CONTRACT);
- Field Events / Originals and Change Order records (BUILD);
- estimated-versus-actual MONITOR rows (MONITOR);
- historical workbook evidence already ingested (FG-006 / FG-013).

**V1 does not require:** fabricating years of operating history; ML recommendations; auto-updating the cost book from actuals; industry benchmarking.

Meaningful organization-specific learning **matures during Brayman real-life UAT** as real project history accumulates. That maturation is **not** a V1 launch blocker.

Capture capability today is **SUBSTANTIALLY COMPLETE**. Recommendation/ML remains **POST-V1**.

---

## 5. Package inventory (no missing / duplicate major packages)

Joel’s eleven packages are accepted as the V1 major-work set after repository reconciliation.

**Not added as a 12th major package:**

| Capability | Why it is not a major V1 package |
|------------|----------------------------------|
| Permit Intelligence (FG-015 / FG-016) | Ontario/Ottawa POC is **CLOSED / OPERATIONAL FOR UAT**. Supporting PLAN capability. National library is **POST-V1**. |
| Historical ingestion (FG-006 / FG-013) | Closed. Serves LEARN/calibration capture, not a separate V1 outcome. |
| Organization Brand Profile (FG-017) | Closed. Serves customer-document presentation. |
| Project Hub (FG-011) | Closed. Lifecycle shell, not a remaining V1 outcome. |

**Overlaps (do not build twice):**

| Overlap | Rule |
|---------|------|
| V1-04 output 4 ↔ V1-06 | V1-06 **owns** the contract/warranty library and generation. V1-04 tracks four-output **consistency** from one estimate record. |
| V1-04 output 3 ↔ V1-05 | V1-05 **owns** the QuickBooks handoff. V1-04 tracks whether output 3 exists in the package. |
| V1-07 ↔ V1-06 06I | Native Signing is a **separate process track**. Contract signing remains behind the Legal Content Gate. Change Order signing may proceed under separate governance before Ontario templates exist. |

No package from Joel’s list is rejected. No existing August 2026 four-output / Legal Content Gate / Native Signing / BMR launch-partner commitment is moved to POST-V1.

---

## 6. Headline dashboard

| Field | Value |
|-------|--------|
| **CALIBRAYTAI V1 READINESS** | **60%** |
| **MAJOR PACKAGES COMPLETE** | **4 / 11** |
| COMPLETE | **4** (V1-01, V1-02, V1-03, V1-05) |
| SUBSTANTIALLY COMPLETE | **2** (V1-08, V1-09) |
| PARTIAL | **3** (V1-04, V1-06, V1-10) |
| IMPLEMENTED / NOT CLOSED | **0** |
| ARCHITECTURE COMPLETE / NOT IMPLEMENTED | **1** (V1-07) |
| NOT STARTED | **1** (V1-11) |
| **CURRENT V1 PACKAGE** | **V1-04** |
| **CRITICAL PATH** | V1-04; V1-06 parallel; V1-10 before real UAT; V1-11 last |
| **BMR DEMO READY** | **NO** |
| **BRAYMAN REAL-LIFE UAT READY** | **NO** |

Scoring arithmetic is in §8.

---

## 7. Major packages

Weights total **100%** and reflect **remaining business/product significance** for V1 launch (BMR demo + Brayman real-life UAT), not file counts.

### V1-01 — PLAN → PRICE Phase D

| Field | Value |
|-------|--------|
| Intent | Approved / reviewed PLAN quantities become traceable governed estimate items |
| Weight | **10%** |
| Status | **COMPLETE** — live-migrated; bounded office UAT **PASS**; [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **CLOSED / OPERATIONAL FOR UAT** |
| Factor | **1.00** |
| Contribution | **10.0** |
| V1 REQUIRED? | **YES** |
| BLOCKER? | **NO** |
| Dependencies | FG-010 **CLOSED**; existing Draft EstimateVersion + Assembly/CostItem on the same Project |
| Governing | [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **CLOSED / OPERATIONAL FOR UAT**; [fg-026-takeoff-to-estimate-mapping-preflight.md](architecture/fg-026-takeoff-to-estimate-mapping-preflight.md); ADR-005/006/007/011/031 |
| Next governed action | V1-02 / [FG-027](feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) is **COMPLETE / CLOSED / OPERATIONAL FOR UAT**. V1-03 / [FG-029](feature-gates/FG-029-bmr-supplier-workflow-v1.md) is **COMPLETE / CLOSED / OPERATIONAL FOR UAT**. Do **not** implement FG-024 or FG-030 from this register. |

PLAN proposes. Estimating commits. Package approval does **not** insert. Live UAT: TakeoffPackage **id 1** on project **3** mapped to Estimate **id 9** / version **id 9** / line **id 7** (quantity **3** `ea`) with insertion **id 1** and **3** citations. Package 1 **unchanged**. No labour/pricing snapshot, MaterialRequirement, or supplier/SKU from the insert.

### V1-02 — Automated costing + human cost approval

| Field | Value |
|-------|--------|
| Intent | CalibraytAI develops costs from governed organizational commercial intelligence. Human **costing** approval remains required. Mature path: CalibraytAI costs → flags exceptions / low-confidence → estimator reviews → **Approve all costing** → Pricing Engine. |
| Weight | **10%** |
| Status | **COMPLETE** — live-migrated; bounded office UAT **PASS**; [FG-027](feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) **CLOSED / OPERATIONAL FOR UAT** |
| Factor | **1.00** |
| Contribution | **10.0** |
| V1 REQUIRED? | **YES** (human-approved costing before pricing). Exception-based review is **V1 maturation**, not a launch fabricator of history. |
| BLOCKER? | **NO** |
| Dependencies | V1-01 for takeoff-sourced lines; FG-008 / FG-009 / FG-014 foundations |
| Governing | [FG-027](feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) **CLOSED / OPERATIONAL FOR UAT**; [ADR-044](adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) **Accepted**; [fg-027-costing-approval-preflight.md](architecture/fg-027-costing-approval-preflight.md); [FG-008](feature-gates/FG-008-labour-engine-phase-b.md) **CLOSED**; [FG-009](feature-gates/FG-009-organization-calibrated-pricing-engine.md) **CLOSED**; [FG-014](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **CLOSED**; ADR-025/030/034/035/036 |
| Next governed action | V1-03 / [FG-029](feature-gates/FG-029-bmr-supplier-workflow-v1.md) is **COMPLETE / CLOSED / OPERATIONAL FOR UAT**. Next package is V1-04. Do **not** implement FG-024 or FG-030 from this register. |

**Exists live / office-UAT-verified (EstimateVersion id 9):** additive `a5b6c7d8e9f0`; Costing Review; zero-cost BLOCK; legacy NULL-reference freeze (`library_unit_cost_reference` **0.0000**); `MANUAL_OVERRIDE` with reason/actor/time; Approve All snapshot **1 SUPERSEDED 750.00** / **2 CURRENT 780.00**; Pricing consume CURRENT then STALE then re-apply (`EstimatePricingSnapshot` id **6**, `costing_snapshot_id` **2**, TRUE_GM, customer **1036.94**). Labour snapshot **not** in selling-price basis. Supplier evidence not required. Assembly **id 2** and TakeoffPackage **id 1** unchanged. Repair SHA **`72949f99da2b56ec06e95e16e29fa194a6730bbd`**.

**Out of V1-02:** MaterialRequirement; supplier-priced costing; ML confidence; V1-03 / ADR-008.

“Approve all” means **costing** approval only. It does **not** approve takeoff mappings, customer selling price, or bypass commercial validation.

**Joel decision (recorded 2026-09-08 in ADR-044):** V1 ships with **human costing + explicit Approve All Costing before Pricing Engine**. Exception-based review matures during real UAT. Zero/missing CostItem/Assembly commercial cost **BLOCKS**. Manual Custom/Allowance **WARN** if a valid cost is entered. Labour snapshots remain out of default pricing basis. Supplier evidence is not required.

### V1-03 — BMR / supplier workflow V1

| Field | Value |
|-------|--------|
| Intent | Minimum credible demonstration of project requirement → supplier commercial evidence/pricing → estimate. BMR Winchester is first launch/reference supplier. Not a marketplace. |
| Weight | **12%** |
| Status | **COMPLETE** — live-migrated; bounded DEMO Winchester office UAT **PASS**; [FG-029](feature-gates/FG-029-bmr-supplier-workflow-v1.md) **CLOSED / OPERATIONAL FOR UAT** |
| Factor | **1.00** |
| Contribution | **12.0** |
| V1 REQUIRED? | **YES** for BMR demo |
| BLOCKER? | **NO** (V1-03 complete; ADR-008 still **Proposed**; BMR DEMO READY still **NO** pending fail-closed/Ontario contract story) |
| Dependencies | Material Catalogue identity (FG-014 **CLOSED**); V1-01 for requirement traceability; ADR-033 dual relationships |
| Governing | [ADR-046](adr/ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) **Accepted**; [FG-029](feature-gates/FG-029-bmr-supplier-workflow-v1.md) **CLOSED / OPERATIONAL FOR UAT**; [fg-029-bmr-supplier-workflow-v1-preflight.md](architecture/fg-029-bmr-supplier-workflow-v1-preflight.md); [ADR-033](adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted**; [ADR-036](adr/ADR-036-material-commercial-evidence-and-supplier-mapping.md) **Accepted**; [ADR-008](adr/ADR-008-supplier-price-snapshotting.md) **Proposed**; FG-014 identity only |
| Next governed action | **STOP.** V1-03 is **COMPLETE**. FG-028 is **CLOSED / OPERATIONAL FOR UAT**. FG-031 is **CLOSED / OPERATIONAL FOR UAT**. Slice A and Slice B are **OPERATIONAL FOR UAT**. Do **not** implement FG-030. Do **not** begin V1-04 / FG-024 from this close. Do **not** implement subcontract RFQ/package. Return to ChatGPT Architect. |

**V1 minimum (honest BMR demo, not a marketplace):** thin `MaterialRequirement` → human-reviewed DEMO Winchester SKU mapping → inform-only price/availability evidence → frozen Supplier Package HTML+PDF. Live-migrated 2026-09-09. Bounded DEMO/SYNTHETIC UAT **PASS** on project **id 14**. FG-010 remains interior-door count only. Inventory API, EDI, POs, bulk onboarding, other dealers, Darcy channel economics, and supplier-price → estimate cost remain **OUT OF FG-029** / **POST-V1** unless Joel expands V1. Evidence: [fg029-live-migrate-bounded-uat-record.md](testing/fg029-live-migrate-bounded-uat-record.md).

Supplier **named-user login / workspace** is a separate recorded gate: [FG-030](feature-gates/FG-030-supplier-identity-authentication-and-access-isolation.md) **RECORDED / NOT IMPLEMENTATION-AUTHORIZED**; [ADR-047](adr/ADR-047-supplier-identity-authentication-and-access-isolation.md) **Accepted** (architecture only). FG-030 is **not** a 12th major package and does **not** change this factor. FG-029 remains HTML/PDF delivery, not a supplier portal.

**Scope delivery / make-buy routing** is a separate supporting gate: [FG-031](feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) **CLOSED / OPERATIONAL FOR UAT**; [ADR-048](adr/ADR-048-scope-delivery-make-buy-and-procurement-routing-ownership-boundary.md) **Accepted**. FG-031 is **not** a 12th major package and does **not** change this factor or V1 scoring. Do **not** rescore from Slice B UAT.

### V1-04 — Authoritative four-output estimate package

| Field | Value |
|-------|--------|
| Intent | One authoritative estimate record supports: (1) Internal Detailed Cost Breakdown, (2) Customer-Facing Estimate, (3) QuickBooks Estimate / Entry, (4) Contract / execution package |
| Weight | **8%** |
| Status | **PARTIAL** |
| Factor | **0.50** (outputs 1–2 complete; output 3 complete under V1-05 / FG-032 and scored there; output 4 not) |
| Contribution | **4.0** |
| V1 REQUIRED? | **YES** (existing August 2026 commitment) |
| BLOCKER? | Output 4 blocked on V1-06 Ontario legal approval for production |
| Dependencies | FG-012; V1-05 for output 3 (**COMPLETE**); V1-06 for output 4; FG-022 presentation masters; [FG-031](feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) **CLOSED / OPERATIONAL FOR UAT** informs internal delivery class and QuickBooks cost-class split (customer estimate remains delivery-blind); [FG-032](feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) **CLOSED / OPERATIONAL FOR UAT** |
| Governing | [project-document-package.md](architecture/project-document-package.md); [FG-012](feature-gates/FG-012-estimate-output-consistency.md) **CLOSED**; [FG-022](feature-gates/FG-022-reusable-approved-document-template-family-v1.md) **CLOSED** (presentation only) |
| Next governed action | Do **not** begin V1-04 product work from this register. Output 3 is **COMPLETE** under V1-05 / [FG-032](feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) **CLOSED / OPERATIONAL FOR UAT**. Output 4 under V1-06. Do not build a second contract system. |

| Output | Status |
|--------|--------|
| 1 Internal Detailed Cost Breakdown | **COMPLETE** (FG-012) |
| 2 Customer-Facing Estimate (Proposal) | **COMPLETE** as entity (FG-012). Remaining contractor-facing PDF terminology is V1-09. |
| 3 QuickBooks Estimate / Entry | **COMPLETE** under V1-05 / [FG-032](feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) **CLOSED / OPERATIONAL FOR UAT** (Option A controlled pair). Presentation reference (Allen Jacques / Family 04) exists **outside Git**. |
| 4 Contract / execution package | **NOT IMPLEMENTED.** Family 05 is **COMMERCIAL_DRAFT / NOT LEGALLY APPROVED**. |

### V1-05 — QuickBooks V1

| Field | Value |
|-------|--------|
| Intent | Reliable Brayman operational accounting handoff |
| Weight | **6%** |
| Status | **COMPLETE** — live-migrated; bounded office UAT **PASS**; [FG-032](feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) **CLOSED / OPERATIONAL FOR UAT** (Option A) |
| Factor | **1.00** |
| Contribution | **6.0** |
| V1 REQUIRED? | **YES** as four-output item 3. Live API is **not** assumed. |
| BLOCKER? | **NO** for Option A. Option B live API remains **POST-V1**. |
| Dependencies | Approved customer estimate (output 2); CURRENT costing + CURRENT pricing; FG-031 frozen routing for companion class |
| Governing | [quickbooks-integration.md](architecture/quickbooks-integration.md); [project-document-package.md](architecture/project-document-package.md) output 3; [FG-032](feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) **CLOSED / OPERATIONAL FOR UAT**; [ADR-049](adr/ADR-049-quickbooks-ready-output-ownership-and-snapshot.md) **Accepted**; [fg-032-quickbooks-option-a-preflight.md](architecture/fg-032-quickbooks-option-a-preflight.md) |
| Next governed action | **STOP.** V1-05 is **COMPLETE**. Do **not** implement live QuickBooks API. Do **not** begin V1-04 product work from this package. Return to ChatGPT Architect. |

| Option | Repository evidence | Register recommendation |
|--------|---------------------|-------------------------|
| **A.** Governed QuickBooks-ready output / entry workflow | Existing V1 architecture. Human review. No API. [FG-032](feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) **CLOSED / OPERATIONAL FOR UAT**. Slices A+B and Slice C live-migrated / bounded office UAT PASS. | **JOEL SELECTED 2026-09-10.** V1 REQUIRED. **COMPLETE.** |
| **B.** Live QuickBooks Online API | Explicitly **prohibited** until Feature Gate + Joel approval | **POST-V1** unless Joel reverses |

Estimator remains the authoritative commercial record. QuickBooks must not become SoR.

### V1-06 — Jurisdictional contract & warranty library

| Field | Value |
|-------|--------|
| Intent | Architecture and engine to select/generate the governed construction contract/warranty package from project jurisdiction. Ontario operational for Brayman real-life UAT. Not an Ontario one-off. Not every NA jurisdiction populated. |
| Weight | **16%** (major V1 package) |
| Status | **PARTIAL** |
| Factor | **0.25** (jurisdiction identity implemented + FG-024 architecture recorded; no generation, no Ontario legal package) |
| Contribution | **4.0** |
| V1 REQUIRED? | **YES** (06A–06I). 06J **POST-V1**. |
| BLOCKER? | **YES** for production contract use: Legal Content Gate **empty**; Family 05 **NOT LEGALLY APPROVED**; AI cannot mark legal content APPROVED |
| Dependencies | ADR-037 / FG-015 jurisdiction identity; Legal Content Gate; V1-07 for 06I |
| Governing | [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**; [legal-content-and-templates.md](governance/legal-content-and-templates.md) |
| Next governed action | **STOP.** Do **not** implement FG-024 from this register. |

Deep reconciliation: **§9**. Sub-gates: **§9.4**.

### V1-07 — Native Signing + signed Change Order / contract workflow

| Field | Value |
|-------|--------|
| Intent | Native electronic signing of frozen customer documents. Change Orders first. Contract signing later, behind Legal Content Gate. |
| Weight | **8%** |
| Status | **ARCHITECTURE COMPLETE / NOT IMPLEMENTED** (production **BLOCKED** pending counsel process approval) |
| Factor | 0.15 |
| Contribution | **1.2** |
| V1 REQUIRED? | **YES** for signed Change Orders in real Brayman use. Contract signing required for V1 contract execution after 06D. |
| BLOCKER? | **YES** for **production / real customer use**. Development **may proceed** under separate governance. |
| Dependencies | Existing Change Order record (do not create a second entity); frozen PDF snapshot; Legal Content Gate for **contract** signing |
| Governing | [contract-esignature-and-signed-change-order.md](architecture/contract-esignature-and-signed-change-order.md); [native-signing-process-counsel-review.md](legal/native-signing-process-counsel-review.md) **DRAFT FOR ONTARIO COUNSEL REVIEW / NOT LEGAL APPROVAL**; [change-order-document-family.md](architecture/change-order-document-family.md) **FUTURE / NOT IMPLEMENTED** |
| Next governed action | Separate Native Signing Feature Gate when Joel authorizes **development**. Do not enable real customer signing. |

No Native Signing Feature Gate exists yet. Recommendation remains **NATIVE V1** (not DocuSign/Adobe as SoR).

### V1-08 — BUILD V1 / Project Closeout

| Field | Value |
|-------|--------|
| Intent | Minimum remaining BUILD capability for Ben / Brayman to operate a real construction project. Not a Procore replacement. Do not duplicate Field Capture / Field Web. |
| Weight | **7%** |
| Status | **SUBSTANTIALLY COMPLETE** |
| Factor | 0.75 |
| Contribution | **5.25** |
| V1 REQUIRED? | **YES** for operating an active project. Closeout is **V1-desired**; see Joel decision. |
| BLOCKER? | **NO** |
| Dependencies | FG-018/019; FG-020/021; FG-023 actuals |
| Governing | [FG-020](feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) **CLOSED**; [FG-021](feature-gates/FG-021-field-web-v1-today-and-capture.md) **CLOSED**; [FG-023](feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) **CLOSED**; [build-media-storage-lifecycle.md](architecture/build-media-storage-lifecycle.md) |
| Next governed action | Do not start Closeout, Observation Delete, or Field plan-access from this register. |

**Exists:** Field Observation foundation; Field Web Today + Capture (session-expiry recovery **DEFERRED**); Change Order **records**; MONITOR actuals on the Project Hub.

**Remaining (bounded):** Project Closeout / archive-and-purge; Change Order **document family** (frozen snapshot / client presentation); Observation Delete (**QUEUED / NOT AUTHORIZED**); Field plan access (deferred by FG-021).

**Joel decision:** whether Closeout must exist before the **first** real Brayman project, or whether active-project BUILD is sufficient and Closeout may follow during UAT. Register recommendation: **active BUILD is V1-required; Closeout is V1-desired, not a BMR-demo blocker.**

### V1-09 — Contractor / customer UX completion

| Field | Value |
|-------|--------|
| Intent | Bounded commercialization-language work required before BMR demo and real Brayman use |
| Weight | **6%** |
| Status | **SUBSTANTIALLY COMPLETE** |
| Factor | 0.70 |
| Contribution | **4.2** |
| V1 REQUIRED? | **YES** for office/Field language already shipped. Remaining surfaces are **not** automatically V1-required. |
| BLOCKER? | **NO** |
| Dependencies | None beyond existing screens |
| Governing | [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 1–5 IMPLEMENTED / NOT CLOSED**; remaining surfaces **NOT AUTHORIZED** |
| Next governed action | **STOP.** Do **not** start another FG-025 slice from this register. |

Remaining unauthorized candidates: customer Proposal/PDF terminology; Historical Evidence nav/screens; standalone Permit screens; Hub PRICE leftover `TRUE_GROSS_MARGIN`; final product-wide sweep.

**Joel decision:** whether customer Proposal/PDF terminology is **V1-required for BMR demo**. Register recommendation: **YES for BMR** (customer-facing output 2), still requiring a **separate** FG-025 slice prompt.

### V1-10 — Operational hardening / real-project readiness

| Field | Value |
|-------|--------|
| Intent | Minimum security, integrity, backup/recovery, production configuration, onboarding, operating docs, training, error/recovery, and deployment to put **real** Brayman projects into CalibraytAI safely. Not enterprise-scale infrastructure. |
| Weight | **10%** |
| Status | **PARTIAL** |
| Factor | 0.35 |
| Contribution | **3.5** |
| V1 REQUIRED? | **YES** before Brayman real-life UAT (not required for an internal BMR demo on synthetic/UAT data) |
| BLOCKER? | **NO** until real-project entry is attempted |
| Dependencies | FG-018 **CLOSED** (operational for UAT, **not** production-security certification) |
| Governing | [FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md); ADR-041; local `.env` `SECRET_KEY`; SQLite `instance/brayman_estimator.db` |
| Next governed action | Separate operational-readiness prompt. Do not invent hosting/RBAC from this register. |

**Exists:** office login/membership/CSRF; org isolation; SECRET_KEY fail-closed in non-dev; ad-hoc gitignored SQLite copies before some live migrations (not a product backup service); testing standards.

**Missing for real-project V1:** governed backup/restore runbook; production hosting/secrets; user onboarding/training pack; issue/feedback process; SESSION-EXPIRY / session revocation (explicitly **NOT FG-021**); office RBAC (**POST-V1**). Supplier named-user isolation is [FG-030](feature-gates/FG-030-supplier-identity-authentication-and-access-isolation.md) **RECORDED** (principal class, not office RBAC) and is **not** implementation-authorized from this register.

### V1-11 — BMR demo certification + Brayman real-life UAT launch

| Field | Value |
|-------|--------|
| Intent | Final V1 release gate. End-to-end PLAN → PRICE → CONTRACT → BUILD → MONITOR, plus LEARN evidence-capture readiness. |
| Weight | **7%** |
| Status | **NOT STARTED** |
| Factor | 0.00 |
| Contribution | **0.0** |
| V1 REQUIRED? | **YES** |
| BLOCKER? | Depends on packages above |
| Dependencies | V1-01 through V1-10 to the V1-required bar |
| Governing | This register §§10–11 |
| Next governed action | After critical-path packages are complete. Not now. |

---

## 8. Weighted readiness arithmetic

| ID | Weight | Factor | Contribution |
|----|--------|--------|--------------|
| V1-01 | 10 | 1.00 | 10.0 |
| V1-02 | 10 | 1.00 | 10.0 |
| V1-03 | 12 | 1.00 | 12.0 |
| V1-04 | 8 | 0.50 | 4.0 |
| V1-05 | 6 | 1.00 | 6.0 |
| V1-06 | 16 | 0.25 | 4.0 |
| V1-07 | 8 | 0.15 | 1.2 |
| V1-08 | 7 | 0.75 | 5.25 |
| V1-09 | 6 | 0.70 | 4.2 |
| V1-10 | 10 | 0.35 | 3.5 |
| V1-11 | 7 | 0.00 | 0.0 |
| **Total** | **100** | | **60.15 → 60%** |

Round the published readiness to the **nearest whole percent**. Recalculate from this table when a package status changes. Do not average Feature Gate counts.

---

## 9. V1-06 Contract Library — deep reconciliation

### 9.1 What is already governed?

| Question | Answer |
|----------|--------|
| 1. Contract-library architecture | [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) records one linked gate: Slice A library, Slice B update engine, Slice C generation + frozen snapshot, Slice D change monitoring. **RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED.** |
| 2. Legal Content Gate | [legal-content-and-templates.md](governance/legal-content-and-templates.md) remains approval authority. Register **empty**. AI **cannot** independently set legal content to APPROVED. Versions are superseded, not silently overwritten. |
| 3. Four-output home | Output 4 in [project-document-package.md](architecture/project-document-package.md). FG-012 does **not** own it. |
| 4. Native Signing | Separate process track. Production blocked pending counsel. Development may proceed under separate governance. |
| 5. Presentation | [FG-022](feature-gates/FG-022-reusable-approved-document-template-family-v1.md) Family 05 is an **APPROVED REUSABLE PRESENTATION MASTER** only — **COMMERCIAL_DRAFT / NOT LEGALLY APPROVED / NOT FOR EXECUTION**. |
| 6. Jurisdiction identity | **Reusable.** [ADR-037](adr/ADR-037-project-location-and-jurisdiction-resolution.md) **Accepted**; [FG-015](feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **CLOSED**. One resolver. Permit rules (ADR-038) are **not** contract clauses. |
| 7. Frozen snapshot pattern | ADR-002 (accepted proposals); ADR-039 (permit reports); FG-024 records the CONTRACT analogue. **Not implemented** for contracts. |
| 8. Update / monitoring | FG-024 Slice B + D **recorded**, not implemented. Effective-date fields are specified (source publication ≠ counsel approval ≠ platform activation ≠ generation). |
| 9. Fail-closed | FG-024: no approved package / unsupported jurisdiction / unresolved effective-date → **FAIL CLOSED**. **No generic North American fallback.** |

### 9.2 FG-024 pieces vs V1

| FG-024 slice | V1 vs post-V1 |
|--------------|----------------|
| A — Jurisdictional Legal Content Library (schema/engine + Ontario population) | **V1 REQUIRED** (engine + Ontario). Other jurisdictions **POST-V1** (06J). |
| B — Contract Update Engine (candidate → counsel → new version → effective date) | **V1 REQUIRED** at **manual/counsel-driven** update + supersession. |
| C — Generation + frozen snapshot | **V1 REQUIRED** |
| D — Automated legal-source monitoring / alerts | **JOEL DECISION.** Register recommendation: **POST-V1**. V1 can ship with human/counsel-initiated updates (Slice B without live watchers). Do **not** treat this as dropping 06H: effective-date / supersession remain V1. |

**Do not implement FG-024 from this register.**

### 9.3 Ontario contract / legal blockers

| Blocker | Production effect |
|---------|-------------------|
| Legal Content Gate empty | No production contract/warranty templates |
| Family 05 **COMMERCIAL_DRAFT / NOT LEGALLY APPROVED** | Presentation only; not for execution or Native Signing |
| AI cannot mark legal content APPROVED | Counsel/human approval required |
| Native Signing production blocked pending counsel **process** approval | Separate from template approval; both required for signed Ontario contracts |

**What can be developed before counsel approval:** FG-024 Slices A–C **engine** (empty library, fail-closed); Native Signing **development** (Change Order first); jurisdiction reuse; frozen-snapshot plumbing.

**What remains blocked:** populating Ontario legal language; marking content APPROVED; generating executable contracts; real-customer signing; Native Signing production activation.

### 9.4 Sub-gates 06A–06J

| ID | Name | V1 REQUIRED? | Status | Notes |
|----|------|--------------|--------|-------|
| 06A | Contract library architecture / engine | **YES** | **ARCHITECTURE COMPLETE / NOT IMPLEMENTED** | FG-024 Slice A recorded |
| 06B | Project jurisdiction → correct legal package | **YES** | **PARTIAL** | Identity/resolver **COMPLETE** (FG-015). Package **selection** not implemented. |
| 06C | Versioned contract/warranty content + provenance/approval states | **YES** | **ARCHITECTURE COMPLETE / NOT IMPLEMENTED** | Legal Content Gate states + FG-024 library states recorded |
| 06D | Ontario approved contract + warranty package | **YES** | **BLOCKED** | Counsel/legal approval. Empty register. |
| 06E | Contract generation from approved project/estimate | **YES** | **NOT STARTED** | FG-024 Slice C |
| 06F | Frozen generated-contract snapshot | **YES** | **ARCHITECTURE COMPLETE / NOT IMPLEMENTED** | Pattern exists elsewhere; not for contracts |
| 06G | Fail-closed when approved jurisdiction package unavailable | **YES** | **ARCHITECTURE COMPLETE / NOT IMPLEMENTED** | Specified; not coded |
| 06H | Effective-date / supersession / update architecture | **YES** | **ARCHITECTURE COMPLETE / NOT IMPLEMENTED** | V1 = versioning + supersession + effective dates. Live source monitoring = recommended POST-V1 |
| 06I | Contract package → Native Signing handoff | **YES** | **ARCHITECTURE COMPLETE / NOT IMPLEMENTED** | Depends on V1-07; production blocked |
| 06J | Additional province/state population | **NO** | **POST-V1** | Unless Joel names another launch jurisdiction |

Canada (provinces/territories) and United States (states) remain the commercial destination architecture. Adding a jurisdiction must extend the library **without product redesign**.

---

## 10. BMR demonstration — minimum definition

The BMR demo must show CalibraytAI as an **integrated contractor platform**, not a slide deck of screens.

### 10.1 In the minimum demo

| Step | V1 package | Current |
|------|------------|---------|
| Project setup (ORG-001, location, commercial context) | supporting / V1-10 | **EXISTS** |
| Plan ingestion + sheet/review | PLAN foundation | **EXISTS** (M005–M010) |
| Takeoff / quantity evidence | FG-010 | **EXISTS** (mock extractor; interior-door count) |
| Map approved quantities → estimate | V1-01 | **COMPLETE** (FG-026 **CLOSED / OPERATIONAL FOR UAT**) |
| Estimate creation on the same project | PRICE | **EXISTS** (manual builder) |
| Costing from org commercial intelligence | V1-02 | **COMPLETE** (human costing + Approve All before Pricing; exception-based review is maturation) |
| Supplier / BMR relationship | V1-03 | **COMPLETE / CLOSED / OPERATIONAL FOR UAT** |
| Pricing Engine apply | FG-009 | **EXISTS** (separate human action) |
| Customer estimate | V1-04 output 2 | **EXISTS** |
| QuickBooks-ready entry (Option A) | V1-05 / V1-04 output 3 | **EXISTS** ([FG-032](feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) **CLOSED / OPERATIONAL FOR UAT**) |
| Contract package (Ontario) | V1-06 / V1-04 output 4 | **NOT IMPLEMENTED** (presentation draft only) |
| Field capture | V1-08 | **EXISTS** |
| Actual cost + MONITOR | FG-023 | **EXISTS** |
| Traceability / audit | ADR-005/002/039/023 | **PARTIAL** (PLAN/PRICE/BUILD/MONITOR; not CONTRACT) |

### 10.2 Not required to inflate the BMR demo

- Live QuickBooks API
- Every NA contract package
- CAD / real external AI
- National permit library
- Supplier marketplace / PO / inventory API
- Project Closeout
- LEARN recommendations
- Observation Delete
- Session revocation
- Customer Proposal/PDF polish **unless** Joel confirms it is in the demo script (recommended in)

**BMR DEMO READY = NO.** V1-01 exists, V1-02 exists, V1-03 Winchester slice exists, V1-05 Option A exists, and [FG-031](feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) is **CLOSED / OPERATIONAL FOR UAT**. Remaining independent blocker: a **fail-closed or Ontario** contract story that does not pretend Family 05 is legally approved. ADR-008 remains **Proposed**. FG-032 close does **not** flip this to YES.

A demo that only shows takeoff + manual estimate + Field + MONITOR is a **partial platform tour**, not BMR demo-ready under this register.

---

## 11. Brayman real-life UAT — minimum release criteria

Real-life UAT means V1 is complete and controlled enough to operate **real Brayman projects**. It does **not** mean all future development is done.

| Criterion | V1 bar | Current |
|-----------|--------|---------|
| Data safety / tenant integrity | Org isolation; no cross-org writes | **PARTIAL** (UAT-operational; not production-certified) |
| Migration state | Live current = heads; known residue labeled | **YES** (`f1a2b3c4d5e6 (head)`; labeled synthetics remain including `FG029-UAT-BMR-DEMO`, `FG031-UAT-SCOPE-ROUTING`, Slice B project **id 25**, and FG-032 project **id 26**) |
| Backups | Governed backup/restore before real projects | **NO** (ad-hoc gitignored copies only) |
| Authentication | Office login; SECRET_KEY not the committed dev secret | **UAT YES / production not certified** |
| User onboarding + Ben/Brayman training | Written operating/training pack | **NO** |
| Real project creation | CRM + Hub + location | **YES** |
| Estimate workflow | V1-01 + V1-02 + FG-009 | **YES** (V1-01 **COMPLETE**; V1-02 **COMPLETE**; FG-009 **CLOSED**). Real-life UAT still **NO** pending V1-10 / legal / V1-11 |
| Customer-document workflow | Output 2; branded Proposal | **YES** (FG-012/017). Remaining PDF language = V1-09 decision |
| Contract / legal safety | Fail-closed unless Ontario package APPROVED | **FAIL-CLOSED by absence** (cannot lawfully generate) |
| BUILD / Field | Capture + office observations | **YES** (FG-020/021) |
| Actual costs + MONITOR | FG-023 | **YES** |
| Recovery / error handling | Documented; session-expiry still deferred | **PARTIAL** |
| Known limitations | Published to operators | **THIS REGISTER** (initial) |
| Feedback / issue process | Named path to Joel/ChatGPT | **NO** (needs V1-10) |

**BRAYMAN REAL-LIFE UAT READY = NO.**

Do not enter real Brayman commercial projects until V1-10 backup/onboarding, V1-01, legal fail-closed (or Ontario 06D), and V1-11 certification pass.

Labeled synthetic UAT residue (FG-008 through FG-023) must remain labeled and must not be confused with real projects.

---

## 12. Post-V1 boundary

Do **not** block V1 on:

- all 50 U.S. state contract packages
- all Canadian provinces/territories beyond Ontario (unless Joel adds a launch jurisdiction)
- mature autonomous LEARN / ML
- broad external AI / OCR / CAD-first
- national Permit Rules library
- every supplier; supplier marketplace; bulk onboarding; Winchester-beyond-reference
- enterprise RBAC; org-switcher; invitations; SSO
- full enterprise infrastructure / multi-region hosting
- live QuickBooks API (unless Joel chooses option B)
- Field PWA / native iOS / transcription
- MONITOR remainder (forecast-final GM, cost-to-complete, Field Web MONITOR)

**Not moved to POST-V1** (existing V1 commitments):

- four-output package (output 3 **COMPLETE** under V1-05; output 4 remains in V1)
- Ontario contract/warranty **package** (06D)
- Native Signing **production** after counsel (V1-07)
- BMR Winchester **minimum workflow** (V1-03)
- PLAN → PRICE mapping (V1-01)

---

## 13. Unresolved Joel decisions

| # | Decision | Register recommendation |
|---|----------|-------------------------|
| 1 | QuickBooks V1 = A (output/entry) vs B (live API) | **SELECTED (2026-09-10): A now; API POST-V1.** [FG-032](feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) **CLOSED / OPERATIONAL FOR UAT**. V1-05 **COMPLETE**. |
| 2 | Exception-based CalibraytAI costing required before BMR? | **RECORDED (ADR-044 / FG-027).** **No.** Human costing + explicit Approve All Costing is V1; exception-based matures in real UAT |
| 3 | FG-024 Slice D live legal-source monitoring in V1? | **POST-V1.** Keep 06H versioning/supersession/effective-date in V1 |
| 4 | Customer Proposal/PDF FG-025 remainder in BMR demo? | **Yes**, via a later bounded slice |
| 5 | Project Closeout before first real project? | **No** for BMR; **V1-desired** before long-running real UAT |
| 6 | Any launch jurisdiction besides Ontario? | **No** unless named (06J stays POST-V1) |
| 7 | Native Signing **development** now vs wait for counsel? | Architecture already: **development may proceed**; **production blocked** |

---

## 14. Future development-report block

Copy this block into later implementation reports and fill from this register:

```text
CALIBRAYTAI V1 READINESS: 60%

MAJOR PACKAGES:
4 / 11 COMPLETE

CURRENT V1 PACKAGE:
V1-04

CRITICAL PATH:
V1-04
V1-06 parallel
V1-10 before real UAT
V1-11 last

BMR DEMO READY:
NO

BRAYMAN REAL-LIFE UAT READY:
NO
```

---

## Related

- [platform-roadmap.md](platform-roadmap.md)
- [current-state.md](current-state.md)
- [feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md)
- [feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md)
- [feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md](feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md)
- [adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md](adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md)
- [governance/legal-content-and-templates.md](governance/legal-content-and-templates.md)
- [architecture/project-document-package.md](architecture/project-document-package.md)
- [architecture/CAR-001-calibai-product-architecture-reconciliation.md](architecture/CAR-001-calibai-product-architecture-reconciliation.md)
- [feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md](feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md)
- [adr/ADR-048-scope-delivery-make-buy-and-procurement-routing-ownership-boundary.md](adr/ADR-048-scope-delivery-make-buy-and-procurement-routing-ownership-boundary.md)
