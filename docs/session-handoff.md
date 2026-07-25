# Session Handoff — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Continuity |
| Updated | 2026-07-25 |
| Complements | [current-state.md](current-state.md) · [chat-workflow-log.md](chat-workflow-log.md) · [project-state-report.md](project-state-report.md) · [milestones.md](milestones.md) |

## Distinctions (do not substitute)

| Document | Role |
|----------|------|
| **This file** ([session-handoff.md](session-handoff.md)) | Immediate continuation after a pause |
| [project-state-report.md](project-state-report.md) | Authoritative **milestone-level** state |
| [milestones.md](milestones.md) | **Historical** milestone record (append-only) |

Session handoff is not a substitute for the project state report or milestone history.

## Instructions

Update this file at the end of every substantial session. Prefer facts verified from the repository. Use **To be verified** when evidence is missing—do not invent test counts, migration heads, or feature completeness.

---

## Current handoff

| Field | Value |
|-------|--------|
| **Date** | 2026-07-25 |
| **Current branch** | `main` (tracks `origin/main` at start of governance sprint) |
| **HEAD (verified)** | `7b8d5ca` — Merge PR #3 project-controls change orders (at sprint start). Re-verify with `git rev-parse HEAD` after commits. |
| **Latest completed milestone** | Governance Foundation sprint (documentation) — pending Joel commit approval |
| **Current implementation status** | App features on `main`: Clients, Projects, Cost Items, Assemblies, Estimates (versions/sections/lines), Proposals (templates, snapshots, preview, PDF), Change Orders. Nav placeholders disabled for Purchase Orders, Job Costing, Reports, AI Assistant, Settings. |
| **Test status** | `./venv/bin/python -m pytest -q` → **78 passed**, 43 warnings (2026-07-25). |
| **Migration status** | Alembic scripts present under `migrations/versions/`. ScriptDirectory heads observed: `e8b2c4d15a90`. Live DB `alembic current`: **To be verified** (CLI without Flask app context failed). |
| **Current database head if known** | To be verified (`flask db current` or equivalent with `FLASK_APP=app.py`) |
| **Uncommitted work** | Governance docs / AGENTS.md / `.cursor/rules` / README pointer (this sprint) — confirm with `git status` |
| **Architectural decisions made** | Rules 1–12 adopted; Current vs Intended vs Future documented; Feature Gate required |
| **Active risks** | Hard-coded SECRET_KEY in create_app; audit trail UI incomplete for change orders; acceptance→project snapshot workflow not fully productized; no prior docs system |
| **Next recommended step** | Joel/ChatGPT review governance foundation; commit if approved; then pick one Feature-Gated product milestone |
| **Exact commands to resume** | See below |
| **Documents to read first** | [README.md](README.md) reading order; [platform-constitution.md](platform-constitution.md); [project-state-report.md](project-state-report.md); [current-state.md](current-state.md); this file; [platform-governance.md](platform-governance.md) |

### Commands to resume (Cursor Terminal)

```bash
cd /Users/joelbrayman/Desktop/Brayman-Estimator
git status
git rev-parse HEAD
git branch -vv
./venv/bin/python -m pytest -q
# Optional migration check:
# FLASK_APP=app.py ./venv/bin/flask db current
```

---

## Handoff template (copy for next session)

| Field | Content |
|-------|---------|
| Date | |
| Current branch | |
| HEAD | |
| Latest completed milestone | |
| Current implementation status | |
| Test status | |
| Migration status | |
| Current database head if known | |
| Uncommitted work | |
| Architectural decisions made | |
| Active risks | |
| Next recommended step | |
| Exact commands to resume | |
| Documents to read first | |
