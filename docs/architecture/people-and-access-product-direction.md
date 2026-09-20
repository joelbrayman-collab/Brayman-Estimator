# People & Access — owner product-direction freeze

| Attribute | Value |
|-----------|--------|
| Status | **RECORDED MANDATORY PRODUCT DIRECTION / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED** |
| Date | 2026-09-17 |
| Surface | Future contractor-facing **Settings → People & Access** |
| Owner | Organization subsystem (`User` / `UserMembership` / access-domain grants). Office / platform consumes later administration UI. No new product module in this freeze. |
| ADR | [ADR-041](../adr/ADR-041-user-membership-and-office-authentication.md) **Accepted**. Decision 4 remains the historical FG-018 close record (job-title RBAC rejected; named access domains permitted). **No new ADR.** |
| Parent auth | [FG-018](../feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) **CLOSED / OPERATIONAL FOR UAT**. This freeze does **not** reopen FG-018. |
| Authorization seam | [FG-037](../feature-gates/FG-037-company-management-access-domain-authorization.md) **CLOSED / OPERATIONAL FOR COMPANY_MANAGEMENT AUTHORIZATION**. [company-management-access-domain-seam.md](company-management-access-domain-seam.md) remains the Domain B owner-decision contract. Operator CLI remains bootstrap infrastructure. People & Access is the future contractor-facing administration layer. This freeze does **not** reopen FG-037. |
| Desktop sibling | [v1-desktop-contractor-experience-product-direction.md](v1-desktop-contractor-experience-product-direction.md) **RECORDED / NOT IMPLEMENTED**. Desktop UX law in §30 also informs later Home Office and Company Attention. |
| PERF-C | [fg-035-perf-c-product-definition.md](fg-035-perf-c-product-definition.md) **DEFINED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. Company Attention remains the first recorded product consumer of Domain B. This freeze does **not** expand PERF-C. |
| Schema | **NONE in this freeze.** Do **not** create a migration, Person table, Sys Admin flag, invitation flow, or Sensitive Financial grant from this file. |
| Baseline | HEAD / `origin/main` **`f1940ebe1d80ab0e6e4feb795b7f97402a652bae`**. Live Alembic **`a0b1c2d3e4f5 (head)`**. Live `COMPANY_MANAGEMENT` grant rows **1** (ORG-001 Membership 1 / Joel Brayman). |
| V1 | **NOT RESCORED** (official **65% / 4 of 11**; secondary Functional V1 Build **79% / 22 of 28**). Scorecard reconciliation is separate. |

**Subsequent status (2026-09-20 PA-C bounded live Person UAT):** [testing/fg038-pa-c-person-worker-live-uat.md](../testing/fg038-pa-c-person-worker-live-uat.md) **PASS / LIVE PERSON UAT PASS / 1 INACTIVE SYNTHETIC UAT PERSON RETAINED.** Product SHA **`0698f9d2a4ccabcef53ebcef9cb1415bfcd470f7`**. Person **1** / FG038 PA-C UAT Worker / INACTIVE. This freeze is **not rewritten**. People & Access UI remains **NOT IMPLEMENTED**. PA-D **NOT IMPLEMENTED**. Next **PA-D Platform Access / Person-User linkage**.

**Subsequent status (2026-09-20 PA-C Stage 1 live migration):** [testing/fg038-pa-c-live-migration-empty-person-checkpoint.md](../testing/fg038-pa-c-live-migration-empty-person-checkpoint.md) **PASS / LIVE-MIGRATED / EMPTY-PERSON CHECKPOINT PASS / NO LIVE PERSON DATA.** Product SHA **`0698f9d2a4ccabcef53ebcef9cb1415bfcd470f7`**. Additive **`g7b8c9d0e1f2` applied live**. Live Alembic **`g7b8c9d0e1f2 (head)`**. Live Person rows **0**. This freeze is **not rewritten**. People & Access UI remains **NOT IMPLEMENTED**. PA-D **NOT IMPLEMENTED**. Next **bounded Person UAT decision**, then PA-D.

