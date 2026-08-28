# CalibAi Continuity & Anti-Drift Protocol

| Attribute | Value |
|-----------|--------|
| Title | CalibAi Continuity & Anti-Drift Protocol |
| Status | **APPROVED / GOVERNING** |
| Approved by | Joel Brayman |
| Adopted | 2026-08-28 |
| Updated | 2026-08-28 |
| Applies to | ChatGPT, Cursor, Codex, and future AI development agents |

## Repository application

This protocol is adopted into the **Brayman-Estimator** repository (product name in this repository: **The Estimator**). Adoption does **not** rename the product or repository.

This protocol **supplements** the [Platform Constitution](../platform-constitution.md), [architecture principles](../architecture-principles.md), [platform governance](../platform-governance.md), [development workflow](../development-workflow.md), and [AGENTS.md](../../AGENTS.md). It does **not** amend the Constitution.

Existing context-drift rules in [platform-governance.md](../platform-governance.md#context-drift-and-handoff-mandatory-stop) remain in force. This document is the detailed governing protocol for continuity and anti-drift.

---

## Purpose

Prevent AI context drift, continuity loss, unauthorized reinterpretation, and silent replacement of approved project state from becoming durable CalibAi product state.

---

## Core rule

**AI memory is never authoritative project state.**

The repository is the system of record. Chat history, model memory, summaries, and prior AI assertions are aids only unless the relevant decision or state is memorialized in the repository.

---

## Mandatory principles

1. **Repository before memory.**  
   Reconstruct current state from authoritative repository records before substantive architecture or implementation work.

2. **Search before creation.**  
   Search for existing decisions, implementations, schemas, workflows, assets, and documentation before proposing replacements or new structures.

3. **Evidence before assertion.**  
   Do not claim that a feature, decision, test, deployment, file, asset, or project state exists without current evidence.

4. **Approval before mutation.**  
   Product, architecture, schema, financial, legal-template, protected-asset, and scope changes require applicable explicit approval before mutation.

5. **Protected means immutable.**  
   Approved baselines and assets are outside generative or incidental mutation scope unless Joel explicitly authorizes a new revision.  
   Work from a copy when revision is authorized.  
   Preserve the prior approved master.

6. **One authorized delta at a time.**  
   Each implementation objective must identify:
   - baseline
   - exact approved delta
   - protected areas
   - required tests
   - stopping conditions

7. **No silent reinterpretation.**  
   An AI agent may not replace an approved decision with what it considers a better design, architecture, wording, workflow, or implementation.

8. **Tests and repository evidence before completion claims.**  
   Never infer success from intent or partial execution.

---

## Mandatory preflight gate

Before substantive architecture or implementation, establish from repository evidence:

- repository and branch
- current commit / synchronization state where relevant
- current milestone and authoritative product state
- governing documents read
- protected baselines and invariants
- exact approved objective / authorized delta
- explicitly prohibited changes
- unresolved decisions or missing approvals
- expected tests / verification
- stopping conditions

If these cannot be established reliably:

**STOP — RECONCILE BEFORE PROCEEDING.**

---

## Existing-before-new gate

Before creating or materially redesigning any feature, schema, workflow, document, visual asset, module, integration, or architecture:

1. Search authoritative repository documentation.
2. Search relevant code and tests.
3. Identify the existing owner and baseline, if any.
4. State whether proposed work is:
   - reuse
   - extension
   - replacement
   - genuinely new
5. Replacement requires explicit approval.

Absence from current AI context is never evidence that something does not exist.

---

## Approval-state discipline

Material decisions should use explicit states where applicable:

- **PROPOSED**
- **APPROVED**
- **IMPLEMENTED**
- **VERIFIED**
- **SUPERSEDED**

Discussion does not equal approval.  
Implementation does not equal verification.  
Superseded decisions remain preserved historically.

---

## Continuity correction trigger

A substantive user correction indicating continuity loss is a drift signal, including statements equivalent to:

- “we already decided this”
- “that already exists”
- “do not redesign/change that”
- “you have lost where we are”
- “that is not the approved version”

Two substantive continuity corrections in a working session require an immediate **STOP**.

After the second correction:

1. No further implementation or generative modification.
2. Reconstruct current state from repository evidence.
3. Identify divergence and affected work.
4. Confirm protected state and authorized delta.
5. Resume only after reconciliation and Joel approval where required.

A single severe protected-baseline violation may justify immediate stop without waiting for a second correction.

---

## Context-risk / rollover rule

Long conversational context must never be treated as a reason to continue through degraded reliability.

When an agent detects:

- context pressure
- continuity uncertainty
- repeated mistakes
- conflicting recollection
- inability to distinguish approved state from discussion

it must stop substantive work and create/update a repository-backed stopping state before continuing in a fresh session.

No implementation may depend upon preserving one long chat session.

---

## Rollover package

Before rollover, record or verify:

- current repository / branch / commit
- current milestone
- approved baseline
- exact authorized delta
- protected state
- last explicit approval
- implementation status
- test status
- open decisions
- next authorized action
- exact resume instructions

---

## Fresh-session reconstruction

Before substantive work resumes, reconstruct from repository evidence:

Baseline  
→ Approved delta  
→ Protected state  
→ Last approval  
→ Implementation status  
→ Open decisions  
→ Next authorized action

---

## Architect / executor separation

Use this controlled sequence for material development:

Repository evidence  
→ reconciliation  
→ Joel approval  
→ authorized delta  
→ executor implementation  
→ tests  
→ repository/documentation update  
→ verification

An architect/adviser does not silently grant execution authority.

An executor does not reinterpret architecture or product policy.

Neither may treat another AI agent's memory or chat output as the system of record.

---

## Protected-asset rule

Once Joel explicitly marks an image, logo, graphic, document template, or other visual/design asset **APPROVED**:

Generative AI must never modify, regenerate, recreate, enhance, reinterpret, or approximate that approved master.

Approved assets must be used as immutable files/layers.

Deterministic technical processing may be used only when required for delivery and must preserve the master.

A design revision begins from a copy and does not replace the approved master until Joel explicitly approves the revision.

---

## Drift containment principle

The objective is not to assume AI drift can be eliminated.

The objective is to ensure:

**DRIFT CANNOT QUIETLY BECOME DURABLE PROJECT STATE.**

Where possible, enforce protection through architecture, permissions, immutable assets, explicit scope, tests, and repository state rather than relying solely on prompt instructions.

---

## Stop condition

When evidence, approval, ownership, context, or continuity is uncertain:

**STOP — SEARCH — VERIFY — RECONCILE — THEN EXECUTE.**

---

## Related

- [Platform Constitution](../platform-constitution.md) — highest-order platform law (not amended by this protocol)
- [platform-governance.md](../platform-governance.md) — Feature Gate, roles, existing context-drift stop
- [architecture-principles.md](../architecture-principles.md) — Rule 10 (repository is the system of record)
- [development-workflow.md](../development-workflow.md)
- [session-handoff.md](../session-handoff.md)
- [current-state.md](../current-state.md)
- [project-state-report.md](../project-state-report.md)
- [AGENTS.md](../../AGENTS.md)
- [aiRIA-lessons-adopted.md](../aiRIA-lessons-adopted.md)
