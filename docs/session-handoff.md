# Session Handoff & Review Turnover Package — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | **OFFICIAL V1 RESCORE 65% / 4 OF 11 COMMITTED.** Secondary Functional V1 Build **79% / 22 of 28** (labelled secondary; not averaged). Company/Management access-domain seam **DEFINED / NOT IMPLEMENTED.** FG-037 **NOT YET IMPLEMENTED** (stashed WIP is **not** product). **FG-035 PERF-C DEFINED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED.** PERF-B **SEALED**. PERF-A **SEALED**. V1 DESKTOP CONTRACTOR EXPERIENCE / CONTEXT-AWARE HOME OFFICE **RECORDED / ORGANIZATION SCALE RECORDED / NOT IMPLEMENTED.** SCH-D **IMPLEMENTED / TESTED / SERVER-SIDE LIVE UAT PASS / PHYSICAL IPHONE UAT PASS / COMMITTED / SHA-PINNED / PUSHED.** SCH-C **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS.** SCH-B **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS.** SCH-A **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS.** TIME **IMPLEMENTED / LIVE-MIGRATED / SYNTHETIC UAT PASS.** [FG-035](feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) **OPEN / PARTIAL**. TAX/WBS **IMPLEMENTED**. SCOPE **IMPLEMENTED**. TIME **IMPLEMENTED**. SCH overall **OPEN / PARTIAL**. CLOSE / LEARN / QB-T **NOT AUTHORIZED**. Platform-wide **warning law** **INFORMATIONAL ONLY / NON-BLOCKING**. Print **RECORDED / IMPLEMENTATION SEQUENCED LATER**. [ADR-053](adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**. [ADR-041](adr/ADR-041-user-membership-and-office-authentication.md) Decision 4 **narrowly amended** 2026-09-17. Repository Alembic head **`f9b0c1d2e3f4`**. Live current **`f9b0c1d2e3f4`**. Help / Voice / User Manual remain **FUTURE / RECORDED / NOT IMPLEMENTED**. [FG-034](feature-gates/FG-034-account-recovery-and-transactional-email.md) **CLOSED / OPERATIONAL FOR UAT**. Live Postmark **DEFERRED**. **FG-033 CLOSED / OPERATIONAL FOR UAT**. EST-2026-0019 untouched. PRODUCTION packages **0**. CalibraytAI V1 readiness **65%**. **4 / 11** COMPLETE. BMR DEMO READY **NO**. BRAYMAN REAL-LIFE UAT READY **NO**. |
| Updated | 2026-09-17 |
| Protocol | [docs/governance/review-turnover-protocol.md](governance/review-turnover-protocol.md) — 22-point package |
| Complements | [current-state.md](current-state.md) · [v1-completion-register.md](v1-completion-register.md) · [chat-workflow-log.md](chat-workflow-log.md) · [project-state-report.md](project-state-report.md) · [milestones.md](milestones.md) |
| Active ChatGPT development chat title | **BRAYMAN — CALIBRAYTAI DEVELOPMENT 17 SEP 2026** |

Authority order for the next session: repository governance → current-state records → accepted ADRs / Feature Gates → implementation/migration/test evidence → conversation memory only as supplementary context.

**ALL-CHAT TURNOVER:** After this package is committed, every active CalibraytAI development chat may be abandoned. A new chat has **zero reliable conversation memory**. Chat history is supplemental only. No new chat may continue from a pasted old Cursor prompt without first running the required repository preflight/review.

**PRESERVE → SEARCH → VERIFY → EXECUTE.** Existing before new. No unauthorized redesign. No arbitrary policy invention. No context-drift changes. ChatGPT / Cursor memory is never corporate memory.

```text
ACTIVE CHAT TITLE:
BRAYMAN — CALIBRAYTAI DEVELOPMENT 17 SEP 2026

CONTINUITY DISPLAY RULE:
Every CalibraytAI development response begins with the exact active ChatGPT
development chat title in bold and ends with:

END — <exact active chat title>

When a Cursor prompt is present, the END line follows the complete prompt.
Every CalibraytAI development response ends with the next complete ready-to-paste
Cursor prompt unless Joel explicitly says no prompt is required.
```

