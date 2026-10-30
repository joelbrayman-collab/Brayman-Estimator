# Governed Scheduling Engine — approved design

| Attribute | Value |
|-----------|--------|
| Status | **APPROVED DESIGN / RECORDED / NOT IMPLEMENTATION-AUTHORIZED.** No Gantt, schema, migration or behaviour change is authorized by this record. The five open scheduling decisions were **APPROVED on 2026-10-30** (§20); no scheduling decision remains open. |
| Date | 2026-10-30 |
| Owner | Joel Brayman (conceptual design approved through the Architect review) |
| Extends | [fg-035-sch-dynamic-scheduling-preflight.md](fg-035-sch-dynamic-scheduling-preflight.md), the SCH architecture source of record. That record and its SCH-A–D implementation remain authoritative for what exists. This document records the next approved design layer on top of it. |
| ADR | No new ADR. Per the SCH record, extend [ADR-053](../adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) when implementation is authorized. |
| Lifecycle | [estimate-to-project-lifecycle.md](estimate-to-project-lifecycle.md) |
| Inspected | Repository `joelbrayman-collab/Brayman-Estimator`. The application code is identical to origin/main `ed3ff7d6`; this branch adds documentation only. |

```text
CALIBRAYT CREATES THE SCHEDULE.
THE PROJECT MANAGER MANAGES IT.
THE COMPANY GOVERNS COMPANY-LEVEL CONFLICTS.
ACTUAL PERFORMANCE IMPROVES FUTURE SCHEDULES.
ONE GOVERNED SCHEDULE — MANY VIEWS.
```

## 1. Governing principle

There is **one** governed underlying schedule. The following are all views of that one schedule:

- the project Gantt
- the Company Calendar
- project calendars
- crew calendars
- employee calendars
- equipment and resource calendars

The Gantt and the calendars are views and controllers over the engine. They are never independent schedules kept in step with each other. This preserves the existing SCH rule: no second work model, and a single current scheduled window.

## 2. Decision hierarchy

1. **Calibrayt construction intelligence.** Reusable sequencing, dependencies and multi-phase trade relationships. For example: foundation → framing → rough-ins → insulation → drywall → finishes. A trade may make several visits. Plumbing, for instance, has a septic/foundation tie-in, a rough-in and a finish. Each phase has its own duration, dependencies, anticipated window, confirmed window and status.
2. **Company scheduling templates.** Company-configurable templates per project kind: custom home, addition, renovation, ICF foundation, deck, exterior/siding. They cover sequencing, dependencies, crew assumptions, standard subcontract phases and calendars.
3. **Project intelligence.** Project-specific evidence:
   - accepted scope and work packages
   - quantities
   - estimated hours
   - production rates
   - delivery method and subcontracted work
   - material lead times
   - equipment
   - anticipated construction start
4. **Project Manager adjustment.** Calibrayt generates the preliminary schedule. The PM adjusts it rather than building it.
5. **Company governance.** Changes are analysed against company-wide projects and shared resources.
   - A change contained within the project may be committed on PM authority.
   - A change affecting other projects or protected shared resources needs Company Schedule Authority approval.
6. **Actual performance and learning.** The full chain is preserved as calibration evidence for future estimating and scheduling:
   estimated hours → calculated duration → initial proposed duration → PM-adjusted duration → approved duration → actual hours → actual duration.

## 3. Automatic initial Gantt

**Anticipated Construction Start** is a first-class governed **planning input**. It is entered once and reused downstream.

It is **not** the authoritative project start date and never competes with the live schedule (approved decision 2, §20).

The **Proposed Initial Gantt** is generated from whatever of the following is available:

- accepted scope and work packages
- work activities and quantities
- estimated labour hours and production rates
- crew and resource assumptions
- dependencies
- subcontract phases
- material lead times
- equipment
- anticipated start
- the company scheduling template

The objective: a competent PM normally adjusts the schedule rather than constructing it.

## 4. Views

- **Project Gantt:** the primary project-management view.
- **Company Calendar:** the company-wide view of projects and the demands they place on people, crews, equipment and other governed resources.
- **Other calendars:** filtered views of the same schedule.

Moving a Gantt activity does not synchronize another calendar. It proposes a change to the governed schedule. Once the change is effective, every view shows the same authoritative schedule.

