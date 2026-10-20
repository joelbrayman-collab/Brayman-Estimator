# Test Environment — setup, fixtures and commands

| Attribute | Value |
|-----------|--------|
| Status | Current (technical cleanup, 18 Oct 2026) |
| Script | `tools/setup_test_environment.sh` |
| Pins | `requirements-lock.txt` (production's exact versions), `requirements-dev.txt` (test only), `calculation-engines/*/package-lock.json` |

## Which run is the release authority

The **native Mac regression inside the release gate** (`tools/release/release_gate.sh`) is the regression that releases depend on. It runs on a fresh clone of the exact commit, with Python 3.9.6 (the version production runs), the production dependency versions, Google Chrome and LibreOffice, and the confidential Family 05 master and historical workbooks that exist only on the office Mac. Since 18 Oct 2026 it must finish with **no skipped test**.

The cloud workspace can now run the same suite with the same result, given a copy of the Family 05 master (below). Its only legitimate skips are the 11 historical-ingestion tests, which need real customer workbooks that never leave the Mac.

## Set up

```bash
bash tools/setup_test_environment.sh                      # builds ./venv and checks everything
PYTHON=python3.9 VENV=/tmp/fresh bash tools/setup_test_environment.sh   # a separate clean venv
bash tools/setup_test_environment.sh --check              # report only
```

The script installs `requirements.txt` + `requirements-dev.txt` constrained by `requirements-lock.txt`, runs `npm ci` in `calculation-engines/concrete-slab-1.0.0` and `calculation-engines/stair-ontario-residential-v1`, installs Playwright's Chromium unless `PLAYWRIGHT_BROWSERS_PATH` already provides one, and then reports each requirement below as `[ok]` or `[MISSING]`.

| Requirement | Used by | Mac | Cloud workspace |
|---|---|---|---|
| Python 3.9.6 | everything (production version) | `/usr/bin/python3` | `uv python install 3.9.6` (3.13 also passes) |
| Python packages, exact versions | everything | `requirements-lock.txt` | same |
| Python Playwright 1.56.0 + Chromium | `test_employment_calculator_v11.py`, `test_trade_calculator_pages_browser.py` | `pip install -r requirements-dev.txt`, `python -m playwright install chromium` | pre-installed Chromium (`PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers`) |
| Node 20+ and the two engine `node_modules` (Playwright 1.56.1) | calculator page tests, end-to-end walk, release browser checks | Homebrew Node; `npm ci` | pre-installed Node; `npm ci` |
| Google Chrome | Node page tests launch `channel: "chrome"` | installed | `/opt/google/chrome` |
| LibreOffice (`soffice`) — **optional** | Not needed by any test (the signing tests inject a converter or use `tests/fake_soffice.py`) or by production; reported only | not installed on the office Mac (18 Oct) | 24.2 present |
| Family 05 contract master (SHA-256 `24bb319a…000fb5`) | 40+ contract-generation and signing tests | `~/Documents/CalibAi/Approved Document Templates/Reusable Master Template Family V1/MASTER DOCX/` (the code's default) | a copy **outside the repository**, named by `CALIBRAYTAI_FAMILY_05_MASTER_PATH` |
| Historical estimate workbooks (20 real customer files) | 11 tests in `test_historical_ingestion.py` | `~/Desktop/CalibAi Historical Estimates` | not available: the 11 tests skip with the reason |

## Environment variables (tests only)

| Variable | Meaning |
|---|---|
| `CALIBRAYTAI_FAMILY_05_MASTER_PATH` | Path to a copy of the Family 05 master. Read only by `tests/conftest.py`; production code is unchanged and hosted still refuses Family 05. Tests still verify the copy's SHA-256. |
| `CALIBRAYTAI_HISTORICAL_ESTIMATES_DIR` | Another copy of the historical workbooks (default `~/Desktop/CalibAi Historical Estimates`). |
| `PLAYWRIGHT_BROWSERS_PATH` | Where Playwright finds Chromium (cloud: `/opt/pw-browsers`). |
| `E2E_BROWSER_EXECUTABLE` | Optional Chromium for `tests/e2e/contractor_workflow.mjs` where Google Chrome is absent. |

## Family 05 master: how a run reports it (20 Oct 2026)

Joel, 20 Oct: the recurring cloud failures are the confidential Family 05 Ontario contract master, not application code; report the dependency clearly; never skip, disable or weaken the contract tests; never commit the master.

- `tests/conftest.py` checks the master the tests will read (SHA-256 against the governed value) and ends every run with one line:
  - `FAMILY_05_MASTER=present (SHA-256 matches the governed file); contract tests ran normally`, or
  - a red section **MISSING TEST DEPENDENCY — not an application failure** giving the status (`missing` / `sha-mismatch`), the path, the number of contract-test failures that need the master, and the number of **other** failures it does not explain. The run still fails.
- The ten files that need it are listed in `FAMILY_05_DEPENDENT_FILES` (`tests/conftest.py`); `tests/test_family_05_test_dependency.py` fails if a listed file disappears, if a test reading the master directly is not listed, if any of them gains a skip, or if the master is ever tracked by Git.
- Cloud workspace procedure (each new session): stage the master from the connected Mac folder `~/Documents/CalibAi/Approved Document Templates/Reusable Master Template Family V1/MASTER DOCX/` through the device bridge, copy it to `/home/claude/fixtures-confidential/` (outside every repository, read-only), and run with `CALIBRAYTAI_FAMILY_05_MASTER_PATH` set to that copy. Check the summary line says `present`.
- The Mac release gate reads the code's default path, checks the SHA-256 before the regression, and requires zero failures and zero skips.

## Never committed

The Family 05 master, the historical workbooks, any office database (`instance/`), backups, passwords and tokens. `instance/` and `*.db` are in `.gitignore`. A local `instance/brayman_estimator.db` does not affect the suite: tests use in-memory databases, and `test_af_no_live_db_mutation_and_memory_only` proves the file is byte-for-byte unchanged.

## Commands

```bash
./venv/bin/python -m pytest -q                       # complete suite
./venv/bin/python -m pytest -q tests/test_<area>.py  # one area
node --test --test-force-exit tests/e2e/contractor_workflow.mjs   # also run inside the suite
```

Report exact counts (passed, failed, skipped, errors, warnings), duration and the commit SHA, and the reason for every skip (definition of done, item 5).

## Cloud failures before 18 Oct 2026, and what fixed them

| Former failure | Count | Root cause | Correction |
|---|---|---|---|
| Contract generation, Family 05 merge, signing sign-a/b/e, signing mail, account recovery | 40 | The confidential master exists only on the Mac (hard-coded default path) | `CALIBRAYTAI_FAMILY_05_MASTER_PATH` for tests; master copied outside the repo, SHA verified. (Earlier notes blamed LibreOffice for sign-e; with the master present all 15 sign-e tests pass, so the master was the cause.) |
| `test_browser_process::test_a_timeout_kills_a_detached_child` | 1 | The killed child stays a zombie: the container's first process does not collect orphans, and `os.kill(pid, 0)` succeeds on a zombie | The test checks the process is no longer running (zombie = stopped) with a bounded 5 s wait; a second test proves the check is not vacuous. 25/25 runs passed. |
| `test_employment_calculator_access` (browser) | 1 (intermittent) | The test measured the progress bar during its 0.2 s CSS transition (99.5 px) | Bounded wait for the transition to end; assertion unchanged |
| Other calculator browser tests | 5 (intermittent) | Load from running two halves at once; pass when run alone | None needed; the complete run is sequential |
| `test_system_administrator_authority_fg038::test_af_…` | 1 (local) | Compared a local office database with its PA-B checkpoint values | Compares the file before and after the test instead |
| Two Python Playwright files on the Mac | 2 skips | `playwright` not installed; `importorskip` hid it | `requirements-dev.txt`; the files now import it directly, so a missing dependency fails |