Canonical rule: [governance/continuity-and-anti-drift.md](governance/continuity-and-anti-drift.md#chat-title-continuity-convention-permanent). Cursor/IDE workspace titles remain `BRAYMAN — <Topic>`.

---

## 1. PROJECT / REPOSITORY

- **Product:** CalibraytAI / Brayman Estimator (The Estimator). Formerly CalibAi. Do not confuse with office chrome (Brayman Construction Platform) or tenant Brand Profile.
- **Path:** `/Users/joelbrayman/Desktop/Brayman-Estimator` (`~/Desktop/Brayman-Estimator`)
- **Environment:** local Flask office app; SQLite development/UAT DB (`sqlite:///brayman_estimator.db` → `instance/brayman_estimator.db`)
- **ACTIVE CHAT TITLE:** `BRAYMAN — CALIBRAYTAI DEVELOPMENT 17 SEP 2026`
- **Cursor / IDE workspace chat titles:** must start with `BRAYMAN — <Topic>`

## 2. VERIFIED BASELINE

- Branch: `main`
- FG-017 close SHA: `620dec1a9612e87a1ede20cfa6aa46c6d72a8dd5` (`docs: close FG-017 live migration and office UAT`). Docs-reconciliation content: `dd30d752190e56ed687e270950df9bf9a06d7a26`. SHA-pin: `07cb46c501d968542dff567943044dc1db870f01`. Implementation parent `00ca492e28118d75757e9a9c82384978b5decd92`. FG-016 close `fa591f14b2eb99db75c4e3720fdeb30d14a8f77a`.
- FG-016 implementation commit: `a709829d32d94ab2baf36f142ad0095254ba3d3a` (`feat: implement FG-016 Ontario Ottawa Permit Intelligence POC`)
- FG-032 Slices A+B product SHA **`70e571140e12377aa5bd009b598530576401113b`** (`feat: implement FG-032 QuickBooks-ready artifacts`). Product parent / architecture errata **`010f6d641a756ceb2ab67475a284d3b8426c7b20`** (`docs: correct FG-032 Issued vs Accepted freeze`). Architecture **`93773820e410e327cd81919172c49a6f661def9e`** (`docs: define V1-05 QuickBooks Option A`). Docs pin **`9c254a38c39ef866cad3c5aca1f01cae4907f376`** (`docs: pin FG-032 Slices A+B SHA`). FG-031 Slice B UAT start pin **`314ced5699688a329dbdd7ab2484ef552dd447db`**. FG-031 Slice B product SHA **`5e1082af68e0eb145d9da01c0fa26585f6b8b9d1`** (`feat: implement FG-031 subcontract quote evidence`). Slice B UAT close **`8629f0459e51a94ee42cb475a536570cfbc21639`**. FG-031 docs close **`1a473d15c4cefb99a519f0b797f1772844206074`**. Start pin **`0d98b87112e8dda3537fe125d25f0737212bfe1c`**. FG-031 Slice A live-migrate/UAT close **`b50b0dcd1ea24f1a37ed32d04325ce09127fd203`**. Product SHA **`54120608df98432b9be80faf8c2a3a08cdb5679c`** (`feat: implement FG-031 scope delivery routing`). Confirmation-gate repair **`ec8dcf35f0da109b75422504e1a104c1623d186c`**. Start pin **`bbe22f2a10ba9ba827e50c92688774a025b95d34`**. FG-031 architecture SHA **`1c6c8c492b92f11cc80ad1b6e8689f0e42523bcd`** (`docs: record scope delivery routing architecture`). FG-028 Slice 3 product SHA **`502035fa70ced1d0ff042db3077cc66f50e68de4`** (`feat: install approved CalibraytAI product logo assets`). FG-029 close SHA **`880697a246de7e901a81f89584168a9a9fb1dd67`** (`docs: reconcile FG-029 close and current authority`). FG-029 product SHA **`ee578dcb5a688842ebedaff0682131826e6c7188`** (`feat: implement FG-029 BMR supplier workflow`). Parent architecture pin **`a077ba9f30c5925542fdf2663081f60a10241066`**. FG-029 architecture SHA **`07039c8dabfeba7b6ef4714d2cee50abf648bc4f`** (`docs: record V1-03 BMR supplier workflow architecture`). Parent FG-028 pin **`b8d74a4cbe2e25d2fce795cdb15aab7b4f76cc8f`** (`docs: pin FG-028 Slices 1-2 SHA`). FG-028 Slices 1–2 SHA **`e06fa92c4543ae641ba5067b1d277af048d97139`** (`feat: transition current product identity to CalibraytAI`). Parent pin **`3e15aeea065f74aae2a9036e1709ae5e76948e4e`**. FG-027 close SHA **`c348bcfb41daead674aaf75050fc0a6847a8c0c0`**. Parent pin **`cf282bc6ea5cb8c917b9bae052c84a31cae65445`**. FG-027 repair docs SHA **`020bb55cfb87222ed6dfb1b6fd6770f3b0e3b6be`**. FG-027 legacy override-provenance repair SHA **`72949f99da2b56ec06e95e16e29fa194a6730bbd`** (`fix: preserve FG-027 legacy override provenance`). FG-027 live-migrate / first-UAT-stop SHA **`3bf832b2fea5e1ade8c3e412dc7635a4a15c42b1`**. Pin **`db43d54e57a884de491cffa3bcda9119efde0c7a`**. FG-027 product SHA **`c751d72b32f1ed415375719df2fd69936ace64d7`** (`feat: implement FG-027 costing approval`). Start pin **`28fb5c0445fafabb2924d5d43bce46bf5fca3d0e`**. FG-026 product SHA **`aa4c71800586e0b8e2a63931bcdc8bc44d87a489`** (`feat: implement FG-026 takeoff-to-estimate mapping`). Parent **`73253c46b5fcb54a96345107ac49fe1162063369`** (`docs: establish CalibAi V1 completion register`). Slice 5 product SHA **`5b497905086554214e85f69afd8101d88f89161c`** (`feat: continue FG-025 contractor-facing Field Web language`). Parent **`0ed4d67282551d75b4204e33d367f3f3baba023a`** (`docs: reconcile FG-025 Slice 4 close record`). Slice 4 product SHA remains **`56e16f03446f982d577d2a3f0d3375ef865e1dc9`**. Slice 3 product SHA remains **`071f5f923515c6405298bf96b0af249a20f81358`**.
- Alembic graph head (repository): **`f9b0c1d2e3f4`**. Live `flask db current`: **`f9b0c1d2e3f4 (head)`**. SCH-C **`f9b0c1d2e3f4` applied live** 2026-09-16. SCH-B **`f7f8a9b0c1d2`** is superseded as live current. SCH-A **`f6e7f8a9b0c1`** is superseded as live current. FG-035 TIME **`f5d6e7f8a9b0` applied live** 2026-09-15 (superseded as live current). FG-035 SCOPE **`f4c5d6e7f8a9` applied live** 2026-09-15. FG-035 TAX/WBS **`f3b4c5d6e7f8` applied live** 2026-09-15. FG-034 MAIL-A/AUTH-A **`f2a3b4c5d6e7` applied live** 2026-09-15. Remaining applied-live chain through FG-033 / FG-024 / FG-032 is unchanged.
- HEAD / `origin/main`: parent before this rescore commit **`f764b0892bd48d0255a87785a21cdf39ed1f4765`** (`docs: freeze company-management access-domain seam`). This commit is the official V1 **65%** rescore. Product PERF-B **`dcde4adfe4a475932b7f144b0220b2b60e4bd75c`** (`feat: implement FG-035 PERF-B needs attention`). This pin follows. Product PERF-A **`7a4b7000e2650eadf68b4ea44d48f75c65830c1f`** (`feat: implement FG-035 PERF-A labour performance`). Operating-scope recording **`e809dcdbc3735aa91033f968a9ed562e749e6a0c`**. PERF-A pin **`618dfaefbff1d5926bafa39c438075dc9c26055b`**. Product SCH-D **`59d36b8f0b3a86eb41aee03890cb432d0fc58e52`** (`feat: implement FG-035 SCH-D field schedule`). Product SCH-C **`c57e23c55260b44fc88cadfe2fc40924aa58dde7`**. Working tree after this commit is the official 65% docs close. Interrupted FG-037 WIP remains **stashed / unapplied / not product**.
- Latest governed full suite (this 17 Sep 2026 FG-035 PERF-B post-live-UAT): **1190 passed**, 4212 warnings, **746.12s**, exit **0**. Dedicated PERF-B **36 passed**, 339 warnings, **18.78s**. PERF-A+B **50 passed**, 463 warnings, **26.40s**. Focused TAX/WBS+SCOPE+TIME+SCH-A+SCH-B+SCH-C+SCH-D+PERF-A+PERF-B+Hub/Field/MONITOR **206 passed**, 1047 warnings, **116.29s**. HISTORICAL PERF-A post-live-UAT full suite **1154 passed**, 3873 warnings, **633.10s**. HISTORICAL PERF-B engineering full suite **1190 passed**, 4212 warnings, **619.11s**. HISTORICAL SCH-D post-physical full suite **1140 passed**, 3749 warnings, **665.58s**.
- Chain: … → **`c1d2e3f4a5b6` (FG-020)** → **`d2e3f4a5b6c7` (FG-021)** → **`e3f4a5b6c7d8` (FG-023 Slice A; applied live 2026-09-07 Slice C)** → **`f4a5b6c7d8e9` (FG-026; applied live 2026-09-08)**
- Historical Slice 5 full suite remains **612 passed**. Slice 4 dedicated **16** / Slice-4 focused **114** / governed **226** / full **609** remain historical. Close-time FG-023 dedicated **35** / focused **149** / full **593** remain historical.
- Working tree was **clean** at Slice 5 implementation inspect parent. Live DB mutated only by authorized Slice C migrate + labeled UAT project **id 13**. Slice 5 wrote **no** actuals and **no** live Field Events/Originals. Slice 4 wrote **no** actuals. Slice 3 wrote **no** actuals. Slice 2 wrote **no** actuals. Slice 1 wrote **no** actuals. Close wrote **no** further actuals.
- Real external AI provider **NOT AUTHORIZED**. [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **CLOSED / OPERATIONAL FOR UAT**. Runtime permit web lookup **NOT AUTHORIZED**.

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

Read first: `AGENTS.md`; [platform-constitution.md](platform-constitution.md); [governance/continuity-and-anti-drift.md](governance/continuity-and-anti-drift.md); [governance/review-turnover-protocol.md](governance/review-turnover-protocol.md); [platform-governance.md](platform-governance.md); [v1-completion-register.md](v1-completion-register.md); this file; [current-state.md](current-state.md); [project-state-report.md](project-state-report.md); [platform-roadmap.md](platform-roadmap.md); [feature-gates/README.md](feature-gates/README.md); [adr/README.md](adr/README.md).

FG-008 / FG-009 / FG-010 / FG-011 / FG-012 / **FG-013** files: **CLOSED / OPERATIONAL FOR UAT**. [FG-014](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-015](feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-016](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **CLOSED / OPERATIONAL FOR UAT**. [ADR-037](adr/ADR-037-project-location-and-jurisdiction-resolution.md) / [ADR-038](adr/ADR-038-permit-intelligence-authority-and-rules-library.md) / [ADR-039](adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md) **Accepted**. [ADR-032](adr/ADR-032-app-managed-historical-workbook-storage.md) **Accepted**. [ADR-033](adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted** (architecture only). ADR-010 **Proposed**. Do not bulk-accept remaining Proposed ADRs. [ADR-040](adr/ADR-040-organization-brand-profile.md) is **Accepted**. [FG-017](feature-gates/FG-017-organization-brand-profile-v1.md) is **CLOSED / OPERATIONAL FOR UAT**. [ADR-041](adr/ADR-041-user-membership-and-office-authentication.md) is **Accepted**. [FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) is **CLOSED / OPERATIONAL FOR UAT**. [FG-019](feature-gates/FG-019-shared-api-foundation-v1.md) is **CLOSED / OPERATIONAL FOR UAT**. **ADR-021 Accepted** (MONITOR Slice A projection + Slice B Hub **implemented / live-migrated / office-UAT-verified**; [FG-023](feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) **CLOSED / OPERATIONAL FOR UAT**). Organization Brand Profile is **operational for office UAT**. Change Order document family is a **future pin only**.

## 4. APPROVED PRODUCT VISION

PLAN → PRICE → CONTRACT → BUILD → MONITOR → LEARN on one `Project`. No repository rename. Office and field complementary. CalibraytAI owns methodology; each organization owns commercial intelligence. Brayman Construction is `ORG-001`, not the universal CalibraytAI default.

## 5. CURRENT CALIBAI LIFECYCLE STATE

- **ORGANIZATION:** implemented (M011)
- **HISTORICAL EVIDENCE:** Phase B implemented (FG-006)
- **PLAN:** partial — M005–M010 implemented; **M012 / FG-010 foundation CLOSED / OPERATIONAL FOR UAT**; FG-015 Permit Foundation **CLOSED / OPERATIONAL FOR UAT**; FG-016 Pass 2 **CLOSED / OPERATIONAL FOR UAT**; Phase D mapping [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **CLOSED / OPERATIONAL FOR UAT**
- **PRICE:** partial — builder + commercial gate; Labour Engine Phase B **CLOSED / OPERATIONAL FOR UAT**; Pricing Engine **CLOSED / OPERATIONAL FOR UAT**; FG-012 internal breakdown + Proposal consistency **CLOSED / OPERATIONAL FOR UAT**; V1-02 / [FG-027](feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) costing approval **CLOSED / OPERATIONAL FOR UAT**
- **CONTRACT:** partial (proposals are the customer-facing estimate; FG-012 reconciles snapshot totals; output 4 Future). [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / SLICE A CLOSED / OPERATIONAL FOR UAT / SLICE B CLOSED / OPERATIONAL FOR UAT / SLICE C CLOSED / OPERATIONAL FOR UAT / TECH-A IMPLEMENTED / TECH-B IMPLEMENTED / TECH-C IMPLEMENTED / TECH-D IMPLEMENTED / OVERALL OPEN / PARTIAL**. Empty library of PRODUCTION content. Update foundation live. Generation **engine live / TECH-B policy live / TECH-C Family 05 DOCX merge + private custody live / TECH-D synthetic E2E proven / no real jurisdictional content**. Slice D **NOT AUTHORIZED**. Native Signing [FG-033](feature-gates/FG-033-native-signing-document-approval-signature-and-executed-artifact.md) **CLOSED / OPERATIONAL FOR UAT**; SIGN-A **IMPLEMENTED**; SIGN-B **IMPLEMENTED**; SIGN-C **IMPLEMENTED**; SIGN-D **IMPLEMENTED** (automated); SIGN-E **IMPLEMENTED**. [ADR-050](adr/ADR-050-north-american-legal-content-library-ownership.md) **Accepted**. [ADR-051](adr/ADR-051-legal-content-source-and-update-lifecycle.md) **Accepted**.
- **BUILD:** partial (change orders operational; Field Observation foundation **CLOSED / OPERATIONAL FOR UAT**; Field Web **CLOSED**; TIME **IMPLEMENTED** — duration entry, approval, approved labour hours; SCH-A **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**; SCH-B **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**; SCH-C **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**; SCH-D **IMPLEMENTED / TESTED / SERVER-SIDE LIVE UAT PASS / PHYSICAL IPHONE UAT PASS / COMMITTED / SHA-PINNED / PUSHED**; PERF-A **IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS**; PERF-B **IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS / COMMITTED / SHA-PINNED / PUSHED**; PERF-C **DEFINED / NOT IMPLEMENTATION-AUTHORIZED**)
- **MONITOR:** [FG-023](feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) **CLOSED / OPERATIONAL FOR UAT**; Slice A + Slice B **IMPLEMENTED / LIVE-MIGRATED**; Slice C **MIGRATION COMPLETE / OFFICE UAT COMPLETE / PASS**; MONITOR V1 **IMPLEMENTED / LIVE-MIGRATED / OFFICE-UAT-VERIFIED / CLOSED** (ADR-021 **Accepted**; recon [monitor-v1-implementation-reconnaissance.md](architecture/monitor-v1-implementation-reconnaissance.md) **COMPLETE**; preflight [fg-023-monitor-v1-implementation-preflight.md](architecture/fg-023-monitor-v1-implementation-preflight.md) **COMPLETE**). PERF-A labour-hours Hub panel **IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS** — do **not** put labour-hours math inside `assemble_monitor_v1`.
- **LEARN:** future (ADR-024 boundary accepted; no ML)

## 6. COMPLETED CODED MILESTONES

M001, M005, M007, M008 (docs), M009 (`5dc4b09`), M010 (`6b969fe`), M011 (`cb38d93`), FG-006 (`690d755`), FG-008 (`0569f25`; integrity `ff5d856`), FG-009 (`8e11179`; not a numbered M0xx), **M012 / FG-010** (`9665295`; live-migrate docs `316cc9f`).

## 7. CURRENT MILESTONE

**[FG-035](feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) OPEN / PARTIAL / TAX/WBS IMPLEMENTED / SCOPE IMPLEMENTED / TIME IMPLEMENTED / SCH-A IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS / SCH-B IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS / SCH-C IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS / SCH-D IMPLEMENTED / TESTED / SERVER-SIDE LIVE UAT PASS / PHYSICAL IPHONE UAT PASS / COMMITTED / SHA-PINNED / PUSHED / PERF-A IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS / COMMITTED / SHA-PINNED / PUSHED / PERF-B IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS / COMMITTED / SHA-PINNED / PUSHED / PERF-C DEFINED / NOT IMPLEMENTATION-AUTHORIZED / SCH OVERALL OPEN / PARTIAL.** [ADR-053](adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**. Repository Alembic head **`f9b0c1d2e3f4`**. Live current **`f9b0c1d2e3f4`**. **[FG-034](feature-gates/FG-034-account-recovery-and-transactional-email.md) CLOSED / OPERATIONAL FOR UAT / MAIL-A IMPLEMENTED / AUTH-A IMPLEMENTED / AUTH-B IMPLEMENTED / AUTH-C IMPLEMENTED / MAIL-B IMPLEMENTED / AUTH-D IMPLEMENTED / PASS.** [ADR-052](adr/ADR-052-account-recovery-and-transactional-email.md) **Accepted**. Live MAIL-A/AUTH-A revision **`f2a3b4c5d6e7`** (superseded as live current). **[FG-033](feature-gates/FG-033-native-signing-document-approval-signature-and-executed-artifact.md) CLOSED / OPERATIONAL FOR UAT / SIGN-A IMPLEMENTED / SIGN-B IMPLEMENTED / SIGN-C IMPLEMENTED / SIGN-D IMPLEMENTED / SIGN-E IMPLEMENTED.** [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **SLICE A CLOSED / OPERATIONAL FOR UAT / SLICE B CLOSED / OPERATIONAL FOR UAT / SLICE C CLOSED / OPERATIONAL FOR UAT / TECH-A IMPLEMENTED / TECH-B IMPLEMENTED / TECH-C IMPLEMENTED / TECH-D IMPLEMENTED / OVERALL OPEN / PARTIAL.** [ADR-050](adr/ADR-050-north-american-legal-content-library-ownership.md) **Accepted**. [ADR-051](adr/ADR-051-legal-content-source-and-update-lifecycle.md) **Accepted**. **[FG-032](feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) CLOSED / OPERATIONAL FOR UAT.** [ADR-049](adr/ADR-049-quickbooks-ready-output-ownership-and-snapshot.md) **Accepted**. Product SHA **`70e571140e12377aa5bd009b598530576401113b`**. Product parent **`010f6d641a756ceb2ab67475a284d3b8426c7b20`**. Canonical UAT project **id 26**. V1-05 **COMPLETE**. **[FG-031](feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) CLOSED / OPERATIONAL FOR UAT.** [ADR-048](adr/ADR-048-scope-delivery-make-buy-and-procurement-routing-ownership-boundary.md) **Accepted**. **[FG-029](feature-gates/FG-029-bmr-supplier-workflow-v1.md) CLOSED / OPERATIONAL FOR UAT.** **IMPLEMENTED / TESTED / COMMITTED / PUSHED / LIVE-MIGRATED / BOUNDED BMR DEMO OFFICE UAT PASS.** [ADR-046](adr/ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) **Accepted**. ADR-008 remains **Proposed**. V1 **65% / 4 of 11**. V1-03 **COMPLETE**. V1-04 **PARTIAL**. V1-05 **COMPLETE**. V1-06 **PARTIAL / 0.40**. V1-07 **PARTIAL / SIGN-A THROUGH SIGN-E IMPLEMENTED / PRODUCTION NOT COMPLETE**. **[FG-030](feature-gates/FG-030-supplier-identity-authentication-and-access-isolation.md) RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED.** [ADR-047](adr/ADR-047-supplier-identity-authentication-and-access-isolation.md) **Accepted** (architecture only). **[FG-027](feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) CLOSED / OPERATIONAL FOR UAT.** [FG-028](feature-gates/FG-028-calibai-to-calibraytai-product-identity-transition.md) **SLICES 1–3 COMPLETE / CLOSED / OPERATIONAL FOR UAT.** [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) remains **CLOSED / OPERATIONAL FOR UAT.** [FG-023](feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) remains **CLOSED / OPERATIONAL FOR UAT.** [FG-021 CLOSED.]

## 8. LAST AUTHORIZED DELTA

**Last authorized delta:** **2026-09-17 official V1 rescore 65% (docs-only / COMMIT / PUSH).** Arithmetic 64.55 → **65%**. Still **4 / 11** COMPLETE. Secondary Functional V1 Build **79% / 22 of 28** (labelled secondary; not averaged; not official scoring). V1-06 PARTIAL **0.25 → 0.40**. V1-07 ARCHITECTURE COMPLETE **0.15 →** PARTIAL **0.40**. No other factor changes. No new package COMPLETE. BMR DEMO READY **NO**. BRAYMAN REAL-LIFE UAT READY **NO**. FG-037 **NOT YET IMPLEMENTED**. Interrupted FG-037 WIP preserved in `stash@{0}` **`840dba8320b59ff9464410fec390d755a31a56aa`** (`WIP FG-037 interrupted before V1 rescore`) and **not applied / not counted as product**. Parent HEAD **`f764b0892bd48d0255a87785a21cdf39ed1f4765`**. Alembic **`f9b0c1d2e3f4 (head)`**. PERF-A / PERF-B remain **SEALED**. PERF-C **DEFINED / NOT IMPLEMENTATION-AUTHORIZED**. Company/Management seam **DEFINED / NOT IMPLEMENTED**. Next action **STOP.** Return to ChatGPT Architect. Do **not** pop the FG-037 stash from this record. Do **not** implement PERF-C.

**Prior:** **2026-09-17 Company/Management access-domain seam owner-decision freeze (docs-only / committed).** Status **DEFINED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. Freeze [architecture/company-management-access-domain-seam.md](architecture/company-management-access-domain-seam.md). ADR-041 Decision 4 **narrowly amended**. Default deny. No job-title RBAC. No Settings Members. No live grants. PERF-C remains **DEFINED / NOT IMPLEMENTATION-AUTHORIZED**. HEAD **`f764b0892bd48d0255a87785a21cdf39ed1f4765`**. Alembic **`f9b0c1d2e3f4 (head)`**. PERF-A / PERF-B remain **SEALED**. Historical V1 at freeze **60% / 4 of 11**. Next action was Architect review.

**Prior:** **2026-09-17 FG-035 PERF-C owner-decision freeze correction (docs-only / not committed).** Status **DEFINED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. Contractor question: **Where does my business need attention?** Owner decisions 1–16 **ACCEPTED**. Freeze [architecture/fg-035-perf-c-product-definition.md](architecture/fg-035-perf-c-product-definition.md). Pin **`1b80d244e3efb0c65d3a02dd247d923dfd95166c`**. No schema. No product. No Field Company Attention. Permission domains **RECORDED / NOT IMPLEMENTED**. Alembic **`f9b0c1d2e3f4 (head)`**. PERF-A / PERF-B remain **SEALED**. V1 **unchanged** (**60% / 4 of 11**). Next action **STOP.** Return to ChatGPT Architect. Do **not** implement Company Attention. Do **not** implement Home Office.

**Prior:** **2026-09-17 FG-035 PERF-C product definition / owner-decision freeze (docs-only / not committed).** Status **DEFINED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. Freeze [architecture/fg-035-perf-c-product-definition.md](architecture/fg-035-perf-c-product-definition.md). Pin **`1b80d244e3efb0c65d3a02dd247d923dfd95166c`**. No schema. No product. Alembic **`f9b0c1d2e3f4 (head)`**. PERF-A / PERF-B remain **SEALED**. V1 **unchanged** (**60% / 4 of 11**). Next action **STOP.** Return to ChatGPT Architect. Do **not** implement Company Attention. Do **not** implement Home Office.

**Prior:** **2026-09-17 FG-035 PERF-B CLOSE / COMMIT / SHA-PIN / PUSH.** Status **IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS / COMMITTED / SHA-PINNED / PUSHED**. Product SHA **`dcde4adfe4a475932b7f144b0220b2b60e4bd75c`**. Project **50**. No schema. Alembic **`f9b0c1d2e3f4 (head)`**. PERF-C **NOT AUTHORIZED**. V1 **unchanged** (**60% / 4 of 11**). Evidence [testing/fg035-perf-b-live-bounded-uat-record.md](testing/fg035-perf-b-live-bounded-uat-record.md). Next action **STOP.** Return to ChatGPT Architect. Do **not** begin PERF-C.

**Prior:** **2026-09-17 FG-035 PERF-B bounded synthetic live UAT (uncommitted).** Status **IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS**. Project **50**. Dedicated **36 passed**. Focused **206 passed**. Full suite **1190 passed**, 4212 warnings, **746.12s**, exit **0**. No schema. Alembic **`f9b0c1d2e3f4 (head)`**. Not committed. Not pushed. PERF-C **NOT AUTHORIZED**. V1 **unchanged** (**60% / 4 of 11**). Evidence [testing/fg035-perf-b-live-bounded-uat-record.md](testing/fg035-perf-b-live-bounded-uat-record.md). Next action **STOP.** Return to ChatGPT Architect. Do **not** commit. Do **not** push. Do **not** begin PERF-C.

**Prior:** **2026-09-17 FG-035 PERF-B engineering implementation (uncommitted).** Status **IMPLEMENTED / TESTED / NOT LIVE-UAT**. Dedicated **36 passed**. Focused **206 passed**. Full suite **1190 passed**, 4212 warnings, **619.11s**, exit **0**. No schema. Alembic **`f9b0c1d2e3f4 (head)`**. Not committed. Not pushed. Live UAT **not performed**. PERF-C **NOT AUTHORIZED**. V1 **unchanged** (**60% / 4 of 11**). Next action **STOP.** Return to ChatGPT Architect. Do **not** commit. Do **not** push. Do **not** live-UAT PERF-B. Do **not** begin PERF-C.

**Prior:** **2026-09-17 FG-035 PERF-B design freeze sealed.** Status **IMPLEMENTATION PREFLIGHT COMPLETE / DESIGN FROZEN / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. Owner decisions A–G **ACCEPTED**. Freeze [architecture/fg-035-perf-b-implementation-preflight.md](architecture/fg-035-perf-b-implementation-preflight.md). No schema. No product. V1 **unchanged** (**60% / 4 of 11**). Next action **STOP.** Return to ChatGPT Architect. Do **not** implement PERF-B. Do **not** begin PERF-C.

**Prior:** **2026-09-17 FG-035 PERF-B implementation preflight (docs-only / not committed).** Status **PREFLIGHT COMPLETE / OWNER DECISIONS REQUIRED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. Freeze [architecture/fg-035-perf-b-implementation-preflight.md](architecture/fg-035-perf-b-implementation-preflight.md). No schema. No product. V1 **unchanged** (**60% / 4 of 11**). Next action **STOP.** Return to ChatGPT Architect. Do **not** implement PERF-B. Do **not** begin PERF-C.

**Prior:** **2026-09-17 V1 Desktop Contractor Experience organization scale / operating-scope amendment.** Organization remains the hard tenancy / security boundary. Division / Operating Unit is optional and subordinate. Crew is not Division. No schema. No RBAC. No PERF-B. Record [architecture/v1-desktop-contractor-experience-product-direction.md](architecture/v1-desktop-contractor-experience-product-direction.md) §23. V1 **unchanged** (**60% / 4 of 11**). Next action **STOP.** Return to ChatGPT Architect. Do **not** implement Home Office. Do **not** begin PERF-B.

**Prior:** **2026-09-17 V1 DESKTOP CONTRACTOR EXPERIENCE / CONTEXT-AWARE HOME OFFICE product-direction recording.** Status **RECORDED / MANDATORY V1 / MANDATORY PRE-BEN/TEAM REAL-WORLD UAT / IMPLEMENTATION SEQUENCED AFTER PERF ATTENTION / NOT IMPLEMENTED**. Record [architecture/v1-desktop-contractor-experience-product-direction.md](architecture/v1-desktop-contractor-experience-product-direction.md). No product. No PERF-B. V1 **unchanged** (**60% / 4 of 11**). Next action **STOP.** Return to ChatGPT Architect. Do **not** implement Home Office. Do **not** begin PERF-B.

**Prior:** **2026-09-17 FG-035 PERF-A CLOSE / COMMIT / SHA-PIN / PUSH.** PERF-A **IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS / COMMITTED / SHA-PINNED / PUSHED**. Product SHA **`7a4b7000e2650eadf68b4ea44d48f75c65830c1f`**. Project **49**. No schema. V1 **unchanged** (**60% / 4 of 11**). Evidence [testing/fg035-perf-a-live-bounded-uat-record.md](testing/fg035-perf-a-live-bounded-uat-record.md). Next action **STOP.** Return to ChatGPT Architect. Do **not** begin PERF-B.

**Prior:** **2026-09-17 FG-035 PERF-A bounded synthetic live UAT (uncommitted).** PERF-A **IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS**. Project **49**. Dedicated **14 passed**. Focused **170 passed**. Full suite **1154 passed**, 3873 warnings, **633.10s**, exit **0**. HEAD **`8187d88d9a7695d009b4e8610ab2468831ec4fe3`**. No schema. Not committed. Not pushed. V1 **unchanged** (**60% / 4 of 11**). Evidence [testing/fg035-perf-a-live-bounded-uat-record.md](testing/fg035-perf-a-live-bounded-uat-record.md). Next action **STOP.** Return to ChatGPT Architect. Do **not** commit. Do **not** begin PERF-B.

**Prior:** **2026-09-17 FG-035 PERF-A engineering implementation (uncommitted).** PERF-A **IMPLEMENTED / TESTED / NOT LIVE-UAT**. `assemble_project_performance` + Hub `#hub-labour`. Dedicated **14 passed**. Focused **170 passed**. Full suite **1154 passed**, 3873 warnings, **473.49s**, exit **0**. HEAD **`8187d88d9a7695d009b4e8610ab2468831ec4fe3`**. No schema. Not committed. Not pushed. Live UAT **not performed**. V1 **unchanged** (**60% / 4 of 11**). Next action **STOP.** Return to ChatGPT Architect. Do **not** commit. Do **not** begin PERF-B. Do **not** perform live UAT unless separately authorized.

**Prior:** **2026-09-17 FG-035 PERF-A design freeze sealed (this commit).** PERF-A **DESIGN FROZEN / NOT IMPLEMENTED**. Freeze [architecture/fg-035-perf-a-implementation-preflight.md](architecture/fg-035-perf-a-implementation-preflight.md). Parent **`f1aa486a738a1877d34b16e53fc31d610444ae19`**. No schema. No app/tests. SCH-D remains **COMMITTED / SHA-PINNED / PUSHED**. V1 **unchanged** (**60% / 4 of 11**). Next action **STOP.** Return to ChatGPT Architect. Do **not** implement PERF-A unless separately authorized. Do **not** begin PERF-B.

**Prior:** **2026-09-17 FG-035 PERF-A implementation preflight (docs-only).** PERF-A **DESIGN FROZEN / NOT IMPLEMENTED**. Freeze [architecture/fg-035-perf-a-implementation-preflight.md](architecture/fg-035-perf-a-implementation-preflight.md). No schema. No app/tests. HEAD **`f1aa486a738a1877d34b16e53fc31d610444ae19`**. SCH-D remains **COMMITTED / SHA-PINNED / PUSHED**. V1 **unchanged** (**60% / 4 of 11**). Next action **STOP.** Return to ChatGPT Architect. Do **not** implement PERF-A unless separately authorized. Do **not** begin PERF-B.

**Prior:** **2026-09-17 FG-035 SCH-D committed.** SCH-D **IMPLEMENTED / TESTED / SERVER-SIDE LIVE UAT PASS / PHYSICAL IPHONE UAT PASS / COMMITTED / NOT PUSHED**. Product SHA **`59d36b8f0b3a86eb41aee03890cb432d0fc58e52`**. Future-direction docs **`78ca4f7934495538e2c6c6c256547369577f6258`**. Darcy docs **`61a92d0ae1541e1fb70bed1867b0c0a12c6e0a0a`**. No migration. Live current = repository head **`f9b0c1d2e3f4 (head)`**. Manual Impact **CURRENT**. V1 **unchanged** (**60% / 4 of 11**). Evidence [testing/fg035-sch-d-live-physical-iphone-uat-record.md](testing/fg035-sch-d-live-physical-iphone-uat-record.md). Next action **STOP.** Do **not** begin PERF.

**Prior:** **2026-09-17 FG-035 SCH-D final physical iPhone UAT reconciliation + post-physical regression.** Joel G1–G6 **PHYSICAL PASS**. Directions + native iOS return **PHYSICAL PASS**. Dedicated SCH-D **21 passed**. TIME+Field+SCH-D **49 passed**. SCH-A/B/C **36 passed**. Focused **156 passed**. Full suite **1140 passed**, 3749 warnings, **665.58s**, exit **0**. SCH-D **IMPLEMENTED / TESTED / SERVER-SIDE LIVE UAT PASS / PHYSICAL IPHONE UAT PASS / NOT COMMITTED / NOT PUSHED**. Next **STOP.** Return to ChatGPT Architect. Do **not** commit. Do **not** begin PERF.

**Prior:** **2026-09-17 FG-035 SCH-D job-site location + Directions UAT correction.** G1/G5/G6 **PHYSICAL PASS**. G2/G3/G4 **FAIL** because Project 48 had no address. Field projects `Project.address` / civic `ProjectLocation`. Synthetic Project **48** address `48 Synthetic UAT Job-Site Road, North Gower, ON`. Dedicated SCH-D **21 passed**. Governed bundle **85 passed**. Month/Time not redesigned. Next **STOP.** Joel **G2/G3/G4** only. Do **not** submit Time. Do **not** commit.

**Prior:** **2026-09-17 FG-035 SCH-D address + Directions + Month calendar.** Authority `projects.address`. No migration. Directions phone-maps handoff. Month calendar + selected-day detail. Dedicated SCH-D **19 passed**. TIME+Field+SCH-D **47 passed**. F1/F2/F4 physical PASS preserved. F3 Month FAIL replaced, not physically passed. Project **48** has no stored address. Next **STOP.** Joel **G1–G6** portrait only. Do **not** rotate. Do **not** submit Time. Do **not** commit.

**Prior:** **2026-09-16/17 FG-035 SCH-D HTTPS UAT harness recovery.** Terminated unhealthy Python **2556** (stuck `192.168.2.160:61619`; localhost `/login` timeout). Restarted same SCH-D tree with `flask run --with-threads`. Replacement Python **78027** start **2026-09-17 00:25:54**. Localhost `/login` **200** **32 ms**. Concurrency hold-TLS 3s + `/login` **200** **12 ms**. **No product change.** Post-C3 blanks **not** product-render evidence. Next **STOP.** Joel **E1** portrait Today, **E2** portrait Time once. Do **not** rotate. Do **not** submit Time. Do **not** commit.

**Prior:** **2026-09-16 FG-035 SCH-D physical UAT UX #4 measure-then-correct.** A1 **My Work — Joel PASS**. A2 Date **FAIL**. A4 landscape **FAIL**. Field action performance **FAIL / DIAGNOSIS**: Flask Enter Time **12–20 ms**; bottleneck render-blocking Google Fonts + idle IndexedDB. Date `min-width: 0`. Landscape 36rem shell. TIME+Field+SCH-D **43 passed**. HTTPS restart onto corrected product. Do **not** claim UX #4 physical PASS. Next action **STOP.** Joel physically retests B1–B5. Do **not** submit another Time entry. Do **not** commit. Do **not** begin PERF.

**Prior:** **2026-09-16 FG-035 SCH-D physical UAT UX #4.** UX #3 A1 **My Work — Joel PASS**. A2 Date **FAIL** (overflow right of Time card). A4 landscape **FAIL** (narrow column). Landscape performance was **mis-recorded** as landscape-only slowness; Joel corrected that to general Field action slowness. Date-only `min-width: 0`; lift `42rem` via `(min-width: 36rem)`. Dedicated SCH-D **14 passed**. TIME+Field **28 passed**. HTTPS restarted onto UX #4 CSS. Do **not** claim UX #4 physical PASS.

**Prior:** **2026-09-16 FG-035 SCH-D physical UAT UX #3.** Joel UX #2 Test A **FAIL / CORRECTION REQUIRED**. Chrome crash loop was **AiRIA pytest / not CalibraytAI**. Identity **My Work — first name**; sibling Time Date; restore FG-021 landscape two-column. Dedicated SCH-D **14 passed**. TIME+Field **28 passed**. SCH-A+B **22 passed**. HTTPS restarted onto UX #3. Do **not** claim UX #3 physical PASS. Overall physical UAT **not closed**. V1 **unchanged** (**60% / 4 of 11**). Next action **STOP.** Joel physically retests A1–A4 only. Do **not** continue Company Today / Week / Month. Do **not** submit another Time entry. Do **not** commit. Do **not** begin PERF.

**Prior:** **2026-09-16 continuity + live/UAT deployment audit.** Sealed through SCH-C confirmed. SCH-D remains uncommitted and running on HTTPS **5443**. Shop / Company Work recorded docs-only ([architecture/company-work-product-direction.md](architecture/company-work-product-direction.md)). HTTPS not restarted. V1 **unchanged**. Next action **STOP.** Do **not** commit. Do **not** implement Shop / Banked Hours. Do **not** begin PERF.

**Prior:** **2026-09-16 FG-035 SCH-D physical UAT UX #2.** Joel recorded **SCHEDULED TIME PHYSICAL PASS**. Remaining findings: weekday missing; redundant own-name My work; Time date right-shift; ad-hoc work must be obvious. Correction: derived weekday + natural date; omit current-user name on worker My work; Time date Field-form alignment; **Working somewhere else?** / **Choose different work** uses existing TIME pickers; Cleanup Time does not change Schedule. Dedicated SCH-D **13 passed**. TIME+Field **41 passed**. HTTPS restarted onto UX #2. Overall physical UAT **not closed**. Banked Hours **RECORDED / NOT AUTHORIZED**. Evidence [testing/fg035-sch-d-live-physical-iphone-uat-record.md](testing/fg035-sch-d-live-physical-iphone-uat-record.md). V1 **unchanged** (**60% / 4 of 11**). Next action **STOP.** Joel physically retests A–E. Do **not** continue Tests 2–8 until then. Do **not** claim overall physical PASS. Do **not** commit. Do **not** begin PERF. Do **not** implement Banked Hours.

**Prior:** **2026-09-16 FG-035 SCH-D Time-entry correction after physical iPhone Test 1 FAIL.** Root cause: `GET /field/projects/48/time` **302** to Confirm Project when the job was not confirmed, so Hours never rendered. Correction: Time URL confirms that project; `submit_time()` unchanged. Bounded Today dates / warning dedupe / project label / Today SVG. Dedicated SCH-D **12 passed**. TIME+Field **40 passed**. Focused **147 passed**. HTTPS restart required onto corrected code. Physical retest **not claimed**. Banked Hours **RECORDED / NOT AUTHORIZED** ([architecture/banked-hours-product-direction.md](architecture/banked-hours-product-direction.md)). Evidence [testing/fg035-sch-d-live-physical-iphone-uat-record.md](testing/fg035-sch-d-live-physical-iphone-uat-record.md). V1 **unchanged** (**60% / 4 of 11**). Next action **STOP.** Joel physically repeats Test 1 and Test 5. Do **not** continue Tests 2–8 until then. Do **not** claim physical PASS. Do **not** commit. Do **not** begin PERF. Do **not** implement Banked Hours.

**Prior:** **2026-09-16 FG-035 SCH-C committed / pushed.** SCH-C **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. Product SHA **`c57e23c55260b44fc88cadfe2fc40924aa58dde7`**. Additive **`f9b0c1d2e3f4`**. Live current = repository head. Synthetic Project **47**. Projects **45** / **46** unchanged. EST-2026-0019 unchanged. Manual Impact **CURRENT**. Manual **FRAMEWORK ACTIVE**. V1 **unchanged** (**60% / 4 of 11**). Evidence [testing/fg035-sch-c-live-bounded-uat-record.md](testing/fg035-sch-c-live-bounded-uat-record.md). Next action **STOP.** Return to ChatGPT Architect. Do **not** begin SCH-D.

**Prior:** **2026-09-16 FG-035 SCH-C resume / verify / complete existing implementation (not committed).** Lightweight **MANUAL IMPACT — SCH-C** in [architecture/manual-impact-log.md](architecture/manual-impact-log.md). Completed User Guide to Kevin/Ben **BEFORE** platform access. Help / Voice / Manual **NOT IMPLEMENTED**. SCH-C remains **IMPLEMENTED / TESTED / NOT LIVE-MIGRATED**. V1 **unchanged** (**60% / 4 of 11**). Next action **STOP.** Return to ChatGPT Architect. Do **not** implement Help, Voice, or the Manual. Do **not** live-migrate SCH-C. Do **not** commit unless separately authorized.

**Prior:** **2026-09-16 FG-035 SCH-C Lightweight Element dependencies + sequence warnings implemented / tested / not live-migrated (not committed).** Additive **`f9b0c1d2e3f4`**. Repository head **`f9b0c1d2e3f4`**. Live current remains **`f7f8a9b0c1d2`**. Sequence / predecessor-unscheduled facts are informational warnings only. KEEP / MOVE / REVIEW optional. Feature Gate **FG-035 OPEN / PARTIAL**. SCH-A / SCH-B remain **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. SCH-D **NOT AUTHORIZED**. V1 **unchanged** (**60% / 4 of 11**). Next action **STOP.** Return to ChatGPT Architect. Do **not** live-migrate. Do **not** begin live UAT. Do **not** commit unless separately authorized.

**Prior:** **2026-09-16 platform-wide warning law + desktop Print / paper workflow recorded and committed (docs only).** Docs SHA **`884aae30d845b9cf4cac3e0be2de454b4da2cfe8`**. Pin **`bad182d0d85e51584260988f2887b481333660df`**. Canonical [architecture/project-element-authority-future-record.md](architecture/project-element-authority-future-record.md). Warnings are **INFORMATIONAL ONLY / NON-BLOCKING**. KEEP / MOVE / REVIEW are optional affordances. Print is a V1 requirement, not a scoring unit, not implemented. Feature Gate **FG-035 OPEN / PARTIAL**. SCH-A / SCH-B remain **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. SCH-C **PREFLIGHT PASS / NOT IMPLEMENTED**. SCH-D **NOT AUTHORIZED**. V1 **unchanged** (**60% / 4 of 11**). Next action **STOP.** Return to ChatGPT Architect. Do **not** implement Print. Do **not** begin SCH-C product.

**Prior:** **2026-09-16 platform-wide desktop Print / paper workflow recorded (docs only; interrupted before commit).** Canonical [architecture/project-element-authority-future-record.md](architecture/project-element-authority-future-record.md). Folded into the same docs-only close with the warning law.

**Prior:** **2026-09-16 FG-035 SCH-B Assignment + optional Crew committed / pushed.** Feature Gate **FG-035 OPEN / PARTIAL**. SCH-B **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. Product SHA **`374798d7338a4c00d90a9c7a2b2efa310bc7e355`**. Additive **`f7f8a9b0c1d2`**. Live current = repository head. Synthetic Project **46**. Project **45** unchanged. EST-2026-0019 unchanged. PRODUCTION packages **0**. V1 **unchanged** (**60% / 4 of 11**). Evidence [testing/fg035-sch-b-live-bounded-uat-record.md](testing/fg035-sch-b-live-bounded-uat-record.md).

**Prior:** **2026-09-16 FG-035 SCH-B Assignment + optional Crew implementation.** Feature Gate **FG-035 OPEN / PARTIAL**. SCH-B **IMPLEMENTED / TESTED / NOT LIVE-MIGRATED** at that pass. Additive **`f7f8a9b0c1d2`**. Live current then remained **`f6e7f8a9b0c1`**. Working tree **DIRTY** (not committed). Live UAT **NOT YET PERFORMED** at that pass. Project **46** not created at that pass. Project **45** not mutated. EST-2026-0019 untouched. PRODUCTION packages **0**. V1 **unchanged** (**60% / 4 of 11**).

**Prior:** **2026-09-16 FG-035 SCH-A Schedule Core committed / pushed.** Feature Gate **FG-035 OPEN / PARTIAL**. SCH-A **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. Product SHA **`fd8a66990df8286e54151b80b6f3cd5be5dd3ad1`**. Live current then = repository head **`f6e7f8a9b0c1`**. Existing Project **45** preserved. Evidence [testing/fg035-sch-a-live-bounded-uat-record.md](testing/fg035-sch-a-live-bounded-uat-record.md).

**Prior:** **2026-09-15 FG-035 SCH-A Schedule Core implementation.** Feature Gate **FG-035 OPEN / PARTIAL**. SCH-A **IMPLEMENTED / TESTED / NOT LIVE-MIGRATED** at that pass. Live UAT **NOT YET PERFORMED** at that pass. Repository Alembic head **`f6e7f8a9b0c1`**. Live current then recorded as **`f5d6e7f8a9b0`**. SCH overall **NOT CLOSED**. SCH-B / SCH-C / SCH-D **NOT AUTHORIZED**. EST-2026-0019 untouched. PRODUCTION packages **0**. V1 **unchanged** (**60% / 4 of 11**).

**Prior:** **2026-09-15 FG-035 SCH implementation preflight (docs only).** Feature Gate **FG-035 OPEN / PARTIAL**. SCH **ARCHITECTURE RECORDED / IMPLEMENTATION PREFLIGHT COMPLETE / DESIGN FROZEN**. Record [architecture/fg-035-sch-implementation-preflight.md](architecture/fg-035-sch-implementation-preflight.md). No live migrate. TIME remains **IMPLEMENTED**. EST-2026-0019 untouched. PRODUCTION packages **0**. V1 **unchanged** (**60% / 4 of 11**).

**Prior:** **2026-09-15 FG-035 TIME field duration entry + approval + approved labour actuals.** Feature Gate **FG-035 OPEN / PARTIAL**. TIME **IMPLEMENTED / LIVE-MIGRATED / SYNTHETIC UAT PASS**. Product SHA **`03c074fb1eb2bbca77ba86e495726c0e042c1979`**. Additive **`f5d6e7f8a9b0`**. No Draft. No offline Time sync. Self-approval fail-closed. EST-2026-0019 untouched. PRODUCTION packages **0**. V1 **unchanged** (**60% / 4 of 11**). Next action **STOP.** Return to ChatGPT Architect. Do **not** begin SCH / PERF / CLOSE / LEARN / QB-T.

**Prior:** **2026-09-15 Help / Voice / User Manual §§26–39 continuation (docs only).** No product code. No FG-036. No Alembic. §§26–39 **RECORDED**. §26 task-based pre-UAT script **REQUIRED**. Voice mutation **not required** for V1 Voice completion. Do **not** invent §§40+. Does **not** interrupt FG-035. Record [architecture/interactive-help-voice-and-user-manual-future-record.md](architecture/interactive-help-voice-and-user-manual-future-record.md). FG-035 remains **OPEN / PARTIAL**. TAX/WBS remains **IMPLEMENTED**. V1 **unchanged** (**60% / 4 of 11**). Next action **STOP.** Return to ChatGPT Architect. Do **not** implement Help, Voice, or the Manual. Do **not** begin SCOPE from this note.

**Prior:** **2026-09-15 Interactive Help + Voice + professional User Manual product-direction record (docs only).** No product code. No new Feature Gate. No Alembic. Help / Voice / Manual **RECORDED / NOT IMPLEMENTED**. Does **not** interrupt FG-035. §26 truncated; remainder not invented. Open question on task-based pre-UAT scripts **received / not decided**. Record [architecture/interactive-help-voice-and-user-manual-future-record.md](architecture/interactive-help-voice-and-user-manual-future-record.md). FG-035 remains **OPEN / PARTIAL**. TAX/WBS remains **IMPLEMENTED**. V1 **unchanged** (**60% / 4 of 11**). Next action **STOP.** Return to ChatGPT Architect. Do **not** implement Help, Voice, or the Manual. Do **not** begin SCOPE / TIME / SCH from this note.

**Prior:** **2026-09-15 FG-035 TAX/WBS project work structure.** Feature Gate **FG-035 OPEN / PARTIAL**. TAX/WBS **IMPLEMENTED / LIVE-MIGRATED / SYNTHETIC UAT PASS**. [ADR-053](adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**. Additive **`f3b4c5d6e7f8`**. EST-2026-0019 untouched. PRODUCTION packages **0**. Later slices **NOT AUTHORIZED**. V1 **unchanged** (**60% / 4 of 11**). Dedicated TAX/WBS **13 passed**. Focused **98 passed**, 400 warnings, **39.20s**. Full suite **1065 passed**, 3403 warnings, **456.75s**. Evidence [testing/fg035-tax-wbs-live-bounded-uat-record.md](testing/fg035-tax-wbs-live-bounded-uat-record.md). Next action **STOP.** Return to ChatGPT Architect. Do **not** begin SCOPE / TIME / SCH from this note.

**Prior:** **2026-09-15 FG-034 AUTH-D complete Account Recovery + transactional email close.** Feature Gate **FG-034 CLOSED / OPERATIONAL FOR UAT**. Postmark HTTP adapter activated. Live Postmark **DEFERRED — PROVIDER CONFIGURATION REQUIRED / NOT CLAIMED AS PASS**. Complete local/fake E2E (Account Recovery + Native Signing mail). Automated desktop/mobile Account Recovery. Physical iPhone UAT **DEFERRED**. No new Alembic. EST-2026-0019 untouched. PRODUCTION packages **0**. FG-033 remains **CLOSED**. Future Time/Schedule record **unchanged**. V1 **unchanged** (**60% / 4 of 11**). Dedicated AUTH-D **12 passed**. Focused AUTH-D + MAIL-A/AUTH-A + AUTH-B + AUTH-C + MAIL-B + FG-018 + SIGN-A–E **185 passed**, 356 warnings, **117.94s**. Full suite **1052 passed**, 3338 warnings, **434.60s**. Evidence [testing/fg034-auth-d-complete-close-record.md](testing/fg034-auth-d-complete-close-record.md). Next action **STOP.** Return to ChatGPT Architect. Do **not** send live Postmark from this note. Do **not** implement Time / Schedule.

**Prior:** **2026-09-15 §105 sequencing completion + future-record close (docs only).** No product code. Completes §105 steps 9–13 of [architecture/project-element-authority-future-record.md](architecture/project-element-authority-future-record.md). Recording status **COMPLETE FOR PRODUCT-DIRECTION RECORDING**. MAIL-B remains **IMPLEMENTED / PASS** at **`6dfc2e940456cf9c292c700e07840fac5d871df4`**. V1 **unchanged** (**60% / 4 of 11**).

**Prior:** **2026-09-15 §72 remainder + LEARN/alerts/UAT/sequencing final continuation (docs only).** No product code. No AUTH-D. No new Feature Gate. Completes remainder of §72 and §§73–104 of [architecture/project-element-authority-future-record.md](architecture/project-element-authority-future-record.md). §105 recorded as received through **8. CORRECT** (remainder not invented). MAIL-B remains **IMPLEMENTED / PASS** at **`6dfc2e940456cf9c292c700e07840fac5d871df4`**. V1 **unchanged**. Next action **STOP.** Return to ChatGPT Architect. Do **not** begin AUTH-D. Do **not** implement the loop.

**Prior:** **2026-09-15 Change Order / Extra Work / Closeout / LEARN data-quality continuation (docs only).** No product code. No AUTH-D. No new Feature Gate. Completes §§40–71 of [architecture/project-element-authority-future-record.md](architecture/project-element-authority-future-record.md). §72 preflight checklist recorded as received (truncated after Closeout performance review). MAIL-B remains **IMPLEMENTED / PASS** at **`6dfc2e940456cf9c292c700e07840fac5d871df4`**. V1 **unchanged**. Next action **STOP.** Return to ChatGPT Architect. Do **not** begin AUTH-D. Do **not** implement the loop.

**Prior:** **2026-09-15 complete Time / Schedule / Performance / MONITOR / LEARN / language-audit product-direction record (docs only).** No product code. No AUTH-D. No new Feature Gate. MAIL-B remains **IMPLEMENTED / PASS** at **`6dfc2e940456cf9c292c700e07840fac5d871df4`**. Complete loop recorded in [architecture/project-element-authority-future-record.md](architecture/project-element-authority-future-record.md). Cursor prompt truncated at §40. V1 **unchanged**. Next action **STOP.** Return to ChatGPT Architect. Do **not** begin AUTH-D. Do **not** implement the loop.

**Prior:** **2026-09-15 FG-034 MAIL-B Native Signing transactional delivery.** Feature Gate **FG-034 OPEN / PARTIAL**. Native Signing invitation/resend/complete uses the existing MAIL-A engine. Same `/sign` credential. Copyable URL retained. SENT ≠ delivered. SIGNING_COMPLETE after EXECUTED has no new token and no PDF attachment. Mail failure does not roll back SENT or EXECUTED. Office copy: Email captured for testing. No new Alembic. EST-2026-0019 untouched. PRODUCTION packages **0**. FG-033 remains **CLOSED**. V1 **unchanged** (**60% / 4 of 11**). Dedicated MAIL-B **9 passed**. Focused MAIL-B + MAIL-A/AUTH-A + AUTH-B + AUTH-C + FG-018 + SIGN-A–E **173 passed**, 338 warnings, **107.18s**. Full suite **1040 passed**, 3320 warnings, **376.12s**. Evidence [testing/fg034-mail-b-native-signing-delivery-record.md](testing/fg034-mail-b-native-signing-delivery-record.md). Visual Dynamic Project / Crew Scheduling addendum **recorded only / not implemented**. Next action **STOP.** Return to ChatGPT Architect. Do **not** begin AUTH-D.

**Prior:** **2026-09-15 FG-034 AUTH-C complete Account Recovery E2E.** Feature Gate **FG-034 OPEN / PARTIAL**. AUTH-C proves MAIL-A + AUTH-A + AUTH-B as one local product: login → forgot → generic confirmation → `PASSWORD_RESET` capture → reset → token consumed → `credentials_epoch` bump → old sessions fail → new password office login. Enumeration, token failure, CSRF, rate limits, delivery-failure generic public result, CLI break-glass, desktop/mobile automated parity. Bounded MAIL-A wrap records `TRANSPORT_ERROR` when an injected transport raises. No new Alembic. EST-2026-0019 untouched. PRODUCTION packages **0**. FG-033 remains **CLOSED**. V1 **unchanged** (**60% / 4 of 11**). Dedicated AUTH-C **10 passed**. Focused AUTH-C + AUTH-B + MAIL-A/AUTH-A + FG-018 + SIGN-A–E **164 passed**, 318 warnings, **96.83s**. Full suite **1031 passed**, 3300 warnings, **395.54s**. Evidence [testing/fg034-auth-c-complete-e2e-record.md](testing/fg034-auth-c-complete-e2e-record.md). Next action **STOP.** Return to ChatGPT Architect. Do **not** begin MAIL-B.

**Prior:** **2026-09-15 FG-034 MAIL-A / AUTH-A Account Recovery + transactional email foundation.** Feature Gate **FG-034 OPEN / PARTIAL**. Shared transactional engine (local/fake; Postmark adapter boundary; no live HTTP). `credentials_epoch`; hash-at-rest reset tokens; 60-minute TTL; 8-character new-password floor; CLI reset retained and epoch-bumping. Additive **`f2a3b4c5d6e7` applied live**. Legacy Flask-Login `"<user_id>"` accepted as epoch **0**. EST-2026-0019 untouched. PRODUCTION packages **0**. FG-033 remains **CLOSED**. V1 **unchanged** (**60% / 4 of 11**). Dedicated MAIL-A / AUTH-A **28 passed**. Focused MAIL-A/AUTH-A + FG-018 + SIGN-A–E **142 passed**. Full suite **1009 passed**, 3290 warnings, **344.09s**. Evidence [testing/fg034-mail-a-auth-a-live-bounded-uat-record.md](testing/fg034-mail-a-auth-a-live-bounded-uat-record.md).

**Prior:** **2026-09-15 FG-033 SIGN-E convert-once + generated-contract Native Signing + desktop/iPhone parity.** Feature Gate **FG-033 CLOSED / OPERATIONAL FOR UAT**. LibreOffice/soffice convert-once; converter provenance; same `/sign` engine for CONTRACT and CHANGE_ORDER; PRODUCTION send BLOCK without ACTIVE PRODUCTION package; desktop + iPhone viewport assertions. Additive **`e0f1a2b3c4d5` applied live**. Automated product / E2E **PASS**. Real iPhone UAT **DEFERRED TO BRAYMAN / BEN REAL-WORLD UAT** — **NOT CLAIMED AS PASS**. No transactional email. EST-2026-0019 untouched. PRODUCTION packages **0**. TECH-D evidence intact. Family 05 remains **COMMERCIAL_DRAFT**. Slice D **not authorized**. FG-024 **not closed**. Native Signing production **NOT COMPLETE**. No external-review dependency. V1 **unchanged** (**60% / 4 of 11**). Dedicated SIGN-E **19 passed**. Focused SIGN-A/B/C/D/E + CO + Hub + TECH **208 passed**. Full suite **981 passed**, 3262 warnings, **371.67s**. Evidence [testing/fg033-sign-e-live-bounded-uat-record.md](testing/fg033-sign-e-live-bounded-uat-record.md).

**Prior:** **2026-09-15 FG-033 SIGN-D Change Order Native Signing E2E + office/Hub + automated mobile UX.** Feature Gate **FG-033 OPEN / PARTIAL** at that close. Office Send for Signature; Hub UNSIGNED / AWAITING SIGNATURE / SIGNED / EXECUTED; name-first customer `/sign` copy; countersign and no-countersign EXECUTED; lifecycle fail-closed; tenant isolation; automated mobile markup/CSS/copy/state. No new Alembic. Automated product / E2E **PASS**. Real iPhone UAT **DEFERRED TO BRAYMAN / BEN REAL-WORLD UAT** — **NOT CLAIMED AS PASS**. No transactional email. EST-2026-0019 untouched. PRODUCTION packages **0**. Dedicated SIGN-D **11 passed**. Focused SIGN-A/B/C/D + CO + Hub + TECH **206 passed**. Full suite **962 passed**, 3184 warnings, **317.78s**. Evidence [testing/fg033-sign-d-live-bounded-uat-record.md](testing/fg033-sign-d-live-bounded-uat-record.md).

**Prior:** **2026-09-14 FG-033 SIGN-C countersign + executed PDF + custody.** Feature Gate **FG-033 OPEN / PARTIAL**. HUMAN countersign; no-countersign execute; pypdf audit page; distinct executed SHA/custody; VOID/EXPIRE/DECLINE/RESEND; customer/office executed retrieval. Additive **`d9e0f1a2b3c4` applied live**. Synthetic UAT **PASS** (`SIGN-2026-0004` EXECUTED; `SIGN-2026-0005` no-countersign EXECUTED). SIGN-B `SIGN-2026-0003` retained SIGNED. SIGN-A `SIGN-2026-0001` / `SIGN-2026-0002` retained APPROVED_FOR_SIGNATURE. No transactional email. No LibreOffice. EST-2026-0019 untouched. PRODUCTION packages **0**. TECH-D evidence intact. Family 05 remains **COMMERCIAL_DRAFT**. SIGN-D/E **NOT STARTED**. Slice D **not authorized**. FG-024 **not closed**. Native Signing production **NOT COMPLETE**. No external-review dependency. V1 **unchanged** (**60% / 4 of 11**). Dedicated SIGN-C **19 passed**. Dedicated SIGN-A **11 passed**. Dedicated SIGN-B **18 passed**. Focused SIGN-A/B + CONTRACT + Change Order **174 passed**. Full suite **951 passed**, 3151 warnings, **529.43s**. Evidence [testing/fg033-sign-c-live-bounded-uat-record.md](testing/fg033-sign-c-live-bounded-uat-record.md). Next action **STOP.** Return to ChatGPT Architect. Do **not** begin SIGN-D from this note.

**Prior:** **2026-09-14 FG-033 SIGN-B secure invitation + public customer ceremony.** Feature Gate **FG-033 OPEN / PARTIAL**. Hash-at-rest invitation; no customer account; narrow public `/sign/*`; frozen CO PDF review; pinned consent; typed-name SIGN & ACCEPT; CSRF; rate limit; SENT → SIGNED; IP/user-agent evidence. Additive **`c8d9e0f1a2b3` applied live**. Synthetic customer UAT **PASS** (`SIGN-2026-0003` SIGNED). SIGN-A `SIGN-2026-0001` / `SIGN-2026-0002` retained APPROVED_FOR_SIGNATURE. No executed PDF. No countersign. No transactional email. EST-2026-0019 untouched. PRODUCTION packages **0**. TECH-D evidence intact. Family 05 remains **COMMERCIAL_DRAFT**. SIGN-C/D/E **NOT STARTED** at that close. Slice D **not authorized**. FG-024 **not closed**. Native Signing production **NOT COMPLETE**. No external-review dependency. V1 **unchanged** (**60% / 4 of 11**). Dedicated SIGN-B **18 passed**. Dedicated SIGN-A **11 passed**. Focused SIGN + CONTRACT + Change Order **137 passed**. Full suite **933 passed**, 3110 warnings, **342.95s**. Evidence [testing/fg033-sign-b-live-bounded-uat-record.md](testing/fg033-sign-b-live-bounded-uat-record.md).

**Prior:** **2026-09-14 FG-033 SIGN-A Native Signing freeze + request engine + audit.** Feature Gate **FG-033 OPEN / PARTIAL**. Overlay freeze of current Change Order ReportLab PDF; generated-contract DOCX bind; `SIGN-YYYY-NNNN`; HUMAN CREATED → APPROVED_FOR_SIGNATURE; AI/AUTOMATION BLOCK; append-only audit. Additive **`b7c8d9e0f1a2` applied live**. Office synthetic UAT **PASS** (`SIGN-2026-0001`, `SIGN-2026-0002` / `CTR-2026-0005`). No `/sign` route. No tokens. No executed PDF. No transactional email. EST-2026-0019 untouched. PRODUCTION packages **0**. TECH-D evidence intact. Family 05 remains **COMMERCIAL_DRAFT**. SIGN-B/C/D/E **NOT STARTED** at that close. Slice D **not authorized**. FG-024 **not closed**. Native Signing production **NOT COMPLETE**. V1 **unchanged** (**60% / 4 of 11**). Dedicated SIGN-A **11 passed**. Focused SIGN-A + CONTRACT + Change Order **103 passed**. Full suite **915 passed**, 3068 warnings, **341.52s**. Evidence [testing/fg033-sign-a-live-bounded-uat-record.md](testing/fg033-sign-a-live-bounded-uat-record.md).

**Prior:** **2026-09-14 FG-024 TECH-D production-shaped synthetic Ontario UAT.** End-to-end technical CONTRACT chain proven with SYNTHETIC_UAT only. C1 Issued/Draft, TECH-A HUMAN activation, C2 WARN, C3 warranty BLOCK/PASS, Family 05 copy merge, private DOCX custody/immutability, production selector ignores synthetic authority. No new migration. Live PRODUCTION packages **0**. EST-2026-0019 untouched. Family 05 remains **COMMERCIAL_DRAFT**. GENERATED != EXECUTED. Native Signing **not started**. Slice D **not authorized**. FG-024 **not closed**. V1 **unchanged** (**60% / 4 of 11**). Dedicated TECH-D **5 passed**. Focused TECH-A/B/C/D + FG-024 **124 passed**. Full suite **904 passed**, 3040 warnings, **350.10s**. Evidence [testing/fg024-tech-d-live-bounded-uat-record.md](testing/fg024-tech-d-live-bounded-uat-record.md). Next action **STOP.** Return to ChatGPT Architect. Do **not** begin Native Signing from this note.

**Prior:** **2026-09-14 FG-024 TECH-C Family 05 merge + artifact custody.** Family 05 remains presentation authority. Renderer works from a copy only. DOCX-primary technical V1 artifact. Frozen commercial facts + frozen `contract_provision` + `warranty` merged. Generated DOCX bytes retained privately with SHA-256 and master provenance. GENERATED != EXECUTED. Synthetic COMMERCIAL_DRAFT / NOT FOR SIGNATURE labels retained. Additive **`a6b7c8d9e0f1` applied live**. Live PRODUCTION packages **0**. EST-2026-0019 untouched. Family 05 remains **COMMERCIAL_DRAFT**. Counsel deferred for technical development only; pre-production counsel gate mandatory. TECH-D **not started**. Native Signing **not started**. Slice D **not authorized**. FG-024 **not closed**. V1 **unchanged** (**60% / 4 of 11**). Focused TECH-C + FG-024 related + Hub/customer/proposal **175 passed**. Full suite **899 passed**, 3022 warnings, **290.85s**. Evidence [testing/fg024-tech-c-live-migrate-bounded-uat-record.md](testing/fg024-tech-c-live-migrate-bounded-uat-record.md). Future Project Element / Time / LEARN direction, including mobile-first / iPhone-primary Time Entry UX, recorded only: [architecture/project-element-authority-future-record.md](architecture/project-element-authority-future-record.md) — **NOT IMPLEMENTED**. Next action **STOP.** Return to ChatGPT Architect. Do **not** begin TECH-D from this note.

**Prior:** **2026-09-14 FG-024 TECH-B C1/C2/C3 generation policy.** Issued/Accepted locked EstimateVersion + explicit Issued/Accepted Proposal required. Valid ACTIVE + pending candidate = WARN; current ACTIVE remains authority; candidate is not authority. Ontario V1 requires contract_provision + warranty. Additive **`f5a6b7c8d9e0` applied live**. Live PRODUCTION packages **0**. EST-2026-0019 untouched. Family 05 remains **COMMERCIAL_DRAFT**. Counsel deferred for technical development only; pre-production counsel gate mandatory. TECH-C/D **not started** at that commit. Native Signing **not started**. Slice D **not authorized**. FG-024 **not closed**. V1 **unchanged** (**60% / 4 of 11**). Focused TECH-B + FG-024 related **150 passed**. Full suite **886 passed**, 2989 warnings, **292.71s**. Evidence [testing/fg024-tech-b-live-migrate-bounded-uat-record.md](testing/fg024-tech-b-live-migrate-bounded-uat-record.md).

**Prior:** **2026-09-14 FG-024 TECH-A human activation + authority class.** HUMAN/COUNSEL may activate an eligible APPROVED package. AI cannot ACTIVE. Ordinary production selection = ACTIVE + PRODUCTION. SYNTHETIC_UAT only via explicit technical path. Additive **`e4f5a6b7c8d9` applied live**. Live PRODUCTION packages **0**. EST-2026-0019 untouched. Family 05 remains **COMMERCIAL_DRAFT**. Counsel deferred for technical development only; pre-production counsel gate mandatory. TECH-B/C/D **not started** at that commit. Native Signing **not started**. FG-024 **not closed**. V1 **unchanged** (**60% / 4 of 11**). Focused TECH-A + FG-024 related **73 passed**. Full suite **853 passed**, 2881 warnings, **276.57s**. Evidence [testing/fg024-tech-a-live-migrate-bounded-uat-record.md](testing/fg024-tech-a-live-migrate-bounded-uat-record.md).

**Prior:** **2026-09-14 fail-closed CONTRACT Hub UX.** Existing Slice A selector result shown on Project Hub CONTRACT. Ontario + no ACTIVE package → BLOCK. No generate/override. No Family 05 fallback. No schema/migration. C1/C2/C3 recorded (not implemented beyond existing selector). Independent BMR contract-story **PASS**. BMR DEMO READY remains **NO**. FG-024 **not closed**. V1 **unchanged** (**60% / 4 of 11**). EST-2026-0019 untouched. Focused Hub + Hub UX **22 passed**. Full suite **838 passed**, 2857 warnings, **277.98s**. Live current remains **`d3e4f5a6b7c8 (head)`**. Parent HEAD **`bd1baf9426ab3a6db2d0d063fe1a76c14c8bc3ef`**. Next action **STOP.** Return to ChatGPT Architect.

**Prior:** **2026-09-14 FG-025 customer-document language slice.** Existing Proposal preview/PDF customer title **CONSTRUCTION ESTIMATE**. Presentation-only. No schema. No migration. No V1 rescore. EST-2026-0019 untouched. FG-025 overall **NOT CLOSED**. BMR DEMO READY remains **NO**. Focused **97 passed**. Full suite **829 passed**, 2778 warnings, **264.51s**. Live current remains **`d3e4f5a6b7c8 (head)`**. Parent HEAD **`d2c7f35734495d8e93c97cbba9802efacb3d659b`**. Next action **STOP.** Return to ChatGPT Architect.

**Prior:** **2026-09-14 known documentation-drift cleanup.** Bounded docs-only reconciliation of stale CURRENT-STATE / INDEX / HANDOFF language with already-governed later authority. No product implementation. No V1 rescore. No migration. No EST-2026-0019 mutation. Full suite **825 passed**, 2771 warnings, **258.44s**. Live current remains **`d3e4f5a6b7c8 (head)`**. Parent HEAD **`92005e15bf9785350234bf78d7e85c175fa4b587`**.

**Prior:** **2026-09-13 FG-024 Slice C live migrate + bounded office UAT.** Live `flask db upgrade` **PASS**. Live current **`d3e4f5a6b7c8 (head)`**. Synthetic generation + immutable snapshot office UAT **PASS**. Dedicated Slice C **16 passed**. Dedicated Slice A **17 passed**. Dedicated Slice B **16 passed**. Full suite **825 passed**, 2771 warnings, **266.33s**. Slice C **CLOSED / OPERATIONAL FOR UAT**. Legal Content Gate **empty**. No real jurisdictional content. No real customer contract. EST-2026-0019 occupancy preserved. V1 remains **60% / 4 of 11**. Opening V1 remains **DEPLOYED / OPERATIONAL** (`d6fa984`). Parent HEAD **`1a2553932da1b750e2cbe0e32fd90e54d569a685`**. Evidence [testing/fg024-slice-c-live-migrate-bounded-uat-record.md](testing/fg024-slice-c-live-migrate-bounded-uat-record.md).

**Prior:** **2026-09-13 FG-024 Slice C product foundation.** Generation + immutable snapshot **implemented in the repository**. Alembic **`d3e4f5a6b7c8`**. Live migrate **not** run at that commit. Office UAT **not** run at that commit. Synthetic tests only. Legal Content Gate **empty**. C1/C2/C3 unresolved. Native Signing absent. Family 05 remains presentation shell. V1 remains **60% / 4 of 11**. Opening V1 remains **DEPLOYED / OPERATIONAL** (`d6fa984`). Parent HEAD **`252870da30433922c9b55bd4bfcf555704be73c8`**.

**Prior:** **2026-09-13 FG-024 Slice B live migrate + bounded office UAT.** Live `flask db upgrade` **PASS**. Live current **`c2d3e4f5a6b7 (head)`**. Source/snapshot/candidate/AI-boundary/Slice-A regression UAT **PASS**. Dedicated Slice B **16 passed**. Dedicated Slice A **17 passed**. Full suite **809 passed**, 2738 warnings, **278.30s**. Slice B **CLOSED / OPERATIONAL FOR UAT**. Legal Content Gate **empty**. V1 remains **60% / 4 of 11**. Opening V1 remains **DEPLOYED / OPERATIONAL** (`d6fa984`). Parent HEAD **`e36397778d282e14801bfb00c896ec7a3c36057f`**. Evidence [testing/fg024-slice-b-live-migrate-bounded-uat-record.md](testing/fg024-slice-b-live-migrate-bounded-uat-record.md).

**Prior:** **2026-09-13 FG-024 Slice B product foundation.** Source / snapshot / candidate / review tables + `app/services/legal_content_update.py`. Additive Alembic **`c2d3e4f5a6b7`** (not applied live at that commit). Dedicated **16 passed**. Full suite **809 passed**. Slice A selector preserved. AI cannot APPROVE/ACTIVE. Candidate does not auto-SUPERSEDE or deactivate ACTIVE. Generation-while-pending **deferred**. No live monitoring. No legal seed. No contract generation. Legal Content Gate **empty**. V1 remains **60% / 4 of 11**. Opening V1 remains **DEPLOYED / OPERATIONAL** (`d6fa984`). Parent HEAD **`72b54515f93683f96e7c09723f613cf27fc13082`**.

**Prior:** **2026-09-13 FG-024 Slice B architecture adopted.** Existing untracked drafts reconciled against FG-024 / ADR-050 / Legal Content Gate. Slice B preflight **PREFLIGHT COMPLETE**. [ADR-051](adr/ADR-051-legal-content-source-and-update-lifecycle.md) **Accepted** (architecture only). §6 generation-while-pending **deferred**. Slice B product **NOT AUTHORIZED / NOT IMPLEMENTED** at that commit. Legal Content Gate **empty**. V1 remains **60% / 4 of 11**. No Alembic. No live DB mutation. Opening V1 remains **DEPLOYED / OPERATIONAL** (`d6fa984`). Parent docs HEAD **`3c2420209680c7d06ce85b6278920f7fcc45faa4`**.

**Prior:** **2026-09-13 CalibraytAI Opening V1 Phase 3 production + ingest.** Product SHA **`d6fa984b1e84be4a1b21ff8f7358fc1d43fa74dc`**. Rollback **`06ad8f7f69437b2e4302ba155ece6291ba9414ce`**. Joel approved Phase 2 Pass 2 (“good for now — deploy and move on”). Frame F locked. HQ + web MP4/WebM ingested at `app/static/opening/v1/`. Login playback fail-open. Local smoke on port **5020**. Website integration **SEPARATE**. HostPapa app deploy **not applicable**. Uncommitted FG-024 Slice B preflight files must **not** be mixed into this commit.

**Prior:** **2026-09-13 FG-024 Slice A live migrate + bounded office UAT.** `flask db upgrade` **PASS**. Live current **`b1c2d3e4f5a6 (head)`**. Empty library. Fail-closed UAT PASS on labeled projects **13** and **9**. Dedicated **17 passed**. Full suite **782 passed**. Slice A **CLOSED / OPERATIONAL FOR UAT**. V1 remains **60% / 4 of 11**. EST-2026-0019 occupancy ($275/m³) unchanged and not issued.

**Prior:** **2026-09-13 FG-024 Slice A product.** Empty North American legal-content library persistence, ADR-037 resolver-backed selection, coded fail-closed. One additive Alembic **`b1c2d3e4f5a6`** (not applied live at that commit). Dedicated **17 passed**. Full suite **782 passed**. V1 remains **60% / 4 of 11**. EST-2026-0019 occupancy ($275/m³) unchanged and not issued. No UI. No Ontario/U.S. seed.

**Prior:** **2026-09-13 ADR-050 Accepted** (architecture / fail-closed ownership only). Joel Brayman / ChatGPT Architect. FG-024 Slice A architecture prerequisite **satisfied**. Product **NOT IMPLEMENTED** at that commit. V1 remains **60% / 4 of 11**. No Alembic. No live-schema mutation. EST-2026-0019 commercial occupancy ($275/m³) unchanged and not issued.

**Prior:** **2026-09-12 EST-2026-0019 recost — concrete $275/m³ Brayman Construction cost (Ben).** Version **34** line updated; TRUE GM 15% reapplied; Proposal **14** Draft totals refreshed. Two Joel-review DOCX regenerated from FG-022 copies (masters SHA unchanged). Direct **$42,392.00** · sell **$49,872.94** · HST **$6,483.48** · total **$56,356.42** · labour **284 mh** unchanged. Concrete 60 m³ × **$275** = **$16,500**. **Not issued.**

**Prior:** **2026-09-12 EST-2026-0019 two documents generated for Joel review.** Family 02 title **INTERNAL DETAILED COST BREAKDOWN**. Customer display title **CONSTRUCTION ESTIMATE** on a copy of the Family 03 visual master (Joel authorized this-project title; FG-022 register cleanup later / non-blocking). Masters not rewritten. Direct **$39,992.00** · sell **$47,049.41** · HST **$6,116.42** · total **$53,165.83** · labour **284 mh**. **Not issued.**

**Prior:** **2026-09-12 STOP — EST-2026-0019 document-title authority conflict.** Joel required customer document title **CONSTRUCTION ESTIMATE**. Current FG-022 Family 03 approved master/register/product title is **CUSTOMER-FACING ESTIMATE**. The string `CONSTRUCTION ESTIMATE` is **not** in the repository, not on any reusable master, and is not Family 07 (`Client Construction Proposal`). Family 02 title **INTERNAL DETAILED COST BREAKDOWN** matches. No master rewrite. No Marc regeneration. No family rename.

**Prior:** **2026-09-12 EST-2026-0019 two-document package using FG-022 approved masters.** Client **22**, Project **27**, Estimate **28**, EstimateVersion **34** Draft, snapshot **14**, Proposal **14** `PROP-2026-0006` Draft. Direct **$39,992.00** · sell **$47,049.41** · HST **$6,116.42** · total **$53,165.83**. Documents generated by filling **copies** of Family **02** and Family **03** masters (masters SHA unchanged). Ad-hoc HTML review files **removed**. Product code unchanged. No Alembic. **Not issued.** Standing rule: **approved template first; do not redesign project-by-project.** Do **not** recreate these IDs. Do **not** Issue/Send/Accept. Do **not** generate Documents 01/04–07 unless Joel lists them.

**Prior:** **2026-09-12 documentation-only catch-up / publication / deployment reconciliation.** Present-state leftovers from the FG-032 close were corrected (live Alembic current, FG-032/ADR-049 closed status, FG-029 closed status, FG-021 closed status, M009 implemented). Full suite rerun **765 passed**, 2669 warnings, **297.20s**. No application-code change. No migration. No live DB mutation. No V1-04. No V1 rescore. Parent FG-032 close **`09fca291a72fc17ca6f00872c01b4ff20ef19136`**.

**Prior:** **2026-09-11 FG-032 documentation-only final close + V1-05 evidence-based rescore.** Gate **CLOSED / OPERATIONAL FOR UAT**. V1-05 **COMPLETE**. Readiness **60% / 4 of 11**. V1-04 remains **PARTIAL / CURRENT SCORED PACKAGE**. BMR DEMO READY **NO**. BRAYMAN REAL-LIFE UAT READY **NO**. Parent Slice C UAT docs **`07490698fe325a6bd433be47070bce429c9f8ad8`**. Do **not** implement live QuickBooks API. Do **not** begin V1-04 product work. Do **not** implement FG-030.

**Prior:** **2026-09-11 FG-032 Slice C live migrate + bounded office UAT.** `flask db upgrade f1a2b3c4d5e6` **PASS**. Live current **`f1a2b3c4d5e6 (head)`**. Bounded DEMO office UAT **PASS** on project **26** package **1**. Evidence [testing/fg032-slice-c-live-migrate-bounded-uat-record.md](testing/fg032-slice-c-live-migrate-bounded-uat-record.md). Slices A+B remain **LIVE-MIGRATED / BOUNDED OFFICE UAT PASS / OPERATIONAL FOR UAT**. Gate **OVERALL NOT CLOSED** at that UAT. V1 remained **55% / 3 of 11** at that UAT. Parent occupancy repair **`00de0517b994635dec0be04a6e581167f690f7fe`**.

**Prior:** **2026-09-11 FG-032 Slice C atomic ENTERED occupancy repair.** Unique `estimate_quickbooks_entry_occupancies` lock row; concurrent ENTERED fail-closed; additive **`f1a2b3c4d5e6`** after **`f0a1b2c3d4e5`** (not applied live at that commit). Slices A+B remain **LIVE-MIGRATED / BOUNDED OFFICE UAT PASS / OPERATIONAL FOR UAT**. Gate **OVERALL NOT CLOSED**. Slice C office UAT **NOT RUN** at that commit. V1 remains **55% / 3 of 11**. Live current at that commit remained **`e9f0a1b2c3d4`**. Parent **`3275df0381133ac246670620f75ca1e767b198b3`**.

**Prior:** **2026-09-11 FG-032 Slice C implementation.** Explicit human ENTERED/REVERSED/CORRECTED confirmation; append-only `estimate_quickbooks_entry_events`; additive **`f0a1b2c3d4e5`** (not applied live). Slices A+B remain **LIVE-MIGRATED / BOUNDED OFFICE UAT PASS / OPERATIONAL FOR UAT**. Gate **OVERALL NOT CLOSED**. Slice C office UAT **NOT RUN**. V1 remains **55% / 3 of 11**. Live current remains **`e9f0a1b2c3d4`**. Parent **`e4336f8dbe5f40f971f253f2e0c7c8781138eb29`**. Do **not** live-migrate Slice C. Do **not** conduct Slice C office UAT. Do **not** close FG-032. Do **not** rescore V1.

**Prior:** **2026-09-11 FG-032 post-UAT documentation correction.** Documentation-only. Corrected V1 register live current **`d8e9f0a1b2c3` → `e9f0a1b2c3d4`**, stale “output 3 remains to be authorized” wording, and ADR README present-state FG-032 **NOT LIVE-MIGRATED**. No application-code change. No migration. No live DB mutation. Product tests **not** rerun. HISTORICAL dedicated **23 passed** / full **751 passed**. Live current remains **`e9f0a1b2c3d4`**. Parent **`92a349fcc854dffa70f850408c95112c1efca8ab`**. [FG-032](feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) **OVERALL NOT CLOSED**. Slice C **NOT AUTHORIZED**. V1 remains **55% / 3 of 11**. Do **not** re-migrate. Do **not** implement Slice C. Do **not** close FG-032. Do **not** rescore V1.

**Prior:** **2026-09-11 FG-032 Slices A+B live migrate + bounded office UAT.** Start pin **`520eeca7410e1a575f46a0bb8ed8126ea0d26445`**. Product SHA **`70e571140e12377aa5bd009b598530576401113b`**. Live `flask db upgrade e9f0a1b2c3d4` **PASS**. Live current = head **`e9f0a1b2c3d4`**. Canonical DEMO UAT project **id 26**. Packages **QB-2026-0001 ISSUED**, **QB-2026-0002 ISSUED**, **QB-2026-0003 REVIEWED** (stale BLOCK). Evidence [testing/fg032-slices-ab-live-migrate-bounded-uat-record.md](testing/fg032-slices-ab-live-migrate-bounded-uat-record.md). Dedicated **23 passed** / 12.96s. Full suite **751 passed** / 2479 warnings / 329.14s. No product-code correction. Gate **OVERALL NOT CLOSED**. Slice C **NOT AUTHORIZED**. V1 remains **55% / 3 of 11**. Do **not** re-migrate. Do **not** implement Slice C. Do **not** close FG-032. Do **not** rescore V1.

**Prior:** **2026-09-11 FG-032 post-implementation documentation reconciliation.** Corrected FG-032 product parent to **`010f6d641a756ceb2ab67475a284d3b8426c7b20`**. Product SHA remains **`70e571140e12377aa5bd009b598530576401113b`**. Pin **`9c254a38c39ef866cad3c5aca1f01cae4907f376`**. Documentation-only. No application-code change. No migration. No live DB mutation. Product tests **not** rerun. HISTORICAL dedicated **23 passed** / focused **209 passed** / full **751 passed**. Live current **`d8e9f0a1b2c3`**. Repository head **`e9f0a1b2c3d4`**. [FG-032](feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) **NOT CLOSED**. Slice C **NOT AUTHORIZED**. V1 remains **55% / 3 of 11**. Do **not** live-migrate. Do **not** office-UAT. Do **not** implement Slice C.

**Prior:** **2026-09-10 FG-032 Slices A+B product implementation.** Product SHA **`70e571140e12377aa5bd009b598530576401113b`**. Product parent **`010f6d641a756ceb2ab67475a284d3b8426c7b20`**. Docs pin **`9c254a38c39ef866cad3c5aca1f01cae4907f376`**. [ADR-049](adr/ADR-049-quickbooks-ready-output-ownership-and-snapshot.md) **Accepted**. Live current **`d8e9f0a1b2c3`**. Repository head **`e9f0a1b2c3d4`**. Dedicated **23 passed**. Focused **209 passed**. Full **751 passed**. Live migration **NOT RUN**. Office UAT **NOT RUN**. Slice C **NOT AUTHORIZED**. Gate **OVERALL NOT CLOSED**. V1 remains **55% / 3 of 11**.

**Prior:** **2026-09-10 V1-05 Option A documentation-only architecture preflight.** [FG-032](feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) **RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. [ADR-049](adr/ADR-049-quickbooks-ready-output-ownership-and-snapshot.md) **Proposed**. Joel selected Option A. No application-code change. No migration. No live DB mutation. Product tests **not** rerun. HISTORICAL focused **83 passed** / full **728 passed**. V1 remains **55% / 3 of 11**. Current scored package **V1-04 / PARTIAL**. Do **not** implement FG-032. Do **not** implement FG-030. Do **not** begin V1-04 product work.

**Prior:** **2026-09-10 FG-031 documentation-only final governance close.** Gate **CLOSED / OPERATIONAL FOR UAT**. Slice A and Slice B remain **OPERATIONAL FOR UAT**. Product SHA **`5e1082af68e0eb145d9da01c0fa26585f6b8b9d1`**. Slice B UAT close **`8629f0459e51a94ee42cb475a536570cfbc21639`**. Live current **`d8e9f0a1b2c3`**. Repository head **`d8e9f0a1b2c3`**. No application-code change. No migration. No live DB mutation. Product tests **not** rerun. HISTORICAL focused **83 passed** / full **728 passed**. V1 remains **55% / 3 of 11**. Current scored package **V1-04 / NOT STARTED**. Subcontract RFQ/package remains **maturation during UAT / not implemented**. Do **not** implement FG-030. Do **not** begin V1-04.

**Prior:** **2026-09-10 FG-031 Slice B live migrate + bounded office UAT.** Start pin **`314ced5699688a329dbdd7ab2484ef552dd447db`**. Product SHA **`5e1082af68e0eb145d9da01c0fa26585f6b8b9d1`**. Live current **`d8e9f0a1b2c3`**. Repository head **`d8e9f0a1b2c3`**. Canonical UAT project **id 25**. Evidence [testing/fg031-slice-b-live-migrate-bounded-uat-record.md](testing/fg031-slice-b-live-migrate-bounded-uat-record.md). Focused **83 passed**. Full suite **728 passed**. No product correction. Gate **OVERALL NOT CLOSED** at that UAT (historical). V1 remains **55% / 3 of 11**. Do **not** implement FG-030. Do **not** begin V1-04.

**Prior:** **2026-09-10 FG-031 Slice B product implementation.** Product SHA **`5e1082af68e0eb145d9da01c0fa26585f6b8b9d1`**. Start pin **`0d98b87112e8dda3537fe125d25f0737212bfe1c`**. Live current was **`c7d8e9f0a1b2`**. Repository head **`d8e9f0a1b2c3`**. Dedicated Slice B **21 passed**. Slice A **26**. FG-027 **20**. FG-029 **16**. Governed bundle **306**. Full suite **728**. Gate **OVERALL NOT CLOSED**. V1 remains **55% / 3 of 11**.

**Prior:** **2026-09-09 FG-031 Slice A live migrate + bounded office UAT.** Close **`b50b0dcd1ea24f1a37ed32d04325ce09127fd203`**. Start pin **`bbe22f2a10ba9ba827e50c92688774a025b95d34`**. Live current **`c7d8e9f0a1b2`**. Canonical UAT project **id 19**. Evidence [testing/fg031-live-migrate-bounded-uat-record.md](testing/fg031-live-migrate-bounded-uat-record.md). Historical dedicated FG-031 **26** / bundle **258** / full **707**.

**Prior:** **2026-09-09 FG-031 Slice A product implementation.** Product SHA **`54120608df98432b9be80faf8c2a3a08cdb5679c`**. Pin **`c7662164a3f562f18cdd4b71079970348b1cd72c`**. Two stored dimensions; 1:1 `EstimateScopeDelivery`; Hub PRICE Scope Delivery Review; Approve All Scope Routing; Supplier Package cited + confirmed `CONTRACTOR_PURCHASED` filter. Historical dedicated **23**. Historical full suite **704**. Migration file **`c7d8e9f0a1b2` not applied live**.

**Prior:** **2026-09-09 ADR-048 / FG-031 scope delivery routing architecture recording (docs only).** Architecture SHA **`1c6c8c492b92f11cc80ad1b6e8689f0e42523bcd`**. Pin **`9c3eeddb0ae8e4c0daaba119ee6eb590a25c6a18`**. [ADR-048](adr/ADR-048-scope-delivery-make-buy-and-procurement-routing-ownership-boundary.md) **Accepted**. Two stored dimensions; 1:1 EstimateLineItem; no HYBRID enum. Supporting V1 gate; **not** a 12th package. V1 remains **55% / 3 of 11**.

**Prior:** **2026-09-09 FG-028 Slice 3 approved logo installation.** Runtime `app/static/branding/calibraytai-logo-v2.png` (exact ZIP V2 PNG). Field header PRODUCT placement only. Office/login/tenant Brand Profile/Proposal/Change Order tenant marks unchanged. Field favicon unchanged. Dedicated **13**. Combined Field/brand/proposal/CO/auth **131**. Focused **117**. FG-029 regression **16**. Full suite **681**. No schema. No live DB mutation. Gate **CLOSED / OPERATIONAL FOR UAT**. Does **not** rescore V1 (**55% / 3 of 11**).

**Prior:** **2026-09-09 FG-029 post-UAT governance reconciliation (docs only).** One coherent governance commit of already-authorized interleaved FG-029 close / FG-028 asset-status / FG-030 architecture / copyable-output dirt. Product tests **not** rerun. Do **not** install FG-028 Slice 3. Do **not** implement FG-030.

**Prior:** **2026-09-09 FG-029 live migration + bounded BMR demo office UAT.** Live `flask db upgrade b6c7d8e9f0a1` **PASS**. Project **id 14** `FG029-UAT-BMR-DEMO`. Issued Supplier Package **id 1**. HTML/PDF **PASS**. Non-floating freeze **PASS**. Gate **CLOSED / OPERATIONAL FOR UAT**. V1-03 **COMPLETE**. Readiness **55%**. Product tests **not** rerun (HISTORICAL dedicated **16** / governed **210** / full **677**). Close-doc Git commit was **blocked** at UAT time by interleaved FG-028/FG-030 dirt (reconciled in the subsequent governance commit).

**Prior:** **2026-09-09 FG-030 supplier identity / isolation architecture recording (docs only).** [ADR-047](adr/ADR-047-supplier-identity-authentication-and-access-isolation.md) **Accepted** (architecture). [FG-030](feature-gates/FG-030-supplier-identity-authentication-and-access-isolation.md) **RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. No product code. No migration. V1 remains **45% / 2 of 11**.

**Prior:** **2026-09-09 FG-028 Slice 3 asset-status recording (docs only).** Package `CalibraytAI_090926_Final.zip` **ASSET RECEIVED / JOEL APPROVED / INSTALLATION PENDING**. **Not installed.** Was **not** installed during FG-029 live migration / UAT. FG-028 **NOT CLOSED**. V1 remains **45% / 2 of 11**.

**Prior:** **2026-09-09 V1-03 / FG-029 product implementation.** [ADR-046](adr/ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) **Accepted**. FG-029 **IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT LIVE-MIGRATED / UAT NOT AUTHORIZED / NOT CLOSED** at that commit. Dedicated **16 passed**. Full suite **677 passed**. Migration file `b6c7d8e9f0a1` **not applied live** at that commit.

**Prior:** **2026-09-09 FG-028 CalibAi → CalibraytAI product identity Slices 1–2**. Slices 1–2 **IMPLEMENTED**. Slice 3 was then **HELD**. Gate **NOT CLOSED**. Product SHA **`e06fa92c4543ae641ba5067b1d277af048d97139`**. Pin **`b8d74a4cbe2e25d2fce795cdb15aab7b4f76cc8f`**. Full suite **661 passed**.

**Prior:** **2026-09-08 V1-02 / FG-027 bounded office UAT continuation + close**. Remaining office UAT **PASS**. Gate **CLOSED / OPERATIONAL FOR UAT**. V1-02 **COMPLETE**. Readiness **45%**. No new migration. No product-code change. Product tests **not** rerun (last verified dedicated **20** / full **652**).

**Prior:** **2026-09-08 V1-02 / FG-027 bounded legacy override-provenance repair**. Product SHA **`72949f99da2b56ec06e95e16e29fa194a6730bbd`**. No new migration. Dedicated **20** / full **652**. Gate was then **LIVE-MIGRATED / OFFICE UAT STOPPED / NOT PASS / NOT CLOSED**.

**Prior:** **2026-09-08 V1-02 / FG-027 live migrate + bounded office UAT**. Live upgrade **PASS**. Office UAT **STOPPED / NOT PASS** on line-7 override provenance. Gate **NOT CLOSED**. V1 readiness remains **39%**.

**Prior:** **2026-09-08 V1-02 / FG-027 product implementation**. Status **IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT LIVE-MIGRATED / UAT NOT AUTHORIZED**. [ADR-044](adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) **Accepted**. Product SHA **`c751d72b32f1ed415375719df2fd69936ace64d7`**. Full suite **647 passed**. V1 readiness remains **39%**.

**Prior:** **2026-09-08 FG-026 live migrate + bounded office UAT**. Status **LIVE-MIGRATED / OFFICE UAT PASS / CLOSED / OPERATIONAL FOR UAT**. V1-01 **COMPLETE**.

**Prior:** **2026-09-08 FG-026 implementation**. Status **IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT LIVE-MIGRATED / UAT NOT RUN**. Product SHA **`aa4c71800586e0b8e2a63931bcdc8bc44d87a489`**. Dedicated **20** / full **632**.

**Prior:** **2026-09-08 FG-026 Feature Gate + architecture preflight** (docs only). Status **RECORDED / ARCHITECTURE PREFLIGHT COMPLETE / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. No product code.

**Prior:** **2026-09-08 Review Turnover** (docs only). Status **RECONCILIATION / SHA PIN / CURRENT-AUTHORITY REPAIR**. No product code. Slice 5 product SHA remains **`5b497905086554214e85f69afd8101d88f89161c`**.

**Prior:** **FG-025 Slice 5 contractor-facing Field Web language** (2026-09-08). Status **SLICE 5 AUTHORIZED AND IMPLEMENTED / NOT CLOSED**. Presentation mapping only. Remaining surfaces **NOT AUTHORIZED**.

**Prior:** **FG-025 Slice 4 contractor-facing office language** (2026-09-08). Status **SLICE 4 AUTHORIZED AND IMPLEMENTED / NOT CLOSED**. Presentation mapping only. Remaining surfaces were then **NOT AUTHORIZED**.

**Prior:** **FG-025 Slice 2 contractor-facing Project Hub language** (2026-09-07). Status **SLICE 2 AUTHORIZED AND IMPLEMENTED / NOT CLOSED**. Presentation mapping only. Remaining slices **NOT AUTHORIZED**.

**Prior:** **FG-025 Slice 1 Hub MONITOR contractor-facing display mapping** (2026-09-07). Status **SLICE 1 AUTHORIZED AND IMPLEMENTED / NOT CLOSED**. Presentation mapping only. Remaining slices were then **NOT AUTHORIZED**.

**Prior:** **FG-023 MONITOR V1 close** (2026-09-07, docs / governance). Status **CLOSED / OPERATIONAL FOR UAT**. MONITOR V1 **IMPLEMENTED / LIVE-MIGRATED / OFFICE-UAT-VERIFIED / CLOSED**. Close-time tests dedicated **35** / focused **149** / full **593**. No product code. Hub lifecycle already operational for MONITOR; LEARN remains Future.

**Prior:** **FG-025 Contractor-Facing UX Language recorded** (2026-09-07, docs / governance only). Status **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. Product-wide copy sweep after FG-023 close. No product code. No UI rewrite. Does **not** implement from this recording. FG-023 is now **CLOSED**.

**Prior:** **FG-023 Slice C live migrate + office UAT** (2026-09-07). Live `flask db upgrade e3f4a5b6c7d8` **PASS**. Office Hub UAT **PASS** on port **5014** against synthetic project **id 13** `FG023-UAT-MONITOR`. Four-class create **PASS**. `0.00` supersession **PASS**. Independent arithmetic **PASS**. Gate remains **OPEN**. FG-024 remains **FUTURE / NOT IMPLEMENTATION-AUTHORIZED**. No product-code change. No new migration.

**Prior:** **FG-024 North American Contract Intelligence recorded** (2026-09-07, docs / governance only). Status **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. One linked gate; Slices A–D **not authorized**. No product code. No migration. No legal-content population. Does **not** interrupt FG-023.

**Prior:** **FG-023 Slice C implementation preflight** (2026-09-07, docs / reconnaissance only). Parent product SHA `7dd4d82c927ec2c38a0562e7e1cdedbccabb6662`. No live migrate. No office UAT.

**Prior:** **FG-023 Slice B** Hub `#hub-monitor` + BUILD office actuals create/supersede (2026-09-07). SHA `7dd4d82c927ec2c38a0562e7e1cdedbccabb6662`. Dedicated **35**. Focused **149**. Full **593**. Gate remains **OPEN**.

**Prior:** **FG-023 Slice B implementation preflight** (2026-09-07, docs / reconnaissance only). SHA `b5e68bec0819985b75e306637bb0de79b948045e`.

**Prior:** **Review Turnover** (2026-09-07, docs only). Package `ea9c4b765bd58c5d12414784399e2c29822f1e6f`. SHA-pin `68b7d02b08553f51e08882bb1dc8ae2b7eb434d3`.

**Prior:** **FG-023 Slice A** (model + additive migration `e3f4a5b6c7d8` + BUILD actuals service + MONITOR `assemble_monitor_v1` + dedicated tests). Product SHA **`2553cf09bdd6b8018112d7eb4b682f87aa103b01`**. Dedicated **23**. Historical focused **126**. Full **581**. Live current remains `d2e3f4a5b6c7`. Live **39** / **39**. No live actuals table. Hub UI **not implemented**. Gate **not closed**. Do **not** live-migrate.

**Prior:** **FG-023 MONITOR V1 implementation preflight** (docs + read-only inspect). Readiness **B. READY WITH EXPLICIT NON-BLOCKING NOTES**. Canonical artifact: [architecture/fg-023-monitor-v1-implementation-preflight.md](architecture/fg-023-monitor-v1-implementation-preflight.md). FG-023 remains **APPROVED**. No product code in that pass. No tests. No migration. No ADR. Live current = head `d2e3f4a5b6c7`. Live **39** / **39**.

**Prior:** **APPROVE FG-023 MONITOR V1 Feature Gate** (docs only). Status **APPROVED / IMPLEMENTATION NOT STARTED / IMPLEMENTATION NOT YET AUTHORIZED**. Joel/ChatGPT accepted the gate as written on 2026-09-06, including correction semantics (`amount >= 0`; superseding successor may carry `0.00`). Office Direct Cost actuals remain in the approved gate (BUILD `ProjectDirectCostActual`; not created). No product code. No tests. No migration. No ADR. Live current = head `d2e3f4a5b6c7`. Live **39** / **39**. Do **not** implement MONITOR from this approval.

**Prior:** **DRAFT FG-023 MONITOR V1 Feature Gate** (docs only). Status **DRAFT FOR JOEL APPROVAL / NOT APPROVED / NOT AUTHORIZED FOR IMPLEMENTATION**. Office Direct Cost actuals **included** in the draft (BUILD `ProjectDirectCostActual`; not created). Residual roadmap “Next recommended milestones” / “Decisions Required” Item 13 leftover repaired. No product code. No tests. No migration. No ADR. Live current = head `d2e3f4a5b6c7`. Live **39** / **39**. Do **not** implement MONITOR.

**Prior:** **MONITOR V1 / Item 13 read-only implementation reconnaissance** (docs only). Recon **COMPLETE**. MONITOR **NOT IMPLEMENTED / NOT FEATURE-GATED / NOT AUTHORIZED FOR CODE**. No product code. No tests. No migration. No Feature Gate created. No ADR accepted. Current-authority stale-pin repairs: roadmap “Current (near-term product governance)”; Observation Delete capture header/priority; modules README live-head pins. Live current = head `d2e3f4a5b6c7`. Live **39** / **39**. Do **not** implement MONITOR. Do **not** implement Observation Delete. Do **not** implement session revocation.

**Prior:** **CLOSE FG-021 with OPTION 2 explicit SESSION-EXPIRY deferred exception** (docs only). Gate **CLOSED**. IMPLEMENTED / LIVE-MIGRATED / REAL-IPHONE UAT COMPLETE SUBJECT TO THE EXPLICIT SESSION-EXPIRY DEFERRED EXCEPTION. **SESSION-EXPIRY RECOVERY: DEFERRED / NOT YET EXERCISED.** NOT PASS. NOT FAIL. NOT N/A. NOT WAIVED. Recovery path implemented; current product has no naturally exercisable real-iPhone session-expiry trigger. Event **37** / Original **37** remain authenticated residue, **not** recovery evidence. **OLDER SUPPORTED IPHONE / SAFARI WAIVED AS NOT PRACTICAL.** Observation Delete **QUEUED / NOT AUTHORIZED / NOT IMPLEMENTED / NON-BLOCKING**. Server-side per-login session revocation / idle timeout remains **FUTURE AUTHENTICATION HARDENING / NOT FG-021**. Do **not** start Item 13 / MONITOR. Do **not** implement Observation Delete. Do **not** implement session revocation from this close.

**Prior:** **OLDER SUPPORTED IPHONE / SAFARI WAIVED AS NOT PRACTICAL.** Not PASS. Not FAIL. Not exercised. Conservative disposition: older-device coverage is distinct from the primary UAT device. Joel has no separate older physical iPhone. Approved FG-021 uses “where practical.” Primary UAT remains iPhone 14 / iOS 26.6.1 / Safari and is **not** the older-device PASS. Repository does not define “older” or a device matrix. SESSION-EXPIRY RECOVERY remains **OPEN / DEFERRED / NOT YET EXERCISED** (only substantive unresolved FG-021 UAT). Observation Delete **QUEUED** and does **not** block closure. Do **not** close FG-021. Do **not** resume session-expiry UAT from this pass.

**Prior:** **LANDSCAPE-TOLERANCE REAL-IPHONE UAT PASS.** Implemented CSS `057ff15` is sufficient. Initial post-fix retest **FAIL** was confounded by iPhone Portrait Orientation Lock **ON** (not a CalibAi product defect). After lock **OFF**, Field adjusted correctly. Portrait / one-handed / outdoor / landscape / orientation **PASS**. **CURRENT-IPHONE FIELD-USABILITY PASS.** No second CSS correction. Do **not** close FG-021. Do **not** start older-device or session-expiry UAT from this pass.

**Prior:** **LANDSCAPE-TOLERANCE CSS CORRECTION.** Operator FAIL: phone does not adjust for landscape. Portrait / one-handed / outdoor / general visibility **PASS**. CSS-only `@media (orientation: landscape)` in `app/static/css/field.css`. Portrait defaults unchanged. Templates/JS unchanged. Dedicated **20**. Focused **148**. Full **558**. **LANDSCAPE TOLERANCE: FIX IMPLEMENTED / REAL-IPHONE RETEST REQUIRED / NOT YET PASS.** Do **not** close FG-021. Do **not** start older-device or session-expiry UAT from this pass.

**Prior:** **CSRF RECOVERY REAL-IPHONE UAT PASS.** Natural Flask-WTF expiry on the same Capture document. HTTPS `https://192.168.134.223:5443`, detached PID **88819**, **Project 11**, text-only. T0 Capture GET **200** `06:02:58` EDT. Save `07:40:34` EDT (dwell **5856 s**). Sequence: Event POST **400** → Capture GET **200** (`refreshCsrf`, no static) → Event POST **201** → Original POST **201**. Event **39** / Original **39**, `ORG-001`, Joel Brayman `user_id` 1. Body `FG-021 CSRF recovery UAT - 6 Sep 2026`. UUIDs `0012e6af-c627-4c40-9793-5e1e6611691f` / `acba9f83-5ed2-40ae-a811-c805318594c0`. Live **39** / **39**. Operator UI **SAVED**. Event **38** remains interrupted-pending residue (not this PASS). SESSION-EXPIRY RECOVERY remains **OPEN / DEFERRED / NOT YET EXERCISED**. Do **not** close FG-021. Do **not** start usability UAT from this pass.

**Prior:** **BACKGROUND / FOREGROUND PERSISTENCE REAL-IPHONE UAT PASS.** Unsaved Capture text survived ordinary Safari backgrounding (not force-close). HTTPS `https://192.168.134.223:5443`, **Project 11**, text-only. Flask Cursor Terminal **556723**: Capture GET `07:17:25`; Event **201** + Original **201** at `07:19:10`; Today **200** `07:19:17`. Event **36** / Original **36**, `ORG-001`, Joel Brayman `user_id` 1. Body `FG-021 background-foreground UAT - 5 Sep 2026`. UUIDs `3394825c-bb74-409b-93c6-d976021ec39e` / `f4ede486-1b7b-40de-be02-47e5af04c5ba`. Live **36** / **36**. Desktop Hub `/projects/11/field-events/36` **200**. One Event + one text Original. Do **not** close FG-021. Do **not** start session-expiry in this pass.

**Prior:** **MIXED CAPTURE REAL-IPHONE UAT PASS.** One Save: text + Take Photo JPEG + voice. HTTPS `https://192.168.134.223:5443`, **Project 11**. Flask Cursor Terminal **556723** `06:52:40` Event **201** then three Original POSTs **201**. Event **35**, `ORG-001`, Joel Brayman `user_id` 1. UUIDs `addef41b-5120-4361-b2c7-b99e4b9c7711` / text `f4079f97-dec4-4898-be4a-ceb31ee13449` / audio `37945d9e-acba-4510-a86c-0e86bf0475ad` / image `bf996029-13b6-43e7-a794-449ae0c86b13`. Original **33** text `FG-021 mixed capture UAT - 5 Sep 2026`. Original **34** `note.m4a` `audio/mp4` 190338 bytes SHA-256 `92d3896b7f88887dd33bd3dc443609a413e8581a8bb86d2b743de6258e5b6c5f`. Original **35** `image.jpg` JPEG JFIF 3076035 bytes SHA-256 `d3e947e6603e7d1dbd947634e0a603778de2e2688367266e3972f3d61f9c3bae`. Kind set `{text, image, audio}`. Live **35** / **35**. Field Today **200**. Desktop Hub `/projects/11/field-events/35` **200**. Do **not** close FG-021. Do **not** repeat mixed capture.

**Prior:** **HEIC REAL-DEVICE UAT PASS.** Files source `IMG_5351.HEIC`. Safari Choose Photo → Browse/Files → Save. HTTPS `https://192.168.134.223:5443`, **Project 11**. Flask Cursor Terminal **556723** `06:36:56` Event **201** then Original **201**. Event **34** / Original **32**, `ORG-001`, Joel Brayman `user_id` 1. Filename `IMG_5351.HEIC`; MIME `image/heic`; stored `instance/build_originals/ORG-001/11/34/32.heic`. Actual bytes ISO-BMFF HEIC (`ftyp` major `heic`), 1479610 bytes, SHA-256 `e042b2672cbb7170bcfeeefc74cb816dae72710c5bf937cf17a46b313851b319`. Compatible rendition `instance/build_renditions/ORG-001/11/34/32/display.jpg` JPEG JFIF 439618 bytes, SHA-256 `946ce4f6eaa4bab05616f664695ce81d9c1d7c3bffcf32ab231e45b060f9365c`. Original `/content` remains `image/heic`; Field Today and Hub `/display` serve the JPEG rendition. Desktop Hub `/projects/11/field-events/34` **200**. Live **34** / **32**. One Event + one Original; no 409. UUIDs `307a54d0-23b6-4a0f-b956-e1948562e918` / `3f993d7a-14fa-449b-ab1b-5f5e137e80de`. Do **not** close FG-021. Do **not** start mixed capture.

**Prior:** **HEIC REAL-DEVICE UAT NOT EXERCISED.** High Efficiency native Camera → library → Field Web Choose Photo. Joel Save + Field Today succeeded. Actual Original **31** bytes are JPEG JFIF (`IMG_5350.jpeg`, 2691705 bytes, SHA-256 `2fbfe2217f22f727a0a76455b5fb07e8e65d0b403a7ff521c4c1f2b7c4ec66f0`), Event **33**, project **12**. Safari delivered JPEG; HEIC/HEIF Original + Compatible Rendition path **not** exercised on that attempt.

**Prior:** **REAL IPHONE BROWSER CLOSE → INDEXEDDB RECOVERY → RETRY PASS.** HTTPS `https://192.168.134.223:5443`. Take Photo JPEG. Operator completed pending capture → Safari close → reopen → retry. Flask Cursor Terminal **556723**: no Event POST after Capture GET `05:14:26` until Capture GET `05:19:01`, then Event **201** + Original **201** at `05:19:02`. Event **32** / Original **30**, project **11**, `ORG-001`, Joel Brayman `user_id` 1. `image/jpeg`, `image.jpg`, 2796786 bytes, JFIF, SHA-256 `4bbd4d2fa9b5a660a57bc2d60c32e094876023c91fa8705a6c6827e22c3e3155`. UUIDs `bdfd719f-d008-4ecf-957f-6168c6edefe5` / `586c19d4-e122-4bdf-be71-525ab2574e61`. One Event + one Original; no 409. Live **32** / **30**. Desktop Hub `/projects/11/field-events/32` **200**. Safari process-kill operator-attested. Do **not** close FG-021. **HEIC REAL-DEVICE NOT YET TESTED.**

**Prior:** **GOVERN CalibAi chat-title continuity convention (docs only).** Permanent response/turnover traceability: begin with exact ChatGPT development chat title in bold; end with `END — <title>` after any Cursor prompt; standing next-prompt rule preserved. Does **not** alter FG-021, FG-022, product code, Legal Content Gate, or master bytes.

**Prior:** **CLOSE FG-022 reusable approved document template family V1 (docs only; no master-byte change).** Joel presentation-master approval recorded. Families 01–04, 06–07 **JOEL APPROVED / APPROVED REUSABLE MASTER**. Family 05 **JOEL APPROVED / APPROVED REUSABLE PRESENTATION MASTER**; legal **COMMERCIAL_DRAFT / NOT LEGALLY APPROVED**. Immutable source ZIP unchanged. Legal Content Gate **empty**. FG-012 / FG-017 / FG-021 **unchanged**. FG-021 **OPEN**. FG-022 **CLOSED**.

**Prior:** **IMPLEMENT FG-022 reusable approved document masters (durable DOCX/PDF outside Git; docs/register in Git).** Seven families EXTRACTED / SOURCE-VERIFIED / ZERO-RESIDUE VERIFIED / VISUALLY VERIFIED. **Not** JOEL APPROVED. Immutable source ZIP unchanged. Legal Content Gate **empty**. Document **04** = **INTERNAL ENTRY REFERENCE**. Document **05** = **COMMERCIAL_DRAFT / NOT FOR EXECUTION**. FG-012 / FG-017 / FG-021 **unchanged**. FG-021 **OPEN**. FG-022 **NOT CLOSED**.

**Prior:** **APPROVE FG-022 reusable approved document template family (docs/governance only).** [FG-022](feature-gates/FG-022-reusable-approved-document-template-family-v1.md) **APPROVED / IMPLEMENTATION NOT STARTED**. Extraction **not** performed. Immutable source ZIP unchanged. Legal Content Gate **empty**. Document **04** = **INTERNAL ENTRY REFERENCE**. Document **05** = **COMMERCIAL_DRAFT / NOT FOR EXECUTION**. FG-012 / FG-017 / FG-021 **unchanged**. FG-021 **OPEN**.

**Prior:** **CLOSE approved document template custody (docs + durable byte copy; no Git binaries).** Source ZIP SHA-256 `26f5e579c01651f2e304a76fbed1de7ab54ba144055937c2a1fc6871ebe5e874` re-verified. All **17** members PASS including families **01–07**. Durable store: `/Users/joelbrayman/Documents/CalibAi/Approved Document Templates/Allen Jacques Presentation Baseline - 2026-09-03/` (exact original ZIP only). ChatGPT Library logical collection `/CalibAi/Approved Document Templates/Allen Jacques Presentation Baseline - 2026-09-03/`. Desktop copy leave-in-place. **SOURCE CUSTODY CLOSED.** Document **04** = **INTERNAL ENTRY REFERENCE**. Document **05** legal = **COMMERCIAL_DRAFT / NOT APPROVED**. Legal Content Gate **empty**. Reusable extraction **not** performed. FG-012 / FG-017 / FG-021 **unchanged**. FG-021 **OPEN**.

**Prior:** **COMMIT recovered Allen Jacques approved document presentation baseline (docs only).** ZIP SHA-256 `26f5e579c01651f2e304a76fbed1de7ab54ba144055937c2a1fc6871ebe5e874` verified. Pin [architecture/approved-document-presentation-reference-baseline.md](architecture/approved-document-presentation-reference-baseline.md) + [testing/allen-jacques-garage-presentation-baseline-manifest.md](testing/allen-jacques-garage-presentation-baseline-manifest.md). Documents 01–07 **APPROVED PRESENTATION REFERENCES**. Document **04** = **INTERNAL ENTRY REFERENCE** (ZIP customer-facing folder is provenance only). Document **05** legal = **COMMERCIAL_DRAFT / NOT APPROVED**. Bytes **not** in Git. FG-021 **unchanged / OPEN**.

**Prior:** **REAL IPHONE NETWORK RETAIN / RETRY PASS.** HTTPS `https://192.168.134.223:5443`. Text-only. Wi-Fi off then Save: no Event POST (Case A); status **NEEDS RETRY**; feedback Safari `Load failed`. Today **Needs Retry** / `1 capture needs retry.` Retry: Flask **855195** `14:02:16` POST Event **201** then Original **201**. Event **31** / Original **29**, project **11**, `ORG-001`, Joel Brayman `user_id` 1. Body `FG021 Network Retry UAT`. UUIDs `532871ae-db01-4263-8562-d64baf4aa00e` / `022fe42b-8e8f-421b-a159-0c01eae15667`. Live **31** / **29**. Desktop Hub `/projects/11/field-events/31` same Event (Mac login required on HTTPS origin). Do **not** close FG-021. **HEIC REAL-DEVICE NOT YET TESTED.**

**Prior:** **REAL IPHONE VOICE SAVE PASS.** HTTPS `https://192.168.134.223:5443`. Flask **420792** `07:44:50` POST Event **201** then Original **201**. Event **30** / Original **28**, project **11**, `ORG-001`, Joel Brayman `user_id` 1. Actual MIME `audio/mp4` (file `ftyp iso5`), filename `note.m4a`, 179117 bytes, SHA-256 `f248655624f1f84f9c80a61cb7623443d96afd40069fdca29406f76a6072c1f9`. Client UUIDs populated. Event **29** POST at `07:44:11` has **no** Original (refresh leftover). Do **not** close FG-021. **HEIC REAL-DEVICE NOT YET TESTED.**

Prior: HTTPS iPhone voice UAT — Record/playback **PASS**; Save **FAIL**. Origin `https://192.168.134.223:5443` (Bonjour `.local` searched as Yahoo). CA profile installed; Certificate Trust Settings ON. Login/CSRF/Field Capture worked. Exact Save error: `Cannot safely keep this capture on this phone. Try photo or text later, or free storage.` HTTPS Flask **510616** / port **5443**: no Event/Original POST after Capture GET 200 at `07:09:07`. Live DB still **28** / **27**. Audio still persisted as IndexedDB Blob (`field.js` `saveNew`); images were repaired to `Uint8Array` bytes. **Do not repair from this observation.** Gate **NOT CLOSED**.

Prior: FG-021 **SECURE-CONTEXT INVESTIGATION COMPLETE** (read-only / environment-only; docs only). HTTPS **NOT IMPLEMENTED** at that time. Product code / tests / DB / migration **unchanged**. Confirmed: iPhone Safari `getUserMedia` / `MediaRecorder` require a secure context; HTTP LAN `http://192.168.134.223:5014` is **not** one. No existing trusted local cert; `which mkcert` failed; `cryptography` not installed (`flask --cert adhoc` unavailable). OpenSSL LibreSSL **3.3.6** present. Current UAT Flask **562293** remains HTTP-only `flask run --host=0.0.0.0 --port=5014 --no-debugger --no-reload`. No nginx/caddy; stock `httpd` not running. Bonjour name `Joels-MacBook-Air.local`. Smallest later local path (not started at investigation time): Flask `--cert`/`--key` with a newly generated cert whose SAN matches the hostname the iPhone will type, plus iOS CA profile + Certificate Trust Settings. IndexedDB is origin-scoped — do not migrate; from UAT observation no voice pending was created (Save never reached). Record can appear tappable when voice APIs are missing (captured, not repaired). Alembic current = head **`d2e3f4a5b6c7`**. Preserve **TAKE PHOTO PASS AS JPEG**. **HEIC REAL-DEVICE NOT YET TESTED.** Gate **NOT CLOSED**.

Prior: REAL IPHONE VOICE UAT **BLOCKED** at Record tap (observation only; no product-code change). Same iPhone Safari Capture page, Project **11**, HTTP LAN `http://192.168.134.223:5014`. Joel tapped Record; no recording-state UX, no reported permission prompt, no Save. Flask Cursor terminal **562293**: last Event/Original POST remains `14:43:26` / `14:43:27` Event **28** / Original **27** (Take Photo JPEG). Later iPhone `GET /field/projects/11/capture` at `14:52:41` from `192.168.134.202` — **no** Event POST and **no** Original POST after that. Live SQLite still **28** Events / **27** Originals; Event **26** still originals-empty; no new `kind=audio` Original for Project 11. Alembic current = head **`d2e3f4a5b6c7`**. Most likely stage: `enableVoice()` (`app/static/js/field.js`) disables `#field-record` and does not bind `startRecord` when `navigator.mediaDevices` / `getUserMedia` / `MediaRecorder` is missing on insecure HTTP LAN. Architecture already records that `getUserMedia` requires a secure context (HTTPS or localhost). **VOICE UAT BLOCKED — SECURE CONTEXT INVESTIGATION REQUIRED.** Preserve **TAKE PHOTO PASS AS JPEG**. **HEIC REAL-DEVICE NOT YET TESTED.** Gate **NOT CLOSED**.

Prior: REAL IPHONE TAKE PHOTO **PASS**. Flask **562293** `14:43:26` POST Event **201**, `14:43:27` Original **201**. Event **28** / Original **27**, project **11**, `image/jpeg`, filename `image.jpg`, 3568736 bytes. **TAKE PHOTO PASS AS JPEG.** **HEIC REAL-DEVICE NOT YET TESTED.**

Prior: SMALL SCREENSHOT IMAGE SAVE **PASS**. Event **27** / Original **26**, `image/png`, 160522 bytes. `field.js` **200** at 14:37. Uint8Array persist repair `1422279`.

Prior: Screenshot re-UAT after File→Blob (`ada1b7c`) — **FAIL**. Live **25/25**. Events **19–25** text-only. Zero image Originals.

Prior: Bounded IndexedDB photo-put repair **LANDED** (`ada1b7c`) in `app/static/js/field.js`: image `File` → `arrayBuffer()` → `new Blob([buffer], { type: original MIME })` before `pending_originals` put. Dedicated FG-021 **17**; focused **145**; full **555**. Alembic still `d2e3f4a5b6c7`.

Prior: Objective verify of Joel-reported iPhone Safari FG-021 text-only Save (`FG021-IPHON-UAT-TEXT`, no photo). Live `instance/brayman_estimator.db` now **18/18** Events/Originals (prior **17/17**). Event **18** / Original **18** on project **11** / `ORG-001`; actor **Joel Brayman** (`user_id` 1); `occurred_at` `2026-09-02 17:02:30.474201` UTC (= 13:02:30 EDT); `client_capture_uuid` and `client_original_uuid` populated. Flask Cursor terminal **562293** at `02/Sep/2026 13:02:30` from `192.168.134.202`: `POST /api/v1/projects/11/field-events` **201** then `POST .../field-events/18/originals` **201**. UUID repair + text path **PASS**. Photo / IndexedDB quota **still open**. Gate **NOT CLOSED**. Next: one small screenshot/JPEG — do **not** attach a full-size HEIC yet.

Prior: Bounded FG-021 iPhone HTTP LAN Save Original repair. `app/static/js/field.js` `newUuid()` now uses `crypto.randomUUID()` when available, else `crypto.getRandomValues` 16-byte RFC 4122 v4 (version/variant bits). No `Math.random()`. Pre-POST UUID failure shows existing Capture feedback: `Unable to prepare this capture for saving. Please retry.` Dedicated FG-021 **15**; focused **143**; full **553**. Live current remains head `d2e3f4a5b6c7`. No migration. CSRF/auth unchanged. Gate **NOT CLOSED**.

Prior: FG-021 live migration only. Identified live SQLite `instance/brayman_estimator.db`. Created one gitignored byte-for-byte pre-migration copy `instance/brayman_estimator-backup-before-fg021-d2e3f4a5b6c7.db` (outside Git; not used for recovery). Applied `flask db upgrade` `c1d2e3f4a5b6` → `d2e3f4a5b6c7`. Live current = head. Product/test/migration files **not** changed in that pass. Gate **NOT CLOSED**.

Prior: FG-021 Field Web V1 product implementation. `/field` Today + Project confirm + Capture. IndexedDB. Idempotent Event/Original API. Display GET. Revision `d2e3f4a5b6c7` created. Live upgrade **not** run in that pass. Gate **NOT CLOSED**.

Prior: docs-only **ADR-043 Proposed + FG-021 DRAFT / NOT APPROVED** (`6273fa4`). Copy-icon Cursor rule `d69cfb6` pushed separately. Canonical architecture: [architecture/field-web-today-and-capture.md](architecture/field-web-today-and-capture.md).

Prior: **FG-020 LIVE MIGRATION / OFFICE UAT CLOSE.** Gate **CLOSED / OPERATIONAL FOR UAT**. Live current = head `c1d2e3f4a5b6`. Office UAT port **5013**, project **12**. Dedicated **44** / focused **128** / full **538**. Item 11 **COMPLETE**.

Prior: docs-only **NATIVE SIGNED CHANGE ORDER counsel-review specification PREPARED**. Canonical counsel document: [legal/native-signing-process-counsel-review.md](legal/native-signing-process-counsel-review.md) — **DRAFT FOR ONTARIO COUNSEL REVIEW / NOT LEGAL APPROVAL / NOT IMPLEMENTED**. Architecture recon remains **COMPLETE**. Recommendation **NATIVE V1**. Implementation **NOT AUTHORIZED**. No signing Feature Gate.

Prior: docs-only **CONTRACT / E-SIGNATURE / SIGNED CHANGE ORDER** architecture reconnaissance **COMPLETE**. Canonical: [architecture/contract-esignature-and-signed-change-order.md](architecture/contract-esignature-and-signed-change-order.md). Recommendation **NATIVE V1**. Implementation **NOT AUTHORIZED**.

Prior: **FG-020 Media Compatibility increment** — automatic HEIC/HEIF → JPEG Compatible Renditions after Original Source preservation. Image-only. No new migration. Live upgrade **not** run. Storage-lifecycle docs preserved and committed with this increment. FG-020 remains **IMPLEMENTED / LIVE MIGRATION PENDING**.

Prior: docs-only **BUILD media compatibility + project-close storage lifecycle** clarification. Pin [build-media-storage-lifecycle.md](architecture/build-media-storage-lifecycle.md). Committed together with the rendition increment (not left stranded).

Prior: **implement FG-020 BUILD Field Capture V1**. Product code, tests, docs, additive revision `c1d2e3f4a5b6`. Live `flask db upgrade` **not** run. Status **IMPLEMENTED / LIVE MIGRATION PENDING**. Not closed.

Prior: docs-only **approve FG-020** and **record implementation reconnaissance**. BUILD product code **not started**. No migration.

Prior: docs-only **accept ADR-042** and **draft FG-020** (**NOT APPROVED**). No BUILD code. No migration.

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
- FG-019: GET-only `/api/v1/me`, `/api/v1/projects`, `/api/v1/projects/<id>` plus **narrow** FG-020 BUILD POST allow-list; `app/services/shared_api.py`; JSON 401/403/404/405/409. API UAT port **5012**.
- FG-018: `User`; `UserMembership`; `app/services/auth.py`; `/login` `/logout`; CSRFProtect; membership org context; CLI bootstrap/reset. Live current `b0c1d2e3f4a5`. Office UAT port **5011**.
- FG-020: `FieldCaptureEvent`; `FieldCaptureOriginal`; `FieldCaptureDerivedCandidate`; `app/services/build.py`; `app/services/build_storage.py`; `app/services/build_rendition.py`; office `/projects/<id>/field-events/...` including `/display` JPEG; Hub Field Observations; `flask build propose-derived-candidate`. Gate-at-close live current = head was `c1d2e3f4a5b6`.
- FG-021: `/field` Today + Project confirm + Capture; IndexedDB `calibai-field-v1`; idempotent Event/Original POST; display GET; `client_capture_uuid` / `client_original_uuid`. **Gate-at-close** live current `d2e3f4a5b6c7` (later superseded by FG-023 `e3f4a5b6c7d8`).
- FG-023: `ProjectDirectCostActual` / `project_direct_cost_actuals`; `app/services/direct_cost_actuals.py`; `app/services/monitor.py` `assemble_monitor_v1`; Hub `#hub-monitor`; BUILD create/supersede POSTs; additive revision `e3f4a5b6c7d8` **applied live** 2026-09-07. Product SHA `7dd4d82c927ec2c38a0562e7e1cdedbccabb6662`. Office UAT project **id 13**.
- FG-026: `TakeoffEstimateInsertion` / `TakeoffEstimateInsertionCitation`; `app/services/takeoff_estimate_mapping.py`; office `/projects/<id>/plans/takeoff/packages/<package_id>/map`. Additive revision `f4a5b6c7d8e9` **applied live** 2026-09-08. Product SHA **`aa4c71800586e0b8e2a63931bcdc8bc44d87a489`**. Office UAT port **5015**. Gate **CLOSED / OPERATIONAL FOR UAT**.
- FG-027: `EstimateCostingSnapshot` / `EstimateCostingSnapshotLine`; `app/services/estimate_costing.py`; Estimate version Costing Review + Approve All Costing; Pricing consume / stale. Additive `a5b6c7d8e9f0` **applied live**. Implementation SHA **`c751d72b32f1ed415375719df2fd69936ace64d7`**. Repair SHA **`72949f99da2b56ec06e95e16e29fa194a6730bbd`**. Gate **CLOSED / OPERATIONAL FOR UAT**. Office UAT continuation **PASS**.
- FG-025: `app/presentation/contractor_copy.py` Slice 1–5 display mapping (Hub MONITOR, Project Hub, office PRICE specialist, office shell, Field Web). Slice 5 product SHA **`5b497905086554214e85f69afd8101d88f89161c`**. Gate **NOT CLOSED**. Remaining surfaces **NOT AUTHORIZED**.
- FG-032: `EstimateQuickBooksPackage` / sales + cost-class lines + `EstimateQuickBooksEntryEvent` + `EstimateQuickBooksEntryOccupancy`; `app/services/estimate_quickbooks.py`; Hub PRICE `/projects/<id>/quickbooks-entry`; A+B additive **`e9f0a1b2c3d4` applied live** 2026-09-11; Slice C events **`f0a1b2c3d4e5`** and occupancy **`f1a2b3c4d5e6` applied live** 2026-09-11. A+B product SHA **`70e571140e12377aa5bd009b598530576401113b`**. Canonical UAT project **id 26**. Slices A+B **LIVE-MIGRATED / BOUNDED OFFICE UAT PASS / OPERATIONAL FOR UAT**. Slice C **LIVE-MIGRATED / BOUNDED OFFICE UAT PASS / OPERATIONAL FOR UAT**. Gate **CLOSED / OPERATIONAL FOR UAT**. V1-05 **COMPLETE**.

## 10. TEST / UAT / MIGRATION STATUS

- Live current **`d3e4f5a6b7c8 (head)`**. Repository head **`d3e4f5a6b7c8`**. One graph head. FG-024 Slice C **`d3e4f5a6b7c8` applied live** 2026-09-13. FG-024 Slice B **`c2d3e4f5a6b7` applied live** 2026-09-13. FG-024 Slice A **`b1c2d3e4f5a6` applied live** 2026-09-13. FG-032 A+B **`e9f0a1b2c3d4` applied live** 2026-09-11. Slice C events **`f0a1b2c3d4e5`** and occupancy **`f1a2b3c4d5e6` applied live** 2026-09-11 (historical **gate-at-close** live current for FG-032; superseded as live current today). Canonical DEMO UAT project **id 26**. Latest governed full suite (this 14 Sep 2026 docs-only reconciliation): **825 passed**, 2771 warnings, **258.44s**. HISTORICAL FG-024 Slice C live-UAT close: **825 passed**, 2771 warnings, **266.33s**. HISTORICAL FG-032 Slice C UAT: dedicated **37 passed** / 16.61s; regressions **256 passed** / 88.48s; full **765 passed** / 299.75s; office UAT **97 cases PASS**. Historical occupancy-repair full **765** / 422.30s remain historical. Historical Slice C implementation dedicated **36 passed** / full **764 passed**. Historical A+B post-migrate dedicated **23 passed** (12.96s) / full **751 passed**. Evidence [testing/fg024-slice-c-live-migrate-bounded-uat-record.md](testing/fg024-slice-c-live-migrate-bounded-uat-record.md), [testing/fg032-slice-c-live-migrate-bounded-uat-record.md](testing/fg032-slice-c-live-migrate-bounded-uat-record.md) and [testing/fg032-slices-ab-live-migrate-bounded-uat-record.md](testing/fg032-slices-ab-live-migrate-bounded-uat-record.md).
- Historical FG-027-era note (superseded as live current): Repository graph head `a5b6c7d8e9f0`. Live current `a5b6c7d8e9f0`. Applied `f4a5b6c7d8e9` → `a5b6c7d8e9f0` (2026-09-08 FG-027). No new revision in the override-provenance repair. Live costing snapshot tables exist; no CURRENT snapshot on EstimateVersion 9. Live UAT line 7 residue: working unit_cost **250**, `library_unit_cost_reference` **NULL**.
- Latest product-changing: dedicated FG-027 **20**; estimating **29**; pricing **52**; FG-026 **20**; A–D bundle **121**; full suite **652 passed** (repair SHA `72949f99da2b56ec06e95e16e29fa194a6730bbd`). Historical FG-027 implementation dedicated **15** / full **647**. Historical FG-026 dedicated **20** / full **632**. Historical Slice 5 dedicated FG-025 **19**; Field-focused **83**; prompt governed list **190**; full suite **612 passed** remain the pre-FG-026 baseline. Dedicated FG-023 **35**; focused **149**; historical Slice A close focused **126**; pre-Slice-B focused **137**; full suite **593 passed** remain historical close-time FG-023 evidence.
- Historical dedicated: FG-021 **20**; FG-020 **44** (33 + 11 media compatibility); FG-019 **34**; FG-018 **37**; FG-017 **22**; FG-016 **37**; FG-015 permit foundation **19**; FG-014 material catalogue **35**; FG-013 upload 27; FG-012 19; Project Hub (post-FG-020 assertions); take-off 18; Plan Intelligence 56; Pricing 33; Labour 25; Historical 11.
- Prior FG-021 close bundle (historical): focused (Hub + FG-018 + FG-019 + both FG-020 + FG-021) **148 passed**. Full suite at FG-021 close **558 passed**.
- Live API FG-019 UAT **PASSED** on port **5012**. Live office FG-018 UAT **PASSED** on port **5011**. FG-017 UAT remains **PASSED** on port **5010**. Pratt Permit Report UAT remains **PASSED** on port **5009** (project id 9). FG-020 office UAT **PASSED** on port **5013**.

## 11. PROTECTED STATE

- Constitution Articles 1–12
- Accepted proposal immutability; live DB has labeled Draft `PROP-FG012-UAT-GM` (not Accepted)
- PlanDocument bytes / SHA-256 immutability; historical workbook content and hashes outside Git (`~/Desktop/CalibAi Historical Estimates`) — **legacy corpus not modified**. Productized FG-013 bytes (when implemented) live under ADR-032 app-managed storage, not Git.
- `HistoricalLabourItem` source facts **not rewritten** (120 rows; 43 with stored `hourly_rate = 0.13` remain evidence defects)
- Human review is authoritative; AI confidence advisory only
- ORG isolation; no cross-org pooling; ORG-001 $65 / 15% GM are org-specific, not CalibAi defaults
- Legal Content Gate for construction contract/warranty — registers **empty**; Document 05 does **not** populate them; [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / SLICE A CLOSED / OPERATIONAL FOR UAT / SLICE B CLOSED / OPERATIONAL FOR UAT / SLICE C CLOSED / OPERATIONAL FOR UAT / OVERALL OPEN / PARTIAL**; Slice D **NOT AUTHORIZED**
- Approved Allen Jacques presentation source ZIP — SHA-256 `26f5e579c01651f2e304a76fbed1de7ab54ba144055937c2a1fc6871ebe5e874`; durable bytes outside Git at `/Users/joelbrayman/Documents/CalibAi/Approved Document Templates/Allen Jacques Presentation Baseline - 2026-09-03/`; **not** in `instance/`; [FG-022](feature-gates/FG-022-reusable-approved-document-template-family-v1.md) derived masters at `…/Reusable Master Template Family V1/`; **CLOSED / APPROVED REUSABLE MASTER FAMILY V1**; Family 05 legal remains **COMMERCIAL_DRAFT / NOT LEGALLY APPROVED**
- Append-only audit history (including ORG-999 probe row and UAT reconciliation)

## 12. ACCEPTED ADRs

002, 005, 006, 007, 009, 011, 017, 018, 019, 020, **021**, 022, 023, 024, 025, 026, 027, 028, 029, 030, 031, **032**, **033**, **034**, **035**, **036**, **037**, **038**, **039**, **040**, **041**, **042**, **043**, **044**, **045**, **046**, **047**, **048**, **049**, **050**, **051**.

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
- **FG-017:** **CLOSED / OPERATIONAL FOR UAT**. **Gate-at-close** current = head `a9b0c1d2e3f4`. Office UAT port **5010**. ADR-040 **Accepted**. Change Order / Permit branding **not** in this gate. Live current today is `d3e4f5a6b7c8`.
- **FG-018:** **CLOSED / OPERATIONAL FOR UAT**. [ADR-041](adr/ADR-041-user-membership-and-office-authentication.md) **Accepted**. Live current `b0c1d2e3f4a5`. Office UAT port **5011**. Shared API **out of this gate**. Not production-security certification.
- **FG-019:** **CLOSED / OPERATIONAL FOR UAT**. Shared API Foundation V1. GET-only `/api/v1` plus FG-020 BUILD POST allow-list. No FG-019 migration. API UAT port **5012**.
- **FG-020:** **CLOSED / OPERATIONAL FOR UAT**. [ADR-042](adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) **Accepted**. Image-only Compatible Renditions **implemented**. Gate-at-close live current = head was `c1d2e3f4a5b6`. Office UAT port **5013**. Dedicated **44**. Full suite **538**. Field Web **not** in this gate. Closeout **not** started.
- **FG-021:** **CLOSED** (2026-09-06). IMPLEMENTED / LIVE-MIGRATED / REAL-IPHONE UAT COMPLETE SUBJECT TO THE EXPLICIT SESSION-EXPIRY DEFERRED EXCEPTION. [ADR-043](adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md) **Accepted**. **Gate-at-close** live current = head `d2e3f4a5b6c7` (later superseded by FG-023 `e3f4a5b6c7d8`). Text **PASS**. Screenshot PNG **PASS**. **TAKE PHOTO PASS AS JPEG.** Voice Save **PASS** (Event **30**, `audio/mp4`). Network retain/retry **PASS** (Event **31**, text). Browser-close IndexedDB recovery **PASS** (Event **32** / Original **30**, JPEG). **HEIC REAL-DEVICE PASS** (Event **34** / Original **32**, Files/Browse `IMG_5351.HEIC`). **MIXED CAPTURE PASS** (Event **35**, Originals **33** text / **34** audio / **35** JPEG). **BACKGROUND / FOREGROUND PERSISTENCE PASS** (Event **36** / Original **36**, text). **CSRF RECOVERY PASS** (Event **39** / Original **39**, text). Portrait **PASS**. One-handed **PASS**. Outdoor readability **PASS**. **LANDSCAPE TOLERANCE PASS.** **ORIENTATION / PORTRAIT PASS.** **CURRENT-IPHONE FIELD-USABILITY PASS.** Desktop continuity **PASS**. **SESSION-EXPIRY RECOVERY: DEFERRED / NOT YET EXERCISED** (NOT PASS / NOT FAIL / NOT N/A / NOT WAIVED). **OLDER SUPPORTED IPHONE / SAFARI WAIVED AS NOT PRACTICAL.** Observation Delete **QUEUED / NOT AUTHORIZED / NOT IMPLEMENTED / NON-BLOCKING**. Live **39** Events / **39** Originals. Dedicated **20**. Focused **148**. Full **558**.
- **FG-022:** **CLOSED / APPROVED REUSABLE MASTER FAMILY V1**. Reusable approved document template family V1. Seven DOCX + seven verification PDFs. Parallel document-template track. Legal Content Gate **empty**. Family 05 **COMMERCIAL_DRAFT / NOT LEGALLY APPROVED**. Does **not** alter FG-021 or item 12.
- **FG-023:** **CLOSED / OPERATIONAL FOR UAT**. Slice A + Slice B **IMPLEMENTED / LIVE-MIGRATED**. Slice C **MIGRATION COMPLETE / OFFICE UAT COMPLETE / PASS**. MONITOR V1 **IMPLEMENTED / LIVE-MIGRATED / OFFICE-UAT-VERIFIED / CLOSED**. Live current = heads `e3f4a5b6c7d8`. Office UAT port **5014**. Synthetic project **id 13** `FG023-UAT-MONITOR`. Close-time dedicated **35**. Current focused **149**. Historical Slice A focused **126**. Pre-Slice-B focused **137**. Full **593**.
- **FG-024:** **FUTURE / RECORDED / SLICE A CLOSED / OPERATIONAL FOR UAT / SLICE B CLOSED / OPERATIONAL FOR UAT / SLICE C CLOSED / OPERATIONAL FOR UAT / OVERALL OPEN / PARTIAL**. One linked North American CONTRACT intelligence gate (library / update engine / frozen snapshot / monitoring). Slice A preflight [architecture/fg-024-slice-a-legal-content-library-preflight.md](architecture/fg-024-slice-a-legal-content-library-preflight.md). Slice B preflight [architecture/fg-024-slice-b-legal-content-source-lifecycle-preflight.md](architecture/fg-024-slice-b-legal-content-source-lifecycle-preflight.md). Slice C preflight [architecture/fg-024-slice-c-contract-generation-snapshot-preflight.md](architecture/fg-024-slice-c-contract-generation-snapshot-preflight.md). Evidence [testing/fg024-slice-c-live-migrate-bounded-uat-record.md](testing/fg024-slice-c-live-migrate-bounded-uat-record.md). [ADR-050](adr/ADR-050-north-american-legal-content-library-ownership.md) **Accepted**. [ADR-051](adr/ADR-051-legal-content-source-and-update-lifecycle.md) **Accepted**. Slice D **not authorized**. Legal Content Gate **empty**. Does **not** alter FG-023. FG-025 is **not** a split of this gate.
- **FG-025:** **FUTURE / RECORDED / IMPLEMENTATION PREFLIGHT COMPLETE / SLICE 1 IMPLEMENTED / TESTED / COMMITTED / PUSHED / SLICE 2 IMPLEMENTED / TESTED / COMMITTED / PUSHED / SLICE 3 IMPLEMENTED / TESTED / COMMITTED / PUSHED / SLICE 4 IMPLEMENTED / TESTED / COMMITTED / PUSHED / SLICE 5 IMPLEMENTED / TESTED / COMMITTED / PUSHED / SLICE 6 IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT CLOSED / NOT YET PRODUCT-WIDE COMPLETE**. Remaining surfaces **NOT AUTHORIZED**. Does **not** alter FG-023.
- **FG-026:** **CLOSED / OPERATIONAL FOR UAT**. PLAN proposes / Estimating commits. Package approval does **not** insert. Additive `f4a5b6c7d8e9` **applied live**. Office UAT **PASS** on port **5015**.
- **FG-027:** **CLOSED / OPERATIONAL FOR UAT**. **IMPLEMENTED / TESTED / COMMITTED / PUSHED / LIVE-MIGRATED / OFFICE UAT PASS**. Repair SHA **`72949f99da2b56ec06e95e16e29fa194a6730bbd`**. V1-02 **COMPLETE**. [ADR-044](adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) **Accepted**. Approve All = costing approval only. Additive `a5b6c7d8e9f0` **applied live**. Does **not** accept ADR-008.

## 15. CHAT → REPOSITORY DELTA LEDGER RESULT

**2026-09-08 V1-02 / FG-027 bounded office UAT continuation + close.** Remaining office UAT **PASS** on EstimateVersion **id 9** / port **5016**. Legacy override freeze **PASS**. Approve All / supersession / Pricing consume / STALE / re-apply **PASS**. Gate **CLOSED / OPERATIONAL FOR UAT**. V1-02 **COMPLETE**. Readiness **45%**. No new migration. No product-code change. Product tests **not** rerun (last verified dedicated **20** / full **652**).

**2026-09-08 V1-02 / FG-027 bounded legacy override-provenance repair.** Product SHA **`72949f99da2b56ec06e95e16e29fa194a6730bbd`**. NULL CostItem/Assembly `library_unit_cost_reference` now freezes pre-edit working `unit_cost` on Draft cost edit. Dedicated **20** / bundle **121** / full **652**. No new migration. Live line 7 **not** mutated in the repair pass. UAT **not** resumed in the repair pass. Gate was then **NOT CLOSED**.

**2026-09-08 V1-02 / FG-027 live migrate + bounded office UAT.** Live `flask db upgrade a5b6c7d8e9f0` **PASS**. Office UAT port **5016**. Zero-cost BLOCK **PASS**. Failed approval atomicity **PASS**. Manual override provenance **FAIL** (EstimateLineItem id 7 `library_unit_cost_reference` NULL; working unit_cost 250 classified `LIBRARY_ASSEMBLY`; reason not persisted). UAT **STOPPED**. No costing snapshot. No Pricing apply. Gate **NOT CLOSED**. Product tests **not** rerun. V1 readiness remains **39%**.

**2026-09-08 V1-02 / FG-027 product implementation.** [FG-027](feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) **IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT LIVE-MIGRATED / UAT NOT AUTHORIZED / NOT CLOSED** at that commit. Product SHA **`c751d72b32f1ed415375719df2fd69936ace64d7`**. Migration file `a5b6c7d8e9f0`. Dedicated **15** / full **647**. Live current at that commit remained **`f4a5b6c7d8e9`**. V1 readiness remains **39%**. Subsequent live migrate supersedes the “not live-migrated” current-authority pin.

**2026-09-08 V1-02 / FG-027 ADR + Feature Gate + preflight.** [FG-027](feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) **RECORDED / ARCHITECTURE PREFLIGHT COMPLETE / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED** at that recording. [ADR-044](adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) **Accepted**. Docs only. No product code. No migration at that recording. Completeness for that recording: ADR + Feature Gate + preflight + current-authority pins. V1 readiness remains **39%**. Subsequent product implementation supersedes the “not implemented” current-authority pin.

**2026-09-08 FG-026 live migrate + bounded office UAT.** [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **CLOSED / OPERATIONAL FOR UAT**. Live `flask db upgrade f4a5b6c7d8e9` **PASS**. Office UAT **PASS** on port **5015**. TakeoffPackage **id 1** unchanged. Estimate **id 9** / version **id 9** / line **id 7** / insertion **id 1** / **3** citations. V1-01 **COMPLETE**. Readiness **39%**. Product tests **not** rerun.

**2026-09-08 FG-026 implementation.** [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT LIVE-MIGRATED / UAT NOT RUN / NOT CLOSED**. Product code + additive `f4a5b6c7d8e9`. Dedicated **20** / full **632**. Live DB **not** mutated at implementation time. UAT **NOT RUN** at implementation time.

**2026-09-08 FG-026 recording.** [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **FUTURE / RECORDED / ARCHITECTURE PREFLIGHT COMPLETE / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. Docs only. Preflight [architecture/fg-026-takeoff-to-estimate-mapping-preflight.md](architecture/fg-026-takeoff-to-estimate-mapping-preflight.md). Does **not** authorize implementation. Does **not** create a migration. Does **not** write live DB. Completeness for this recording: Feature Gate + preflight + current-authority pins **IN THIS COMMIT**.

**2026-09-08 Review Turnover.** Chat history is not the system of record. Classifications:

| Item | Classification |
|------|----------------|
| FG-025 Slice 5 Field Web copy / SHA `5b497905086554214e85f69afd8101d88f89161c` / dedicated **19** / Field-focused **83** / governed **190** / full **612** | **ALREADY IN REPOSITORY** (product). SHA pin was **PARTIALLY MEMORIALIZED** — pinned this pass |
| Live Alembic `e3f4a5b6c7d8`; Field **39 / 39**; Project 13 five actuals | **ALREADY IN REPOSITORY** (verified this pass) |
| FG-023 CLOSED; FG-024 FUTURE / NOT IMPLEMENTATION-AUTHORIZED; FG-025 NOT CLOSED; remaining surfaces NOT AUTHORIZED | **ALREADY IN REPOSITORY** |
| §3 ADR-021 “Hub UI not implemented / gate not closed” | **SUPERSEDED** — repaired this pass |
| §19 “Do not start Slice 5” after Slice 5 implemented | **SUPERSEDED** — repaired this pass |
| §10 / §21 / §22 still citing FG-023 full **593** as latest product-changing suite | **PARTIALLY MEMORIALIZED** — repaired this pass |
| Durable-storage A–J still “Slice 1 / Do not start Slice 2” | **SUPERSEDED** — repaired this pass |
| Feature-gates README FG-017 “live current today is d2e3f4a5b6c7”; FG-021 index “Live current = head d2e3…”; roadmap “Do not start Slice 5” | **SUPERSEDED** — repaired this pass |
| Observation Delete; SESSION-EXPIRY RECOVERY deferred; no Slice 6 authorization | **ALREADY IN REPOSITORY** |

**Completeness test:** Is there any material approved decision, requirement, implementation fact, protected baseline, unresolved decision, or current authorization present in the active conversation / Turnover Delta Ledger that is not represented in the repository? **NO — verified through Turnover Delta Ledger reconciliation.**

**2026-09-07 Review Turnover.** Chat history is not the system of record. Classifications:

| Item | Classification |
|------|----------------|
| FG-023 Slice A model / services / tests / migration `e3f4a5b6c7d8` / SHA `2553cf09bdd6b8018112d7eb4b682f87aa103b01` | **ALREADY IN REPOSITORY** |
| Frozen FG-023 commercial identities (Accepted Proposal lock, `MISSING_CUSTOMER_COMMITMENT`, `AMBIGUOUS_COMMITMENT`, CO delta, `MISSING_ACTUALS` ≠ zero, Field Events evidence only, no NET PROFIT, no forecast-final GM) | **ALREADY IN REPOSITORY** |
| `incurred_on` any parseable calendar date (no today cutoff) | **ALREADY IN REPOSITORY** |
| Live current `d2e3f4a5b6c7`; repo head `e3f4a5b6c7d8`; live **39** / **39**; no live actuals table | **ALREADY IN REPOSITORY** (verified this pass) |
| FG-021 CLOSED; SESSION-EXPIRY **DEFERRED / NOT YET EXERCISED**; Observation Delete **QUEUED** | **ALREADY IN REPOSITORY** |
| FG-022 CLOSED / APPROVED REUSABLE MASTER FAMILY V1 | **ALREADY IN REPOSITORY** |
| Stale §9 / §10 / §14 / §18 current-authority pins (FG-021-era tests 558/148; repo head `d2e3f4a5b6c7`; MONITOR listed unimplemented wholesale) | **PARTIALLY MEMORIALIZED** — repaired this pass |
| Stale §22 Fresh Chat Startup Prompt (`DO NOT start Item 13 / MONITOR`; Alembic current = heads `d2e3f4a5b6c7`) | **SUPERSEDED** — replaced this pass |
| Slice B product code / live migrate / office UAT | **DISCUSSION ONLY / NOT APPROVED** as this-pass work. Slice B **preflight COMPLETE** 2026-09-07. Next governed action is Slice B **implementation** (separate authorization), not product code from this preflight. |

**2026-09-07 Slice B implementation.** Hub `#hub-monitor` + BUILD actuals POSTs **IMPLEMENTED / NOT LIVE-MIGRATED**. Live migrate / office UAT remain **NOT APPROVED**. Dedicated **35**. Focused **149**. Full **593**.

**2026-09-07 FG-024 recording.** [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. Docs only. Does **not** authorize implementation. Does **not** interrupt FG-023.

**2026-09-07 Slice C execution.** Live migrate `e3f4a5b6c7d8` **PASS**. Office UAT **PASS**. Gate remains **OPEN**. FG-024 remains **FUTURE / NOT IMPLEMENTATION-AUTHORIZED**.

**2026-09-07 FG-025 recording.** [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. Docs only. Does **not** rewrite UI. Does **not** interrupt FG-023.

**2026-09-07 FG-023 close.** [FG-023](feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) **CLOSED / OPERATIONAL FOR UAT**. MONITOR V1 **IMPLEMENTED / LIVE-MIGRATED / OFFICE-UAT-VERIFIED / CLOSED**. Close-time tests **35 / 149 / 593**. No product-code change. Hub MONITOR lifecycle already operational; LEARN remains Future.

**2026-09-07 FG-025 Slice 1 implementation.** [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 1 IMPLEMENTED / NOT CLOSED**. Hub MONITOR display mapping. Remaining slices **NOT AUTHORIZED**.

**2026-09-08 FG-025 Slice 5 implementation.** [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 5 IMPLEMENTED / NOT CLOSED**. Field Web copy. Remaining surfaces **NOT AUTHORIZED**.

**2026-09-08 FG-025 Slice 4 close-record documentation reconciliation.** Docs only. Slice 4 product SHA pinned **`56e16f03446f982d577d2a3f0d3375ef865e1dc9`**. This reconciliation is **not** the Slice 4 product SHA. Remaining surfaces **NOT AUTHORIZED**.

**2026-09-08 FG-025 Slice 4 implementation.** [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 4 IMPLEMENTED / NOT CLOSED**. Shared office nav/dashboard/auth/Settings copy. Remaining surfaces **NOT AUTHORIZED**.

**2026-09-07 FG-025 Slice 2 implementation.** [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 2 IMPLEMENTED / NOT CLOSED**. Project Hub PLAN/permit, pricing-assumptions, and actual-cost history copy. Remaining slices **NOT AUTHORIZED**.

**2026-09-07 FG-025 implementation preflight.** [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **IMPLEMENTATION PREFLIGHT COMPLETE**. Docs only. Did **not** rewrite UI. Did **not** authorize remaining slices.

**Completeness test (historical 2026-09-07 Review Turnover):** answered **NO** at that pass. Superseded by the 2026-09-08 Review Turnover completeness test above.

## 16. OPEN DECISIONS

- Real external AI provider / ADR-010 (not authorized)
- Phase D reviewed quantity → estimate mapping — [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **CLOSED / OPERATIONAL FOR UAT**. V1-02 / [FG-027](feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) **CLOSED / OPERATIONAL FOR UAT**.
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
- **Organization Brand Profile** is **CLOSED / OPERATIONAL FOR UAT** ([organization-brand-profile.md](architecture/organization-brand-profile.md)). [ADR-040](adr/ADR-040-organization-brand-profile.md) **Accepted**. [FG-017](feature-gates/FG-017-organization-brand-profile-v1.md). Settings at `/settings/brand-profile`. Proposal preview/PDF consume snapshot-or-current. **Gate-at-close** current = head `a9b0c1d2e3f4`. Office UAT port **5010**. Live current today is `f4a5b6c7d8e9`.
- **FG-023 Slice C** live migrate + office UAT **COMPLETE / PASS** (2026-09-07). Synthetic `FG023-UAT-MONITOR` project **id 13**. Gate **CLOSED / OPERATIONAL FOR UAT**.
- **GM Hub display** pinned in Slice B preflight B5: percent via `as_money(gm * 100)` two decimals; missing GM is the state label, never `0.00%` / Inf / NaN. Not a stored column.
- **SESSION-EXPIRY RECOVERY** remains **DEFERRED / NOT YET EXERCISED** (NOT PASS / NOT FAIL / NOT N/A / NOT WAIVED).
- **Authentication / actor identity + shared API** — [ADR-041](adr/ADR-041-user-membership-and-office-authentication.md) **Accepted**. [FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-019](feature-gates/FG-019-shared-api-foundation-v1.md) **CLOSED / OPERATIONAL FOR UAT**. Roadmap item 10 is **COMPLETE**. [ADR-042](adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) **Accepted**. [FG-020](feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) **CLOSED / OPERATIONAL FOR UAT**. Item 12 Field Web is **CLOSED** ([FG-021](feature-gates/FG-021-field-web-v1-today-and-capture.md); SESSION-EXPIRY RECOVERY **DEFERRED / NOT YET EXERCISED**).
- **Change Order document family** is **FUTURE / NOT IMPLEMENTED** ([change-order-document-family.md](architecture/change-order-document-family.md)). Existing Change Order record remains authoritative. Do not create a second entity. Not email. Not field UX.
- **[FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md)** is **FUTURE / RECORDED / SLICE A CLOSED / OPERATIONAL FOR UAT / SLICE B CLOSED / OPERATIONAL FOR UAT / SLICE C CLOSED / OPERATIONAL FOR UAT / OVERALL OPEN / PARTIAL**. One linked gate. Slice D **not authorized**. Legal Content Gate remains **empty**. Do **not** populate jurisdictions. Do **not** begin Slice D. FG-025 is **not** a split of this gate.
- **[FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md)** is **FUTURE / RECORDED / IMPLEMENTATION PREFLIGHT COMPLETE / SLICE 1 IMPLEMENTED / SLICE 2 IMPLEMENTED / SLICE 3 IMPLEMENTED / SLICE 4 IMPLEMENTED / SLICE 5 IMPLEMENTED / SLICE 6 IMPLEMENTED / NOT CLOSED**. Remaining surfaces **NOT AUTHORIZED**. Do **not** start another FG-025 slice from this handoff.
- **[FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md)** is **CLOSED / OPERATIONAL FOR UAT**. PLAN proposes / Estimating commits. Additive `f4a5b6c7d8e9` **applied live**.
- **[FG-027](feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md)** is **CLOSED / OPERATIONAL FOR UAT**. [ADR-044](adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) **Accepted**. Do **not** accept ADR-008.
- **[FG-029](feature-gates/FG-029-bmr-supplier-workflow-v1.md)** is **CLOSED / OPERATIONAL FOR UAT**. [ADR-046](adr/ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) **Accepted**. Preflight [fg-029-bmr-supplier-workflow-v1-preflight.md](architecture/fg-029-bmr-supplier-workflow-v1-preflight.md). Live current **`b6c7d8e9f0a1`**. UAT project **id 14**. Evidence [testing/fg029-live-migrate-bounded-uat-record.md](testing/fg029-live-migrate-bounded-uat-record.md).

## 17. KNOWN RISKS / UNRESOLVED PRODUCT ITEMS

**FG-008 (evidence defects — do not repair as product bugs):** 0.13 hourly-rate cluster (43/120); material SKUs classified as labour; historical crew/duration inconsistencies.

**FG-009 carry-forward:** Optional layers unspecified as above. Labour-snapshot Direct Labour Cost not in estimate basis by default.

**FG-012 residual:** Office proposal create/detail still lists Overhead/Profit amounts (zero when named method governs). Customer preview/PDF do not. Live FG-009 UAT estimates have no Allowance lines and no labour snapshots; dedicated tests cover those cases. Synthetic UAT residue including `PROP-FG012-UAT-GM`.

**FG-010:** 6 `takeoff.candidate.accept` PlanAuditEvent rows vs 4 accepted candidate rows (duplicate submit residue; do not invent a cleanup). Leftover suggested candidates on runs 2–3.

**Platform:** office authentication is **operational for UAT** (FG-018). Shared API Foundation V1 is **operational for UAT** (FG-019). RBAC and org-switcher are **not implemented**. This is not production-security certification.

No product-code defects were opened for repair in this turnover. Do not fix them here.

## 18. DEFERRED ITEMS

[FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) Phase D mapping is **CLOSED / OPERATIONAL FOR UAT**; V1-02 / [FG-027](feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) costing is **CLOSED / OPERATIONAL FOR UAT**; Crew Template catalog; payroll burden; `LabourActualObservation`; Project Closeout / archive-and-purge; FG-021 SESSION-EXPIRY RECOVERY (**DEFERRED / NOT YET EXERCISED**; not PASS); Observation Delete (**QUEUED / NOT AUTHORIZED**); subcontract RFQ/package (**maturation during UAT / not implemented**; [FG-031](feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) **CLOSED / OPERATIONAL FOR UAT**; two stored dimensions; no HYBRID enum); server-side per-login session revocation / idle timeout (**FUTURE AUTHENTICATION HARDENING / NOT FG-021**); QuickBooks live API (**POST-V1**; [FG-032](feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) Option A **CLOSED / OPERATIONAL FOR UAT**; V1-05 **COMPLETE**); contractor-facing UX language remaining surfaces ([FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 1, SLICE 2, SLICE 3, SLICE 4, SLICE 5, AND SLICE 6 IMPLEMENTED / NOT CLOSED**; unauthorized candidate surfaces: Historical Evidence nav and historical specialist screens; standalone Permit screens; Hub PRICE leftover `TRUE_GROSS_MARGIN`; final product-wide sweep; **REVIEW / DECISION REQUIRED**: Cost Items nav; “Contract value”; Dashboard `page_title`; Office sign in / Brayman Construction Platform titles; `GENERIC_LOGIN_FAILURE`; Brand Profile saved. flash; Settings (coming soon) frozen by FG-017); construction contract/warranty ([FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **SLICE A CLOSED / OPERATIONAL FOR UAT / SLICE B CLOSED / OPERATIONAL FOR UAT / SLICE C CLOSED / OPERATIONAL FOR UAT / OVERALL OPEN / PARTIAL**); four-output output 4; TBD/PLACEHOLDER durable state; OCR/CAD; multi-trade extraction; real external AI provider; MONITOR remainder (forecast-final GM / cost-to-complete / Field Web MONITOR / LEARN remain out of V1); LEARN **implementation**; native/token auth; [FG-029](feature-gates/FG-029-bmr-supplier-workflow-v1.md) BMR / supplier workflow (**CLOSED / OPERATIONAL FOR UAT**); live BMR API / bulk supplier catalogue onboarding; Darcy channel economics; industry benchmarking; RBAC / org-switcher / invitations / SSO; national Permit Rules expansion; Change Order document family; Native Signing [FG-033](feature-gates/FG-033-native-signing-document-approval-signature-and-executed-artifact.md) **OPEN / PARTIAL** (SIGN-A **IMPLEMENTED**; SIGN-B/C/D/E **NOT STARTED**; production blocked pending counsel).

## 19. EXPLICITLY PROHIBITED NEXT ACTIONS

Do **not** send live Postmark from this note. Do **not** create a Postmark account from this note. Do **not** reopen FG-032. Do **not** implement live QuickBooks API. Do **not** implement [FG-030](feature-gates/FG-030-supplier-identity-authentication-and-access-isolation.md). Do **not** implement PERF-C / Company Attention. Do **not** implement Home Office. Do **not** begin CLOSE / LEARN / QB-T. Do **not** mutate Project **45**, Project **46**, Project **47**, Project **48**, Project **49**, Project **50**, or EST-2026-0019. Do **not** implement visual Schedule / MONITOR forecast / Closeout / Contractor Language + UX E2E Audit. Do **not** implement desktop Print / print CSS. Do **not** implement Interactive Help, Voice, or the professional User Manual. Do **not** invent FG-036. Do **not** begin FG-024 Slice D. Do **not** populate Ontario production legal content. Do **not** implement remaining FG-025 surfaces. Do **not** implement Observation Delete. Do **not** accept ADR-008. Do **not** publish the marketing website from this repository.

## 20. NEXT AUTHORIZED ACTION

**Next governed action:** **STOP.** Official V1 readiness **65% / 4 of 11**. Secondary Functional V1 Build **79% / 22 of 28**. FG-037 **NOT YET IMPLEMENTED** (stash unapplied / not product). PERF-C **DEFINED / NOT IMPLEMENTATION-AUTHORIZED**. Freeze [architecture/fg-035-perf-c-product-definition.md](architecture/fg-035-perf-c-product-definition.md). PERF-A / PERF-B remain **SEALED**. [FG-035](feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) **OPEN / PARTIAL**. Product SHA **`dcde4adfe4a475932b7f144b0220b2b60e4bd75c`**. Pin **`1b80d244e3efb0c65d3a02dd247d923dfd95166c`**. No schema. Do **not** pop the FG-037 stash from this record. Do **not** implement Company Attention. Do **not** implement Home Office. Return to ChatGPT Architect.

**Roadmap direction (not authorization):** Item 12 Field Web is **CLOSED**. Item 13 **CLOSED / OPERATIONAL FOR UAT**. [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) is **SLICE 1, SLICE 2, SLICE 3, SLICE 4, SLICE 5, AND SLICE 6 IMPLEMENTED / NOT CLOSED** (remaining surfaces not authorized). [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) is **CLOSED / OPERATIONAL FOR UAT**. Item 15 / [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) is **FUTURE / RECORDED / SLICE A CLOSED / OPERATIONAL FOR UAT / SLICE B CLOSED / OPERATIONAL FOR UAT / SLICE C CLOSED / OPERATIONAL FOR UAT / TECH-A IMPLEMENTED / TECH-B IMPLEMENTED / TECH-C IMPLEMENTED / TECH-D IMPLEMENTED / OVERALL OPEN / PARTIAL**. Project Closeout remains **FUTURE**. Native Signing is a **parallel** track. **ROADMAP SEQUENCE ≠ IMPLEMENTATION AUTHORIZATION.**

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
./venv/bin/python -m pytest -q tests/test_contract_generation_policy_fg024.py
./venv/bin/python -m pytest -q tests/test_contract_generation_fg024.py
./venv/bin/python -m pytest -q tests/test_legal_content_activation_fg024.py
./venv/bin/python -m pytest -q tests/test_legal_content_update_fg024.py
./venv/bin/python -m pytest -q tests/test_legal_content_library_fg024.py
./venv/bin/python -m pytest -q tests/test_monitor_v1_fg023.py
./venv/bin/python -m pytest -q tests/test_monitor_v1_fg023.py tests/test_project_hub.py tests/test_auth_fg018.py tests/test_build_field_observation_fg020.py tests/test_build_media_compatibility_fg020.py tests/test_field_web_fg021.py
./venv/bin/python -m pytest -q tests/test_build_field_observation_fg020.py tests/test_build_media_compatibility_fg020.py
./venv/bin/python -m pytest -q tests/test_auth_fg018.py tests/test_shared_api_fg019.py
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

Expected: branch `main`; HEAD = `origin/main` = this FG-034 MAIL-A / AUTH-A product commit (parent SIGN-E **`3062c67ce3706b4341394d05c3eddb4df9b54c22`**); working tree clean; Alembic **live current `f2a3b4c5d6e7 (head)`**; **repository head `f2a3b4c5d6e7`**; dedicated MAIL-A / AUTH-A **28**; focused MAIL-A/AUTH-A + FG-018 + SIGN-A–E **142**; dedicated SIGN-E **19**; dedicated SIGN-D **11**; dedicated SIGN-C **18**; dedicated SIGN-A **11**; dedicated SIGN-B **18**; full suite **1009 passed**. PRODUCTION packages **0**. PRODUCTION packages **0**. Labeled SYNTHETIC_UAT package `FG024D-UAT-ON-001` ACTIVE retained as technical evidence. Labeled Slice B UAT source `FG024B-UAT-SRC-001` retained. Labeled Slice C contracts `CTR-2026-0001` / `CTR-2026-0002` retained. TECH-D contracts `CTR-2026-0003` / `CTR-2026-0004` retained (GENERATED; not executed). SIGN-A `SIGN-2026-0001` / `SIGN-2026-0002` / `CTR-2026-0005` retained (APPROVED_FOR_SIGNATURE only). SIGN-B `SIGN-2026-0003` retained (SIGNED; not EXECUTED). SIGN-C `SIGN-2026-0004` EXECUTED (countersign) and `SIGN-2026-0005` EXECUTED (no-countersign). SIGN-D live residue `SIGN-2026-0010` EXECUTED / `0011` VOIDED / `0012` VOIDED (synthetic; **not** real iPhone UAT PASS). Private signing artifacts under gitignored `instance/signing_artifacts/`. EST-2026-0019 occupancy unchanged. Non-development `flask` CLI requires local-only `SECRET_KEY` (gitignored `.env`).

## 22. FRESH CHAT STARTUP PROMPT

Canonical location for the next conversation. Paste into a **new** ChatGPT or Cursor chat. Do **not** continue from an old prompt without preflight.

```text
BRAYMAN — RESUME FROM REVIEW TURNOVER
CONTINUITY / REPOSITORY-FIRST INITIALIZATION

You are starting a FRESH conversation on the Brayman-Estimator (CalibraytAI / The Estimator) platform following a successful Review Turnover (2026-09-09).
The prior conversation has been discarded. You have ZERO reliable conversation memory.
Chat history is supplemental only. The repository is the ONE SOURCE OF TRUTH.
ChatGPT / Cursor memory is never corporate memory.

Conversation titles in this Cursor/IDE workspace must start with: BRAYMAN — <Topic>.

ACTIVE CHAT TITLE (ChatGPT originating development chat):
BRAYMAN — CALIBRAYTAI DEVELOPMENT 15 SEP 2026
(Record the exact title of the NEW ChatGPT development chat once Joel names it. Until then, keep using this title.)

CONTINUITY DISPLAY RULE:
Every CalibraytAI development response begins with the exact active ChatGPT
development chat title in bold and ends with:

END — <exact active chat title>

When a Cursor prompt is present, the END line follows the complete prompt.
Every CalibraytAI development response ends with the next complete ready-to-paste
Cursor prompt unless Joel explicitly says no prompt is required.

DO NOT reopen FG-021.
DO NOT convert SESSION-EXPIRY RECOVERY to PASS / N/A / WAIVED.
DO NOT begin V1-02.
DO NOT run flask db upgrade against the live UAT DB.
DO NOT implement Observation Delete.
DO NOT implement session revocation / idle timeout.
DO NOT invent iPhone UAT results.
DO NOT implement Native Signing for real customer / commercial use.
DO NOT weaken the Legal Content Gate.
DO NOT implement Project Closeout.
DO NOT add tokens or API keys.
DO NOT start RBAC or an org-switcher.
DO NOT start Change Order document work.
DO NOT reopen FG-026.
DO NOT start LEARN.
DO NOT start supplier integration.
DO NOT enable external AI or runtime web lookup.
DO NOT create another migration.
DO NOT amend the frozen FG-023 commercial contract.
DO NOT start another FG-025 slice.
DO NOT start FG-024 product (Slice A preflight is COMPLETE; ADR-050 is Accepted; product remains unauthorized).

ROADMAP SEQUENCE ≠ IMPLEMENTATION AUTHORIZATION.
Last product-changing commit:
aa4c71800586e0b8e2a63931bcdc8bc44d87a489
feat: implement FG-026 takeoff-to-estimate mapping
This live-migrate / UAT close is docs-only. Its commit is NOT the FG-026 product SHA.
Slice 5 product SHA remains 5b497905086554214e85f69afd8101d88f89161c.
Ancestor FG-023 Slice B product SHA remains 7dd4d82c927ec2c38a0562e7e1cdedbccabb6662.
Item 10 is COMPLETE (FG-018 + FG-019 both CLOSED / OPERATIONAL FOR UAT).
Item 11 BUILD Field Observation foundation is COMPLETE.
Image-only Compatible Renditions (HEIC/HEIF → JPEG) are IMPLEMENTED.
ADR-042 is Accepted. FG-020 is CLOSED / OPERATIONAL FOR UAT.
Live Alembic current = f4a5b6c7d8e9 (EQUALS repository head).
Repository Alembic head = f4a5b6c7d8e9 (FG-026; applied live 2026-09-08).
Item 12 Field Web is CLOSED.
ADR-043 is Accepted. FG-021 is CLOSED.
SESSION-EXPIRY RECOVERY is DEFERRED / NOT YET EXERCISED (NOT PASS / NOT FAIL / NOT N/A / NOT WAIVED).
OLDER SUPPORTED IPHONE / SAFARI is WAIVED AS NOT PRACTICAL.
Event 37 / Original 37 = authenticated UAT residue, NOT session-expiry recovery. Do not delete.
Event 38 = interrupted CSRF residue. Do not delete.
Event 39 / Original 39 = CSRF PASS.
Live 39 Events / 39 Originals.
Observation Delete is QUEUED / NOT AUTHORIZED / NOT IMPLEMENTED / NON-BLOCKING.
FG-022 is CLOSED / APPROVED REUSABLE MASTER FAMILY V1. Family 05 remains COMMERCIAL_DRAFT / NOT LEGALLY APPROVED.
Native Signing DEVELOPMENT MAY PROCEED UNDER SEPARATE GOVERNANCE.
Native Signing PRODUCTION ACTIVATION is BLOCKED PENDING COUNSEL PROCESS APPROVAL.
Project Closeout is FUTURE.
FG-023 is CLOSED / OPERATIONAL FOR UAT.
Slice A is IMPLEMENTED / LIVE-MIGRATED.
MONITOR V1 is IMPLEMENTED / LIVE-MIGRATED / OFFICE-UAT-VERIFIED / CLOSED.
Hub #hub-monitor is LIVE / OFFICE-UAT-VERIFIED.
Office write routes/forms are LIVE / OFFICE-UAT-VERIFIED.
Office UAT is COMPLETE / PASS (project id 13 FG023-UAT-MONITOR, port 5014).
Item 13 is CLOSED / OPERATIONAL FOR UAT.
FG-025 Slice 5 dedicated 19. Field-focused 83. Prompt governed 190. Full suite 612.
Historical Slice 4 dedicated 16 / Slice-4 focused 114 / governed 226 / full 609.
Historical Slice 3 dedicated 13 / PRICE-focused 167 / governed 303 / full 606.
Historical Slice 2 dedicated 10 / focused 159 / full 603.
Dedicated FG-023 35. Focused 149. Historical Slice A close focused 126. Pre-Slice-B focused 137. Full suite at close 593.
Prior FG-021 close bundle (historical): dedicated 20 / focused 148 / full 558.

FROZEN FG-023 CONTRACT (do not amend):
Locked source = Accepted Proposal estimate_version_id.
Zero Accepted → MISSING_CUSTOMER_COMMITMENT.
More than one → AMBIGUOUS_COMMITMENT (do not pick latest).
Snapshot DC/selling when present; else Σ extended_cost and Proposal subtotal + overhead + profit.
Authorized COs: Approved or Invoiced; delta = subtotal + markup; exclude tax.
Current Authorized Estimated Cost = Original Estimated Direct Cost.
MISSING_ACTUALS ≠ zero. Explicit 0.00 ACTIVE row is present.
incurred_on accepts any parseable calendar date (no today cutoff).
Field Events evidence only. No NET PROFIT. No forecast-final GM.
Money: existing as_money ROUND_HALF_UP 0.01.

Next governed action = STOP. Do NOT begin V1-02.
FG-026 is CLOSED / OPERATIONAL FOR UAT.
Live migrate f4a5b6c7d8e9 PASS. Office UAT PASS on port 5015.
Do NOT flask db upgrade live.
Do NOT begin V1-02 / Approve All Costing / V1-03.
Slice C MIGRATION COMPLETE / OFFICE UAT COMPLETE / PASS.
Slice A + Slice B IMPLEMENTED / LIVE-MIGRATED.
FG-025 is IMPLEMENTATION PREFLIGHT COMPLETE / SLICE 1 IMPLEMENTED / SLICE 2 IMPLEMENTED / SLICE 3 IMPLEMENTED / SLICE 4 IMPLEMENTED / SLICE 5 IMPLEMENTED / NOT CLOSED.
Remaining FG-025 surfaces are NOT AUTHORIZED.
Do not begin V1-02. Do not begin another FG-025 slice. Do not begin FG-024. Do not begin LEARN.
Do NOT re-run flask db upgrade f4a5b6c7d8e9.

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
- docs/feature-gates/FG-023-monitor-v1-estimated-versus-actual.md
- docs/feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md
- docs/architecture/fg-023-monitor-v1-implementation-preflight.md
- docs/architecture/monitor-v1-implementation-reconnaissance.md
- docs/adr/ADR-021-monitor-commercial-baseline.md
- docs/modules/monitor.md
- docs/architecture/field-web-today-and-capture.md
- docs/adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md
- docs/feature-gates/FG-021-field-web-v1-today-and-capture.md
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
- last product-changing commit is ancestor aa4c71800586e0b8e2a63931bcdc8bc44d87a489
- Alembic current = f4a5b6c7d8e9
- Alembic heads = f4a5b6c7d8e9 (one graph head; live current EQUALS repository head)
- live project_direct_cost_actuals table EXISTS
- live Field Events / Originals = 39 / 39
- FG023-UAT-MONITOR project id 13 exists; no UAT actuals on projects 1, 2, 9, 11, 12

3. IDENTIFY CURRENT STOP STATE
Independently reconstruct from the repository:
- FG-008 through FG-021 CLOSED (FG-021 subject to SESSION-EXPIRY deferred exception)
- FG-022 CLOSED / APPROVED REUSABLE MASTER FAMILY V1
- FG-023 CLOSED / OPERATIONAL FOR UAT
- Slice A + Slice B IMPLEMENTED / LIVE-MIGRATED
- Slice C MIGRATION COMPLETE / OFFICE UAT COMPLETE / PASS
- Hub #hub-monitor LIVE / OFFICE-UAT-VERIFIED
- MONITOR V1 IMPLEMENTED / LIVE-MIGRATED / OFFICE-UAT-VERIFIED / CLOSED
- Live current = heads f4a5b6c7d8e9
- FG-026 CLOSED / OPERATIONAL FOR UAT
- FG-025 IMPLEMENTATION PREFLIGHT COMPLETE / SLICE 1 IMPLEMENTED / SLICE 2 IMPLEMENTED / SLICE 3 IMPLEMENTED / SLICE 4 IMPLEMENTED / SLICE 5 IMPLEMENTED / NOT CLOSED
- Remaining FG-025 surfaces NOT AUTHORIZED
- Dedicated FG-025 19; Field-focused 83; prompt governed 190; full suite 612
- Historical Slice 4 dedicated FG-025 16; Slice-4 focused 114; governed 226; full suite 609
- Historical Slice 3 dedicated FG-025 13; PRICE-focused 167; governed 303; full suite 606
- Dedicated FG-023 35; focused 149; historical Slice A focused 126; pre-Slice-B focused 137; full suite 593 (close-time rerun 2026-09-07)
- Pratt UAT project id 9 / FG016-UAT-PRATT / analysis v3 / advisory only
- FG-018 office UAT PASSED on port 5011
- FG-019 API UAT PASSED on port 5012
- FG-020 office UAT PASSED on port 5013
- ADR-021 Accepted (Slice A projection + Slice B Hub implemented / live-migrated / office-UAT-verified)
- ADR-040 / ADR-041 / ADR-042 / ADR-043 Accepted
- Roadmap item 10 COMPLETE
- Item 11 BUILD COMPLETE
- Item 12 Field Web CLOSED
- Item 13 CLOSED / OPERATIONAL FOR UAT
- SESSION-EXPIRY RECOVERY DEFERRED / NOT YET EXERCISED
- OLDER SUPPORTED IPHONE / SAFARI WAIVED AS NOT PRACTICAL
- Observation Delete QUEUED / NOT AUTHORIZED / NOT IMPLEMENTED / NON-BLOCKING
- Native Signing DEVELOPMENT MAY PROCEED UNDER SEPARATE GOVERNANCE; PRODUCTION ACTIVATION BLOCKED PENDING COUNSEL
- ADR-008 and ADR-010 remain Proposed
- CalibraytAI V1 readiness 60%; 4 / 11 COMPLETE (V1-01, V1-02, V1-03, V1-05); BMR DEMO READY NO; BRAYMAN REAL-LIFE UAT READY NO
- Real external AI NOT AUTHORIZED
- Runtime permit web lookup NOT AUTHORIZED

4. RETURN A CONCISE CURRENT STATE REVIEW
FG-023 is CLOSED / OPERATIONAL FOR UAT.
MONITOR V1 is IMPLEMENTED / LIVE-MIGRATED / OFFICE-UAT-VERIFIED / CLOSED.
FG-025 is SLICE 1, SLICE 2, SLICE 3, SLICE 4, AND SLICE 5 IMPLEMENTED / NOT CLOSED.
Remaining FG-025 surfaces are NOT AUTHORIZED.
FG-026 is CLOSED / OPERATIONAL FOR UAT.
FG-027 is CLOSED / OPERATIONAL FOR UAT.
FG-028 is SLICES 1–3 COMPLETE / CLOSED / OPERATIONAL FOR UAT.
FG-029 is CLOSED / OPERATIONAL FOR UAT. LIVE-MIGRATED / BOUNDED BMR DEMO OFFICE UAT PASS.
FG-030 is RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED.
ADR-047 is Accepted (architecture only). ADR-046 is Accepted. ADR-008 remains Proposed.
FG-031 is CLOSED / OPERATIONAL FOR UAT. Slice A and Slice B are OPERATIONAL FOR UAT.
ADR-048 is Accepted.
FG-032 is CLOSED / OPERATIONAL FOR UAT.
ADR-049 is Accepted by Joel Brayman, 10 Sep 2026. Product SHA 70e571140e12377aa5bd009b598530576401113b. Product parent 010f6d641a756ceb2ab67475a284d3b8426c7b20. Joel selected V1-05 Option A. Live QuickBooks API is POST-V1.
Subcontract RFQ/package is MATURATION DURING UAT / NOT IMPLEMENTED.
CalibraytAI V1 readiness is 60%. 4 / 11 COMPLETE (V1-01, V1-02, V1-03, V1-05). V1-03 COMPLETE. Current scored package V1-04 PARTIAL. V1-05 COMPLETE. BMR DEMO READY NO. BRAYMAN REAL-LIFE UAT READY NO.
Website Version 15 CalibraytAI identity is published / live QA PASS (external). HostPapa migration is QUEUED POST-BETA.
The next governed action is STOP and return to ChatGPT Architect. Do NOT implement live QuickBooks API. Do NOT implement FG-030. Do NOT begin V1-04 product work. Do NOT implement subcontract RFQ/package.
STOP. Do NOT implement supplier login. Do NOT begin V1-04. Do NOT implement subcontract RFQ/package. Do NOT start another FG-025 slice. Do NOT start FG-024 product. ADR-050 is Accepted / architecture only. Do NOT start LEARN.
Do NOT reopen FG-021.
Do NOT convert SESSION-EXPIRY RECOVERY to PASS / N/A / WAIVED.
Do NOT invent iPhone UAT results.
Do NOT implement Project Closeout.
Do NOT enable Native Signing for real customer use.

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

**LIVE COMMERCIAL (not UAT residue) — EST-2026-0019 / Draft / NOT ISSUED**

- Client **22** Marc Bouliion / Solid Steel Management (site address TBD — do not invent)
- Project **27** 40x80 Thickened-Edge Concrete Slab / Estimating
- Estimate **28** `EST-2026-0019` Draft · EstimateVersion **34** Draft priced · snapshot **14** TRUE_GROSS_MARGIN
- Proposal **14** `PROP-2026-0006` Draft · `show_detailed_pricing=False` · `show_section_totals=False`
- Totals: direct **$42,392.00** · sell **$49,872.94** · HST **$6,483.48** · total **$56,356.42**
- Joel-review DOCX (FG-022 copies, masters not written): preserved review copies at `~/Documents/CalibAi/Review-EST-2026-0019/` and the gitignored instance review directory `instance/review-EST-2026-0019/`. Desktop copies named `EST-2026-0019-Internal-Detailed-Cost-Breakdown.docx` and `EST-2026-0019-Construction-Estimate.docx` are **not** the current preserved location. Do **not** move, copy, regenerate, issue, or duplicate EST-2026-0019.
- Office: `/estimates/28/versions/34/internal-breakdown`
- Locked basis: 3,200 sf; 240 LF; 6″; body 45.31 m³ NET; TES extra 14.00 m³ **ESTIMATING ASSUMPTION — NOT ENGINEERING**; order 60 m³; 32 MPa with fibre **$275/m³** Brayman Construction cost (Ben, 12 Sep 2026; replaces $235); fibre included; exclude excavation/granular/stone/stripping/subgrade/grading/compaction/disposal
- Do **not** duplicate these records. Do **not** copy Allen/Speakeasy customer facts into Marc customer docs.

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

A–J: [FG-023](feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) **CLOSED / OPERATIONAL FOR UAT**; Slice A + Slice B **IMPLEMENTED / LIVE-MIGRATED**; Slice C **MIGRATION COMPLETE / OFFICE UAT COMPLETE / PASS**; MONITOR V1 **IMPLEMENTED / LIVE-MIGRATED / OFFICE-UAT-VERIFIED / CLOSED**; preflight [architecture/fg-023-monitor-v1-implementation-preflight.md](architecture/fg-023-monitor-v1-implementation-preflight.md) **COMPLETE**; MONITOR V1 recon **COMPLETE**; BUILD actuals live; migration `e3f4a5b6c7d8` **applied live**; live current today **`d3e4f5a6b7c8 (head)`**; repository Alembic head **`d3e4f5a6b7c8`**; [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **CLOSED / OPERATIONAL FOR UAT**; dedicated FG-026 **20**; full **632** remain historical close-time FG-026 evidence; historical full **612** is the pre-FG-026 baseline; [FG-021](feature-gates/FG-021-field-web-v1-today-and-capture.md) **CLOSED**; IMPLEMENTED / LIVE-MIGRATED / REAL-IPHONE UAT COMPLETE SUBJECT TO THE EXPLICIT SESSION-EXPIRY DEFERRED EXCEPTION; **SESSION-EXPIRY RECOVERY: DEFERRED / NOT YET EXERCISED**; Observation Delete **QUEUED / NOT AUTHORIZED / NOT IMPLEMENTED / NON-BLOCKING**; Slice 5 product SHA **`5b497905086554214e85f69afd8101d88f89161c`**; dedicated FG-025 **19**; Field-focused **83**; prompt governed **190**; dedicated FG-023 **35**; focused **149**; historical Slice A focused **126**; pre-Slice-B focused **137**; full **593** (close-time rerun 2026-09-07); dedicated FG-021 **20**; FG-020 **CLOSED / OPERATIONAL FOR UAT**; [FG-022](feature-gates/FG-022-reusable-approved-document-template-family-v1.md) **CLOSED / APPROVED REUSABLE MASTER FAMILY V1**; Family 05 **COMMERCIAL_DRAFT / NOT LEGALLY APPROVED**; Legal Content Gate **empty**; [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / SLICE A CLOSED / OPERATIONAL FOR UAT / SLICE B CLOSED / OPERATIONAL FOR UAT / SLICE C CLOSED / OPERATIONAL FOR UAT / OVERALL OPEN / PARTIAL**; Slice D **NOT AUTHORIZED**; [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **FUTURE / RECORDED / IMPLEMENTATION PREFLIGHT COMPLETE / SLICE 1–5 IMPLEMENTED / NOT CLOSED**; remaining surfaces **NOT AUTHORIZED**; Native Signing **DEVELOPMENT MAY PROCEED UNDER SEPARATE GOVERNANCE**; **PRODUCTION ACTIVATION BLOCKED PENDING COUNSEL**; Project Closeout **FUTURE**. Do **not** begin V1-04 product work. Do **not** reopen FG-023. Do **not** begin FG-024 Slice D. Do **not** start another FG-025 slice. Pre-migration SQLite copies remain gitignored under `instance/` and must **not** be committed.