**Subsequent status (2026-09-20 PA-C SHA pin):** PA-C **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NOT LIVE-MIGRATED / NO LIVE PERSON DATA.** Product SHA **`0698f9d2a4ccabcef53ebcef9cb1415bfcd470f7`**. Additive **`g7b8c9d0e1f2`**. Live Alembic remains **`f6a7b8c9d0e1`**. This freeze is **not rewritten**. People & Access UI remains **NOT IMPLEMENTED**. PA-D **NOT IMPLEMENTED**.

**Subsequent status (2026-09-20 PA-C Person / Worker identity foundation):** PA-C **IMPLEMENTED IN WORKING TREE / TESTED / MIGRATION FILE CREATED / NOT LIVE-MIGRATED / NO LIVE PERSON / NOT COMMITTED / NOT PUSHED.** Additive **`g7b8c9d0e1f2`**. Graph head **`g7b8c9d0e1f2`**. Live Alembic remains **`f6a7b8c9d0e1`**. Person ≠ User. No auto-link. Wage Owner/Sys-Admin protected; **not** Domain C. This freeze is **not rewritten**. People & Access UI remains **NOT IMPLEMENTED**. Next **PA-D Platform Access / Person-User linkage** after PA-C ACCEPT COMMIT / live empty-Person checkpoint / bounded Person UAT.

**Subsequent status (2026-09-20 PA-B Stage 2 first Sys Admin UAT):** [testing/fg038-pa-b-first-system-administrator-authority-uat.md](../testing/fg038-pa-b-first-system-administrator-authority-uat.md) **PASS / LIVE APPOINT UAT PASS / LIVE REMOVE UAT PASS / ZERO CURRENT SYS ADMINS.** Current Sys Admin **0**. APPOINT **1**. REMOVE **1**. Owner **UNCHANGED**. This freeze is **not rewritten**. People & Access UI remains **NOT IMPLEMENTED**. Next product block **PA-C Person / Worker identity**.

**Subsequent status (2026-09-20 PA-B Stage 1 live migration):** [testing/fg038-pa-b-live-migration-zero-sys-admin-checkpoint.md](../testing/fg038-pa-b-live-migration-zero-sys-admin-checkpoint.md) **PASS / LIVE-MIGRATED / ZERO-SYS-ADMIN CHECKPOINT PASS / NO LIVE SYS ADMIN.** Product SHA **`2b25ec99b010c0c66d58d6aa08fdbab55b077e08`**. Additive **`f6a7b8c9d0e1` applied live**. Live Alembic **`f6a7b8c9d0e1 (head)`**. Live Sys Admin **0**. Owner **UNCHANGED**. This freeze is **not rewritten**. People & Access UI remains **NOT IMPLEMENTED**.

**Subsequent status (2026-09-20 PA-B SHA pin):** PA-B **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NOT LIVE-MIGRATED / NO LIVE SYS ADMIN.** Product SHA **`2b25ec99b010c0c66d58d6aa08fdbab55b077e08`**. Additive **`f6a7b8c9d0e1`**. Live Alembic remains **`e5f6a7b8c9d0`**. Live Sys Admin **0**. Owner **UNCHANGED**. This freeze is **not rewritten**. People & Access UI remains **NOT IMPLEMENTED**.

**Subsequent status (2026-09-19 PA-B System Administrator authority foundation):** PA-B **IMPLEMENTED IN WORKING TREE / TESTED / MIGRATION FILE CREATED / NOT LIVE-MIGRATED / NO LIVE SYS ADMIN / NOT COMMITTED / NOT PUSHED.** Additive **`f6a7b8c9d0e1`**. Live Alembic remains **`e5f6a7b8c9d0`**. Live Sys Admin **0**. Owner **UNCHANGED**. This freeze is **not rewritten**. People & Access UI remains **NOT IMPLEMENTED**.

