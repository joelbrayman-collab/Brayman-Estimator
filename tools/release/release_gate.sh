#!/bin/bash
# CalibraytAI release gate for a release WITHOUT a database change. Runs on the office Mac.
# It pushes nothing and deploys nothing: it stops at READY_FOR_PUSH. Production needs Joel's
# separate authorization; then Claude pushes the tested commit itself to main and deploys it,
# and Joel runs postrelease_check.sh.
#
# Replaces the per-release copies in ~/Desktop/Brayman-Estimator/generated/ (cal1_release.sh,
# v1bd_release.sh, ...). The gates are the same ones those scripts ran; only the release values
# are now parameters instead of being edited into a new copy each time.
#
# Usage (from any folder; fetch this script from the candidate commit itself):
#   git -C ~/Desktop/Brayman-Estimator fetch -q origin <branch>
#   git -C ~/Desktop/Brayman-Estimator show <candidate>:tools/release/release_gate.sh > /tmp/release_gate.sh
#   bash /tmp/release_gate.sh --label cal2 --candidate <sha> --branch v1/completion \
#        --main-base <sha> --live-base <sha> --live-deploy <dep-id> [--browser-expected 43]
#
# Gates (stops at the first failure):
#   1 one run at a time; GitHub main = --main-base; --branch = --candidate; live instance (SSH) = --live-base
#   2 fresh clone at the candidate: fast-forward from main, descends from live, no migration or model change,
#     nothing outside app/ tests/ docs/ tools/ calculation-engines/ requirements*.txt changed;
#     Python from requirements.txt + requirements-dev.txt with requirements-lock.txt (production's exact
#     versions); complete native regression must exit 0 with NO skipped test (on the Mac the historical
#     folder and Python Playwright are present, so nothing may skip); the end-to-end contractor walk and the
#     Cal tests must have run and passed; release browser checks in Google Chrome
#   3 fresh hosted backup (SQLite online backup), copied to the Mac, checksum and integrity verified, rows counted
#   3b contract signing readiness (read-only)
#   4 READY_FOR_PUSH — stop.
# A release WITH a migration still needs its own rehearsal script, prepared and authorized separately.
set -u
usage() { sed -n '2,32p' "$0"; exit 2; }
LABEL=""; SHA=""; BRANCH=""; MAIN_BASE=""; LIVE_BASE=""; LIVE_DEPLOY=""; BROWSER_EXPECTED=43
while [ $# -gt 0 ]; do
  case "$1" in
    --label) LABEL=$2; shift 2;;
    --candidate) SHA=$2; shift 2;;
    --branch) BRANCH=$2; shift 2;;
    --main-base) MAIN_BASE=$2; shift 2;;
    --live-base) LIVE_BASE=$2; shift 2;;
    --live-deploy) LIVE_DEPLOY=$2; shift 2;;
    --browser-expected) BROWSER_EXPECTED=$2; shift 2;;
    *) usage;;
  esac
done
for v in LABEL SHA BRANCH MAIN_BASE LIVE_BASE LIVE_DEPLOY; do [ -n "${!v}" ] || usage; done
for v in SHA MAIN_BASE LIVE_BASE; do
  [[ "${!v}" =~ ^[0-9a-f]{40}$ ]] || { echo "$v must be a full 40-character commit SHA"; exit 2; }
done
[[ "$LABEL" =~ ^[a-z0-9-]+$ ]] || { echo "--label: lower-case letters, digits and dashes only"; exit 2; }

REPO_URL=https://github.com/joelbrayman-collab/Brayman-Estimator.git
GEN=/Users/joelbrayman/Desktop/Brayman-Estimator/generated
HOST=srv-dar95mh42hec73df4rug@ssh.virginia.render.com
SSH_OPTS=(-o UpdateHostKeys=no)
BACKUPS=$HOME/Desktop/Brayman-office-backups
DEST=$HOME/Developer/Brayman-Estimator-$LABEL-release-$(date +%Y%m%d-%H%M%S)
TS=$(date +%Y%m%d-%H%M%S); OUT="$GEN/$LABEL-release-$TS"; LOG="$OUT.log"; STATUS="$GEN/$LABEL-release-status.txt"
STATE="$GEN/$LABEL-release-state.txt"
mkdir -p "$GEN"

