# Milestone History — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Authoritative historical record |
| Updated | 2026-09-20 |
| Policy | **Append-only** |

## Purpose

Record completed and in-progress platform milestones so progress is recoverable without chat history.

## Numbering convention

- Format: `Milestone NNN` with zero-padded integers (`001`, `002`, …)
- Title: short human name
- Separate **planned** milestones (roadmap) from **recorded** entries here
- Architecture reconciliations use **CAR-NNN** and are **not** milestone numbers. Do not reuse M009 for CAR-001.

## Required fields (each entry)

Milestone · Status · Branch · Base commit · Objective · Deliverables · Validation · Architectural findings · Open decisions · Next milestone · Commit · Date

## Rules

1. Entries are **append-only** (newest first under Completed / Recorded).
2. Completed entries are **not rewritten** except to correct factual errors (note the correction).
3. Distinguish **Planned** (may live primarily on the roadmap) from **Completed / Recorded** here.
4. “Completed pending baseline commit” means deliverables exist in the working tree awaiting Joel-approved commit.

---

## Entries

### 2026-09-20 — FG-038 PA-C bounded live Person UAT

| Field | Content |
|-------|---------|
| Milestone | FG-038 PA-C bounded live Person UAT |
| Status | **LIVE PERSON UAT PASS / 1 INACTIVE SYNTHETIC UAT PERSON RETAINED.** Product SHA **`0698f9d2a4ccabcef53ebcef9cb1415bfcd470f7`**. Pin SHA **`bc0ce7f541728262df0573a6096b5948d7abe6ed`**. Live Alembic **`g7b8c9d0e1f2 (head)`**. Person **1** / FG038 PA-C UAT Worker / INACTIVE. Instance Owner **UNCHANGED**. Sys Admin current **0**. People UI **NOT IMPLEMENTED**. Official V1 **not rescored**. |
| Branch | `main` |
| Base commit | Stage 1 governance **`433c46f2ae08dfe5513ee2ad86ad72347b8c47e3`** |
| Objective | Prove live Person authority: create, identity read, protected wage, update, deactivate, reactivate, final deactivate. |
| Deliverables | One synthetic Person via governed CLI; [testing/fg038-pa-c-person-worker-live-uat.md](testing/fg038-pa-c-person-worker-live-uat.md); bounded live occupancy test update. |
| Validation | Dedicated PA-C **37 passed**. PA-B **38**. PA-A **35**. Focused identity **192 passed**, 563 warnings, **107.20s**, exit **0**. Full suite **1514 passed**, 5163 warnings, **691.64s**, exit **0**. |
| Architectural findings | Creating Person created no User, Membership, login, A/B/C, Owner, or Sys Admin. Wage omitted from PersonIdentity. Owner wage ALLOW 37.50. Ordinary AUTH-B User 6 DENY. No safe live B-only non-Owner identity without creating a grant. Historical User FKs unchanged. |
| Open decisions | Architect PA-D Platform Access / Person-User linkage. |
| Next milestone | **PA-D Platform Access / Person-User linkage.** |
| Commit | this UAT governance commit follows |
| Date | 2026-09-20 |

### 2026-09-20 — FG-038 PA-C Stage 1 live migration / empty-Person checkpoint

| Field | Content |
|-------|---------|
| Milestone | FG-038 PA-C Stage 1 live migration |
| Status | **LIVE-MIGRATED / EMPTY-PERSON CHECKPOINT PASS / NO LIVE PERSON DATA.** Product SHA **`0698f9d2a4ccabcef53ebcef9cb1415bfcd470f7`**. Pin SHA **`bc0ce7f541728262df0573a6096b5948d7abe6ed`**. Live Alembic **`g7b8c9d0e1f2 (head)`**. Live Person rows **0**. Instance Owner **LIVE / OPERATIONAL / UNCHANGED**. Sys Admin current **0**. APPOINT **1**. REMOVE **1**. People UI **NOT IMPLEMENTED**. Official V1 **not rescored**. |
| Branch | `main` |
| Base commit | PA-C pin **`bc0ce7f541728262df0573a6096b5948d7abe6ed`** |
| Objective | Apply additive Person schema live and prove an empty Person baseline before any live Person creation. |
| Deliverables | Live `organization_people`; empty-Person checkpoint; [testing/fg038-pa-c-live-migration-empty-person-checkpoint.md](testing/fg038-pa-c-live-migration-empty-person-checkpoint.md); bounded live empty-Person test assertion. |
| Validation | Dedicated PA-C **37 passed**, 101 warnings, **16.66s**, exit **0**. Focused identity **192 passed**, 563 warnings, **103.59s**, exit **0**. Full suite **1514 passed**, 5163 warnings, **680.24s**, exit **0**. Live Person rows **0**. |
| Architectural findings | Creating the table does not create a Person, User, Membership, A/B/C, Owner, or Sys Admin. Historical User FKs unchanged. |
| Open decisions | Architect bounded Person UAT decision. Then PA-D. Then People UI. |
| Next milestone | **Architect bounded Person UAT decision.** |
| Commit | this Stage 1 governance commit follows |
| Date | 2026-09-20 |

### 2026-09-20 — FG-038 PA-C SHA pin

| Field | Content |
|-------|---------|
| Milestone | FG-038 PA-C pin |
| Status | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NOT LIVE-MIGRATED / NO LIVE PERSON DATA.** Product SHA **`0698f9d2a4ccabcef53ebcef9cb1415bfcd470f7`**. Additive **`g7b8c9d0e1f2`**. Graph head **`g7b8c9d0e1f2`**. Live Alembic remains **`f6a7b8c9d0e1`**. Instance Owner **LIVE / OPERATIONAL / UNCHANGED**. Sys Admin current **0**. People UI **NOT IMPLEMENTED**. Official V1 **not rescored**. |
| Branch | `main` |
| Base commit | PA-C product **`0698f9d2a4ccabcef53ebcef9cb1415bfcd470f7`** |
| Objective | Pin the accepted PA-C Person / Worker product SHA before Stage 1 live migration. |
| Deliverables | Governance SHA pointers only. |
| Validation | Reused accepted PA-C evidence. No product change. |
| Architectural findings | No product change. |
| Open decisions | Stage 1 live migrate (this prompt). Bounded Person UAT. PA-D. People & Access UI. |
| Next milestone | **Stage 1 live migration / empty-Person checkpoint.** |
| Commit | this pin commit follows |
| Date | 2026-09-20 |

### 2026-09-20 — FG-038 PA-C Person / Worker identity foundation

| Field | Content |
|-------|---------|
| Milestone | FG-038 PA-C — Person / Worker identity foundation |
| Status | **IMPLEMENTED IN WORKING TREE / TESTED / MIGRATION FILE CREATED / NOT LIVE-MIGRATED / NO LIVE PERSON / NOT COMMITTED / NOT PUSHED.** Additive **`g7b8c9d0e1f2`**. Graph head **`g7b8c9d0e1f2`**. Live Alembic remains **`f6a7b8c9d0e1`**. Instance Owner **LIVE / OPERATIONAL / UNCHANGED**. Sys Admin current **0**. People UI **NOT IMPLEMENTED**. Official V1 **not rescored**. |
| Branch | `main` |
| Base commit | Stage 2 UAT governance **`6ad1410db5dbbccb6a4728b7c7b7ae442b935227`** |
| Objective | Additive Person / Worker identity distinct from User, without login, membership, A/B/C, Owner, or Sys Admin, and without retargeting Time/Crew/Field FKs. |
| Deliverables | `organization_people`; `OrganizationPerson`; `app/services/organization_people.py`; protected wage-read seam; bounded CLI; dedicated tests; additive **`g7b8c9d0e1f2`** file only. |
| Validation | Dedicated PA-C **37 passed**. Focused PA-C/PA-B/PA-A/Close/Reopen/FG-018/FG-037 **192 passed**, 563 warnings, **107.11s**, exit **0**. Full suite **1514 passed**, 5163 warnings, **723.80s**, exit **0**. Live Person table **absent**. Live Sys Admin **0**. |
| Architectural findings | Person ≠ User. No Person↔User FK. Matching email does not auto-link. Wage is mandatory Numeric(10,2) compensation data readable only by effective Owner or Sys Admin. Not Domain C. Historical User FKs unchanged. |
| Open decisions | Architect ACCEPT COMMIT / PUSH / SHA-PIN. Then live empty-Person checkpoint. Then bounded Person UAT. Then PA-D. |
| Next milestone | **Architect ACCEPT COMMIT / PUSH / SHA-PIN PA-C.** |
| Commit | working tree only; this implementation is not committed |
| Date | 2026-09-20 |

### 2026-09-20 — FG-038 PA-B Stage 2 first System Administrator authority UAT

| Field | Content |
|-------|---------|
| Milestone | FG-038 PA-B Stage 2 first Sys Admin UAT |
| Status | **LIVE APPOINT UAT PASS / LIVE REMOVE UAT PASS / ZERO CURRENT SYS ADMINS.** Product SHA **`2b25ec99b010c0c66d58d6aa08fdbab55b077e08`**. Pin SHA **`3a4735b40ee4580ad3ae419569cafb7bdec32352`**. Stage 1 governance SHA **`162bcb60d09bb32bd231ed0753c020e5c0720a81`**. Live Alembic **`f6a7b8c9d0e1 (head)`**. System Administrator foundation **LIVE / OPERATIONAL**. Current Sys Admin **0**. APPOINT **1**. REMOVE **1**. Instance Owner **LIVE / OPERATIONAL / UNCHANGED**. People UI **NOT IMPLEMENTED**. Official V1 **not rescored**. |
| Branch | `main` |
| Base commit | Stage 1 governance **`162bcb60d09bb32bd231ed0753c020e5c0720a81`** |
| Objective | Appoint Membership **5** / User **6** / AUTH-B UAT User as temporary Sys Admin by Owner User **1**, prove authority, then remove, leaving current **0** and permanent APPOINT/REMOVE history. |
| Deliverables | Bounded live CLI appoint/remove; helper proofs; docs-only UAT evidence [testing/fg038-pa-b-first-system-administrator-authority-uat.md](testing/fg038-pa-b-first-system-administrator-authority-uat.md). |
| Validation | Dedicated PA-B **38**, PA-A **35**, Close/Reopen **22**, FG-018 **37**, FG-037 **23** — focused **155 passed**, 462 warnings, **88.17s**, exit **0**. Full suite **not run** (no product/code change). Final live current Sys Admin **0**. APPOINT **1**. REMOVE **1**. |
| Architectural findings | AUTH-B is a UAT display name, not Domain B. Membership **5** received no B/C grant. Owner pointer unchanged. Same-current appoint is a governed no-op (exit **0**, no extra event). Sys Admin cannot appoint. Sys Admin cannot impair Owner. Close/Reopen helper authorized Membership **5** while appointed and not after remove. No live Close/Reopen. Person ≠ User remains unsolved. |
| Open decisions | Architect: PA-C Person / Worker identity foundation. |
| Next milestone | **PA-C Person / Worker identity foundation.** |
| Commit | this Stage 2 UAT governance commit follows |
| Date | 2026-09-20 |

### 2026-09-20 — FG-038 PA-B Stage 1 live migration / zero-Sys-Admin checkpoint

| Field | Content |
|-------|---------|
| Milestone | FG-038 PA-B Stage 1 live migration |
| Status | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE-MIGRATED / ZERO-SYS-ADMIN CHECKPOINT PASS / NO LIVE SYS ADMIN.** Product SHA **`2b25ec99b010c0c66d58d6aa08fdbab55b077e08`**. Pin SHA **`3a4735b40ee4580ad3ae419569cafb7bdec32352`**. Additive **`f6a7b8c9d0e1` applied live**. Live Alembic **`f6a7b8c9d0e1 (head)`**. System Administrator foundation **LIVE / OPERATIONAL / NO ADMIN APPOINTED**. Instance Owner **LIVE / OPERATIONAL / UNCHANGED**. People UI **NOT IMPLEMENTED**. Official V1 **not rescored**. |
| Branch | `main` |
| Base commit | PA-B pin **`3a4735b40ee4580ad3ae419569cafb7bdec32352`** |
| Objective | Apply additive `f6a7b8c9d0e1` live and prove zero Sys Admins, with Owner and A/B/C occupancy unchanged. |
| Deliverables | Timestamped SQLite backup; live upgrade; zero-Sys-Admin checkpoint; read-only helper proof; Stage 1 governance record. |
| Validation | Dedicated PA-B **38 passed**, 108 warnings, **29.18s**. Authority/CORE CLOSE bundle **210 passed**, 605 warnings, **159.36s**. Help+C1/C2 **95 passed**, 208 warnings, **176.07s**. Full suite **1477 passed**, 5062 warnings, **969.59s**, exit **0**. Live Sys Admin **0**. APPOINT **0**. REMOVE **0**. |
| Architectural findings | Migration created empty authority tables. Owner was not auto-converted. B did not become Sys Admin. Combined helper remains true for Joel because he is Instance Owner. |
| Open decisions | Architect: bounded first Sys Admin UAT **or** People & Access UI. |
| Next milestone | **Architect decision — bounded first Sys Admin authority UAT or proceed directly to People & Access.** |
| Commit | this Stage 1 governance commit follows |
| Date | 2026-09-20 |

### 2026-09-20 — FG-038 PA-B SHA pin

| Field | Content |
|-------|---------|
| Milestone | FG-038 PA-B pin |
| Status | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NOT LIVE-MIGRATED / NO LIVE SYS ADMIN.** Product SHA **`2b25ec99b010c0c66d58d6aa08fdbab55b077e08`**. Instance Owner **LIVE / OPERATIONAL / UNCHANGED**. People UI **NOT IMPLEMENTED**. Official V1 **not rescored**. |
| Branch | `main` |
| Base commit | PA-B product **`2b25ec99b010c0c66d58d6aa08fdbab55b077e08`** |
| Objective | Pin the accepted PA-B System Administrator product SHA before Stage 1 live migration. |
| Deliverables | Governance SHA pointers only. |
| Validation | Reused accepted PA-B evidence. No product change. |
| Architectural findings | No product change. |
| Open decisions | Stage 1 live migrate (this prompt). First Sys Admin UAT. People & Access UI. |
| Next milestone | **Stage 1 live migration / zero-Sys-Admin checkpoint.** |
| Commit | this pin commit follows |
| Date | 2026-09-20 |

### 2026-09-19 — FG-038 PA-B System Administrator authority foundation

| Field | Content |
|-------|---------|
| Milestone | FG-038 PA-B — System Administrator authority foundation |
| Status | **IMPLEMENTED IN WORKING TREE / TESTED / MIGRATION FILE CREATED / NOT LIVE-MIGRATED / NO LIVE SYS ADMIN / NOT COMMITTED / NOT PUSHED.** Instance Owner **LIVE / OPERATIONAL / UNCHANGED**. People & Access **PARTIAL / NOT OPERATIONAL**. People UI **NOT IMPLEMENTED**. Official V1 **not rescored**. |
| Branch | `main` |
| Base commit | D5 pin **`c670dc2e35178ad18f02f53683098ee330c4dd7b`** |
| Objective | Persist explicit org-scoped System Administrator authority distinct from Instance Owner and from A/B/C, with append-only APPOINT/REMOVE history, without live mutation or People UI. |
| Deliverables | Current Sys Admin membership rows; APPOINT/REMOVE events; `is_system_administrator`; appoint/remove services; Owner protection; bounded CLI; dedicated tests A–AF; additive **`f6a7b8c9d0e1`** file only. |
| Validation | Dedicated PA-B **38 passed**, 108 warnings, **26.16s**. PA-A **35**. FG-037 **23**. FG-018 **37**. Close/Reopen **22**. Slice A **18**. Slice B **37**. Help D1/D3/D4/D5 **35**. C1 **26**. C2 **34**. Full suite **1477 passed**, 5062 warnings, **676.28s**, exit **0**. Live Alembic **`e5f6a7b8c9d0`**. Graph head **`f6a7b8c9d0e1`**. Live Sys Admin **0**. |
| Architectural findings | Sys Admin is not Domain B. Owner-only appoint. Owner/Sys Admin remove. Self-removal allowed. Owner cannot be appointed or impaired. Same-state appoint/remove does not duplicate events. Existing Close/Reopen helper now authorizes effective Sys Admin in TEST DB. No new ADR. |
| Open decisions | Architect ACCEPT COMMIT PA-B. Live migrate. First Sys Admin UAT. People & Access UI. |
| Next milestone | **Architect ACCEPT COMMIT / PUSH / SHA-PIN PA-B**, then live migration / ownerless-Sys-Admin checkpoint if separately authorized. |
| Commit | **NOT COMMITTED** |
| Date | 2026-09-19 |

### 2026-09-19 — D5 Voice with Help

| Field | Content |
|-------|---------|
| Milestone | D5 — Voice with Help |
| Status | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / NO MIGRATION / NO DB MUTATION.** Voice is an interface to the existing Help authority. Voice actions **NOT IMPLEMENTED / NOT V1**. User Guide remains outstanding. LEARN remains Future. Official V1 **not rescored**. Completion Sign-Off **NOT IMPLEMENTED**. |
| Branch | `main` |
| Base commit | `adcc78a0d15ee17971878c848038e035b12b9fca` (`docs: pin D4 Field Help SHA`) |
| Objective | Let a contractor ask the current contextual Help by typing or speaking, without a second knowledge base or an action engine. |
| Deliverables | Shared `answer_help_question()`; `POST /help/ask`; one Help question box + Ask by speaking inside contextual Help; optional Speak answer; dedicated D5 tests |
| Validation | Dedicated D5 **9 passed**, 9 warnings, **2.91s**. D1 **9 passed**. D3 **8 passed**. D4 **9 passed**. D2 **6 passed**. Combined Help **41 passed**, 94 warnings, **19.71s**. Focused **246 passed**, 743 warnings, **148.85s**. Full suite **1439 passed**, 4954 warnings, **650.95s**, exit **0**. Live text Help smoke **PASS** on **5462**. Voice browser smoke **UNAVAILABLE**. |
| Architectural findings | One Help authority. Browser Web Speech only. No provider. Bounded intent matching, not open-ended AI. Field cannot retrieve Company Attention. `/help/ask` does not mutate. No schema. |
| Open decisions | People & Access PA-B. Whole-product UAT. Completion Sign-Off after UAT. |
| Next milestone | **FG-038 PA-B — System Administrator authority foundation.** |
| Commit | `021a893104260baa543e1f791b24d671562f40dd` (`feat: add Voice to contextual Help`) |
| Date | 2026-09-19 |

### 2026-09-19 — D4 Field Help

| Field | Content |
|-------|---------|
| Milestone | D4 — Field Help |
| Status | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / LIVE FIELD HELP SMOKE PASS / NO MIGRATION / NO DB MUTATION.** Presentation only. Same Help authority as D1/D3. Contextual Help coverage complete for Hub / Office / Field. Voice and User Guide remain outstanding. LEARN remains Future. Official V1 **not rescored**. Completion Sign-Off **NOT IMPLEMENTED**. |
| Branch | `main` |
| Base commit | `1ab6cf09328e84915b306dd91a601dd4eb5a0c71` (`docs: pin D3 Office Help SHA`) |
| Objective | Extend the existing D1/D3 Help authority to high-value contractor-facing Field/iPhone surfaces. Voice-ready `help_payload()` unchanged. |
| Deliverables | Field topics in `help_content.py`; native `<details>` Help on Today, This week, This month, Company today, Projects, Capture, Time, My time, Extra work; Field-native CSS; dedicated D4 tests |
| Validation | Dedicated D4 **9 passed**, 35 warnings, **5.11s**. D1 **9 passed**. D3 **8 passed**. D2 **6 passed**. Focused Help/Field **281 passed**, 884 warnings, **148.96s**. Full suite **1430 passed**, 4945 warnings, **698.92s**, exit **0**. Live Field GET Help smoke **PASS**. iPhone/browser visual smoke **unavailable**. |
| Architectural findings | Single Help authority. Voice seam remains `topic_for_context` / `help_payload`. Company today ≠ Company Attention. No Field Punch List or client Walkthrough product. No schema. No Voice. C2 sealed. |
| Open decisions | Voice-with-Help. People & Access. Whole-product UAT. Completion Sign-Off after UAT. |
| Next milestone | **D5 — Voice with Help.** |
| Commit | `e7c3fb35a1b1c4519c387a71eb8f7e81a6cc1169` (`feat: extend contextual Help across Field`) |
| Date | 2026-09-19 |

### 2026-09-19 — D3 office Help

| Field | Content |
|-------|---------|
| Milestone | D3 — Office Help |
| Status | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / LIVE OFFICE SMOKE PASS / NO MIGRATION / NO DB MUTATION.** Presentation only. D1 Hub Help preserved. D2 terminology reused. Help product overall **PARTIAL**. LEARN remains Future. Official V1 **not rescored**. Completion Sign-Off **NOT IMPLEMENTED**. |
| Branch | `main` |
| Base commit | `95dfe22dab338e6302e8820dfe4017435bad5e41` (`feat: clarify remaining contractor-facing language residuals`) |
| Objective | Extend the existing D1 Help authority to high-value contractor-facing office screens outside the Project Hub. One reusable Help/context payload for later Voice. |
| Deliverables | Office topics in `help_content.py`; native `<details>` Help on Dashboard, Clients, Projects Current/Closed, Schedule, Company Attention, Estimates, Previous estimates, Cost library, Settings/Brand Profile, Permit report, Job location, Time, Change Orders; `help_payload()`; dedicated D3 tests |
| Validation | Dedicated D3 **8 passed**. D1 Help **9 passed**. Focused/regression **348 passed**, 966 warnings, **161.81s**. Full suite **1421 passed**, 4910 warnings, **678.61s**, exit **0**. |
| Architectural findings | Single Help authority. Voice seam is `topic_for_context` / `help_payload`. C1/C2 contractor UI remains on Hub BUILD Help. Field Help empty. No schema. No Voice. C2 sealed. |
| Open decisions | D4 Field Help. Voice-with-Help. People & Access. Whole-product UAT. Completion Sign-Off after UAT. |
| Next milestone | **D4 — Field Help.** |
| Commit | `61f86789ae4e755fb39b3d65cbfee6a481ab15e8` (`feat: extend contextual Help across Office`) |
| Date | 2026-09-19 |

### 2026-09-19 — D2 bounded contractor-language residuals

| Field | Content |
|-------|---------|
| Milestone | D2 — Bounded contractor-language residuals |
| Status | **IMPLEMENTED / TESTED / COMMITTED / PUSHED.** Presentation only. D1 Help preserved. Help product overall **PARTIAL**. LEARN remains Future. Official V1 **not rescored**. Completion Sign-Off **NOT IMPLEMENTED**. |
| Branch | `main` |
| Base commit | `76749bb4fd301c928e88b092226fb8a7a0d29e20` (`feat: add Project Hub contextual Help`) |
| Objective | Remove bounded contractor-facing language/navigation residuals on Hub PRICE, Previous estimates, Permit screens, header Settings, and Cost library. |
| Deliverables | contractor_copy labels; Hub PRICE display; header Settings link; nav/page titles; permit chrome/PDF banner; dedicated D2 tests |
| Validation | Dedicated D2 **6 passed**. Focused/regression **357 passed**, 1040 warnings, **150.18s**. Full suite **1413 passed**, 4891 warnings, **613.33s**, exit **0**. |
| Architectural findings | No pricing/estimate/permit-logic/C2/schema change. Internal method keys unchanged. |
| Open decisions | D3 Office Help. D4 Field Help. Voice. People & Access. Whole-product UAT. Completion Sign-Off after UAT. |
| Next milestone | **STOP.** Recommended next: **D3 — Office Help**. Do **not** implement D3 from this record. |
| Commit | this D2 commit follows |
| Date | 2026-09-19 |

### 2026-09-19 — D1 Project Hub contextual Help

| Field | Content |
|-------|---------|
| Milestone | D1 — Project Hub contextual Help |
| Status | **IMPLEMENTED / TESTED / COMMITTED / PUSHED.** Help product overall **PARTIAL**. LEARN remains Future. Voice / office/Field Help / User Guide **NOT IMPLEMENTED**. Official V1 **not rescored** (**65% / 4 of 11**). Secondary Functional V1 Build **79% / 22 of 28**. Completion Sign-Off **NOT IMPLEMENTED**. |
| Branch | `main` |
| Base commit | `4b9c456698370da67a91705b703ea0cbcfed986c` (`docs: record FG-035 Client Final Walkthrough live migration`) |
| Objective | First in-product Help on Project Hub PLAN / PRICE / CONTRACT / BUILD / MONITOR. Reusable static Help content authority. Informational only. |
| Deliverables | `app/presentation/help_content.py`; `app/templates/partials/contextual_help.html`; Hub `projects/detail.html` Help controls; CSS; dedicated tests |
| Validation | Dedicated D1 **9 passed**. Focused Hub/C2/C1/Close **169 passed**. Full suite **1407 passed**, 4875 warnings, **670.37s**, exit **0**. |
| Architectural findings | Native `<details>` / `<summary>`. Shell injects `help_content`. No schema. No Voice. C2 remained sealed. |
| Open decisions | D2 language residuals. D3 office Help. D4 Field Help. Voice. People & Access. Whole-product UAT. Completion Sign-Off after UAT. |
| Next milestone | **STOP.** Recommended next: **D2 — bounded contractor-language residuals**. Do **not** implement D2 from this record. |
| Commit | this D1 commit follows |
| Date | 2026-09-19 |

### 2026-09-19 — FG-035 CORE CLOSE C2 Client Final Walkthrough live migration

| Field | Content |
|-------|---------|
| Milestone | FG-035 CORE CLOSE C2 Client Final Walkthrough live migration |
| Status | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE-MIGRATED / EMPTY LIVE BASELINE VERIFIED / NOT LIVE-UATed WITH CLIENT DATA.** Product SHA **`ec4ef9956025fd8e281c12c17d84493b121f8337`**. Pin SHA **`14bd00b88c3a25ea7576be1d3dd2bbe288d272de`**. Additive **`e5f6a7b8c9d0` applied live**. Live Alembic **`e5f6a7b8c9d0 (head)`**. C2 **LIVE / 0 INVITATIONS**. C1 Punch List remains **LIVE / 0 ITEMS**. Completion Sign-Off **NOT IMPLEMENTED**. CORE CLOSE overall **PARTIAL**. FG-035 **OPEN / PARTIAL**. |
| Branch | `main` |
| Base commit | `14bd00b88c3a25ea7576be1d3dd2bbe288d272de` |
| Objective | Live migrate accepted C2 schema. Prove empty Final Walkthrough baseline. No live client invitation. No Completion Sign-Off. |
| Deliverables | Backup; `flask db upgrade e5f6a7b8c9d0`; empty baseline proof; office restart; read-only Hub smoke; minimum governance. Evidence [testing/fg035-core-close-c2-client-final-walkthrough-live-migration-empty-baseline.md](testing/fg035-core-close-c2-client-final-walkthrough-live-migration-empty-baseline.md). |
| Validation | Dedicated **34 passed**, 74 warnings, **18.70s**. Focused **352 passed**, 1303 warnings, **198.21s**. Full suite **1398 passed**, 4860 warnings, **779.71s**, exit **0**. Live occupancy 50/50 ACTIVE/0 CLOSED/0 events. C2 invitations **0**. Punch List items **0**. |
| Architectural findings | Additive schema only. No seed. No automatic invitation. Client input remains CLIENT INPUT. Pending C2 is not a Sign-Off hard gate. |
| Open decisions | Completion Sign-Off. Labeled live Close/Reopen UAT. PA-B. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Recommended next: **D — PROJECT COMPLETION SIGN-OFF**. |
| SHA / tag | product **`ec4ef9956025fd8e281c12c17d84493b121f8337`**; pin **`14bd00b88c3a25ea7576be1d3dd2bbe288d272de`**; this live-migration record follows |
| Date | 2026-09-19 |

### 2026-09-19 — FG-035 CORE CLOSE C2 Client Final Walkthrough SHA pin

| Field | Content |
|-------|---------|
| Milestone | FG-035 CORE CLOSE C2 Client Final Walkthrough SHA pin |
| Status | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NOT LIVE-MIGRATED / NOT LIVE-UATed.** Product SHA **`ec4ef9956025fd8e281c12c17d84493b121f8337`**. Additive **`e5f6a7b8c9d0`**. Graph head **`e5f6a7b8c9d0`**. Live Alembic remains **`d4e5f6a7b8c9`**. C2 **IMPLEMENTED / NOT LIVE**. C1 Punch List remains **LIVE / 0 ITEMS**. Completion Sign-Off **NOT IMPLEMENTED**. CORE CLOSE overall **PARTIAL**. FG-035 **OPEN / PARTIAL**. |
| Branch | `main` |
| Base commit | `ec4ef9956025fd8e281c12c17d84493b121f8337` |
| Objective | Pin accepted C2 product SHA. No live C2 data. No Completion Sign-Off. |
| Deliverables | Minimum SHA-pin governance. Product already committed. |
| Validation | Accepted evidence reused: Dedicated **34 passed**, 74 warnings, **19.71s**. Focused **352 passed**, 1303 warnings, **197.04s**. Full suite **1398 passed**, 4860 warnings, **767.57s**, exit **0**. |
| Architectural findings | Hashed no-login invitation. Client input ≠ Punch List. Accept requires work source. Origin CLIENT_WALKTHROUGH. Photos DEFERRED. Email copyable-link. |
| Open decisions | Live migrate `e5f6a7b8c9d0` (same authorized prompt). Completion Sign-Off. Labeled live Close/Reopen UAT. PA-B. |
| Next milestone | Same authorized prompt continues to live migrate after a hard clean checkpoint. Do **not** send a live client invitation. |
| SHA / tag | product **`ec4ef9956025fd8e281c12c17d84493b121f8337`**; this pin follows |
| Date | 2026-09-19 |

### 2026-09-19 — FG-035 CORE CLOSE C2 Client Final Walkthrough (working tree / not committed)

| Field | Content |
|-------|---------|
| Milestone | FG-035 CORE CLOSE C2 Client Final Walkthrough |
| Status | **IMPLEMENTED IN WORKING TREE / TESTED / MIGRATION FILE CREATED / NOT LIVE-MIGRATED / NOT COMMITTED / NOT PUSHED.** Additive **`e5f6a7b8c9d0`**. Graph head **`e5f6a7b8c9d0`**. Live Alembic remains **`d4e5f6a7b8c9`**. No live C2 data. Photo **DEFERRED**. Email **copyable link / pending configuration**. C1 Punch List remains **LIVE / 0 ITEMS**. Completion Sign-Off **NOT IMPLEMENTED**. CORE CLOSE overall **PARTIAL**. FG-035 **OPEN / PARTIAL**. |
| Branch | `main` |
| Base commit | HEAD / `origin/main` **`2fdc89b47230d1389309a415373c2742610efcd2`** |
| Objective | Bounded no-login Client Final Walkthrough. Client input is not the Punch List. Contractor remains authoritative. |
| Deliverables | Invitation + item + access-attempt models; additive migration FILE; service; Hub `#hub-final-walkthrough`; public `/walkthrough/<credential>` form; dedicated tests; minimum governance; Manual Impact. |
| Validation | Dedicated `tests/test_core_close_client_final_walkthrough_c2_fg035.py` **34 passed**, 74 warnings, **19.71s**. C1 **26 passed**, 56 warnings, **14.65s**. Focused **352 passed**, 1303 warnings, **197.04s**. Full suite **1398 passed**, 4860 warnings, **767.57s**, exit **0**. |
| Architectural findings | Hashed token + lookup_key. One response per invitation. Accept-to-Punch-List requires contractor work source. Origin CLIENT_WALKTHROUGH. Pending client input is not a Sign-Off hard gate. Unanswered invitation does not block Close. |
| Open decisions | Architect ACCEPT COMMIT C2. Live migrate separately. Completion Sign-Off. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Expected: **ACCEPT COMMIT C2**. After C2 close: **D — COMPLETION SIGN-OFF**. |
| Commit | none |
| Date | 2026-09-19 |

### 2026-09-19 — FG-035 CORE CLOSE C1 Contractor Punch List live migration

| Field | Content |
|-------|---------|
| Milestone | FG-035 CORE CLOSE C1 Contractor Punch List live migration |
| Status | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE-MIGRATED / EMPTY LIVE BASELINE VERIFIED / NOT LIVE-UATed WITH MUTATING DATA.** Product SHA **`81b6d802ccf15c10b01a1f63337ef4d0d5a26d6c`**. Pin SHA **`7bdbf191fe062f43550a9ccb81abf6eb21db8691`**. Additive **`d4e5f6a7b8c9` applied live**. Live Alembic **`d4e5f6a7b8c9 (head)`**. Punch List **LIVE / 0 ITEMS**. C2 Client Final Walkthrough **NOT IMPLEMENTED**. Completion Sign-Off **NOT IMPLEMENTED**. CORE CLOSE overall **PARTIAL**. FG-035 **OPEN / PARTIAL**. |
| Branch | `main` |
| Base commit | `7bdbf191fe062f43550a9ccb81abf6eb21db8691` |
| Objective | Live migrate accepted C1 schema. Prove empty Punch List baseline. No mutating live UAT. |
| Deliverables | Backup; `flask db upgrade d4e5f6a7b8c9`; empty baseline proof; office restart; read-only Hub smoke; minimum governance. Evidence [testing/fg035-core-close-c1-punch-list-live-migration-empty-baseline.md](testing/fg035-core-close-c1-punch-list-live-migration-empty-baseline.md). |
| Validation | Dedicated **26 passed**, 56 warnings, **14.51s**. Focused **228 passed**, 862 warnings, **110.42s**. Full suite **1364 passed**, 4786 warnings, **808.82s**, exit **0**. Live occupancy 50/50 ACTIVE/0 CLOSED/0 events. Punch List items **0**. |
| Architectural findings | Additive schema only. No seed. Open Punch List does not hard-block Close. Zero OPEN items satisfies the Punch List prerequisite. |
| Open decisions | C2 Client Final Walkthrough. Completion Sign-Off. Labeled live Close/Reopen UAT. PA-B. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Recommended next: **C2 CLIENT FINAL WALKTHROUGH**. |
| SHA / tag | product **`81b6d802ccf15c10b01a1f63337ef4d0d5a26d6c`**; pin **`7bdbf191fe062f43550a9ccb81abf6eb21db8691`**; this live-migration record follows |
| Date | 2026-09-19 |

### 2026-09-19 — FG-035 CORE CLOSE C1 Contractor Punch List SHA pin

| Field | Content |
|-------|---------|
| Milestone | FG-035 CORE CLOSE C1 Contractor Punch List SHA pin |
| Status | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NOT LIVE-MIGRATED.** Product SHA **`81b6d802ccf15c10b01a1f63337ef4d0d5a26d6c`**. Additive **`d4e5f6a7b8c9`**. Graph head **`d4e5f6a7b8c9`**. Live Alembic remains **`c3d4e5f6a7b8`**. Punch List **IMPLEMENTED / NOT LIVE**. C2 Client Final Walkthrough **NOT IMPLEMENTED**. Completion Sign-Off **NOT IMPLEMENTED**. CORE CLOSE overall **PARTIAL**. FG-035 **OPEN / PARTIAL**. |
| Branch | `main` |
| Base commit | `81b6d802ccf15c10b01a1f63337ef4d0d5a26d6c` |
| Objective | Pin accepted C1 product SHA. No live Punch List data. No C2. |
| Deliverables | Minimum SHA-pin governance. Product already committed. |
| Validation | Accepted evidence reused: Dedicated **26 passed**, 56 warnings, **17.71s**. Focused **228 passed**, 862 warnings, **148.71s**. Full suite **1364 passed**, 4786 warnings, **719.07s**, exit **0**. |
| Architectural findings | OPEN/COMPLETE only. CONTRACTOR origin only. Open Punch List does not hard-block Close. Zero OPEN items satisfies the Punch List prerequisite. |
| Open decisions | Live migrate `d4e5f6a7b8c9` (same authorized prompt). C2 Client Final Walkthrough. Completion Sign-Off. Labeled live Close/Reopen UAT. PA-B. |
| Next milestone | Same authorized prompt continues to live migrate after a hard clean checkpoint. Do **not** create live Punch List data. |
| SHA / tag | product **`81b6d802ccf15c10b01a1f63337ef4d0d5a26d6c`**; this pin follows |
| Date | 2026-09-19 |

### 2026-09-18 — FG-035 CORE CLOSE C1 Contractor Punch List (working tree / not committed)

| Field | Content |
|-------|---------|
| Milestone | FG-035 CORE CLOSE C1 Contractor Punch List |
| Status | **IMPLEMENTED IN WORKING TREE / TESTED / MIGRATION FILE CREATED / NOT LIVE-MIGRATED / NOT COMMITTED / NOT PUSHED.** Additive **`d4e5f6a7b8c9`**. Graph head **`d4e5f6a7b8c9`**. Live Alembic remains **`c3d4e5f6a7b8`**. No live Punch List rows. Client Final Walkthrough **NOT IMPLEMENTED**. Completion Sign-Off **NOT IMPLEMENTED**. CORE CLOSE overall **PARTIAL / NOT YET SEALED**. |
| Branch | `main` |
| Base commit | HEAD / `origin/main` **`098616284cfb468a5ebecb49c25a30ebd2a621e2`** |
| Objective | Authoritative contractor Punch List with OPEN/COMPLETE, work source vs origin, Hub surface, derived zero-open Sign-Off seam, C2-ready architecture without C2 implementation. |
| Deliverables | Model + events; additive migration FILE; service; Hub `#hub-punch-list`; dedicated tests; minimum governance; Manual Impact. |
| Validation | Dedicated `tests/test_core_close_punch_list_c1_fg035.py` **26 passed**, 56 warnings, **17.71s**. Focused CORE CLOSE/work/FG-038 **228 passed**, 862 warnings, **148.71s**. Full suite **1364 passed**, 4786 warnings, **719.07s**, exit **0**. Live occupancy 50/50 ACTIVE/0 CLOSED/0 events. |
| Architectural findings | Contractor origin only. Client input ≠ Punch List item. Open Punch List does not hard-block Close. Future C2 photo may reuse FG-020 Originals. |
| Open decisions | Architect ACCEPT COMMIT. Live migrate separately. C2 Client Final Walkthrough. Completion Sign-Off. |
| Next milestone | **STOP.** Return to ChatGPT Architect. |
| Commit | none |
| Date | 2026-09-18 |

### 2026-09-18 — FG-035 CORE CLOSE Close/Reopen Option A SHA pin

| Field | Content |
|-------|---------|
| Milestone | FG-035 CORE CLOSE Close/Reopen Option A SHA pin |
| Status | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NO MIGRATION / NOT LIVE-UATed.** Product SHA **`172f0786aaa9e668f30be28c3cee30ac4fce5b1f`**. Authorization = Instance Owner / future System Administrator. `COMPANY_MANAGEMENT` is **not** Close/Reopen authority. Close and Reopen **NOT LIVE-EXECUTED**. Punch List **NOT IMPLEMENTED**. Completion Sign-Off **NOT IMPLEMENTED**. CORE CLOSE overall **PARTIAL / NOT YET SEALED**. |
| Branch | `main` |
| Base commit | `172f0786aaa9e668f30be28c3cee30ac4fce5b1f` |
| Objective | Pin accepted Option A product SHA. No live Close. No product expansion. |
| Deliverables | Minimum SHA-pin governance. Product already committed. |
| Validation | Accepted full suite **1338 passed**, 4730 warnings, **966.45s**, exit **0**. Live occupancy 50 / 50 ACTIVE / 0 CLOSED / 0 events. |
| Architectural findings | No migration. Domain B remains not Close authority. Invalid repeats remain fail-and-flash. |
| Open decisions | Punch List. Completion Sign-Off. Labeled live Close/Reopen UAT. PA-B. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Recommended next: FG-035 CORE CLOSE PUNCH LIST. Do **not** Close a live Project from this record. |
| SHA / tag | product **`172f0786aaa9e668f30be28c3cee30ac4fce5b1f`**; this pin follows |
| Date | 2026-09-18 |

### 2026-09-18 — FG-035 CORE CLOSE Close/Reopen Option A (working tree / not committed)

| Field | Content |
|-------|---------|
| Milestone | FG-035 CORE CLOSE Close/Reopen Option A |
| Status | **IMPLEMENTED IN WORKING TREE / TESTED / NO MIGRATION / NOT COMMITTED / NOT PUSHED / NOT LIVE-UATed.** Authorization = Instance Owner / future System Administrator. `COMPANY_MANAGEMENT` is **not** Close/Reopen authority. Close and Reopen **NOT LIVE-EXECUTED**. Punch List **NOT IMPLEMENTED**. Completion Sign-Off **NOT IMPLEMENTED**. CORE CLOSE overall **PARTIAL / NOT YET SEALED**. |
| Branch | `main` |
| Base commit | `acb6e1e0df7c84047e8cfa748cea160108b24b9e` |
| Objective | Implement Hub Close/Reopen Option A using existing PA-A authority and lifecycle schema. No live Close. No commit. |
| Deliverables | `close_project` / `reopen_project`; GET/POST confirmation; Hub Current/Closed identity; hide New Change Order on CLOSED Hub; dedicated tests; minimum governance; Manual Impact. |
| Validation | Dedicated **22 passed**, 133 warnings, **18.23s**, exit **0**. Slice A+B **55 passed**, 143 warnings, **18.54s**. FG-038 **35 passed**, 88 warnings, **18.61s**. Full suite **1338 passed**, 4730 warnings, **966.45s**, exit **0**. Live occupancy 50 / 50 ACTIVE / 0 CLOSED / 0 events. |
| Architectural findings | Existing `ProjectOperatingStateEvent` is sufficient. Domain B is not Close authority. Invalid repeats fail-and-flash. No migration. |
| Open decisions | Architect ACCEPT COMMIT. Labeled live Close/Reopen UAT. Punch List. Completion Sign-Off. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do **not** commit, push, SHA-pin, or Close a live Project from this record. |
| SHA / tag | none — not committed |

### 2026-09-18 — FG-038 PA-A Stage 2 first Instance Owner SET

| Field | Content |
|-------|---------|
| Milestone | FG-038 PA-A Stage 2 first Owner SET |
| Status | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE-MIGRATED / FIRST OWNER ASSIGNED / LIVE AUTHORITY UAT PASS.** Product SHA **`01e7463082b84b2fcd9d61ff7125a5012b7f8043`**. Live Alembic **`c3d4e5f6a7b8 (head)`**. ORG-001 Owner = Membership **1** / User **1** / Joel Brayman. Isolation orgs **OWNERLESS**. Owner SET events **1**. Sys Admin **NOT IMPLEMENTED**. People & Access UI **NOT IMPLEMENTED**. Close/Reopen **NOT IMPLEMENTED**. CORE CLOSE owner-authority blocker **CLEARED FOR ORG-001**. |
| Branch | `main` |
| Base commit | `b434b041b4c873d62a2f2e8926c16e563e786e6d` |
| Objective | Explicit live SET ORG-001 Membership 1 / actor 1. Prove authority. No Close/Reopen. |
| Deliverables | Live pointer + one SET event; [testing/fg038-pa-a-first-instance-owner-authority-uat.md](testing/fg038-pa-a-first-instance-owner-authority-uat.md); minimum governance. |
| Validation | CLI exit **0**. Dedicated **35 passed**. Focused **113 passed**. Full **1316 passed**, 4597 warnings, **683.84s**, exit **0**. Occupancy **50 / 50 ACTIVE / 0 CLOSED / 0 events**. Grants **1**. |
| Architectural findings | Owner is not Domain B. Isolation orgs remain ownerless. CORE CLOSE may later consume `require_instance_owner_or_system_administrator` for ORG-001. Close/Reopen still unimplemented. |
| Open decisions | PA-B Sys Admin. Close/Reopen. People & Access UI. |
| Next milestone | Architect review. Do **not** implement Close/Reopen from this record. |
| Commit | this Stage 2 governance commit |
| Date | 2026-09-18 |

### 2026-09-18 — FG-038 PA-A Stage 1 live migration (ownerless checkpoint)

| Field | Content |
|-------|---------|
| Milestone | FG-038 PA-A Stage 1 live migration |
| Status | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE-MIGRATED / NO OWNER ASSIGNED.** Product SHA **`01e7463082b84b2fcd9d61ff7125a5012b7f8043`**. Live Alembic **`c3d4e5f6a7b8 (head)`**. Organizations **3 OWNERLESS**. Owner SET events **0**. Sys Admin **NOT IMPLEMENTED**. People & Access UI **NOT IMPLEMENTED**. Close/Reopen **NOT IMPLEMENTED**. |
| Branch | `main` |
| Base commit | `a42ffe59005f8e282d4dbbfcbcbc0b5bbb86db8d` |
| Objective | Apply additive `c3d4e5f6a7b8` live. Prove ownerless. No Owner SET. |
| Deliverables | Live schema; [testing/fg038-pa-a-live-migration-ownerless-checkpoint.md](testing/fg038-pa-a-live-migration-ownerless-checkpoint.md); minimum governance. |
| Validation | `flask db upgrade c3d4e5f6a7b8` exit **0**. Dedicated **35 passed**. Focused **113 passed**. Full **1316 passed**, 4597 warnings, **574.01s**, exit **0**. Occupancy **50 / 50 ACTIVE / 0 CLOSED / 0 events**. Grants **1**. |
| Architectural findings | Live current now equals graph head. Ownerless fail-closed proven. Domain B unchanged. Owner is not Domain B. |
| Open decisions | Stage 2 explicit Owner SET. PA-B Sys Admin. Close/Reopen. |
| Next milestone | Architect review. Do **not** assign Owner from this record. |
| Commit | this Stage 1 governance commit |
| Date | 2026-09-18 |

### 2026-09-18 — FG-038 PA-A product SHA pin

| Field | Content |
|-------|---------|
| Milestone | FG-038 PA-A pin |
| Status | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NOT LIVE-MIGRATED / NO OWNER ASSIGNED.** Product SHA **`01e7463082b84b2fcd9d61ff7125a5012b7f8043`**. Additive **`c3d4e5f6a7b8`**. Live Alembic remains **`b2c3d4e5f6a7`**. Graph head **`c3d4e5f6a7b8`**. All organizations **OWNERLESS**. Sys Admin **NOT IMPLEMENTED**. People & Access UI **NOT IMPLEMENTED**. Close/Reopen **NOT IMPLEMENTED**. |
| Branch | `main` |
| Base commit | `01e7463082b84b2fcd9d61ff7125a5012b7f8043` |
| Objective | Pin PA-A product SHA. No live migrate. No Owner assignment. |
| Deliverables | Minimum governance SHA pin. |
| Validation | Product tests not rerun. Accepted dedicated **35** / focused **150** / full **1316**. Live occupancy **50 / 50 ACTIVE / 0 CLOSED / 0 events**. Grants **1**. Live Instance Owners **0**. |
| Architectural findings | Graph head vs live current mismatch is intentional until separately authorized live migrate. Owner is not Domain B. |
| Open decisions | Live migrate. Explicit Owner assignment. PA-B Sys Admin. Close/Reopen. |
| Next milestone | Architect review. Do **not** live-migrate from this pin. Do **not** assign Owner from this pin. |
| Commit | this pin |
| Date | 2026-09-18 |

### 2026-09-18 — FG-038 PA-A Instance Owner authority foundation (working tree)

| Field | Content |
|-------|---------|
| Milestone | FG-038 PA-A Instance Owner authority foundation |
| Status | **IMPLEMENTED IN WORKING TREE / TESTED / MIGRATION FILE CREATED / NOT LIVE-MIGRATED / NOT COMMITTED / NO OWNER ASSIGNED.** Additive **`c3d4e5f6a7b8`**. Live Alembic remains **`b2c3d4e5f6a7`**. Graph head **`c3d4e5f6a7b8`**. All organizations **OWNERLESS**. Sys Admin **DEFERRED**. People & Access UI **NOT IMPLEMENTED**. Close/Reopen **NOT IMPLEMENTED**. |
| Branch | `main` |
| Base commit | `46939919a83f6952680eff80d990521937ba4f21` |
| Objective | Persist Contractor Instance Owner as protected organization-scoped administrative root. No live assignment. |
| Deliverables | Owner pointer + SET events; `instance_authority` service; `flask auth set-instance-owner`; deactivation guards; dedicated tests; FG-038; additive migration file only. |
| Validation | Dedicated **35 passed**, 88 warnings, **15.49s**. Focused **150 passed**, 364 warnings, **60.60s**. Full suite **1316 passed**, 4597 warnings, **561.70s**, exit **0**. Live occupancy **50 / 50 ACTIVE / 0 CLOSED / 0 events**. Grants **1**. |
| Architectural findings | Owner is not Domain B. Ownerless 403. Combined helper ready for later PA-B. No new ADR. |
| Open decisions | Live migrate. Explicit Owner assignment (org-id + membership-id). PA-B Sys Admin. Close/Reopen. |
| Next milestone | Architect-governed live migrate and/or Owner assignment — **NOT THIS WORKING TREE**. |
| Commit | none — not committed |
| Date | 2026-09-18 |

### 2026-09-18 — FG-035 CORE CLOSE Slice B SHA pin

| Field | Content |
|-------|---------|
| Milestone | FG-035 CORE CLOSE Slice B pin |
| Status | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NO MIGRATION.** Product SHA **`9360b706ab66f2588306b201ca0c4c45645fcb9a`**. Close/Reopen **NOT IMPLEMENTED**. Punch List **NOT IMPLEMENTED**. Completion Sign-Off **NOT IMPLEMENTED**. CORE CLOSE overall **PARTIAL / NOT OPERATIONAL**. |
| Branch | `main` |
| Base commit | `9360b706ab66f2588306b201ca0c4c45645fcb9a` |
| Objective | Pin Slice B product SHA. No Close/Reopen. No Punch List. |
| Deliverables | Minimum governance SHA pin. |
| Validation | Product tests not rerun. Accepted dedicated **37** / A+B **55** / focused **234** / scope **23** / full **1281**. Alembic remains **`b2c3d4e5f6a7`**. Live occupancy **50 / 50 ACTIVE / 0 CLOSED / 0 events**. |
| Architectural findings | CLOSE blocks NEW operational records. It does not strand administrative completion of existing Time / CO / actuals. Incomplete physical work is Punch List later. |
| Open decisions | Close/Reopen action. Punch List. Completion Sign-Off. |
| Next milestone | Architect review. Do **not** implement Close/Reopen from this pin. |
| Commit | this pin |
| Date | 2026-09-18 |

### 2026-09-18 — FG-035 CORE CLOSE Slice A live migration

| Field | Content |
|-------|---------|
| Milestone | FG-035 CORE CLOSE Slice A live migration |
| Status | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE-MIGRATED.** Product SHA **`f4b7515664c51850f3d87ed79f4a7e1226886fbd`**. Live Alembic **`b2c3d4e5f6a7 (head)`**. All existing Projects **ACTIVE**. Event rows **0**. Close/Reopen **NOT IMPLEMENTED**. Punch List **NOT IMPLEMENTED**. Completion Sign-Off **NOT IMPLEMENTED**. |
| Branch | `main` |
| Base commit | `cdb107058cc475cfd2ef960593939226df6ad02b` |
| Objective | Apply additive `b2c3d4e5f6a7` live. Prove ACTIVE baseline. No Slice B. |
| Deliverables | Live schema/data; minimum governance record. |
| Validation | `flask db upgrade` exit **0**. Focused **176 passed**, 670 warnings, **91.05s**, exit **0**. Occupancy fingerprint unchanged. EST-2026-0019 unchanged. Grants **1**. |
| Architectural findings | Live current now equals graph head. Intentional mismatch is resolved. Close/Reopen still unimplemented. |
| Open decisions | Slice B / consumer switches. Close/Reopen action. Punch List. Completion Sign-Off. |
| Next milestone | Architect review. Do **not** implement Slice B from this record. |
| Commit | this live-migration docs commit |
| Date | 2026-09-18 |

### 2026-09-18 — FG-035 CORE CLOSE Slice A SHA pin

| Field | Content |
|-------|---------|
| Milestone | FG-035 CORE CLOSE Slice A pin |
| Status | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NOT LIVE-MIGRATED.** Product SHA **`f4b7515664c51850f3d87ed79f4a7e1226886fbd`**. Close/Reopen **NOT IMPLEMENTED**. Punch List **NOT IMPLEMENTED**. Completion Sign-Off **NOT IMPLEMENTED**. |
| Branch | `main` |
| Base commit | `f4b7515664c51850f3d87ed79f4a7e1226886fbd` |
| Objective | Pin Slice A product SHA. No live migrate. |
| Deliverables | Minimum governance SHA pin. |
| Validation | Product tests not rerun. Accepted dedicated **18** / focused **176** / full **1244**. Live current remains **`a0b1c2d3e4f5`**. |
| Architectural findings | Graph head `b2c3d4e5f6a7` vs live current `a0b1c2d3e4f5` is intentional. |
| Open decisions | Live migrate. Close/Reopen action. Consumer switches. Punch List. Completion Sign-Off. |
| Next milestone | Architect review. Do **not** live-migrate from this pin. |
| Commit | this pin |
| Date | 2026-09-18 |

### 2026-09-18 — FG-035 CORE CLOSE Slice A foundation (working tree / then product-committed)

| Field | Content |
|-------|---------|
| Milestone | FG-035 CORE CLOSE Slice A |
| Status | **IMPLEMENTED IN WORKING TREE / TESTED / MIGRATION FILE CREATED / NOT LIVE-MIGRATED / NOT COMMITTED.** Close/Reopen **NOT IMPLEMENTED**. Punch List **NOT IMPLEMENTED**. Completion Sign-Off **NOT IMPLEMENTED**. |
| Branch | `main` |
| Base commit | `2d173b512a5be87b0ee24ce1b5ce0dfbb3ede125` |
| Objective | Persist Project operating lifecycle foundation without Close/Reopen action or consumer switches. |
| Deliverables | `Project.operating_state` ACTIVE/CLOSED; `ProjectOperatingStateEvent`; `list_current_operating_projects`; additive **`b2c3d4e5f6a7`**; dedicated tests; subsequent owner freeze that physical work completion ≠ administrative Change Order completion. |
| Validation | Dedicated **18 passed**. Focused **176 passed**, 670 warnings, **110.43s**, exit **0**. Full suite **1244 passed**, 4390 warnings, **640.57s**, exit **0**. Live `flask db current` remains **`a0b1c2d3e4f5`**. Stash **`840dba8320b59ff9464410fec390d755a31a56aa`** preserved. |
| Architectural findings | Do not reuse `Project.status`. Do not infer physical completion from Change Order status. Incomplete physical work is Punch List, not admin CO. NEW CO after Close requires Reopen. |
| Open decisions | Architect ACCEPT COMMIT. Live migrate. Close/Reopen action waits persisted Instance Owner. Consumer switches. Punch List. Completion Sign-Off. |
| Next milestone | Architect review / ACCEPT COMMIT. Do **not** live-migrate from this record. |
| Commit | **NOT COMMITTED** |
| Date | 2026-09-18 |

### 2026-09-18 — FG-035 CORE CLOSE / Project lifecycle owner freeze (docs-only)


| Field | Content |
|-------|---------|
| Milestone | FG-035 CORE CLOSE |
| Status | **RECORDED MANDATORY PRODUCT DIRECTION / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED.** No schema. No product. No live Project Close. |
| Branch | `main` |
| Base commit | `9765c7da56d96a3dafd431fef5901e0d821c3393` |
| Objective | Freeze Joel owner decisions for CORE CLOSE / Project operating lifecycle, Punch List, and Project Completion Sign-Off. |
| Deliverables | [architecture/core-close-project-lifecycle-product-direction.md](architecture/core-close-project-lifecycle-product-direction.md) plus minimum FG-035 / index / handoff updates. |
| Validation | Docs-only. Baseline HEAD = origin/main `9765c7d`. Alembic `a0b1c2d3e4f5 (head)`. No app/test/migration change. Prompt §36 DESKTOP body truncated; no extra desktop/Field Close product invented. |
| Architectural findings | CORE CLOSE is distinct from LEARN Closeout. V1 operating lifecycle is ACTIVE / CLOSED. Do not reuse `Project.status`. Shared current-operating-Project authority. History law. Instance Owner / Sys Admin Close/Reopen. Punch List hard-gates Completion Sign-Off. Unsigned Completion Sign-Off warns on Close. |
| Open decisions | Implementation authorization. People & Access product. Home Office. LEARN. Scores not rescored. |
| Next milestone | Architect review / ACCEPT COMMIT. STOP. |
| Commit | pending Joel-approved docs commit |
| Date | 2026-09-18 |

### 2026-09-17 — FG-035 PERF-C LIVE UAT / SEAL (docs-only)

| Field | Content |
|-------|---------|
| Milestone | FG-035 PERF-C |
| Status | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE UAT PASS / SEALED.** No schema. No live occupancy mutation. |
| Branch | `main` |
| Base commit | `d6febfcac0687584f631987205282a8202fa99ef` |
| Objective | Record Architect live-UAT disposition and seal PERF-C. |
| Deliverables | [testing/fg035-perf-c-live-uat-record.md](testing/fg035-perf-c-live-uat-record.md); minimum PERF-C / FG-035 governance. |
| Validation | Architect-accepted existing-occupancy UAT: Joel `/company-attention` **200**; AUTH-B **403**; 49 Projects considered; 6 with attention; 27 sealed facts; 0 unsupported; 0 duplicates. |
| Architectural findings | Organization-wide UAT-vessel dominance is valid occupancy noise / future Project lifecycle, not a PERF-C defect. No filtering implemented. |
| Open decisions | Functional V1 Build score reconciliation. Project lifecycle. FG-035 remains OPEN (CLOSE / LEARN / QB-T). |
| Next milestone | Architect-governed next product. STOP. |
| Commit | this docs close (`docs: seal FG-035 PERF-C after live UAT`) |
| Date | 2026-09-17 |

### 2026-09-17 — FG-035 PERF-C Company Attention Slice A COMMIT / PUSH / SHA-PIN

| Field | Content |
|-------|---------|
| Milestone | FG-035 PERF-C Slice A |
| Status | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NOT LIVE-UATed.** No schema. No live UAT data. |
| Branch | `main` |
| Base commit | `d32aa14c13bf3149fc1c3dd8c9024761d8cdda29` |
| Objective | Commit, push, and pin accepted PERF-C Slice A. |
| Deliverables | Product SHA **`22fd30cd774fcf155ae69d7dcf99a44123d91409`**. This pin. |
| Validation | Accepted tests: dedicated **13 passed**; focused **115 passed**; full suite **1226 passed**. No code change during close. |
| Architectural findings | No persistence. No migration. Live grants **1**. Occupancy Projects 45–50 / 27 / EST-2026-0019 unchanged. |
| Open decisions | Live UAT separately governed. Scores not rescored. |
| Next milestone | Architect-governed PERF-C live UAT. STOP. |
| Commit | product **`22fd30cd774fcf155ae69d7dcf99a44123d91409`**; this pin |
| Date | 2026-09-17 |

### 2026-09-17 — FG-035 PERF-C Company Attention Slice A (working tree)

| Field | Content |
|-------|---------|
| Milestone | FG-035 PERF-C Slice A |
| Status | **IMPLEMENTED IN WORKING TREE / TESTED / NOT COMMITTED / NOT PUSHED / NOT LIVE-UATed.** No schema. No live UAT data. |
| Branch | `main` |
| Base commit | `d32aa14c13bf3149fc1c3dd8c9024761d8cdda29` |
| Objective | Derived Company Attention aggregation + office surface + COMPANY_MANAGEMENT gate + tests. |
| Deliverables | `app/services/company_attention.py`; `/company-attention`; office template; permission-aware nav; dedicated tests; minimum governance. |
| Validation | Dedicated **13 passed**, 79 warnings, **10.06s**. Focused **115 passed**, 648 warnings, **68.73s**. Full suite **1226 passed**, 4366 warnings, **610.51s**, exit **0**. Synthetic fixtures only. |
| Architectural findings | Consumes sealed `assemble_project_attention` once per Project. Order = existing `list_organization_projects` `created_at` desc plus `id` desc tiebreaker, then sealed PERF-B item order. No archive filter. No persistence. |
| Open decisions | Commit / live UAT separately authorized. Scores not rescored. |
| Next milestone | Architect review. STOP. |
| Commit | none |
| Date | 2026-09-17 |

### 2026-09-17 — People & Access owner product-direction freeze (docs-only)

| Field | Content |
|-------|---------|
| Milestone | People & Access |
| Status | **RECORDED MANDATORY PRODUCT DIRECTION / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED.** No new ADR. No new Feature Gate. Architect-accepted; sealed by this documentation freeze. |
| Branch | `main` |
| Base commit | `f1940ebe1d80ab0e6e4feb795b7f97402a652bae` |
| Objective | Freeze Instance Owner, System Administrator, Person vs User, A/B/C, Delete User, hourly-wage sensitivity, and desktop UX law. |
| Deliverables | [architecture/people-and-access-product-direction.md](architecture/people-and-access-product-direction.md) plus minimum index/current-authority pointers. |
| Validation | Baseline HEAD f1940eb / FG-037 CLOSED / live grant 1 / Joel Membership 1. Docs-only. |
| Architectural findings | No new ADR required (same pattern as desktop contractor experience and access-domain seam freezes). FG-037 not reopened. PERF-C unchanged. |
| Open decisions | Ben Sys Admin. Scorecard. Ownership transfer rules later. |
| Next milestone | **STOP.** Return to ChatGPT Architect. |
| Commit | this documentation freeze (`docs: freeze People & Access product direction`) |
| Date | 2026-09-17 |

### 2026-09-17 — FG-037 Company / Management access-domain authorization close

| Field | Content |
|-------|---------|
| Milestone | FG-037 |
| Status | **CLOSED / OPERATIONAL FOR COMPANY_MANAGEMENT AUTHORIZATION.** Live migration **PASS**. First explicit grant **PASS**. Default deny **PASS**. Granted user allow **PASS**. Ungranted user deny **PASS**. Project/Operational non-regression **PASS**. Field firewall **PASS**. Sensitive Financial firewall **PASS**. PERF-C **NOT IMPLEMENTED**. |
| Branch | `main` |
| Base commit | `967fea285bb8fc3cb7abefdba9153bbf717d3dcd` |
| Objective | Record owner access policy; grant `COMPANY_MANAGEMENT` only to ORG-001 Membership 1 / Joel Brayman; prove bounded seam UAT; close FG-037. |
| Deliverables | Live grant row 1; owner-policy documentation; FG-037 close. |
| Validation | CLI show Membership 1 effective yes; Membership 2/5 effective no; `require_access_domain` Joel 200 / AUTH-B 403; `/projects/` 200; Field Today 200 with no Company Attention; C rejected; focused **154 passed**, 435 warnings, **82.70s**. |
| Architectural findings | A does not imply B. B does not imply C. Joel+Ben both receiving B/future C is owner policy, not architectural coupling. Ben genuine ORG-001 membership is absent. |
| Open decisions | Architect scorecard (eligibility vs 79%/22 of 28). Ben membership then Ben grant. PERF-C implementation. Recovery stash drop. |
| Next milestone | **STOP.** Return to ChatGPT Architect. |
| Commit | this FG-037 close docs commit |
| Date | 2026-09-17 |

### 2026-09-17 — FG-035 PERF-C product definition / owner-decision freeze (docs-only / not committed)

| Field | Content |
|-------|---------|
| Milestone | FG-035 PERF-C |
| Status | **OPEN / PARTIAL.** PERF-C **DEFINED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. PERF-A / PERF-B remain **SEALED**. No new ADR. No schema. V1 **60% / 4 of 11** **NO RESCORE**. |
| Branch | `main` |
| Base commit | `1b80d244e3efb0c65d3a02dd247d923dfd95166c` |
| Objective | Freeze Company Attention owner decisions. Docs-only. No product. |
| Deliverables | [architecture/fg-035-perf-c-product-definition.md](architecture/fg-035-perf-c-product-definition.md). Minimum index / continuity updates. |
| Validation | Docs-only. Tests **not rerun**. Last accepted full suite **1190 passed**, 4212 warnings, **746.12s**, exit **0**. Alembic **`f9b0c1d2e3f4 (head)`**. |
| Architectural findings | Business-level attention: **Where does my business need attention?** Initial facts = sealed PERF-B only. Not a new risk engine. No persistence. Not Home Office. **NO COMPANY ATTENTION IN THE FIELD APP.** Permission domains A/B/C recorded, not implemented. Organization-wide V1. |
| Open decisions | PERF-C implementation authorization. Home Office. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do **not** implement PERF-C. |
| Commit | none — not committed |
| Date | 2026-09-17 |

### 2026-09-17 — FG-035 PERF-B CLOSE / COMMIT / SHA-PIN / PUSH

| Field | Content |
|-------|---------|
| Milestone | FG-035 PERF-B |
| Status | **OPEN / PARTIAL.** PERF-B **IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS / COMMITTED / SHA-PINNED / PUSHED**. PERF-A remains **SEALED**. No new ADR. No schema. V1 **60% / 4 of 11** **NO RESCORE**. |
| Branch | `main` |
| Base commit | `11a11cb33e8bc7c185557980a1852af66d53b367` |
| Objective | Commit accepted Project Needs Attention. SHA-pin. Push. |
| Deliverables | Product SHA **`dcde4adfe4a475932b7f144b0220b2b60e4bd75c`**. No PERF-B migration. Evidence [testing/fg035-perf-b-live-bounded-uat-record.md](testing/fg035-perf-b-live-bounded-uat-record.md). |
| Validation | Dedicated **36 passed**. Focused **206 passed**. Full suite **1190 passed**, 4212 warnings, **746.12s**, exit **0**. Bounded synthetic live UAT Project **50**. |
| Architectural findings | No schema. SEQUENCE consumed from SCH. Waiting is not its own fact. Field and MONITOR money unchanged. Warning law informational / non-blocking. |
| Open decisions | PERF-C. Home Office. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do **not** begin PERF-C. |
| Commit | `dcde4adfe4a475932b7f144b0220b2b60e4bd75c` |
| Date | 2026-09-17 |

### 2026-09-17 — FG-035 PERF-B bounded synthetic live UAT (uncommitted)

| Field | Content |
|-------|---------|
| Milestone | FG-035 PERF-B |
| Status | **OPEN / PARTIAL.** PERF-B **IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS**. PERF-A remains **SEALED**. No new ADR. No schema. V1 **60% / 4 of 11** **NO RESCORE**. |
| Branch | `main` |
| Base commit | `11a11cb33e8bc7c185557980a1852af66d53b367` |
| Objective | Bounded synthetic live UAT of Project Needs Attention on one new Project. |
| Deliverables | Project **50**; [testing/fg035-perf-b-live-bounded-uat-record.md](testing/fg035-perf-b-live-bounded-uat-record.md); Manual Impact from live workflow; governance |
| Validation | Dedicated **36 passed**. Focused **206 passed**. Full suite **1190 passed**, 4212 warnings, **746.12s**, exit **0**. Alembic **`f9b0c1d2e3f4 (head)`**. Projects **45–49** and EST-2026-0019 unchanged. |
| Architectural findings | No schema. SEQUENCE consumed from SCH. Waiting is not its own fact. Field and MONITOR money unchanged. Warning law informational / non-blocking. |
| Open decisions | Commit/push. PERF-C. Home Office. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do **not** commit. Do **not** begin PERF-C. |
| Commit | none — not committed |
| Date | 2026-09-17 |

### 2026-09-17 — FG-035 PERF-B engineering implementation (uncommitted)

| Field | Content |
|-------|---------|
| Milestone | FG-035 PERF-B |
| Status | **OPEN / PARTIAL.** PERF-B **IMPLEMENTED / TESTED / NOT LIVE-UAT**. PERF-A remains **SEALED**. No new ADR. No schema. V1 **60% / 4 of 11** **NO RESCORE**. |
| Branch | `main` |
| Base commit | `11a11cb33e8bc7c185557980a1852af66d53b367` |
| Objective | Project Needs Attention derived projection on Hub `#hub-labour`. |
| Deliverables | `assemble_project_attention`; contractor copy; Hub Needs Attention; dedicated tests; Manual Impact; governance docs |
| Validation | Dedicated **36 passed**. Focused **206 passed**. Full suite **1190 passed**, 4212 warnings, **619.11s**, exit **0**. Alembic **`f9b0c1d2e3f4 (head)`**. |
| Architectural findings | No schema. SEQUENCE consumed from SCH. Waiting is not its own fact. Field and MONITOR money unchanged. |
| Open decisions | Live UAT authorization. PERF-C. Home Office. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do **not** commit. Do **not** live-UAT. |
| Commit | none — not committed |
| Date | 2026-09-17 |

### 2026-09-17 — FG-035 PERF-B design freeze sealed (docs-only commit / push)

| Field | Content |
|-------|---------|
| Milestone | FG-035 PERF-B |
| Status | **OPEN / PARTIAL.** PERF-B **IMPLEMENTATION PREFLIGHT COMPLETE / DESIGN FROZEN / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. Owner decisions A–G **ACCEPTED**. PERF-A remains **SEALED**. No new ADR. No schema. V1 **60% / 4 of 11** **NO RESCORE**. |
| Branch | `main` |
| Base commit | `e809dcdbc3735aa91033f968a9ed562e749e6a0c` |
| Objective | Seal accepted PERF-B Project Needs Attention design. Do not implement product. |
| Deliverables | [architecture/fg-035-perf-b-implementation-preflight.md](architecture/fg-035-perf-b-implementation-preflight.md). Minimum index/continuity updates. |
| Validation | Docs-only. Tests **NOT RERUN**. Last accepted full suite **1154 passed**, 0 failed. Alembic unchanged **`f9b0c1d2e3f4 (head)`**. |
| Architectural findings | 80% module constant. SEQUENCE consumed not recalculated. Unassigned not PERF-B. Positive copy: Nothing needs attention right now. Needs Attention above labour summary in `#hub-labour`. No alert table. |
| Open decisions | PERF-B implementation not authorized. |
| Next milestone | **STOP.** PERF-B **NOT IMPLEMENTATION-AUTHORIZED**. |
| Commit | this freeze |
| Date | 2026-09-17 |

### 2026-09-17 — FG-035 PERF-B implementation preflight (docs-only / not committed)

| Field | Content |
|-------|---------|
| Milestone | FG-035 PERF-B |
| Status | **OPEN / PARTIAL.** PERF-B **PREFLIGHT COMPLETE / OWNER DECISIONS REQUIRED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. PERF-A remains **SEALED**. No new ADR. No schema. V1 **60% / 4 of 11** **NO RESCORE**. |
| Branch | `main` |
| Base commit | `e809dcdbc3735aa91033f968a9ed562e749e6a0c` |
| Objective | Freeze PERF-B Project Needs Attention design enough for owner decisions. Do not implement product. |
| Deliverables | [architecture/fg-035-perf-b-implementation-preflight.md](architecture/fg-035-perf-b-implementation-preflight.md). Minimum index/continuity updates. |
| Validation | Docs-only. Tests **NOT RERUN**. Last accepted full suite **1154 passed**, 0 failed. Alembic unchanged **`f9b0c1d2e3f4 (head)`**. |
| Architectural findings | Consume PERF-A labour. Extra Work by current lineage. Schedule date-grain. Reuse SCH conflicts; do not duplicate the engine. No alert table. |
| Open decisions | Owner A–G (80% threshold, finish passed, no-Time start rule, SCH promotion, unassigned, positive state, Hub placement). |
| Next milestone | **STOP.** PERF-B **NOT IMPLEMENTATION-AUTHORIZED**. |
| Commit | none — not committed |
| Date | 2026-09-17 |

### 2026-09-17 — V1 Desktop Contractor Experience / context-aware Home Office product-direction recording

| Field | Content |
|-------|---------|
| Milestone | V1 Desktop Contractor Experience (product-direction recording) |
| Status | **RECORDED / MANDATORY V1 / MANDATORY PRE-BEN/TEAM REAL-WORLD UAT / IMPLEMENTATION SEQUENCED AFTER PERF ATTENTION / NOT IMPLEMENTED.** Context-aware Home Office **RECORDED / NOT IMPLEMENTED**. PERF-A remains **SEALED**. PERF-B / PERF-C **NOT AUTHORIZED**. No new ADR. No new Feature Gate. V1 **60% / 4 of 11** **NO RESCORE**. |
| Branch | `main` |
| Base commit | `618dfaefbff1d5926bafa39c438075dc9c26055b` |
| Objective | Record accepted future V1 desktop direction so it cannot be lost while FG-035 continues. Do not implement product. |
| Deliverables | [architecture/v1-desktop-contractor-experience-product-direction.md](architecture/v1-desktop-contractor-experience-product-direction.md). Minimum index/roadmap/register/continuity updates. |
| Validation | Docs-only. Tests **NOT RERUN**. Last accepted full suite **1154 passed**, 0 failed. Alembic unchanged **`f9b0c1d2e3f4 (head)`**. |
| Architectural findings | Home Office is a calm operational briefing. Context changes emphasis only. Cash awareness, not cash anxiety. Desktop UX audit is broader than Home Office. Ben test not claimed PASS. |
| Open decisions | Home Office implementation. PERF-B. QuickBooks/banking. Print. Help/Voice/Manual. |
| Next milestone | **STOP.** Home Office **NOT AUTHORIZED**. PERF-B **NOT AUTHORIZED**. |
| Commit | this recording |
| Date | 2026-09-17 |

### 2026-09-17 — FG-035 PERF-A CLOSE / COMMIT / SHA-PIN / PUSH

| Field | Content |
|-------|---------|
| Milestone | FG-035 PERF-A |
| Status | **OPEN / PARTIAL.** PERF-A **IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS / COMMITTED / SHA-PINNED / PUSHED**. SCH-D remains **IMPLEMENTED / TESTED / SERVER-SIDE LIVE UAT PASS / PHYSICAL IPHONE UAT PASS / COMMITTED / SHA-PINNED / PUSHED**. SCH overall **OPEN / PARTIAL**. PERF-B / PERF-C / CLOSE / LEARN / QB-T **NOT AUTHORIZED**. [ADR-053](adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**. No new ADR. V1 **60% / 4 of 11** **NO RESCORE**. |
| Branch | `main` |
| Base commit | `8187d88d9a7695d009b4e8610ab2468831ec4fe3` |
| Objective | Commit accepted PERF-A labour Allowed · Used · Remaining on Project Hub. SHA-pin. Push. |
| Deliverables | Product SHA **`7a4b7000e2650eadf68b4ea44d48f75c65830c1f`**. No PERF-A migration. Evidence [testing/fg035-perf-a-live-bounded-uat-record.md](testing/fg035-perf-a-live-bounded-uat-record.md). |
| Validation | Dedicated **14 passed**. Focused **170 passed**. Full suite **1154 passed**, 3873 warnings, **633.10s**, exit **0**. Bounded synthetic live UAT Project **49**. |
| Architectural findings | Activity grain. Used = APPROVED. Waiting = SUBMITTED. Extra Work by current SCOPE lineage. Stale Time `scope_origin` not rewritten. MONITOR money unchanged. Field unchanged. |
| Open decisions | PERF-B. Desktop Contractor Experience / Home Office (not recorded this close). Print. Help/Voice/Manual. |
| Next milestone | **STOP.** PERF-B **NOT AUTHORIZED**. |
| Commit | `7a4b7000e2650eadf68b4ea44d48f75c65830c1f` |
| Date | 2026-09-17 |

### 2026-09-17 — FG-035 SCH-D CLOSE / COMMIT / SHA-PIN / PUSH

| Field | Content |
|-------|---------|
| Milestone | FG-035 SCH-D |
| Status | **OPEN / PARTIAL.** SCH-D **IMPLEMENTED / TESTED / SERVER-SIDE LIVE UAT PASS / PHYSICAL IPHONE UAT PASS / COMMITTED / NOT PUSHED**. SCH overall **OPEN / PARTIAL**. SCH-A / SCH-B / SCH-C remain **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. TAX/WBS / SCOPE / TIME remain **IMPLEMENTED**. Warning law **INFORMATIONAL ONLY / NON-BLOCKING**. Print **RECORDED / IMPLEMENTATION SEQUENCED LATER**. Manual **FRAMEWORK ACTIVE / SCH-D MANUAL IMPACT CURRENT**. Shop / Company Work **RECORDED / NOT IMPLEMENTED**. Banked Hours **RECORDED / NOT IMPLEMENTED**. [ADR-053](adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**. No new ADR. V1 **60% / 4 of 11** **NO RESCORE**. |
| Branch | `main` |
| Base commit | `61a92d0ae1541e1fb70bed1867b0c0a12c6e0a0a` |
| Objective | Preserve Darcy docs. Commit future-direction docs separately. Commit and pin the accepted SCH-D package. Push linear `main`. Do not begin PERF. |
| Deliverables | Product SHA **`59d36b8f0b3a86eb41aee03890cb432d0fc58e52`**. Future-direction SHA **`78ca4f7934495538e2c6c6c256547369577f6258`**. No SCH-D migration. Evidence [testing/fg035-sch-d-live-physical-iphone-uat-record.md](testing/fg035-sch-d-live-physical-iphone-uat-record.md). |
| Validation | Not rerun for this commit. Authoritative post-physical: Dedicated SCH-D **21 passed**. TIME+Field+SCH-D **49 passed**. SCH-A/B/C **36 passed**. Focused **156 passed**. Full suite **1140 passed**, 3749 warnings, **665.58s**, exit **0**. Live current = repository head **`f9b0c1d2e3f4 (head)`**. |
| Architectural findings | No new Schedule store. No Field Schedule POSTs. Directions is phone-maps handoff. Native iOS return accepted. Warning law preserved. |
| Open decisions | PERF / CLOSE / LEARN / QB-T not authorized. V1 remains **60% / 4 of 11**. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do **not** begin PERF. |
| Commit | `59d36b8f0b3a86eb41aee03890cb432d0fc58e52` |
| Date | 2026-09-17 |

### 2026-09-16 — FG-035 SCH-C CLOSE / COMMIT / PUSH

| Field | Content |
|-------|---------|
| Milestone | FG-035 SCH-C |
| Status | **OPEN / PARTIAL.** SCH-C **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS / COMMITTED / PUSHED**. SCH overall **OPEN / PARTIAL**. SCH-D **NOT AUTHORIZED**. SCH-A / SCH-B remain **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. TAX/WBS / SCOPE / TIME remain **IMPLEMENTED**. Warning law **INFORMATIONAL ONLY / NON-BLOCKING**. Print **RECORDED / IMPLEMENTATION SEQUENCED LATER**. Manual **FRAMEWORK ACTIVE / SCH-C MANUAL IMPACT CAPTURED**. [ADR-053](adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**. No new ADR. V1 **60% / 4 of 11** **NO RESCORE**. |
| Branch | `main` |
| Base commit | `d59bc716fa6c1ff2e173107500e6178dc0489a5d` |
| Objective | Commit and push the accepted SCH-C package. Pin product SHA. Do not begin SCH-D. |
| Deliverables | Product SHA **`c57e23c55260b44fc88cadfe2fc40924aa58dde7`**. Additive **`f9b0c1d2e3f4`**. Evidence [testing/fg035-sch-c-live-bounded-uat-record.md](testing/fg035-sch-c-live-bounded-uat-record.md). |
| Validation | Not rerun for this commit. Authoritative post-live-UAT: Dedicated SCH-C **14 passed**. SCH-A+SCH-B **22 passed**. Focused **135 passed**. Full suite **1119 passed**, 3705 warnings, **507.32s**, exit **0**. Live current = repository head **`f9b0c1d2e3f4 (head)`**. |
| Architectural findings | No additional product development during close. `dependency_id` remains Integer with no FK. Warning law preserved. |
| Open decisions | SCH-D not authorized. V1 remains **60% / 4 of 11**. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do **not** begin SCH-D. |
| Commit | `c57e23c55260b44fc88cadfe2fc40924aa58dde7` |
| Date | 2026-09-16 |

### 2026-09-16 — FG-035 SCH-C live migrate + bounded synthetic UAT

| Field | Content |
|-------|---------|
| Milestone | FG-035 SCH-C live migrate + bounded synthetic UAT. Not a V1 rescore. |
| Status | **OPEN / PARTIAL** for FG-035. SCH-C **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. SCH-A / SCH-B remain **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. Warning law **INFORMATIONAL ONLY / NON-BLOCKING**. Print **RECORDED / IMPLEMENTATION SEQUENCED LATER**. Manual **FRAMEWORK ACTIVE / SCH-C MANUAL IMPACT CAPTURED**. V1 **60% / 4 of 11** **NO RESCORE**. |
| Branch | `main` |
| Base commit | `d59bc716fa6c1ff2e173107500e6178dc0489a5d` |
| Objective | Apply `f9b0c1d2e3f4`, create one synthetic SCH-C Project, prove work-order / warning-law / retirement, run fresh tests. Do not commit. |
| Deliverables | Live current = repository head **`f9b0c1d2e3f4`**. Project **47**. [testing/fg035-sch-c-live-bounded-uat-record.md](testing/fg035-sch-c-live-bounded-uat-record.md). |
| Validation | Dedicated SCH-C **14 passed**. SCH-A+SCH-B **22 passed**. Focused **135 passed**. Full suite **1119 passed**, 3705 warnings, **507.32s**, exit **0**. |
| Architectural findings | Cycle remains validation. Sequence / predecessor-unscheduled remain informational. KEEP / MOVE / REVIEW remain optional. `f9b0c1d2e3f4` preserved. |
| Open decisions | SCH-D. Print implementation. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do **not** begin SCH-D. |
| Commit | `c57e23c55260b44fc88cadfe2fc40924aa58dde7`
| Date | 2026-09-16 |

### 2026-09-16 — FG-035 SCH-C Lightweight Element dependencies + sequence warnings

| Field | Content |
|-------|---------|
| Milestone | FG-035 SCH-C Lightweight Element dependencies + sequence warnings. Not a V1 rescore. |
| Status | **OPEN / PARTIAL** for FG-035. SCH-C **IMPLEMENTED / TESTED / NOT LIVE-MIGRATED**. SCH-A / SCH-B remain **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. Warning law **INFORMATIONAL ONLY / NON-BLOCKING**. Print **RECORDED / IMPLEMENTATION SEQUENCED LATER**. V1 **60% / 4 of 11** **NO RESCORE**. |
| Branch | `main` |
| Base commit | `d59bc716fa6c1ff2e173107500e6178dc0489a5d` (User Guide framework). Prior pin `bad182d0d85e51584260988f2887b481333660df`. |
| Objective | Implement SCH-C Element→Element dependencies and informational sequence warnings. Do not live-migrate. Do not live-UAT. Do not commit. |
| Deliverables | `ProjectWorkDependency`; `app/services/schedule.py` create/retire/cycle/warnings; Company/Hub work-order UX; Element-retirement edge cleanup; additive **`f9b0c1d2e3f4`**; `tests/test_work_schedule_dependency_fg035.py`; required docs. |
| Validation | Resume/verify 16 Sep 2026: Dedicated SCH-C **14 passed**, 32 warnings, **4.48s**. SCH-A+SCH-B **22 passed**, 57 warnings, **10.42s**. Focused **135 passed**, 540 warnings, **60.21s**. Full suite **1119 passed**, 3705 warnings, **453.73s**, exit **0**. Live DB not upgraded. |
| Architectural findings | Expected Alembic token `f8a9b0c1d2e3` collides with FG-016; minted **`f9b0c1d2e3f4`**. Warnings do not block Save. KEEP / MOVE / REVIEW are optional. |
| Open decisions | SCH-C live migrate / bounded synthetic UAT (later completed). SCH-D. Print implementation. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do **not** live-migrate. Do **not** begin live UAT. Do **not** commit unless separately authorized. |
| Commit | `c57e23c55260b44fc88cadfe2fc40924aa58dde7`
| Date | 2026-09-16 |

### 2026-09-16 — Platform-wide warning law + Print product-direction recording

| Field | Content |
|-------|---------|
| Milestone | Product-direction recording (Print + warning law). Not a coded FG-035 slice. |
| Status | **OPEN / PARTIAL** for FG-035. Warning law **INFORMATIONAL ONLY / NON-BLOCKING / PLATFORM-WIDE**. Print **RECORDED / IMPLEMENTATION SEQUENCED LATER**. SCH-C **PREFLIGHT PASS / NOT IMPLEMENTED**. SCH-A / SCH-B remain **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. V1 **60% / 4 of 11** **NO RESCORE**. |
| Branch | `main` |
| Base commit | `36cdddcfe10151b5f5d2fd5b00406e0dedd0ead7` |
| Objective | Fold the platform-wide warning law into the already-authorized docs-only Print recording, then commit and push. |
| Deliverables | Canonical [architecture/project-element-authority-future-record.md](architecture/project-element-authority-future-record.md). Minimum SCH freeze/architecture pointers. Continuity. |
| Validation | Docs-only. `git diff --check`. No app/tests/migrations/DB mutation. Authoritative SCH-B post-live-UAT full suite **1105 passed**. |
| Architectural findings | Warnings inform; humans decide. Validation remains fail-closed. KEEP / MOVE / REVIEW are optional contractor affordances, not persisted states. Architecture-principles numbered rules unchanged (no Rule 13; no ADR). |
| Open decisions | SCH-C product not authorized. Print implementation sequenced later. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do **not** begin SCH-C product. |
| Commit | `884aae30d845b9cf4cac3e0be2de454b4da2cfe8` |
| Date | 2026-09-16 |

### 2026-09-16 — FG-035 SCH-B CLOSE / COMMIT / PUSH

| Field | Content |
|-------|---------|
| Milestone | FG-035 SCH-B |
| Status | **OPEN / PARTIAL.** SCH-B **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS / COMMITTED / PUSHED**. SCH overall **OPEN / PARTIAL**. SCH-C / SCH-D **NOT AUTHORIZED**. SCH-A remains **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. TAX/WBS / SCOPE / TIME remain **IMPLEMENTED**. [ADR-053](adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**. No new ADR. |
| Branch | `main` |
| Base commit | `d3352509b708482ac9bbacce8cea0860b2d8cfcf` |
| Objective | Commit and push the accepted SCH-B package. Pin product SHA. Do not begin SCH-C. |
| Deliverables | Product SHA **`374798d7338a4c00d90a9c7a2b2efa310bc7e355`**. Additive **`f7f8a9b0c1d2`**. Evidence [testing/fg035-sch-b-live-bounded-uat-record.md](testing/fg035-sch-b-live-bounded-uat-record.md). |
| Validation | Not rerun for this commit. Authoritative post-live-UAT: Dedicated SCH-B **9 passed**. Dedicated SCH-A **13 passed**. Focused **121 passed**. Full suite **1105 passed**, 3673 warnings, **450.77s**, exit **0**. Live current = repository head **`f7f8a9b0c1d2 (head)`**. |
| Architectural findings | No additional product development during close. History `assignment_id` remains Integer with no FK. |
| Open decisions | SCH-C not authorized. V1 remains **60% / 4 of 11**. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do **not** begin SCH-C. |
| Commit | `374798d7338a4c00d90a9c7a2b2efa310bc7e355` |
| Date | 2026-09-16 |

### 2026-09-16 — FG-035 SCH-B live migrate + bounded synthetic UAT

| Field | Content |
|-------|---------|
| Milestone | FG-035 SCH-B |
| Status | **OPEN / PARTIAL.** SCH-B **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. SCH overall **OPEN / PARTIAL**. SCH-C / SCH-D **NOT AUTHORIZED**. SCH-A remains **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. TAX/WBS / SCOPE / TIME remain **IMPLEMENTED**. [ADR-053](adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**. No new ADR. |
| Branch | `main` |
| Base commit | `d3352509b708482ac9bbacce8cea0860b2d8cfcf` |
| Objective | Apply SCH-B live migration and prove bounded synthetic office UAT on a new vessel without mutating Project 45 or EST-2026-0019. |
| Deliverables | Live upgrade `f6e7f8a9b0c1` → **`f7f8a9b0c1d2`**. Backup `instance/brayman_estimator-backup-before-fg035-sch-b-f7f8a9b0c1d2-20260916-062918.db`. Synthetic Project **46**. Authoritative [testing/fg035-sch-b-live-bounded-uat-record.md](testing/fg035-sch-b-live-bounded-uat-record.md). Governance LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS. |
| Validation | Dedicated SCH-B **9 passed**, 26 warnings, **6.28s**. Dedicated SCH-A **13 passed**, 31 warnings, **3.85s**. Focused TAX/WBS+SCOPE+TIME+SCH-A+SCH-B+Hub/Field/MONITOR **121 passed**, 508 warnings, **54.70s**. Full suite **1105 passed**, 3673 warnings, **450.77s**, exit **0**. Live current = repository head **`f7f8a9b0c1d2 (head)`**. |
| Architectural findings | USER XOR Crew. Zero rows = Unassigned. History `assignment_id` remains Integer with no FK (SQLite reused assignment id 8 after delete). Item retire unassigns then retires in the same transaction. Crew membership evaluated against the scheduled window. Conflicts are a read projection. USER-THROUGH-CREW detected when membership overlaps the scheduled window; no false historical conflict when membership begins after the window. |
| Open decisions | SCH-C not authorized. V1 remains **60% / 4 of 11**. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do **not** begin SCH-C. |
| Commit | `374798d7338a4c00d90a9c7a2b2efa310bc7e355` |
| Date | 2026-09-16 |

### 2026-09-16 — FG-035 SCH-B Assignment + optional Crew implementation

| Field | Content |
|-------|---------|
| Milestone | FG-035 SCH-B |
| Status | **OPEN / PARTIAL.** SCH-B **IMPLEMENTED / TESTED / NOT LIVE-MIGRATED**. Live UAT **NOT YET PERFORMED**. SCH overall **OPEN / PARTIAL**. SCH-C / SCH-D **NOT AUTHORIZED**. SCH-A remains **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. TAX/WBS / SCOPE / TIME remain **IMPLEMENTED**. [ADR-053](adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**. No new ADR. |
| Branch | `main` |
| Base commit | `d3352509b708482ac9bbacce8cea0860b2d8cfcf` |
| Objective | Implement SCH-B WHO on the existing SCH-A WHEN without live migration or live UAT. |
| Deliverables | `WorkScheduleAssignment`; `OrganizationCrew` / `OrganizationCrewMember`; `app/services/organization_crew.py`; dedicated `/settings/crews`; assignment POST routes; overlap projection; additive Alembic **`f7f8a9b0c1d2`**; `tests/test_work_schedule_assignment_fg035.py`; FG-035 / ADR-053 / continuity |
| Validation | Dedicated SCH-B **9 passed**, 26 warnings, **6.28s**. Focused TAX/WBS+SCOPE+TIME+SCH-A+SCH-B+Hub/Field/MONITOR **121 passed**, 508 warnings, **53.45s**. Full suite **1105 passed**, 3673 warnings, **445.16s**, exit **0**. Live `flask db current` remained **`f6e7f8a9b0c1`** (no longer Alembic head). |
| Architectural findings | USER XOR Crew. Zero rows = Unassigned. History `assignment_id` remains Integer with no FK. Item retire unassigns then retires in the same transaction. Crew membership evaluated against the scheduled window. Conflicts are a read projection. New SCH-B POST forms use CSRF; SCH-A forms were not swept. |
| Open decisions | Live migrate / live UAT not authorized. V1 remains **60% / 4 of 11**. |
| Next milestone | **STOP.** Return to ChatGPT Architect for live-migrate / UAT authorization. |
| Commit | `374798d7338a4c00d90a9c7a2b2efa310bc7e355` |
| Date | 2026-09-16 |

### 2026-09-15 — FG-035 SCH-A existing live-UAT reconciliation + completion

| Field | Content |
|-------|---------|
| Milestone | FG-035 SCH-A |
| Status | **OPEN / PARTIAL.** SCH-A **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. SCH overall **OPEN / PARTIAL**. SCH-B / SCH-C / SCH-D **NOT AUTHORIZED**. TAX/WBS / SCOPE / TIME remain **IMPLEMENTED**. [ADR-053](adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**. No new ADR. |
| Branch | `main` |
| Base commit | `94fc575a720751dadb36f9df70ae85f40b9680d3` |
| Objective | Preserve existing live f6 / Project 45. Reconstruct durable evidence. Complete only unprovable UAT steps. Fresh post-UAT tests. Authoritative UAT record. |
| Deliverables | [testing/fg035-sch-a-live-bounded-uat-record.md](testing/fg035-sch-a-live-bounded-uat-record.md); FG-035 / ADR-053 / continuity updates. No second migration. No second UAT project. |
| Validation | Dedicated SCH-A **13 passed**, 31 warnings, **4.12s**. Focused TAX/WBS+SCOPE+TIME+SCH-A+Hub/Field/MONITOR **112 passed**, 482 warnings, **51.94s**. Full suite **1096 passed**, 3647 warnings, **514.43s**, exit **0**. Live `flask db current` **`f6e7f8a9b0c1 (head)`**. |
| Architectural findings | Live migration proven/reconciled from backup `f5d6e7f8a9b0` vs live `f6e7f8a9b0c1`. This reconciliation did **not** apply the migration. Window integrity FAIL CLOSED re-proven on Project 45. |
| Open decisions | SCH-B not authorized. V1 remains **60% / 4 of 11**. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do **not** begin SCH-B. |
| Commit | `fd8a66990df8286e54151b80b6f3cd5be5dd3ad1` |
| Date | 2026-09-15 |

### 2026-09-15 — FG-035 SCH-A Schedule Core implementation

| Field | Content |
|-------|---------|
| Milestone | FG-035 SCH-A |
| Status | **OPEN / PARTIAL.** SCH-A **IMPLEMENTED / TESTED / NOT LIVE-MIGRATED**. Live UAT **NOT YET PERFORMED**. SCH overall **NOT CLOSED**. SCH-B / SCH-C / SCH-D **NOT AUTHORIZED**. TAX/WBS / SCOPE / TIME remain **IMPLEMENTED**. [ADR-053](adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**. No new ADR. |
| Branch | `main` |
| Base commit | `94fc575a720751dadb36f9df70ae85f40b9680d3` |
| Objective | Implement SCH-A Schedule Core without live migration or live UAT. |
| Deliverables | `WorkScheduleItem` / `WorkScheduleHistory`; `app/services/schedule.py`; `/schedule`; Hub `#hub-schedule`; additive Alembic **`f6e7f8a9b0c1`**; `tests/test_work_schedule_fg035.py`; FG-035 / ADR-053 / continuity |
| Validation | Dedicated SCH-A **13 passed**, 31 warnings, **3.77s**. Focused TAX/WBS+SCOPE+TIME+Hub/Field/MONITOR **99 passed**, 451 warnings, **43.00s**. Full suite **1096 passed**, 3647 warnings, **413.66s**, exit **0**. Live `flask db current` remained **`f5d6e7f8a9b0`**. |
| Architectural findings | Overlay on Project work. One current scheduled window. Project range derived. Activity-inside-Element invariant. Schedule does not create Time. |
| Open decisions | Live migrate / live UAT not authorized. V1 remains **60% / 4 of 11**. |
| Next milestone | **STOP.** Return to ChatGPT Architect for live-migrate / UAT authorization. |
| Commit | `fd8a66990df8286e54151b80b6f3cd5be5dd3ad1` |
| Date | 2026-09-15 |

### 2026-09-15 — FG-035 SCH implementation preflight / design freeze

| Field | Content |
|-------|---------|
| Milestone | FG-035 SCH implementation freeze |
| Status | **OPEN / PARTIAL.** SCH **IMPLEMENTATION PREFLIGHT COMPLETE / DESIGN FROZEN / NOT IMPLEMENTATION-AUTHORIZED**. TAX/WBS / SCOPE / TIME remain **IMPLEMENTED**. PERF / CLOSE / LEARN / QB-T **NOT AUTHORIZED**. [ADR-053](adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**. No new ADR. |
| Branch | `main` |
| Base commit | `75d0655df8513ccfcddaccc9bb4d3a2811dbfd8b` |
| Objective | Freeze SCH names, constraints, slices, and SCH-A test matrix without implementing Schedule. |
| Deliverables | [architecture/fg-035-sch-implementation-preflight.md](architecture/fg-035-sch-implementation-preflight.md); FG-035 / ADR-053 / continuity pointers |
| Validation | Docs only. `git diff --check`. Product tests **NOT RERUN**. Historical TIME full suite **1083 passed**. |
| Architectural findings | `scheduled_start` / `scheduled_end`. Window integrity is validation. SCH-A first. Crew period membership SCH-B. Element-only DAG SCH-C. |
| Open decisions | SCH-A implementation not authorized. V1 remains **60% / 4 of 11**. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Bounded SCH-A implementation — **NOT AUTHORIZED FROM THIS RECORD**. |
| Commit | (pending Joel commit) |
| Date | 2026-09-15 |

### 2026-09-15 — FG-035 SCH Dynamic Scheduling architecture recording

| Field | Content |
|-------|---------|
| Milestone | FG-035 SCH architecture |
| Status | **OPEN / PARTIAL.** SCH **PREFLIGHT COMPLETE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. TAX/WBS / SCOPE / TIME remain **IMPLEMENTED**. PERF / CLOSE / LEARN / QB-T **NOT AUTHORIZED**. [ADR-053](adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**. No new ADR. |
| Branch | `main` |
| Base commit | `4f99a31f50aeb9639fb2889ad56825e09320a692` |
| Objective | Record accepted SCH overlay architecture (data model and contractor workflow) without implementing Schedule. |
| Deliverables | [architecture/fg-035-sch-dynamic-scheduling-preflight.md](architecture/fg-035-sch-dynamic-scheduling-preflight.md); FG-035 / ADR-053 / continuity pointers |
| Validation | Docs only. `git diff --check`. Product tests **NOT RERUN**. Historical TIME full suite **1083 passed**. |
| Architectural findings | Overlay on existing Project work. One current scheduled window. Element grain default. Project bar derived. Optional Crew with period membership truth. Activity window integrity is a confirmed same-action constraint. |
| Open decisions | SCH implementation not authorized. Crew effective-dating belongs to implementation preflight. V1 remains **60% / 4 of 11**. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Bounded SCH implementation authorization / preflight — **NOT AUTHORIZED FROM THIS RECORD**. |
| Commit | (pending Joel commit) |
| Date | 2026-09-15 |

### 2026-09-15 — FG-035 TIME field duration entry + approval + approved labour actuals

| Field | Content |
|-------|---------|
| Milestone | FG-035 TIME |
| Status | **OPEN / PARTIAL.** TIME **IMPLEMENTED / LIVE-MIGRATED / SYNTHETIC UAT PASS**. SCH / PERF / CLOSE / LEARN / QB-T **NOT AUTHORIZED**. [ADR-053](adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**. |
| Branch | `main` |
| Base commit | `82a2e750c4fc0915b7db648ca44a52912760b0db` |
| Objective | Duration-based labour Time Entry with SCOPE inheritance, Extra Work, approval, and approved labour actuals. |
| Deliverables | `labour_time_entries` + `labour_time_history`; Field Time / My time; office `/time`; Hub Time; `approved_labour_hours()`; additive `f5d6e7f8a9b0`; synthetic UAT project **44** |
| Validation | Dedicated TIME included in focused TIME+SCOPE+TAX/WBS **31 passed**, 278 warnings, **16.29s**. Hub/Field/MONITOR+TIME **76 passed**, 258 warnings, **35.03s**. Full suite **1083 passed**, 3616 warnings, **466.85s**, exit **0**. Synthetic UAT **PASS**. Occupancy EST-2026-0019 unchanged. PRODUCTION packages **0**. |
| Architectural findings | No Draft. Online-session Time only. Self-approval fail-closed. Money actuals remain `ProjectDirectCostActual`. |
| Open decisions | SCH / PERF remain unauthorized. Physical iPhone Time UAT deferred. |
| Next milestone | SCH — **NOT AUTHORIZED FROM THIS RECORD** |
| Commit | `03c074fb1eb2bbca77ba86e495726c0e042c1979` |
| Date | 2026-09-15 |

### 2026-09-15 — FG-035 SCOPE original / Change Order / Extra Work lineage

| Field | Content |
|-------|---------|
| Milestone | FG-035 SCOPE |
| Status | **OPEN / PARTIAL.** SCOPE **IMPLEMENTED / LIVE-MIGRATED / SYNTHETIC UAT PASS**. TIME / SCH / PERF / CLOSE / LEARN / QB-T **NOT AUTHORIZED**. [ADR-053](adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**. |
| Branch | `main` |
| Base commit | `26f675cd4982a92f823d1e3b34d16d92b6eb589c` |
| Objective | Original scope immutable; Change Orders modify current authorized Project work; Extra Work before CO. |
| Deliverables | `scope_origin` + CO refs; `project_work_scope_deltas`; append-only history; Hub/Field Extra work; additive `f4c5d6e7f8a9`; synthetic UAT project **43** |
| Validation | Dedicated SCOPE **10 passed**. Focused **23 passed**. Full suite **1075 passed**, 3531 warnings, **437.62s**. Live migrate **PASS**. EST-2026-0019 unchanged. PRODUCTION packages **0**. |
| Architectural findings | ChangeOrder remains commercial SoR. Original hours never overwritten. Draft CO cannot authorize Project scope. Ambiguous PROJECT-created work fail-closed EXTRA_WORK. |
| Open decisions | TIME / SCH not authorized. Physical iPhone Extra work UAT **DEFERRED**. V1 remains **60% / 4 of 11**. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do **not** begin TIME / SCH from this note. |
| Commit | `21bf0eba47acdb19eb292c2319d675a1748c1dff` |
| Date | 2026-09-15 |

### 2026-09-15 — Help / Voice / User Manual §§40–60 close

| Field | Content |
|-------|---------|
| Milestone | Help / Voice / User Manual product-direction close |
| Status | **FUTURE / RECORDED / COMPLETE FOR PRODUCT-DIRECTION RECORDING / MANDATORY PRE-UAT V1 / NOT IMPLEMENTATION-AUTHORIZED.** |
| Branch | `main` |
| Base commit | `040e94d4f87b218bea514238322236835e2eb825` |
| Objective | Close the Help / Voice / User Manual future record through §60. |
| Deliverables | Canonical future-record §§40–60; PRE-UAT RELEASE GATE; minimum continuity |
| Validation | Docs only. `git diff --check`. Tests **NOT RERUN**. |
| Architectural findings | Help content quality/versioning/source-priority. Manual visual/procedure standards. Independent UAT blocked until §52 gate. |
| Open decisions | None from this close. V1 remains **60% / 4 of 11**. FG-035 SCOPE **not authorized**. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do **not** begin SCOPE. |
| Commit | `d3079ffeec728f743195ae3e443a2dc7e41e599f` |
| Date | 2026-09-15 |

### 2026-09-15 — Help / Voice / User Manual §§26–39

| Field | Content |
|-------|---------|
| Milestone | Help / Voice / User Manual §§26–39 continuation |
| Status | **FUTURE / RECORDED THROUGH §39 / NOT IMPLEMENTATION-AUTHORIZED.** Task-based pre-UAT script **REQUIRED**. Does **not** interrupt FG-035. |
| Branch | `main` |
| Base commit | `d01d3d06086d7dc4ffe57537e64d3547e8ae5057` |
| Objective | Complete truncated §26 and record §§27–39. |
| Deliverables | Canonical future-record §§26–39; minimum continuity |
| Validation | Docs only. `git diff --check`. Tests **NOT RERUN**. |
| Architectural findings | No-coaching UAT. Manual-first. Physical device evidence for iPhone PASS. Voice mutation not required for V1 Voice. |
| Open decisions | None from §§26–39. V1 remains **60% / 4 of 11**. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do **not** implement Help / Voice / Manual. Do **not** begin SCOPE. |
| Commit | `872f5ec377740bdccedcf30f2c81324b6e59e48d` |
| Date | 2026-09-15 |

### 2026-09-15 — Help / Voice / User Manual PRE-UAT record

| Field | Content |
|-------|---------|
| Milestone | Help / Voice / professional User Manual product-direction record |
| Status | **FUTURE / RECORDED / MANDATORY PRE-UAT V1 / NOT IMPLEMENTATION-AUTHORIZED.** Does **not** interrupt FG-035. |
| Branch | `main` |
| Base commit | `3d3a225edeac276e681ee18dd43ab18fff81d466` (FG-035 TAX/WBS SHA pin) |
| Objective | Record Interactive Help, Voice, and a professional User Guide as mandatory before Ben / father-in-law / Kevin real-world UAT. |
| Deliverables | [architecture/interactive-help-voice-and-user-manual-future-record.md](architecture/interactive-help-voice-and-user-manual-future-record.md); continuity indexes |
| Validation | Docs only. No product tests. No Alembic. EST-2026-0019 unchanged. |
| Architectural findings | One User Help Content authority. Voice mutation fail-closed. Language audit precedes final manual. |
| Open decisions | Task-based pre-UAT script question received / not decided. §26 truncated. V1 remains **60% / 4 of 11**. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do **not** implement Help / Voice / Manual. Do **not** begin SCOPE / TIME / SCH. |
| Commit | `2511fc55921a84bcb3618e9ce754ab9b33a38e81` |
| Date | 2026-09-15 |

### 2026-09-15 — FG-035 TAX/WBS project work structure

| Field | Content |
|-------|---------|
| Milestone | FG-035 TAX/WBS |
| Status | **OPEN / PARTIAL.** TAX/WBS **IMPLEMENTED / LIVE-MIGRATED / SYNTHETIC UAT PASS**. Later slices **NOT AUTHORIZED**. [ADR-053](adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**. |
| Branch | `main` |
| Base commit | `97719937f28c62956b2e08803cfd06f46d31224c` (FG-034 AUTH-D close) |
| Objective | Foundational Project work-structure authority for the closed operational / learning loop. |
| Deliverables | FG-035; ADR-053; additive `f3b4c5d6e7f8`; catalog + Hub Project work; synthetic UAT project **42** |
| Validation | Dedicated **13 passed**. Focused **98 passed**. Full suite **1065 passed**, 3403 warnings, **456.75s**. EST-2026-0019 unchanged. PRODUCTION packages **0**. |
| Architectural findings | Three-layer taxonomy. Explicit locked snapshot seed. LabourTask not merged. Commercial project_type unchanged. |
| Open decisions | Later slice authorization. V1 remains **60% / 4 of 11**. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do **not** begin SCOPE / TIME / SCH from this note. |
| Commit | `c8c01269ecbb30f6920c44af9c503eb73eec6e92` |
| Date | 2026-09-15 |

### 2026-09-15 — FG-034 AUTH-D complete Account Recovery + transactional email close

| Field | Content |
|-------|---------|
| Milestone | FG-034 AUTH-D |
| Status | **CLOSED / OPERATIONAL FOR UAT.** [FG-034](feature-gates/FG-034-account-recovery-and-transactional-email.md) **CLOSED / OPERATIONAL FOR UAT**. MAIL-A / AUTH-A / AUTH-B / AUTH-C / MAIL-B / AUTH-D **IMPLEMENTED / PASS**. Live Postmark **DEFERRED — PROVIDER CONFIGURATION REQUIRED / NOT CLAIMED AS PASS**. |
| Branch | `main` |
| Base commit | `84d32f27433363597eb12008e95932148ffe1b8a` (future-record close); product MAIL-B `6dfc2e940456cf9c292c700e07840fac5d871df4` |
| Objective | Prove complete Account Recovery + transactional email + Native Signing delivery; activate Postmark HTTP adapter; close FG-034. |
| Deliverables | Postmark HTTP adapter; AUTH-D tests; synthetic UAT; FG-034 closure docs |
| Validation | Dedicated AUTH-D **12 passed**. Focused **185 passed**, 356 warnings, **117.94s**. Full suite **1052 passed**, 3338 warnings, **434.60s**. Alembic **`f2a3b4c5d6e7`**. EST-2026-0019 unchanged. PRODUCTION packages **0**. |
| Architectural findings | One engine. Missing Postmark token → `FAILED_CONFIG`. Never `DELIVERED`. Physical iPhone UAT deferred. |
| Open decisions | Live Postmark token / sender domain; physical iPhone UAT; PRODUCTION legal package. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do **not** send live Postmark from this note. Do **not** implement Time / Schedule. Do **not** rescore V1. |
| Commit | this AUTH-D product commit |
| Date | 2026-09-15 |

### 2026-09-15 — §105 sequencing completion + future-record close

| Field | Content |
|-------|---------|
| Milestone | Future record only (not a coded milestone) |
| Status | **RECORDED / COMPLETE FOR PRODUCT-DIRECTION RECORDING / NOT IMPLEMENTATION-AUTHORIZED.** MAIL-B remains **IMPLEMENTED / PASS**. AUTH-D **NOT STARTED**. |
| Branch | `main` |
| Objective | Close the truncated §105 sequence and mark the future product-direction record complete. |
| Deliverables | [architecture/project-element-authority-future-record.md](architecture/project-element-authority-future-record.md) §105 steps 9–13. |
| Validation | Docs-only. No product tests re-run. Last MAIL-B full suite **1040 passed**. EST-2026-0019 occupancy unchanged. |
| Architectural findings | Sequence now ends: final E2E regression → V1 governance audit → V1 rescore → production-readiness review → V1 close. |
| Open decisions | AUTH-D; later Architect preflight of the loop. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do **not** begin AUTH-D. |
| Date | 2026-09-15 |

### 2026-09-15 — §72 remainder + LEARN/alerts/UAT/sequencing final continuation

| Field | Content |
|-------|---------|
| Milestone | Future record only (not a coded milestone) |
| Status | **RECORDED / NOT IMPLEMENTATION-AUTHORIZED.** MAIL-B remains **IMPLEMENTED / PASS**. AUTH-D **NOT STARTED**. |
| Branch | `main` |
| Objective | Complete remaining §72 checklist and record LEARN/alerts/UAT/sequencing without implementing them. |
| Deliverables | [architecture/project-element-authority-future-record.md](architecture/project-element-authority-future-record.md) remainder of §72; §§73–104; §105 through **8. CORRECT**. |
| Validation | Docs-only. No product tests re-run. Last MAIL-B full suite **1040 passed**. EST-2026-0019 occupancy unchanged. |
| Architectural findings | Like-with-like LEARN comparability. Organization-specific evidence. One alert engine. Field simplicity. Language audit close criterion remains YES. |
| Open decisions | Remainder of §105 after 8. CORRECT; later Architect preflight; AUTH-D. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do **not** begin AUTH-D. |
| Date | 2026-09-15 |

### 2026-09-15 — Change Order / Extra Work / Closeout future-record continuation

| Field | Content |
|-------|---------|
| Milestone | Future record only (not a coded milestone) |
| Status | **RECORDED / NOT IMPLEMENTATION-AUTHORIZED.** MAIL-B remains **IMPLEMENTED / PASS**. AUTH-D **NOT STARTED**. |
| Branch | `main` |
| Objective | Complete the truncated Change Order / Extra Work / Closeout / LEARN data-quality rules without implementing them. |
| Deliverables | [architecture/project-element-authority-future-record.md](architecture/project-element-authority-future-record.md) §§40–71. §72 checklist recorded as received (truncated after Closeout performance review). |
| Validation | Docs-only. No product tests re-run. Last MAIL-B full suite **1040 passed**. EST-2026-0019 occupancy unchanged. |
| Architectural findings | Original scope immutable. Three performance views. Extra Work is a field flag. Lineage belongs to work structure. Closeout is LEARN eligibility gate. |
| Open decisions | Remainder of §72; later Architect preflight; AUTH-D; close-block vs warning at Closeout. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do **not** begin AUTH-D. |
| Date | 2026-09-15 |

### 2026-09-15 — Complete Time / Schedule / Performance / LEARN product-direction record

| Field | Content |
|-------|---------|
| Milestone | Future record only (not a coded milestone) |
| Status | **RECORDED / NOT IMPLEMENTATION-AUTHORIZED.** MAIL-B remains **IMPLEMENTED / PASS**. AUTH-D **NOT STARTED**. |
| Branch | `main` |
| Objective | Preserve the complete closed operational / learning loop and the mandatory Contractor Language + UX E2E Audit without implementing them. |
| Deliverables | [architecture/project-element-authority-future-record.md](architecture/project-element-authority-future-record.md) complete 15 Sep 2026 consolidation. Prompt truncated at §40. |
| Validation | Docs-only. No product tests re-run. Last MAIL-B full suite **1040 passed**. EST-2026-0019 occupancy unchanged. |
| Architectural findings | One loop, not unrelated features. Same Project / Element / Activity for Schedule and Time. No CalibraytAI fork per contractor. Language audit is later V1 closure, not FG-025 reopen. |
| Open decisions | Remainder of §40+ (Change Order / Extra Work / Closeout detail); later Architect preflight; AUTH-D; V1 vs later for MONITOR forecast expansion. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do **not** begin AUTH-D. |
| Date | 2026-09-15 |

### 2026-09-15 — FG-034 MAIL-B Native Signing transactional delivery

| Field | Content |
|-------|---------|
| Milestone | FG-034 MAIL-B |
| Status | **PARTIAL.** [FG-034](feature-gates/FG-034-account-recovery-and-transactional-email.md) **OPEN / PARTIAL**. MAIL-A **IMPLEMENTED**. AUTH-A **IMPLEMENTED**. AUTH-B **IMPLEMENTED / PASS**. AUTH-C **IMPLEMENTED / PASS**. MAIL-B **IMPLEMENTED / PASS**. AUTH-D **NOT STARTED**. |
| Branch | `main` |
| Objective | Connect Native Signing invitation/resend/complete to the existing MAIL-A engine without changing `/sign` ceremony or adding a schema. |
| Deliverables | `app/services/signing_mail.py`; MAIL-A templates for invitation/resend/complete; office Email captured for testing overlay; dedicated MAIL-B tests; [testing/fg034-mail-b-native-signing-delivery-record.md](testing/fg034-mail-b-native-signing-delivery-record.md). Visual Schedule addendum recorded only in [architecture/project-element-authority-future-record.md](architecture/project-element-authority-future-record.md). |
| Validation | Dedicated MAIL-B **9 passed**. Focused MAIL-B + MAIL-A/AUTH-A + AUTH-B + AUTH-C + FG-018 + SIGN-A–E **173 passed**, 338 warnings, **107.18s**. Full suite **1040 passed**, 3320 warnings, **376.12s**, exit **0**. Alembic current = heads `f2a3b4c5d6e7`. EST-2026-0019 occupancy unchanged. Live PRODUCTION packages **0**. No new migration. |
| Architectural findings | Signing consumes MAIL-A. SENT remains invitation-issued. `TransactionalMessage` is delivery authority. Copyable URL retained. Mail failure does not roll back SENT or EXECUTED. No INVITATION_EMAIL_* signing events (CHECK constraint). Live contract invitation blocked by converter unavailability; automated contract path PASS. |
| Open decisions | AUTH-D close; Postmark token / sender domain; physical iPhone UAT; PRODUCTION legal package. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do **not** begin AUTH-D. |
| Date | 2026-09-15 |

### 2026-09-15 — FG-034 AUTH-C complete Account Recovery E2E

| Field | Content |
|-------|---------|
| Milestone | FG-034 AUTH-C |
| Status | **PARTIAL.** [FG-034](feature-gates/FG-034-account-recovery-and-transactional-email.md) **OPEN / PARTIAL**. MAIL-A **IMPLEMENTED**. AUTH-A **IMPLEMENTED**. AUTH-B **IMPLEMENTED / PASS**. AUTH-C **IMPLEMENTED / PASS**. MAIL-B, AUTH-D **NOT STARTED**. |
| Branch | `main` |
| Objective | Complete Account Recovery as one local product: public flow, MAIL-A capture, token consume, session invalidation, and security failure paths. |
| Deliverables | Bounded MAIL-A transport-exception wrap; dedicated AUTH-C tests; synthetic UAT user `authc-uat@example.invalid` (id 7, epoch 1 after reset); [testing/fg034-auth-c-complete-e2e-record.md](testing/fg034-auth-c-complete-e2e-record.md). |
| Validation | Dedicated AUTH-C **10 passed**. Focused AUTH-C + AUTH-B + MAIL-A/AUTH-A + FG-018 + SIGN-A–E **164 passed**, 318 warnings, **96.83s**. Full suite **1031 passed**, 3300 warnings, **395.54s**, exit **0**. Alembic current = heads `f2a3b4c5d6e7`. EST-2026-0019 occupancy unchanged. Live PRODUCTION packages **0**. No new migration. |
| Architectural findings | AUTH-C is integration/proof, not new architecture. Public confirmation stays generic on known, unknown, inactive, rate-limited, and provider-failure paths. Transport exceptions become durable FAILED / TRANSPORT_ERROR. |
| Open decisions | MAIL-B Native Signing mail; Postmark token / sender domain; AUTH-D close; physical iPhone Account Recovery UAT. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do **not** begin MAIL-B. |
| Date | 2026-09-15 |

### 2026-09-15 — FG-034 AUTH-B responsive Forgot Password / Reset UX

| Field | Content |
|-------|---------|
| Milestone | FG-034 AUTH-B |
| Status | **PARTIAL.** [FG-034](feature-gates/FG-034-account-recovery-and-transactional-email.md) **OPEN / PARTIAL**. MAIL-A **IMPLEMENTED**. AUTH-A **IMPLEMENTED**. AUTH-B **IMPLEMENTED / PASS**. AUTH-C, MAIL-B, AUTH-D **NOT STARTED**. |
| Branch | `main` |
| Objective | Responsive Forgot Password / Reset browser UX on AUTH-A, with desktop + iPhone functional parity on one system. |
| Deliverables | Login Forgot Password link; `/forgot-password` + `/forgot-password/sent`; `/reset-password/<credential>` + `/reset-password/complete`; `app/static/css/auth.css`; public-route exemptions; dedicated AUTH-B tests; [testing/fg034-auth-b-responsive-forgot-reset-ux-record.md](testing/fg034-auth-b-responsive-forgot-reset-ux-record.md). |
| Validation | Dedicated AUTH-B **12 passed**. Focused AUTH-B + MAIL-A/AUTH-A + FG-018 + SIGN-A–E + FG-028 **167 passed**, 325 warnings, **92.58s**. Full suite **1021 passed**, 3300 warnings, **394.93s**, exit **0**. Alembic current = heads `f2a3b4c5d6e7`. EST-2026-0019 occupancy unchanged. Live PRODUCTION packages **0**. No new migration. |
| Architectural findings | Thin routes over AUTH-A. Generic non-enumerating confirmation. CSRF remains on. Account-recovery exemptions are separate from `/sign/*`. `complete_password_reset` validates the credential before password-mismatch so invalid tokens fail closed. |
| Open decisions | AUTH-C delivery E2E close; MAIL-B Native Signing mail; Postmark token / sender domain; physical iPhone Account Recovery UAT. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do **not** begin AUTH-C. |
| Date | 2026-09-15 |

### 2026-09-15 — FG-034 MAIL-A / AUTH-A Account Recovery + transactional email foundation

| Field | Content |
|-------|---------|
| Milestone | FG-034 MAIL-A / AUTH-A |
| Status | **PARTIAL.** [FG-034](feature-gates/FG-034-account-recovery-and-transactional-email.md) **OPEN / PARTIAL**. MAIL-A **IMPLEMENTED**. AUTH-A **IMPLEMENTED**. AUTH-B/C, MAIL-B, AUTH-D **NOT AUTHORIZED**. |
| Branch | `main` |
| Objective | Shared transactional-email foundation (no live send) and Account Recovery security/data foundation (no Forgot Password pages). |
| Deliverables | `app/services/transactional_email.py`; `app/services/password_reset.py`; `users.credentials_epoch`; additive `f2a3b4c5d6e7` applied live; [ADR-052](adr/ADR-052-account-recovery-and-transactional-email.md) **Accepted**; [testing/fg034-mail-a-auth-a-live-bounded-uat-record.md](testing/fg034-mail-a-auth-a-live-bounded-uat-record.md). |
| Validation | Dedicated MAIL-A / AUTH-A **28 passed**. Focused MAIL-A/AUTH-A + FG-018 + SIGN-A–E **142 passed**. Full **1009 passed**, 3290 warnings, **344.09s**. Alembic current = heads `f2a3b4c5d6e7`. EST-2026-0019 occupancy unchanged. Live PRODUCTION packages **0**. |
| Architectural findings | One transactional engine. Postmark is the default production provider but MAIL-A uses local/fake only. Password-reset tokens are a separate domain from Signing. Legacy Flask-Login `"<user_id>"` is accepted as `credentials_epoch` 0. |
| Open decisions | AUTH-B Forgot Password pages; MAIL-B Native Signing mail; Postmark token / sender domain; physical iPhone Account Recovery UAT. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do **not** begin AUTH-B. |
| Date | 2026-09-15 |

### 2026-09-15 — FG-033 SIGN-E convert-once + generated-contract Native Signing + desktop/iPhone parity

| Field | Content |
|-------|---------|
| Milestone | FG-033 SIGN-E |
| Status | **COMPLETED** (automated). [FG-033](feature-gates/FG-033-native-signing-document-approval-signature-and-executed-artifact.md) **CLOSED / OPERATIONAL FOR UAT**. Real iPhone UAT **DEFERRED**. Production Native Signing **NOT COMPLETE**. |
| Branch | `main` |
| Objective | Convert-once Family 05 DOCX→PDF; generated-contract ceremony on the one signing engine; desktop + iPhone functional parity; FG-033 close. |
| Deliverables | `app/services/signing_docx_pdf.py`; converter provenance on frozen artifacts; additive `e0f1a2b3c4d5` applied live; responsive `/sign` CSS; dedicated SIGN-E tests; [testing/fg033-sign-e-live-bounded-uat-record.md](testing/fg033-sign-e-live-bounded-uat-record.md). |
| Validation | Dedicated SIGN-E **19 passed**. Focused SIGN-A/B/C/D/E + CO + Hub + TECH **208 passed**. Full **981 passed**, 3262 warnings, **371.67s**. Alembic current = heads `e0f1a2b3c4d5`. EST-2026-0019 occupancy unchanged. Live PRODUCTION packages **0**. |
| Architectural findings | One signing engine. Convert once at bind. No ReportLab/HTML fallback. Same routes for CHANGE_ORDER and CONTRACT. Desktop must not be degraded; mobile must not be a compressed desktop page. |
| Open decisions | Real-device iPhone UAT; ACTIVE PRODUCTION package; transactional email for normal real-customer send. |
| Next milestone | **STOP.** Return to ChatGPT Architect. |
| Date | 2026-09-15 |

### 2026-09-15 — FG-033 SIGN-D Change Order Native Signing E2E + automated close

| Field | Content |
|-------|---------|
| ID | FG-033 SIGN-D Change Order E2E + office/Hub + automated mobile UX |
| Status | **COMPLETE / NOT A GATE CLOSE.** FG-033 overall **OPEN / PARTIAL**. SIGN-E **not started**. Real iPhone UAT **DEFERRED TO BRAYMAN / BEN REAL-WORLD UAT** — **NOT CLAIMED AS PASS**. Production Native Signing **not complete**. |
| Branch | `main` |
| Base commit | `e48b074c27543bc300322362b9e174508e745d4c` |
| Objective | Close SIGN-D on automated product validation: Change Order E2E, office/Hub, customer mobile ceremony, countersign/no-countersign, lifecycle fail-closed, tenant isolation. Real iPhone UAT deferred by Joel / Architect. |
| Deliverables | Office Send for Signature; Hub labels; name-first `/sign` copy; iPhone-first CSS; dedicated SIGN-D tests; [testing/fg033-sign-d-live-bounded-uat-record.md](testing/fg033-sign-d-live-bounded-uat-record.md). No new Alembic. |
| Validation | Dedicated SIGN-D **11 passed**. Focused SIGN-A/B/C/D + CO + Hub + TECH **206 passed**. Full **962 passed**, 3184 warnings, **317.78s**. Alembic current = heads `d9e0f1a2b3c4`. EST-2026-0019 occupancy unchanged. Live PRODUCTION packages **0**. |
| Architectural findings | No new ADR. No schema change. Public `/favicon.ico` does not redirect to office login. Customer ceremony hides SHA/enums. Real-device UAT is deferred, not PASS. |
| Open decisions | SIGN-E. Ontario 06D. Slice D. V1 rescore. Later Project Element preflight. |
| Next milestone | **STOP.** Recommended next chunk SIGN-E — **not authorized from this note**. |
| Commit | this SIGN-D product commit (`feat: integrate Change Order Native Signing`) |
| Date | 2026-09-15 |

---

### 2026-09-14 — FG-033 SIGN-C countersign + executed PDF + custody

| Field | Content |
|-------|---------|
| ID | FG-033 SIGN-C countersign + executed PDF + custody |
| Status | **COMPLETE / NOT A GATE CLOSE.** FG-033 overall **OPEN / PARTIAL**. SIGN-D/E **not started**. Production Native Signing **not complete**. |
| Branch | `main` |
| Base commit | `daf254c1a0f7e1125dbad4620c29bf8d40625254` |
| Objective | Implement SIGN-C only: organization countersign, executed PDF assembly/custody, VOID/EXPIRE/DECLINE/RESEND. |
| Deliverables | `signing_executed_artifacts`; countersign/execute/lifecycle services; pypdf audit page; office `/signing-requests/<id>/executed`; customer executed download; CLI complete/lifecycle; additive `d9e0f1a2b3c4` applied live; [testing/fg033-sign-c-live-bounded-uat-record.md](testing/fg033-sign-c-live-bounded-uat-record.md). |
| Validation | Dedicated SIGN-C **19 passed**. Dedicated SIGN-A **11 passed**. Dedicated SIGN-B **18 passed**. Focused SIGN-A/B + CONTRACT + Change Order **174 passed**. Full **951 passed**, 3151 warnings, **529.43s**. Alembic current = heads `d9e0f1a2b3c4`. EST-2026-0019 occupancy unchanged. Live PRODUCTION packages **0**. SIGN-2026-0004 EXECUTED. SIGN-2026-0003 retained SIGNED. |
| Architectural findings | Pre-sign freeze never overwritten. Executed SHA is of retained bytes and is not printed inside the PDF. Custody failure leaves SIGNED. No new ADR. |
| Open decisions | SIGN-D. Ontario 06D. Slice D. V1 rescore. Later Project Element preflight. |
| Next milestone | **STOP.** Recommended next chunk SIGN-D — **not authorized from this note**. |
| Commit | this SIGN-C product commit (`feat: complete Native Signing execution lifecycle`) |
| Date | 2026-09-14 |

### 2026-09-14 — FG-033 SIGN-B secure invitation + public customer ceremony

| Field | Content |
|-------|---------|
| ID | FG-033 SIGN-B invitation + customer ceremony |
| Status | **COMPLETE / NOT A GATE CLOSE.** FG-033 overall **OPEN / PARTIAL**. SIGN-C/D/E **not started**. Production Native Signing **not complete**. |
| Branch | `main` |
| Base commit | `df383e234f30e67597b31a543c10c858eca4f16c` |
| Objective | Implement SIGN-B only: secure invitation token, public `/sign` customer ceremony, frozen PDF review, pinned consent, typed-name SIGN & ACCEPT. |
| Deliverables | `app/routes/sign.py`; `app/templates/signing/`; `app/static/css/signing.css`; token/rate-limit service; CLI `flask signing invite`; additive `c8d9e0f1a2b3` applied live; [testing/fg033-sign-b-live-bounded-uat-record.md](testing/fg033-sign-b-live-bounded-uat-record.md). |
| Validation | Dedicated SIGN-B **18 passed**. Dedicated SIGN-A **11 passed**. Focused SIGN + CONTRACT + Change Order **137 passed**. Full **933 passed**, 3110 warnings, **342.95s**. Alembic current = heads `c8d9e0f1a2b3`. EST-2026-0019 occupancy unchanged. Live PRODUCTION packages **0**. SIGN-2026-0003 SIGNED. SIGN-A requests retained. |
| Architectural findings | Raw secret never stored. Public `/sign/*` is a narrow login exemption. CSRF remains on. Countersign and EXECUTED remain SIGN-C. No customer account. |
| Open decisions | SIGN-C. Ontario 06D. Slice D. V1 rescore. Later Project Element preflight. |
| Next milestone | **STOP.** Recommended next chunk SIGN-C — **not authorized from this note**. |
| Commit | this SIGN-B product commit (`feat: add secure customer signing ceremony`) |
| Date | 2026-09-14 |

### 2026-09-14 — FG-033 SIGN-A Native Signing freeze + request engine + audit

| Field | Content |
|-------|---------|
| ID | FG-033 SIGN-A freeze + request engine + audit |
| Status | **COMPLETE / NOT A GATE CLOSE.** FG-033 overall **OPEN / PARTIAL**. SIGN-B/C/D/E **not started**. Production Native Signing **not complete**. |
| Branch | `main` |
| Base commit | `de4c2e194c71d66aaf9b81463d8d36eafe52c844` |
| Objective | Open Native Signing Feature Gate FG-033 and implement SIGN-A freeze + request identity + HUMAN APPROVED_FOR_SIGNATURE + append-only audit. |
| Deliverables | [FG-033](feature-gates/FG-033-native-signing-document-approval-signature-and-executed-artifact.md); `app/models/signing.py`; `app/services/signing.py`; `app/services/signing_artifact_storage.py`; `app/cli/signing.py`; additive `b7c8d9e0f1a2` applied live; [testing/fg033-sign-a-live-bounded-uat-record.md](testing/fg033-sign-a-live-bounded-uat-record.md). |
| Validation | Dedicated SIGN-A **11 passed**. Focused SIGN-A + CONTRACT + Change Order **103 passed**. Full **915 passed**, 3068 warnings, **341.52s**. Alembic current = heads `b7c8d9e0f1a2`. EST-2026-0019 occupancy unchanged. Live PRODUCTION packages **0**. TECH-D CTR-2026-0003 / CTR-2026-0004 intact. |
| Architectural findings | Overlay only. Frozen CO PDF bytes do not follow later live re-render. SIGN-A contract path copies retained DOCX; no LibreOffice. AI/AUTOMATION cannot approve. |
| Open decisions | SIGN-B. Ontario 06D. Slice D. V1 rescore. Later Project Element preflight. |
| Next milestone | **STOP.** Recommended next chunk SIGN-B — **not authorized from this note**. |
| Commit | this SIGN-A product commit (`feat: add Native Signing request foundation`); preceding `docs: open Native Signing feature gate` |
| Date | 2026-09-14 |

### 2026-09-14 — FG-024 TECH-D production-shaped synthetic Ontario UAT

| Field | Content |
|-------|---------|
| ID | FG-024 TECH-D production-shaped synthetic Ontario UAT |
| Status | **COMPLETE / NOT A GATE CLOSE.** FG-024 overall **OPEN / PARTIAL**. Native Signing **not started**. |
| Branch | `main` |
| Base commit | `af00fca3e3c1d34ed3bdd890ef71826b1b97d5a8` |
| Objective | Prove the TECH-A/B/C CONTRACT chain end-to-end with unmistakably synthetic Ontario UAT content. |
| Deliverables | `tests/test_synthetic_ontario_contract_uat_fg024.py`; live SYNTHETIC_UAT package `FG024D-UAT-ON-001`; CTR-2026-0003 / CTR-2026-0004; [testing/fg024-tech-d-live-bounded-uat-record.md](testing/fg024-tech-d-live-bounded-uat-record.md). |
| Validation | Dedicated TECH-D **5 passed**. Focused TECH-A/B/C/D + FG-024 **124 passed** / 25.62s. Full **904 passed**, 3040 warnings, **350.10s**. Alembic current = heads `a6b7c8d9e0f1`. EST-2026-0019 occupancy unchanged. Live PRODUCTION packages **0**. Family 05 master SHA unchanged. |
| Architectural findings | No new schema required. SYNTHETIC_UAT ACTIVE never satisfies ordinary PRODUCTION selection. WARN generation uses current ACTIVE bodies. Retrieval reads retained bytes. |
| Open decisions | Native Signing. Ontario 06D. Slice D. V1 rescore. Later Project Element preflight. |
| Next milestone | **STOP.** Recommended next workstream Native Signing — **not authorized from this note**. |
| Commit | this TECH-D commit (`test: prove synthetic Ontario contract flow`) |
| Date | 2026-09-14 |

### 2026-09-14 — FG-024 TECH-C Family 05 merge + artifact custody

| Field | Content |
|-------|---------|
| ID | FG-024 TECH-C Family 05 merge + artifact custody |
| Status | **COMPLETE / NOT A GATE CLOSE.** FG-024 overall **OPEN / PARTIAL**. TECH-D **not started**. |
| Branch | `main` |
| Base commit | `689262818b172aa4e317648a9a0ae72639f1f070` |
| Objective | Merge frozen commercial facts and frozen legal objects into a copy of governed Family 05; retain generated DOCX privately with SHA-256 and master provenance. |
| Deliverables | `app/services/family_05_master.py`, `family_05_contract_merge.py`, `contract_artifact_storage.py`; generation wiring; additive `a6b7c8d9e0f1` applied live; [testing/fg024-tech-c-live-migrate-bounded-uat-record.md](testing/fg024-tech-c-live-migrate-bounded-uat-record.md). Future Project Element direction recorded only: [architecture/project-element-authority-future-record.md](architecture/project-element-authority-future-record.md). |
| Validation | Focused TECH-C + FG-024 related + Hub/customer/proposal **175 passed** / 42.44s. Full **899 passed**, 3022 warnings, **290.85s**. Alembic current = heads `a6b7c8d9e0f1`. EST-2026-0019 occupancy unchanged. Live PRODUCTION packages **0**. Family 05 master SHA unchanged. |
| Architectural findings | Renderer never writes the master path. Historical Slice C contracts remain valid with nullable storage keys. Retrieval reads retained bytes; it does not re-render. |
| Open decisions | TECH-D production-shaped synthetic Ontario UAT. Ontario 06D. Slice D. Native Signing. V1 rescore. Later Project Element preflight. |
| Next milestone | **STOP.** Recommended next chunk TECH-D — **not authorized from this note**. |
| Commit | `9a6c86fb8e66234a10ac19f15118d8caea200af6` (`feat: render governed Family 05 contract artifact`) |
| Date | 2026-09-14 |

### 2026-09-14 — FG-024 TECH-B C1/C2/C3 generation policy

| Field | Content |
|-------|---------|
| ID | FG-024 TECH-B C1/C2/C3 generation policy |
| Status | **COMPLETE / NOT A GATE CLOSE.** FG-024 overall **OPEN / PARTIAL**. TECH-C/D **not started**. |
| Branch | `main` |
| Base commit | `bb4ddb1db07e020c02f829400e40db7e6287b718` |
| Objective | Govern production-shaped Ontario contract generation: commercial gate, pending-candidate WARN, warranty requirement. |
| Deliverables | Selector ALLOW/WARN/BLOCK; proposal pin; Ontario provision+warranty; Hub WARN copy; additive `f5a6b7c8d9e0` applied live; [testing/fg024-tech-b-live-migrate-bounded-uat-record.md](testing/fg024-tech-b-live-migrate-bounded-uat-record.md). |
| Validation | Focused TECH-B + FG-024 related **150 passed** / 31.37s. Full **886 passed**, 2989 warnings, **292.71s**. Alembic current = heads `f5a6b7c8d9e0`. EST-2026-0019 occupancy unchanged. Live PRODUCTION packages **0**. |
| Architectural findings | Candidate content is never authority. Historical Slice C contracts remain valid with nullable proposal_id. SYNTHETIC_UAT never satisfies ordinary production selection. |
| Open decisions | TECH-C Family 05 merge. Ontario 06D. Slice D. Native Signing. V1 rescore. |
| Next milestone | **STOP.** Recommended next chunk TECH-C — **not authorized from this note**. |
| Commit | this TECH-B commit (`feat: govern Ontario contract generation policy`) |
| Date | 2026-09-14 |

### 2026-09-14 — FG-024 TECH-A human activation + authority class

| Field | Content |
|-------|---------|
| ID | FG-024 TECH-A human activation + authority class |
| Status | **COMPLETE / NOT A GATE CLOSE.** FG-024 overall **OPEN / PARTIAL**. TECH-B/C/D **not started**. |
| Branch | `main` |
| Base commit | `065b724eaf6f7b8aa4d4586dd33b0d852e84e329` |
| Objective | HUMAN/COUNSEL activation of eligible APPROVED packages; SYNTHETIC_UAT vs PRODUCTION; ordinary production selector safety. |
| Deliverables | `authority_class`, `activated_by`, `legal_content_activation_events`; `activate_legal_content`; `flask legal-content activate`; additive `e4f5a6b7c8d9` applied live; [testing/fg024-tech-a-live-migrate-bounded-uat-record.md](testing/fg024-tech-a-live-migrate-bounded-uat-record.md). |
| Validation | Focused TECH-A + FG-024 related **73 passed** / 12.72s. Full **853 passed**, 2881 warnings, **276.57s**. Alembic current = heads `e4f5a6b7c8d9`. EST-2026-0019 occupancy unchanged. Live PRODUCTION packages **0**. |
| Architectural findings | APPROVED ≠ ACTIVE. SYNTHETIC_UAT never satisfies ordinary production selection. Unique ACTIVE-per-node index remains final DB protection. |
| Open decisions | TECH-B C1/C2/C3. Ontario 06D. Slice D. Native Signing. V1 rescore. |
| Next milestone | **STOP.** Recommended next chunk TECH-B — **not authorized from this note**. |
| Commit | this TECH-A commit (`feat: add governed legal content activation`) |
| Date | 2026-09-14 |

### 2026-09-14 — Fail-closed CONTRACT Hub UX

| Field | Content |
|-------|---------|
| ID | FG-024 fail-closed CONTRACT Hub UX (06G office exposure) |
| Status | **COMPLETE / NOT A GATE CLOSE.** FG-024 overall **OPEN / PARTIAL**. Independent BMR contract-story **PASS**. BMR DEMO READY remains **NO**. |
| Branch | `main` |
| Base commit | `bd1baf9426ab3a6db2d0d063fe1a76c14c8bc3ef` |
| Objective | Show the existing fail-closed selector result on office CONTRACT so Ontario with no ACTIVE package cannot pretend a production contract exists. |
| Deliverables | Hub `#hub-contract-legal` status panel; contractor_copy mapping; dedicated tests; C1/C2/C3 recorded in governance docs |
| Validation | Focused Hub + Hub UX **22 passed** / 12.82s. Full **838 passed**, 2857 warnings, **277.98s**. Alembic unchanged `d3e4f5a6b7c8 (head)`. EST-2026-0019 occupancy unchanged. Live library packages/objects **0**. |
| Architectural findings | Selector remains authority. No generation control. No Family 05 fallback. No schema/migration. Activation not built. Native Signing remains separate. |
| Open decisions | Architect review of overall BMR DEMO READY. Ontario 06D / Output 4. C2 WARN UI deferred until selector returns WARN. Slice D unauthorized. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do not begin Slice D. Do not populate Ontario legal content. |
| Commit | This fail-closed CONTRACT Hub UX commit |
| Date | 2026-09-14 |

### 2026-09-14 — FG-025 customer-document language slice

| Field | Content |
|-------|---------|
| ID | FG-025 Slice 6 (customer Proposal preview/PDF language) |
| Status | **COMPLETE / NOT A GATE CLOSE.** Presentation-only. FG-025 overall **NOT CLOSED**. |
| Branch | `main` |
| Base commit | `d2c7f35734495d8e93c97cbba9802efacb3d659b` |
| Objective | Clean customer-facing wording on the existing Proposal preview and Proposal PDF. Customer-facing title **CONSTRUCTION ESTIMATE**. |
| Deliverables | Preview/PDF title and pricing labels; office status removed from customer document; centralized copy constants; dedicated tests; continuity docs |
| Validation | Focused **97 passed** / 33.12s. Full **829 passed**, 2778 warnings, **264.51s**. Alembic unchanged `d3e4f5a6b7c8 (head)`. EST-2026-0019 occupancy unchanged. |
| Architectural findings | Presentation language only. No schema. No migration. No new customer-estimate entity. FG-012 firewall and FG-017 brand freeze unchanged. Proposal immutability unchanged. |
| Open decisions | FG-025 remaining surfaces still unauthorized. Independent BMR DEMO READY blocker remains fail-closed / Ontario contract story. ADR-001 / ADR-004 remain **Proposed**. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do not close FG-025. Do not begin Slice D. |
| Commit | This FG-025 customer-document language commit |
| Date | 2026-09-14 |

---

### 2026-09-14 — Known documentation-drift cleanup

| Field | Content |
|-------|---------|
| ID | Docs-only stale-state reconciliation |
| Status | **COMPLETE.** Docs-only. No product implementation. No V1 rescore. No migration. |
| Branch | `main` |
| Base commit | `92005e15bf9785350234bf78d7e85c175fa4b587` (`docs: close FG-024 Slice C after live UAT`) |
| Objective | Reconcile known stale CURRENT catalogs/indexes/handoff with already-governed later authority; preserve historically truthful records. |
| Deliverables | Current-facing FG-024 Slice C / V1 / MONITOR / material-catalogue / architecture-index / EST-2026-0019 path / ADR subsequent-status / frozen subsequent-status notes; normal continuity records. |
| Validation | Full suite **825 passed** / 2771 warnings / 258.44s / exit **0**. Live current = repo head `d3e4f5a6b7c8`. One graph head. |
| Architectural findings | No governance substance changed. ADR-008 / ADR-010 remain Proposed. FG-024 overall OPEN / PARTIAL. Slice D NOT AUTHORIZED. V1 remains 60% / 4 of 11. Legal Content Gate empty. EST-2026-0019 unchanged. |
| Open decisions | Next real CalibraytAI development priority remains with Joel / ChatGPT Architect. |
| Next milestone | **STOP.** Return to ChatGPT Architect. |
| Commit | This docs-only reconciliation commit |
| Date | 2026-09-14 |

---

### 2026-09-13 — FG-024 Slice C live migrate + bounded office UAT

| Field | Content |
|-------|---------|
| ID | FG-024 Slice C live UAT |
| Status | **CLOSED / OPERATIONAL FOR UAT.** Slice A remains **CLOSED / OPERATIONAL FOR UAT**. Slice B remains **CLOSED / OPERATIONAL FOR UAT**. Gate overall **OPEN / PARTIAL**. |
| Branch | `main` |
| Base commit | `1a2553932da1b750e2cbe0e32fd90e54d569a685` (`feat: add FG-024 contract generation foundation`) |
| Objective | Live-migrate additive `d3e4f5a6b7c8`; bounded office UAT of generation, provenance, immutable snapshot, fail-closed, and Slice A/B regression; close Slice C if all criteria pass. |
| Deliverables | Live current `d3e4f5a6b7c8 (head)`; backup `instance/brayman_estimator-backup-before-fg024c-d3e4f5a6b7c8-20260913-143836.db` (gitignored); [testing/fg024-slice-c-live-migrate-bounded-uat-record.md](testing/fg024-slice-c-live-migrate-bounded-uat-record.md); current-authority governance updates. No application-code change. |
| Validation | Dedicated Slice C **16 passed** / 2.71s. Slice A **17 passed** / 2.32s. Slice B **16 passed** / 2.10s. Full suite **825 passed** / 2771 warnings / 266.33s / exit **0**. Live current = repo head `d3e4f5a6b7c8`. One graph head. |
| Architectural findings | Empty library FAIL CLOSED. Family 05 remains presentation shell. ADR-051 §6 remains deferred / fail-closed. GENERATED ≠ EXECUTED. Old snapshot unchanged after later mutation. Later generation created a new snapshot. No Native Signing. No real legal content. No real customer contract. |
| Open decisions | C1 production “APPROVED estimate” mapping. C2 ADR-051 §6 ALLOW/BLOCK/WARN. C3 warranty increment. Slice D. 06D Ontario counsel. |
| Next milestone | **STOP.** Do not begin Slice D. |
| Commit | This live-UAT close commit |
| Date | 2026-09-13 |

---

### 2026-09-13 — FG-024 Slice C contract-generation product foundation

| Field | Content |
|-------|---------|
| ID | FG-024 Slice C product |
| Status | **PRODUCT FOUNDATION IMPLEMENTED IN REPOSITORY / NOT LIVE-MIGRATED / NOT OFFICE-UAT / NOT CLOSED.** Slice A remains **CLOSED / OPERATIONAL FOR UAT**. Slice B remains **CLOSED / OPERATIONAL FOR UAT**. Gate overall **OPEN / PARTIAL**. |
| Branch | `main` |
| Base commit | `252870da30433922c9b55bd4bfcf555704be73c8` (`docs: record FG-024 Slice C contract-generation preflight`) |
| Objective | Smallest governed generation + immutable snapshot foundation. Synthetic tests only. No live migrate. No Slice D. No legal seed. |
| Deliverables | `GeneratedProjectContract`, `ProjectContractSnapshot`, `ProjectContractSnapshotObject`; `app/services/contract_generation.py`; Alembic `d3e4f5a6b7c8`; focused tests. No UI. No seed. No Native Signing. |
| Validation | Dedicated Slice C **16 passed** / 2.66s. Slice A **17 passed** / 2.92s. Slice B **16 passed** / 2.72s. Full suite **825 passed** / 2771 warnings / 494.48s. Live current remains `c2d3e4f5a6b7`. One graph head `d3e4f5a6b7c8`. |
| Architectural findings | Slice A selector reused. Draft EstimateVersion fail-closed. Family 05 is presentation shell only. Pending-candidate §6 branch fail-closed without encoding ALLOW/WARN. GENERATED ≠ EXECUTED. Old snapshot unchanged after later mutation. |
| Open decisions | Slice C live migrate + bounded UAT. C1 production “APPROVED estimate” mapping. C2 ADR-051 §6 ALLOW/BLOCK/WARN. C3 warranty increment. Slice D. 06D Ontario counsel. |
| Next milestone | **STOP.** Do not live-migrate. Do not begin Slice D. |
| Commit | This product commit |
| Date | 2026-09-13 |

---

### 2026-09-13 — FG-024 Slice C contract-generation preflight

| Field | Content |
|-------|---------|
| ID | FG-024 Slice C preflight |
| Status | **PREFLIGHT COMPLETE / PRODUCT NOT AUTHORIZED / NOT IMPLEMENTED.** Slice A remains **CLOSED / OPERATIONAL FOR UAT**. Slice B remains **CLOSED / OPERATIONAL FOR UAT**. Gate overall **OPEN / PARTIAL**. |
| Branch | `main` |
| Base commit | `a176db36034af17309fd3f3e7e8c9a58043d6f56` (`docs: close FG-024 Slice B after live UAT`) |
| Objective | Freeze Slice C contract-generation + immutable project-snapshot architecture. No product code. No migration. No live DB mutation. No legal drafting. |
| Deliverables | [architecture/fg-024-slice-c-contract-generation-snapshot-preflight.md](architecture/fg-024-slice-c-contract-generation-snapshot-preflight.md); current-authority governance updates. No application-code change. |
| Validation | Documentation-only. `./venv/bin/python -m pytest -q` — **809 passed**, 2738 warnings, **545.74s**, exit **0**. No Slice C behavioural tests created. |
| Architectural findings | Slice C consumes Slice A selector; does not own Legal Content Gate APPROVED, Slice B source/update, Native Signing, or a second library. Empty library remains FAIL CLOSED. Family 05 is presentation shell only. GENERATED ≠ EXECUTED. ADR-051 §6 remains deferred / fail-closed on that branch. SCHEMA REQUIRED later. NEW ADR NOT REQUIRED. Draft EstimateVersion cannot generate. |
| Open decisions | C1 production mapping of “APPROVED estimate”. C2 ADR-051 §6 ALLOW/BLOCK/WARN. C3 warranty schedule increment. Slice C product authorization. Slice D. |
| Next milestone | **STOP.** Do not begin Slice C product or Slice D. |
| Commit | This Slice C preflight commit |
| Date | 2026-09-13 |

### 2026-09-13 — FG-024 Slice B live migrate + bounded office UAT

| Field | Content |
|-------|---------|
| ID | FG-024 Slice B live UAT |
| Status | **CLOSED / OPERATIONAL FOR UAT.** Slice A remains **CLOSED / OPERATIONAL FOR UAT**. Gate overall **OPEN / PARTIAL**. |
| Branch | `main` |
| Base commit | `e36397778d282e14801bfb00c896ec7a3c36057f` (`feat: add FG-024 legal-content update foundation`) |
| Objective | Live-migrate additive `c2d3e4f5a6b7`; bounded office UAT of source/snapshot/candidate/AI-boundary; preserve Slice A fail-closed; close Slice B if all criteria pass. |
| Deliverables | Live current `c2d3e4f5a6b7 (head)`; backup `instance/brayman_estimator-backup-before-fg024b-c2d3e4f5a6b7-20260913-125346.db` (gitignored); [testing/fg024-slice-b-live-migrate-bounded-uat-record.md](testing/fg024-slice-b-live-migrate-bounded-uat-record.md); current-authority governance updates. No application-code change. |
| Validation | Dedicated Slice B **16 passed** / 2.21s. Dedicated Slice A **17 passed** / 2.25s. Full suite **809 passed** / 2738 warnings / 278.30s / exit 0. Commercial continuity PASS. Source/snapshot/candidate/AI-boundary/Slice-A regression PASS. Legal Content Gate empty. |
| Architectural findings | Candidate is not legal authority. AI/AUTOMATION cannot APPROVE or ACTIVE. Slice B activation remains unavailable. Unchanged snapshot does not create a false candidate. ADR-051 §6 remains deferred. No live monitoring. |
| Open decisions | Slice C/D. Generation-while-`UPDATE_PENDING_REVIEW`. 06D Ontario counsel. |
| Next milestone | **STOP.** Do not begin Slice C or Slice D. |
| Commit | This live-UAT close commit |
| Date | 2026-09-13 |

---

### 2026-09-13 — FG-024 Slice B product foundation (not live-migrated)

| Field | Content |
|-------|---------|
| ID | FG-024 Slice B product |
| Status | **PRODUCT FOUNDATION IMPLEMENTED IN REPOSITORY / NOT LIVE-MIGRATED / NOT OFFICE-UAT / NOT CLOSED.** Slice A remains **CLOSED / OPERATIONAL FOR UAT**. Gate overall **OPEN / PARTIAL**. |
| Branch | `main` |
| Base commit | `72b54515f93683f96e7c09723f613cf27fc13082` (`docs: adopt FG-024 Slice B lifecycle architecture`) |
| Objective | Smallest source / snapshot / candidate / review foundation. No live migrate. No Slice C/D. No legal seed. |
| Deliverables | `LegalContentSource`, `LegalContentSourceSnapshot`, `LegalContentCandidateChange`, `LegalContentCandidateImpact`, `LegalContentReviewEvent`; `app/services/legal_content_update.py`; Alembic `c2d3e4f5a6b7`; focused tests. No UI. No seed. |
| Validation | Dedicated **16 passed** / 2.17s. Full suite **809 passed** / 2738 warnings / 373.56s. Live current remains `b1c2d3e4f5a6`. One graph head `c2d3e4f5a6b7`. |
| Architectural findings | Slice A selector unreopened. AI cannot APPROVE/ACTIVE. Candidate is review material. No auto-SUPERSEDE/deactivate. Generation-while-pending deferred. No live monitoring. |
| Open decisions | Slice B live migrate + bounded UAT. Generation-while-`UPDATE_PENDING_REVIEW`. Slice C/D. 06D Ontario counsel. |
| Next milestone | **STOP.** Do not live-migrate. Do not begin Slice C or Slice D. |
| Commit | This product commit |
| Date | 2026-09-13 |

---

### 2026-09-13 — FG-024 Slice B architecture adopted (ADR-051 Accepted)

| Field | Content |
|-------|---------|
| ID | FG-024 Slice B architecture |
| Status | **PREFLIGHT COMPLETE / ADR-051 ACCEPTED / PRODUCT NOT AUTHORIZED / NOT IMPLEMENTED.** Slice A remains **CLOSED / OPERATIONAL FOR UAT**. Gate overall **OPEN / PARTIAL**. |
| Objective | Reconcile existing untracked Slice B drafts against current FG-024 / ADR-050 / Legal Content Gate authority; adopt if conforming; Accept ADR-051. |
| Deliverables | Tracked Slice B preflight; ADR-051 Accepted; continuity docs. No product code. |
| Validation | Documentation-only. Canonical suite required after adoption. |
| Open decisions | Generation-while-`UPDATE_PENDING_REVIEW` **deferred**. Ontario legal population BLOCKED. |
| Next milestone | STOP. Do not begin Slice B product. |
| Date | 2026-09-13 |

### 2026-09-13 — CalibraytAI Opening V1 ingest

| Field | Content |
|-------|---------|
| ID | Opening V1 |
| Status | **DEPLOYED / OPERATIONAL** for local governed UAT + `origin/main`. Website integration **SEPARATE**. HostPapa app deploy **not applicable**. |
| Objective | Final silent ~7s opening from locked Frame F; ingest web media; fail-open login playback. |
| Deliverables | HQ/web/WebM, `app/static/opening/v1/`, login overlay, focused tests. |
| Validation | Dedicated opening tests **11 passed**. Full suite **793 passed**, 2716 warnings, **301.25s**. Local Flask port **5020**. Pushed `origin/main`. |
| Open decisions | Public website reuse is a separate package. |
| Next milestone | STOP. No opening polish. No FG-024 Slice B from this package. |
| Commit | Product `d6fa984b1e84be4a1b21ff8f7358fc1d43fa74dc`. Rollback `06ad8f7f69437b2e4302ba155ece6291ba9414ce`. |
| Date | 2026-09-13 |

### 2026-09-13 — FG-024 Slice A live migrate + bounded office UAT close

| Field | Content |
|-------|---------|
| ID | FG-024 Slice A live migrate / office UAT |
| Status | **CLOSED / OPERATIONAL FOR UAT.** Gate overall **OPEN / PARTIAL**. V1 remains **60% / 4 of 11**. Legal Content Gate **empty**. Live library **empty**. |
| Branch | `main` |
| Base commit | `868f8f2c7c46b36c4e121204fa2c12b2250c00ce` |
| Date | 2026-09-13 |
| Objective | Apply additive `b1c2d3e4f5a6` live and prove empty-library / resolver-backed / coded fail-closed office UAT without legal seed. |
| Deliverables | Live current `b1c2d3e4f5a6 (head)`; backup `instance/brayman_estimator-backup-before-fg024a-b1c2d3e4f5a6-20260913-091555.db` (gitignored); [testing/fg024-slice-a-live-migrate-bounded-uat-record.md](testing/fg024-slice-a-live-migrate-bounded-uat-record.md); current-authority governance updates. No application-code change. |
| Validation | Dedicated **17 passed** / 2.28s. Full suite **782 passed** / 2704 warnings / 269.18s. Live current = repo head `b1c2d3e4f5a6`. One graph head. Unresolved jurisdiction BLOCK `JURISDICTION_UNRESOLVED`. Ontario + empty library BLOCK `JURISDICTION_NOT_SUPPORTED`. |
| Architectural findings | ADR-037 resolver reused. No Family 05 / Permit Rules legal authority. No generic fallback. Empty live library is the intended Slice A state. |
| Open decisions | Slices B–D. Ontario counsel population. V1-04. |
| Next milestone | **STOP.** Do not begin Slice B. |
| Commit | This documentation commit |

### 2026-09-13 — FG-024 Slice A empty legal-content library product

| Field | Content |
|-------|---------|
| ID | FG-024 Slice A product |
| Status | **PRODUCT IMPLEMENTED IN REPOSITORY / NOT LIVE-MIGRATED / NOT OFFICE-UAT / NOT CLOSED.** V1 remains **60% / 4 of 11**. Legal Content Gate **empty**. |
| Branch | `main` |
| Base commit | `a4516b5a82ae6210751d42270e3250ca470cc139` |
| Date | 2026-09-13 |
| Objective | Empty North American legal-content library persistence + ADR-037-backed selection + coded fail-closed. |
| Deliverables | `legal_content_jurisdiction_packages`, `legal_content_objects`, Alembic `b1c2d3e4f5a6`, `app/services/legal_content.py`, focused tests. No UI. No seed. |
| Validation | Dedicated **17 passed** / 2.29s. Full suite **782 passed** / 2704 warnings / 267.61s. Live current remains `f1a2b3c4d5e6`. One graph head `b1c2d3e4f5a6`. |
| Architectural findings | Platform-governed library; no org ownership; no country-node fallback; APPROVED ≠ ACTIVE. |
| Open decisions | Live migrate + bounded office UAT. Slices B–D. Ontario counsel population. |
| Next milestone | **STOP.** Do not live-migrate. Do not begin Slice B. |
| Commit | This product commit |

### 2026-09-13 — ADR-050 Accepted (North American legal-content library ownership)

| Field | Content |
|-------|---------|
| ID | ADR-050 acceptance (architecture / fail-closed ownership only) |
| Status | **ACCEPTED.** [ADR-050](adr/ADR-050-north-american-legal-content-library-ownership.md) **Accepted** by Joel Brayman / ChatGPT Architect. FG-024 Slice A architecture prerequisite **satisfied**. Product **NOT IMPLEMENTED**. V1 remains **60% / 4 of 11**. |
| Branch | `main` |
| Base commit | `20c62d43ee12a679d39fbd44e2232a87754964ed` (`docs: record FG-024 Slice A legal-content library preflight`) |
| Objective | Final bounded review of ADR-050 against the approved Slice A preflight. Accept if it exactly records approved architecture. Reconcile current-state docs. No product code. No migration. |
| Deliverables | ADR-050 status **Accepted**; present-state documentation reconciliation. |
| Validation | `./venv/bin/python -m pytest -q` — **765 passed**, 2669 warnings, **301.88s**. Live current remains **`f1a2b3c4d5e6 (head)`**. No application-code change. |
| Architectural findings | ADR-050 matches the approved preflight: one North American library; Ontario first UAT package not product scope; one ADR-037 resolver; one Legal Content Gate; fail-closed / no generic fallback; Family 05 presentation only; V1-04 completeness vs V1-06 engine; Native Signing separate; additive future schema not `permit_rules`. |
| Open decisions | Bounded FG-024 Slice A empty-library product prompt. Ontario counsel (06D). |
| Next milestone | **STOP.** Do **not** begin FG-024 Slice A product from this acceptance. |
| Commit | This documentation acceptance commit |
| Date | 2026-09-13 |

### 2026-09-12 — FG-024 Slice A legal-content library preflight

| Field | Content |
|-------|---------|
| ID | FG-024 Slice A documentation-only implementation preflight |
| Status | **PREFLIGHT COMPLETE / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED.** [ADR-050](adr/ADR-050-north-american-legal-content-library-ownership.md) **Proposed**. V1 remains **60% / 4 of 11**. V1-04 remains **PARTIAL**. V1-06 remains **PARTIAL**. |
| Branch | `main` |
| Base commit | `3200112d627d6c6d8173daf72194f8409ac84b11` (`docs: reconcile present-state leftovers after FG-032 close`) |
| Objective | Freeze Slice A engine architecture, fail-closed matrix, ownership, schema-later decision, and ADR-050 Proposed. Retitle output 4. No product code. No migration. No legal drafting. |
| Deliverables | [architecture/fg-024-slice-a-legal-content-library-preflight.md](architecture/fg-024-slice-a-legal-content-library-preflight.md); [adr/ADR-050-north-american-legal-content-library-ownership.md](adr/ADR-050-north-american-legal-content-library-ownership.md); present-state documentation updates. |
| Validation | `./venv/bin/python -m pytest -q` — **765 passed**, 2669 warnings, **268.08s**. Live current remains **`f1a2b3c4d5e6 (head)`**. No application-code change. |
| Architectural findings | North American library intent confirmed. Ontario is first package, not product scope. Fail-closed is mandatory. Empty library + fail-closed is the smallest later product slice. Second contract system forbidden. |
| Open decisions | Joel Accept/reject ADR-050. Slice A product authorization. Ontario counsel (06D). |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do **not** implement FG-024 Slice A product. |
| Commit | This documentation preflight commit |
| Date | 2026-09-12 |

### 2026-09-12 — Catch-up / publication / deployment reconciliation

| Field | Content |
|-------|---------|
| ID | Catch-up present-state documentation reconciliation |
| Status | **RECORDED.** No product change. FG-032 remains **CLOSED / OPERATIONAL FOR UAT**. V1-05 remains **COMPLETE**. Readiness remains **60% / 4 of 11**. |
| Branch | `main` |
| Base commit | `09fca291a72fc17ca6f00872c01b4ff20ef19136` (`docs: close FG-032 and rescore V1-05`) |
| Objective | Account for unpublished/stranded work; correct present-state leftovers; verify migrations, tests, and deployment meaning. No V1-04. No new Feature Gate. No new ADR. |
| Deliverables | Present-state corrections in current-state, session-handoff, project-state-report, roadmap, Feature Gate/ADR/module/architecture indexes, chat-workflow-log. Stale local branches inventoried and left in place. |
| Validation | `./venv/bin/python -m pytest -q` — **765 passed**, 2669 warnings, **297.20s**. Live current = repository head **`f1a2b3c4d5e6 (head)`**. Working tree was clean at inspect. No stash. One worktree. |
| Architectural findings | No unpublished completed product on `main`. Unique July 2026 commits on `cursor/constructos-branding-engine` and `cursor/sidebar-navigation-refinement` remain **STALE / HISTORICAL**. Brayman-Estimator governed environment is local Flask/SQLite UAT; HostPapa is website **QUEUED POST-BETA**. |
| Open decisions | V1-04 documentation-only prompt still belongs to ChatGPT Architect. Do **not** merge stale branches. Do **not** deploy HostPapa from this repository. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do **not** begin V1-04 product work. |
| Commit | This documentation catch-up commit |
| Date | 2026-09-12 |

### 2026-09-11 — FG-032 documentation-only final governance close + V1-05 rescore

| Field | Content |
|-------|---------|
| ID | FG-032 final governance close + V1-05 evidence-based rescore |
| Status | **CLOSED / OPERATIONAL FOR UAT.** V1-05 **COMPLETE**. Readiness **60% / 4 of 11**. V1-04 remains **PARTIAL / CURRENT SCORED PACKAGE**. BMR DEMO READY **NO**. BRAYMAN REAL-LIFE UAT READY **NO**. |
| Branch | `main` |
| Base commit | `07490698fe325a6bd433be47070bce429c9f8ad8` (`docs: record FG-032 Slice C live migration and UAT`) |
| Objective | Documentation-only Architect close of FG-032 after Slices A+B and Slice C implementation, live migrate, and bounded office UAT PASS. Evidence-based V1-05 rescore. No application-code change. No migration. No live DB mutation. No UAT rerun. No V1-04 rescore. |
| Deliverables | Current-authority status reconciliation across FG-032, ADR-049, preflight, V1 register, indexes, current-state, project-state-report, session-handoff, roadmap, modules, milestones, and chat-workflow-log. Historical UAT records preserved with subsequent close notes. |
| Validation | Product tests **NOT RERUN**. HISTORICAL Slice C UAT dedicated **37 passed**, 496 warnings, 16.61s; affected regressions **256 passed**, 1147 warnings, 88.48s; full **765 passed**, 2669 warnings, 299.75s. Live current remains **`f1a2b3c4d5e6 (head)`**. Repository head **`f1a2b3c4d5e6`**. One graph head. |
| Architectural findings | Option A remains the V1 requirement. Option B live QuickBooks API remains **POST-V1**. V1-05 owns output 3 scoring. V1-04 remains PARTIAL (outputs 1–2 complete; output 3 scored under V1-05; output 4 not). Close does **not** flip BMR DEMO READY or BRAYMAN REAL-LIFE UAT READY. Independent remaining blocker: Ontario/fail-closed contract story. |
| Open decisions | V1-04 product work. FG-030 implementation. Subcontract RFQ/package remains maturation. ADR-008 remains **Proposed**. Live QuickBooks API remains POST-V1. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do **not** implement live QuickBooks API. Do **not** implement FG-030. Do **not** begin V1-04. Do **not** implement subcontract RFQ/package. |
| Commit | This documentation close commit (`docs: close FG-032 and rescore V1-05`) |
| Date | 2026-09-11 |

### 2026-09-11 — FG-032 Slice C live migrate + bounded office UAT

| Field | Content |
|-------|---------|
| ID | FG-032 Slice C live migrate + bounded office UAT |
| Status | **LIVE-MIGRATED / BOUNDED OFFICE UAT PASS / OPERATIONAL FOR UAT.** Slices A+B remain **LIVE-MIGRATED / BOUNDED OFFICE UAT PASS / OPERATIONAL FOR UAT**. Gate **OVERALL NOT CLOSED**. V1 remains **55% / 3 of 11**. V1-04 **PARTIAL**. V1-05 **PARTIAL**. BMR DEMO READY **NO**. BRAYMAN REAL-LIFE UAT READY **NO**. |
| Branch | `main` |
| Base commit | `00de0517b994635dec0be04a6e581167f690f7fe` (`fix: enforce atomic FG-032 entry confirmation`) |
| Objective | Apply pending Slice C revisions `f0a1b2c3d4e5` then `f1a2b3c4d5e6` to the live UAT DB and prove bounded DEMO office ENTERED/CORRECTED/REVERSED/re-entry without closing FG-032. |
| Deliverables | Live current **`f1a2b3c4d5e6 (head)`**; backup `instance/brayman_estimator-backup-before-fg032c-f1a2b3c4d5e6-20260911-115130.db` (gitignored); [testing/fg032-slice-c-live-migrate-bounded-uat-record.md](testing/fg032-slice-c-live-migrate-bounded-uat-record.md); current-authority governance updates. No application-code change. |
| Validation | Dedicated **37 passed** / 16.61s. Affected regressions **256 passed** / 88.48s. Full **765 passed** / 2669 warnings / 299.75s. Bounded office UAT **97 cases PASS** on DEMO project **id 26** package **1**. Historical occupancy-repair 37/256/765 remain historical. |
| Architectural findings | Download/issue is not entry. Unique occupancy by package PK. Concurrent race proof remains the focused test `test_concurrent_entered_exactly_one_succeeds` (not live). No QuickBooks API/OAuth/CSV/IIF. |
| Open decisions | FG-032 close. Do **not** rescore V1. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do **not** close FG-032. Do **not** rescore V1. |
| Date | 2026-09-11 |

### 2026-09-11 — FG-032 Slice C atomic ENTERED occupancy repair

| Field | Content |
|-------|---------|
| ID | FG-032 Slice C concurrent ENTERED repair |
| Status | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT LIVE-MIGRATED / OFFICE UAT NOT RUN.** Slices A+B remain **LIVE-MIGRATED / BOUNDED OFFICE UAT PASS / OPERATIONAL FOR UAT**. Gate **OVERALL NOT CLOSED**. V1 remains **55% / 3 of 11**. V1-04 **PARTIAL**. V1-05 **PARTIAL**. |
| Branch | `main` |
| Objective | Enforce at most one active ENTERED confirmation under concurrent submissions using a database unique occupancy lock after `f0a1b2c3d4e5`. |
| Deliverables | `EstimateQuickBooksEntryOccupancy`; revision **`f1a2b3c4d5e6`**; `confirm_entered` / `reverse_entry` occupancy claim/release; genuine concurrent-session test; governance updates. Live DB **not** upgraded. |
| Validation | Dedicated **37 passed** / 15.98s. Affected regressions **256 passed** / 134.28s. Full **765 passed** / 2669 warnings / 422.30s. Live current remains **`e9f0a1b2c3d4`**. One graph head **`f1a2b3c4d5e6`**. |
| Next milestone | Slice C live migrate + office UAT — **NOT AUTHORIZED FROM THIS REPAIR**. Do **not** close FG-032. Do **not** rescore V1. |
| Date | 2026-09-11 |

### 2026-09-11 — FG-032 Slice C implementation

| Field | Content |
|-------|---------|
| ID | FG-032 Slice C entry confirmation |
| Status | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT LIVE-MIGRATED / OFFICE UAT NOT RUN.** Slices A+B remain **LIVE-MIGRATED / BOUNDED OFFICE UAT PASS / OPERATIONAL FOR UAT**. Gate **OVERALL NOT CLOSED**. V1 remains **55% / 3 of 11**. V1-04 **PARTIAL**. V1-05 **PARTIAL**. |
| Branch | `main` |
| Objective | Implement explicit human ENTERED confirmation, REVERSED, CORRECTED, duplicate active-entry BLOCK, append-only events, org-scoped UI/routes, one additive Alembic revision after `e9f0a1b2c3d4`. |
| Deliverables | `EstimateQuickBooksEntryEvent`; revision **`f0a1b2c3d4e5`**; service/routes/UI; focused + regression + full-suite tests; governance updates. Live DB **not** upgraded. |
| Validation | Dedicated **36 passed** / 15.04s. Affected regressions **203 passed** / 77.92s. Full **764 passed** / 2652 warnings / 396.89s. Live current remains **`e9f0a1b2c3d4`**. One graph head **`f0a1b2c3d4e5`**. |
| Next milestone | Slice C live migrate + office UAT — **NOT AUTHORIZED FROM THIS IMPLEMENTATION**. Do **not** close FG-032. Do **not** rescore V1. |
| Date | 2026-09-11 |

### 2026-09-11 — FG-032 post-UAT documentation correction

| Field | Content |
|-------|---------|
| ID | FG-032 post-UAT present-state correction (documentation only) |
| Status | **DOCUMENTATION-ONLY.** Slices A+B remain **LIVE-MIGRATED / BOUNDED OFFICE UAT PASS / OPERATIONAL FOR UAT / SLICE C NOT AUTHORIZED / OVERALL NOT CLOSED.** V1 remains **55% / 3 of 11**. V1-04 **PARTIAL**. V1-05 **PARTIAL**. |
| Branch | `main` |
| Objective | Correct leftover present-state contradictions after live migrate / UAT (V1 register live current; stale “output 3 remains to be authorized”; ADR README FG-032 NOT LIVE-MIGRATED) |
| Validation | Product tests **not** rerun. HISTORICAL dedicated **23** / full **751**. Live current remained `e9f0a1b2c3d4`. Live DB untouched. |
| Next milestone | **STOP.** Joel decision: authorize Slice C or leave FG-032 open. |
| Date | 2026-09-11 |

### 2026-09-11 — FG-032 Slices A+B live migrate + bounded office UAT

| Field | Content |
|-------|---------|
| ID | FG-032 Slices A+B live migrate / bounded office UAT (V1-05 Option A; not a 12th major package) |
| Status | **LIVE-MIGRATED / BOUNDED OFFICE UAT PASS / OPERATIONAL FOR UAT / SLICE C NOT AUTHORIZED / OVERALL NOT CLOSED.** V1 remains **55% / 3 of 11**. Current scored package **V1-04 / PARTIAL**. V1-05 **PARTIAL**. BMR DEMO READY **NO**. BRAYMAN REAL-LIFE UAT READY **NO**. |
| Branch | `main` |
| Objective | Apply additive `e9f0a1b2c3d4` to live UAT DB and prove bounded DEMO office QuickBooks-ready entry without Slice C |
| Validation | Dedicated **23 passed** / 12.96s. Full **751 passed**, 2479 warnings, 329.14s. Canonical project **id 26**. Packages QB-2026-0001 ISSUED / 0002 ISSUED / 0003 REVIEWED (stale BLOCK). Live current = head `e9f0a1b2c3d4`. |
| Product SHA | **`70e571140e12377aa5bd009b598530576401113b`** (`feat: implement FG-032 QuickBooks-ready artifacts`) |
| Start pin | **`520eeca7410e1a575f46a0bb8ed8126ea0d26445`** |
| Evidence | [testing/fg032-slices-ab-live-migrate-bounded-uat-record.md](testing/fg032-slices-ab-live-migrate-bounded-uat-record.md) |
| Next milestone | **STOP.** Slice C / close gate / V1-04 require separate authorization. |
| Date | 2026-09-11 |

### 2026-09-11 — FG-032 post-implementation governance reconciliation (documentation only)

| Field | Content |
|-------|---------|
| ID | FG-032 docs recon / product-parent correction |
| Status | **DOCUMENTATION-ONLY.** Slices A+B remain **IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT LIVE-MIGRATED / OFFICE UAT NOT RUN / SLICE C NOT AUTHORIZED / OVERALL NOT CLOSED.** Product parent corrected to **`010f6d641a756ceb2ab67475a284d3b8426c7b20`**. Product SHA **`70e571140e12377aa5bd009b598530576401113b`**. V1 remains **55% / 3 of 11**. V1-04 **PARTIAL**. V1-05 **PARTIAL**. BMR DEMO READY **NO**. BRAYMAN REAL-LIFE UAT READY **NO**. |
| Branch | `main` |
| Objective | Correct the known FG-032 product-parent error and reconcile current governance records with Git |
| Validation | Product tests **not** rerun. HISTORICAL dedicated **23** / focused **209** / full **751**. Live current remained `d8e9f0a1b2c3`. |
| Next milestone | **STOP.** Live migrate / office UAT / Slice C require separate authorization. |
| Date | 2026-09-11 |

### 2026-09-10 — FG-032 Slices A+B QuickBooks-ready artifacts (not live-migrated)

| Field | Content |
|-------|---------|
| ID | FG-032 Slices A+B / ADR-049 Accepted (V1-05 Option A; not a 12th major package) |
| Status | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT LIVE-MIGRATED / OFFICE UAT NOT RUN / SLICE C NOT AUTHORIZED / OVERALL NOT CLOSED.** V1 remains **55% / 3 of 11**. Current scored package **V1-04 / PARTIAL**. V1-05 **PARTIAL**. BMR DEMO READY **NO**. BRAYMAN REAL-LIFE UAT READY **NO**. |
| Branch | `main` |
| Objective | Governed internal-office sales-entry sheet + planned cost-class companion |
| Validation | Dedicated **23 passed**; focused **209 passed**; full **751 passed**. Live current remained `d8e9f0a1b2c3`. |
| Product SHA | **`70e571140e12377aa5bd009b598530576401113b`** (`feat: implement FG-032 QuickBooks-ready artifacts`) |
| Next milestone | **STOP.** Live migrate / office UAT / Slice C require separate authorization. |
| Date | 2026-09-10 |

### 2026-09-10 — V1-05 QuickBooks Option A architecture preflight (documentation only)

| Field | Content |
|-------|---------|
| ID | FG-032 / ADR-049 recording (V1-05 Option A; not a 12th major package) |
| Status | **RECORDED / ARCHITECTURE PREFLIGHT COMPLETE / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED.** Joel selected Option A. Option B live API **POST-V1**. V1 remains **55% / 3 of 11**. Current scored package **V1-04 / PARTIAL**. BMR DEMO READY **NO**. BRAYMAN REAL-LIFE UAT READY **NO**. |
| Branch | `main` |
| Objective | Repository reconnaissance and architecture preflight for governed QuickBooks-ready output / controlled human-entry workflow. Documentation only. No product code. No migration. No live DB mutation. No V1 rescore. |
| Deliverables | ADR-049 Proposed; FG-032 recorded; Option A preflight; quickbooks-integration and project-document-package pins; estimating ownership note; indexes; current-state; project-state-report; session-handoff; V1 register status text; milestones; chat-workflow-log. |
| Validation | Product tests **NOT RERUN**. HISTORICAL Slice B UAT focused **83 passed**, 454 warnings, 15.24s; full **728 passed**, 2173 warnings, 373.17s. Live current remains **`d8e9f0a1b2c3`**. Repository head **`d8e9f0a1b2c3`**. One graph head. |
| Architectural findings | Output 3 = controlled pair (sales-entry sheet + planned cost-class companion). Format = office HTML/PDF; QuickBooks-ready not importable. Estimating owns the artifact. Amounts from CURRENT costing + CURRENT pricing + Issued/Accepted Proposal. Routing classifies; does not prove amount. ENTERED is a human record. Family 04 presentation content review required before implementation. |
| Open decisions | ADR-049 acceptance. FG-032 implementation authorization. Family 04 layout mapping. FG-030. V1-04 start. ADR-008 remains **Proposed**. Ontario contract blocker unchanged. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do **not** implement FG-032. Do **not** create a migration. Do **not** implement FG-030. Do **not** begin V1-04 product work. |
| Commit | This documentation recording (`docs: define V1-05 QuickBooks Option A`) |
| Date | 2026-09-10 |

### 2026-09-10 — FG-031 documentation-only final governance close

| Field | Content |
|-------|---------|
| ID | FG-031 final governance close (supporting V1 gate; not a 12th major package) |
| Status | **CLOSED / OPERATIONAL FOR UAT.** Slice A **OPERATIONAL FOR UAT**. Slice B **OPERATIONAL FOR UAT**. Subcontract RFQ/package **MATURATION DURING UAT / NOT IMPLEMENTED**. V1 remains **55% / 3 of 11**. Current scored package **V1-04 / NOT STARTED**. BMR DEMO READY **NO**. BRAYMAN REAL-LIFE UAT READY **NO**. |
| Branch | `main` |
| Objective | Documentation-only Architect close of FG-031 after Slice A and Slice B implementation, live migrate, and office UAT PASS. No application-code change. No migration. No live DB mutation. No UAT rerun. No V1 rescore. |
| Deliverables | Current-authority status reconciliation across FG-031, ADR-048, preflight, indexes, current-state, project-state-report, session-handoff, V1 register, roadmap, modules, milestones, and chat-workflow-log. Historical UAT records preserved. |
| Validation | Product tests **NOT RERUN**. HISTORICAL Slice B UAT focused **83 passed**, 454 warnings, 15.24s; full **728 passed**, 2173 warnings, 373.17s. Live current remains **`d8e9f0a1b2c3`**. Repository head **`d8e9f0a1b2c3`**. One graph head. |
| Architectural findings | Two stored dimensions; no HYBRID enum; human routing confirmation; unresolved routing blocks FG-027; Allowance exception preserved; quote is evidence not cost; selected-quote freeze; PLAN/catalogue ownership preserved. Close does **not** authorize RFQ/package, FG-030, or V1-04. |
| Open decisions | FG-030 implementation. V1-04 start. Subcontract RFQ/package remains maturation. ADR-008 remains **Proposed**. Independent remaining blocker: Ontario/fail-closed contract story. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do **not** implement FG-030. Do **not** begin V1-04. Do **not** implement subcontract RFQ/package. |
| Commit | This documentation close commit (`docs: close FG-031`) |
| Date | 2026-09-10 |

### 2026-09-10 — FG-031 Slice B live migrate + bounded office UAT

| Field | Content |
|-------|---------|
| ID | FG-031 Slice B live migrate + bounded office UAT (supporting V1 gate; not a 12th major package) |
| Status | **SLICE B LIVE-MIGRATED / OFFICE UAT PASS / OPERATIONAL FOR UAT.** Slice A remains **OPERATIONAL FOR UAT**. Overall **NOT CLOSED.** V1 remains **55% / 3 of 11**. BMR DEMO READY **NO**. BRAYMAN REAL-LIFE UAT READY **NO**. |
| Branch | `main` |
| Objective | Recoverable live SQLite backup; apply committed migration `d8e9f0a1b2c3`; bounded synthetic office UAT of FG-031 Slice B. No FG-030. No V1-04. No subcontract RFQ/package. |
| Deliverables | Backup `instance/brayman_estimator-backup-before-fg031b-d8e9f0a1b2c3-20260910-083215.db` (gitignored). Live current = head `d8e9f0a1b2c3`. Canonical UAT project **id 25**. Dedicated UAT record. Governance close docs. |
| Validation | Focused **83 passed**. Full suite **728 passed**, 2173 warnings, 373.17s. All required UAT cases **PASS**. No product correction. |
| Architectural findings | Quote remains evidence. FG-027 remains costing authority. Quote selection does not mutate cost or Pricing. Selected-quote freeze is non-floating. Customer and Supplier Package outputs remain private. |
| Open decisions | FG-031 overall close remains with ChatGPT Architect. RFQ/package is maturation. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do **not** implement FG-030. Do **not** begin V1-04. |
| Commit | This documentation/UAT close commit (`docs: close FG-031 Slice B UAT`) |
| Date | 2026-09-10 |

### 2026-09-10 — FG-031 Slice B subcontract quote evidence product implementation

| Field | Content |
|-------|---------|
| ID | FG-031 Slice B subcontract identity + quote evidence (supporting V1 gate; not a 12th major package) |
| Status | **SLICE B IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT LIVE-MIGRATED / UAT NOT AUTHORIZED.** Slice A remains **OPERATIONAL FOR UAT**. Overall **NOT CLOSED.** V1 remains **55% / 3 of 11**. BMR DEMO READY **NO**. BRAYMAN REAL-LIFE UAT READY **NO**. |
| Branch | `main` |
| Objective | Thin org-scoped Subcontractor; EstimateVersion-scoped SubcontractQuoteEvidence; human SELECTED workflow; freeze selected quote facts onto EstimateCostingSnapshotLine; contractor-facing PRICE quote review. No live migrate. No live UAT. No FG-030. No V1-04. |
| Deliverables | `app/models/subcontractor.py`; additive Alembic **`d8e9f0a1b2c3` FILE**; `app/services/subcontract_quote.py`; costing freeze columns; Scope Delivery Review quote UI; dedicated tests. |
| Validation | Dedicated Slice B **21 passed**. Slice A **26**. FG-027 **20**. FG-029 **16**. Governed bundle **306**. Full suite **728**. Live current remains **`c7d8e9f0a1b2`**. |
| Architectural findings | Quote is evidence, not cost authority. One SELECTED quote per line; prior SELECTED becomes SUPERSEDED. No SOURCE_SUBCONTRACT_QUOTE. Attachment is optional textual `provenance_note` only. |
| Open decisions | Slice B live migrate / UAT. FG-030. V1-04. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do **not** live-migrate Slice B. |
| Commit | Product **`5e1082af68e0eb145d9da01c0fa26585f6b8b9d1`**. Start pin **`0d98b87112e8dda3537fe125d25f0737212bfe1c`**. Pin follows. |
| Date | 2026-09-10 |

### 2026-09-09 — FG-031 Slice A live migrate + bounded office UAT

| Field | Content |
|-------|---------|
| ID | FG-031 Slice A live migrate / office UAT (supporting V1 gate; not a 12th major package) |
| Status | **SLICE A IMPLEMENTED / TESTED / COMMITTED / PUSHED / LIVE-MIGRATED / OFFICE UAT PASS / OPERATIONAL FOR UAT / SLICE B NOT AUTHORIZED / OVERALL NOT CLOSED.** V1 remains **55% / 3 of 11**. BMR DEMO READY **NO**. BRAYMAN REAL-LIFE UAT READY **NO**. |
| Branch | `main` |
| Objective | Governed live backup; apply `c7d8e9f0a1b2`; bounded synthetic office UAT of Scope Delivery Review, confirmation gate, Supplier Package filter, clone reconfirm, and privacy/isolation. No Slice B. No product-code repair. |
| Deliverables | Live current = head `c7d8e9f0a1b2`. Canonical DEMO project **id 19**. UAT record. Current-authority close docs. |
| Validation | Required commercial UAT cases **PASS**. Product tests **NOT RERUN** (no product defect). Historical dedicated FG-031 **26** / FG-027 **20** / FG-029 **16** / governed **258** / full **707**. |
| Architectural findings | CONFIRMED routing is costing authority; resolved PROPOSED still blocks. Supplier Package includes only cited CONFIRMED CONTRACTOR_PURCHASED. Slice B tables remain absent. |
| Open decisions | Slice B remains separately authorized. FG-030 remains **RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. V1-04 not begun. ADR-008 remains **Proposed**. |
| Next milestone | **STOP.** Return to ChatGPT Architect. Do not implement Slice B. Do not implement FG-030. Do not begin V1-04. |
| Commit | Close **`b50b0dcd1ea24f1a37ed32d04325ce09127fd203`**. Start pin **`bbe22f2a10ba9ba827e50c92688774a025b95d34`**. Pin follows. |
| Date | 2026-09-09 |

### 2026-09-09 — FG-031 Slice A human-confirmation costing gate repair

| Field | Content |
|-------|---------|
| ID | FG-031 Slice A repair (supporting V1 gate; not a 12th major package) |
| Status | **SLICE A IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT LIVE-MIGRATED / UAT NOT AUTHORIZED / SLICE B NOT AUTHORIZED / NOT CLOSED.** Human-confirmation costing gate repaired. V1 remains **55% / 3 of 11**. |
| Branch | `main` |
| Objective | Require CONFIRMED scope routing before FG-027 Costing Approval. PROPOSED is not commercial authority. |
| Deliverables | Costing BLOCK extended to unconfirmed routing; dedicated tests; minimum current-authority docs. No migration. |
| Validation | Dedicated FG-031 **26 passed**. FG-027 **20**. FG-029 **16**. Governed bundle **258 passed**. Full suite **707 passed**. Live migrate **not run**. |
| Architectural findings | Reused `SCOPE_DELIVERY_UNRESOLVED`. No new public block code. Clone remains PROPOSED until human reconfirm. |
| Open decisions | Live migrate / office UAT / Slice B remain separately authorized. |
| Next milestone | **STOP.** Do not live-migrate. Do not implement Slice B. Do not implement FG-030. Do not begin V1-04. |
| Commit | Repair **`ec8dcf35f0da109b75422504e1a104c1623d186c`**. Pin follows. |
| Date | 2026-09-09 |

### 2026-09-09 — FG-031 Slice A scope delivery routing product implementation

| Field | Content |
|-------|---------|
| ID | FG-031 Slice A (supporting V1 gate; not a 12th major package) |
| Status | **SLICE A IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT LIVE-MIGRATED / UAT NOT AUTHORIZED / SLICE B NOT AUTHORIZED / NOT CLOSED.** ADR-048 **Accepted**. V1 remains **55% / 3 of 11**. FG-030 remains **RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. |
| Branch | `main` |
| Objective | Implement Estimating-owned two-dimension scope delivery routing, Scope Delivery Review, Approve All, FG-027 unresolved BLOCK, Supplier Package CONTRACTOR_PURCHASED filter. |
| Deliverables | `EstimateScopeDelivery`; additive Alembic file `c7d8e9f0a1b2`; Hub PRICE UI; costing BLOCK; package eligibility; clone copy; dedicated + regression tests; current-authority docs. |
| Validation | Dedicated FG-031 **23 passed**. Governed bundle **235 passed**. Full suite **704 passed**. Live migrate **not run**. UAT **not run**. |
| Architectural findings | No stored HYBRID. Clone conservative reconfirmation (`PROPOSED`/`DRAFT`, confirmation cleared). Uncited MANUAL/DEMO fail-closed via required estimate-line citation + confirmed CONTRACTOR_PURCHASED. |
| Open decisions | Live migrate / office UAT / Slice B remain separately authorized. |
| Next milestone | **STOP.** Do not live-migrate. Do not implement Slice B. Do not implement FG-030. Do not begin V1-04. |
| Commit | Product **`54120608df98432b9be80faf8c2a3a08cdb5679c`**. Pin follows. |
| Date | 2026-09-09 |

### 2026-09-09 — ADR-048 / FG-031 scope delivery routing architecture recording

| Field | Content |
|-------|---------|
| ID | ADR-048 / FG-031 (supporting V1 gate; not a 12th major package) |
| Status | **RECORDED / ARCHITECTURE PREFLIGHT COMPLETE / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED.** ADR-048 **Accepted** (architecture only). V1 remains **55% / 3 of 11**. FG-030 remains **RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. |
| Branch | `main` |
| Objective | Record scope delivery / make-buy / procurement routing ownership and two bounded FG-031 slices from the completed architecture reconciliation. Docs only. |
| Deliverables | ADR-048; FG-031; preflight; current-authority indexes and handoff docs |
| Validation | `git diff --check`. Product tests **NOT RERUN**. |
| Architectural findings | Two stored dimensions; 1:1 EstimateScopeDelivery per EstimateLineItem; no HYBRID enum; PLAN remains quantity/evidence; Estimating owns routing; Supplier Package filter CONTRACTOR_PURCHASED; unresolved later BLOCKS FG-027 except Allowance. |
| Open decisions | FG-031 implementation authorization. First Slice A UI hide vs expose owner-supplied/third-party. FG-030 implementation. V1-04 start. |
| Next milestone | **STOP.** Do **not** implement FG-031, FG-030, or V1-04. |
| Commit | Architecture **`1c6c8c492b92f11cc80ad1b6e8689f0e42523bcd`**. Pin follows. |
| Date | 2026-09-09 |

### 2026-09-09 — FG-028 Slice 3 approved logo installation / close

| Field | Content |
|-------|---------|
| ID | FG-028 / product identity Slice 3 |
| Status | **SLICES 1–3 COMPLETE / CLOSED / OPERATIONAL FOR UAT.** CALIBRAYTAI PRODUCT IDENTITY TRANSITION **COMPLETE**. Runtime V2 Field header logo installed. Tenant branding preserved. V1 remains **55% / 3 of 11**. FG-030 **RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. |
| Branch | `main` |
| Objective | Install Joel-approved CalibraytAI runtime product logos from `CalibraytAI_090926_Final.zip`; test; verify; close FG-028. |
| Deliverables | `app/static/branding/calibraytai-logo-v2.png`; Field header src; bounded tests; FG-028 close docs. |
| Validation | Dedicated **13**. Combined Field/brand/proposal/CO/auth **131**. Focused **117**. FG-029 **16**. Full **681**. Visual QA Field desktop/mobile + office dashboard PASS. `git diff --check`. No `migrations/`. Live current remains `b6c7d8e9f0a1`. |
| Open decisions | FG-030 implementation. V1-04. SCOPE DELIVERY / MAKE-BUY architecture. Field favicon remains tenant PNG. |
| Next milestone | **STOP.** Return to ChatGPT Architect. |
| Commit | Product **`502035fa70ced1d0ff042db3077cc66f50e68de4`**. Pin follows. |
| Date | 2026-09-09 |

### 2026-09-09 — FG-029 post-UAT governance reconciliation

| Field | Content |
|-------|---------|
| ID | FG-029 / V1-03 close docs |
| Status | **GOVERNANCE RECONCILED.** FG-029 **CLOSED / OPERATIONAL FOR UAT**. V1-03 **COMPLETE**. V1 **55% / 3 of 11**. FG-028 Slice 3 **APPLICATION INSTALLATION / TEST / ACCEPTANCE PENDING / NOT CLOSED**. FG-030 **RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. Copyable-output rule preserved. |
| Branch | `main` |
| Objective | Reconcile interleaved already-authorized governance dirt into one coherent current-authority state. |
| Deliverables | FG-029 close/UAT authority; FG-028 asset-status; FG-030 architecture recording; `.cursor/rules/50-chat-copyable-output.mdc` preserved; UAT record. |
| Validation | Docs/governance only. Product tests **NOT RERUN**. Historical FG-029 dedicated **16** / governed **210** / full **677**. `git diff --check` clean. No `app/` / `tests/` / `migrations/` changes. Live current remains `b6c7d8e9f0a1`. |
| Open decisions | FG-028 Slice 3 application installation. FG-030 implementation. V1-04. SCOPE DELIVERY / MAKE-BUY architecture. |
| Next milestone | **STOP.** Return to ChatGPT Architect. |
| Commit | Close **`880697a246de7e901a81f89584168a9a9fb1dd67`**. Pin follows. |
| Date | 2026-09-09 |

### 2026-09-09 — FG-029 live migration + bounded BMR demo office UAT

| Field | Content |
|-------|---------|
| ID | FG-029 / V1-03 |
| Status | **CLOSED / OPERATIONAL FOR UAT.** Live-migrated. Bounded DEMO Winchester UAT **PASS**. Subsequent governance reconciliation committed the close docs. |
| Branch | `main` |
| Objective | Apply `b6c7d8e9f0a1` live and exercise the governed supplier workflow on labeled DEMO/SYNTHETIC data only. |
| Deliverables | Live current = head `b6c7d8e9f0a1`. Project **id 14** `FG029-UAT-BMR-DEMO`. Issued package **id 1**. HTML+PDF. Non-floating freeze. V1-03 **COMPLETE**. Readiness **55%**. |
| Validation | UAT PASS. Product tests **not** rerun (HISTORICAL dedicated 16 / governed 210 / full 677). |
| Open decisions | FG-028 Slice 3 application installation. FG-030 implementation. V1-04. |
| Next milestone | **STOP.** Return to ChatGPT Architect. |
| Date | 2026-09-09 |

### 2026-09-09 — FG-029 V1-03 BMR / supplier workflow product implementation

| Field | Content |
|-------|---------|
| ID | FG-029 / V1-03 |
| Status | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT LIVE-MIGRATED / UAT NOT AUTHORIZED / NOT CLOSED.** |
| Branch | `main` |
| Objective | Implement authorized FG-029 BMR / supplier workflow from interrupted WIP |
| Deliverables | MaterialRequirement; Supplier Catalogue; mapping review UI; frozen Supplier Package HTML+PDF; additive migration file `b6c7d8e9f0a1`; dedicated tests; current-authority recording |
| Validation | Dedicated **16 passed**. Material Catalogue **35**. Estimating+FG-026+FG-027 **62**. Output/PDF **41**. Tenancy **56**. Governed bundle **210**. Full suite **677 passed**. Live current remains `a5b6c7d8e9f0`. Repository head `b6c7d8e9f0a1`. Live migrate **not** run. UAT **NOT RUN**. |
| Architectural findings | Supplier price INFORM ONLY. No EstimateLineItem / FG-027 / Pricing mutation. ADR-008 remains Proposed. FG-010 remains door count. |
| Open decisions | Live-migrate / UAT authorization; FG-028 Slice 3 asset; website |
| Next milestone | **STOP.** Do **not** live-migrate. Do **not** populate live DEMO BMR data. V1 remains **45% / 2 of 11**. |
| Commit | Product **`ee578dcb5a688842ebedaff0682131826e6c7188`**. Pin follows. |

### 2026-09-09 — FG-029 V1-03 BMR / supplier workflow architecture recording

| Field | Content |
|-------|---------|
| ID | FG-029 / V1-03 |
| Status | **RECORDED / ARCHITECTURE PREFLIGHT COMPLETE / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED.** |
| Branch | `main` |
| Objective | Record ADR-046 and FG-029 so V1-03 has governing architecture without product implementation |
| Deliverables | ADR-046 Accepted; FG-029; [fg-029-bmr-supplier-workflow-v1-preflight.md](architecture/fg-029-bmr-supplier-workflow-v1-preflight.md); current-authority reconciliation |
| Validation | Docs only. **PRODUCT TESTS NOT RERUN — V1-03 ADR / FG / PREFLIGHT ONLY.** Live current = heads `a5b6c7d8e9f0`. No schema. |
| Architectural findings | Thin MaterialRequirement; inform-only supplier price; DEMO Winchester; FG-010 remains door count; ADR-008 stays Proposed |
| Open decisions | FG-029 implementation authorization; FG-028 Slice 3 asset; website |
| Next milestone | **STOP.** Do **not** implement V1-03. V1 remains **45% / 2 of 11**. |
| Commit | Architecture recording **`07039c8dabfeba7b6ef4714d2cee50abf648bc4f`**. Pin follows. |

### 2026-09-09 — FG-028 CalibAi → CalibraytAI product identity Slices 1–2

| Field | Content |
|-------|---------|
| ID | FG-028 |
| Status | **SLICES 1–2 IMPLEMENTED / TESTED / COMMITTED / PUSHED. SLICE 3 ASSET INSTALLATION PENDING. NOT CLOSED.** |
| Branch | `main` |
| Objective | Governed product-identity transition CalibAi → CalibraytAI without history rewrite, tenant overwrite, or schema churn |
| Deliverables | ADR-045 Accepted; FG-028; [product-identity.md](governance/product-identity.md); Slice 1 visible strings + tests; Slice 2 current-authority docs |
| Validation | Dedicated **9 passed**. Focused Field/Hub/Permit/Brand/Labour **117 passed**. Full suite **661 passed**. Live current = heads `a5b6c7d8e9f0`. No live DB mutation. |
| Architectural findings | Four identities remain distinct. Field PNG/title conflation held for Slice 3. |
| Open decisions | Joel-approved CalibraytAI lettering asset; external website pass |
| Next milestone | **STOP.** V1-03 **NOT STARTED**. V1 remains **45% / 2 of 11**. |
| Commit | `e06fa92c4543ae641ba5067b1d277af048d97139` |

### 2026-09-08 — V1-02 / FG-027 office UAT continuation + close

| Field | Content |
|-------|---------|
| ID | FG-027 / V1-02 |
| Status | **CLOSED / OPERATIONAL FOR UAT.** Remaining office UAT **PASS**. V1-02 **COMPLETE**. Readiness **45%**. |
| Branch | `main` |
| Base commit | `cf282bc6ea5cb8c917b9bae052c84a31cae65445` |
| Objective | Resume remaining FG-027 office UAT after the legacy override-provenance repair and close the gate only if UAT PASS. |
| Deliverables | Live UAT continuation on EstimateVersion **id 9** / port **5016**; FG-027 / V1 register / current-authority close docs. No new migration. No product-code change. |
| Validation | Override freeze **PASS**. Approve All **PASS**. Pricing consume **PASS**. Recost supersession **PASS**. STALE / re-apply **PASS**. Labour-in-basis unchanged. Assembly **id 2** / TakeoffPackage **id 1** unchanged. Product tests **not** rerun (last verified dedicated **20** / full **652**). |
| Architectural findings | Stale Flask 5016 (pre-repair PID) had to be restarted onto current `main` before the repair could be office-verified. |
| Open decisions | V1-03 authorization. Do not accept ADR-008 from this close. |
| Next milestone | **STOP.** Return to ChatGPT Architect for V1-03 authorization. Do **not** begin V1-03 from this close. |
| Commit | Close SHA **`c348bcfb41daead674aaf75050fc0a6847a8c0c0`** |
| Date | 2026-09-08 |

### 2026-09-08 — V1-02 / FG-027 bounded legacy override-provenance repair

| Field | Content |
|-------|---------|
| ID | FG-027 / V1-02 |
| Status | **LEGACY OVERRIDE-PROVENANCE DEFECT REPAIRED / TESTED / COMMITTED / PUSHED / AWAITING UAT CONTINUATION.** Gate remains **LIVE-MIGRATED / OFFICE UAT STOPPED / NOT PASS / NOT CLOSED**. |
| Branch | `main` |
| Base commit | `db43d54e57a884de491cffa3bcda9119efde0c7a` |
| Objective | Repair NULL `library_unit_cost_reference` classification so a later working-cost change on a pre-FG-027 CostItem/Assembly Draft line is `MANUAL_OVERRIDE` with required reason/actor/time. |
| Deliverables | `establish_legacy_library_unit_cost_reference` in `app/services/estimate_costing.py`; call from `update_line_item` before applying a new `unit_cost`; dedicated tests in `tests/test_estimate_costing_fg027.py`. No new migration. No live DB write. |
| Validation | Dedicated FG-027 **20 passed**. Estimating focused **29**. Pricing focused **52**. FG-026 **20**. Governed A–D bundle **121**. Full suite **652 passed**. Historical dedicated **15** / full **647** remain the pre-repair baseline. |
| Architectural findings | Best available historical copy for a NULL-reference library-derived line is the **pre-edit working `unit_cost`**, not today’s CostItem/Assembly library value. Populated references stay frozen. |
| Open decisions | Office UAT continuation authorization. FG-027 close. V1-02 COMPLETE. |
| Next milestone | **STOP.** Return to ChatGPT Architect for UAT-continuation authorization. Do **not** close FG-027. Do **not** begin V1-03. |
| Commit | Product **`72949f99da2b56ec06e95e16e29fa194a6730bbd`** (`fix: preserve FG-027 legacy override provenance`) |
| Date | 2026-09-08 |

### 2026-09-08 — V1-02 / FG-027 live migration and office UAT stop

| Field | Content |
|-------|---------|
| ID | FG-027 / V1-02 |
| Status | **LIVE-MIGRATED / OFFICE UAT STOPPED / NOT PASS / NOT CLOSED** |
| Branch | `main` |
| Base commit | `b944436136d0bafb198b27c401b79792d076ef16` |
| Objective | Apply additive `a5b6c7d8e9f0` live and run bounded office UAT of costing approval on EstimateVersion 9 |
| Deliverables | Live current = heads `a5b6c7d8e9f0`; gitignored backup `instance/brayman_estimator-backup-before-fg027-a5b6c7d8e9f0.db`; office UAT port **5016** |
| Validation | Live upgrade **PASS**. Zero-cost BLOCK **PASS**. Failed Approve All atomicity **PASS**. Manual override provenance **FAIL** (line 7 `library_unit_cost_reference` NULL; working unit_cost 250 classified `LIBRARY_ASSEMBLY`). No costing snapshot. No Pricing apply. Product tests **not** rerun. |
| Architectural findings | Pre-FG-027 inserted lines do not backfill `library_unit_cost_reference`. `classify_working_source_kind` treats NULL reference as non-override. |
| Open decisions | Defect repair authorization. Remaining office UAT after repair. |
| Next milestone | **STOP.** Return defect to ChatGPT Architect. Do not silently repair. Do not begin V1-03. |
| Commit | `3bf832b2fea5e1ade8c3e412dc7635a4a15c42b1` |
| Date | 2026-09-08 |

### 2026-09-08 — V1-02 / FG-027 costing-approval product implementation

| Field | Content |
|-------|---------|
| ID | FG-027 / V1-02 |
| Status | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT LIVE-MIGRATED / UAT NOT AUTHORIZED / NOT CLOSED** |
| Branch | `main` |
| Base commit | `28fb5c0445fafabb2924d5d43bce46bf5fca3d0e` |
| Objective | Implement Automated Costing + Human Cost Approval V1: working costing review, deterministic BLOCK/WARN, Approve All Costing, immutable costing snapshots, recost/supersession, Pricing consume / STALE |
| Deliverables | `EstimateCostingSnapshot` + frozen lines; working override columns; Pricing `costing_snapshot_id`; Costing Review UI; migration file `a5b6c7d8e9f0`; dedicated tests |
| Validation | Dedicated FG-027 **15 passed**. Estimating focused **29**. Pricing focused **52**. Labour/material **60**. FG-026 **20**. Governed bundle **176**. Full suite **647 passed**. Live migrate **NOT RUN**. UAT **NOT RUN**. |
| Architectural findings | Estimating owns costing. Pricing consumes frozen `approved_direct_cost_total`. Labour snapshot remains out of basis. Empty Assembly $0 BLOCKS. No supplier requirement. |
| Open decisions | Live migrate + office UAT require a later prompt. V1-03 / ADR-008 remain unauthorized. |
| Next milestone | **STOP.** Do not live-migrate. Do not UAT. Do not begin V1-03. |
| Commit | `c751d72b32f1ed415375719df2fd69936ace64d7` |
| Date | 2026-09-08 |

### 2026-09-08 — V1-02 / FG-027 costing-approval ADR, Feature Gate, and architecture preflight

| Field | Content |
|-------|---------|
| ID | FG-027 / ADR-044 |
| Status | **RECORDED / ARCHITECTURE PREFLIGHT COMPLETE / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED** |
| Branch | `main` |
| Base commit | `bacb5abf574b3dfe30bda4b6d6015026a3946607` |
| Objective | Memorialize V1-02 costing-approval boundary: ADR, Feature Gate, architecture preflight, and current-authority pins. No product implementation. |
| Deliverables | ADR-044 **Accepted**; FG-027 recorded; `docs/architecture/fg-027-costing-approval-preflight.md`; governance cross-pins. No `app/**`. No `migrations/**`. |
| Validation | `git diff --check`. Docs only. Product tests **not** rerun. |
| Architectural findings | Estimating owns costing snapshots. Pricing consumes. Labour snapshots remain out of selling-price basis. Approve All = costing approval only. Proposed later revision `a5b6c7d8e9f0` down_revision `f4a5b6c7d8e9` — not created. |
| Open decisions | FG-027 implementation authorization. Remaining V1 register §13 items except #2. |
| Next milestone | **STOP.** Do **not** implement FG-027. |
| Commit | `076e12f022fa5248a34e7baf7d05ae51e9e0ac4b` |
| Date | 2026-09-08 |

### 2026-09-08 — FG-026 live migration and office UAT close

| Field | Content |
|-------|---------|
| ID | FG-026 |
| Status | **CLOSED / OPERATIONAL FOR UAT** |
| Branch | `main` |
| Base commit | `1a855cc7e020f1f712c6710b30c8e7faca2c4713` |
| Objective | Apply additive `f4a5b6c7d8e9` live and run bounded project-3 office UAT for Phase D mapping. |
| Deliverables | Live current = heads `f4a5b6c7d8e9`; labeled Draft estimate/version/section; human-created Assembly `FG026-UAT-DOOR`; one EstimateLineItem with three frozen citations; governance close. |
| Validation | Live upgrade **PASS**. One graph head. Additive tables exist. Office UAT **PASS** on port **5015**. Package 1 unchanged. No labour/pricing snapshot, MaterialRequirement, or supplier/SKU from insert. Product tests **not** rerun. |
| Architectural findings | PLAN proposes / Estimating commits remains. Package approval still does not insert. Hub PLAN leftover mapping copy is out of this gate. |
| Open decisions | V1-02 costing authorization. |
| Next milestone | **STOP.** Do **not** begin V1-02. |
| Commit | `20d23b0103ee729e1d9770feeddfa7f8754e8804` |
| Date | 2026-09-08 |

### 2026-09-08 — FG-026 takeoff-to-estimate mapping V1 implementation

| Field | Content |
|-------|---------|
| ID | FG-026 |
| Status | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT LIVE-MIGRATED / UAT NOT RUN / NOT CLOSED** |
| Branch | `main` |
| Base commit | `73253c46b5fcb54a96345107ac49fe1162063369` |
| Objective | Bounded PLAN → PRICE Phase D: map an approved TakeoffPackage into governed EstimateLineItem(s) on an existing editable Draft on the same Project, with frozen Estimating-owned insertion/citation provenance. |
| Deliverables | Models + additive `f4a5b6c7d8e9`; mapping service; builder uncommitted helpers; map UI; dedicated tests **20**; full suite **632**. |
| Validation | Dedicated / PLAN / Estimating / pricing-labour-material / governed bundle / full pytest as recorded in chat-workflow-log. Live migrate **not** run. UAT **NOT RUN**. |
| Architectural findings | PLAN proposes / Estimating commits. Existing `add_*_line` still commit for manual builder. FG-026 insert is one transaction. |
| Open decisions | Live migrate + bounded project-3 UAT authorization. |
| Next milestone | Separate live-migrate / UAT prompt. |
| Commit | `aa4c71800586e0b8e2a63931bcdc8bc44d87a489` |
| Date | 2026-09-08 |

### 2026-09-08 — CalibAi V1 completion register

| Field | Content |
|-------|---------|
| ID | CalibAi V1 Completion Register |
| Status | **RECORDED / GOVERNING / DOCS ONLY** |
| Branch | `main` |
| Base commit | `95b396602eb578f0399e7785d7e066b6dd0056f8` |
| Objective | Establish the authoritative CalibAi V1 definition and 11-package completion register. |
| Deliverables | `docs/v1-completion-register.md`; cross-pins. No product code. |
| Validation | `git diff --check`. Docs only. Product tests **not** rerun. |
| Architectural findings | V1 = BMR DEMO READY **and** BRAYMAN REAL-LIFE UAT READY. Initial readiness **30%**. **0 / 11** COMPLETE. FG-024 remains **NOT IMPLEMENTATION-AUTHORIZED**. FG-026 remains **NOT IMPLEMENTATION-AUTHORIZED**. |
| Open decisions | Seven Joel decisions in the register §13. |
| Next milestone | **STOP.** Do **not** implement FG-026. Do **not** implement FG-024. Do **not** start another FG-025 slice. |
| Commit | this V1 register docs commit |
| Date | 2026-09-08 |

### 2026-09-08 — FG-026 takeoff-to-estimate mapping preflight

| Field | Content |
|-------|---------|
| ID | FG-026 — PLAN → PRICE Phase D Takeoff-to-Estimate Mapping V1 |
| Status | **RECORDED / ARCHITECTURE PREFLIGHT COMPLETE / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED** |
| Branch | `main` |
| Base commit | `1c20100a3838828cdeebece51ed820bcf15063fb` |
| Objective | Record FG-026 Feature Gate and architecture preflight. Docs/governance only. |
| Deliverables | FG-026 gate; preflight; current-authority pins. No product code. No migration. |
| Validation | `git diff --check`. Docs only. Product tests **not** rerun. |
| Architectural findings | PLAN proposes / Estimating commits. Package approval does **not** insert. Later implementation would require an additive migration. No new ADR in this pass. |
| Open decisions | FG-026 implementation authorization (separate prompt). Remaining FG-025 surfaces. Observation Delete still QUEUED. |
| Next milestone | **STOP.** Do **not** implement FG-026 from this recording. Do **not** start another FG-025 slice. Do **not** start FG-024. Do **not** start LEARN. |
| Commit | this FG-026 docs commit |
| Date | 2026-09-08 |

### 2026-09-08 — FG-025 Slice 5 Review Turnover

| Field | Content |
|-------|---------|
| ID | Review Turnover — FG-025 Slice 5 |
| Status | **RECORDED / DOCS ONLY / TURNOVER PASS** |
| Branch | `main` |
| Base commit | `5b497905086554214e85f69afd8101d88f89161c` |
| Objective | Complete Review Turnover. Pin Slice 5 product SHA. Repair current-authority contradictions. |
| Deliverables | session-handoff 22-point package; Fresh Chat Startup Prompt; SHA pins; drift repairs. |
| Validation | Dedicated FG-025 **19 passed** reconfirmed. Live Alembic `e3f4a5b6c7d8`. Live **39 / 39**. Project 13 five actuals unchanged. Full **612** remains the Slice 5 product-SHA evidence (not rerun this pass). |
| Architectural findings | No product-code change. This commit is **not** the Slice 5 product SHA. |
| Open decisions | Remaining FG-025 surfaces; Observation Delete still QUEUED. |
| Next milestone | **STOP.** Do **not** start another FG-025 slice. Do **not** start FG-024. Do **not** start LEARN. |
| Commit | this Review Turnover docs commit |
| Date | 2026-09-08 |

### 2026-09-08 — FG-025 Slice 5 contractor-facing Field Web language

| Field | Content |
|-------|---------|
| ID | FG-025 — Slice 5 Field Web language |
| Status | **RECORDED / IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT CLOSED** |
| Branch | `main` |
| Base commit | `0ed4d67282551d75b4204e33d367f3f3baba023a` |
| Objective | Contractor-facing Field Web copy only. |
| Deliverables | Field templates + `field.js` visible strings + `contractor_copy.py` Slice 5 constants; FG-025 and FG-021 copy tests. |
| Validation | Dedicated **19 passed**. Field-focused **83 passed**. Prompt governed list **190 passed**. Full **612 passed**. Manual Field Web review **PASS** on port **5026**. Live **39 / 39**. Project 13 five actuals unchanged. `git diff --check` clean. |
| Architectural findings | Presentation only. **Save original** preserved. No Observation Delete. No session revocation. No Field observation-detail page exists. |
| Open decisions | Remaining FG-025 surfaces; “contract value” wording still flagged; FG-024 unauthorized. |
| Next milestone | **STOP.** Do **not** start another FG-025 slice. Do **not** start FG-024. Do **not** start LEARN. |
| Commit | `5b497905086554214e85f69afd8101d88f89161c` |
| Date | 2026-09-08 |

### 2026-09-08 — FG-025 Slice 4 post-close documentation reconciliation

| Field | Content |
|-------|---------|
| ID | FG-025 — Slice 4 close-record documentation reconciliation |
| Status | **DOCS ONLY.** Slice 4 product SHA pinned. Gate **NOT CLOSED.** Remaining surfaces **NOT AUTHORIZED.** |
| Branch | `main` |
| Base commit | `56e16f03446f982d577d2a3f0d3375ef865e1dc9` |
| Objective | Correct Slice 4 close-review documentation-hygiene findings. No product change. |
| Deliverables | Pin Slice 4 product SHA; reconcile current-state/PSR/handoff HEAD; complete remaining-surface inventory with REVIEW/DECISION vs unauthorized-candidate distinction. |
| Validation | `git diff --check`. Docs only. Tests not rerun. Preserved Slice 4: dedicated **16** / Slice-4 focused **114** / governed **226** / full **609**. Independent close review reran dedicated **16** and Slice-4 focused **114**; governed and full not independently rerun. |
| Architectural findings | This commit is **not** the Slice 4 product SHA. No schema / migration / DB / calculation change. |
| Open decisions | Remaining FG-025 surfaces; FG-024 unauthorized. |
| Next milestone | **STOP.** Do **not** start Slice 5. Do **not** start FG-024. Do **not** start LEARN. |
| Commit | this docs-only reconciliation commit (not Slice 4 product SHA `56e16f03446f982d577d2a3f0d3375ef865e1dc9`) |
| Date | 2026-09-08 |

### 2026-09-08 — FG-025 Slice 4 contractor-facing office language

| Field | Content |
|-------|---------|
| ID | FG-025 — Slice 4 office shell language |
| Status | **SLICE 4 IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT CLOSED.** Remaining surfaces **NOT AUTHORIZED.** Not a product-wide sweep. |
| Branch | `main` |
| Base commit | `ab6219827f33a59f4d6528bbfffbd4551b9d1411` |
| Objective | Contractor-facing language on shared OFFICE navigation, dashboard, authentication, and Settings / Brand Profile, without changing routes, permissions, auth behavior, or Settings values. |
| Deliverables | Shared office templates + `contractor_copy.py` Slice 4 constants; nav titles aligned to Slice 3 page names; FG-025 and Brand Profile HTML tests. |
| Validation | Dedicated **16 passed**. Slice-4 focused **114 passed**. Governed **226 passed**. Full **609 passed**. Independent close review reran dedicated **16** and Slice-4 focused **114**; governed and full not independently rerun. Manual office-shell review **PASS** (Flask 5025). `git diff --check`. Live current = heads `e3f4a5b6c7d8`. Field **39 / 39**. Project **13** five actuals unchanged. |
| Architectural findings | Reused Slice 1–3 presentation map. Global nav **Labour rates** / **Pricing**. Historical Evidence nav left as-is. Cost Items left as-is. Header disabled **Settings (coming soon)** left frozen. Field Web **Log out** unchanged. |
| Open decisions | Remaining FG-025 surfaces; “contract value” wording still flagged; FG-024 unauthorized. |
| Next milestone | **STOP.** Do **not** start Slice 5. Do **not** start FG-024. Do **not** start LEARN. |
| Commit | `56e16f03446f982d577d2a3f0d3375ef865e1dc9` (`feat: continue FG-025 contractor-facing office language`) |
| Date | 2026-09-08 |

### 2026-09-08 — FG-025 Slice 3 post-close documentation reconciliation

| Field | Content |
|-------|---------|
| ID | FG-025 — Slice 3 close-record documentation reconciliation |
| Status | **DOCS ONLY.** Slice 3 product SHA pinned. Gate **NOT CLOSED.** Remaining surfaces **NOT AUTHORIZED.** |
| Branch | `main` |
| Base commit | `071f5f923515c6405298bf96b0af249a20f81358` |
| Objective | Correct three Slice 3 close-review documentation-hygiene findings. No product change. |
| Deliverables | Pin Slice 3 product SHA; restore CAR-001 Slice 2 subsequent-status and append Slice 3; restore FG-025 Slice 2 historical stop-line from parent. |
| Validation | `git diff --check`. Docs only. Tests not rerun. Preserved Slice 3: dedicated **13** / PRICE-focused **167** / governed **303** / full **606**. Independent close review reran dedicated **13** and PRICE-focused **167**; governed and full not independently rerun. |
| Architectural findings | This commit is **not** the Slice 3 product SHA. No schema / migration / DB / calculation change. |
| Open decisions | Remaining FG-025 surfaces; FG-024 unauthorized. |
| Next milestone | **STOP.** Do **not** start Slice 4. Do **not** start FG-024. Do **not** start LEARN. |
| Commit | this docs-only reconciliation commit (not Slice 3 product SHA `071f5f923515c6405298bf96b0af249a20f81358`) |
| Date | 2026-09-08 |

### 2026-09-07 — FG-025 Slice 3 contractor-facing PRICE language

| Field | Content |
|-------|---------|
| ID | FG-025 — Slice 3 PRICE specialist language |
| Status | **SLICE 3 IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT CLOSED.** Remaining surfaces **NOT AUTHORIZED.** Not a product-wide sweep. |
| Branch | `main` |
| Base commit | `1aa54f51dcd2447ce6934dddbf5305c81016a824` |
| Objective | Contractor-facing language on current office PRICE specialist screens (Pricing, Labour rates, Estimates, Cost Library, Assemblies, Material Catalogue), without changing calculations, schema, or MONITOR. |
| Deliverables | PRICE templates + `contractor_copy.py` Slice 3 maps; Hub PRICE link labels only; FG-025 and PRICE HTML tests. |
| Validation | Dedicated **13 passed**. PRICE-focused **167 passed**. Governed **303 passed**. Full **606 passed**. Manual PRICE review **PASS**. `git diff --check`. Live current = heads `e3f4a5b6c7d8`. Field **39 / 39**. Project **13** five actuals unchanged. |
| Architectural findings | Reused Slice 1/2 presentation map. Office titles **Pricing** / **Labour rates**. Internal `TRUE_GROSS_MARGIN` unchanged; display **Gross Margin Pricing**. Global nav still says Labour Engine / Pricing Engine (Slice 4). Hub PRICE table leftover `TRUE_GROSS_MARGIN` left frozen except link labels. |
| Open decisions | Remaining FG-025 surfaces; “contract value” wording still flagged; FG-024 unauthorized. |
| Next milestone | **STOP.** Do **not** start Slice 4. Do **not** start FG-024. Do **not** start LEARN. |
| Commit | `071f5f923515c6405298bf96b0af249a20f81358` (`feat: continue FG-025 contractor-facing PRICE language`) |
| Date | 2026-09-07 |

### 2026-09-07 — FG-025 Slice 2 contractor-facing Project Hub language

| Field | Content |
|-------|---------|
| ID | FG-025 — Slice 2 Project Hub language |
| Status | **SLICE 2 IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT CLOSED.** Remaining slices **NOT AUTHORIZED.** Not a product-wide sweep. |
| Branch | `main` |
| Base commit | `5a2dd7addfd71ddde6c81fab63a6f8f040a27315` |
| Objective | Contractor-facing language on the office Project Hub and embedded PLAN/PRICE/CONTRACT/BUILD/MONITOR copy, without rewriting standalone modules. |
| Deliverables | Hub `detail.html` copy; `contractor_copy.py` Slice 2 constants; FG-025 and Hub HTML tests. |
| Validation | Dedicated **10 passed**. Focused **159 passed**. Full **603 passed**. Manual Hub review **PASS** (project 13, Flask 5015). `git diff --check`. Live current = heads `e3f4a5b6c7d8`. Field **39 / 39**. Project **13** five actuals unchanged. |
| Architectural findings | Reused Slice 1 presentation map. Chosen heading **Pricing assumptions**. Frozen metric labels unchanged. |
| Open decisions | Remaining FG-025 slices; “contract value” wording still flagged; FG-024 unauthorized. |
| Next milestone | **STOP.** Do **not** start Slice 3. Do **not** start FG-024. Do **not** start LEARN. |
| Commit | (this product commit) |
| Date | 2026-09-07 |

### 2026-09-07 — FG-025 Slice 1 Hub MONITOR contractor-facing display mapping

| Field | Content |
|-------|---------|
| ID | FG-025 — Slice 1 Hub MONITOR display mapping |
| Status | **SLICE 1 IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT CLOSED.** Remaining slices **NOT AUTHORIZED.** Not a product-wide sweep. |
| Branch | `main` |
| Base commit | `01d6fadbcbb968ad873552ec463fa83eb0b7fd8d` |
| Objective | Presentation-layer mapping so Hub `#hub-monitor` and office actuals forms/tables no longer display raw MONITOR/BUILD state names. |
| Deliverables | `app/presentation/contractor_copy.py`; Hub MONITOR/actuals template mapping; `tests/test_fg025_contractor_copy.py`; HTML copy assertion updates. Optional `app/shell.py` template-helper wiring. |
| Validation | Dedicated **10 passed**. Focused **159 passed**. Full **603 passed**. `git diff --check`. Live current = heads `e3f4a5b6c7d8`. Field **39 / 39**. Project **13** five actuals unchanged. |
| Architectural findings | Internal domain keys (`MISSING_ACTUALS`, `other_direct`, `CO_COST_DELTA_COPY`) remain in services. Frozen Hub metric identities unchanged. |
| Open decisions | Remaining FG-025 slices; “contract value” wording still flagged; FG-024 unauthorized. |
| Next milestone | **STOP.** Do **not** start Slice 2. Do **not** start FG-024. Do **not** start LEARN. |
| Commit | (this product commit) |
| Date | 2026-09-07 |

### 2026-09-07 — FG-025 contractor-facing UX implementation preflight

| Field | Content |
|-------|---------|
| ID | FG-025 — implementation preflight |
| Status | **IMPLEMENTATION PREFLIGHT COMPLETE / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED / NOT CLOSED.** |
| Branch | `main` |
| Base commit | `00c763b1a5d936eaa3b825105ffa0001b48c5ef5` |
| Objective | Inventory user-facing language; pin terminology principles and slice strategy; do not rewrite UI. |
| Deliverables | FG-025 IMPLEMENTATION PREFLIGHT section; current-authority pins. No product-code change. |
| Validation | Docs-only. No `app/` / `tests/` / `migrations/` change. `git diff --check`. Product pytest not re-run. Live current = heads `e3f4a5b6c7d8`. Field **39 / 39**. |
| Architectural findings | Highest leakage is Hub MONITOR raw enums. Presentation-layer mapping recommended. Customer Proposal/PDF is a separate audience. “Current contract value” can confuse legal contract with authorized revenue. |
| Open decisions | Final glossary strings; Slice 1 authorization; specialist nav names. |
| Next milestone | Joel/ChatGPT review, then optional FG-025 Slice 1 prompt. Do **not** start FG-024. |
| Commit | (this docs commit) |
| Date | 2026-09-07 |

### 2026-09-07 — FG-023 MONITOR V1 CLOSED / OPERATIONAL FOR UAT

| Field | Content |
|-------|---------|
| ID | FG-023 MONITOR V1 — close |
| Status | **CLOSED / OPERATIONAL FOR UAT.** MONITOR V1 **IMPLEMENTED / LIVE-MIGRATED / OFFICE-UAT-VERIFIED / CLOSED.** Item 13 **CLOSED / OPERATIONAL FOR UAT.** |
| Branch | `main` |
| Base commit | `9e0978a9662c9e4bce7cf5dbe30e78f8e992cd9e` |
| Objective | Independently verify Slice C PASS and close FG-023. Bounded Hub-label exception only if MONITOR still claimed Future. |
| Deliverables | Gate close; current-authority reconciliation; close-time pytest. No product-code change (Hub already operational). No new migration. No further actuals. |
| Validation | Dedicated **35 passed**. Focused **149 passed**. Full **593 passed**. Live current = heads `e3f4a5b6c7d8`. Field **39 / 39**. Project **13** five actuals; zero on 1/2/9/11/12. `git diff --check`. |
| Architectural findings | Hub lifecycle already `MONITOR` operational; `LEARN · Future` retained. FG-025 copy sweep not started. |
| Open decisions | FG-025 implementation; FG-024 implementation; Observation Delete; SESSION-EXPIRY. |
| Next milestone | **STOP.** Do **not** start FG-025 or FG-024 from this close. |
| Commit | (this docs commit) |
| Date | 2026-09-07 |

### 2026-09-07 — FG-025 Contractor-Facing UX Language recorded

| Field | Content |
|-------|---------|
| ID | FG-025 — Contractor-Facing UX Language & Terminology Standardization |
| Status | **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED.** Does **not** rewrite UI. Does **not** interrupt FG-023. |
| Branch | `main` |
| Base commit | `ed0c45dec3c4e705b884109466f566d957aea2e2` |
| Objective | Record a future product-wide contractor-facing terminology sweep after FG-023 close and before broad external UAT. Keep internal enums in code. Inventory leakage; do not rewrite copy. |
| Deliverables | [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md); discoverability pins in feature-gates README, roadmap commercialization hygiene, current-authority indexes; FG-024 clarification that FG-025 is not a contract-slice split. |
| Validation | Docs-only. No `app/` / `tests/` / `migrations/` change. `git diff --check`. Product pytest not re-run. |
| Architectural findings | Extends Hub/Field/customer-document copy practice. No existing product-wide UX language standard. MONITOR Hub currently leaks enum names (`MISSING_ACTUALS`, etc.). |
| Open decisions | Implementation authorization after FG-023 close; final contractor wording (not pinned). |
| Next milestone | FG-023 close authorization. Do **not** start FG-025 copy rewrite. |
| Commit | (this docs commit) |
| Date | 2026-09-07 |

### 2026-09-07 — FG-023 MONITOR V1 Slice C (live migrate + office UAT)

| Field | Content |
|-------|---------|
| ID | FG-023 MONITOR V1 — Slice C execution |
| Status | **MIGRATION COMPLETE / OFFICE UAT COMPLETE / PASS.** Gate **NOT CLOSED.** MONITOR V1 **IMPLEMENTED / LIVE-MIGRATED / OFFICE-UAT-VERIFIED / NOT YET CLOSED.** |
| Branch | `main` |
| Base commit | `2cb6e783cbce6951bf54002133296e9144667eff` |
| Objective | Apply existing revision `e3f4a5b6c7d8`; verify schema and Field continuity; office-UAT Hub MONITOR, four-class actuals, and `0.00` supersession on labeled `FG023-UAT-MONITOR`. |
| Deliverables | Live migrate; gitignored backup; synthetic UAT project **id 13**; office UAT on port **5014**; current-authority docs. No product-code change. No new migration. |
| Validation | `flask db upgrade e3f4a5b6c7d8` **PASS**. current = heads = `e3f4a5b6c7d8`. Field **39 / 39**. Hub baseline **PASS**. Four-class create **PASS**. Supersession / `0.00` **PASS**. Independent arithmetic **PASS**. Fail-closed HTTP **AUTOMATED COVERAGE SUFFICIENT FOR V1**. Tests **not rerun** (historical **35 / 149 / 126 / 137 / 593**). Zero UAT actuals on projects 1, 2, 9, 11, 12. |
| Architectural findings | ACTIVE rollup after supersession **175.00**. Successor `0.00` PRESENT not MISSING_ACTUALS. Original 10.00 row preserved SUPERSEDED. Pending/Rejected CO and tax excluded. Field Evidence excluded. |
| Open decisions | FG-023 **close authorization**. SESSION-EXPIRY **DEFERRED**. Observation Delete **QUEUED**. |
| Next milestone | FG-023 close authorization. Do **not** begin FG-024. |
| Commit | (this docs commit) |
| Date | 2026-09-07 |

### 2026-09-07 — FG-024 North American Contract Intelligence recorded

| Field | Content |
|-------|---------|
| ID | FG-024 — North American Contract Intelligence & Legal Content Lifecycle |
| Status | **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED.** Slices A–D **not authorized**. Does **not** interrupt FG-023. |
| Branch | `main` |
| Base commit | `60011d1b37e02da6ad71c5f230c7bb1a6919a164` |
| Objective | Record one linked future Feature Gate for jurisdiction-aware legal content, update engine, frozen contract snapshots, and legal-change monitoring. Preserve the Legal Content Gate. Do not implement. |
| Deliverables | [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md); discoverability pins in feature-gates README, Legal Content Gate, project-document-package, roadmap Item 15, current-authority indexes. |
| Validation | Docs-only. No `app/` / `tests/` / `migrations/` change. `git diff --check`. Product pytest not re-run. |
| Architectural findings | Extends existing Legal Content Gate + ADR-037 jurisdiction identity + issued-document immutability. Permit Rules remain a separate domain. Fail closed; no generic North American fallback. |
| Open decisions | Implementation authorization; Ontario/U.S. content population; later ADR for library schema if required. |
| Next milestone | FG-023 **close authorization**. Do **not** start FG-024 Slice A. |
| Commit | (this docs commit) |
| Date | 2026-09-07 |

### 2026-09-07 — FG-023 MONITOR V1 Slice C implementation preflight

| Field | Content |
|-------|---------|
| ID | FG-023 MONITOR V1 — Slice C preflight |
| Status | **PREFLIGHT COMPLETE / NOT PERFORMED.** Live migrate **NOT RUN.** Office UAT **NOT STARTED.** Gate **NOT CLOSED.** Does **not** authorize Slice C execution. |
| Branch | `main` |
| Base commit | `7dd4d82c927ec2c38a0562e7e1cdedbccabb6662` |
| Objective | Pin live upgrade of existing `e3f4a5b6c7d8`, post-migration verification, UAT project strategy, and closure threshold. |
| Deliverables | Slice C section in [fg-023-monitor-v1-implementation-preflight.md](architecture/fg-023-monitor-v1-implementation-preflight.md); current-authority next-action pins. No `app/` / `tests/` / `migrations/` change. |
| Validation | Docs only. `git diff --check`. Product pytest not rerun. Last product baseline dedicated **35** / focused **149** / historical Slice A focused **126** / pre-Slice-B focused **137** / full **593**. Live current `d2e3f4a5b6c7`. Live **39** / **39**. |
| Architectural findings | No existing live project is a lawful MONITOR happy-path write vessel. Strategy **C**: new labeled `FG023-UAT-MONITOR` required at execution. Explicit `flask db upgrade e3f4a5b6c7d8`. Fail-closed HTTP automated-sufficient for V1. |
| Open decisions | Slice C **execution** authorization. FG-023 close after UAT. SESSION-EXPIRY **DEFERRED**. Observation Delete **QUEUED**. |
| Next milestone | FG-023 Slice C live migrate + office UAT execution. Do not live-migrate from this preflight. |
| Commit | (this docs commit) |
| Date | 2026-09-07 |

### 2026-09-07 — FG-023 MONITOR V1 Slice B (Hub MONITOR + office actuals writes)

| Field | Content |
|-------|---------|
| ID | FG-023 MONITOR V1 — Slice B |
| Status | **IMPLEMENTED / COMMITTED / PUSHED / NOT LIVE-MIGRATED.** Hub `#hub-monitor` **in product code.** Gate **NOT CLOSED.** Office UAT **NOT STARTED.** |
| Branch | `main` |
| Base commit | `b5e68bec0819985b75e306637bb0de79b948045e` |
| Objective | Render MONITOR V1 on Project Hub `#hub-monitor` and add BUILD office actual-cost create/supersede writes without live migrate. |
| Deliverables | `app/services/project_hub.py` `hub["monitor"]`; `app/templates/projects/detail.html` `#hub-monitor`; BUILD POSTs in `app/routes/build.py`; tests in `tests/test_monitor_v1_fg023.py` and `tests/test_project_hub.py`; current-authority docs. No new migration. |
| Validation | Dedicated **35 passed**. Focused **149 passed**. Full suite **593 passed**. Historical Slice A focused **126** and pre-Slice-B focused **137** remain historical. `git diff --check` clean. Live current remains `d2e3f4a5b6c7`. Live **39** / **39**. No live actuals table. |
| Architectural findings | Hub GET continues to pass `hub`. Template consumes `assemble_monitor_v1` output. Writes stay on BUILD. No second MONITOR engine. No DELETE. No in-place amount edit. |
| Open decisions | Slice C live-migrate + office UAT. SESSION-EXPIRY **DEFERRED**. Observation Delete **QUEUED**. |
| Next milestone | FG-023 Slice C live `flask db upgrade` + office UAT. Do not live-migrate from Slice B. |
| Commit | (this commit) |
| Date | 2026-09-07 |

### 2026-09-07 — FG-023 MONITOR V1 Slice B implementation preflight

| Field | Content |
|-------|---------|
| ID | FG-023 MONITOR V1 — Slice B preflight |
| Status | **PREFLIGHT COMPLETE.** Hub UI **NOT IMPLEMENTED.** Gate **NOT CLOSED.** Does **not** authorize Slice B product code. |
| Branch | `main` |
| Base commit | `68b7d02b08553f51e08882bb1dc8ae2b7eb434d3` |
| Objective | Pin Slice B Hub + office actual-cost write workflow against existing Slice A services and Field Observation patterns. |
| Deliverables | Slice B section in [fg-023-monitor-v1-implementation-preflight.md](architecture/fg-023-monitor-v1-implementation-preflight.md); current-authority next-action pins. No `app/` / `tests/` / `migrations/` change. |
| Validation | Docs only. `git diff --check`. Product pytest not rerun. Last product baseline dedicated **23** / current focused **137** / historical Slice A focused **126** / full **581**. Live current `d2e3f4a5b6c7`. Live **39** / **39**. |
| Architectural findings | Writes belong on BUILD POSTs from Hub `#hub-monitor`. `projects.py` GET stays if hub service carries MONITOR. No second model. No new migration. GM Hub display pinned as percent. Focused **137** is the Slice B regression bundle; **126** remains historical Slice A close. |
| Open decisions | Slice B **implementation** authorization. Slice C live-migrate + office UAT. SESSION-EXPIRY **DEFERRED**. Observation Delete **QUEUED**. |
| Next milestone | FG-023 Slice B Hub write routes/forms + `#hub-monitor` implementation. Do not live-migrate from this preflight. |
| Commit | (this docs commit) |
| Date | 2026-09-07 |

### 2026-09-07 — Review Turnover (FG-023 Slice A stop state)

| Field | Content |
|-------|---------|
| ID | Review Turnover (docs only) |
| Status | **TURNOVER PASS** — FG-023 remains **APPROVED / OPEN / NOT CLOSED**; Slice A **IMPLEMENTED / NOT LIVE-MIGRATED** |
| Branch | `main` |
| Base commit | `2553cf09bdd6b8018112d7eb4b682f87aa103b01` |
| Objective | Durably represent FG-023 Slice A stop state; repair stale current-authority pins; rebuild session-handoff §22 for a zero-memory fresh chat. |
| Deliverables | 22-point turnover package; completeness test **NO**; fresh-chat prompt in session-handoff §22. No `app/` / `tests/` / `migrations/` change. |
| Validation | Docs only. `git diff --check`. Product pytest not rerun. Last product baseline dedicated **23** / focused **126** / full **581**. Live current `d2e3f4a5b6c7`. Live **39** / **39**. |
| Architectural findings | Stale §22 still said do not start Item 13 / MONITOR and pinned Alembic current = heads `d2e3f4a5b6c7`. Superseded this pass. |
| Open decisions | Slice B Hub UI authorization. Slice C live-migrate + office UAT. GM display digits. SESSION-EXPIRY **DEFERRED**. Observation Delete **QUEUED**. |
| Next milestone | FG-023 Slice B implementation preflight / authorization. Do not live-migrate. Do not start Slice B product code from this turnover. |
| Commit | `ea9c4b765bd58c5d12414784399e2c29822f1e6f` |
| Date | 2026-09-07 |

### 2026-09-06 — FG-023 MONITOR V1 Slice A (model + services + tests)

| Field | Content |
|-------|---------|
| ID | FG-023 MONITOR V1 — Slice A |
| Status | **IMPLEMENTED / COMMITTED / PUSHED / NOT LIVE-MIGRATED.** Hub UI **NOT IMPLEMENTED.** Gate **NOT CLOSED.** |
| Branch | `main` |
| Base commit | `b50cf6881555c32e25ca4ab7e5c8d7fcac044c0b` |
| Objective | Persist BUILD office Direct Cost actuals and MONITOR V1 projection without Hub UI or live migrate. |
| Deliverables | `ProjectDirectCostActual`; additive revision `e3f4a5b6c7d8`; `app/services/direct_cost_actuals.py`; `app/services/monitor.py` `assemble_monitor_v1`; `tests/test_monitor_v1_fg023.py`; current-authority docs. |
| Validation | Dedicated **23 passed**. Focused **126 passed**. Full suite **581 passed**. `git diff --check` clean. Live current remains `d2e3f4a5b6c7`. Live **39** / **39**. No live actuals rows. |
| Architectural findings | Cross-project supersession requires caller `project` plus org-scoped prior load. Field Events remain evidence only. `MISSING_ACTUALS` is not zero cost. |
| Open decisions | Slice B Hub UI. Slice C live-migrate + office UAT. GM display digits. |
| Next milestone | FG-023 Slice B Hub write routes/forms + `#hub-monitor`. Do not live-migrate from Slice A. |
| Commit | `2553cf09bdd6b8018112d7eb4b682f87aa103b01` |
| Date | 2026-09-06 |

### 2026-09-06 — FG-023 MONITOR V1 implementation preflight

| Field | Content |
|-------|---------|
| ID | FG-023 MONITOR V1 — implementation preflight |
| Status | **PREFLIGHT COMPLETE / READY WITH EXPLICIT NON-BLOCKING NOTES.** Implementation **NOT AUTHORIZED.** [fg-023-monitor-v1-implementation-preflight.md](architecture/fg-023-monitor-v1-implementation-preflight.md). |
| Branch | `main` |
| Base commit | `64b6a5472613f00b862170bd57be07486a11f91f` |
| Objective | Pin later implementation mechanics for approved FG-023. Do not implement MONITOR. Do not create a migration. |
| Deliverables | Canonical preflight artifact; current-authority pins. Frozen FG-023 contract preserved. No product code. No tests. No migration. |
| Validation | Docs-only. Last governed product-changing suite: dedicated FG-021 **20**; focused **148**; full **558**. Live **39** Events / **39** Originals. Alembic current = head `d2e3f4a5b6c7`. |
| Architectural findings | No `ProjectDirectCostActual` exists. Hub `#hub-monitor` remains Future. Field Events remain evidence only. Expected later `down_revision = d2e3f4a5b6c7`. Non-blocking notes: future-dated `incurred_on`; GM display digits; multiple Accepted Proposals. |
| Open decisions | Separate implementation authorization. Observation Delete **QUEUED**. |
| Next milestone | Separate implementation prompt. Do not implement MONITOR from this preflight. |
| Commit | this docs-only preflight record |
| Date | 2026-09-06 |

### 2026-09-06 — FG-023 MONITOR V1 Feature Gate approval

| Field | Content |
|-------|---------|
| ID | FG-023 MONITOR V1 — Estimated versus Actual (approval record) |
| Status | **APPROVED / IMPLEMENTATION NOT STARTED / IMPLEMENTATION NOT YET AUTHORIZED.** [FG-023](feature-gates/FG-023-monitor-v1-estimated-versus-actual.md). |
| Branch | `main` |
| Base commit | `da02f44712bf40911dbda44926db1dd96f0a146c` |
| Objective | Record Joel/ChatGPT approval of FG-023 as written. Do not implement MONITOR. Do not create a migration. |
| Deliverables | Approval-state update on FG-023 and current-authority docs. Frozen contract preserved. No product code. No tests. No migration. |
| Validation | Docs-only. Last governed product-changing suite: dedicated FG-021 **20**; focused **148**; full **558**. Live **39** Events / **39** Originals. Alembic current = head `d2e3f4a5b6c7`. |
| Architectural findings | Correction semantics including `amount >= 0` / `0.00` superseding successor accepted. BUILD office actuals remain in the approved gate (not created). MONITOR comparison remains live projection. Field Events remain evidence only. No new ADR. |
| Open decisions | Separate implementation authorization. Observation Delete **QUEUED**. |
| Next milestone | IMPLEMENTATION READINESS / PREFLIGHT. Do not implement MONITOR from this approval. |
| Commit | this docs-only approval record |
| Date | 2026-09-06 |

### 2026-09-06 — FG-023 MONITOR V1 Feature Gate draft

| Field | Content |
|-------|---------|
| ID | FG-023 MONITOR V1 — Estimated versus Actual (draft) |
| Status | **DRAFT FOR JOEL APPROVAL / NOT APPROVED / NOT AUTHORIZED FOR IMPLEMENTATION.** [FG-023](feature-gates/FG-023-monitor-v1-estimated-versus-actual.md). |
| Branch | `main` |
| Base commit | `1285ecfe0366e7a946323fbac83a1a829e940cb8` |
| Objective | Draft the MONITOR V1 Feature Gate from recon. Do not implement MONITOR. Do not create a migration. |
| Deliverables | FG-023 document; current-authority pins; residual roadmap Item 13 leftover repair. No product code. No tests. No migration. |
| Validation | Docs-only. Last governed product-changing suite: dedicated FG-021 **20**; focused **148**; full **558**. Live **39** Events / **39** Originals. Alembic current = head `d2e3f4a5b6c7`. |
| Architectural findings | Office actuals included in the draft gate as BUILD-owned incremental Direct Cost. MONITOR comparison is live projection. Field Events remain evidence only. No new ADR. |
| Open decisions | Joel approval of FG-023. Observation Delete **QUEUED**. |
| Next milestone | Joel review. Do not implement MONITOR. |
| Commit | this docs-only draft |
| Date | 2026-09-06 |

### 2026-09-06 — MONITOR V1 / Item 13 implementation reconnaissance

| Field | Content |
|-------|---------|
| ID | Roadmap Item 13 MONITOR V1 implementation reconnaissance |
| Status | **RECON COMPLETE / NOT IMPLEMENTED / NOT FEATURE-GATED / NOT AUTHORIZED FOR CODE.** [monitor-v1-implementation-reconnaissance.md](architecture/monitor-v1-implementation-reconnaissance.md). ADR-021 remains **Accepted** architecture only. |
| Branch | `main` |
| Base commit | `c1ec5f35e77f263d8191300a34e87490cfcb81bb` |
| Objective | Freeze smallest lawful MONITOR V1 design. Do not implement MONITOR. Do not create a Feature Gate. |
| Deliverables | Recon artifact; current-authority pins; three CURRENT-looking stale-authority repairs. No product code. No tests. No migration. No database mutation. |
| Validation | Docs-only. Last governed product-changing suite: dedicated FG-021 **20**; focused **148**; full **558**. Live **39** Events / **39** Originals. Alembic current = head `d2e3f4a5b6c7`. |
| Architectural findings | No verified Actual Direct Cost records exist. Field Events are evidence only. CO is sell-side revenue delta, not cost. Smallest useful V1 is Hub projection plus recommended BUILD office Direct Cost actuals. Forecast out of V1. Ready for Feature Gate draft. |
| Open decisions | Include office actuals in V1 (recommended yes). Incremental vs restated-to-date. No MONITOR snapshot table in V1. Observation Delete **QUEUED**. |
| Next milestone | Draft MONITOR V1 Feature Gate. Do not implement MONITOR. |
| Commit | this docs-only recon |
| Date | 2026-09-06 |

### 2026-09-06 — FG-021 CLOSED with SESSION-EXPIRY deferred exception

| Field | Content |
|-------|---------|
| ID | FG-021 closure (OPTION 2 explicit deferred SESSION-EXPIRY exception) |
| Status | **CLOSED.** IMPLEMENTED / LIVE-MIGRATED / REAL-IPHONE UAT COMPLETE SUBJECT TO THE EXPLICIT SESSION-EXPIRY DEFERRED EXCEPTION. [FG-021](feature-gates/FG-021-field-web-v1-today-and-capture.md). **SESSION-EXPIRY RECOVERY: DEFERRED / NOT YET EXERCISED** (NOT PASS / NOT FAIL / NOT N/A / NOT WAIVED). **OLDER SUPPORTED IPHONE / SAFARI WAIVED AS NOT PRACTICAL.** Observation Delete **QUEUED / NOT AUTHORIZED / NOT IMPLEMENTED / NON-BLOCKING**. Live current = head `d2e3f4a5b6c7`. |
| Branch | `main` |
| Base commit | `24d291603c62c88e620c17a86222a6dd40603758` |
| Objective | Close FG-021 under Joel/ChatGPT-authorized OPTION 2. Do not claim SESSION-EXPIRY PASS. Do not start Item 13. |
| Deliverables | Current-authority documentation/governance closure. No product code. No tests. No migration. No database mutation. |
| Validation | Docs-only. Last governed product-changing suite: dedicated FG-021 **20**; focused **148**; full **558**. Live **39** Events / **39** Originals. Alembic current = head `d2e3f4a5b6c7`. |
| Architectural findings | Recovery path (persist → API 401 → IndexedDB retained → login `next` → same-UUID replay) is implemented. Current product has no naturally exercisable real-iPhone session-expiry trigger. Event **37** / Original **37** are authenticated residue, not recovery evidence. |
| Open decisions | Observation Delete **QUEUED**. Session revocation / idle timeout **FUTURE AUTHENTICATION HARDENING / NOT FG-021**. Item 13 MONITOR **NOT AUTHORIZED**. |
| Next milestone | **STOP.** Do not start Item 13 / MONITOR. Do not implement Observation Delete. Do not implement session revocation. |
| Commit | this docs-only close |
| Date | 2026-09-06 |

### 2026-09-02 — FG-021 live migration to d2e3f4a5b6c7

| Field | Content |
|-------|---------|
| ID | FG-021 live-migration increment (gate **NOT CLOSED**) |
| Status | **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT PENDING.** [FG-021](feature-gates/FG-021-field-web-v1-today-and-capture.md) live current = head `d2e3f4a5b6c7`. Real iPhone UAT **not complete**. |
| Branch | `main` |
| Base commit | `5c36f6fcdf3c54aab9d103cd5152685382618984` |
| Objective | Apply live `flask db upgrade` to `d2e3f4a5b6c7` after one gitignored pre-migration SQLite copy. Do not close the gate. |
| Deliverables | Live schema UUID columns/constraints; docs status LIVE-MIGRATED / IPHONE UAT PENDING. Product/test/migration files unchanged. |
| Validation | Dedicated FG-021 **13 passed**. Focused **141 passed**. Full suite **551 passed**. `flask db current` = `flask db heads` = `d2e3f4a5b6c7`. |
| Architectural findings | No backfill. Existing FG-020 rows remain client-UUID NULL. Named UNIQUE constraints present in live SQLite. Backup not committed. |
| Open decisions | Real iPhone Safari UAT. Gate close. |
| Next milestone | Real iPhone UAT / FG-021 close under a separate prompt. |
| Commit | verify `git rev-parse HEAD` after this live-migration docs commit |
| Date | 2026-09-02 |

### 2026-09-02 — FG-021 Field Web V1 implemented / live migration pending

| Field | Content |
|-------|---------|
| ID | FG-021 coded increment (gate **NOT CLOSED**) |
| Status | **IMPLEMENTED / LIVE MIGRATION PENDING.** [FG-021](feature-gates/FG-021-field-web-v1-today-and-capture.md) landed. Live current remains `c1d2e3f4a5b6`. Graph head `d2e3f4a5b6c7`. Real iPhone UAT **not complete**. |
| Branch | `main` |
| Base commit | `eb4466c4d090aaf366d39ebe2e3ff8ec1a382993` |
| Objective | Land Field Web V1 Today + Project confirm + Capture and idempotent Event/Original API without applying the live migration or closing the gate. |
| Deliverables | `/field` routes/templates/CSS/JS; `client_capture_uuid` / `client_original_uuid`; Event/Original 201/200/409; display GET; revision `d2e3f4a5b6c7`; dedicated tests. |
| Validation | Dedicated FG-021 **13 passed**. Focused **141 passed**. Full suite **551 passed**. Live current `c1d2e3f4a5b6` verified (upgrade not run). |
| Architectural findings | Frozen recon held. Office Hub unchanged. No PWA. No transcription. Native Signing unchanged. |
| Open decisions | Live upgrade authorization. Real iPhone UAT. Gate close. |
| Next milestone | Live `flask db upgrade` + iPhone UAT close, under a separate prompt. |
| Commit | verify `git rev-parse HEAD` after this implementation commit |
| Date | 2026-09-02 |

### 2026-09-02 — ADR-043 Accepted + FG-021 approved + implementation recon

| Field | Content |
|-------|---------|
| ID | Governance acceptance / recon (not a coded milestone) |
| Status | **RECORDED / NOT IMPLEMENTED.** [ADR-043](adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md) **Accepted**. [FG-021](feature-gates/FG-021-field-web-v1-today-and-capture.md) **APPROVED / IMPLEMENTATION NOT STARTED**. Implementation recon **COMPLETE**. Field Web product **NOT STARTED**. |
| Branch | `main` |
| Base commit | Draft `6273fa4`; tooling `d69cfb66aaad5ad178375ddb2eaddc55091f6a7c`; Item 12 recon `24959d2650021380bbe8b1ef9ba94d5857debd26`. |
| Objective | Accept ADR-043, Approve FG-021, and freeze FG-021 implementation design without product code or a migration. |
| Deliverables | ADR-043 Accepted; FG-021 approved/not started; [architecture/fg-021-field-web-v1-implementation-reconnaissance.md](architecture/fg-021-field-web-v1-implementation-reconnaissance.md); index/handoff updates. No migration. No product code. |
| Validation | Docs only. Alembic current = heads `c1d2e3f4a5b6` verified. Full suite **538 passed** claimed, not rerun. |
| Architectural findings | Event UUID UNIQUE(org, uuid) String(36) nullable. Original UUID UNIQUE(event, uuid) String(36) nullable. UUID v4 36-char lowercase. Event/Original 201/200/409. IndexedDB `calibai-field-v1`. No PWA. Safari reopen/retry. Designed revision `d2e3f4a5b6c7`. Readiness: READY FOR BOUNDED IMPLEMENTATION after a separate prompt. |
| Open decisions | Separate implementation prompt. Native Signing production remains counsel-blocked. |
| Next milestone | **STOP Field Web product implementation** until a separate FG-021 implementation prompt. |
| Commit | verify `git rev-parse HEAD` after this docs commit |
| Date | 2026-09-02 |

### 2026-09-01 — ADR-043 Proposed + FG-021 draft (not approved)

| Field | Content |
|-------|---------|
| ID | Governance draft (not a coded milestone) |
| Status | **RECORDED / NOT IMPLEMENTED.** [ADR-043](adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md) **Proposed**. [FG-021](feature-gates/FG-021-field-web-v1-today-and-capture.md) **DRAFT FOR JOEL REVIEW / NOT APPROVED**. Field Web implementation **NOT AUTHORIZED**. |
| Branch | `main` |
| Base commit | Item 12 recon `24959d2650021380bbe8b1ef9ba94d5857debd26`; copy-icon rule `d69cfb66aaad5ad178375ddb2eaddc55091f6a7c` committed separately first (not pushed). |
| Objective | Draft Field Web V1 capture-reliability ADR and Feature Gate for Joel review without accepting, approving, or implementing. |
| Deliverables | ADR-043 Proposed; FG-021 draft; index/handoff updates. No migration. No product code. |
| Validation | Docs only. Alembic current = heads `c1d2e3f4a5b6` verified. Full suite **538 passed** claimed, not rerun. |
| Architectural findings | V1 = Today + Project confirm + Capture. Flask/Jinja + focused JS. IndexedDB pending hold. Server idempotent replay required. Plan/Derived/CO visibility deferred. Real iPhone UAT required to close FG-021. |
| Open decisions | Joel Accept ADR-043 and Approve FG-021. Native Signing production remains counsel-blocked. |
| Next milestone | **STOP Field Web implementation.** Implementation requires Accepted ADR-043 + Approved FG-021 + a separate implementation prompt. |
| Commit | uncommitted docs; verify `git rev-parse HEAD` |
| Date | 2026-09-01 |

### 2026-09-01 — Item 12 Field Web recon complete + Native Signing counsel pin

| Field | Content |
|-------|---------|
| ID | Architecture reconnaissance + governance pin (not a Feature Gate) |
| Status | **RECORDED / NOT IMPLEMENTED.** Item 12 recon **COMPLETE / NOT IMPLEMENTED**. Native Signing **DEVELOPMENT MAY PROCEED UNDER SEPARATE GOVERNANCE**; **PRODUCTION ACTIVATION BLOCKED PENDING COUNSEL**. |
| Branch | `main` |
| Base commit | `42b9c792b7c4fd968ed46be0ff15975cf3880eb5` |
| Objective | Close Item 12 architecture reconnaissance as the canonical pin and record Joel’s Native Signing counsel pin so counsel is not treated as a general development hold. |
| Deliverables | [architecture/field-web-today-and-capture.md](architecture/field-web-today-and-capture.md) (canonical; extended). Counsel pin recorded across governed indexes. FG-021 / ADR-043 **not created**. |
| Validation | Docs only. No pytest this pass. Alembic current = heads `c1d2e3f4a5b6` verified. Full suite **538 passed** claimed, not rerun. |
| Architectural findings | Field V1 = Flask/Jinja `/field` + `/api/v1`. Server-side Event/Original idempotency required (schema gap vs FG-020). API display rendition GET missing. Plan access and CO signing visibility deferred from V1. |
| Open decisions | Joel may authorize FG-021 + ADR-043 drafting **or** a separately governed Native Signing development track. Production signing remains counsel-blocked. |
| Next milestone | **STOP Field Web implementation.** Do not create FG-021 / ADR-043 unless Joel authorizes. |
| Commit | uncommitted docs; verify `git rev-parse HEAD` |
| Date | 2026-09-01 |

### 2026-09-01 — FG-020 live migration / office UAT close

| Field | Content |
|-------|---------|
| ID | [FG-020](feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) |
| Status | **CLOSED / OPERATIONAL FOR UAT.** Item 11 **COMPLETE**. Item 12 **ELIGIBLE FOR SEPARATE GOVERNANCE / NOT AUTHORIZED**. |
| Branch | `main` |
| Base commit | `473b04eff8766f917e46abf793cc699b179a4fb6` |
| Objective | Verify live Alembic current=head and close office UAT of Field Observations + HEIC JPEG renditions. |
| Deliverables | Live current = head `c1d2e3f4a5b6`; office UAT port **5013**; project 12 events 9–17 plus prior 1–8; close docs. |
| Validation | Dedicated **44 passed**; focused **128 passed**; full suite **538 passed**. |
| Architectural findings | Commercial fingerprints unchanged. HEIC Original SHA preserved. Renditions regenerable and independently stored. API second successor and derived re-decision **409**. FG-019 mutation lock intact. |
| Open decisions | Field Web Feature Gate not created. Native Signing waiting for counsel. Closeout FUTURE. |
| Next milestone | **STOP.** Do not start Field Web. Give counsel the Native Signing spec. |
| Commit | this commit; verify `git rev-parse HEAD` |
| Date | 2026-09-01 |

### 2026-09-01 — Native Signed Change Order counsel-review specification

| Field | Content |
|-------|---------|
| ID | Governance specification (not a Feature Gate) |
| Status | **RECORDED / NOT IMPLEMENTED.** Counsel process-review specification **PREPARED**. Native Signing recon remains **COMPLETE**. Recommendation **NATIVE V1**. Implementation **NOT AUTHORIZED**. No Feature Gate. No ADR. |
| Branch | `main` |
| Base commit | `4538e6f3e8a6bdbe4cb01e2555ebf5a13ce41a86` |
| Objective | Give Ontario construction counsel a concise review specification of the proposed Native electronic-signing process for Brayman Change Orders. |
| Deliverables | [legal/native-signing-process-counsel-review.md](legal/native-signing-process-counsel-review.md) |
| Validation | Docs only. No pytest. |
| Architectural findings | None new. Overlay existing Change Order. BRAYMAN APPROVED ≠ CUSTOMER SIGNED. SHA-256 + immutable Signing Record pending counsel vs PAdES. |
| Open decisions | Counsel YES/NO/MODIFY list in the spec. Do not implement until Joel authorizes a Feature Gate after counsel. |
| Next milestone | Give counsel the spec. No signing Feature Gate from this pass. FG-020 remains **IMPLEMENTED / LIVE MIGRATION PENDING**. |
| Commit | this commit; verify `git rev-parse HEAD` |
| Date | 2026-09-01 |

### 2026-08-31 — Contract / e-signature / signed Change Order reconnaissance (native signing delta)

| Field | Content |
|-------|---------|
| ID | Architecture reconnaissance (not a Feature Gate) |
| Status | **RECORDED / NOT IMPLEMENTED.** Reconnaissance **COMPLETE**. Recommendation **NATIVE V1** subject to Ontario counsel review of the signing process. Implementation **NOT AUTHORIZED**. |
| Branch | `main` |
| Base commit | `3a31ed052cc4813b98d94ec8c71ec9a1b2b57946` |
| Objective | Evaluate CalibAi-native electronic signing vs DocuSign vs Adobe Acrobat Sign without assuming a TSP. |
| Deliverables | [architecture/contract-esignature-and-signed-change-order.md](architecture/contract-esignature-and-signed-change-order.md) |
| Validation | Docs only. No pytest. |
| Architectural findings | Signing mechanism ≠ commercial SoR. CO overlay on existing `ChangeOrder`. Click-to-sign + typed name. Application-level PDF hashing pending counsel vs PAdES. |
| Open decisions | Counsel process review; optional vendor pricing research; do not implement. |
| Next milestone | **STOP.** No signing Feature Gate from this pass. |
| Commit | this commit; verify `git rev-parse HEAD` |
| Date | 2026-08-31 |

### 2026-08-31 — FG-020 Media Compatibility increment (HEIC/HEIF → JPEG)

| Field | Content |
|-------|---------|
| ID | FG-020 Compatible Rendition increment / still live-migration pending |
| Status | [FG-020](feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) remains **IMPLEMENTED / LIVE MIGRATION PENDING**. Image-only Compatible Renditions **implemented**. Project Closeout **FUTURE**. Item 12 **BLOCKED**. |
| Branch | `main` |
| Base commit | `77d496367f9e6f003eb69949adb3bd82c6cadfd7` |
| Objective | Automatic HEIC/HEIF → JPEG Compatible Rendition after Original Source preservation. Preserve storage-lifecycle docs. Do not live-migrate. Do not start Field Web or Closeout. |
| Deliverables | `app/services/build_rendition.py`; desktop `/display` JPEG route; Event Detail Photo rendering; `Pillow` + `pillow-heif`; `tests/test_build_media_compatibility_fg020.py`; storage-lifecycle pin committed with this increment. No new Alembic revision. |
| Validation | Dedicated media compatibility **11 passed**. Combined dedicated FG-020 **44 passed**. Focused Hub+FG-018+FG-019+FG-020 **128 passed**. Full suite **538 passed**. Live current remains `b0c1d2e3f4a5`. Repository head remains `c1d2e3f4a5b6`. |
| Next | Separate live-migration / office UAT prompt. Do not mark FG-020 closed. Do not start Field Web. Do not implement Closeout. |

### 2026-08-31 — BUILD media compatibility + project-close storage lifecycle (docs only)

| Field | Content |
|-------|---------|
| ID | Docs-only BUILD media storage-lifecycle clarification |
| Status | Architecture pin recorded. [FG-020](feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) remains **IMPLEMENTED / LIVE MIGRATION PENDING**. Compatible Renditions **not implemented**. Project Closeout **FUTURE / NOT AUTHORIZED**. Item 12 **BLOCKED**. |
| Branch | `main` |
| Base commit | `77d496367f9e6f003eb69949adb3bd82c6cadfd7` |
| Objective | Clarify Original Source vs Compatible Rendition vs Closed Project Archive. Do not implement BUILD. Do not implement Closeout. |
| Deliverables | [build-media-storage-lifecycle.md](architecture/build-media-storage-lifecycle.md); subsequent status on ADR-042 / FG-020; indexes; current-state / session-handoff / roadmap / project-state-report / chat-workflow-log. No `app/` / `tests/` / `migrations/`. |
| Validation | Docs-only. Product tests not rerun. Governed baseline remains **527 passed**. Live current remains `b0c1d2e3f4a5`. |
| Next | **STOP.** Joel/ChatGPT review. Then a revised FG-020 increment authorization if Compatible Renditions are to land. Do not start Field Web. |

### 2026-08-31 — Implement FG-020 BUILD Field Capture V1 (live migration pending)

| Field | Content |
|-------|---------|
| ID | FG-020 implementation / pre-live-migration stop |
| Status | [FG-020](feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) **IMPLEMENTED / LIVE MIGRATION PENDING**. Not **CLOSED / OPERATIONAL FOR UAT**. Item 11 implemented / live migration pending. Item 12 **BLOCKED / NOT AUTHORIZED**. |
| Branch | `main` |
| Base commit | `440d7c7c50306499fb720e874f7d0352031090e8` |
| Objective | Implement bounded FG-020 Field Observation foundation. Preserve HEIC/HEIF originals. Do not live-migrate. Do not start Field Web. |
| Deliverables | Additive revision `c1d2e3f4a5b6`; BUILD models/services/storage; office Field Observations; bounded `/api/v1` BUILD; UAT CLI; dedicated tests; governed docs. |
| Validation | Dedicated **33 passed**. Focused **370 passed**. Full suite **527 passed**. Live current remains `b0c1d2e3f4a5`. Repository head `c1d2e3f4a5b6`. Live `flask db upgrade` **not run**. |
| Next | Separate live-migration / office UAT prompt. Do not mark FG-020 closed. Do not start Field Web. |

### 2026-08-31 — Approve FG-020 and record BUILD implementation reconnaissance (docs only)

| Field | Content |
|-------|---------|
| ID | Docs-only FG-020 approval + implementation reconnaissance |
| Status | [FG-020](feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) **APPROVED / IMPLEMENTATION NOT STARTED**. Recon recorded. BUILD implementation **NOT STARTED**. Item 11 **approved / not started**. Item 12 **BLOCKED / NOT AUTHORIZED**. |
| Branch | `main` |
| Objective | Approve FG-020. Record recon. Do not implement BUILD. |
| Deliverables | FG-020 approved; implementation reconnaissance; indexes; current-state / session-handoff / roadmap / project-state-report / chat-workflow-log. No `app/` / `tests/` / `migrations/`. |
| Validation | `git diff --check`. Docs-only; product tests not rerun. Governed baseline remains **494 passed**. Alembic current = head `b0c1d2e3f4a5`. |
| Next | **STOP.** Joel/ChatGPT review of recon. Then a separate implementation prompt. Do not start Field Web. |

### 2026-08-31 — Accept ADR-042 and draft FG-020 (governance only)

| Field | Content |
|-------|---------|
| ID | Docs-only ADR-042 acceptance + FG-020 draft |
| Status | [ADR-042](adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) **Accepted**. [FG-020](feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) **DRAFT FOR JOEL REVIEW / NOT APPROVED**. BUILD implementation **NOT STARTED**. Item 11 **governance in progress / NOT AUTHORIZED**. Item 12 **BLOCKED / NOT AUTHORIZED**. |
| Branch | `main` |
| Objective | Accept BUILD field-evidence architecture. Draft FG-020. Do not implement BUILD. |
| Deliverables | ADR-042 Accepted; FG-020 draft; indexes; current-state / session-handoff / roadmap / project-state-report / chat-workflow-log. No `app/` / `tests/` / `migrations/`. |
| Validation | `git diff --check`. Docs-only; product tests not rerun. Governed baseline remains **494 passed**. Alembic current = head `b0c1d2e3f4a5`. |
| Next | **STOP.** Joel review of FG-020. Do not implement BUILD. Do not start Field Web. |

### 2026-08-31 — Draft ADR-042 BUILD field evidence architecture (governance only)

| Field | Content |
|-------|---------|
| ID | Docs-only ADR-042 governance draft |
| Status | [ADR-042](adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) **Proposed / FOR JOEL REVIEW**. Not accepted. FG-020 **not created**. [FG-019](feature-gates/FG-019-shared-api-foundation-v1.md) remains **CLOSED / OPERATIONAL FOR UAT**. Item 10 **COMPLETE**. Item 11 **ELIGIBLE FOR SEPARATE GOVERNANCE / NOT AUTHORIZED**. |
| Branch | `main` |
| Objective | Memorialize iPhone-first / voice-first / desktop-review BUILD field-evidence architecture as a Proposed ADR. Do not implement BUILD. Do not create FG-020. |
| Deliverables | ADR-042; ADR index; CAR-001 subsequent status; BUILD module; current-state / session-handoff / roadmap / project-state-report / chat-workflow-log. No `app/` / `tests/` / `migrations/`. |
| Validation | `git diff --check`. Docs-only; product tests not rerun. Governed baseline remains **494 passed**. Alembic current = head `b0c1d2e3f4a5`. |
| Next | **STOP.** Joel review of ADR-042. Do not create FG-020. Do not start BUILD. |

### 2026-08-31 — FG-019 Shared API Foundation V1 implementation and close

| Field | Content |
|-------|---------|
| ID | FG-019 implementation / UAT close |
| Status | [FG-019](feature-gates/FG-019-shared-api-foundation-v1.md) **CLOSED / OPERATIONAL FOR UAT**. Roadmap item 10 **COMPLETE**. [FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) remains **CLOSED / OPERATIONAL FOR UAT**. BUILD Item 11 **ELIGIBLE FOR SEPARATE GOVERNANCE / NOT AUTHORIZED**. |
| Branch | `main` |
| Objective | Approve and implement GET-only `/api/v1` cookie/session Shared API. No migration. No BUILD. |
| Deliverables | `app/routes/api_v1.py`; `app/services/shared_api.py`; API JSON auth/error handling in `app/__init__.py`; `tests/test_shared_api_fg019.py`; governed docs. Alembic unchanged `b0c1d2e3f4a5`. |
| Validation | Dedicated **34 passed**. Focused **326 passed**. Full suite **494 passed**. API UAT port **5012**. |
| Next | **STOP.** Do not start BUILD. |

### 2026-08-31 — Draft FG-019 Shared API Foundation V1

| Field | Content |
|-------|---------|
| ID | Docs-only FG-019 governance draft |
| Status | [FG-019](feature-gates/FG-019-shared-api-foundation-v1.md) **DRAFT FOR JOEL REVIEW / NOT APPROVED**. [FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) remains **CLOSED / OPERATIONAL FOR UAT**. Roadmap item 10 remains **PARTIALLY COMPLETE**. Shared API product code **NOT STARTED**. BUILD remains **BLOCKED**. |
| Branch | `main` |
| Objective | Draft the remaining Shared API slice of roadmap item 10 as a Feature Gate. Do not implement `/api/`. Do not create an ADR. |
| Deliverables | FG-019 draft; Feature Gate / docs indexes; current-state; session-handoff; project-state-report; roadmap; chat-workflow-log; milestones. No `app/` / `tests/` / `migrations/`. |
| Validation | `git diff --check`. Docs-only; product tests not rerun. Governed baseline remains **460 passed**. |
| Next | **STOP.** Joel review of FG-019. Do not implement Shared API from this pass. |

### 2026-08-31 — Post-FG-018 current-state documentation reconciliation

| Field | Content |
|-------|---------|
| ID | Post-FG-018 docs reconciliation |
| Status | Docs-only. [FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) remains **CLOSED / OPERATIONAL FOR UAT**; [ADR-041](adr/ADR-041-user-membership-and-office-authentication.md) remains **Accepted**. Roadmap item 10 recorded **PARTIALLY COMPLETE**. |
| Branch | `main` |
| Objective | Repair current-state documentation lag identified by the post-FG-018 read-only roadmap reconciliation. |
| Deliverables | Current-state / roadmap / ADR index / CAR-001 subsequent status / ADR-041 current-status / handoff / project-state-report / Feature Gate index clarifications. No `app/` / `tests/` / `migrations/`. No FG-019. No ADR created or accepted. |
| Validation | `git diff --check`. Docs-only; product tests not rerun. |
| Next | **STOP.** No Feature Gate authorized. Do not start Shared API reconnaissance from this pass. |

### 2026-08-31 — FG-018 live migration + office UAT close

| Field | Content |
|-------|---------|
| ID | FG-018 live migrate / bootstrap / UAT |
| Status | [FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) **CLOSED / OPERATIONAL FOR UAT**; [ADR-041](adr/ADR-041-user-membership-and-office-authentication.md) **Accepted** |
| Branch | `main` |
| Objective | Apply `b0c1d2e3f4a5` live; bootstrap first ORG-001 user; bounded authenticated office UAT. |
| Deliverables | Live current = head `b0c1d2e3f4a5`; local-only SECRET_KEY; CLI bootstrap; office UAT port **5011**; docs close. Product code unchanged this pass. |
| Validation | Dedicated **37 passed**. Focused **460 passed**. Full suite **460 passed**. Office UAT port **5011**. |
| Next | **STOP.** Do not start shared API, BUILD, RBAC, or org-switcher. |

### 2026-08-31 — Implement FG-018 organization authentication (pre-live-migration)

| Field | Content |
|-------|---------|
| ID | FG-018 implementation |
| Status | [FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) **IMPLEMENTED / LIVE MIGRATION PENDING**; [ADR-041](adr/ADR-041-user-membership-and-office-authentication.md) **Accepted** |
| Branch | `main` |
| Objective | Implement office User, membership, login/logout, CSRF, SECRET_KEY fail-closed, CLI bootstrap/reset, membership org context, bounded actor snapshots, shell org isolation. Do not live-migrate. |
| Deliverables | `users` / `user_memberships`; revision `b0c1d2e3f4a5`; Flask-Login + Flask-WTF; dedicated tests; docs. |
| Validation | Dedicated FG-018 **37 passed**. Full suite **460 passed**. Live `flask db current` remains `a9b0c1d2e3f4`. Repository head `b0c1d2e3f4a5`. `git diff --check` clean. Live upgrade **not run**. |
| Next | **STOP. Do not live-migrate.** Wait for Joel/ChatGPT authorization to apply `b0c1d2e3f4a5`, bootstrap ORG-001, set SECRET_KEY, and UAT. Do not mark CLOSED. |

### 2026-08-30 — Accept ADR-041 / Approve FG-018 / implementation reconnaissance

| Field | Content |
|-------|---------|
| ID | Docs-only Item 10 acceptance + reconnaissance |
| Status | [ADR-041](adr/ADR-041-user-membership-and-office-authentication.md) **Accepted**; [FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) **APPROVED / IMPLEMENTATION NOT STARTED** |
| Branch | `main` |
| Objective | Accept ADR-041, approve FG-018, record implementation reconnaissance. Do not implement. |
| Deliverables | Status updates; FG-018 reconnaissance section. No `app/` / `tests/` / `migrations/`. |
| Validation | Docs only. `git diff --check`. Tests not rerun. Alembic current/head remains `a9b0c1d2e3f4`. |
| Next | **STOP product implementation.** Joel/ChatGPT review reconnaissance. Separate implementation prompt required. Shared API deferred. BUILD remains blocked. |

### 2026-08-30 — Draft ADR-041 and FG-018 (Item 10 office authentication)

| Field | Content |
|-------|---------|
| ID | Docs-only Item 10 governance draft |
| Status | [ADR-041](adr/ADR-041-user-membership-and-office-authentication.md) **Proposed**; [FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) **DRAFT / NOT APPROVED**; implementation **NOT STARTED** |
| Branch | `main` |
| Objective | Draft User/membership/office-auth ADR and FG-018. Do not accept, approve, or implement. |
| Deliverables | ADR-041; FG-018; index/current-state/handoff/roadmap updates. No `app/` / `tests/` / `migrations/`. |
| Validation | Docs only. `git diff --check`. Tests not rerun. Alembic current/head remains `a9b0c1d2e3f4`. |
| Next | **STOP product implementation.** Joel/ChatGPT review. Do not implement Authentication. Shared API deferred. BUILD remains blocked. |

### 2026-08-30 — Post-FG-017 roadmap documentation reconciliation

| Field | Content |
|-------|---------|
| ID | Docs-only roadmap / turnover reconciliation |
| Status | FG-017 remains **CLOSED / OPERATIONAL FOR UAT**; ADR-040 **Accepted**; no next Feature Gate |
| Branch | `main` |
| Objective | Repair stale CURRENT/FUTURE/NEXT language after FG-017 close so the repository is one coherent post-FG-017 record. |
| Deliverables | Roadmap, current-state, session-handoff, project-state-report, Feature Gate index, ADR index, related index docs. No `app/` / `tests/` / `migrations/`. |
| Validation | Docs only. `git diff --check`. Tests not rerun. Alembic current/head remains `a9b0c1d2e3f4`. |
| Next | **STOP.** Do not start Authentication. Do not create FG-018. Expected next *substantive* step only after Joel/ChatGPT review: separately authorized Authentication architecture and Feature-Gate reconnaissance. |

### 2026-08-30 — FG-017 live migration + office UAT close

| Field | Content |
|-------|---------|
| ID | FG-017 live migrate / UAT |
| Status | [FG-017](feature-gates/FG-017-organization-brand-profile-v1.md) **CLOSED / OPERATIONAL FOR UAT**; [ADR-040](adr/ADR-040-organization-brand-profile.md) **Accepted** |
| Branch | `main` |
| Objective | Apply `a9b0c1d2e3f4` live; ensure Brand Profiles; backfill Issued/Accepted snapshots; bounded office UAT. |
| Deliverables | Live current = head `a9b0c1d2e3f4`; ORG-001 logo custody; isolation org without Brayman logo; UAT proposals 2–4; docs close. Product code unchanged. |
| Validation | Dedicated **22 passed**. Focused **97 passed**. Full suite **423 passed**. Office UAT port **5010**. |
| Next | **STOP.** Do not start the next Feature Gate. |

### 2026-08-30 — Implement FG-017 Organization Brand Profile V1 (pre-live-migration)

| Field | Content |
|-------|---------|
| ID | FG-017 implementation |
| Status | [FG-017](feature-gates/FG-017-organization-brand-profile-v1.md) **IMPLEMENTED / LIVE MIGRATION PENDING**; [ADR-040](adr/ADR-040-organization-brand-profile.md) **Accepted** |
| Branch | `main` |
| Objective | Bounded Brand Profile V1 + Proposal snapshot. No live migrate. |
| Deliverables | `organization_brand_profiles`; `proposal_brand_snapshots`; `instance/brand_logos`; Settings `/settings/brand-profile`; Proposal preview/PDF consume snapshot-or-current; revision `a9b0c1d2e3f4`; dedicated tests 22; full suite 423 |
| Validation | Focused 119 passed. Full suite **423 passed**. Live `flask db current` remains `f8a9b0c1d2e3`. `git diff --check`. |
| Next | **STOP.** Separate live-migrate / UAT prompt. Do not mark CLOSED. |

### 2026-08-30 — Accept ADR-040 / Approve FG-017 / implementation reconnaissance

| Field | Content |
|-------|---------|
| ID | Governance approval + reconnaissance (docs only) |
| Status | [ADR-040](adr/ADR-040-organization-brand-profile.md) **Accepted**; [FG-017](feature-gates/FG-017-organization-brand-profile-v1.md) **APPROVED / IMPLEMENTATION NOT STARTED**; Brand Profile **NOT IMPLEMENTED** |
| Branch | `main` |
| Objective | Accept ADR-040, approve FG-017, record exact implementation plan. No product code. |
| Deliverables | Status updates; FG-017 reconnaissance section (schema, freeze, storage, tests). No `app/` / `tests/` / `migrations/`. |
| Validation | Docs only. `git diff --check`. Tests not rerun. |
| Next | **STOP.** Separate FG-017 implementation prompt required. |

### 2026-08-30 — Organization Brand Profile ADR + Feature Gate governance draft

| Field | Content |
|-------|---------|
| ID | Governance draft (docs only) |
| Status | **DRAFTED FOR JOEL REVIEW** — [ADR-040](adr/ADR-040-organization-brand-profile.md) **Proposed**; [FG-017](feature-gates/FG-017-organization-brand-profile-v1.md) **DRAFT / NOT APPROVED**; Brand Profile **NOT IMPLEMENTED** |
| Branch | `main` |
| Objective | Draft Organization Brand Profile architecture decision and first bounded Feature Gate from the accepted reconnaissance. Docs only. |
| Deliverables | ADR-040 Proposed; FG-017 Draft; index/status updates. No `app/` / `tests/` / `migrations/`. No live migrate. |
| Validation | Docs only. `git diff --check`. Tests not rerun. |
| Next | **STOP.** Wait for Joel / ChatGPT review. Do not implement Brand Profile. |

### 2026-08-30 — Post-FG-016 full documentation / governance turnover

| Field | Content |
|-------|---------|
| ID | Review Turnover (docs only) |
| Status | **TURNOVER RECONCILED** — FG-016 remains **CLOSED / OPERATIONAL FOR UAT** |
| Branch | `main` |
| Objective | Durably represent approved CalibAi decisions; eliminate stale present-tense language; rebuild session-handoff for zero-memory fresh chats. |
| Deliverables | SHA pin `fa591f14b2eb99db75c4e3720fdeb30d14a8f77a`; Alembic current=head `f8a9b0c1d2e3`; Pratt UAT evidence; STOP authorization; fresh-chat prompt in session-handoff §22. |
| Validation | Docs only. `git diff --check`. No `app/` / `tests/` / `migrations/`. Tests not rerun. |
| Next | **STOP.** No next product gate authorized. Organization Brand Profile reconnaissance is a candidate only. |

### 2026-08-30 — FG-016 Ontario / Ottawa Permit Intelligence POC closed (live migration + Pratt UAT)

| Field | Content |
|-------|---------|
| ID | [FG-016](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) |
| Status | **CLOSED / OPERATIONAL FOR UAT** |
| Branch | `main` |
| Objective | Apply `f8a9b0c1d2e3` to development/UAT; bounded live office Pratt Permit Intelligence UAT; HTML/PDF verify; close the gate. |
| Deliverables | Live current=head `f8a9b0c1d2e3`. Pratt UAT project id 9 port 5009. Analyses v1–v3. HTML/PDF same snapshot. Source inventory reconciles to 10 live APPROVED rules. |
| Validation | Dedicated **37 passed**. Relevant regressions **357 passed**. Full suite **401 passed**. No product-code change. No product/rule/source defect. |
| Next | STOP. Do not begin national permit expansion, Phase D, branding, Change Order documents, supplier integration, or external AI / runtime web. |

### 2026-08-30 — FG-016 Ontario / Ottawa Permit Intelligence POC implemented (live migration pending)

| Field | Content |
|-------|---------|
| ID | [FG-016](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) |
| Status | **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE MIGRATION PENDING** (not CLOSED) |
| Branch | `main` |
| Objective | Bounded Ontario / Ottawa coach-house Permit Intelligence POC with governed rules, facts, deterministic evaluation, immutable snapshots, office HTML report, and neutral CalibAi PDF. |
| Deliverables | `permit_rules` / facts / analyses / findings; migration `f8a9b0c1d2e3`; `/projects/<id>/permit-report`; Hub PLAN extension; source inventory. |
| Validation | Dedicated **37 passed**. Full suite **401 passed**. Throwaway upgrade/downgrade verified. Live current remains `e7f8a9b0c1d2`. |
| Next | FG-016 live migration + office Pratt UAT. |

### 2026-08-30 — FG-016 Ontario / Ottawa Permit Intelligence POC approved for implementation

| Field | Content |
|-------|---------|
| ID | [FG-016](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) |
| Status | **APPROVED FOR IMPLEMENTATION** / **IMPLEMENTATION NOT STARTED** |
| Date | 2026-08-30 |
| Objective | Approve bounded Ontario / Ottawa Permit Intelligence POC (governed rules + Mike Pratt reference). Docs only. |
| Deliverables | FG-016; [permit-rules-library.md](architecture/permit-rules-library.md); indexes; architecture/module/status/handoff/log/roadmap updates. No product code. No migration. |
| Validation | Docs only. `git diff --check`. No `app/` / `tests/` / `migrations/`. Alembic current=head `e7f8a9b0c1d2`. FG-015 remains **CLOSED / OPERATIONAL FOR UAT**. |
| Next | **FG-016 implementation** under a later Cursor prompt. Do not populate rules in this pass. Do not create the Pratt project now. |

### 2026-08-30 — FG-015 Permit Foundation V1 live-migrated and closed

| Field | Content |
|-------|---------|
| ID | [FG-015](feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) |
| Status | **CLOSED / OPERATIONAL FOR UAT** |
| Date | 2026-08-30 |
| Objective | Apply `e7f8a9b0c1d2` live; bounded office UAT; close the gate. |
| Deliverables | Live current = head `e7f8a9b0c1d2`. Office UAT on port **5008**. Docs close. No product-code change. |
| Validation | Dedicated FG-015 **19 passed**. Relevant regressions **338 passed**. Full suite **364 passed**. Browser UAT PASSED. |
| Next | Later **Ontario / Ottawa Permit Rules + Mike Pratt POC** Feature Gate (**not created**). Do not populate the Permit Rules Library. |

### 2026-08-30 — FG-015 Permit Foundation V1 implemented (live migration pending)

| Field | Content |
|-------|---------|
| ID | [FG-015](feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) |
| Status | **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED** — **LIVE MIGRATION PENDING** (not CLOSED) |
| Date | 2026-08-30 |
| Objective | Implement bounded Permit Foundation V1. One additive Alembic revision. Do not live-migrate. |
| Deliverables | `ProjectLocation`; platform jurisdiction seed + aliases; deterministic resolver; versioned preliminary `PermitProfile`; Hub PLAN panel; location edit workflow; dedicated tests; docs. Revision `e7f8a9b0c1d2`. |
| Validation | Dedicated FG-015 **19 passed**. Full suite **364 passed**. Throwaway upgrade/downgrade on isolated DB. Live `flask db current` remains `d6e7f8a9b0c1`. |
| Next | **FG-015 live migration** under a later Cursor prompt. Do not populate the Permit Rules Library. Do not CLOSE yet. |

### 2026-08-30 — FG-015 Permit Foundation V1 approved for implementation

| Field | Content |
|-------|---------|
| ID | [FG-015](feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) |
| Status | **APPROVED FOR IMPLEMENTATION** / **IMPLEMENTATION NOT STARTED** |
| Date | 2026-08-30 |
| Objective | Approve Permit Foundation V1 (structured location, jurisdiction resolver foundation, preliminary Permit Profile). Docs only. |
| Deliverables | FG-015; indexes; architecture/module/status/handoff/log/roadmap updates. No product code. No migration. |
| Validation | Docs only. `git diff --check`. No `app/` / `tests/` / `migrations/`. Alembic current=head `d6e7f8a9b0c1`. FG-014 remains **CLOSED / OPERATIONAL FOR UAT**. |
| Next | **FG-015 implementation** under a later Cursor prompt. Do not populate the Permit Rules Library. |

### 2026-08-30 — Permit Intelligence architecture governed (ADR-037 / ADR-038 / ADR-039)

| Field | Content |
|-------|---------|
| ID | [ADR-037](adr/ADR-037-project-location-and-jurisdiction-resolution.md) · [ADR-038](adr/ADR-038-permit-intelligence-authority-and-rules-library.md) · [ADR-039](adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md) |
| Status | **Accepted** / **NOT IMPLEMENTED** |
| Date | 2026-08-30 |
| Objective | Memorialize Permit Intelligence architecture after reconnaissance review. Docs/ADRs only. |
| Deliverables | Three Accepted ADRs; jurisdiction-resolution architecture; Permit Intelligence module stub; report/engine architecture; indexes and status docs. No product code. No Feature Gate. No migration. |
| Validation | Docs only. `git diff --check`. No `app/` / `tests/` / `migrations/`. FG-014 remains **CLOSED / OPERATIONAL FOR UAT**. Alembic current=head `d6e7f8a9b0c1`. |
| Next | **STOP.** Recommended first future gate **Permit Foundation V1** is **not created**. Do not implement Permit Intelligence. |

### 2026-08-30 — Organization Brand Profile + Change Order document family pin

| Field | Content |
|-------|---------|
| ID | [organization-brand-profile.md](architecture/organization-brand-profile.md) · [change-order-document-family.md](architecture/change-order-document-family.md) |
| Status | **FUTURE / NOT IMPLEMENTED** |
| Date | 2026-08-30 |
| Objective | Pin future organization branding and Change Order document-family requirements without implementation. |
| Deliverables | Canonical architecture pins; indexes; status/handoff/log updates. No product code. No Feature Gate. No ADR. |
| Validation | Docs only. Existing Change Order record remains authoritative. FG-014 remains **CLOSED / OPERATIONAL FOR UAT**. Roadmap next action unchanged. |
| Next | **Permit Intelligence Engine architecture reconnaissance** (not implementation). Do not implement these pins. |

### 2026-08-30 — FG-014 closed / operational for UAT

| Field | Content |
|-------|---------|
| ID | [FG-014](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) |
| Status | **CLOSED / OPERATIONAL FOR UAT** |
| Date | 2026-08-30 |
| Objective | Office re-UAT of repaired catalogue-link flashes and close the gate. |
| Deliverables | Port **5007** re-UAT evidence recorded on the Feature Gate. Status docs reconciled. No product-code change. |
| Validation | Valid link/unlink, empty-select, Labour/Equipment fail-closed, cross-org fail-closed, catalogue list/search, identity read-only, isolation GET 404. Tests not rerun (35 / 29 / 345 preserved). |
| Next | **Permit Intelligence Engine architecture reconnaissance** (not implementation). |

### 2026-08-30 — FG-014 catalogue-link flash repair

| Field | Content |
|-------|---------|
| ID | [FG-014](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) |
| Status | **LIVE-MIGRATED / FLASH REPAIR APPLIED — OFFICE RE-UAT REMAINING** |
| Date | 2026-08-30 |
| Objective | Repair misleading catalogue-link flash for non-Material / cross-org POSTs without changing link semantics. |
| Deliverables | `link_cost_item` catches `MaterialCatalogueError` first. Regression tests for Labour/Equipment/Subcontractor/Allowance/Other, cross-org, and empty select. Status docs reconciled. |
| Validation | Dedicated **35 passed**. Assemblies/estimates/estimate_builder **29 passed**. Full suite **345 passed**. Live POST `/material-catalogue/7/link` Labour id 5 flashed the service reason; data remained unlinked. |
| Next | **Office re-UAT of catalogue-link error flashes, then close FG-014**. Do not implement Permit Intelligence. |

### 2026-08-30 — Permit & Approvals Report requirement pin

| Field | Content |
|-------|---------|
| ID | Permit & Approvals Report (not a numbered M0xx; not a Feature Gate; not an ADR) |
| Status | **FUTURE / NOT IMPLEMENTED** — requirement pin only |
| Date | 2026-08-30 |
| Objective | Record a governed advisory project permit-preflight document as future architecture. Identify permit/zoning/servicing/approval issues early enough to affect feasibility, scope, pricing, and contracting. Final authority remains the AHJ. |
| Deliverables | Canonical pin [permit-and-approvals-report.md](architecture/permit-and-approvals-report.md); project-document-package additional-document note; UAT reference case (Mike Pratt Coach House, 2562 Church Street, North Gower, Ontario); indexes and status-doc cross-refs. |
| Validation | Docs-only; `git diff --check`. No `app/` / `tests/` / `migrations/`. No Feature Gate. No ADR. Tests not required this pass. Last recorded full suite **338 passed**. |
| Next | **FG-014 catalogue-link flash repair + re-UAT** (unchanged). Do not implement Permit Intelligence, legal-library, live regulatory lookup, schema, or a Permit Feature Gate in this record. |

### 2026-08-30 — FG-014 live-migrated; office UAT closure blocked

| Field | Content |
|-------|---------|
| ID | [FG-014](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) |
| Status | **LIVE-MIGRATED / UAT DEFECT — CLOSURE BLOCKED** |
| Date | 2026-08-30 |
| Objective | Apply `d6e7f8a9b0c1` and office UAT. Close only if UAT passes. |
| Deliverables | Live current = head = `d6e7f8a9b0c1`. Seed verified. Office UAT mostly passed. Closure blocked by catalogue link flash defect. Product code not repaired. |
| Validation | Dedicated **28**. Regressions **278**. Full suite **338**. Browser UAT on port 5005. |
| Next | Bounded defect repair for `link_cost_item` exception order, then re-UAT. Do not re-migrate. Do not start supplier ingest. |

### 2026-08-30 — FG-014 Material Catalogue V1 implemented (not live-migrated)

| Field | Content |
|-------|---------|
| ID | [FG-014](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) |
| Status | **IMPLEMENTED / VERIFIED / NOT LIVE-MIGRATED** |
| Date | 2026-08-30 |
| Objective | Canonical lumber/sheet identity, platform seed, optional Material CostItem link, office catalogue UX. |
| Deliverables | `canonical_materials`; revision `d6e7f8a9b0c1`; `/material-catalogue/`; dedicated tests. Live DB not upgraded. |
| Validation | Dedicated **28 passed**. Full suite **338 passed**. Throwaway upgrade/downgrade. Live current remains `c5d6e7f8a9b0`. |
| Next | Live-migrate + office UAT when authorized. Do not start Phase D or supplier POC. |

### 2026-08-30 — FG-014 Material Catalogue V1 Feature Gate approved

| Field | Content |
|-------|---------|
| ID | [FG-014](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) (not a numbered M0xx) |
| Status | **APPROVED FOR IMPLEMENTATION / IMPLEMENTATION NOT STARTED** |
| Date | 2026-08-30 |
| Objective | Authorize bounded CalibAi Material Catalogue identity V1 (dimensional lumber + sheet goods) + optional Material CostItem link + office catalogue UX. |
| Deliverables | Feature Gate FG-014; module stub; indexes; status docs. **Future pin:** governed bulk supplier onboarding (not implemented; does not expand FG-014; no Supplier Feature Gate). |
| Validation | Docs-only; `git diff --check`. No `app/` / `tests/` / `migrations/`. Tests not required this pass. Last recorded full suite **310 passed**. |
| Next | Separate **FG-014 implementation prompt**. Do not implement in this record. Do not start Phase D, supplier POC, or bulk supplier onboarding. Do not accept ADR-008. |

### 2026-08-30 — Material Catalogue ADR-034 / ADR-035 / ADR-036

| Field | Content |
|-------|---------|
| ID | ADR-034, ADR-035, ADR-036 (not a numbered M0xx; not a Feature Gate) |
| Status | **Accepted** (governance / architecture only; not implemented) |
| Date | 2026-08-30 |
| Objective | Accept canonical identity, quantity/UOM/requirement boundary, and commercial-evidence/mapping ADRs. |
| Deliverables | Three Accepted ADRs. ADR-008 remains Proposed. No Feature Gate. No product code. |
| Validation | Docs-only; `git diff --check`. Tests not required this pass. |
| Next | **Material Catalogue Feature Gate** (identity-only lumber/sheets) when authorized. Do not implement in this record. Do not start Phase D or supplier POC. |

### 2026-08-30 — Material Catalogue architecture (docs)

| Field | Content |
|-------|---------|
| ID | Material Catalogue architecture (not a numbered M0xx; not a Feature Gate) |
| Status | **Intended architecture documented** (not implemented) |
| Date | 2026-08-30 |
| Objective | Lock CalibAi-seeded material identity vs org CostItem vs supplier catalogue vs mapping; living vs identity; first FG identity-only. |
| Deliverables | [material-catalogue-architecture.md](architecture/material-catalogue-architecture.md); supplier-doc ownership reconciliation; living intelligence (price increase + promotion) recorded. No ADR. No Feature Gate. No product code. |
| Validation | Docs-only; `git diff --check`. Tests not required this pass. |
| Next | **Material Catalogue Feature Gate** when authorized. Do not implement. Do not accept ADR-008 in the identity pass. Do not start Phase D or supplier POC. |

### 2026-08-30 — FG-013 live-migration reconciliation + UAT closure

| Field | Content |
|-------|---------|
| ID | FG-013 (not a numbered M0xx) |
| Status | **CLOSED / OPERATIONAL FOR UAT** |
| Date | 2026-08-30 |
| Objective | Verify already-applied `c5d6e7f8a9b0`, complete bounded browser/UAT, close the gate without re-running `flask db upgrade`. |
| Deliverables | Provenance: migration **VERIFIED APPLIED** before this pass (prior interrupted live-migrate). Multi-file mixed/duplicate/review UAT on port 5004. Folder/OS-drag not live-browser verified. Tests 27/11/25/33/**310**. Docs only. |
| Validation | Dedicated FG-013 **27 passed**; full suite **310 passed**. Live current=head `c5d6e7f8a9b0`. Legacy 20-file corpus SHA match. |
| Next | **Material Catalogue architecture** (docs) when authorized. Do not `flask db upgrade`. Do not start supplier POC, Phase D, MONITOR. |

### 2026-08-30 — ADR-033 supplier neutrality / Winchester launch-partner channel

| Field | Content |
|-------|---------|
| ID | ADR-033 (not a numbered M0xx; not a Feature Gate) |
| Status | **Accepted** (governance / architecture only) |
| Date | 2026-08-30 |
| Objective | Lock supplier-channel rules before any Winchester / supplier-integration POC: neutrality, no exclusivity, dual relationships, launch-partner (not distribution lock-in), Darcy originated-value participation without terms. |
| Deliverables | ADR-033 Accepted; [supplier-channel-and-launch-partner.md](architecture/supplier-channel-and-launch-partner.md). No product code. No Feature Gate. No percentages. |
| Validation | Docs-only; `git diff --check`. No product tests required this pass. |
| Next | **Do not start supplier integration.** FG-013 live-migrate + UAT remains the next **product** action when separately authorized. Darcy commercial terms unset. |

### 2026-08-30 — FG-013 historical-upload implementation

| Field | Content |
|-------|---------|
| ID | FG-013 (not a numbered M0xx) |
| Status | **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED · LIVE MIGRATION PENDING** |
| Date | 2026-08-30 |
| Objective | Productize office UPLOAD PREVIOUS ESTIMATES on FG-006 with ADR-032 custody. |
| Deliverables | Multi-file/folder UX; `HistoricalUploadAttempt`; app-managed storage; unknown-layout quarantine; TIER_A wording; revision `c5d6e7f8a9b0`; dedicated tests. No UploadBatch. Legacy Desktop corpus untouched. |
| Validation | Dedicated FG-013 **27 passed**; full suite **310 passed**. Temp-SQLite upgrade/downgrade verified. Live `flask db current` remains `b4c5d6e7f8a9`. Browser UAT not performed. |
| Next | Separate live-migrate + UAT smoke prompt. Do not upgrade from this commit. |

### 2026-08-30 — FG-013 historical-upload governance + ADR-032 source custody

| Field | Content |
|-------|---------|
| ID | FG-013 + ADR-032 (not a numbered M0xx) |
| Status | FG-013 **APPROVED FOR IMPLEMENTATION / IMPLEMENTATION NOT STARTED**. ADR-032 **Accepted**. |
| Date | 2026-08-30 |
| Objective | Complete FG-013 gate answers and accept app-managed immutable historical workbook custody without implementing uploads. |
| Deliverables | FG-013 approved; ADR-032 Accepted (legacy Desktop corpus leave-in-place; productized uploads app-managed); durable per-file attempts; no UploadBatch; additive schema/migration authorized for a later implementation prompt only. Docs only. |
| Validation | Docs-only; `git diff --check`. No product tests required this pass. Alembic current/head `b4c5d6e7f8a9`. |
| Next | Separate FG-013 **implementation** prompt (must explicitly authorize the one bounded additive Alembic revision). Do not implement from this governance commit. |

### 2026-08-30 — ADR-021 MONITOR Commercial Baseline / Project Gross Margin

| Field | Content |
|-------|---------|
| ID | ADR-021 (not a numbered M0xx; not a Feature Gate) |
| Status | **Accepted** (governance only) |
| Date | 2026-08-30 |
| Objective | Lock MONITOR estimated baseline and Project Gross Margin semantics before any MONITOR / profitability code. |
| Deliverables | ADR-021 Accepted: composed frozen baseline; Project Gross Margin (not net profit); floating-draft prohibition; MONITOR comparison/read ownership; actuals/BUILD/LEARN/benchmarking not implemented. Docs only. |
| Validation | Docs-only; `git diff --check`. No product tests required. Alembic current/head `b4c5d6e7f8a9`. |
| Next | **STOP DEVELOPMENT.** Do not implement MONITOR. Do not create a MONITOR Feature Gate. Phase D **NOT STARTED / NOT AUTHORIZED**. |

### 2026-08-30 — FG-012 Internal Detailed Cost Breakdown + Customer Estimate Consistency

| Field | Content |
|-------|---------|
| ID | FG-012 (not a numbered M0xx) |
| Status | **CLOSED / OPERATIONAL FOR UAT** |
| Date | 2026-08-30 |
| Objective | Internal Detailed Cost Breakdown + customer Proposal consistency from the same EstimateVersion / pricing snapshot. |
| Deliverables | Estimating-owned internal breakdown; named-method Proposal totals from frozen snapshot; customer PDF without Overhead/Profit rows; Estimate Totals method presentation; dedicated tests; docs. No schema/migration/ADR. |
| Validation | Dedicated FG-012 **19 passed**; full suite **283 passed**. Browser UAT on labeled FG-009 residue + `PROP-FG012-UAT-GM`. Alembic current/head `b4c5d6e7f8a9`. |
| Next | **STOP DEVELOPMENT.** Phase D **NOT STARTED / NOT AUTHORIZED**. Do not begin another Feature Gate. |

### 2026-08-30 — FG-011 Project Hub UX

| Field | Content |
|-------|---------|
| ID | FG-011 (not a numbered M0xx) |
| Status | **CLOSED / OPERATIONAL FOR UAT** |
| Date | 2026-08-30 |
| Objective | Evolve `/projects/<id>` into the office-estimator Project Hub. |
| Deliverables | Read-only hub assembly; lifecycle IA PLAN → PRICE → CONTRACT → BUILD with Future MONITOR/LEARN; dedicated tests; docs reconciliation. No schema/migration/ADR. |
| Validation | Dedicated Project Hub **13 passed**; full suite **264 passed**. Browser smoke on labeled FG-009 `/projects/2` and FG-010 `/projects/3`. Alembic current/head `b4c5d6e7f8a9`. |
| Next | **STOP DEVELOPMENT.** Phase D **NOT STARTED / NOT AUTHORIZED**. Estimate-output consistency remains separately gated. |

### 29 Aug 2026 — Day-end reconciliation / Review Turnover

| Field | Content |
|-------|---------|
| ID | Review Turnover (not a product milestone) |
| Status | **COMPLETE / DURABLE / CLEAN TURNOVER** |
| Date | 2026-08-30 |
| Objective | Prove 29 Aug FG-008 / FG-009 / FG-010 work is durable, consistent, pushed, migrated, documented, and reconstructable without chat memory. |
| Deliverables | 22-point `session-handoff.md`; live DB snapshot; residue classification; stale current-state corrections; this journal entry. |
| Validation | Dedicated take-off **18**; Plan Intelligence **56**; Pricing **33**; Labour **25**; Historical **11**; full suite **251**. Alembic current/head `b4c5d6e7f8a9`. |
| Next | **STOP DEVELOPMENT.** Next candidate: Project Hub UX — **NOT STARTED / NOT AUTHORIZED**. Phase D **NOT STARTED / NOT AUTHORIZED**. |

### M012 / FG-010 — Live migration and synthetic UAT smoke

| Field | Content |
|-------|---------|
| ID | M012 / FG-010 |
| Status | **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED** |
| Date | 2026-08-30 |
| Objective | Apply additive migration `b4c5d6e7f8a9` to live development/UAT and perform bounded synthetic browser/UAT smoke. |
| Deliverables | Live Alembic current/head `b4c5d6e7f8a9`; synthetic FG-010 UAT project/docs/runs/package; COUNT-without-scale and dimensional fail-closed; docs reconciliation. |
| Validation | Dedicated **18 passed**; Plan Intelligence combined **56 passed**; Pricing **33**; Labour **25**; historical **11**; full suite **251**. Estimate/Labour/Pricing deltas **ZERO**. External provider calls **ZERO**. Browser smoke on `/projects/3/plans/takeoff`. |
| Next | **STOP DEVELOPMENT.** Day-End Reconciliation / Review Turnover audit. Do not enable a real external AI provider. Do not start Phase D. Do not start another milestone. |

### M012 / FG-010 — Implementation commit and push

| Field | Content |
|-------|---------|
| ID | M012 / FG-010 |
| Status | **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED** — **NOT YET LIVE-MIGRATED** |
| Date | 2026-08-29 |
| Objective | Commit and push the reviewed provider-neutral AI take-off foundation. Live migrate not authorized. |
| Deliverables | One implementation commit on `main` including models/services/UI, migration `b4c5d6e7f8a9`, tests, and docs. |
| Validation | Dedicated **18 passed**; Plan Intelligence combined **56 passed**; Pricing **33**; Labour **25**; historical **11**; full suite **251**. Live current remains `a3b4c5d6e7f8`. Browser/live UAT **not yet performed**. |
| Next | Separate authorization to apply `b4c5d6e7f8a9` live and perform bounded synthetic browser/UAT smoke. Do not enable a real external AI provider. Do not start Phase D. |

### M012 / FG-010 — Foundation implementation (uncommitted)

| Field | Content |
|-------|---------|
| ID | M012 / FG-010 |
| Status | **IMPLEMENTED / VERIFIED** — **NOT YET LIVE-MIGRATED** — **uncommitted** |
| Date | 2026-08-29 |
| Objective | Implement the provider-neutral AI take-off foundation: extraction runs, candidates, human review, immutable packages, mock extractor, COUNT-without-scale, org isolation, PlanAuditEvent extensions, office UI. |
| Deliverables | Models/services/routes/templates; additive migration `b4c5d6e7f8a9`; `tests/test_takeoff.py`; COUNT regression in `tests/test_scale_measurement.py`; docs reconciliation. |
| Validation | Dedicated **18 passed**; Plan Intelligence combined **56 passed**; Pricing **33**; Labour **25**; historical **11**; full suite **251**. Temp DB upgrade/downgrade `a3b4c5d6e7f8` ↔ `b4c5d6e7f8a9`. Live current remains `a3b4c5d6e7f8`. |
| Next | Governance review. **Do not commit, push, or live-migrate** until separately authorized. Do not enable a real external AI provider. Do not start Phase D. |

### M012 / FG-010 — Governance approval (documentation)

| Field | Content |
|-------|---------|
| ID | M012 / FG-010 |
| Status | **APPROVED FOR IMPLEMENTATION** — **NOT IMPLEMENTED** |
| Date | 2026-08-29 |
| Objective | Record Joel/ChatGPT approval of FG-010 and accept ADR-005/006/007/009/011/031. Keep ADR-010 Proposed. COUNT-without-scale clarification. Real external AI provider not authorized. |
| Deliverables | Status reconciliation across FG-010, ADRs, architecture, indexes, handoff. Docs-only commit. |
| Validation | Plan Intelligence combined **51 passed**; Pricing **33**; Labour **25**; historical **11**; full suite **228**. Product/migration files unchanged. |
| Next | Separate bounded FG-010 implementation prompt (provider-neutral). **Do not implement in this pass.** |

### M012 / FG-010 — AI Take-off architecture and Feature Gate preparation

| Field | Content |
|-------|---------|
| ID | M012 / FG-010 (architecture only; not implemented) |
| Status | **PREPARED FOR GOVERNANCE APPROVAL** — **NOT APPROVED** — **NOT IMPLEMENTED** |
| Date | 2026-08-29 |
| Objective | Reconcile Plan Intelligence ADRs; define extraction-run / candidate / package architecture; prepare FG-010. No product code. |
| Deliverables | Take-off architecture; FG-010; ADR-031 **Proposed**; ADR-005–011 reconciliation notes; indexes/handoff. |
| Validation | Plan Intelligence combined **51 passed**; Pricing **33**; Labour **25**; historical **11**; full suite **228**. `git diff --check` expected clean after this pass. Product/migration files unchanged. |
| Next | Joel / ChatGPT review. **Do not implement AI take-off** until FG-010 is approved and a separate implementation prompt is issued. |

### FG-009 — Live development/UAT migration and smoke verification

| Field | Content |
|-------|---------|
| ID | FG-009 (not a numbered product milestone) |
| Status | **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED** |
| Date | 2026-08-29 |
| Objective | Apply committed migration `a3b4c5d6e7f8` to live development/UAT and perform bounded Pricing Engine UAT smoke. No new product features. |
| Deliverables | Live Alembic current/head `a3b4c5d6e7f8`; ORG-001 seed verified (`UNSPECIFIED` optional layers); synthetic UAT TRUE_GM / markup / legacy / CO / override / snapshot immutability; docs reconciliation. |
| Validation | Dedicated **33 passed**; Labour Engine **25 passed**; historical ingestion **11 passed**; full suite **228 passed**. HistoricalLabourItem remained 120. Source workbooks untouched. |
| Next | FG-009 closure review, then prepare the next Feature Gate for AI Take-off / Quantity Extraction Foundation. **Do not start AI take-off.** |

### FG-009 — Implementation commit

| Field | Content |
|-------|---------|
| ID | FG-009 (not a numbered product milestone) |
| Status | **IMPLEMENTED / VERIFIED / NOT YET LIVE-MIGRATED** |
| Date | 2026-08-29 |
| Objective | Commit and push the reviewed Organization-Calibrated Pricing Engine foundation. Live migrate not authorized. |
| Deliverables | Pricing Engine models/services/UI; additive migration `a3b4c5d6e7f8`; CO method inheritance; ORG-001 seed with `UNSPECIFIED` optional layers; dedicated tests. |
| Validation | Dedicated **33 passed**; Labour Engine **25 passed**; historical ingestion **11 passed**; full suite **228 passed**. Live DB remains `f2c3d4e5f6a7`. |
| Next | Separate authorization to apply `a3b4c5d6e7f8` to live development/UAT and UAT-smoke. |

### FG-009 — Pre-commit bounded correction (CO method + ORG-001 seed)

| Field | Content |
|-------|---------|
| ID | FG-009 (not a numbered product milestone) |
| Status | **BOUNDED CORRECTION IN WORKING TREE** — tests passed; **not committed**; live DB **not migrated** |
| Date | 2026-08-29 |
| Objective | Close two pre-commit governance defects: FG-009-aware Change Orders apply inherited pricing METHOD; ORG-001 optional layers seed as `UNSPECIFIED` (distinct from org-approved `NOT_APPLIED`). |
| Deliverables | `price_change_order_from_snapshot`; CO recalculate/copy-lines; in-place correction of uncommitted `a3b4c5d6e7f8` seed; regression tests. No new migration. |
| Validation | Dedicated **33 passed**; Labour Engine **25 passed**; historical ingestion **11 passed**; full suite **228 passed**. Legacy estimate totals not rewritten. Historical Change Orders not rewritten. HistoricalLabourItem facts unchanged. |
| Next | Joel / ChatGPT governance review. **Do not commit / push / live-migrate** until authorized. |

### FG-009 — Organization-Calibrated Pricing Engine implementation

| Field | Content |
|-------|---------|
| ID | FG-009 (not a numbered product milestone) |
| Status | **IMPLEMENTED IN WORKING TREE** — tests passed; **not committed**; live DB **not migrated** |
| Date | 2026-08-29 |
| Objective | Implement organization-owned versioned pricing policies, named methods, deterministic resolution, immutable estimate pricing snapshots, ORG-001 seed, legacy stack compatibility, Change Order snapshot inheritance, tenant isolation. |
| Deliverables | `app/models/pricing_engine.py`; `app/services/pricing_engine.py`; `/pricing-engine/` office UI; additive migration `a3b4c5d6e7f8`; `tests/test_pricing_engine.py` (26 passed) |
| Validation | Dedicated **26 passed**; Labour Engine **25 passed**; historical ingestion **11 passed**; full suite **221 passed**. Legacy estimate totals not rewritten. Historical Change Orders not rewritten. HistoricalLabourItem facts unchanged. |
| Next | Joel / ChatGPT governance review. **Do not commit / push / live-migrate** until authorized. |

### FG-009 — Organization-Calibrated Pricing Engine architecture / Feature Gate preparation

| Field | Content |
|-------|---------|
| ID | FG-009 (not a product milestone; **APPROVED FOR IMPLEMENTATION**; **not implemented**) |
| Status | **ARCHITECTURE AND FEATURE GATE APPROVED** (2026-08-29) |
| Date | 2026-08-29 |
| Objective | Audit live pricing math; reconcile ORG-001 true-GM policy vs markup stack; accept ADR-025/030; approve FG-009; adopt contingency source vs pricing-treatment clarification. |
| Deliverables | Architecture report; FG-009; ADR-025 **Accepted**; ADR-030 **Accepted**; module stub; index/handoff updates. **No product code. No migration.** |
| Validation | Labour Engine tests, historical ingestion tests, full suite, `git diff --check` (see stopping report / chat-workflow-log). |
| Next | Issue a separately authorized bounded FG-009 **implementation** prompt. Do **not** implement from the architecture documents alone. |

### FG-008 — Post-UAT integrity stabilization

| Field | Content |
|-------|---------|
| ID | FG-008 (not a new milestone) |
| Status | **UAT INTEGRITY STABILIZATION COMPLETED** |
| Date | 2026-08-29 |
| Objective | Close two live-UAT integrity gaps: accidental ACCEPTED mapping to archived UAT task; labour audit persisted for nonexistent `ORG-999`. |
| Deliverables | `REVOKED` mapping lifecycle; rule suggestion joins ACTIVE tasks only; `record_labour_audit` / resolution fail-closed for unknown organizations; live mapping 1 `REVOKED`; synthetic PRS 1 `WITHDRAWN`; original ORG-999 audit preserved plus ORG-001 reconciliation event |
| Validation | Dedicated **25 passed**; historical **11 passed**; full suite **195 passed**. HistoricalLabourItem id 1 unchanged. No migration. Alembic `f2c3d4e5f6a7`. |
| Next | **STOP.** Do not start Pricing Engine or another milestone. |

### FG-008 — Live development/UAT migration and smoke verification

| Field | Content |
|-------|---------|
| ID | FG-008 |
| Status | **LIVE DEVELOPMENT/UAT MIGRATION APPLIED / UAT-SMOKE-VERIFIED** |
| Date | 2026-08-29 |
| Objective | Apply committed migration `f2c3d4e5f6a7` to the live development/UAT database and bound-smoke-verify Labour Engine without new schema, product code, or historical evidence repair. |
| Deliverables | Alembic upgrade `e1b2c3d4e5f6` → `f2c3d4e5f6a7`; seven FG-008 tables present; ORG-001 $65 DirectLabourCostRateStandard seed; historical counts unchanged (20/20/120); office `/labour-engine/` smoke; post-upgrade 22/11/192 tests |
| Validation | Live `flask db current` = head = `f2c3d4e5f6a7`. HistoricalLabourItem count 120 unchanged. `hourly_rate=0.13` cluster still 43. Zero historical record mutation. Full suite **192 passed**. |
| Next | **STOP.** Do not start Pricing Engine / ADR-025 or another milestone. |
| Commit | Product code unchanged at `0569f25`. Docs-only reconciliation: *docs: record FG-008 live migration verification* |

### FG-008 — Labour Engine Phase B implementation

| Field | Content |
|-------|---------|
| ID | FG-008 |
| Status | **IMPLEMENTED / VERIFIED** — committed and pushed at `0569f25`; live DB subsequently upgraded (see entry above) |
| Date | 2026-08-29 |
| Objective | Implement organization-owned labour methodology: canonical tasks, human-reviewed mappings, versioned production and direct-labour-cost standards, calibration candidate lifecycle, resolution, estimate snapshots, tenant isolation. |
| Deliverables | Models `app/models/labour_engine.py`; services `app/services/labour_engine.py`; office UI `/labour-engine/`; additive migration `f2c3d4e5f6a7`; `tests/test_labour_engine.py` (22 passed) |
| Validation | Full suite **192 passed**; historical ingestion **11 passed**; dedicated FG-008 **22 passed**. HistoricalLabourItem facts unchanged. Estimate selling-price math unchanged. |
| Next | Live migrate applied 2026-08-29 (see entry above) |

### FG-008 — Labour Engine Phase B Feature Gate preparation

| Field | Content |
|-------|---------|
| ID | FG-008 |
| Status | **FEATURE GATE APPROVED FOR IMPLEMENTATION** — architecture record (implementation is a later entry) |
| Date | 2026-08-29 |
| Objective | Define organization-owned labour methodology: canonical tasks, versioned production and direct-labour-cost standards, calibration candidate lifecycle, resolution, conditions, estimate snapshots, tenant isolation. |
| Deliverables | [FG-008](feature-gates/FG-008-labour-engine-phase-b.md); [labour-engine-phase-b-architecture.md](architecture/labour-engine-phase-b-architecture.md); [ADR-029](adr/ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md) **Accepted**; [modules/labour-engine.md](modules/labour-engine.md) |
| Implementation | **Not started.** Architecture approved. No product code, schema, or migration in this record. |
| Next | Bounded FG-008 **implementation** Cursor prompt (separately authorized) |

### FG-006 — Historical Estimate Ingestion Engine Phase B Feature Gate

| Field | Content |
|-------|---------|
| ID | FG-006 |
| Status | **FEATURE GATE APPROVED, IMPLEMENTED & VERIFIED** |
| Date | 2026-08-28 |
| Objective | Authorize and implement deterministic, organization-aware ingestion of historical estimate workbooks into CalibAi's governed evidence model. Ingest the 20 Brayman source workbooks into ORG-001 private intelligence. |
| Deliverables | [FG-006](feature-gates/FG-006-historical-estimate-ingestion-phase-b.md); pure Python OpenXML parser (no macro execution), Template classifier (Families A–E), Family adapters, canonical persistence models (`HistoricalSourceWorkbook`, `HistoricalEstimate`, `HistoricalSourceObservation`, `HistoricalCostLineItem`, `HistoricalLabourItem`, `HistoricalSubcontractItem`, `HistoricalDataQualityFlag`, `HistoricalEstimateReviewDecision`), evidence review service/UI (`/historical-estimates/`), additive migration `e1b2c3d4e5f6`, 11 dedicated tests |
| FG-006 code | Implemented & Verified (170/170 tests passing, 11 dedicated historical ingestion tests; 20/20 source SHA-256 hashes verified exact; committed and pushed on `main` at `690d755d9901e04eb783198f4b89071fbeaf472a`) |

### FG-007 — M011 Organization Foundation & Project Commercial Context Feature Gate

| Field | Content |
|-------|---------|
| ID | FG-007 |
| Status | **FEATURE GATE APPROVED, IMPLEMENTED & VERIFIED** |
| Date | 2026-08-28 |
| Objective | Authorize M011 scope/invariants/tests/migration permission for Organization entity, direct root model ownership, versioned Project Commercial Context, tenant query scoping, and immutable EstimateVersion references. |
| Deliverables | [FG-007](feature-gates/FG-007-m011-organization-foundation-and-project-commercial-context.md); [ADR-028](adr/ADR-028-organization-foundation-and-project-commercial-context.md) **Accepted**; M011 models, services, project form/edit UI, additive migration `d0a1b2c3d4e5`, 19 tests |
| M011 code | Implemented & Verified (159/159 tests passing; committed and pushed on `main` at `cb38d93`) |

### CAR-001 — CalibAi Product & Architecture Reconciliation

| Field | Content |
|-------|---------|
| ID | CAR-001 |
| Status | **APPROVED ARCHITECTURAL DIRECTION** — implementation not authorized by CAR-001 |
| Date | 2026-08-28 |
| Objective | Read-only reconciliation of the existing platform to CalibAi PLAN→PRICE→CONTRACT→BUILD→MONITOR→LEARN; adopt approved vision and core architecture in docs. |
| Deliverables | [CAR-001 record](architecture/CAR-001-calibai-product-architecture-reconciliation.md); vision/roadmap updates; ADR-019–025; BUILD module stub |
| Validation | Docs/governance only; no app/migration/test/schema changes |
| M009 | **Unchanged at CAR-001 time** — M009 remained coded Sheet classification; CAR-001 is not M009. M009 code was **not begun** when CAR-001 was adopted. **Correction (2026-08-29):** M009 was later implemented under FG-004 (`5dc4b09`, migration `b8d9f0a1c2e3`). |
| Next | Feature-Gate M009 when authorized; accept ADR-021/025 when ready |

### FG-005 — M010 Scale Calibration Feature Gate

| Field | Content |
|-------|---------|
| ID | FG-005 |
| Status | **FEATURE GATE APPROVED, IMPLEMENTED & VERIFIED** |
| Date | 2026-08-28 |
| Objective | Authorize M010 scope/invariants/tests/migration permission for drawing scale calibration and manual measurement tools. Implemented in M010 (`6b969fe`, migration `c9e0f1a2b3d4`). |
| Deliverables | [FG-005](feature-gates/FG-005-m010-scale-calibration.md); [ADR-026](adr/ADR-026-scale-ownership-and-calibration-provenance.md) Accepted; [ADR-027](adr/ADR-027-pdf-rendering-and-normalized-coordinate-system.md) Accepted |
| M010 code | Implemented & Verified (`6b969fe`, migration `c9e0f1a2b3d4`) |

### FG-004 — M009 Sheet Classification Feature Gate

| Field | Content |
|-------|---------|
| ID | FG-004 |
| Status | **FEATURE GATE APPROVED, IMPLEMENTED & VERIFIED** |
| Date | 2026-08-28 |
| Objective | Authorize M009 scope/invariants/tests/migration permission. Implemented in M009 (`5dc4b09`, migration `b8d9f0a1c2e3`). |
| Deliverables | [FG-004](feature-gates/FG-004-m009-sheet-classification.md); ADR-017/018 **Accepted**; M009 models, services, review UI, 15 tests |
| M009 code | Implemented & Verified |

---

## Recorded milestones

### Feature Gate 006 — Historical Estimate Ingestion Engine Phase B

| Field | Content |
|-------|---------|
| Milestone | Historical Estimate Ingestion Engine Phase B (FG-006) |
| Status | **Completed & Verified** (implemented, verified, committed, and pushed on `main`) |
| Branch | `main` |
| Base | `cb38d93` |
| Date | 2026-08-28 |
| Objective | Authorize and implement deterministic, organization-aware ingestion of historical estimate workbooks into CalibAi's governed evidence model. Ingest the 20 Brayman source workbooks into ORG-001 private intelligence with full source-cell provenance and human review workflow. |
| Deliverables | [FG-006](feature-gates/FG-006-historical-estimate-ingestion-phase-b.md); pure Python OpenXML parser (no macro execution), Template classifier (Families A–E), Family adapters, canonical persistence models (`HistoricalSourceWorkbook`, `HistoricalEstimate`, `HistoricalSourceObservation`, `HistoricalCostLineItem`, `HistoricalLabourItem`, `HistoricalSubcontractItem`, `HistoricalDataQualityFlag`, `HistoricalEstimateReviewDecision`), evidence review service/UI (`/historical-estimates/`), additive migration `e1b2c3d4e5f6`, 11 dedicated tests in `tests/test_historical_ingestion.py`. |
| Validation | 170/170 full test suite pass; 11/11 dedicated historical ingestion tests pass; 20/20 source workbook SHA-256 hashes verified exact before and after ingestion; ORG-001 private intelligence isolation verified; zero mutation to active estimating tables. |
| Architectural findings | Pure-Python OpenXML reader executes zero macros; cell provenance preserves exact formula and displayed text; cost-plus markup preserved as historical fact without converting to modern gross margin; contingency separated from markup. |
| Open decisions | None for FG-006. Ingestion is complete and sealed. Pricing Engine remains blocked / not started. |
| Next milestone | **FG-008** Labour Engine Phase B — architecture **APPROVED FOR IMPLEMENTATION** (2026-08-29). Implementation not started. |
| Commit | `690d755` — *feat: implement FG-006 historical estimate ingestion engine phase b* |

### Milestone 011 — Organization Foundation & Project Commercial Context

| Field | Content |
|-------|---------|
| Milestone | Organization Foundation & Project Commercial Context |
| Status | **Completed & Verified** (implemented and committed on `main`) |
| Branch | `main` |
| Base | `01b3be4` |
| Date | 2026-08-28 |
| Objective | Implement canonical `Organization` model, Brayman `ORG-001` seed and deterministic backfill, direct ownership FKs on root models (`Client`, `Project`, `CostItem`, `Assembly`, `ProposalTemplate`), tenant-safe query isolation with fail-closed 404s, versioned `ProjectCommercialContext` with 7 mandatory decision parameters, policy-driven justification engine, Commercial Decision Gate in project creation and editing UI, immutable `EstimateVersion.commercial_context_id` references, and controlled additive migration `d0a1b2c3d4e5`. |
| Deliverables | Models (`Organization`, `ProjectCommercialContext`); migration `d0a1b2c3d4e5`; services `app/services/organizations.py`, `app/services/commercial_context.py`; updated routes and templates for projects, clients, cost library, assemblies, proposal templates, estimates, proposals, plan intelligence, project controls; 19 focused tests in `tests/test_organization_foundation.py`. |
| Validation | 159/159 full test suite passes; migration applies cleanly with complete legacy data preservation and deterministic backfill; tenant query isolation verified; policy-driven justification verified; historical estimate version context immutability verified. |
| Architectural findings | Single-tenant context helper `get_current_organization_id()` provides complete query scoping without prematurely implementing auth/RBAC; composite unique constraints preserve cross-tenant code reusability; commercial context captures assumptions without affecting pricing math. |
| Open decisions | None for M011. Organization foundation and Project Commercial Context active. |
| Next milestone | FG-006 — Historical Estimate Ingestion Engine Phase B |
| Commit | `cb38d93` — *feat: implement M011 organization foundation and commercial context* |

### Milestone 010 — Scale Calibration / Measurement Tools

| Field | Content |
|-------|---------|
| Milestone | Scale Calibration / Measurement Tools |
| Status | **Completed & Verified** (implemented on `main`) |
| Branch | `main` |
| Base | `8f7969c` |
| Date | 2026-08-28 |
| Objective | Implement drawing scale calibration (2-point calibration, presets, viewport regions, NTS) and manual measurement tools (linear, polyline, polygon area Shoelace / perimeter, count) with normalized coordinate stability, PDF.js viewer, and fail-closed human authority under Plan Intelligence. |
| Deliverables | Models (`PlanScaleCalibration`, `PlanMeasurement`); migration `c9e0f1a2b3d4`; service layer `app/plan_intelligence/scale_measurement.py`; measurement route and template (`sheet_measure.html`, `sheet-measurement.js`); 19 focused tests in `tests/test_scale_measurement.py`. |
| Validation | 140/140 tests pass; migration applies cleanly; project/revision/sheet isolation verified; source doc/page immutability verified; estimating/proposals unaffected. |
| Architectural findings | Extracted scale strings never auto-confirm; measurements require confirmed calibration; multi-scale viewports scope measurement scales deterministically; geometry persisted in normalized document coordinates `[0.0, 1.0]`. |
| Open decisions | None for M010. Drawing scale calibration and manual measurement tools active. |
| Next milestone | Milestone 011 — Organization Foundation & Project Commercial Context (FG-007) |
| Commit | `6b969fe` — *feat: implement M010 scale calibration* |

### Milestone 009 — Sheet Classification / Human Metadata Review

| Field | Content |
|-------|---------|
| Milestone | Sheet Classification / Human Metadata Review |
| Status | **Completed & Verified** |
| Branch | `main` |
| Base | `da0d38a` |
| Date | 2026-08-28 |
| Objective | Implement durable Sheet entities, non-1:1 Page↔Sheet mapping, first-class suggestions, human review workflow (accept/edit/reject/void), revision uniqueness/finalization validation, and office review UI under Plan Intelligence. |
| Deliverables | Models (`PlanSheet`, `PlanSheetPage`, `PlanSheetSuggestion`, `sheet_id` audit FK); migration `b8d9f0a1c2e3`; service layer `app/plan_intelligence/sheets.py`; office review routes and templates (`sheets_index.html`, `sheet_review.html`, `sheet_create.html`); 15 focused tests in `tests/test_sheet_intelligence.py`. |
| Validation | 121/121 tests pass; migration applies cleanly; project/revision isolation verified; source doc/page immutability verified; estimating/proposals unaffected. |
| Architectural findings | Suggestion presence never auto-accepts SoR; human action required; uniqueness scoped to DrawingRevision; superseded revision sheets remain immutable. |
| Open decisions | None for M009. Scale calibration / measurement tools deferred to M010. |
| Next milestone | M010 — Scale Calibration / Measurement Tools (FG-005 Approved; awaits implementation prompt) |
| Commit | `5dc4b09` — *feat: implement M009 sheet classification* |

### Milestone 008 — Sheet Intelligence Architecture Planning

| Field | Content |
|-------|---------|
| Milestone | Sheet Intelligence Architecture Planning |
| Status | **Completed** (merged to `main`) |
| Branch | `milestone-008-sheet-intelligence` |
| Base | M007 indexing (`cbefe7a`) |
| Date | 2026-07-25 |
| Objective | Design Sheet entity model, page mapping, human review, duplicates/supersession; ADRs only if warranted; **no application code**. |
| Deliverables | [architecture/sheet-intelligence.md](architecture/sheet-intelligence.md); [M008 readiness report](architecture/M008-sheet-intelligence-readiness-report.md); [ADR-017](adr/ADR-017-sheet-metadata-suggestion-and-review-workflow.md); [ADR-018](adr/ADR-018-sheet-uniqueness-duplicates-and-supersession.md); index/roadmap/state updates. |
| Validation | Docs only; no app/migration/test changes for this milestone. |
| Architectural findings | M007 Pages/Revisions are a sufficient foundation; suggestions ≠ system of record; uniqueness is per Revision; first *coded* sheet work is a later Feature-Gated milestone (recommended M009). |
| Open decisions | Accept ADR-017/018; authorize coded sheet Feature Gate. |
| Next milestone | Feature-Gated Sheet classification and human metadata review (not authorized yet) |
| Commit | `8c74e31` — *Document Sheet Intelligence architecture and suggestion/review ADRs.* Merged via PR #6 → `ee9b4b2`. |

### Milestone 007 — Document Indexing and Deterministic Metadata Extraction

| Field | Content |
|-------|---------|
| Milestone | Document Indexing and Deterministic Metadata Extraction |
| Status | **Completed** (merged to `main`) |
| Branch | `milestone-007-document-indexing` |
| Base | M005 Phase A + M006 architecture |
| Date | 2026-07-25 |
| Objective | First coded Document Intelligence phase: pages, deterministic/embedded-text extraction, provenance, archive, audit, relational search. |
| Deliverables | Models/services for Package/Revision (minimal), Page, ProcessingAttempt/Result, audit; migration `a7c8e9f0b1d2`; UI list/search/reprocess/archive; `tests/test_plan_indexing.py`. |
| Validation | Targeted plan tests + full suite **106 passed**, 110 warnings; `flask db upgrade` to `a7c8e9f0b1d2`; `git diff --check` clean. |
| Architectural findings | Upload ownership unchanged; Estimating untouched; hard-delete blocked once audit/index exist; page ≠ sheet. |
| Open decisions | Sheet Intelligence coded review (next Feature Gate); raw payload retention TTL; auth; project-detail archived filter. |
| Next milestone | Milestone 008 — Sheet Intelligence architecture planning |
| Commit | `cbefe7a` — *Implement Document Intelligence indexing for plan pages, processing, and search.* Merged via PR #5 → `eb00123`. |

### Milestone 006 — Document Intelligence Architecture & Feature Gate

| Field | Content |
|-------|---------|
| Milestone | Document Intelligence Architecture and Feature Gate |
| Status | **Completed** (merged to `main`) |
| Branch | `milestone-005-plan-intelligence-phase-a` |
| Base commit | `098647c` (Phase A); docs tip `35413a1` |
| Date | 2026-07-25 |
| Objective | Design Document Intelligence between PDF upload and take-off; FG-003 readiness with conditions; required ADRs only; no code. |
| Deliverables | FG-003 (**CONDITIONAL PASS**); `architecture/document-intelligence.md`; M006 readiness report; ADR-013–016; roadmap/milestones/state updates. |
| Validation | Docs only; no app/migration/test/dependency changes; link check; `git diff --check`. |
| Architectural findings | M005 supports additive DI; Sheet ≠ Page; extraction provenance required; staged relational search; hard-delete/auth/audit are conditions not FAIL causes. |
| Open decisions | Accept ADR-013–016 (as applicable); coded DI delivered in M007. |
| Next milestone | M007 — Document indexing and deterministic metadata extraction |
| Commit | `35413a1` — *Document Document Intelligence architecture and FG-003 readiness.* Merged via PR #4 → `db1a8da`. |

### Milestone 005 — Plan Intelligence Feature Gate and Phase A PDF Upload

| Field | Content |
|-------|---------|
| Milestone | Plan Intelligence Feature Gate and Phase A PDF Upload |
| Status | **Completed** (merged to `main`) |
| Branch | `milestone-005-plan-intelligence-phase-a` |
| Base commit | `c59ec01` |
| Date | 2026-07-25 |
| Objective | Complete FG-002; document ADR-012 (revision ownership); implement Phase A only — secure searchable PDF upload/storage foundation. |
| Deliverables | ADR-012 (Proposed); FG-002 (Approved); `app/plan_intelligence/` (models/services/storage/routes); templates; migration `f9c1a2b3d4e5`; project detail link; `tests/test_plan_upload.py`; module/docs updates. |
| Validation | Phase A tests 8 passed; full suite **97 passed**, 68 warnings. No OCR/CAD/AI/estimate insert/revision UI. |
| Architectural findings | Flat `plan_documents` is intentionally interim; Drawing Set/Revision lifecycle owned by ADR-012 for later gates. Private storage under instance/`PLAN_UPLOAD_ROOT`. |
| Open decisions | Accept ADR-012; auth for uploads; retention/archival policy when take-offs exist. |
| Next milestone | Milestone 006 — Document Intelligence architecture (then M007+ coded DI) |
| Commit | `098647c` — *Implement Plan Intelligence Phase A PDF upload and storage.* Merged via PR #4 → `db1a8da`. |

### Milestone 004 — Plan Intelligence & Automated Take-Off Architecture

| Field | Content |
|-------|---------|
| Milestone | Plan Intelligence & Automated Take-Off Architecture |
| Status | **Completed pending documentation commit** |
| Branch | `main` |
| Base commit | `c59ec01` |
| Date | 2026-07-25 |
| Objective | Design implementation-ready Plan Intelligence architecture: pipeline, conceptual model, human review, source traceability, estimate mapping, ADRs, narrow POC — documentation only. |
| Deliverables | Expanded `modules/plan-intelligence.md`; full `architecture/plan-intelligence-and-automated-takeoff.md`; readiness report; ADR-005/006 updates; ADR-011 confidence policy; roadmap/milestones/state updates. |
| Validation | Docs only; no app/migration/test/dependency changes; link check after edits. |
| Architectural findings | Differentiator is plan→take-off→estimate→proposal; PDF-first; human approval mandatory; citations first-class; estimate builder not redesigned. |
| Open decisions | POC element confirmation; confidence numeric thresholds; auth for reviewer; Phase A Feature Gate timing; build-vs-buy. |
| Next milestone | Feature Gate + implement Plan Intelligence Phase A (PDF upload/storage) |
| Commit | Pending |

### Milestone 003 — Accepted Proposal Immutability

| Field | Content |
|-------|---------|
| Milestone | Accepted Proposal Immutability |
| Status | **Completed** |
| Branch | `main` |
| Base commit | `71e2754` / docs at `9137052` |
| Date | 2026-07-25 |
| Objective | Enforce service-layer immutability for `Accepted` proposals across all mutation paths; keep detail/preview/PDF read-only available. |
| Deliverables | `ensure_proposal_mutable` / `is_proposal_immutable`; route/UI read-only controls; `tests/test_proposal_immutability.py`. |
| Validation | Full pytest: **89 passed**, 53 warnings (at implementation). No migration. |
| Architectural findings | No section CRUD mutation API; line edit + update_proposal + recalculate + status were mutation surfaces. |
| Open decisions | Void/supersede/revision workflow (ADR-004). |
| Next milestone | Milestone 004 — Plan Intelligence architecture |
| Commit | `c59ec01` — *Enforce immutability for accepted proposals* |

### Milestone 002 — Product Architecture Review and Next-Milestone Selection

| Field | Content |
|-------|---------|
| Milestone | Product Architecture Review and Next-Milestone Selection |
| Status | **Completed pending documentation commit** |
| Branch | `main` |
| Base commit | `71e2754` |
| Date | 2026-07-25 |
| Objective | Review Proposals module against roadmap; produce Feature Gate FG-001 and ADRs 001–004; recommend next implementation milestone without code changes. Extended same day with strategic Plan Intelligence / Supplier architecture, pillars, Phases A–G, ADR-005–010, and POC recommendation. |
| Deliverables | `docs/feature-gates/FG-001-proposals-module.md`; ADR-001–004; `docs/architecture/plan-intelligence-and-automated-takeoff.md`; `docs/architecture/supplier-catalogue-inventory-pricing.md`; ADR-005–010; roadmap pillars; module stubs for Plan Intelligence and Supplier Catalogue; cross-links. |
| Validation | Documentation-only; no application/migration/test file changes; internal doc links checked after edits. Full pytest not re-run (last verified: 78 passed, 43 warnings). |
| Architectural findings | Proposal Builder foundation already exists. Highest Proposals gap: Accepted without immutability. Strategic differentiator: PDF-first Plan Intelligence → reviewed take-off → estimate → supplier pricing → proposal/PO. No plan upload or supplier catalogue in code today. |
| Open decisions | Joel acceptance of ADRs 001–010; Milestone 003 vs Phase A POC sequencing; POC element confirmation. |
| Next milestone | **Milestone 003 — Accepted Proposal Immutability** (near-term) and/or Feature Gate for **Plan Intelligence Phase A** (strategic) — neither implementation-authorized until Joel approves |
| Commit | Pending |

### Milestone 001 — Platform Governance Foundation

| Field | Content |
|-------|---------|
| Milestone | Platform Governance Foundation |
| Status | **Completed** |
| Branch | `main` |
| Base commit | `7b8d5ca` |
| Date | 2026-07-25 |
| Objective | Establish repository-based governance, architecture documentation, development workflow, module ownership, Cursor rules, handoff process, and definition of done. |
| Deliverables | `docs/` governance tree (vision, architecture, principles, governance, workflow, standards, DoD, roadmap, current-state, session-handoff, chat-workflow-log, AiRIA lessons); `docs/modules/*`; `docs/adr` template; `AGENTS.md`; `.cursor/rules/*`; root `README.md` pointer; Constitution; milestone history; prompt library; project state report. Commit **`29d1ba9`** included **39** governance/documentation files only; **no** application, migration, or test files changed. |
| Validation | **78 tests passed**, 43 warnings; `git diff --check` clean; **171** internal links checked, **0** broken; no application, migration, or test files changed. |
| Architectural findings | Modular Flask application; estimate versioning and locking exist; proposal snapshots exist; disabled navigation placeholders for future modules; `project_controls` package exists; hard-coded development `SECRET_KEY` requires later cleanup; accepted-proposal immutability needs targeted product review. |
| Open decisions | Next product milestone (pending Product Architecture Review); authentication model; proposal acceptance → project creation; whether Project Controls needs a dedicated module document. |
| Next milestone | Milestone 002 — Product Architecture Review and Next-Milestone Selection |
| Commit | `29d1ba9` — *Complete Estimator governance baseline and prompt library* (record commit `71e2754` memorialized milestone) |
| Remote at record time | Subsequently pushed; tag `v0.1-governance-baseline` published |

---

## Milestone entry template

```markdown
### Milestone NNN — <Title>

| Field | Content |
|-------|---------|
| Milestone | |
| Status | Planned \| In progress \| Completed pending commit \| Completed |
| Branch | |
| Base commit | |
| Date | |
| Objective | |
| Deliverables | |
| Validation | |
| Architectural findings | |
| Open decisions | |
| Next milestone | |
| Commit | |
```

## Related

- [platform-roadmap.md](platform-roadmap.md) — forward-looking plan
- [project-state-report.md](project-state-report.md) — milestone-level state snapshot
- [session-handoff.md](session-handoff.md) — immediate session continuation