**Subsequent status (2026-09-18 Stage 2 first Owner SET):** [testing/fg038-pa-a-first-instance-owner-authority-uat.md](../testing/fg038-pa-a-first-instance-owner-authority-uat.md) **PASS / FIRST OWNER ASSIGNED / LIVE AUTHORITY UAT PASS.** ORG-001 Owner = Membership **1** / User **1** / Joel Brayman. This freeze is **not rewritten**. People & Access UI and Sys Admin remain **NOT IMPLEMENTED**.

**Subsequent status (2026-09-18 Stage 1 live migration):** [testing/fg038-pa-a-live-migration-ownerless-checkpoint.md](../testing/fg038-pa-a-live-migration-ownerless-checkpoint.md) **PASS / LIVE-MIGRATED.** Subsequent Stage 2 assigned the first Owner. This freeze is **not rewritten**.

**Subsequent status (2026-09-18 live-migration + first-Owner preflight):** [fg-038-pa-a-live-migration-owner-preflight.md](fg-038-pa-a-live-migration-owner-preflight.md) **PREFLIGHT COMPLETE.** Subsequent Stage 1 applied. Live Owner assignment remains **NOT IMPLEMENTED**.

**Subsequent status (2026-09-18 PA-A Instance Owner authority foundation):** [FG-038](../feature-gates/FG-038-instance-owner-authority-foundation.md) **OPEN / PARTIAL / PA-A IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NOT LIVE-MIGRATED / NO OWNER ASSIGNED.** Product SHA **`01e7463082b84b2fcd9d61ff7125a5012b7f8043`**. Additive **`c3d4e5f6a7b8`**. Live Alembic remains **`b2c3d4e5f6a7`**. All organizations remain ownerless. This freeze is **not rewritten**. People & Access UI, Sys Admin, and live Owner assignment remain **NOT IMPLEMENTED**.

**Subsequent status (2026-09-18 CORE CLOSE freeze):** [core-close-project-lifecycle-product-direction.md](core-close-project-lifecycle-product-direction.md) **RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. Close / Reopen is Instance Owner or System Administrator only. This People & Access freeze is **not rewritten**. Do **not** implement People & Access or CORE CLOSE from either file.

This file is the frozen **owner product-direction** contract for People & Access, Contractor Instance Owner, System Administrator, user lifecycle, ordinary A/B/C access, and desktop UX law. It is **not** an implementation prompt. It supersedes all earlier unexecuted People & Access prompt drafts and standalone UX amendments.

Do **not** implement People & Access, Settings Members, invitation, PERF-C, Sensitive Financial, Field changes, or existing-desktop redesign from this file.

```text
PEOPLE & ACCESS:
RECORDED MANDATORY PRODUCT DIRECTION
NOT IMPLEMENTATION-AUTHORIZED
NOT IMPLEMENTED
NO SCHEMA
NO MIGRATION
NO NEW ADR
NO NEW FEATURE GATE
NO UI
V1 NOT RESCORED

CONTRACTOR INSTANCE OWNER:
RECORDED PROTECTED ROOT AUTHORITY
PRODUCT LANGUAGE: INSTANCE OWNER (NOT PLATFORM OWNER)

SYSTEM ADMINISTRATOR:
RECORDED OWNER-DESIGNATED BROAD/FULL ADMINISTRATIVE USER
NOT IMPLEMENTED
APPOINTMENT: INSTANCE OWNER ONLY
REMOVAL: INSTANCE OWNER MAY REMOVE ANY SYS ADMIN
SYS ADMIN MAY REMOVE ANOTHER SYS ADMIN
SYS ADMIN MAY NEVER IMPAIR INSTANCE OWNER

DELETE USER:
RECORDED CONTRACTOR-FACING ACCESS-REMOVAL REQUIREMENT
DELETE USER = REMOVE ACCESS, NOT REMOVE HISTORY
NOT IMPLEMENTED

SENSITIVE FINANCIAL:
RECORDED FUTURE ACCESS DOMAIN
NOT IMPLEMENTED

FG-037: UNCHANGED / CLOSED
PERF-C: UNCHANGED / DEFINED / NOT IMPLEMENTATION-AUTHORIZED

DESKTOP UX:
USE AVAILABLE SPACE GENEROUSLY, NOT DENSELY
DESKTOP SHOULD FEEL AS CLEAN AND LEGIBLE AS FIELD / IPHONE
WHILE USING THE ADDITIONAL DESKTOP REAL ESTATE INTELLIGENTLY
```

