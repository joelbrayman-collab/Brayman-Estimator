# Feature Gate FG-035: Project Work Structure + Time + Schedule + Performance + LEARN

| Attribute | Value |
|----------|--------|
| Feature Gate ID | `FG-035` |
| Feature Name | Project Work Structure, Time, Schedule, Performance, and LEARN V1 |
| Target Milestone | Operational / learning loop (Time, Schedule, MONITOR labour-hours remainder, Closeout LEARN quality, calibration). Complements V1-08 / V1-11. **Does not rescore V1.** |
| Module | **Projects** owns work-structure catalog and Project Element / Activity instances. Estimating owns `LabourTask` / snapshots (referenced). BUILD owns Time Entry (`labour_time_entries`). Projects owns Schedule overlay (`work_schedule_items` / `work_schedule_history`) for **SCH-A** and SCH-B assignments (`work_schedule_assignments`). Organization owns optional Crew (`organization_crews` / `organization_crew_members`). SCH architecture [fg-035-sch-dynamic-scheduling-preflight.md](../architecture/fg-035-sch-dynamic-scheduling-preflight.md) **RECORDED**. Design freeze [fg-035-sch-implementation-preflight.md](../architecture/fg-035-sch-implementation-preflight.md). MONITOR remains a consumer. LEARN remains a consumer. Project Controls owns `ChangeOrder` (referenced by SCOPE). |
| Date | 2026-09-15 |
| Status | **OPEN / PARTIAL.** TAX/WBS **IMPLEMENTED**. SCOPE **IMPLEMENTED**. TIME **IMPLEMENTED**. SCH-A **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. SCH-B **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. SCH-C **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. SCH-D **IMPLEMENTED / TESTED / SERVER-SIDE LIVE UAT PASS / PHYSICAL IPHONE UAT PASS / COMMITTED / SHA-PINNED / PUSHED.** SCH overall **OPEN / PARTIAL**. PERF-A **IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS / COMMITTED / SHA-PINNED / PUSHED**. PERF-B **IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS / COMMITTED / SHA-PINNED / PUSHED**. PERF-C **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE UAT PASS / SEALED**. CORE CLOSE Slice A **IMPLEMENTED IN WORKING TREE / TESTED / MIGRATION FILE CREATED / NOT LIVE-MIGRATED / NOT COMMITTED**. Close/Reopen **NOT IMPLEMENTED**. Punch List **NOT IMPLEMENTED**. LEARN Closeout / LEARN / QB-T **NOT AUTHORIZED**. |
| Architecture | [ADR-053](../adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**. SCH architecture [fg-035-sch-dynamic-scheduling-preflight.md](../architecture/fg-035-sch-dynamic-scheduling-preflight.md) **RECORDED**. SCH implementation freeze [fg-035-sch-implementation-preflight.md](../architecture/fg-035-sch-implementation-preflight.md) remains the design freeze. SCH-A product is **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. Live migration is proven/reconciled from durable evidence; the 15 Sep 2026 reconciliation prompt did **not** apply it. Product direction [project-element-authority-future-record.md](../architecture/project-element-authority-future-record.md) **FUTURE / RECORDED**. [FG-023](FG-023-monitor-v1-estimated-versus-actual.md) **CLOSED** (not reopened). [FG-032](FG-032-quickbooks-ready-output-entry-v1.md) **CLOSED** (not rewritten). [FG-033](FG-033-native-signing-document-approval-signature-and-executed-artifact.md) **CLOSED**. [FG-034](FG-034-account-recovery-and-transactional-email.md) **CLOSED**. |
| Related ADRs | [ADR-053](../adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**. [ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md). [ADR-021](../adr/ADR-021-monitor-commercial-baseline.md). [ADR-024](../adr/ADR-024-learn-recommendation-boundary.md). [ADR-028](../adr/ADR-028-organization-foundation-and-project-commercial-context.md). [ADR-029](../adr/ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md). |
| Prerequisites | FG-008 labour snapshots. FG-011 Project Hub. FG-018 office auth. ADR-053 Accepted. |

**Subsequent status (2026-09-18 CORE CLOSE Slice A):** CORE CLOSE Slice A **IMPLEMENTED IN WORKING TREE / TESTED / MIGRATION FILE CREATED / NOT LIVE-MIGRATED / NOT COMMITTED**. Revision **`b2c3d4e5f6a7`**. Close/Reopen **NOT IMPLEMENTED**. Punch List **NOT IMPLEMENTED**. Completion Sign-Off **NOT IMPLEMENTED**. Subsequent owner freeze: physical work completion ≠ administrative Change Order completion; incomplete physical work is Punch List; NEW CO after Close requires Reopen. This gate remains **OPEN / PARTIAL**. LEARN / QB-T remain **NOT AUTHORIZED**. Official V1 **65% / 4 of 11** (not rescored).

**Subsequent status (2026-09-18 CORE CLOSE / Project lifecycle owner freeze):** [architecture/core-close-project-lifecycle-product-direction.md](../architecture/core-close-project-lifecycle-product-direction.md) **RECORDED MANDATORY PRODUCT DIRECTION / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. CORE CLOSE is **distinct** from historical FG-035 CLOSE / LEARN Closeout. V1 operating lifecycle is **ACTIVE / CLOSED** (no ARCHIVED third state; do **not** reuse `Project.status`). Punch List → Project Completion Sign-Off → Close Project is recorded. No schema. No product. No live Project Close. This gate remains **OPEN / PARTIAL**. LEARN / QB-T remain **NOT AUTHORIZED**. Historical CLOSE heading below is **not rewritten**. Official V1 **65% / 4 of 11** (not rescored). Secondary Functional V1 Build **79% / 22 of 28** (not rescored).

**Subsequent status (2026-09-17 PERF-C LIVE UAT / SEAL):** PERF-C **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE UAT PASS / SEALED**. Product SHA **`22fd30cd774fcf155ae69d7dcf99a44123d91409`**. Architect disposition: live UAT **PASS**; existing-occupancy coverage **SUFFICIENT**; additional synthetic vessel **NOT REQUIRED**; product correction **NONE REQUIRED**. Evidence [testing/fg035-perf-c-live-uat-record.md](../testing/fg035-perf-c-live-uat-record.md). Project-scope observation recorded as **PROJECT LIFECYCLE / ACTIVE-ARCHIVED SCOPE / FUTURE GOVERNED PRODUCT DECISION**. **Subsequent (2026-09-18):** that future decision is now frozen as CORE CLOSE **ACTIVE / CLOSED** ([architecture/core-close-project-lifecycle-product-direction.md](../architecture/core-close-project-lifecycle-product-direction.md)); this historical seal sentence is **not rewritten**. No PERF-C filtering. No live occupancy mutation. This gate remains **OPEN / PARTIAL** (CORE CLOSE **RECORDED / NOT IMPLEMENTATION-AUTHORIZED**; LEARN / QB-T **NOT AUTHORIZED**; SCH overall **OPEN / PARTIAL**). PERF-A / PERF-B remain **SEALED**. FG-037 remains **CLOSED**. Official V1 **65% / 4 of 11**. Secondary Functional V1 Build **79% / 22 of 28** (not rescored; PERF-C now eligible for later Functional Build reconciliation).

**Subsequent status (2026-09-17 PERF-C Slice A COMMIT / PUSH / SHA-PIN):** PERF-C **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NOT LIVE-UATed**. Product SHA **`22fd30cd774fcf155ae69d7dcf99a44123d91409`**. Office `/company-attention`. Requires `COMPANY_MANAGEMENT`. No schema. No live UAT data. Dedicated **13 passed**. Focused **115 passed**. Full suite **1226 passed**. This gate remains **OPEN / PARTIAL**. PERF-A / PERF-B remain **SEALED**. FG-037 remains **CLOSED**. Official V1 **65% / 4 of 11**. Secondary Functional V1 Build **79% / 22 of 28**.

**Subsequent status (2026-09-17 PERF-C Slice A implementation):** PERF-C **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NOT LIVE-UATed**. Office `/company-attention`. Requires `COMPANY_MANAGEMENT`. No schema. No live UAT data. Dedicated **13 passed**. Focused **115 passed**. Full suite **1226 passed**, 4366 warnings, **610.51s**, exit **0**. This gate remains **OPEN / PARTIAL**. PERF-A / PERF-B remain **SEALED**. FG-037 remains **CLOSED**. Official V1 **65% / 4 of 11**. Secondary Functional V1 Build **79% / 22 of 28**.

**Subsequent status (2026-09-17 People & Access freeze):** [architecture/people-and-access-product-direction.md](../architecture/people-and-access-product-direction.md) **RECORDED MANDATORY PRODUCT DIRECTION / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. This gate remains **OPEN / PARTIAL**. PERF-C remains **DEFINED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. Do **not** implement Company Attention from the People & Access freeze.

**Subsequent status (2026-09-17 FG-037 close):** [FG-037](FG-037-company-management-access-domain-authorization.md) **CLOSED / OPERATIONAL FOR COMPANY_MANAGEMENT AUTHORIZATION**. First live grant: ORG-001 Membership **1** / Joel Brayman / `COMPANY_MANAGEMENT`. This gate remains **OPEN / PARTIAL**. PERF-C remains **DEFINED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. Official V1 remains **65% / 4 of 11**. Secondary Functional V1 Build remains **79% / 22 of 28**. Recovery stash remains present and was **not dropped**. No PERF-C product from the FG-037 close.

**Subsequent status (2026-09-17 official V1 rescore):** Register rescored to **65% / 4 of 11**. V1-06 **0.40**. V1-07 **PARTIAL / 0.40**. Secondary Functional V1 Build **79% / 22 of 28** (labelled secondary; not averaged). This gate remains **OPEN / PARTIAL**. PERF-C **DEFINED / NOT IMPLEMENTATION-AUTHORIZED**. Company/Management seam **DEFINED**. [FG-037](FG-037-company-management-access-domain-authorization.md) was then **OPEN / SLICE A IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE-MIGRATED / NO LIVE GRANT / NOT CLOSED**. Product SHA **`1649b6fab6d362c19088290a6f3cb52f2a0b3d92`**. Recovery stash remains present and was **not dropped**. No PERF-C product from the rescore.

**Subsequent status (2026-09-17 Company/Management access-domain seam):** Separate authorization freeze [architecture/company-management-access-domain-seam.md](../architecture/company-management-access-domain-seam.md) **DEFINED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. Active membership remains Project/Operational. `COMPANY_MANAGEMENT` is explicit default-deny. PERF-C remains **DEFINED / NOT IMPLEMENTATION-AUTHORIZED** and must **not** ship until that seam is separately implemented and proven. ADR-041 Decision 4 **narrowly amended** (job-title RBAC still rejected). No schema. No product. V1 **not rescored**.

**Subsequent status (2026-09-17 PERF-C product definition / owner-decision freeze):** PERF-C **DEFINED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. Contractor question: **Where does my business need attention?** Owner decisions 1–16 **ACCEPTED**. Freeze [architecture/fg-035-perf-c-product-definition.md](../architecture/fg-035-perf-c-product-definition.md). No Field Company Attention. Permission domains later frozen as the Company/Management seam (see subsequent status above). PERF-A / PERF-B remain **SEALED**. No schema. No product. V1 **not rescored**.

**Subsequent status (2026-09-17 PERF-B CLOSE / COMMIT / SHA-PIN / PUSH):** PERF-B **IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS / COMMITTED / SHA-PINNED / PUSHED**. Product SHA **`dcde4adfe4a475932b7f144b0220b2b60e4bd75c`**. Project **50**. No schema. PERF-C **NOT AUTHORIZED**. V1 **not rescored**. Evidence [testing/fg035-perf-b-live-bounded-uat-record.md](../testing/fg035-perf-b-live-bounded-uat-record.md).

**Subsequent status (2026-09-17 PERF-B bounded synthetic live UAT):** PERF-B **IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS**. Project **50**. Dedicated **36 passed**. Focused **206 passed**. Full suite **1190 passed**, 4212 warnings, **746.12s**, exit **0**. No schema. Not committed. Not pushed. PERF-C **NOT AUTHORIZED**. V1 **not rescored**. Evidence [testing/fg035-perf-b-live-bounded-uat-record.md](../testing/fg035-perf-b-live-bounded-uat-record.md).

**Subsequent status (2026-09-17 PERF-B engineering implementation):** PERF-B **IMPLEMENTED / TESTED / NOT LIVE-UAT**. `assemble_project_performance` / `assemble_project_attention` + Hub `#hub-labour` Needs Attention. Dedicated **36 passed**. Focused **206 passed**. Full suite **1190 passed**, 4212 warnings, **619.11s**, exit **0**. No schema. Not committed. Not pushed. No live UAT. PERF-C **NOT AUTHORIZED**. V1 **not rescored**.

**Subsequent status (2026-09-17 PERF-B design freeze sealed):** PERF-B **IMPLEMENTATION PREFLIGHT COMPLETE / DESIGN FROZEN / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. Owner decisions A–G **ACCEPTED**. Freeze [architecture/fg-035-perf-b-implementation-preflight.md](../architecture/fg-035-perf-b-implementation-preflight.md). No schema. No product. V1 **not rescored**.

**Subsequent status (2026-09-17 PERF-B implementation preflight):** PERF-B **PREFLIGHT COMPLETE / OWNER DECISIONS REQUIRED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. Freeze [architecture/fg-035-perf-b-implementation-preflight.md](../architecture/fg-035-perf-b-implementation-preflight.md). No schema. No product. V1 **not rescored**.

**Subsequent status (2026-09-17 PERF-A CLOSE / COMMIT / SHA-PIN / PUSH):** PERF-A **IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS / COMMITTED / SHA-PINNED / PUSHED**. Product SHA **`7a4b7000e2650eadf68b4ea44d48f75c65830c1f`**. Project **49**. No schema. No PERF-B. V1 **not rescored**. Evidence [testing/fg035-perf-a-live-bounded-uat-record.md](../testing/fg035-perf-a-live-bounded-uat-record.md).

**Subsequent status (2026-09-17 PERF-A bounded synthetic live UAT):** PERF-A **IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS**. Project **49**. Dedicated **14 passed**. Focused **170 passed**. Full suite **1154 passed**, 3873 warnings, **633.10s**, exit **0**. No schema. Not committed. Not pushed. No PERF-B. V1 **not rescored**. Evidence [testing/fg035-perf-a-live-bounded-uat-record.md](../testing/fg035-perf-a-live-bounded-uat-record.md).

**Subsequent status (2026-09-17 PERF-A engineering implementation):** PERF-A **IMPLEMENTED / TESTED / NOT LIVE-UAT**. `assemble_project_performance` + Hub `#hub-labour`. Dedicated **14 passed**. Focused **170 passed**. Full suite **1154 passed**, 3873 warnings, **473.49s**, exit **0**. No schema. Not committed. Not pushed. No live UAT. No PERF-B. V1 **not rescored**.

**Subsequent status (2026-09-17 PERF-A design freeze sealed):** PERF-A **IMPLEMENTATION PREFLIGHT COMPLETE / DESIGN FROZEN / NOT IMPLEMENTED**. Freeze [architecture/fg-035-perf-a-implementation-preflight.md](../architecture/fg-035-perf-a-implementation-preflight.md) committed / pushed. No schema. No product. No PERF-B. V1 **not rescored**.

**Subsequent status (2026-09-17 PERF-A implementation preflight):** PERF-A **IMPLEMENTATION PREFLIGHT COMPLETE / DESIGN FROZEN / NOT IMPLEMENTED**. Freeze [architecture/fg-035-perf-a-implementation-preflight.md](../architecture/fg-035-perf-a-implementation-preflight.md). No schema. No product. No PERF-B. V1 **not rescored**.

**Subsequent status (2026-09-17 SCH-D committed / SHA-pinned / pushed):** SCH-D **IMPLEMENTED / TESTED / SERVER-SIDE LIVE UAT PASS / PHYSICAL IPHONE UAT PASS / COMMITTED / SHA-PINNED / PUSHED**. Product SHA **`59d36b8f0b3a86eb41aee03890cb432d0fc58e52`**. Pin **`f1aa486a738a1877d34b16e53fc31d610444ae19`**. No migration. V1 **not rescored**.

**Subsequent status (2026-09-17 SCH-D final physical iPhone UAT + post-physical regression):** Joel G1–G6 **PHYSICAL PASS**. Directions + native iOS return **PHYSICAL PASS**. Dedicated SCH-D **21 passed**. TIME+Field+SCH-D **49 passed**. SCH-A/B/C **36 passed**. Focused **156 passed**. Full suite **1140 passed**, 3749 warnings, **665.58s**, exit **0**. SCH-D **IMPLEMENTED / TESTED / SERVER-SIDE LIVE UAT PASS / PHYSICAL IPHONE UAT PASS / NOT COMMITTED / NOT PUSHED**. SCH overall **OPEN / PARTIAL**. No PERF. No commit. V1 **not rescored**. Evidence [testing/fg035-sch-d-live-physical-iphone-uat-record.md](../testing/fg035-sch-d-live-physical-iphone-uat-record.md).

**Subsequent status (2026-09-17 SCH-D job-site location + Directions UAT correction):** G1 Today **PHYSICAL PASS**. G5 This Month **PHYSICAL PASS**. G6 Time **PHYSICAL PASS**. G2/G3/G4 **PHYSICAL FAIL** (no job-site address on live Project 48). Field now projects `Project.address` / civic `ProjectLocation`. Bounded synthetic Project **48** address set. Dedicated SCH-D **21 passed**. Governed bundle **85 passed**. Do **not** claim G2/G3/G4 physical PASS. Month/Time not redesigned. No PERF. No commit. V1 **not rescored**. Evidence [testing/fg035-sch-d-live-physical-iphone-uat-record.md](../testing/fg035-sch-d-live-physical-iphone-uat-record.md).

**Subsequent status (2026-09-17 SCH-D address + Directions + Month calendar):** F1 Company Today **PHYSICAL PASS**. F2 This Week **PHYSICAL PASS**. F3 This Month **PHYSICAL FAIL** (too busy). F4 Back to Today **PHYSICAL PASS / IMMEDIATE**. Correction uses existing `Project.address`; Directions handoff; Month calendar + selected-day detail. No migration. Dedicated SCH-D **19 passed**. TIME+Field+SCH-D **47 passed**. Do **not** claim Month or Directions physical PASS. Landscape **not** in this pass. No PERF. No commit. V1 **not rescored**. Evidence [testing/fg035-sch-d-live-physical-iphone-uat-record.md](../testing/fg035-sch-d-live-physical-iphone-uat-record.md).

**Subsequent status (2026-09-16/17 SCH-D HTTPS UAT harness recovery):** Unhealthy Python **2556** terminated. Same SCH-D product restarted with `flask run --with-threads`. Python **78027**. Localhost `/login` **200**. Concurrency proven. **No product change.** Post-C3 blanks **not** product-render evidence. Landscape still **FAIL**. Joel **E1/E2** portrait Today/Time only. No PERF. No commit. V1 **not rescored**. Evidence [testing/fg035-sch-d-live-physical-iphone-uat-record.md](../testing/fg035-sch-d-live-physical-iphone-uat-record.md).

**Subsequent status (2026-09-16 SCH-D fresh Safari tab /field/today blank):** New portrait tab, manual URL, **BLANK**. Fresh `/field/today` **did not complete HTTP**. Flask **2556** listening but **blocked** (iPhone `192.168.2.160:61619` ESTABLISHED; localhost `/login` timeout 3s). Damaged-tab-only **INSUFFICIENT**. **No product patch. HTTPS not restarted.** Do **not** retry. No PERF. No commit. V1 **not rescored**. Evidence [testing/fg035-sch-d-live-physical-iphone-uat-record.md](../testing/fg035-sch-d-live-physical-iphone-uat-record.md).

**Subsequent status (2026-09-16 SCH-D current UX #5 Time blank-screen diagnostic):** After C3, Joel taps Time → blank screen stays; Back returns. Repeated. Flask Python **2556** healthy. Only iPhone Time GET **17:48:48 200**. Post-C3 Time taps: **no Flask request**. Authenticated Time HTML **200** / form present. Date `appearance: none` **not** demonstrated as cause (C1 used it). **No product patch.** Do **not** retest until Architect review. No PERF. No commit. V1 **not rescored**. Evidence [testing/fg035-sch-d-live-physical-iphone-uat-record.md](../testing/fg035-sch-d-live-physical-iphone-uat-record.md).

**Subsequent status (2026-09-16 SCH-D C3 landscape crash diagnostic):** C1 Date **PHYSICAL PASS**. C2 Portrait **PHYSICAL PASS**. C3 Today landscape **PHYSICAL FAIL / entire app crashed**. C4/C5 **NOT TESTED**. Flask HTTPS Python **2556** **did not crash**. No 5xx. No orientation JS. iPhone WebKit logs **unavailable**. **No landscape patch.** Do **not** retest until Architect review. No PERF. No migration. No commit. V1 **not rescored**. Evidence [testing/fg035-sch-d-live-physical-iphone-uat-record.md](../testing/fg035-sch-d-live-physical-iphone-uat-record.md).

**Subsequent status (2026-09-16 SCH-D physical UAT UX #5):** Joel B1 Date **FAIL** (blank top-right box). B2 Portrait **PASS**. B3 Landscape **FAIL** on Today and Time. B4 Enter Time **PASS / QUICK**. B5 other nav **QUICK**; Time → Back to Today **2–3s**. Date native chrome removed (`appearance: none`). Capture-only 2-col landscape. Today IDB only when pending flag set. Cache-bust `schd-ux5b`. TIME+Field+SCH-D **43 passed**. Do **not** claim UX #5 physical PASS. No PERF. No migration. No commit. V1 **not rescored**. Evidence [testing/fg035-sch-d-live-physical-iphone-uat-record.md](../testing/fg035-sch-d-live-physical-iphone-uat-record.md).

**Subsequent status (2026-09-16 SCH-D physical UAT UX #4 measure-then-correct):** Joel clarified Field action/navigation slowness (especially Enter Time); do **not** record landscape-only slowness. Flask Enter Time **12–20 ms**. Bottleneck: render-blocking Google Fonts + idle IndexedDB on Time/Week/Month. Date `min-width: 0`. Landscape `@media (min-width: 36rem)`. Dedicated SCH-D **15 passed** in TIME+Field+SCH-D **43 passed**. Do **not** claim UX #4 physical PASS. No PERF. No migration. No commit. V1 **not rescored**. Evidence [testing/fg035-sch-d-live-physical-iphone-uat-record.md](../testing/fg035-sch-d-live-physical-iphone-uat-record.md).

**Subsequent status (2026-09-16 SCH-D physical UAT UX #4):** UX #3 A1 **My Work — Joel PASS**. A2 Date **FAIL** (control exceeds Time card right edge). A3 portrait improved, Date still a defect. A4 landscape **FAIL** (narrow column, unused viewport). Landscape performance **FAIL**. Date: remove WebKit datetime-edit `width: 100%`; date-only `min-width: 0`. Landscape shell: `@media (min-width: 36rem)` lifts `42rem` cap. No Field JS orientation/resize loop found. Dedicated SCH-D **14 passed**. TIME+Field **28 passed**. Do **not** claim UX #4 physical PASS. No PERF. No migration. No commit. V1 **not rescored**. Evidence [testing/fg035-sch-d-live-physical-iphone-uat-record.md](../testing/fg035-sch-d-live-physical-iphone-uat-record.md).

**Subsequent status (2026-09-16 SCH-D physical UAT UX #3):** Joel UX #2 Test A **FAIL / CORRECTION REQUIRED**. PASS: My Work understandable; Extra Work / Field functions accessible; Schedule-assisted Time **PHYSICAL PASS**. FAIL: personal identity cue missing; Time Date still misaligned; useful landscape / horizontal **REGRESSED**. Chrome desktop crash loop was **AiRIA pytest / not CalibraytAI / no SCH-D product consequence**. Correction: **My Work — first name**; sibling Date label/input; restore FG-021 landscape two-column (no `overflow-x: hidden`). Dedicated SCH-D **14 passed**. TIME+Field **28 passed**. SCH-A+B **22 passed**. HTTPS restart onto UX #3 required. Do **not** claim UX #3 physical PASS. No PERF. No migration. No commit. V1 **not rescored**. Evidence [testing/fg035-sch-d-live-physical-iphone-uat-record.md](../testing/fg035-sch-d-live-physical-iphone-uat-record.md).

**Subsequent status (2026-09-16 SCH-D physical UAT UX #2):** Joel recorded **SCHEDULED TIME PHYSICAL PASS**. Remaining findings: weekday orientation; redundant own-name My work copy; Time date right-shift; ad-hoc work must be obvious. Correction: derived weekday + natural date; omit current-user name on worker My work; Time date Field-form alignment; **Working somewhere else?** / **Choose different work** uses existing TIME pickers; unscheduled Cleanup Time does not change Schedule. Dedicated SCH-D **13 passed**. TIME+Field **41 passed**. HTTPS restarted onto UX #2. Overall physical UAT **not closed**. No PERF. No migration. No commit. V1 **not rescored**. Evidence [testing/fg035-sch-d-live-physical-iphone-uat-record.md](../testing/fg035-sch-d-live-physical-iphone-uat-record.md).

**Subsequent status (2026-09-16 SCH-D Time-entry correction):** Physical iPhone Test 1 **FAIL / UNABLE TO INPUT TIME**. Root cause: `time_entry` 302 to Confirm Project when the job was not already confirmed. Correction: Time URL confirms that project and renders Hours / Send time. Capture confirm unchanged. `submit_time()` unchanged. Bounded Today dates / duplicate warnings / project label / Today SVG. Dedicated SCH-D **12 passed**. Focused **147 passed**. Physical retest **not claimed**. Banked Hours **RECORDED / NOT AUTHORIZED** ([architecture/banked-hours-product-direction.md](../architecture/banked-hours-product-direction.md)). No migration. No commit. V1 **not rescored**.

**Subsequent status (2026-09-16 SCH-D physical iPhone UAT in progress):** Joel-operated iPhone notes recorded. Layout liked; remaining ISO/UAT/warning copy called noise. Extra work not seen (label is Extra work). Enter time on Pour **FAIL** → Confirm Project. Today-Tuesday / week day picker / month project rollup / employee-only schedule permission **not implemented**. No physical PASS. No commit. Evidence [testing/fg035-sch-d-live-physical-iphone-uat-record.md](../testing/fg035-sch-d-live-physical-iphone-uat-record.md). SCH-D **not closed**. V1 **not rescored**.

**Subsequent status (2026-09-16 SCH-D live UAT setup):** SCH-D **IMPLEMENTED / TESTED / SERVER-SIDE LIVE UAT PASS / PHYSICAL IPHONE UAT NOT YET PERFORMED**. No migration. Synthetic Project **48**. Server-side Field/Time **PASS**. HTTPS **5443** running. Physical iPhone UAT is Joel-operated and **not claimed**. Evidence [testing/fg035-sch-d-live-physical-iphone-uat-record.md](../testing/fg035-sch-d-live-physical-iphone-uat-record.md). SCH overall **OPEN / PARTIAL**. SCH-D **not closed**. No new ADR. V1 **not rescored**.

**Subsequent status (2026-09-16 SCH-D implementation):** SCH-D **IMPLEMENTED / TESTED / NOT LIVE-UAT / PHYSICAL IPHONE UAT NOT CLAIMED**. No migration. Field `/field/today` extended with **My work**; `/field/week`, `/field/month`, `/field/company-today` GETs; `/field/schedule/today` maps to Today. `assemble_field_schedule` / `suggest_time_attribution` in `app/services/schedule.py`. Worker Today / Week / Month = USER or Crew membership on date D. Company Today is secondary read-only awareness including scheduled-but-unassigned. No Field Schedule POSTs. TIME remains authoritative. Dedicated `tests/test_work_schedule_field_fg035.py`. Manual Impact **CURRENT**. SCH overall **OPEN / PARTIAL**. SCH-D **not closed**. Physical iPhone UAT **NOT CLAIMED**. No new ADR. V1 **not rescored**.

**Subsequent status (2026-09-16 SCH-C live migrate + bounded synthetic UAT):** SCH-C **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. Additive **`f9b0c1d2e3f4`** applied live (`f7f8a9b0c1d2` → **`f9b0c1d2e3f4 (head)`**). Live current = repository head. Synthetic Project **47**. Projects **45** / **46** unchanged. EST-2026-0019 unchanged. Evidence [testing/fg035-sch-c-live-bounded-uat-record.md](../testing/fg035-sch-c-live-bounded-uat-record.md). SCH overall **OPEN / PARTIAL**. SCH-D **NOT AUTHORIZED**. No new ADR. V1 **not rescored**.

**Subsequent status (2026-09-16 SCH-C resume / verify / complete):** Existing uncommitted SCH-C preserved. Additive **`f9b0c1d2e3f4`** preserved (parent **`f7f8a9b0c1d2`**; `f8a9b0c1d2e3` remains FG-016). Resume tests: dedicated SCH-C **14 passed**; SCH-A+SCH-B **22 passed**; focused **135 passed**; full suite **1119 passed**, 3705 warnings, **453.73s**, exit **0**. Manual Impact **CURRENT**. Manual **FRAMEWORK ACTIVE**. Live current remains **`f7f8a9b0c1d2`**. Not committed. SCH-D **NOT AUTHORIZED**. V1 **not rescored**.

**Subsequent status (2026-09-16 User Manual continuity / Manual Impact):** Help / Voice / Manual remain **NOT IMPLEMENTED**. Lightweight **MANUAL IMPACT — SCH-C** recorded in [architecture/manual-impact-log.md](../architecture/manual-impact-log.md). Kevin / Ben receive the completed User Guide **BEFORE** platform access. Does **not** authorize Help / Voice / Manual product or SCH-C live migrate. V1 **not rescored**.

**Subsequent status (2026-09-16 SCH-C implementation):** SCH-C **IMPLEMENTED / TESTED / NOT LIVE-MIGRATED** (as of that pass). Additive **`f9b0c1d2e3f4`** parented on **`f7f8a9b0c1d2`**. Expected token `f8a9b0c1d2e3` collides with FG-016; next unique sequential id minted. Repository Alembic head **`f9b0c1d2e3f4`**. Live current remained **`f7f8a9b0c1d2`** until the later authorized live migration. Sequence / predecessor-unscheduled facts are informational warnings only. KEEP / MOVE / REVIEW are optional affordances. SCH-D **NOT AUTHORIZED**. No new ADR. V1 **not rescored**.

**Subsequent status (2026-09-16 platform-wide warning law + Print recording):** Warnings are **INFORMATIONAL ONLY / NON-BLOCKING**. Canonical [architecture/project-element-authority-future-record.md](../architecture/project-element-authority-future-record.md). SCH-C sequence/unscheduled-predecessor facts remain warnings, not Save blockers. Print **RECORDED / IMPLEMENTATION SEQUENCED LATER**. Gate remains **OPEN / PARTIAL**. V1 **not rescored**.

**Subsequent status (2026-09-16 platform-wide desktop Print / paper workflow recording):** Print is a **V1 product requirement** and **not** a separate V1 scoring unit. Canonical record [architecture/project-element-authority-future-record.md](../architecture/project-element-authority-future-record.md) (Contractor Language + UX E2E Audit). Schedule Print is a presentation of the **same** Schedule authority as SCH-D Today / Week / Month. This does **not** authorize Print product, SCH-C, or SCH-D. Gate remains **OPEN / PARTIAL**. V1 **not rescored**.

**Subsequent status (2026-09-16 SCH-B live migrate + bounded synthetic UAT):** SCH-B **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. Additive **`f7f8a9b0c1d2`** applied live (`f6e7f8a9b0c1` → **`f7f8a9b0c1d2 (head)`**). Live current = repository head. Synthetic Project **46**. Project **45** unchanged. EST-2026-0019 unchanged. Evidence [testing/fg035-sch-b-live-bounded-uat-record.md](../testing/fg035-sch-b-live-bounded-uat-record.md). SCH overall **OPEN / PARTIAL**. SCH-C / SCH-D **NOT AUTHORIZED**. No new ADR. V1 **not rescored**.

**Subsequent status (2026-09-16 SCH-B implementation):** SCH-B **IMPLEMENTED / TESTED / NOT LIVE-MIGRATED** at that pass. Additive **`f7f8a9b0c1d2`** parented on **`f6e7f8a9b0c1`**. Live current then remained **`f6e7f8a9b0c1`**. Project **46** was not created in that pass.

**Subsequent status (2026-09-15 SCH-A live-UAT reconciliation):** SCH-A **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. Live current = repository head **`f6e7f8a9b0c1`**. Live migration is proven/reconciled from the pre-SCH-A backup (`f5d6e7f8a9b0`, no schedule tables) versus current live `f6` with schedule tables present. The reconciliation prompt did **not** apply the migration and did **not** create a second UAT project. Existing Project **45** was preserved. Evidence [testing/fg035-sch-a-live-bounded-uat-record.md](../testing/fg035-sch-a-live-bounded-uat-record.md). SCH overall **OPEN / PARTIAL**. SCH-B / SCH-C / SCH-D **NOT AUTHORIZED**. SCOPE **IMPLEMENTED / LIVE-MIGRATED / SYNTHETIC UAT PASS**. Additive **`f4c5d6e7f8a9`**. TIME **IMPLEMENTED / LIVE-MIGRATED / SYNTHETIC UAT PASS**. Additive **`f5d6e7f8a9b0`**. SCH architecture **PREFLIGHT COMPLETE / RECORDED**. Design freeze remains [fg-035-sch-implementation-preflight.md](../architecture/fg-035-sch-implementation-preflight.md). PERF / CLOSE / LEARN / QB-T remain **NOT AUTHORIZED**. [architecture/interactive-help-voice-and-user-manual-future-record.md](../architecture/interactive-help-voice-and-user-manual-future-record.md) remains **COMPLETE FOR PRODUCT-DIRECTION RECORDING / NOT IMPLEMENTATION-AUTHORIZED**. Do **not** implement Help, Voice, Manual, or SCH-B/C/D from this gate.

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **OPEN / PARTIAL** |
| TAX/WBS | **IMPLEMENTED** — baseline + org catalog; Project Element / Activity instances; explicit EstimateLabourSnapshot seed; Hub Project work |
| SCOPE | **IMPLEMENTED** — ORIGINAL / CHANGE_ORDER / EXTRA_WORK lineage on Project work; Change Order deltas; Extra Work; Hub/Field presentation |
| TIME | **IMPLEMENTED** |
| SCH | **OPEN / PARTIAL** — SCH-A **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. SCH-B **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. SCH-C **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. SCH-D **IMPLEMENTED / TESTED / SERVER-SIDE LIVE UAT PASS / PHYSICAL IPHONE UAT PASS / COMMITTED / SHA-PINNED / PUSHED**. Architecture **RECORDED**; design freeze [fg-035-sch-implementation-preflight.md](../architecture/fg-035-sch-implementation-preflight.md) |
| PERF | **OPEN / PARTIAL** — PERF-A **IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS**. PERF-B **IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS / COMMITTED / SHA-PINNED / PUSHED**. PERF-C **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE UAT PASS / SEALED** |
| CLOSE | **NOT AUTHORIZED** |
| LEARN | **NOT AUTHORIZED** |
| QB-T | **NOT AUTHORIZED** |
| Schema / Alembic | Additive TAX/WBS **`f3b4c5d6e7f8`** revises **`f2a3b4c5d6e7`**. Additive SCOPE **`f4c5d6e7f8a9`** revises **`f3b4c5d6e7f8`**. Additive TIME **`f5d6e7f8a9b0`** revises **`f4c5d6e7f8a9`**. Additive SCH-A **`f6e7f8a9b0c1`** revises **`f5d6e7f8a9b0`**. Additive SCH-B **`f7f8a9b0c1d2`** revises **`f6e7f8a9b0c1`**. Additive SCH-C **`f9b0c1d2e3f4`** revises **`f7f8a9b0c1d2`** (**live current = repository head**) |
| V1 scoring | **OFFICIAL RESCORE 2026-09-17: 65% / 4 of 11** (this gate did not itself change the score; TIME/SCH/PERF remain inside existing V1-08/V1-09 factors) |

```text
FG-035:
OPEN / PARTIAL
TAX/WBS IMPLEMENTED
SCOPE IMPLEMENTED
TIME IMPLEMENTED
SCH-A IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS
SCH-B IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS
SCH OVERALL OPEN / PARTIAL
SCH-C IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS
SCH-D IMPLEMENTED / TESTED / SERVER-SIDE LIVE UAT PASS / PHYSICAL IPHONE UAT PASS / COMMITTED / SHA-PINNED / PUSHED
WARNING LAW INFORMATIONAL ONLY / NON-BLOCKING / PLATFORM-WIDE
PRINT RECORDED / IMPLEMENTATION SEQUENCED LATER
PERF-A IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS
PERF-B IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS / COMMITTED / SHA-PINNED / PUSHED
PERF-C IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE UAT PASS / SEALED
CLOSE NOT AUTHORIZED
LEARN NOT AUTHORIZED
QB-T NOT AUTHORIZED
ONE LOOP
ONE PLATFORM / ONE CODEBASE
ORG EXTENSIONS ARE CONFIGURATION
FG-023 NOT REOPENED
FG-032 NOT REWRITTEN
V1 NOT RESCORED
```

---

## Purpose

Provide the complete operational / learning loop recorded in [project-element-authority-future-record.md](../architecture/project-element-authority-future-record.md) and bounded by [ADR-053](../adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md):

FROZEN ESTIMATE VERSION → PROJECT WORK STRUCTURE → SCHEDULE / ASSIGNMENT → FIELD TIME → TIME APPROVAL → APPROVED LABOUR ACTUALS → MONITOR / ALERTS → CLOSEOUT REVIEW → LEARN → HUMAN-ACCEPTED CALIBRATION.

TAX/WBS is the foundation every later slice consumes. Later slices are **not** authorized merely because this Feature Gate exists.

---

## Feature Gate answers

| # | Question | Answer |
|---|---------|--------|
| 1 | What problem does this solve? | There is no Project → Element → Activity work authority. Time, Schedule, labour-hours MONITOR, Extra Work, Closeout LEARN quality, and calibration cannot share one structure. |
| 2 | Who is the user? | Office contractor (TAX/WBS configuration and Hub seed). Later slices add field workers (Time / Extra Work) and PM approval. Not customers. |
| 3 | Which module owns it? | Projects owns WBS catalog and instances. Estimating owns LabourTask/snapshots. BUILD will own Time. MONITOR/LEARN consume. Project Controls owns ChangeOrder. |
| 4 | What data does it own (TAX/WBS + SCOPE)? | TAX/WBS tables plus `project_work_scope_deltas`, `project_work_scope_history`, and `scope_origin` / `change_order_id` on Project work. |
| 5 | What data does it reference? | `Organization`, `Project`, `EstimateVersion`, `EstimateLabourSnapshot`, `LabourTask`, `ChangeOrder`. |
| 6 | What may it change? | Additive WBS + SCOPE schema; Hub BUILD Project work panel; Work types office catalog; Field Extra work surface; navigation. |
| 7 | What must it not change? | `ProjectCommercialContext`; `LabourTask` semantics; `ChangeOrder` commercial lifecycle; `ProjectDirectCostActual`; Field capture; FG-023 MONITOR money projection; FG-032 packages; EST-2026-0019; V1 score. |
| 8 | What are the acceptance criteria? | TAX/WBS: three-layer taxonomy; explicit locked/Accepted snapshot seed. SCOPE: original immutable; CO deltas; Extra Work; tenant CO safety; Hub/Field copy; tests + live migrate. Full gate close requires all eight slices. |
| 9 | What tests are required? | Dedicated TAX/WBS and SCOPE tests; Alembic upgrade/downgrade/fresh DB; Hub/catalog/Field office tests; tenant isolation; focused regression; full suite. |
| 10 | What documentation must be updated? | This gate; ADR-053; module/index/continuity docs; UAT records. No V1 rescore. |
| 11 | Does it require an ADR? | **Yes.** ADR-053. |
| 12 | What is explicitly out of scope for this prompt? | TIME, SCH, PERF, CLOSE, LEARN, QB-T, clock-in, Crew Template catalog, CPM, live Postmark, language audit, Time/Schedule UI. |

---

## Complete workstream slices

### TAX/WBS — Work taxonomy and Project work structure

**Status: IMPLEMENTED (this prompt).**

Baseline catalog + organization extensions + Project instances. Work-structure Project Type is **not** commercial `project_type`. Activity may reference LabourTask. Explicit Hub **Build project work** from locked/Accepted `EstimateVersion` with labour snapshots. Pins are immutable. Duplicate seed fail-closed. Evidence [testing/fg035-tax-wbs-live-bounded-uat-record.md](../testing/fg035-tax-wbs-live-bounded-uat-record.md).

**STOP:** no Time; no Schedule.

### SCOPE — Scope origin, Extra Work, Change Order overlay

**Status: IMPLEMENTED (this prompt).**

Original Estimate-seeded work is immutable historical evidence. Eligible Change Orders (Approved / Invoiced) add work or labour/quantity deltas. Draft / unapproved COs cannot become authorized Project scope. Extra Work is operational capture before a CO exists. `ChangeOrder` remains the sole commercial SoR. Evidence [testing/fg035-scope-live-bounded-uat-record.md](../testing/fg035-scope-live-bounded-uat-record.md).

**STOP (SCOPE slice, historical):** no Schedule from SCOPE. Subsequent SCH-A is a separate slice.

### TIME — Field duration entry and approval

**Status: IMPLEMENTED / LIVE-MIGRATED / SYNTHETIC UAT PASS.** Duration-based Time Entry (`labour_time_entries` / `labour_time_history`). Worker enters Project → work → hours. SCOPE lineage is inherited via `inherit_scope_lineage()`. Extra Work uses existing `create_extra_work`. No Draft. No clock-in. No offline Time sync. Submitted is not approved actual. Self-approval fail-closed. Approved labour query: `approved_labour_hours()`. Field `/field/.../time` + My time; office `/time`; Hub `#hub-time`. Additive **`f5d6e7f8a9b0`**. Evidence [testing/fg035-time-live-bounded-uat-record.md](../testing/fg035-time-live-bounded-uat-record.md).

**STOP (TIME slice, historical):** no Schedule from TIME; no labour-budget alerts; no QB Time export. Subsequent SCH-A is a separate slice.

### SCH — Dynamic Schedule + assignment + desktop/iPhone calendar

**Status: SCH-A IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS. SCH-B IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS. SCH-C IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS. SCH-D IMPLEMENTED / TESTED / SERVER-SIDE LIVE UAT PASS / PHYSICAL IPHONE UAT PASS / COMMITTED / SHA-PINNED / PUSHED.** SCH overall **OPEN / PARTIAL**. Architecture **PREFLIGHT COMPLETE / RECORDED**. Design freeze [architecture/fg-035-sch-implementation-preflight.md](../architecture/fg-035-sch-implementation-preflight.md). Platform-wide **warning law** **INFORMATIONAL ONLY / NON-BLOCKING** ([architecture/project-element-authority-future-record.md](../architecture/project-element-authority-future-record.md)). SCH-A: `WorkScheduleItem` / `work_schedule_items`, `WorkScheduleHistory` / `work_schedule_history`, `app/services/schedule.py`, Company `/schedule`, Hub `#hub-schedule`, form create/edit/retire. Additive **`f6e7f8a9b0c1`**. SCH-B: `WorkScheduleAssignment` / `work_schedule_assignments`, optional `OrganizationCrew` / `OrganizationCrewMember`, dedicated `/settings/crews`, USER XOR Crew, ASSIGNED/UNASSIGNED history (Integer `assignment_id`, no FK), overlap warnings as read projection. Additive **`f7f8a9b0c1d2`**. SCH-C: `ProjectWorkDependency` / `project_work_dependencies`, Element→Element, cycle reject, sequence / predecessor-unscheduled informational warnings, optional KEEP / MOVE / REVIEW. Additive **`f9b0c1d2e3f4`** (**live current = repository head**). SCH-D: Field `/field/today` My work, `/field/week`, `/field/month`, `/field/company-today` GET, `/field/schedule/today` alias, `assemble_field_schedule`, `suggest_time_attribution`. No new table. No Field Schedule POSTs. Physical iPhone UAT **PASS**. Committed / SHA-pinned / pushed. No new ADR.

### PERF — Labour-hours performance, alerts, Needs Attention, three MONITOR views

**Status: OPEN / PARTIAL.** PERF-A **IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS** (2026-09-17). Freeze [architecture/fg-035-perf-a-implementation-preflight.md](../architecture/fg-035-perf-a-implementation-preflight.md). Project **49**. Evidence [testing/fg035-perf-a-live-bounded-uat-record.md](../testing/fg035-perf-a-live-bounded-uat-record.md). PERF-B **IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS / COMMITTED / SHA-PINNED / PUSHED** (2026-09-17). Freeze [architecture/fg-035-perf-b-implementation-preflight.md](../architecture/fg-035-perf-b-implementation-preflight.md). Project **50**. Evidence [testing/fg035-perf-b-live-bounded-uat-record.md](../testing/fg035-perf-b-live-bounded-uat-record.md). PERF-C (company attention) **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE UAT PASS / SEALED**. Freeze [architecture/fg-035-perf-c-product-definition.md](../architecture/fg-035-perf-c-product-definition.md). Evidence [testing/fg035-perf-c-live-uat-record.md](../testing/fg035-perf-c-live-uat-record.md). Company/Management authorization **CLOSED / OPERATIONAL FOR COMPANY_MANAGEMENT AUTHORIZATION** ([FG-037](FG-037-company-management-access-domain-authorization.md)).

### CLOSE — Closeout review and LEARN evidence quality

**Status: NOT AUTHORIZED.** Historical heading retained. This remains **LEARN evidence-quality Closeout**, not CORE CLOSE.

**Subsequent owner decision (2026-09-18):** CORE CLOSE / Project operating lifecycle is a **distinct** product authority. Freeze [architecture/core-close-project-lifecycle-product-direction.md](../architecture/core-close-project-lifecycle-product-direction.md) **RECORDED MANDATORY PRODUCT DIRECTION / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. V1 operating lifecycle **ACTIVE / CLOSED**. Punch List → Project Completion Sign-Off → Close Project recorded. LEARN Closeout above remains separately unauthorized.

### LEARN — Comparability, recommendations, calibration provenance

**Status: NOT AUTHORIZED.**

### QB-T — Approved-time export readiness

**Status: NOT AUTHORIZED.**

---

## Production boundary

```text
TAX/WBS: LOCAL OFFICE UAT PROVEN.
SCOPE: LOCAL OFFICE UAT PROVEN.
TIME: LOCAL OFFICE SYNTHETIC UAT PROVEN.
SCH-A: IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS.
SCH-B: IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS.
SCH-C: IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS.
SCH-D: IMPLEMENTED / TESTED / SERVER-SIDE LIVE UAT PASS / PHYSICAL IPHONE UAT PASS / COMMITTED / SHA-PINNED / PUSHED.
SCH OVERALL OPEN / PARTIAL.
PERF-A: IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS.
FG-035 REMAINS OPEN / PARTIAL.
PHYSICAL IPHONE UAT PASS (SCH-D).
PERF-C: IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE UAT PASS / SEALED.
CORE CLOSE: SLICE A IMPLEMENTED IN WORKING TREE / TESTED / MIGRATION FILE CREATED / NOT LIVE-MIGRATED / NOT COMMITTED.
CLOSE/REOPEN: NOT IMPLEMENTED.
PUNCH LIST: NOT IMPLEMENTED.
COMPLETION SIGN-OFF: NOT IMPLEMENTED.
DO NOT IMPLEMENT PUNCH LIST / COMPLETION SIGN-OFF / LEARN / QB-T FROM THIS GATE ALONE.
DO NOT LIVE-MIGRATE FROM THIS GATE ALONE.
DO NOT IMPLEMENT PERF-C FILTERING FROM THIS GATE ALONE.
V1 NOT RESCORED.
```
