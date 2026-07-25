# Prompt Library — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Active |
| Updated | 2026-07-25 |

## Purpose

Reusable Cursor prompt templates so Joel → ChatGPT → Cursor work is consistent, bounded, and recoverable.

## Rules

1. Templates are **starting points**, not substitutes for feature-specific analysis.
2. Every implementation prompt must reference **authoritative docs** (Constitution, governance, architecture, module docs, Feature Gate).
3. The **approved prompt summary** must be recorded in [chat-workflow-log.md](../chat-workflow-log.md).
4. Prompts must explicitly identify **allowed** and **prohibited** changes.
5. Cursor must **inspect before editing**.
6. **No template authorizes scope expansion.**

## Templates

| Template | When to use |
|----------|-------------|
| [cursor-feature-template.md](cursor-feature-template.md) | New or extended product capability |
| [cursor-bugfix-template.md](cursor-bugfix-template.md) | Defect correction with smallest safe fix |
| [cursor-refactor-template.md](cursor-refactor-template.md) | Behaviour-preserving internal improvement |
| [cursor-review-template.md](cursor-review-template.md) | Inspection/report only (default: no code changes) |
| [cursor-migration-template.md](cursor-migration-template.md) | Approved schema/migration work only |
| [cursor-documentation-template.md](cursor-documentation-template.md) | Docs-only updates |

## Related

- [../development-workflow.md](../development-workflow.md)
- [../platform-governance.md](../platform-governance.md) Feature Gate
- [../platform-constitution.md](../platform-constitution.md)