---

## 1. Current vs Intended vs Future

| Layer | State |
|-------|--------|
| **Current** | Durable `User` / `UserMembership` ([FG-018](../feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md)). Domain A = active membership. Domain B = explicit `COMPANY_MANAGEMENT` grant ([FG-037](../feature-gates/FG-037-company-management-access-domain-authorization.md) **CLOSED**). Live B grant: Joel Membership 1 only. Operator CLI is bootstrap infrastructure. Settings is Brand Profile. No People & Access UI. No Instance Owner / Sys Admin product. No Person-vs-User administration. Sensitive Financial **not implemented**. |
| **Intended (this freeze)** | Owner decisions in §§3–30 **ACCEPTED** as product direction. Settings → People & Access is **mandatory** before independent contractor/team operation. **Not implementation-authorized.** |
| **Future (not this freeze)** | Bounded implementation (separate Feature Gate / prompt, including migration approval if schema is chosen). Invitation/authentication workflow. Compensation visibility design. Ownership transfer/recovery. PERF-C Company Attention. Sensitive Financial. Home Office. |

---

## 2. Contractor Instance Owner

Each contractor CalibraytAI organization has a **Contractor Instance Owner**.

Use **Instance Owner** in product language, not **Platform Owner**, so contractor ownership is not confused with ownership or operation of CalibraytAI itself.

The Instance Owner is the **protected root authority** for that contractor’s instance and ultimately controls:

- people
- workforce participation
- platform access
- ordinary-user permissions
- Company / Management permissions
- future Sensitive Financial permissions
- System Administrator appointment
- System Administrator removal
- future ownership transfer/recovery as separately governed

---

## 3. System Administrator

The Instance Owner may designate one or more trusted **System Administrators**.

A System Administrator is a **broad/full-access administrative user**.

If a person should have limited access, that person should normally remain an **ordinary user** with granular access permissions rather than being made a System Administrator.

Do **not** design a large matrix of Sys Admin sub-permissions merely for its own sake.

System Administrator remains **distinct** from Instance Owner.

---

## 4. System Administrator appointment

**Only the Contractor Instance Owner** may appoint a System Administrator.

A System Administrator **cannot** appoint another System Administrator.

Do **not** infer Sys Admin from job title, name, email, creation order, Company / Management permission, employment status, or bootstrap history.

Sys Admin designation is an **explicit Instance Owner decision**.

---

## 5. System Administrator warning

Designating a System Administrator must eventually produce an obvious high-sensitivity warning: the person receives broad administrative access and may have access to sensitive company, employee, compensation, and financial information.

The Instance Owner confirms or cancels.

```text
WARNINGS INFORM.
HUMANS DECIDE.
```

Do **not** implement warning UX from this file.

---

## 6. System Administrator removal

- The Instance Owner may remove **any** System Administrator.
- A System Administrator may remove **another** System Administrator.
- A System Administrator may remove **their own** Sys Admin access if future lifecycle product supports self-removal.

A System Administrator may **never**:

- delete, deactivate, demote, or replace the Instance Owner
- transfer Instance ownership
- remove the Instance Owner’s root authority
- otherwise impair the Instance Owner’s protected ownership authority

The Instance Owner remains protected root authority.

---

## 7. Instance Owner self-removal / ownership transfer

Do **not** treat sole Instance Owner self-deletion as ordinary Delete User.

The sole Contractor Instance Owner must **not** be able to accidentally leave the contractor instance without a root authority.

Ownership transfer, replacement, recovery, and any eventual Instance Owner self-removal require **separately governed** lifecycle rules. Do **not** design those rules here.

---

## 8. Mandatory Person information

Every Person requires **all five**:

- Full name
- Address
- Mobile number
- Email address
- Hourly wage

Email is **not** optional. Hourly wage is **not** optional. This is the minimum contractor workforce/person record.

---

