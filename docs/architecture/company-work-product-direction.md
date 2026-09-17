# Company Work / Shop — product-direction record

| Attribute | Value |
|-----------|--------|
| Status | **PRODUCT REQUIREMENT RECORDED / POLICY NOT YET FROZEN / IMPLEMENTATION NOT AUTHORIZED** |
| Recorded | 2026-09-16 |
| Authority | Joel Brayman / ChatGPT Architect |
| Does not interrupt | [FG-035](../feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) SCH-D physical iPhone UAT |
| Sibling | [banked-hours-product-direction.md](banked-hours-product-direction.md) |

This is **not** an ADR, Feature Gate, preflight, or schema. Do **not** implement from this record. Do **not** invent FG-036. Do **not** rescore V1. Do **not** create a fake SHOP Project. Do **not** add a `shop_time` boolean. Do **not** begin the later TIME EXPANSION preflight from this file.

```text
COMPANY WORK / SHOP:
PRODUCT REQUIREMENT RECORDED
POLICY NOT YET FROZEN
IMPLEMENTATION NOT AUTHORIZED
NO FAKE SHOP PROJECT
NO SHOP_TIME BOOLEAN
IF WORK IS SPECIFICALLY FOR A CUSTOMER JOB: ENTER THE JOB
IF WORK IS GENERAL COMPANY / SHOP WORK: CHOOSE SHOP
TIME REMAINS LIKELY PAID-TIME AUTHORITY
V1 NOT RESCORED
```

## Contractor observation

Workers often spend paid time that is **not** a customer-job task:

- loading / unloading
- organizing tools
- cleaning tools / equipment
- maintaining equipment
- shop cleanup
- receiving / organizing materials
- other general Shop work

The worker experience should eventually be simple:

**Shop**

with simple work choices.

## Important nuance (not frozen)

**If the work is specifically for a customer job: enter the job.**

**If the work is general company / Shop work: choose Shop.**

Do **not** force general Shop time onto a customer Project merely to have somewhere to send Time.

## Later architecture to investigate (not authorized)

A later bounded preflight may investigate **COMPANY WORK / NON-PROJECT PAID TIME**, possibly reusing intuitive Element / Activity concepts so Shop choices feel like other work without creating a fake customer Project.

Do **not** freeze that model now.

## Later TIME EXPANSION preflight (not authorized)

After SCH-D is stabilized, return to ChatGPT Architect to sequence:

**TIME EXPANSION — COMPANY WORK + COMPLETE PAID TIME + BANKED HOURS**

Expected investigation (not started):

A. Company Work identity
B. Element / Activity reuse
C. Shop as first contractor-facing Company Work choice
D. Project-specific vs general Shop work
E. complete eligible paid-Time picture
F. Banked Hours policy
G. credit/debit ledger
H. Field display
I. office display
J. QuickBooks / payroll
K. future PRICE / PERF / LEARN use
L. Manual Impact

Sibling Banked Hours direction: [banked-hours-product-direction.md](banked-hours-product-direction.md).

## Future User Guide / Help

Use **Shop** as the normal contractor term for general company work. Do **not** teach overlay, non-project paid-time architecture, or `shop_time`.

Future Help topics:

- How do I enter Shop time?
- What if the work was for a customer job, not general Shop work?
- What if Ben sends me to another job?

Canonical Help authority remains [interactive-help-voice-and-user-manual-future-record.md](interactive-help-voice-and-user-manual-future-record.md). This record does **not** rewrite the User Guide.

## Sequencing

Do **not** implement Shop from this file. Do **not** interrupt SCH-D.
