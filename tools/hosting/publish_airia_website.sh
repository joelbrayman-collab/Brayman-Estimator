#!/bin/bash
# AiRIA public website capability update -> ai-ria.com (22 Oct 2026). Run as root in WHM Terminal.
# Source: joelbrayman-collab/Discovery-Search, approved commit 595754a0eb25146ac3db5e2d9c1859068d02e7f5,
# folder docs/brand/public-website/working/capability-update-2026-10-19/site/.
# Backs up the current pages and assets/ OUTSIDE the document root first. Uploads only site/ files.
# Deletes nothing. Does not touch Calibrayt or Training Centre folders. Does not merge anything.
COMMIT=595754a0eb25146ac3db5e2d9c1859068d02e7f5
DIR=docs/brand/public-website/working/capability-update-2026-10-19
docroot=$(whmapi1 domainuserdata domain=ai-ria.com 2>/dev/null | awk '/documentroot:/{print $2; exit}')
[ "$docroot" = "/home/solarlight/public_html/ai-ria.com" ] || { echo "STOP: unexpected document root '$docroot'"; exit 1; }
work=$(mktemp -d)
git init -q "$work/r" && cd "$work/r" && git remote add origin https://github.com/joelbrayman-collab/Discovery-Search.git
git fetch -q --depth 1 origin "$COMMIT" || { echo "STOP: could not fetch the approved commit"; exit 1; }
git -c advice.detachedHead=false checkout -q FETCH_HEAD -- "$DIR" || { echo "STOP: folder missing"; exit 1; }
src="$work/r/$DIR/site"
echo "approved commit: $(git rev-parse FETCH_HEAD)  files to upload: $(find "$src" -type f | wc -l)"
# verify every file against VERIFICATION.json before touching the live site
python3 - "$work/r/$DIR/VERIFICATION.json" "$src" <<'PY' || { echo "STOP: hash check failed"; exit 1; }
import hashlib, json, os, sys
v = json.load(open(sys.argv[1])); src = sys.argv[2]
entries = v["files"]
items = entries.items() if isinstance(entries, dict) else [(e.get("path") or e.get("file"), e) for e in entries]
checked = bad = 0
for path, meta in items:
    want = meta if isinstance(meta, str) else (meta.get("sha256") or meta.get("hash"))
    rel = path.split("site/", 1)[-1] if "site/" in path else path
    f = os.path.join(src, rel)
    if not os.path.isfile(f):
        continue
    got = hashlib.sha256(open(f, "rb").read()).hexdigest()
    checked += 1
    if want and got != want:
        bad += 1; print("MISMATCH", rel)
on_disk = sum(len(fs) for _, _, fs in os.walk(src))
print(f"hash-checked {checked} of {on_disk} files, mismatches {bad}")
sys.exit(1 if bad or checked < on_disk else 0)
PY
backup=/root/airia-website-backup-$(date +%Y%m%d-%H%M%S)
mkdir -p "$backup"
( cd "$docroot" && cp -a *.html assets "$backup/" 2>/dev/null )
( cd "$docroot" && tar czf "$backup/full-docroot.tar.gz" . )
echo "backup: $backup ($(ls "$backup" | wc -l) entries)"
cp -a --no-preserve=ownership "$src/." "$docroot/"
chown -R solarlight:solarlight "$docroot"
# confirm the live files now match the approved files
python3 - "$src" "$docroot" <<'PY'
import hashlib, os, sys
src, dst = sys.argv[1:]
bad = n = 0
for root, _, fs in os.walk(src):
    for name in fs:
        rel = os.path.relpath(os.path.join(root, name), src); n += 1
        h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
        if h(os.path.join(src, rel)) != h(os.path.join(dst, rel)):
            bad += 1; print("DIFFERS", rel)
print(f"live files identical to approved: {n - bad} of {n}")
PY
for p in / /platform.html /how-it-works.html /assets/site.css; do
  echo "$p $(curl -s -o /dev/null -w '%{http_code}' -H 'Host: ai-ria.com' http://127.0.0.1$p)"
done
rm -rf "$work"
echo "rollback: cp -a $backup/*.html $backup/assets $docroot/   (or extract full-docroot.tar.gz)"
echo "== done"
