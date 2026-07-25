# Cursor Prompt Template — Documentation

Copy this template for documentation-only work. **No application code, models, migrations, routes, templates, services, repositories, or tests** unless the prompt explicitly authorizes an exception (default: none).

---

## Title

`<documentation task name>`

## Source documents and code to inspect

List docs and code paths Cursor must read before writing.

## Unsupported claims prohibition

Do not claim facts that cannot be verified from the repository. Use **To be verified** when needed.

## Current vs proposed distinction

Separate what exists today from intended/future state. Do not blur them.

## Required cross-links

Link to Constitution, governance, modules, ADRs, milestones, project-state-report as applicable. Prefer cross-reference over duplication.

## Link validation

Check internal documentation links after edits.

## No application changes

Confirm `git status` / diff shows only approved doc/governance paths.

## Validation

`git diff --check`; link check; run full test suite if required by the prompt to prove no behaviour change; report exact results.

## Final report

Files created/modified · intentionally unchanged · validation · risks · suggested commit · **do not commit automatically**.
