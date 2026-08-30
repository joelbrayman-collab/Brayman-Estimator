# Review Turnover Protocol

| Attribute | Value |
|-----------|--------|
| Title | Review Turnover Protocol |
| Status | **APPROVED / GOVERNING** |
| Approved by | Joel Brayman |
| Adopted | 2026-08-28 |
| Updated | 2026-08-28 |
| Exact Trigger Phrase | `Review Turnover` |
| Applies to | ChatGPT, Cursor, Codex, and future AI development agents working on this repository |

---

## 1. Purpose and Position

The **Review Turnover Protocol** is the repository-backed, deterministic anti-drift procedure for safely ending a long, stale, context-heavy, or otherwise continuity-risky ChatGPT / AI-development conversation and starting a fresh one without losing any authoritative project state.

### The Governing Success Criterion
> **AFTER A SUCCESSFUL REVIEW TURNOVER, THE ACTIVE CONVERSATION COULD BE DISCARDED AND A FRESH AGENT COULD ACCURATELY RECONSTRUCT ALL CURRENT, MATERIAL, APPROVED PROJECT STATE FROM REPOSITORY EVIDENCE ALONE.**

### Core Invariants
1. **The turnover is repository-backed.** Chat history, AI memory, model summaries, and prior conversational assertions are NOT authoritative project state. The repository is the ONE SOURCE OF TRUTH.
2. **Conversation is expendable.** Once a turnover receives a `TURNOVER PASS`, the prior chat conversation is considered expendable and can be closed or archived with zero risk to continuity.
3. **No competing authority.** This protocol consolidates and strengthens [continuity-and-anti-drift.md](continuity-and-anti-drift.md), [platform-constitution.md](../platform-constitution.md), [platform-governance.md](../platform-governance.md), and [development-workflow.md](../development-workflow.md).

---

## 2. Immediate Effect of “Review Turnover”

When the exact phrase **`Review Turnover`** is invoked:

1. **Substantive development must STOP immediately.**
2. Until turnover completes and receives a PASS or explicit direction from Joel:
   - NO new product code
   - NO new architecture redesign
   - NO new schema changes or migrations
   - NO unrelated fixes or refactoring
   - NO advancement to the next milestone
   - NO expansion of project scope
3. The turnover procedure itself may make only the minimum repository documentation, governance, and session-handoff updates required to reconcile approved and current project state.
4. If implementation is already in progress when turnover is invoked:
   - Preserve and accurately record its actual state (e.g. uncommitted files, failing tests, partial migrations).
   - Do NOT falsely mark incomplete work complete.
   - Do NOT discard uncommitted work without explicit Joel instruction.
   - Do NOT commit unfinished product work merely to simplify turnover unless existing governance and Joel authorization permit that action.

---

## 3. Two-Phase Invocation Workflow

