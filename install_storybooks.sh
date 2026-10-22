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
# Contractor and supplier-neutral books: open addresses.
# BMR and KBC books: private addresses. Their random names are made once on this server, kept in
# /root/calibrayt-storybook-links.txt and reused every run; they are not stored in GitHub.
KEYS=/root/calibrayt-storybook-links.txt
if [ ! -s "$KEYS" ]; then
  umask 077
  echo "BMR=$(tr -dc a-z0-9 </dev/urandom | head -c 14)" >  "$KEYS"
  echo "KBC=$(tr -dc a-z0-9 </dev/urandom | head -c 14)" >> "$KEYS"
fi
. "$KEYS"
[ -n "$BMR" ] && [ -n "$KBC" ] || { echo "STOP: $KEYS is damaged"; exit 1; }
S="$DOC/storybook"; mkdir -p "$S"
cp -r "$TMP"/storybook/contractor "$TMP"/storybook/supplier-connection "$S/"
rm -rf "$S/bmr-winchester" "$S/kbc"                       # old open addresses for the two supplier editions
for d in "$S"/bmr-winchester-* "$S"/kbc-*; do              # earlier private names, if the keys were ever changed
  case "$d" in "$S/bmr-winchester-$BMR"|"$S/kbc-$KBC") ;; *) [ -d "$d" ] && rm -rf "$d";; esac
done
mkdir -p "$S/bmr-winchester-$BMR" "$S/kbc-$KBC"
cp "$TMP"/storybook/bmr-winchester/index.html "$S/bmr-winchester-$BMR/index.html"
cp "$TMP"/storybook/kbc/index.html "$S/kbc-$KBC/index.html"
# never list the folder (that would reveal the private names)
printf '<!doctype html><meta charset="utf-8"><meta name="robots" content="noindex,nofollow"><title>CalibraytAI</title><meta http-equiv="refresh" content="0;url=/">\n' > "$S/index.html"
printf 'Options -Indexes\n' > "$S/.htaccess"
chown -R "$OWNER":"$OWNER" "$S"; chmod -R u=rwX,go=rX "$S"
rm -rf "$TMP"
sha256sum "$S"/*/index.html

echo "== 4. check the addresses"
code(){ curl -s -o /dev/null -w "%{http_code}" "$1"; }
U=https://calibraytai.com/storybook
for p in contractor supplier-connection "bmr-winchester-$BMR" "kbc-$KBC"; do printf "%-36s %s (expect 200)\n" "$p" "$(code "$U/$p/")"; done
for p in bmr-winchester kbc; do printf "%-36s %s (expect 404, old open address)\n" "$p" "$(code "$U/$p/")"; done
printf "%-36s %s\n" "folder listing" "$(curl -s "$U/" | grep -q -e "bmr-winchester-" -e "kbc-" && echo "SHOWS PRIVATE NAMES - send Claude this output" || echo "hidden (good)")"
echo
echo "PRIVATE LINKS - give each only to that supplier:"
echo "  BMR Winchester:        $U/bmr-winchester-$BMR/"
echo "  KBC (Home Hardware):   $U/kbc-$KBC/"
echo "If any check is not as expected, send Claude this whole output (the private links can be left out)."