## 5. Schedule change impact analysis

Dragging, moving or resizing creates a **proposed** change. Its consequences are analysed and shown before the change becomes authoritative. Nothing cascades silently.

When dependent activities are affected, Calibrayt **automatically calculates the proposed downstream movements**. The PM does not move each dependent activity by hand. Those movements are presented with their impacts and are never committed silently (approved decision 3, §20).

| Kind | Consequences analysed |
|---|---|
| Project | Predecessors and successors; milestones; inspections; completion dates; dependent activities; subcontract phases; material requirements |
| Company | Employees; crews; shared resources; equipment; conflicts with other projects |
| External | Subcontractor commitments; supplier deliveries; rentals; other external commitments |

## 6. Project-contained changes

If a change has no governed adverse cross-project or shared-resource consequence, the PM may commit it. On commit:

- The schedule is updated and versioned.
- The Gantt, Company Calendar, resource calendars and dependent internal information all reflect the change.
- Prior history is preserved.

## 7. Company-impacting changes

A change that affects another project, or a shared crew, employee, item of equipment or other protected resource, becomes a **Company Schedule Change Request**. The original schedule stays authoritative until approval.

This is a **blocking governance gate**, not a warning: the change cannot become authoritative without the required approval. Ordinary scheduling warnings stay non-blocking (approved decision 1, §20).

Authority is the role **COMPANY SCHEDULE AUTHORITY**. It is not hard-coded to a person. Ben may hold the role today.

## 8. Two-authority approval

The PM controls project feasibility. The Company Schedule Authority controls company-resource feasibility. A change that affects both needs both approvals.

Each authority responds with **ACCEPT**, **REJECT** or **PROPOSE NEW TIME**.

- **A rejection** leaves the authoritative schedule unchanged and returns the reason to the PM.
- **A counterproposal** never becomes authoritative automatically. Impact analysis is re-run and the PM responds with ACCEPT, REJECT or PROPOSE NEW TIME.
- **The whole negotiation** is the revisions of **one** request.

Example lineage for one request, `SCR-2027-0042`:

1. original schedule
2. PM proposal
3. impact analysis
4. company counterproposal
5. revised impact analysis
6. PM acceptance
7. approval record
8. effective schedule

## 9. Owner override

An override is an exception, not the normal workflow. It must:

- give an explicit reason
- preserve the previous schedule
- identify the overriding authority
- record the date and time
- immediately notify the affected PM(s)
- identify the affected projects and resources
- remain permanently auditable

## 10. Subcontractor scheduling

A subcontracted trade is not necessarily one block. For example, plumbing might be a tie-in (1 day), a rough-in (4 days) and a finish (2 days).

Each phase has:

- a duration
- dependencies
- an anticipated window
- the subcontractor's availability
- a confirmed window
- a status

The subcontractor supplies scheduling evidence. The PM, with Calibrayt, decides where each phase sits. The subcontractor does not control the project schedule.

## 11. Scheduling information in a subcontract RFQ

An RFQ gives the anticipated work window for each phase. The windows are derived from the anticipated start, the preliminary Gantt, the applicable phases and their dependencies. Example: "Project anticipated to commence: April 2027. Rough-in: late May / early June."

For each phase, the RFQ asks for:

- the duration required
- whether the subcontractor can accommodate the window
- alternate availability if not
- constraints and prerequisites

At RFQ stage these are **planning windows**, not committed dates. The user-facing design must make that distinction plain.

## 12. Subcontractor selection

The comparison considers:

- price
- required duration
- compatibility with the anticipated window
- alternate availability
- historical performance, eventually

The cheapest quote is not automatically the best decision. After award, the subcontractor must formally reconfirm their availability.

## 13. External schedule changes

Once an internal change is fully approved, Calibrayt may update internal consequences automatically. It must **never** silently alter an external commitment or communicate one.

The sequence is:

1. approved internal change
2. external impact analysis
3. **draft created automatically:** the supplier, subcontractor, rental or other external change request or notice
4. **human review and approval** by the responsible communication role (§13A)
5. CaliSIGN sends and tracks it
6. the external party responds (ACCEPT, REJECT/DECLINE or PROPOSE NEW TIME), and the response feeds back into the governed schedule

