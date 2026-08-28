# Feature Gates

| Attribute | Value |
|-----------|--------|
| Status | Active |
| Updated | 2026-08-28 |

Feature Gate documents answer the twelve governance questions in [platform-governance.md](../platform-governance.md) for a specific module or milestone **before** Cursor implementation.

## Index

| ID | Title | Status |
|----|-------|--------|
| [FG-001](FG-001-proposals-module.md) | Proposals Module — Product Architecture Review | Draft for Joel approval |
| [FG-002](FG-002-plan-intelligence-phase-a.md) | Plan Intelligence Phase A (PDF Upload & Storage) | **Approved for Phase A** (Milestone 005) |
| [FG-003](FG-003-document-intelligence-readiness.md) | Document Intelligence Readiness | **CONDITIONAL PASS** — architecture only; implementation not authorized (Milestone 006) |
| [FG-004](FG-004-m009-sheet-classification.md) | M009 Sheet Classification / Human Metadata Review | **APPROVED, IMPLEMENTED & VERIFIED** (Milestone 009; `5dc4b09`, migration `b8d9f0a1c2e3`) |
| [FG-005](FG-005-m010-scale-calibration.md) | M010 Scale Calibration / Measurement Tools | **APPROVED, IMPLEMENTED & VERIFIED** (Milestone 010; migration `c9e0f1a2b3d4`) |

Implementation is not authorized by a Feature Gate until Joel approves the gate and the corresponding Cursor prompt.

**CAR-001** aligns strategic CalibAi lifecycle architecture. **FG-004** authorized M009 (implemented & verified). **FG-005** authorized M010 Scale Calibration & Measurement Tools, now implemented and verified in code on `main`. Future milestones (M011+ AI take-off) require their own dedicated Feature Gate.
