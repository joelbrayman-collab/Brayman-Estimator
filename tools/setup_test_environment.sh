#!/usr/bin/env bash
# Build (or check) a CalibraytAI test environment from pinned versions.
#
#   bash tools/setup_test_environment.sh            # build ./venv, install, then check
#   bash tools/setup_test_environment.sh --check    # only report what is present
#   VENV=/tmp/fresh-venv PYTHON=python3.9 bash tools/setup_test_environment.sh
#
# Works on the office Mac and in the Linux cloud workspace. It never touches
# production, never reads the office database, and never copies confidential
# files into the repository. See docs/testing/test-environment.md.
set -u
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
VENV="${VENV:-$ROOT/venv}"
PYTHON="${PYTHON:-python3}"
CHECK_ONLY=0
[ "${1:-}" = "--check" ] && CHECK_ONLY=1

ok()   { printf '  [ok]      %s\n' "$*"; }
miss() { printf '  [MISSING] %s\n' "$*"; MISSING=$((MISSING + 1)); }
note() { printf '  [note]    %s\n' "$*"; }
MISSING=0

if [ "$CHECK_ONLY" -eq 0 ]; then
  echo "== Python environment ($VENV)"
  if [ ! -x "$VENV/bin/python" ]; then
    "$PYTHON" -m venv "$VENV" || { echo "could not create $VENV with $PYTHON"; exit 1; }
  fi
  "$VENV/bin/python" -m pip install -q --upgrade pip
  "$VENV/bin/python" -m pip install -q -r requirements.txt -r requirements-dev.txt -c requirements-lock.txt \
    || { echo "pip install failed"; exit 1; }
  echo "== Node packages (exact versions from package-lock.json)"
  for pkg in calculation-engines/concrete-slab-1.0.0 calculation-engines/stair-ontario-residential-v1; do
    (cd "$pkg" && npm ci --silent --no-audit --no-fund) || { echo "npm ci failed in $pkg"; exit 1; }
  done
  echo "== Browsers"
  if [ -n "${PLAYWRIGHT_BROWSERS_PATH:-}" ] && ls "$PLAYWRIGHT_BROWSERS_PATH" 2>/dev/null | grep -q '^chromium'; then
    note "Chromium already provided under PLAYWRIGHT_BROWSERS_PATH=$PLAYWRIGHT_BROWSERS_PATH"
  else
    "$VENV/bin/python" -m playwright install chromium
  fi
fi

echo "== Check"
PYV="$("$VENV/bin/python" -c 'import platform; print(platform.python_version())' 2>/dev/null)"
case "$PYV" in
  3.9.*) ok "Python $PYV (production runs 3.9.6)" ;;
  "")    miss "Python venv at $VENV" ;;
  *)     note "Python $PYV; production runs 3.9.6 (use PYTHON=python3.9 for an exact match)" ;;
esac
"$VENV/bin/python" - <<'PY' || MISSING=$((MISSING + 1))
import importlib.metadata as m, re, sys
want = {}
for line in open("requirements-lock.txt"):
    line = line.strip()
    if line and not line.startswith("#"):
        name, ver = line.split("==")
        want[name.lower()] = ver
for line in open("requirements-dev.txt"):
    line = line.strip()
    if line and not line.startswith("#"):
        name, ver = line.split("==")
        want[name.lower()] = ver
bad = []
for name, ver in sorted(want.items()):
    try:
        have = m.version(name)
    except m.PackageNotFoundError:
        bad.append(f"{name} not installed (want {ver})")
        continue
    if have != ver:
        bad.append(f"{name} {have} (pinned {ver})")
if bad:
    print("  [MISSING] Python packages differ from the pins:")
    for b in bad:
        print("              " + b)
    sys.exit(1)
print(f"  [ok]      {len(want)} Python packages match requirements-lock.txt / requirements-dev.txt")
PY
"$VENV/bin/python" -c "import playwright.sync_api" 2>/dev/null && ok "Python Playwright importable" || miss "Python Playwright (pip install -r requirements-dev.txt)"
NODE_BIN="$(command -v node || echo /opt/homebrew/bin/node)"
if [ -x "$NODE_BIN" ]; then ok "Node $("$NODE_BIN" --version)"; else miss "Node (brew install node / apt-get install nodejs)"; fi
for pkg in calculation-engines/concrete-slab-1.0.0 calculation-engines/stair-ontario-residential-v1; do
  [ -d "$pkg/node_modules/playwright" ] && ok "$pkg node_modules" || miss "$pkg node_modules (npm ci)"
done
if [ -d "/Applications/Google Chrome.app" ] || command -v google-chrome >/dev/null 2>&1 || [ -x /opt/google/chrome/chrome ]; then
  ok "Google Chrome (the Node calculator page tests launch channel \"chrome\")"
else
  miss "Google Chrome (the Node calculator page tests launch channel \"chrome\")"
fi
SOFFICE=""
[ -x /Applications/LibreOffice.app/Contents/MacOS/soffice ] && SOFFICE=/Applications/LibreOffice.app/Contents/MacOS/soffice
[ -z "$SOFFICE" ] && SOFFICE="$(command -v soffice || true)"
# Optional: no test needs LibreOffice (the signing tests inject a converter or use tests/fake_soffice.py),
# and production does not convert documents. It is only reported.
if [ -n "$SOFFICE" ]; then ok "LibreOffice $("$SOFFICE" --version 2>/dev/null | head -1) (optional)"
else note "LibreOffice not installed (optional: no test or production path needs it)"; fi

MASTER_SHA=24bb319a10a8d386136fffdff8737dac5a30b80ec3104808c13033c9f5000fb5
MASTER="${CALIBRAYTAI_FAMILY_05_MASTER_PATH:-$HOME/Documents/CalibAi/Approved Document Templates/Reusable Master Template Family V1/MASTER DOCX/05_Brayman_Ontario_Construction_Contract_COMMERCIAL_DRAFT_MASTER_V1.docx}"
if [ -f "$MASTER" ]; then
  HAVE="$( (shasum -a 256 "$MASTER" 2>/dev/null || sha256sum "$MASTER") | awk '{print $1}')"
  if [ "$HAVE" = "$MASTER_SHA" ]; then ok "Family 05 contract master (SHA-256 matches; confidential, never committed)"
  else miss "Family 05 contract master at $MASTER has SHA-256 $HAVE, expected $MASTER_SHA"; fi
else
  miss "Family 05 contract master (set CALIBRAYTAI_FAMILY_05_MASTER_PATH to a copy outside the repository)"
fi
HIST="${CALIBRAYTAI_HISTORICAL_ESTIMATES_DIR:-$HOME/Desktop/CalibAi Historical Estimates}"
if [ -d "$HIST" ]; then ok "Historical estimates folder ($(ls "$HIST" | wc -l | tr -d ' ') files; real customer workbooks, office Mac only)"
else note "Historical estimates folder absent: tests/test_historical_ingestion.py will skip 11 tests (expected outside the office Mac)"; fi
[ -f instance/brayman_estimator.db ] && note "instance/brayman_estimator.db exists (a local office database); tests do not use it"

echo
if [ "$MISSING" -eq 0 ]; then
  echo "READY. Run: $VENV/bin/python -m pytest -q"
  echo "Then the browser walk: node --test --test-force-exit tests/e2e/contractor_workflow.mjs"
else
  echo "NOT READY: $MISSING item(s) missing above."
  exit 1
fi