# One run at a time (two copies of a release script once ran side by side on 18 Oct).
LOCKDIR="$GEN/.release-gate.lock"
if ! mkdir "$LOCKDIR" 2>/dev/null; then
  echo "STOP: another release gate is running (lock $LOCKDIR, started by: $(cat "$LOCKDIR/owner" 2>/dev/null))."
  echo "If no other run is open in any Terminal window, remove the lock folder and start again."
  exit 1
fi
echo "$LABEL pid $$ $(date)" > "$LOCKDIR/owner"
trap 'rm -rf "$LOCKDIR"' EXIT

exec > >(tee "$LOG") 2>&1
status() { echo "$1" >> "$STATUS"; echo "  [status] $1"; }
stop() { status "STOPPED: $1"; echo "STOP: $1"; exit 1; }
val() { grep "^$1=" "$2" | head -1 | cut -d= -f2-; }
REMOTE_PY='cd /opt/render/project/src && if [ -x .venv/bin/python ]; then PY=.venv/bin/python; else PY=$(command -v python3); fi; $PY -'
: > "$STATUS"; : > "$STATE"; status "STARTED $(date) label=$LABEL log=$LOG"

echo "== 1. GitHub main, the candidate branch and the live instance, each checked separately"
MAIN=$(git ls-remote "$REPO_URL" refs/heads/main | cut -f1)
[ "$MAIN" = "$MAIN_BASE" ] || stop "GitHub main is $MAIN, expected $MAIN_BASE"
BR=$(git ls-remote "$REPO_URL" "refs/heads/$BRANCH" | cut -f1)
[ "$BR" = "$SHA" ] || stop "$BRANCH is $BR, expected the candidate $SHA"
LIVE=$(ssh "${SSH_OPTS[@]}" -n "$HOST" 'echo SHA=$RENDER_GIT_COMMIT' 2>/dev/null | tr -d '\r' | grep '^SHA=' | cut -d= -f2)
[ "$LIVE" = "$LIVE_BASE" ] || stop "live instance runs '$LIVE', expected $LIVE_BASE"
status "BASELINE github_main=$MAIN live=$LIVE $BRANCH=$BR to_release=$SHA"

echo "== 2. Clean clone at the candidate; checks; complete native regression; browser checks in Chrome"
[ -e "$DEST" ] && stop "$DEST exists"
mkdir -p "$HOME/Developer"
git clone -q "$REPO_URL" "$DEST" || stop "clone failed"
cd "$DEST"
git fetch -q origin "$BRANCH" || stop "fetch of $BRANCH failed"
git -c advice.detachedHead=false checkout -q "$SHA" || stop "checkout failed (is $SHA pushed to $BRANCH?)"
[ "$(git rev-parse HEAD)" = "$SHA" ] || stop "clone is not $SHA"
git merge-base --is-ancestor "$MAIN_BASE" "$SHA" || stop "$SHA is not a fast-forward from main $MAIN_BASE"
git merge-base --is-ancestor "$LIVE_BASE" "$SHA" || stop "$SHA does not descend from live $LIVE_BASE"
[ -z "$(git diff --name-only "$LIVE_BASE" "$SHA" -- migrations app/models app/plan_intelligence/models.py)" ] \
  || stop "migrations or models changed: this gate is for releases without a database change"
