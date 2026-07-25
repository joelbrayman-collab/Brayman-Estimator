# Cursor Prompt Template — Review (read-only by default)

Copy this template. **No code changes** unless Joel/ChatGPT explicitly authorize them in this prompt.

---

## Title

`<review name>`

## Scope to inspect

Paths, modules, workflows, or commits under review.

## Governing documents

At minimum: `docs/platform-constitution.md`, `docs/architecture-principles.md`, `docs/architecture.md`, relevant `docs/modules/*.md`, Feature Gate / ADR if any.

## Questions to answer

Numbered review questions.

## Ownership review

Does each durable record have one owner? Any dual-write risk?

## Data-flow review

Create / update / read paths; snapshot/version boundaries.

## Migration review

Heads, pending revisions, risk of destructive operations (if migrations in scope).

## Security review

Authn/authz, secrets, CSRF, data exposure. Mark unverified items.

## Test review

Coverage gaps for the scoped behaviour; flaky or missing assertions.

## Documentation review

Docs vs code drift; missing handoff / current-state updates.

## Findings by severity

| Severity | Finding | Evidence (path + line if possible) | Recommendation |
|----------|---------|--------------------------------------|----------------|
| Critical | | | |
| High | | | |
| Medium | | | |
| Low / Note | | | |

## Code changes

**Default: none.** If authorized, list exact allowed edits; otherwise report only.

## Evidence standard

Use file paths and line references where possible. Do not invent facts. Use **To be verified** when needed.
