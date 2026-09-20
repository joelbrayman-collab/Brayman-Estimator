# Module — Projects

| Attribute | Value |
|-----------|--------|
| Status | **Current** (project records + change orders package). [FG-011](../feature-gates/FG-011-project-hub-ux.md) Project Hub UX **CLOSED / OPERATIONAL FOR UAT** |
| Updated | 2026-09-19 |
| Code | `app/models/project.py`, `app/models/work_structure.py`, `app/models/schedule.py`, `app/models/punch_list.py`, `app/models/final_walkthrough.py`, `app/routes/projects.py`, `app/routes/punch_list.py`, `app/routes/final_walkthrough.py`, `app/routes/walkthrough.py`, `app/routes/work_structure.py`, `app/routes/schedule.py`, `app/services/project_hub.py`, `app/services/project_operating_lifecycle.py`, `app/services/project_punch_list.py`, `app/services/project_final_walkthrough.py`, `app/services/project_performance.py`, `app/services/work_structure.py`, `app/services/schedule.py`; Organization Crew: `app/models/organization_crew.py`, `app/services/organization_crew.py`, `app/routes/organization_crew.py`; Project Controls: `app/project_controls/` |
| Feature Gate | [FG-011](../feature-gates/FG-011-project-hub-ux.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-015](../feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **CLOSED / OPERATIONAL FOR UAT** (Hub PLAN Permit Report state + `/projects/<id>/permit-report`). [FG-035](../feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) **OPEN / PARTIAL** — TAX/WBS **IMPLEMENTED**. SCOPE **IMPLEMENTED**. TIME **IMPLEMENTED**. SCH-A **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. SCH-B **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. SCH-C **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. SCH-D **IMPLEMENTED / TESTED / SERVER-SIDE LIVE UAT PASS / PHYSICAL IPHONE UAT PASS / COMMITTED / SHA-PINNED / PUSHED**. SCH overall **OPEN / PARTIAL**. PERF-A **IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS**. PERF-B **IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS / COMMITTED / SHA-PINNED / PUSHED**. PERF-C **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE UAT PASS / SEALED**. CORE CLOSE Slice A **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE-MIGRATED**. CORE CLOSE Slice B **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NO MIGRATION**. Close/Reopen Option A **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NO MIGRATION / NOT LIVE-UATed**. Close/Reopen product SHA **`172f0786aaa9e668f30be28c3cee30ac4fce5b1f`**. C1 Contractor Punch List **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE-MIGRATED / EMPTY LIVE BASELINE VERIFIED**. C2 Client Final Walkthrough **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE-MIGRATED / EMPTY LIVE BASELINE VERIFIED / NOT LIVE-UATed WITH CLIENT DATA**. Product SHA **`ec4ef9956025fd8e281c12c17d84493b121f8337`**. Completion Sign-Off **NOT IMPLEMENTED**. Company/Management authorization **CLOSED / OPERATIONAL FOR COMPANY_MANAGEMENT AUTHORIZATION**. |

## Purpose

Represent construction projects tied to clients; host estimating work; begin project controls (change orders). Long-term home for budgets, scheduling, purchasing, and job cost—**only when Feature-Gated**.

## Responsibilities (current)

- Project CRUD (name, number, address, status, description, client). Field SCH-D presents the same `Project.address` (no Field duplicate) plus a Directions phone-maps handoff.
- Parent for estimates
- Change Orders lifecycle (draft → approval statuses) via `project_controls` package
- D1 Project Hub contextual Help **IMPLEMENTED** (`app/presentation/help_content.py`; native `<details>` on PLAN / PRICE / CONTRACT / BUILD / MONITOR; LEARN Future-only). D3 office Help **IMPLEMENTED** on the same authority (`topics_for_surface("office")`, `help_payload()`). D4 Field Help **IMPLEMENTED** on the same authority (`topics_for_surface("field")`, `field_topic()`). D5 Voice-with-Help **IMPLEMENTED IN WORKING TREE** on the same authority (`answer_help_question()`, `POST /help/ask`). Voice does not mutate product state. No schema. Contextual Help coverage complete for Hub / Office / Field. User Guide remains outstanding.
- Project Hub UX at `/projects/<id>` ([FG-011](../feature-gates/FG-011-project-hub-ux.md) **CLOSED / OPERATIONAL FOR UAT**): identity, versioned commercial context, PLAN / PRICE / CONTRACT stored facts and links, existing Change Orders under BUILD **plus** BUILD Field Observations ([FG-020](../feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) **CLOSED / OPERATIONAL FOR UAT**); BUILD **Project work** ([FG-035](../feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) TAX/WBS + SCOPE); BUILD **Punch List** Hub `#hub-punch-list` ([FG-035] CORE CLOSE C1 **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE-MIGRATED / EMPTY LIVE BASELINE VERIFIED**); BUILD **Client Final Walkthrough** Hub `#hub-final-walkthrough` ([FG-035] CORE CLOSE C2 **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE-MIGRATED / EMPTY LIVE BASELINE VERIFIED / NOT LIVE-UATed WITH CLIENT DATA**); BUILD **Schedule** Hub `#hub-schedule` ([FG-035] SCH-A + SCH-B + SCH-C; same `assemble_schedule` as Company `/schedule`; Field SCH-D presents the same rows); BUILD **Time** Hub `#hub-time` ([FG-035] TIME); BUILD **Labour** Hub `#hub-labour` ([FG-035] PERF-A **IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS** + PERF-B Needs Attention **IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS / COMMITTED / SHA-PINNED / PUSHED**); MONITOR V1 `#hub-monitor` comparison + office actuals writes ([FG-023](../feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) **CLOSED / OPERATIONAL FOR UAT**; Slice B **implemented / live-migrated / office-UAT-verified**); LEARN labeled Future. Read-only assembly in `app/services/project_hub.py` plus BUILD-owned actuals POSTs and work-structure seed POSTs owned by Projects. Punch List mutations are owned by `app/routes/punch_list.py` / `app/services/project_punch_list.py`. No durable hub entity.

## Owned data

- `projects` (FG-035 CORE CLOSE Slice A additive `operating_state` / `operating_state_changed_at` / `operating_state_changed_by_user_id`; migration **`b2c3d4e5f6a7` applied live** 2026-09-18)
- `project_operating_state_events` (FG-035 CORE CLOSE Slice A; human CLOSE/REOPEN audit; table live / row count **0**; Option A Close/Reopen product SHA **`172f0786aaa9e668f30be28c3cee30ac4fce5b1f`** — **NOT LIVE-EXECUTED**)
- `project_punch_list_items`, `project_punch_list_item_events` (FG-035 CORE CLOSE C1; additive **`d4e5f6a7b8c9` applied live**; Punch List **LIVE / 0 ITEMS**)
- `project_final_walkthrough_invitations`, `project_final_walkthrough_items`, `project_final_walkthrough_access_attempts` (FG-035 CORE CLOSE C2; additive **`e5f6a7b8c9d0` applied live**; live C2 rows **0**)
- `project_locations` (1:1 civic location; FG-015)
- `permit_profiles` (versioned preliminary snapshots; FG-015)
- `permit_analyses`, `permit_findings`, `project_permit_facts` (FG-016 project-tied Pass 2; organization-scoped)
- `change_orders`, `change_order_items` (package-owned tables)
- `work_types`, `work_element_templates`, `work_activity_templates`, `project_work_elements`, `project_work_activities`, `project_work_structure_seeds`, `project_work_scope_deltas`, `project_work_scope_history` (FG-035 TAX/WBS + SCOPE; organization-scoped except baseline `organization_id` NULL)
- `work_schedule_items`, `work_schedule_history` (FG-035 SCH-A; organization-scoped overlay on Project work)
- `work_schedule_assignments` (FG-035 SCH-B; current USER XOR Crew booking on an ACTIVE SCH-A item; not historical SoR)
- `project_work_dependencies` (FG-035 SCH-C; Element→Element ACTIVE/INACTIVE sequence; not CPM)

Platform-shared (not org-owned): `jurisdiction_definitions`, `jurisdiction_aliases`, `permit_rules`, `legal_content_jurisdiction_packages`, `legal_content_objects` (FG-024 Slice A; live / empty), `legal_content_sources`, `legal_content_source_snapshots`, `legal_content_candidate_changes`, `legal_content_candidate_impacts`, `legal_content_review_events` (FG-024 Slice B; live; labeled UAT source evidence only, not legal authority), `legal_content_activation_events` (FG-024 TECH-A; live; empty after synthetic UAT cleanup).

Org-scoped generated contracts (FG-024 Slice C; **live / synthetic-UAT proven**; TECH-B proposal pin / WARN provenance **live**; TECH-C Family 05 DOCX merge + private custody **live**; not a real customer contract): `project_generated_contracts`, `project_contract_snapshots`, `project_contract_snapshot_objects`. Services: `app/services/contract_generation.py`, `app/services/family_05_master.py`, `app/services/family_05_contract_merge.py`, `app/services/contract_artifact_storage.py`.

## Referenced data

- `clients` (required FK)
- Optional `estimate_versions` on change orders
- Organization-owned Crew configuration (`organization_crews`, `organization_crew_members`; FG-035 SCH-B; optional; not FG-008 Crew Template)

## Prohibited responsibilities

- Owning proposal snapshot documents (Proposals)
- Owning cost library master data (Estimating)
- Owning Plan Intelligence / take-off / labour catalog / pricing-policy records (read/link only under FG-011)
- Full ERP/accounting
- Field-execution records (proposed **BUILD** module — [build.md](build.md); [ADR-020](../adr/ADR-020-build-module-boundary.md))
- Permit Intelligence / jurisdictional legal library / live regulatory lookup / in-product web lookup / automatic permit approval conclusions / municipal submissions — Pass 2 **[FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) CLOSED / OPERATIONAL FOR UAT**. Live lookup / municipal submissions remain **not authorized**. Foundation **CLOSED / OPERATIONAL FOR UAT**: [FG-015](../feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md). Architecture **Accepted**: [ADR-037](../adr/ADR-037-project-location-and-jurisdiction-resolution.md) / [ADR-038](../adr/ADR-038-permit-intelligence-authority-and-rules-library.md) / [ADR-039](../adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md). Projects owns project location, project-tied resolution, the profile/snapshot relationship, and project-tied permit facts / report versions. Permit Rules Library is platform-governed, not org commercial intelligence.
- Organization Brand Profile / org-owned logo storage — **not authorized**. Pin only: [organization-brand-profile.md](../architecture/organization-brand-profile.md).
- Change Order document-family rewrite, client email, field-native UX, or a second Change Order entity — **not authorized**. Pin only: [change-order-document-family.md](../architecture/change-order-document-family.md). Existing Change Order business record remains authoritative. Native Signing is an overlay owned by [signing.md](signing.md) ([FG-033](../feature-gates/FG-033-native-signing-document-approval-signature-and-executed-artifact.md) SIGN-A **IMPLEMENTED**); it freezes a copy of the current CO PDF and does **not** alter `CHANGE_ORDER_STATUSES`.

## Current implementation

- Project statuses include default `Lead` (model default). `Project.status` is the CRM / pipeline label and is **not** operating-set authority. CORE CLOSE Slice A persists `Project.operating_state` **ACTIVE / CLOSED** plus `ProjectOperatingStateEvent` and `list_current_operating_projects` ([architecture/core-close-project-lifecycle-product-direction.md](../architecture/core-close-project-lifecycle-product-direction.md)). Slice B **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NO MIGRATION** (product SHA **`9360b706ab66f2588306b201ca0c4c45645fcb9a`**): default operating consumers use `list_current_operating_projects`; `list_organization_projects` remains ALL; `get_organization_project` remains historical including CLOSED; Projects **Current | Closed**; CLOSED guards NEW operational work. Live DB unchanged: every Project is **ACTIVE**; event rows **0**. Close/Reopen Option A is **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NO MIGRATION / NOT LIVE-EXECUTED**. C1 Punch List is **LIVE / 0 ITEMS**. C2 Client Final Walkthrough is **LIVE-MIGRATED / EMPTY LIVE BASELINE / 0 INVITATIONS**. D1 Project Hub contextual Help is **IMPLEMENTED**. Completion Sign-Off remains **NOT IMPLEMENTED**. Subsequent [FG-038](../feature-gates/FG-038-instance-owner-authority-foundation.md) PA-A Instance Owner authority seam is **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NOT LIVE-MIGRATED / NO OWNER ASSIGNED** and is **not** Project-owned.
- Change Orders: statuses in `CHANGE_ORDER_STATUSES`; list/detail/PDF support in package
- Nav: Change Orders enabled; Purchase Orders & Job Costing **disabled placeholders**

## Planned capabilities

- Project Hub UX — **Current** ([FG-011](../feature-gates/FG-011-project-hub-ux.md) **CLOSED / OPERATIONAL FOR UAT**)
- Project creation from accepted proposal snapshot (Rule 4) — **Future** (not FG-011)
- Project budgets, scheduling, purchasing, job costing, invoicing — **Future**
- Change order audit trail UI — noted as future in template
- Project work taxonomy / Time / Schedule / LEARN consumers — TAX/WBS + SCOPE + TIME **Current**; SCH-A **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**; SCH-B **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**; SCH-C **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**; SCH-D **IMPLEMENTED / TESTED / SERVER-SIDE LIVE UAT PASS / PHYSICAL IPHONE UAT PASS / COMMITTED / SHA-PINNED / PUSHED** ([FG-035](../feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) **OPEN / PARTIAL**). SCH overall **OPEN / PARTIAL**. Design freeze [architecture/fg-035-sch-implementation-preflight.md](../architecture/fg-035-sch-implementation-preflight.md). PERF-A **IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS** ([architecture/fg-035-perf-a-implementation-preflight.md](../architecture/fg-035-perf-a-implementation-preflight.md)). PERF-B **IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS / COMMITTED / SHA-PINNED / PUSHED** ([architecture/fg-035-perf-b-implementation-preflight.md](../architecture/fg-035-perf-b-implementation-preflight.md)). PERF-C **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE UAT PASS / SEALED** ([architecture/fg-035-perf-c-product-definition.md](../architecture/fg-035-perf-c-product-definition.md)). CORE CLOSE Slice A **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE-MIGRATED** ([architecture/core-close-project-lifecycle-product-direction.md](../architecture/core-close-project-lifecycle-product-direction.md)). Close/Reopen Option A **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NO MIGRATION / NOT LIVE-UATed**. C1 Contractor Punch List **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE-MIGRATED / EMPTY LIVE BASELINE VERIFIED** (product SHA **`81b6d802ccf15c10b01a1f63337ef4d0d5a26d6c`**). C2 Client Final Walkthrough **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE-MIGRATED / EMPTY LIVE BASELINE VERIFIED / NOT LIVE-UATed WITH CLIENT DATA**. Product SHA **`ec4ef9956025fd8e281c12c17d84493b121f8337`**. Completion Sign-Off **NOT IMPLEMENTED**. Company/Management authorization **CLOSED / OPERATIONAL FOR COMPANY_MANAGEMENT AUTHORIZATION** ([architecture/company-management-access-domain-seam.md](../architecture/company-management-access-domain-seam.md)). LEARN Closeout / LEARN / QB-T **NOT AUTHORIZED**. Desktop Print / paper workflow **RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. Platform-wide warning law **INFORMATIONAL ONLY / NON-BLOCKING** ([architecture/project-element-authority-future-record.md](../architecture/project-element-authority-future-record.md)).
- Project location / jurisdiction resolver / preliminary Permit Profile — **CLOSED / OPERATIONAL FOR UAT** ([FG-015](../feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md)). Preserve `Project.address`.
- Project Permit Intelligence Pass 2 / Permit & Approvals Report analysis — **CLOSED / OPERATIONAL FOR UAT** ([FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md); [permit-and-approvals-report.md](../architecture/permit-and-approvals-report.md); ADR-037/038/039).
- Change Order governed document family / preview-generate-email / field UX — **FUTURE / NOT IMPLEMENTED** pin ([change-order-document-family.md](../architecture/change-order-document-family.md)); not a Feature Gate; do not create a second Change Order entity
- Change Order scope lineage / Extra Work / Closeout LEARN data quality — **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED** ([project-element-authority-future-record.md](../architecture/project-element-authority-future-record.md) §§40–71); does not create a second Change Order entity; does not reopen Project Controls product. CORE CLOSE (operating lifecycle) is a **distinct** recorded authority ([architecture/core-close-project-lifecycle-product-direction.md](../architecture/core-close-project-lifecycle-product-direction.md)).
- Contract / e-signature / signed Change Order — **ARCHITECTURE RECONNAISSANCE COMPLETE / NOT IMPLEMENTED** ([contract-esignature-and-signed-change-order.md](../architecture/contract-esignature-and-signed-change-order.md)); recommendation **NATIVE V1**; counsel spec **PREPARED** ([native-signing-process-counsel-review.md](../legal/native-signing-process-counsel-review.md)); implementation **NOT AUTHORIZED**; signing Feature Gate **not** created in this recon. Contract legal-content lifecycle is [FG-024](../feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / SLICE A CLOSED / OPERATIONAL FOR UAT / SLICE B CLOSED / OPERATIONAL FOR UAT / SLICE C CLOSED / OPERATIONAL FOR UAT / TECH-A IMPLEMENTED / TECH-B IMPLEMENTED / TECH-C IMPLEMENTED / TECH-D IMPLEMENTED / OVERALL OPEN / PARTIAL** (not Native Signing). Preflight: [fg-024-slice-a-legal-content-library-preflight.md](../architecture/fg-024-slice-a-legal-content-library-preflight.md); [fg-024-slice-b-legal-content-source-lifecycle-preflight.md](../architecture/fg-024-slice-b-legal-content-source-lifecycle-preflight.md); [fg-024-slice-c-contract-generation-snapshot-preflight.md](../architecture/fg-024-slice-c-contract-generation-snapshot-preflight.md). [ADR-050](../adr/ADR-050-north-american-legal-content-library-ownership.md) **Accepted**. [ADR-051](../adr/ADR-051-legal-content-source-and-update-lifecycle.md) **Accepted**.
- Contractor-facing Hub / office / Field copy — [FG-025](../feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 1, SLICE 2, SLICE 3, SLICE 4, AND SLICE 5 IMPLEMENTED / NOT CLOSED** (Project Hub display mapping plus office PRICE specialist copy, shared office shell, and Field Web; remaining surfaces not authorized)

## Dependencies

- CRM Clients
- Estimating (child estimates)
- Proposals (future acceptance handoff)

## Invariants

- Project requires Client
- Financially significant change-order approvals should become auditable (Rule 6) — gap acknowledged
- `Project` is the CalibAi lifecycle hub ([ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md) **Accepted**)
- BUILD references Change Orders; it does not replace them ([ADR-020](../adr/ADR-020-build-module-boundary.md) **Accepted**)

## Open decisions

- Whether Project Controls becomes its own top-level module doc
- MONITOR Slice A comparison service and Slice B Hub `#hub-monitor` are **implemented / live-migrated / office-UAT-verified**. Baseline governance is [ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) **Accepted**. V1 recon [monitor-v1-implementation-reconnaissance.md](../architecture/monitor-v1-implementation-reconnaissance.md) is **COMPLETE**. [FG-023](../feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) is **CLOSED / OPERATIONAL FOR UAT**.

## Relevant tests

- `tests/test_core_close_punch_list_c1_fg035.py`
- `tests/test_work_structure_tax_wbs_fg035.py`
- `tests/test_permit_foundation_fg015.py`
- `tests/test_project_hub.py`
- `tests/test_contract_fail_closed_hub_fg024.py`
- `tests/test_change_orders.py`
- Project fixtures embedded across estimate/proposal tests

## Relevant ADRs

- [ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md) **Accepted**
- [ADR-053](../adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**
- [ADR-020](../adr/ADR-020-build-module-boundary.md) **Accepted**
- [ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) **Accepted** (MONITOR V1 **CLOSED / OPERATIONAL FOR UAT**; V1 recon complete)