## 9. Person / Worker vs Platform User

**Person / Worker** and **Platform User** are distinct.

A Person may exist for workforce identity, labour costing, Schedule, Time, work assignment, and other governed operational purposes **without** authenticated CalibraytAI access.

Creating a Person does **not** automatically create authenticated access or grant Domain A, B, or C.

Platform access is a **separate explicit administrative decision**.

---

## 10. Platform access

The Instance Owner or System Administrator may eventually enable or disable ordinary-user platform access through People & Access.

The mandatory email address is part of governed Person identity and may support a separately governed authentication/invitation workflow.

Do **not** design or implement invitation mechanics here.

---

## 11. Ordinary user access model

Preserve conceptual access domains:

| Domain | Key | How authority is established | Status |
|--------|-----|------------------------------|--------|
| **A. PROJECT / OPERATIONAL** | *(not stored)* | Active membership / governed ordinary operational access | **Current** |
| **B. COMPANY / MANAGEMENT** | `COMPANY_MANAGEMENT` | Explicit membership grant | **Operational (FG-037)**; People & Access will later administer ordinary-user grants |
| **C. SENSITIVE FINANCIAL** | *(future)* | Later explicit grant | **FUTURE / NOT IMPLEMENTED** |

```text
A DOES NOT IMPLY B.
B DOES NOT IMPLY C.
```

Ordinary users receive only the access explicitly governed for them. Do **not** replace this with job-title RBAC.

System Administrator is conceptually different from ordinary A/B/C grants. Instance Owner remains distinct from System Administrator and retains protected root authority. Do **not** over-engineer granular Sys Admin visibility restrictions at this product-direction stage.

---

## 12. Project / Operational

Domain A covers normal governed operational access such as Projects, Project work, Schedule, Time, Field, and ordinary operational Project information.

Exact future Project-specific scoping remains separately governed. Do **not** invent per-Project ACL architecture here.

---

## 13. Company / Management

Domain B remains a distinct explicit access domain. Company Attention / PERF-C is the first recorded product consumer.

Ordinary Project / Operational access does **not** automatically grant Company / Management access.

The Instance Owner or System Administrator may eventually administer ordinary-user Company / Management grants through People & Access. Do **not** implement that administration here.

---

## 14. Sensitive Financial

Domain C remains a separate future access domain. It may eventually protect bank information, balances, cash position, company cash flow, payroll-sensitive information, compensation, and other sensitive company financial/business information.

Sensitive Financial is **NOT IMPLEMENTED**. Do **not** create schema, grants, or placeholder live permission rows from this file.

---

## 15. Hourly wage is sensitive

Hourly wage is **mandatory Person information** **and** **sensitive information**.

Ordinary Project / Operational access does **not** automatically authorize a user to view another person’s hourly wage.

CalibraytAI may use hourly wage internally for governed labour-cost calculations without exposing the wage to users who lack the required sensitive-information authority.

Example: a supervisor may be permitted to see “Worker worked 8 hours” without being permitted to see “Worker earns $X/hour.”

Exact compensation visibility/edit authority remains future governed implementation design.

---

## 16. Access warnings

Future People & Access must warn before elevated ordinary-user access is granted.

| Elevation | Warning strength | Meaning |
|-----------|------------------|---------|
| Company / Management | Clear | Recipient will receive company-level management access beyond ordinary Project / Operational access |
| Sensitive Financial | Stronger | Recipient may receive access to confidential financial and compensation information |
| System Administrator | Strongest | Recipient receives broad/full administrative authority and access |

```text
WARNINGS INFORM.
HUMANS DECIDE.
```

---

## 17. People & Access lifecycle

Future **Settings → People & Access** must provide obvious contractor-facing controls for:

- Add Person
- Edit Person
- Activate Person
- Deactivate Person
- enable platform access
- disable platform access
- grant ordinary-user access
- revoke ordinary-user access
- designate System Administrator
- remove System Administrator designation
- Delete User

Do **not** implement these controls here.

---

## 18. Delete User

**DELETE USER** must be an obvious contractor-facing People & Access action.