```text
┌─────────────────────────────────────────────────────────────┐
│ PHASE 1 — CHATGPT (Conversation Audit & Delta Extraction)  │
│ 1. Joel types: "Review Turnover"                            │
│ 2. ChatGPT stops substantive work                           │
│ 3. ChatGPT reviews active chat context                      │
│ 4. ChatGPT creates the Turnover Delta Ledger                │
│ 5. ChatGPT prepares governed Cursor Turnover Prompt         │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 2 — CURSOR (Repository Audit & Reconciliation)        │
│ 1. Cursor runs Anti-Drift Preflight & Git baseline check    │
│ 2. Cursor audits repository, migrations, models, and tests  │
│ 3. Cursor reconciles Turnover Delta Ledger against docs     │
│ 4. Cursor updates session-handoff.md with Turnover Package  │
│ 5. Cursor conducts Drift Audit & Completeness Test          │
│ 6. Cursor issues TURNOVER PASS / FAIL Report                │
│ 7. Cursor produces Fresh Chat Startup Prompt                │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Mandatory Repository Review

A Review Turnover must verify and document:

### A. Repository & Baseline
- Repository identity and local path (`~/Desktop/Brayman-Estimator`)
- Branch (expected `main`)
- `HEAD` SHA and `origin/main` SHA (verify parity via `git rev-parse`)
- Working tree cleanliness (`git status`)
- Recent relevant commits
- Current Alembic migration head and runtime database migration state (`flask db current`)
- Any outstanding branches, uncommitted files, or partial implementations

### B. Governance & Authority
- Verify status of [platform-constitution.md](../platform-constitution.md), [continuity-and-anti-drift.md](continuity-and-anti-drift.md), [platform-governance.md](../platform-governance.md), [development-workflow.md](../development-workflow.md).
- Verify [current-state.md](../current-state.md), [project-state-report.md](../project-state-report.md), [session-handoff.md](../session-handoff.md), [platform-roadmap.md](../platform-roadmap.md), [milestones.md](../milestones.md).
- Verify ADR index and statuses (Distinguish **Accepted** from **Proposed**).
- Verify Feature Gate index and statuses (Distinguish **Approved** from **In Progress** or **Not Started**).

### C. Product Lifecycle State (CalibAi Reconciliation)
Reconstruct and classify every lifecycle domain:
- **PLAN**: (e.g. Plan Intelligence Phase A, Document Indexing M007, Sheet Intelligence M009, Scale M010, Take-off M012 foundation operational for UAT; Phase D mapping not started)
- **PRICE**: (Estimating builder + Labour Engine FG-008 + Pricing Engine FG-009 **OPERATIONAL FOR UAT**; ADR-025/030 **Accepted**)
- **CONTRACT**: (Proposals current; Ontario Construction Contract & Warranty templates Future/Governed)
- **BUILD**: (Project Controls change orders partial; Field capture / mobile Future)
- **MONITOR**: (Actual-cost feedback; ADR-021 Proposed)
- **LEARN**: (Recommendation boundary ADR-024 Accepted; ML/recommendation implementation Future)

Classify each domain status strictly from repository evidence:
`IMPLEMENTED`, `PARTIAL`, `ARCHITECTURE ONLY`, `APPROVED / NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `FUTURE`, or `SUPERSEDED`.

### D. Current Milestone & Authorized Delta
- Current milestone name and number
- Governing Feature Gate
- Approved baseline commit
- Exact authorized delta
- Implementation status (models, services, routes, UI)
- Migration status (old head -> new head)
- Test results (exact commands and pass/fail counts)
- Documentation and handoff status
- Remaining items, if any

---

## 5. Mandatory Chat → Repository Delta Ledger

A turnover may **NOT** pass merely because repository documents are internally consistent. The repository must also contain every material decision and requirement developed in the active chat.

Before `TURNOVER PASS`, ChatGPT must extract and Cursor must reconcile the **Turnover Delta Ledger**.

### Ledger Item Classifications

Every material conversational item must be classified into one of:

1. **ALREADY IN REPOSITORY**  
   The item is already accurately recorded in the appropriate repository document. Verify file path and section. No edit needed unless stale.
2. **PARTIALLY MEMORIALIZED**  
   The item is partially recorded but missing key details or constraints. Update the owning document to make it complete.
3. **MISSING FROM REPOSITORY**  
   The item was approved in conversation but is absent from repository docs. If it is within approved scope, memorialize it minimally in the correct document. If it represents a new unapproved architectural shift, classify as `REQUIRES JOEL DECISION`.
4. **SUPERSEDED**  
   The item was discussed or previously adopted but later superseded by a newer decision. Confirm the repository reflects the superseding decision and that the older decision is not presented as current truth.
5. **DISCUSSION ONLY / NOT APPROVED**  
   The item was exploratory, brainstorming, or non-approved chatter. Do NOT record as approved state. Record as an open question only if genuinely useful.
6. **REQUIRES JOEL DECISION**  
   The conversation contains unresolved ambiguity or conflicting product intent. STOP turnover reconciliation, report the ambiguity to Joel, and do not guess.