OUTSIDE=$(git diff --name-only "$MAIN_BASE" "$SHA" | grep -vE '^(app/|tests/|docs/|tools/|calculation-engines/|requirements(-dev|-lock)?\.txt$)')
[ -z "$OUTSIDE" ] || stop "unexpected files changed: $OUTSIDE"
status "FAST_FORWARD main $MAIN_BASE -> $SHA ($(git rev-list --count "$MAIN_BASE..$SHA") commits); descends from live; no migration or model change"
HELPERS=$(cd tools/release && shasum -a 256 hosted_preflight.py hosted_postcheck.py signing_readiness.py evidence_*.mjs | awk '{printf "%s=%s ", $2, substr($1,1,12)}')
status "HELPERS from $SHA: $HELPERS"
/usr/bin/python3 -m venv venv || stop "venv failed"
./venv/bin/python -m pip install -q --upgrade pip
./venv/bin/python -m pip install -q -r requirements.txt -r requirements-dev.txt -c requirements-lock.txt \
  || stop "package install failed"
./venv/bin/python -m playwright install chromium >/dev/null 2>&1 || stop "Playwright Chromium install failed"
for pkg in calculation-engines/concrete-slab-1.0.0 calculation-engines/stair-ontario-residential-v1; do
  ( cd "$pkg" && npm ci --no-audit --no-fund >/dev/null 2>&1 ) || stop "npm ci failed in $pkg"
done
bash tools/setup_test_environment.sh --check || stop "test environment check failed"
PYTEST="./venv/bin/python -u -X faulthandler -m pytest -p no:cacheprovider -o faulthandler_timeout=180"
START=$(date +%s)
$PYTEST -q -rfEs --junitxml="$OUT-junit.xml" tests 2>&1 | tee "$OUT-full.txt" | tail -15
FULL=${PIPESTATUS[0]}
status "MAC_FULL=$(grep -E '(passed|failed)' "$OUT-full.txt" | tail -1) exit=$FULL duration=$(( $(date +%s) - START ))s"
[ "$FULL" -eq 0 ] || stop "complete Mac regression did not pass; nothing pushed"
/usr/bin/python3 - "$OUT-junit.xml" <<'PYEOF' || stop "a test was skipped, or the end-to-end contractor walk or the Cal tests did not run and pass"
import sys, xml.etree.ElementTree as E
cases = list(E.parse(sys.argv[1]).iter("testcase"))
skipped = [c.get("classname") + "::" + c.get("name") for c in cases if any(x.tag == "skipped" for x in c)]
for s in skipped:
    print("SKIPPED " + s)
def clean(name):
    picked = [c for c in cases if c.get("classname") == name]
    return picked and not any(x.tag in ("skipped", "failure", "error") for c in picked for x in c)
sys.exit(0 if not skipped and clean("tests.test_contractor_workflow_e2e") and clean("tests.test_cal_find_it") else 1)
PYEOF
status "NO_SKIPS; E2E_CONTRACTOR_WALK=passed in Google Chrome; CAL_TESTS=passed"
( cd tools/release && EVIDENCE_REPO="$DEST" node --test --test-reporter=tap --test-force-exit --test-concurrency=1 \
    evidence_employment_v11.mjs evidence_trade_pages.mjs evidence_cal_find_it.mjs ) > "$OUT-browser.txt" 2>&1
BR_EXIT=$?
grep -E '(tests|pass|fail) [0-9]+$|^not ok' "$OUT-browser.txt"
[ "$BR_EXIT" -eq 0 ] && grep -qE "^(# |ℹ )pass $BROWSER_EXPECTED\$" "$OUT-browser.txt" && grep -qE '^(# |ℹ )fail 0$' "$OUT-browser.txt" \
  || stop "browser checks failed (expected $BROWSER_EXPECTED passed, 0 failed)"
status "BROWSER_CHECKS=$BROWSER_EXPECTED passed in Google Chrome (desktop and phone)"