(Approved decision 4, §20.)

If an external party cannot accommodate the change, the unresolved exception is surfaced.

Conceptual states: **PROPOSED → INTERNALLY APPROVED → EXTERNAL CONFIRMATION PENDING → FULLY CONFIRMED.** These are to be reconciled with existing status conventions rather than duplicating them.

## 13A. Who approves external schedule communication

Approval of external communication is **role-based**. It is not hard-coded to Ben or to the Company Schedule Authority (approved decision 5, §20).

| Communication | Approved by |
|---|---|
| Subcontractor scheduling | The Project Manager, where the PM owns that relationship |
| Supplier delivery changes | The procurement / purchasing role, where it owns that supplier commitment |
| Any communication whose underlying schedule decision has company-level resource consequences | The Company Schedule Authority also participates, in the underlying schedule decision |

**Schedule authority** (who may make a schedule change effective) and **communication responsibility** (who may approve what is said to an outside party) are separate concepts.

## 14. Materials, suppliers and equipment

Backward planning works from the installation date: required installation date → required-on-site date → supplier lead time → latest order date. The same applies to rentals and equipment.

A proposed change identifies any delivery, booking or lead time that cannot support the new date. This record does **not** authorize procurement automation.

## 15. CaliSIGN

Reuse the existing approval-before-send architecture. No second approval engine is to be built for scheduling.

Extend CaliSIGN for:

- company schedule change approvals
- supplier delivery changes
- subcontract schedule changes
- external scheduling confirmations

For each, preserve the signer and approver identity, timestamps, revisions and final disposition.

## 16. Versioning and audit

Schedule history is never overwritten. It must be possible to tell:

- what the schedule was
- who proposed a change, and why
- the impact analysis at that point
- who accepted, rejected or counterproposed
- the external consequences and confirmations
- when the new schedule became effective

## 17. Lineage

drawing → work package → takeoff → estimate → accepted scope → work activity → schedule activity → resource assignment → actual work.

Scheduling is part of the project lineage, not a planning island.

## 18. Lifecycle integration (no separate "Scheduling" stage)

| Stage | Scheduling contribution |
|---|---|
| 4 Estimate build | Scheduling intelligence from quantities, labour, production and delivery method |
| 5 Contractor review | Package participation and delivery method decide self-performed vs subcontracted |
| 7 Proposal and acceptance | The accepted baseline from which the committed plan develops |
| 8 Procurement and subcontracts | Lead times, subcontract durations and availability, confirmed external commitments |
| 9 Execution | The live engine, Gantt, Company Calendar, resources, changes and confirmations |

Progression: estimate → preliminary schedule → supplier/subcontract evidence → approved project schedule → live schedule → actual performance → future calibration.

---

## 19. Reconciliation with the current repository

### Current capability — reuse

| Area | What exists |
|---|---|
| Work authority | `ProjectWorkElement` / `ProjectWorkActivity`. Activities carry quantity, estimated hours, production rate, labour task, source estimate version and scope origin (original / change order / extra work). |
| Schedule | `WorkScheduleItem`: one current window per Element/Activity. Activity windows must sit within the Element window. |
| History | `WorkScheduleHistory`: append-only; created, dates changed, retired, assigned, unassigned, dependency added/removed; prior and new windows; reason. |
| Assignments | `WorkScheduleAssignment` (a worker or a crew) |
| Crews | `OrganizationCrew` / `OrganizationCrewMember`, with effective-dated membership |
| Dependencies | `ProjectWorkDependency` (Element → Element; same project; acyclic) |
| Conflicts | `list_schedule_conflicts`: booking and sequence conflict facts |
| Shifting | Confirmed bulk project shift (`shift_project_schedule`) |
| Notices | Crew SMS schedule notices (`crew_notices`) |
| Company Calendar | `CompanyAppointment` with history; one-way iCalendar feeds (`calendar-integration.md` §3) |
| Supplier deliveries | Linked to schedule items (`SupplierPurchaseOrder.schedule_item_id`). `SupplierDeliveryChange` already supports a proposed date, accept/decline and a counter (`counter_of_id`). |
| CaliSIGN | Statuses CREATED → APPROVED_FOR_SIGNATURE → SENT → SIGNED/EXECUTED. Families: CHANGE_ORDER, CONTRACT, SUPPLIER_ORDER, SUPPLIER_DELIVERY_CHANGE. |
| Time and actuals | Field time against activities; approved labour hours; `ProjectDirectCostActual` |
| Change orders | `ProjectWorkScopeDelta` (hour/quantity deltas against activities) |
| Learning | Labour engine calibration (`LabourCalibrationCandidate`); MONITOR |