### Ledger Content Rules
- DO NOT paste conversation transcripts wholesale into repository documents.
- DO NOT convert informal discussion into approved policy.
- DO NOT revive superseded assumptions.
- DO NOT create duplicate or competing authority files.

---

## 6. Turnover Completeness Test

Before declaring a turnover complete, the agent must explicitly ask and answer:

> **“Is there any material approved decision, requirement, implementation fact, protected baseline, unresolved decision, or current authorization present in the active conversation / Turnover Delta Ledger that is not represented in the repository?”**

- **Required answer for PASS:**  
  `NO — verified through Turnover Delta Ledger reconciliation.`
- **If the answer is YES or UNCERTAIN:**  
  `TURNOVER FAIL — RECONCILIATION REQUIRED` (List exact missing items).

---

## 7. Protected State & Open Decision Review

### A. Protected State Review
The turnover package must explicitly enumerate all protected assets and invariants:
- **Constitutional Articles 1–12**
- **Accepted ADRs** (ADR-002, ADR-017, ADR-018, ADR-019, ADR-020, ADR-022, ADR-023, ADR-024)
- **Source Immutability**: `PlanDocument` binary bytes, SHA-256 hashes, and `PlanPage` raw extractions are immutable.
- **Human Authority**: AI suggestions never silently set authoritative SoR fields.
- **Accepted Proposal Immutability**: Accepted commercial proposals are sealed.
- **Pricing Policy Baseline**: $65/hr direct labour, 15% gross margin formula `Price = Cost / 0.85`.
- **Legal Content Gate**: Ontario contract and warranty language requires formal template provenance.
- **Protected Visual Assets**: Branding logos and company styling.

### B. Open Decisions & Deferred Items
Clearly distinguish:
- **OPEN DECISION**: Unresolved choices awaiting Joel approval (e.g. ADR-021 MONITOR baseline, real external AI provider / ADR-010).
- **APPROVED DECISION**: Formally authorized by Joel.
- **DEFERRED ITEM**: Intentionally postponed to a later milestone (e.g. Phase D estimate mapping, Project Hub UX, QuickBooks API, field/mobile apps).

---

## 8. Drift Audit

Compare truth across the entire workspace:
- Code vs. Migrations vs. Tests vs. Docs
- Verify no stale SHAs or stale "not pushed" notices remain after pushes.
- Verify migration head matches `flask db current`.
- Verify test counts are exact and verified by command execution.
- Verify that features marked "Implemented" have corresponding code and passing tests.
- Verify that features without code are marked "Architecture only" or "Future".

---

## 9. Turnover Pass / Fail Gate

Every turnover concludes with an explicit verdict:

### Option A: TURNOVER PASS — SAFE TO START FRESH CONVERSATION
Granted only when:
- Git baseline is verified and working tree is clean.
- All code, migrations, and tests are consistent and passing.
- The Chat → Repository Delta Ledger is 100% reconciled.
- The Completeness Test answers **NO**.
- The Turnover Package and Fresh Chat Startup Prompt are fully generated.

### Option B: TURNOVER FAIL — RECONCILIATION REQUIRED
Triggered if:
- Baseline or working tree has unexplained dirty state or diverged pins.
- Material conversational decisions are missing from the repository.
- Tests fail or migration state is out of sync.
- Completeness Test is YES or UNCERTAIN.
- Substantive ambiguities require Joel's decision.

---

## 10. Required Turnover Package (Standard Structure)

On `TURNOVER PASS`, the turnover report and `docs/session-handoff.md` must present the 22-point standard turnover package:

1. **PROJECT / REPOSITORY:** Name, local path, environment.
2. **VERIFIED BASELINE:** Branch, `HEAD` SHA, `origin/main` SHA, working tree state, Alembic head.
3. **GOVERNING DOCUMENTS:** Active governance references.
4. **APPROVED PRODUCT VISION:** Strategic product identity (The Estimator / CalibAi).
5. **CURRENT CALIBAI LIFECYCLE STATE:** Status of PLAN, PRICE, CONTRACT, BUILD, MONITOR, LEARN.
6. **COMPLETED MILESTONES:** List of merged/completed milestones with dates and commit SHAs.
7. **CURRENT MILESTONE:** Current milestone number, name, and exact status.
8. **LAST AUTHORIZED DELTA:** Summary of most recently approved and executed prompt scope.
9. **IMPLEMENTATION STATUS:** Concrete summary of durable models, services, routes, templates.
10. **TEST / UAT / MIGRATION STATUS:** Exact test suite execution results, warning counts, Alembic migration state.
11. **PROTECTED STATE:** Specific list of immutable schemas, commercial invariants, and source data rules.
12. **ACCEPTED ADRs:** List of all Accepted ADRs.
13. **PROPOSED / OPEN ADRs:** List of Proposed ADRs awaiting approval.
14. **FEATURE GATES:** Status of all Feature Gates (FG-001 through latest).
15. **CHAT → REPOSITORY DELTA LEDGER RESULT:** Reconciliation summary.
16. **OPEN DECISIONS:** Explicit list of pending decisions.
17. **KNOWN RISKS:** Technical, architectural, or domain risks.
18. **DEFERRED ITEMS:** Roadmap items deliberately scheduled for future milestones.
19. **EXPLICITLY PROHIBITED NEXT ACTIONS:** Scope boundaries for upcoming work.
20. **NEXT AUTHORIZED ACTION:** Next governed step (e.g. prepare next Feature Gate).
21. **EXACT REPOSITORY RESUME COMMANDS:** Bounded bash block for verifying state upon resume.
22. **FRESH CHAT STARTUP PROMPT:** Complete copy-pasteable prompt for starting a new chat conversation.

---

## 11. Fresh Chat Startup Prompt Format

The turnover protocol must produce a ready-to-paste startup prompt for the next ChatGPT or Cursor conversation. The prompt must instruct the new agent to:

```text
BRAYMAN — RESUME FROM REVIEW TURNOVER
CONTINUITY / REPOSITORY-FIRST INITIALIZATION

You are resuming work on the Brayman-Estimator platform following a successful Review Turnover.
The prior conversation has been discarded. The repository is the ONE SOURCE OF TRUTH.

1. ANTI-DRIFT PREFLIGHT
Read and comply with:
- AGENTS.md
- docs/platform-constitution.md
- docs/governance/continuity-and-anti-drift.md
- docs/governance/review-turnover-protocol.md
- docs/current-state.md
- docs/project-state-report.md
- docs/session-handoff.md

2. VERIFY BASELINE
Run in Cursor Terminal:
git status
git branch --show-current
git log -1 --oneline
git rev-parse HEAD
git rev-parse origin/main

3. RECONSTRUCT AUTHORITATIVE STATE
Independently reconstruct:
- Baseline & branch parity
- Latest completed milestone
- Protected state & invariants
- Accepted ADRs vs Proposed ADRs
- Current migration head
- Open decisions & deferred items
- Next authorized action

Do NOT rely on AI memory. Do NOT guess missing product rules.
Conversation titles in this workspace must start with: BRAYMAN — <Topic>.
```

---

## 12. Library Master & Cross-Project Safety

### ChatGPT Library Master
A human-accessible ChatGPT Library reference copy may be maintained as:
`Review Turnover — Master Protocol.md`
- The Library copy is an invocation/reference template only.
- The repository remains the sole authoritative source of project state.

### Cross-Project Safety
- All chat conversation titles in this workspace must start with **`BRAYMAN — <Topic>`** to prevent cross-project context mixing with other workspaces (e.g. AiRIA).
- Do NOT import AiRIA project state into Brayman/CalibAi. Transferred governance lessons apply only where already adopted in repository documentation.