echo "== 3. Fresh hosted backup"
ssh "${SSH_OPTS[@]}" "$HOST" "export BACKUP_PREFIX=pre-$LABEL; $REMOTE_PY" < tools/release/hosted_preflight.py | tee "$OUT-preflight.txt"
grep -q '^PREFLIGHT=ok' "$OUT-preflight.txt" || stop "hosted preflight failed"
[ "$(val RUNNING_SHA "$OUT-preflight.txt")" = "$LIVE_BASE" ] || stop "live instance is not $LIVE_BASE"
[ "$(val LIVE_INTEGRITY "$OUT-preflight.txt")" = "ok" ] || stop "live integrity is not ok"
[ "$(val BACKUP_INTEGRITY "$OUT-preflight.txt")" = "ok" ] || stop "backup integrity is not ok"
REVISION=$(val LIVE_REVISION "$OUT-preflight.txt")
[ -n "$REVISION" ] && [ "$(val BACKUP_REVISION "$OUT-preflight.txt")" = "$REVISION" ] || stop "backup revision differs from live"
grep -q "^revision = \"$REVISION\"" migrations/versions/*.py || stop "live revision $REVISION is not a migration in the candidate"
BPATH=$(val BACKUP_PATH "$OUT-preflight.txt"); BSHA=$(val BACKUP_SHA256 "$OUT-preflight.txt")
mkdir -p "$BACKUPS"
LOCALB="$BACKUPS/$(basename "$BPATH")"
for i in 1 2 3 4 5; do
  scp "${SSH_OPTS[@]}" -q "$HOST:$BPATH" "$BACKUPS/" && [ "$(shasum -a 256 "$LOCALB" | awk '{print $1}')" = "$BSHA" ] && break
  echo "  backup copy attempt $i did not complete; retrying in $((i * 10)) s"; rm -f "$LOCALB"; sleep $((i * 10))
done
[ -f "$LOCALB" ] || stop "could not copy the backup to the Mac"
[ "$(shasum -a 256 "$LOCALB" | awk '{print $1}')" = "$BSHA" ] || stop "Mac backup checksum differs"
[ "$(/usr/bin/sqlite3 "$LOCALB" 'PRAGMA integrity_check;')" = "ok" ] || stop "Mac backup integrity is not ok"
BROWS=$(/usr/bin/python3 - "$LOCALB" <<'PYEOF'
import sqlite3, sys
c = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
t = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
print("TABLES=%d ROWS=%d" % (len(t), sum(c.execute('SELECT COUNT(*) FROM "%s"' % x).fetchone()[0] for x in t)))
PYEOF
)
status "BACKUP=$BPATH sha256=$BSHA $BROWS revision=$REVISION integrity=ok; Mac copy $LOCALB matches"

echo "== 3b. Contract signing readiness on the live database (read-only)"
ssh "${SSH_OPTS[@]}" "$HOST" "$REMOTE_PY" < tools/release/signing_readiness.py | tee "$OUT-signing-readiness.txt"
grep -q '^READINESS=ok' "$OUT-signing-readiness.txt" || stop "no ACTIVE PRODUCTION contract package on the live database"
status "SIGNING_READINESS $(grep '^ACTIVE_PRODUCTION_PACKAGES=' "$OUT-signing-readiness.txt"); $(grep '^SIGNING_ARTIFACTS=' "$OUT-signing-readiness.txt")"

cat > "$STATE" <<EOF
SHA=$SHA
LIVE_BASE=$LIVE_BASE
LIVE_DEPLOY=$LIVE_DEPLOY
REVISION=$REVISION
BACKUP=$LOCALB
BACKUP_ROWS=$BROWS
CLONE=$DEST
EOF
echo "== 4. READY_FOR_PUSH — stop here"
status "ROLLBACK_TARGET=redeploy $LIVE_BASE ($LIVE_DEPLOY, same settings); no database change to undo; restore only with Joel's approval from $LOCALB"
status "READY_FOR_PUSH commit=$SHA (nothing pushed, nothing deployed; production needs Joel's authorization)"
echo "== DONE. All gates passed. Send Claude the status file: $STATUS"
