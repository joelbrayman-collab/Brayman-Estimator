#!/bin/bash
# One CalibraytAI identity (26 Oct 2026): connect the Training Centre to Production's sign-in. Run as root in WHM
# Terminal, after v1rel13 is on BOTH sites. Each step backs up /opt/calibrayt/env first and prints no password.
#
#   bash training_identity.sh prepare      make the connection secret; shows ONCE the value for Render
#                                          (IDENTITY_CLIENTS) — the Training Centre still signs in locally
#   bash training_identity.sh connect      after Render has the secret: switch real people to Production's
#                                          sign-in, then list (change nothing) how each person is matched
#   bash training_identity.sh reconcile    carry over training-only people's passwords (flask identity reconcile --apply)
#   bash training_identity.sh disconnect   break-glass: back to local Training Centre passwords at once
set -uo pipefail
ENV=/opt/calibrayt/env
APP=/opt/calibrayt/app
PROVIDER=https://calibryatai.onrender.com
STEP="${1:-}"
[ "$(id -u)" = 0 ] || { echo "STOP: run as root (WHM Terminal)"; exit 1; }
[ -f "$ENV" ] || { echo "STOP: $ENV is missing"; exit 1; }
in_env() { sudo -u calibrayt bash -c "cd $APP && set -a && . $ENV && set +a && $1"; }
backup() { local b="$ENV.bak-$(date +%Y%m%d-%H%M%S)"; cp -p "$ENV" "$b" || { echo "STOP: could not back up $ENV"; exit 1; }; echo "backup: $b"; }
set_keys() {  # set_keys KEY=VALUE ... ; KEY= removes it
  python3 - "$ENV" "$@" <<'PY'
import sys
path, pairs = sys.argv[1], [a.split("=", 1) for a in sys.argv[2:]]
want = {k: v for k, v in pairs}
out, seen = [], set()
for line in open(path).read().splitlines():
    key = line.split("=", 1)[0].strip()
    if key in want:
        if key not in seen and want[key] != "":
            out.append(f"{key}={want[key]}")
        seen.add(key)
        continue
    out.append(line)
for key, value in want.items():
    if key not in seen and value != "":
        out.append(f"{key}={value}")
open(path, "w").write("\n".join(out) + "\n")
PY
  chmod 600 "$ENV"; chown calibrayt "$ENV" 2>/dev/null || true
}
case "$STEP" in
  prepare)
    backup
    SECRET=$(openssl rand -hex 32)
    set_keys "IDENTITY_CLIENT_ID=training" "IDENTITY_CLIENT_SECRET=$SECRET" "IDENTITY_PROVIDER_URL="
    systemctl restart calibrayt-training
    echo "== Done. The Training Centre still signs people in locally."
    echo "== In Render → calibryatai → Environment, add these two (then Save, which redeploys):"
    echo "   IDENTITY_CLIENTS = training=$SECRET"
    echo "   IDENTITY_TRAINING_SITE_URL = https://training.calibraytai.com"
    echo "== This value is shown once. Do not paste it anywhere else."
    ;;
  connect)
    grep -q '^IDENTITY_CLIENT_SECRET=' "$ENV" || { echo "STOP: run 'prepare' first"; exit 1; }
    backup
    set_keys "IDENTITY_PROVIDER_URL=$PROVIDER"
    systemctl restart calibrayt-training; sleep 3
    echo "== Matching this site's real people with Production (nothing is changed by this listing):"
    if ! in_env "./venv/bin/flask identity reconcile"; then
      echo "STOP: Production did not accept the connection. Undoing: back to local passwords."
      set_keys "IDENTITY_PROVIDER_URL="; systemctl restart calibrayt-training; exit 1
    fi
    echo "== Connected. Real people now sign in here with their one CalibraytAI password."
    echo "== Next: bash training_identity.sh reconcile   (keeps training-only people's own passwords)"
    ;;
  reconcile)
    in_env "./venv/bin/flask identity reconcile --apply"
    ;;
  disconnect)
    backup
    set_keys "IDENTITY_PROVIDER_URL="
    systemctl restart calibrayt-training
    echo "== Disconnected: the Training Centre signs everyone in with its own local passwords again."
    ;;
  *) echo "usage: bash training_identity.sh prepare|connect|reconcile|disconnect"; exit 2 ;;
esac