The product may say **Delete User**. The governing meaning is:

```text
DELETE USER = REMOVE ACCESS, NOT REMOVE HISTORY.
```

Not: destroy historical data.

### Authority

The Contractor Instance Owner may Delete User for ordinary users and System Administrators.

A System Administrator may Delete User for ordinary users, another System Administrator, and themselves where future lifecycle supports self-removal.

A System Administrator may **never** Delete User / deactivate / demote / replace / impair the Contractor Instance Owner.

### Semantics

Expected future Delete User semantics:

- revoke/disable platform access
- remove the person from active workforce participation
- prevent future active access
- prevent future active work assignment as governed
- remove active administrative authority where applicable
- preserve historical identity
- preserve historical business records
- preserve auditability

Delete User must **not** silently hard-delete history.

### Historical preservation

Historical attribution must remain intact after access removal, including where applicable: Time records, Project work history, Schedule history, approvals, Change Orders, signatures, executed artifacts, audit events, historical costing attribution, and other governed historical actions.

Removing access must not rewrite history to make it appear that someone else performed those actions. Do not orphan historical records.

### Confirmation

Future Delete User requires explicit confirmation: CalibraytAI access will be removed; the person will no longer participate in active work; historical Project / Time / approval / audit records will remain. For a System Administrator, also explain that System Administrator authority will be removed.

```text
WARNINGS INFORM.
HUMANS DECIDE.
```

### Deactivate vs Delete User vs Delete Data

| Action | Meaning |
|--------|---------|
| **Deactivate** | Temporarily/inactively remove the person from current participation while preserving the Person/account relationship as governed |
| **Delete User** | Remove platform access and active participation going forward while preserving historical identity/data |
| **Delete Data** | Fundamentally different. **Not** implied by Delete User |

Do **not** define broad Delete Data functionality here.

---

## 19. Initial Brayman access policy

| Person / class | Instance Owner | A | B | C | System Administrator |
|----------------|----------------|---|---|---|----------------------|
| **Joel Brayman** | **YES** | **YES** | **YES** (current live `COMPANY_MANAGEMENT` grant) | **YES when implemented** | *(Instance Owner; not a Sys Admin designation)* |
| **Ben Brayman** | no | **YES** when a genuine governed membership exists | **YES** when that membership exists and is later explicitly granted | **YES when implemented** | **NOT YET DECIDED** |
| **Other users initially** | no | as appropriate | **NO** unless explicitly granted | **NO** unless explicitly granted | only if explicitly designated by Instance Owner |

Ben still requires a genuine governed ORG-001 user/membership before his Company / Management grant. Do **not** infer, rename, or grant via synthetic users from this file.

A does not imply B. B does not imply C. Joel and Ben both receiving B and future C is **owner access policy**, not architectural coupling.

---

## 20. FG-037 and PERF-C boundaries

[FG-037](../feature-gates/FG-037-company-management-access-domain-authorization.md) is **CLOSED / OPERATIONAL FOR COMPANY_MANAGEMENT AUTHORIZATION**. Do **not** reopen it. Do **not** add People & Access product functionality to it.

The existing Domain B seam and current live Joel grant remain current authority. The governed operator CLI remains bootstrap infrastructure. People & Access is the future contractor-facing administration layer.

[PERF-C](fg-035-perf-c-product-definition.md) remains **DEFINED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. Do **not** implement Company Attention. Do **not** expand PERF-C through this freeze.

---

## 21. V1 direction / scorecard

People & Access is **mandatory product direction** before independent contractor/team operation of CalibraytAI.

It is the future contractor-facing administration layer for workforce/person identity, platform access, ordinary-user permissions, System Administrator designation/removal, and user lifecycle/access removal.

Do **not** automatically change Governed V1 Readiness **65%** or Functional V1 Build **79% / 22 of 28**. Scorecard reconciliation remains separate.

---

## 22. Desktop / People & Access UX law

CalibraytAI desktop should inherit the clean, legible, uncluttered look and feel of the approved Field / iPhone experience.

