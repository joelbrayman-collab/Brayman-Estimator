# The Estimator Platform Constitution

| Attribute | Value |
|-----------|--------|
| Status | **Active** |
| Version | **1.0** |
| Updated | 2026-07-25 |
| Change frequency | Rare — amend only with deliberate approval |

## Purpose

Define the **non-negotiable** governance and architectural principles that supersede implementation convenience. This document is more concise and more stable than [architecture-principles.md](architecture-principles.md). Where they differ in specificity, the Constitution prevails; architecture principles elaborate operational rules consistent with these articles.

Chat history is not authoritative unless memorialized in the repository.

---

## Constitutional Articles

**Article 1 — The Repository Is the System of Record**  
Chat history, memory, and verbal instructions are not authoritative unless memorialized in repository documentation.

**Article 2 — Product Authority Is Explicit**  
Joel owns product vision, construction business rules, priorities, and final approval.

**Article 3 — Architecture Must Precede Expansion**  
New modules or major workflows require documented ownership, boundaries, and approval before implementation.

**Article 4 — Module Ownership Is Exclusive**  
Every durable business record has one authoritative owning module.

**Article 5 — Historical Records Are Preserved**  
Accepted proposals, historical estimates, budgets, and financial records are versioned, superseded, or snapshotted rather than silently overwritten.

**Article 6 — Financial Actions Are Auditable**  
Financially significant actions must leave a reviewable audit trail.

**Article 7 — Documentation Is Part of the Product**  
A feature is incomplete if its authoritative documentation, roadmap, handoff, and implementation record are not current.

**Article 8 — Architecture Changes Require Deliberate Approval**  
Changes to ownership, invariants, module boundaries, or platform rules require an ADR and Joel’s approval.

**Article 9 — Implementation Must Remain Within Approved Scope**  
Cursor must not invent product policy or expand scope without approval.

**Article 10 — Tests Must Support Claims**  
No claim that functionality works or tests pass may be made unless the relevant commands were actually run.

**Article 11 — Migration Safety Is Mandatory**  
Schema changes must be intentional, reviewed, reversible where practical, and limited to the approved feature.

**Article 12 — Governance Supersedes Convenience**  
A faster implementation is not acceptable if it weakens ownership, auditability, history, documentation, or recoverability.

---

## Amendment process

1. Propose the change with rationale and impact.
2. Create or update an ADR when the amendment affects architecture or ownership.
3. Obtain **Joel’s approval**.
4. Update this Constitution (version bump), [architecture-principles.md](architecture-principles.md) if elaboration changes, and [chat-workflow-log.md](chat-workflow-log.md).
5. Do not weaken an Article for a single feature without that process.

## Relationship to architecture-principles.md

| Document | Role |
|----------|------|
| **This Constitution** | Highest-order, rarely changed platform law |
| [architecture-principles.md](architecture-principles.md) | Numbered operational Rules 1–12 that implement the Constitution |
| [platform-governance.md](platform-governance.md) | Process, Feature Gate, roles |
| [adr/](adr/) | Deliberate decisions and exceptions |

## Approval

Version 1.0 established during the Platform Governance Foundation sprint. Subsequent amendments require Joel’s approval as above.
