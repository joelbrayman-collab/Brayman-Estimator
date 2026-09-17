# Banked Hours — product-direction record

| Attribute | Value |
|-----------|--------|
| Status | **PRODUCT REQUIREMENT RECORDED / POLICY NOT YET FROZEN / IMPLEMENTATION NOT AUTHORIZED** |
| Recorded | 2026-09-16 |
| Authority | Joel Brayman / ChatGPT Architect |
| Does not interrupt | [FG-035](../feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) SCH-D physical iPhone UAT / Time-entry correction |

This is **not** an ADR, Feature Gate, preflight, or schema. Do **not** implement from this record. Do **not** invent FG-036. Do **not** rescore V1.

```text
BANKED HOURS:
PRODUCT REQUIREMENT RECORDED
POLICY NOT YET FROZEN
IMPLEMENTATION NOT AUTHORIZED
NOT A TRANSIENT RECALCULATION OF ALL HISTORICAL TIME
AUDITABLE LEDGER LIKELY REQUIRED (CREDIT / DEBIT / BALANCE)
TIME REMAINS THE LIKELY UNDERLYING EARNED-HOURS AUTHORITY
FIELD / IPHONE FAST VISIBILITY REQUIRED (MY HOURS)
CONTRACTOR TERM: BANKED HOURS
V1 NOT RESCORED
```

## Contractor observation

Brayman field workers are normally scheduled for **40 hours per week**. Hours above the applicable weekly threshold go into a **Banked Hours** pool for that worker.

A worker must see this **very quickly**, especially on Field / iPhone (**My Hours**):

- hours worked / credited this week
- applicable weekly threshold
- Banked Hours earned this week
- current Banked Hours balance

Recorded Field sketch (not implemented):

```text
This week:
37.5 / 40 hrs

Banked hours:
18.5 hrs
```

After threshold:

```text
This week:
44.0 / 40 hrs

Banked this week:
+4.0 hrs

Banked balance:
22.5 hrs
```

## Authority direction (not frozen)

Do **not** model Banked Hours merely as a transient recalculation of all historical Time.

The product likely requires an **auditable Banked Hours ledger** that can preserve:

- **CREDIT** — Banked Hours earned
- **DEBIT** — Banked Hours used / withdrawn
- a truthful current balance

**TIME** remains the likely underlying earned-hours authority. Exact policy is **NOT FROZEN**. This record does **not** conflict with current TIME authority (`labour_time_entries` / `submit_time()` / approval). Do **not** change TIME from this note.

## Later preflight (not authorized)

A later bounded preflight must determine at minimum:

- submitted vs approved Time as accrual authority
- exact weekly threshold semantics
- week boundary
- statutory holiday treatment
- vacation / paid leave treatment
- overtime / Banked Hours eligibility
- Shop / company work eligibility
- whether different workers can have different thresholds
- Banked Hours withdrawal / use workflow
- who can authorize adjustments / use
- negative-balance policy
- correction / reversal behavior
- historical audit / provenance
- payroll / QuickBooks relationship
- Field visibility
- office visibility

Do **not** invent those policies now.

## Future User Guide / Help

Use **Banked Hours** as the normal contractor/employee term. Do **not** expose ledger/accounting architecture in the User Guide.

Future Help topics:

- How do I see my Banked Hours?
- How are Banked Hours earned?
- How do I use Banked Hours?
- Why did my Banked Hours balance change?

Canonical Help authority remains [interactive-help-voice-and-user-manual-future-record.md](interactive-help-voice-and-user-manual-future-record.md). This record does **not** rewrite the User Guide.

## Sequencing

After SCH-D is stabilized, return to ChatGPT Architect to sequence a bounded Banked Hours preflight against TIME / remaining V1 work, preferably as part of **TIME EXPANSION — COMPANY WORK + COMPLETE PAID TIME + BANKED HOURS** recorded in [company-work-product-direction.md](company-work-product-direction.md). Do **not** begin that preflight from this file.