**Design objective:** maximize useful desktop real estate without sacrificing legibility, whitespace, visual calm, obvious hierarchy, or ease of use.

```text
USE AVAILABLE SPACE GENEROUSLY, NOT DENSELY.

DESKTOP SHOULD FEEL AS CLEAN AND LEGIBLE AS FIELD / IPHONE
WHILE USING THE ADDITIONAL DESKTOP REAL ESTATE INTELLIGENTLY.
```

Desktop must **not**:

- artificially constrain itself to a narrow mobile-width column
- waste large amounts of useful screen space merely to mimic mobile
- shrink typography to fit more information
- crowd controls together
- become a dense enterprise administration interface
- fill available space with unnecessary cards, widgets, badges, borders, or controls

Desktop **may** use more horizontal space than Field where that aids comprehension. Desktop may show more useful context than mobile. Desktop must **not** feel busier merely because more screen space exists.

Use an **adaptive** layout rather than one fixed column count.

On sufficiently wide desktop surfaces:

- two-column form arrangements are appropriate where fields naturally pair
- inputs must remain large and comfortably spaced
- important or long fields may span the full available form width
- related information should remain visually grouped

Avoid three- or four-column dense form grids for ordinary contractor input.

As viewport width decreases: preserve comfortable control sizes; collapse paired fields progressively; use a clean single-column layout on narrow/mobile surfaces. Never reduce legibility merely to preserve multi-column layout.

### People & Access composition (directional)

Mandatory Person fields: Full Name, Address, Mobile Number, Email Address, Hourly Wage.

A likely desktop composition may pair, where appropriate:

```text
Full Name        | Email Address
Mobile Number    | Hourly Wage
Address          (full available form width)
```

This is **directional**, not a rigid implementation specification. Final implementation should use the cleanest responsive composition supported by the actual design system.

Add Person / Edit Person must **not** resemble a dense traditional administration form. Inputs must be large, clearly labelled, and comfortably spaced.

Visual separation, in this order:

1. PERSON / IDENTITY
2. ACCESS
3. SYSTEM ADMINISTRATOR / SENSITIVE AUTHORITY
4. DELETE USER / ACCESS REMOVAL

Do not crowd permissions beside routine Person identity fields. System Administrator designation must be visually prominent and separate because it carries broad authority.

Sensitive-access warnings must be prominent, highly legible, clearly separated from ordinary helper text, and difficult to mistake or overlook.

Primary actions remain simple and obvious, conceptually:

- Cancel
- Save Person

DELETE USER / access-removal controls must be visually separated from routine Save/Edit actions to reduce accidental activation.

Use large legible typography, generous whitespace, large comfortable inputs, clear labels, obvious primary actions, plain contractor language, progressive disclosure, responsive layouts, and restrained visual chrome.

This principle should inform later People & Access, Company Attention, Home Office, and other contractor-facing desktop surfaces.

Do **not** redesign existing desktop surfaces from this file. Do **not** implement UI from this file.

---

## 23. Firewalls

Do **not** from this file:

- implement People & Access, Settings Members, invitation, or Sys Admin product
- edit application code, models, routes, templates, services, or tests
- create migrations or mutate the database
- create users, memberships, or grants
- reopen FG-037 or FG-018
- implement PERF-C / Company Attention / Field Company Attention
- implement Sensitive Financial
- redesign existing desktop surfaces
- rescore V1

---

## Related

- [company-management-access-domain-seam.md](company-management-access-domain-seam.md)
- [FG-037-company-management-access-domain-authorization.md](../feature-gates/FG-037-company-management-access-domain-authorization.md)
- [FG-018-organization-authentication-actor-identity-and-membership-v1.md](../feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md)
- [ADR-041-user-membership-and-office-authentication.md](../adr/ADR-041-user-membership-and-office-authentication.md)
- [fg-035-perf-c-product-definition.md](fg-035-perf-c-product-definition.md)
- [v1-desktop-contractor-experience-product-direction.md](v1-desktop-contractor-experience-product-direction.md)
- [project-element-authority-future-record.md](project-element-authority-future-record.md) (platform-wide warning law)
