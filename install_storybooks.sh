#!/bin/bash
# CalibraytAI storybooks on calibraytai.com (HostPapa VPS). Run as root in WHM Terminal. Safe to run again.
# Copies the four storybooks from the GitHub branch storybooks/site into the website folder, under /storybook/.
# Reads the repository through the existing /opt/calibrayt/app clone; does not change the Training Centre's code.
echo "== 1. find the calibraytai.com website folder"
# calibraytai.com may be its own cPanel domain, or an alias of another one (for example calibraytai.solarlightasaservice.com).
DOC=$(awk -F': ' '/^documentroot:/{print $2}' /var/cpanel/userdata/*/calibraytai.com 2>/dev/null | head -1)
if [ -z "$DOC" ]; then
  for f in /var/cpanel/userdata/*/*; do
    case "$f" in *.cache|*.json|*_SSL|*/main|*/cache) continue;; esac
    if grep -qE '^(servername|serveralias):.*(^|[ :])(www\.)?calibraytai\.com( |$)' "$f" && ! grep -qE '^servername: *training\.' "$f"; then
      DOC=$(awk -F': ' '/^documentroot:/{print $2}' "$f"); echo "found in $f"; break
    fi
  done
fi
if [ -z "$DOC" ] || [ ! -d "$DOC" ]; then
  echo "STOP: could not find the website folder from cPanel. These files mention calibraytai.com:"
  grep -rl "calibraytai.com" /etc/apache2/conf.d /etc/nginx /var/cpanel/userdata 2>/dev/null | head -10
  exit 1
fi
OWNER=$(stat -c %U "$DOC"); echo "website folder: $DOC (owner $OWNER)"

echo "== 2. get the storybooks"
sudo -u calibrayt git -C /opt/calibrayt/app fetch -q origin storybooks/site || { echo "STOP: fetch failed"; exit 1; }
TMP=$(mktemp -d)
sudo -u calibrayt git -C /opt/calibrayt/app archive FETCH_HEAD storybook | tar -x -C "$TMP" || { echo "STOP: unpack failed"; exit 1; }

echo "== 3. install under $DOC/storybook"
# All four storybooks at plain, open addresses (Joel, 24 Oct 2026: no private links, search engines may list them).
S="$DOC/storybook"; mkdir -p "$S"
rm -rf "$S/contractor" "$S/supplier-connection" "$S/bmr-winchester" "$S/kbc"
cp -r "$TMP"/storybook/contractor "$TMP"/storybook/supplier-connection "$TMP"/storybook/bmr-winchester "$TMP"/storybook/kbc "$S/"
# Links already given out at the earlier private addresses keep working: each now forwards to the open address.
for d in "$S"/bmr-winchester-* "$S"/kbc-*; do
  [ -d "$d" ] || continue
  case "$d" in */bmr-winchester-*) to=/storybook/bmr-winchester/;; *) to=/storybook/kbc/;; esac
  rm -f "$d"/*; printf '<!doctype html><meta charset="utf-8"><title>CalibraytAI</title><meta http-equiv="refresh" content="0;url=%s"><a href="%s">Continue</a>\n' "$to" "$to" > "$d/index.html"
done
# /storybook/ itself goes to the website home page (no folder listing)
printf '<!doctype html><meta charset="utf-8"><title>CalibraytAI</title><meta http-equiv="refresh" content="0;url=/">\n' > "$S/index.html"
printf 'Options -Indexes\n' > "$S/.htaccess"
chown -R "$OWNER":"$OWNER" "$S"; chmod -R u=rwX,go=rX "$S"
rm -rf "$TMP"
sha256sum "$S"/*/index.html

echo "== 4. check the addresses"
code(){ curl -s -o /dev/null -w "%{http_code}" "$1"; }
U=https://calibraytai.com/storybook
for p in contractor supplier-connection bmr-winchester kbc; do printf "%-24s %s (expect 200)  %s/%s/\n" "$p" "$(code "$U/$p/")" "$U" "$p"; done
echo
echo "STORYBOOK LINKS (open to anyone):"
for p in contractor supplier-connection bmr-winchester kbc; do echo "  $U/$p/"; done
