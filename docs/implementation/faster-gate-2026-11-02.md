# Faster release gate (2 Nov 2026)

Branch `feature/faster-gate-2026-11-02` (on top of the density branch, released after it). Approved by Joel on
2 Nov 2026: make the full regression much faster **without weakening any gate** — no skip, no fewer tests, no
relaxed assertion, nothing excluded.

## What changed

| Change | Where | Effect |
|---|---|---|
| Parallel full regression | `tools/release/release_gate.sh` | `pytest -q -rfEs -n ${PYTEST_WORKERS:-auto} --dist loadfile --junitxml=… tests`. One pytest-xdist worker per CPU core; `--dist loadfile` keeps every test file on one worker in file order, as a serial run sees it. |
| New gate check | `tools/release/release_gate.sh` | The junit XML must list exactly as many passing test cases as the summary line reports (`JUNIT_COUNT` otherwise), before the unchanged no-skip, end-to-end walk and Cal checks. |
| Pinned dev dependency | `requirements-dev.txt`, `tests/test_dependency_pins.py` | `pytest-xdist==3.8.0` and `execnet==2.1.1` (both support Python 3.9 and pytest 8.4.2). The gate installs them with the other dev pins; `tools/setup_test_environment.sh --check` verifies them like every other pin. Never installed on Render (`requirements.txt` unchanged). |
| Family 05 summary under xdist | `tests/conftest.py` | Failures are now counted in `pytest_runtest_logreport`, which runs in the process that prints the summary (the only process serially, the controller under xdist, which receives every worker's reports). Workers do not count, so nothing is counted twice. The explanation section is still attached to each failing report. Before this change a parallel run would have printed "no test in this run needed it" with the master missing. |
| Test upload folders | `app/__init__.py` (TESTING only) | A test app that names no `PLAN_UPLOAD_ROOT`, `HISTORICAL_UPLOAD_ROOT` or `DECK_TAKEOFF_ROOT` now gets its own temporary folder, like the eight roots already handled that way. Before, such tests wrote plan PDFs into the repository's shared `instance/plan_uploads/<project id>/` (the 2 Nov serial run left 18 files there), which parallel workers would share. Production and non-test apps are unchanged. |
| Cached empty schema | `tests/fast_fixtures.py`, `tests/conftest.py` | The first `db.create_all()` on a fresh in-memory SQLite database in a test process runs for real and is kept as a byte-for-byte copy (SQLite online backup); later calls on another fresh, empty in-memory database restore it (~5 ms instead of ~0.45 s). Used only when the database is in-memory on one shared connection (StaticPool), completely empty and idle, and the model metadata fingerprint (tables, columns, types, indexes, constraints, DDL listeners) matches. Anything else runs the real `create_all()`. |
| Memoised password check | `tests/fast_fixtures.py`, `tests/auth_fixtures.py` | Werkzeug PBKDF2-SHA256 (1,000,000 iterations) cost ~0.35–0.7 s per sign-in and per test-user creation, and almost every test signs the office user in. `check_password_hash` is a pure function of (stored hash, password); in tests it is memoised per exact pair, so every answer is the real answer (a wrong password or a different hash is a different pair, checked for real). Test users created by `tests/auth_fixtures.create_user` get a real `hash_password()` hash made once per password per process. The app's own hashing (sign-up, reset, invitations) is untouched and still salts every hash. |
| Guard tests | `tests/test_parallel_gate.py` | Gate runs the whole suite in parallel with nothing narrowed; XML count check present; xdist pinned; test apps keep uploads out of `instance/`; the Family 05 summary is right serially and with `-n 2` (the `-n 2` case fails on the old conftest); the cached schema dump equals a real `create_all()` dump (tables, indexes, triggers, FTS5 table, no rows); a non-empty or file database never uses it; the password memo gives the real answer for right and wrong pairs. |

Isolation review (nothing else needed changing): every browser/server helper already binds a free port (port 0)
and its own `tempfile.mkdtemp` database or work folder; tests set environment variables through `monkeypatch`;
the eight storage roots already used temporary folders under `TESTING`; `tmp_path` is per worker under xdist.
**No test is grouped, serialised, skipped or excluded** — there is no `xdist_group` in the suite.

## Measured

To be completed from the runs below (this container has 2 cores; Joel's Mac has more, so the Mac gain is larger).

## How to run

```bash
./venv/bin/python -m pytest -q tests                              # serial, one process, exactly as before
./venv/bin/python -m pytest -q -n auto --dist loadfile tests      # parallel, as the release gate runs it
PYTEST_WORKERS=4 bash /tmp/release_gate.sh …                      # gate with a chosen worker count
PYTEST_WORKERS=0 bash /tmp/release_gate.sh …                      # gate fully serial (xdist off)
CALIBRAYTAI_TEST_CACHES=0 ./venv/bin/python -m pytest -q tests    # without the schema and password caches
```

`-n auto` uses `os.cpu_count()` (psutil is not installed). On an Apple-silicon Mac that is the core count.
