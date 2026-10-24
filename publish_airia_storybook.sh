#!/bin/bash
# AiRIA Storybook v15 -> https://www.ai-ria.com/storybook/ (24 Oct 2026). Run as root in WHM Terminal.
# Source: joelbrayman-collab/Discovery-Search branch docs/storybook-v15-20261024 (58c035a),
# folder docs/brand/storybook/hostpapa-upload/storybook/ — copied unchanged to this public branch because
# Discovery-Search is private. Adds ONLY <ai-ria.com docroot>/storybook/index.html and read.html.
# Changes, overwrites and deletes nothing else. Stops if storybook/ already exists. Does not touch
# Calibrayt, the Training Centre, Render or the AiRIA application. Keeps the files' noindex tag.
set -u
COPY=${1:?usage: bash publish_airia_storybook.sh <commit of branch publish/airia-storybook-v15>}
docroot=$(whmapi1 domainuserdata domain=ai-ria.com 2>/dev/null | awk '/documentroot:/{print $2; exit}')
[ -n "$docroot" ] && [ -d "$docroot" ] || { echo "STOP: could not find the ai-ria.com document root"; exit 1; }
case "$docroot" in *calibray*|*training*) echo "STOP: document root '$docroot' looks like a Calibrayt folder"; exit 1;; esac
echo "ai-ria.com document root: $docroot (owner $(stat -c %U "$docroot"))"
if [ -e "$docroot/storybook" ]; then
  echo "STOP: $docroot/storybook already exists. Nothing was changed. It contains:"
  ls -la "$docroot/storybook"; exit 1
fi
work=$(mktemp -d)
git init -q "$work/r" && cd "$work/r" && git remote add origin https://github.com/joelbrayman-collab/Brayman-Estimator.git
GIT_TERMINAL_PROMPT=0 git fetch -q --depth 1 origin "$COPY" || { echo "STOP: could not fetch $COPY"; exit 1; }
git -c advice.detachedHead=false checkout -q FETCH_HEAD || { echo "STOP: checkout failed"; exit 1; }
( cd storybook && sha256sum -c ../SHA256SUMS ) || { echo "STOP: file check failed; nothing was changed"; rm -rf "$work"; exit 1; }
owner=$(stat -c %U "$docroot"); group=$(stat -c %G "$docroot")
mkdir "$docroot/storybook"
cp storybook/index.html storybook/read.html "$docroot/storybook/"
chown -R "$owner:$group" "$docroot/storybook"
chmod 755 "$docroot/storybook"; chmod 644 "$docroot/storybook/index.html" "$docroot/storybook/read.html"
rm -rf "$work"
echo "== uploaded"
ls -l "$docroot/storybook"
( cd "$docroot/storybook" && sha256sum index.html read.html )
echo "permissions of the rest of the site, for comparison:"
stat -c '%a %U:%G %n' "$docroot" "$docroot/index.html" 2>/dev/null
echo "== HTTPS checks"
for p in /storybook/ /storybook/read.html; do
  out=$(curl -s -w '\n%{http_code} %{size_download}' "https://www.ai-ria.com$p")
  code=$(printf '%s' "$out" | tail -1)
  body=$(printf '%s' "$out" | sed '$d')
  printf '%-22s HTTP %s  noindex:%s  AiRIA:%s\n' "$p" "$code" \
    "$(printf '%s' "$body" | grep -q 'noindex' && echo yes || echo NO)" \
    "$(printf '%s' "$body" | grep -qi 'airia' && echo yes || echo NO)"
done
echo "home page still: HTTP $(curl -s -o /dev/null -w '%{http_code}' https://www.ai-ria.com/)"
echo "To undo (removes only what this added): rm -rf $docroot/storybook"
echo "== done"