### Requires extension

| Area | Extension needed |
|---|---|
| `WorkScheduleItem` | A phase/visit concept for multi-visit subcontract trades. Anticipated vs confirmed window and status. Proposed / effective governance through a change-request record, so the single current window stays the authority. |
| Dependencies | Activity- and phase-level edges where justified (permitted by the SCH record) |
| History | Change-request revisions, the impact analysis at each point, approver identity, overrides |
| `SupplierDeliveryChange` | Route through human review before sending (see the gap below) |
| CaliSIGN | New families: company schedule change, subcontract schedule change, external scheduling confirmation |
| Subcontractor quote evidence | Per-phase duration, window compatibility and alternate availability |
| Company Calendar | Show the governed project schedule and resource demand alongside appointments |
| Learning | Carry the duration chain (§2 level 6) into calibration |

### Connections required

- Selected work / work package to work element (today the seed copies section names). See [estimate-to-project-lifecycle.md](estimate-to-project-lifecycle.md).
- Labour snapshot / estimate line to work activity (`EstimateLabourSnapshot` is designed but never created).
- Subcontract quote phases to schedule phases.
- Material requirement and purchase order lines to schedule activities (PO lines are `lines_json`).
- Approved time to schedule activity, giving actual duration against approved duration.

### Genuine gaps (not to be built from this record)

- Anticipated Construction Start as a planning field
- Company scheduling templates
- Generation of the Proposed Initial Gantt
- The Gantt view itself
- Impact analysis across project, company and external consequences
- The Company Schedule Change Request, with its two-authority negotiation and owner override
- The COMPANY SCHEDULE AUTHORITY role
- Subcontract RFQ anticipated windows
- Schedule-aware subcontractor comparison and post-award reconfirmation
- Backward planning from lead times to latest order date
- Equipment and rental resources

## 20. Approved decisions (2026-10-30)

All five were **APPROVED** by Joel on 2026-10-30. None remains open.

1. **Company-impacting changes are a blocking governance gate.** Ordinary scheduling warnings stay non-blocking, as the platform warning law of 2026-09-16 requires. A proposed change that needs Company Schedule Authority approval **must not** become authoritative until that approval is obtained. This is an authority gate, not a warning, so it does not contradict the warning law.
2. **Anticipated Construction Start is an approved planning input.** It is not the authoritative project start date. It feeds:
   - the Proposed Initial Gantt
   - subcontract planning windows
   - preliminary resource demand
   - other planning outputs

   Once the governed live schedule exists, that schedule is authoritative and the project bar stays derived from it. The SCH rule against `Project.start_date` / `end_date` as a date authority is respected. The anticipated start is kept as historical planning and calibration evidence.
3. **Dependent movement: automate the proposal, not the decision.** Calibrayt calculates the proposed downstream movements automatically, so the PM never moves each dependent activity by hand. Those movements are presented with their project, company and external impacts:
   - **Project-contained consequences** follow PM authority.
   - **Company-impacting consequences** need Company Schedule Authority governance.
   - **External consequences** follow the external-change workflow (§13).

   Nothing cascades silently. This replaces the SCH V1 "no automatic movement" rule with *automatic proposals, human-committed*. CPM, float and lag remain out of scope.
4. **External schedule changes: automatic draft, human approval.** An approved internal change may automatically create the draft supplier, subcontractor, rental or other external request. It must not automatically communicate or alter an external commitment. A responsible person approves the communication before CaliSIGN sends and tracks it. Responses (Accept, Reject/Decline, Propose New Time) feed back into the engine.
   - **Current-code consequence:** today `propose_deliveries_for_schedule_moves` sends the delivery proposal to the supplier directly, with no human review. When implementation is authorized, that path must become *draft → approval → send*. That is an EXTEND item, not an open decision.
5. **External communication approval is role-based** (§13A). Schedule authority and communication responsibility are separate.
