#!/bin/bash
# CalibraytAI Training Centre: send email through Postmark instead of the server's own mail system
# (sign-in reliability, Joel, 26 Oct 2026). Run as root in WHM Terminal, after v1rel13 is on the training site.
#   bash training_email_to_postmark.sh <from address on a Postmark-verified domain>
# Asks for the Postmark Server API token at a hidden prompt (never echoed, logged or stored anywhere but
# /opt/calibrayt/env, mode 600). Backs up /opt/calibrayt/env first. Makes a webhook username and password and
# shows them ONCE, for the Postmark webhook form. Then restarts the service and prints "flask email status".
# Safe to run again: it replaces the same settings. Undo: copy the printed backup over /opt/calibrayt/env and
# restart (systemctl restart calibrayt-training).
set -uo pipefail
ENV=/opt/calibrayt/env
APP=/opt/calibrayt/app
FROM="${1:-}"
[ "$(id -u)" = 0 ] || { echo "STOP: run as root (WHM Terminal)"; exit 1; }
[ -f "$ENV" ] || { echo "STOP: $ENV is missing"; exit 1; }
[[ "$FROM" =~ ^[^@[:space:]]+@[^@[:space:]]+\.[^@[:space:]]+$ ]] || { echo "STOP: give the From address, e.g. signin@calibraytai.com"; exit 1; }
read -rs -p "Postmark Server API token for the training server (hidden, press Return when pasted): " TOKEN; echo
[[ "$TOKEN" =~ ^[A-Za-z0-9-]{20,80}$ ]] || { echo "STOP: that does not look like a Postmark Server API token; nothing changed"; exit 1; }
BACKUP="$ENV.bak-$(date +%Y%m%d-%H%M%S)"
cp -p "$ENV" "$BACKUP" || { echo "STOP: could not back up $ENV; nothing changed"; exit 1; }
HOOK_USER=postmark
HOOK_PASS=$(openssl rand -hex 20)
TOKEN="$TOKEN" FROM="$FROM" HOOK_USER="$HOOK_USER" HOOK_PASS="$HOOK_PASS" python3 - "$ENV" <<'PY'
import os, sys
path = sys.argv[1]
want = {
    "TRANSACTIONAL_EMAIL_PROVIDER": "postmark",
    "POSTMARK_SERVER_TOKEN": os.environ["TOKEN"],
    "TRANSACTIONAL_FROM_EMAIL": os.environ["FROM"],
    "POSTMARK_WEBHOOK_USERNAME": os.environ["HOOK_USER"],
    "POSTMARK_WEBHOOK_PASSWORD": os.environ["HOOK_PASS"],
}
lines = open(path).read().splitlines()
out, seen = [], set()
for line in lines:
    key = line.split("=", 1)[0].strip()
    if key in want:
        if key not in seen:
            out.append(f"{key}={want[key]}")
            seen.add(key)
        continue
    out.append(line)
for key, value in want.items():
    if key not in seen:
        out.append(f"{key}={value}")
open(path, "w").write("\n".join(out) + "\n")
PY
chmod 600 "$ENV"; chown calibrayt "$ENV" 2>/dev/null || true
unset TOKEN
systemctl restart calibrayt-training
sleep 3
echo "== settings now (names only; secrets shown as set / not set)"
sudo -u calibrayt bash -c "cd $APP && set -a && . $ENV && set +a && ./venv/bin/flask email status"
echo "== backup of the previous settings: $BACKUP"
echo
echo "== For Postmark (shown once; type them into the webhook form, do not paste them anywhere else):"
echo "   Webhook URL: https://training.calibraytai.com/webhooks/postmark"
echo "   Basic auth username: $HOOK_USER"
echo "   Basic auth password: $HOOK_PASS"
