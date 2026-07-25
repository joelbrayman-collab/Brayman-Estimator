# Testing Standards — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Governing for QA |
| Updated | 2026-07-25 |

## Expectations

| Type | Expectation |
|------|-------------|
| Focused tests | Cover the changed behaviour; add/adjust tests in `tests/` |
| Regression / full suite | Run `./venv/bin/python -m pytest -q` before claiming completion |
| Migration tests | When schema changes: upgrade/downgrade reviewed; app boots against upgraded DB |
| Negative tests | Invalid input, forbidden status transitions, inactive templates, etc. |
| Authorization tests | When authz exists—claim only after verifying Flask-Login / role behaviour |
| Immutable-record tests | Locked estimate versions; proposal snapshot independence (already present pattern) |
| Audit-trail tests | When audit tables/events exist |

## Reporting

- Report **exact commands** and **exact results** (pass count / failures).
- **Prohibition:** Do not say tests passed unless they were actually run successfully in that session.
- If the suite cannot run, explain why (missing venv, DB lock, env vars) without inventing outcomes.

## Default commands (Cursor Terminal)

```bash
./venv/bin/python -m pytest -q
./venv/bin/python -m pytest -q tests/test_<area>.py
```

## Related

- [definition-of-done.md](definition-of-done.md)
- Existing suite: `tests/` (78 tests collected as of 2026-07-25)
