#!/bin/bash
# Preservation tags for the 28 Oct 2026 turnover corrective pass. Run on the office Mac:
#   bash tools/ops/create_preservation_tags.sh [path-to-a-clone]   (default: ~/Desktop/Brayman-Estimator)
# Creates only the annotated tags that do not exist yet, each on the exact audited commit, and pushes them.
# Never moves, overwrites or deletes a tag or a branch. Safe to run again.
set -u
REPO=${1:-$HOME/Desktop/Brayman-Estimator}
cd "$REPO" || { echo "STOP: no repository at $REPO"; exit 1; }
git fetch -q origin --tags || { echo "STOP: fetch failed"; exit 1; }
made=0
while read -r name sha what; do
  [ -z "$name" ] && continue
  git cat-file -e "$sha^{commit}" 2>/dev/null || git fetch -q origin "$sha" 2>/dev/null
  git cat-file -e "$sha^{commit}" 2>/dev/null || { echo "STOP: commit $sha ($name) not found"; exit 1; }
  if git rev-parse -q --verify "refs/tags/$name" >/dev/null; then
    have=$(git rev-parse "$name^{commit}")
    [ "$have" = "$sha" ] && { echo "exists $name $sha"; continue; }
    echo "STOP: tag $name already points at $have, not $sha (left unchanged)"; exit 1
  fi
  git -c user.name="Joel Brayman" -c user.email="joel.brayman@gmail.com" tag -a "$name" "$sha" \
    -m "$what" -m "Preservation tag (turnover corrective pass, 28 Oct 2026). See docs/operations/source-of-truth.md. Do not delete." \
    && git push -q origin "refs/tags/$name" && { echo "created $name $sha"; made=$((made+1)); } || { echo "STOP: could not create or push $name"; exit 1; }
done <<'LIST'
preserve/2026-10-28/fg041-supplier-native-signing c2a3be143d5aff47a42591295ce3c37167d2c57d FG-041 supplier native signing source (signing/supplier-native-signing-on-prodesk)
preserve/2026-10-28/storybook-refined-2026-10-18 d0e66a3994dd8cf16fff551a83cee5a69d74900c Refined 18 Oct storybook archive (docs/storybook-refined-record-20261018)
preserve/2026-10-28/website-source 5f701cdaf67a8cbd35946540485c88c5fe3d54f0 Public website editable source (website/source)
preserve/2026-10-28/website-static-calibrayt 18904f1b53d0f1b3c29eff28e21e15ca13940704 Website static build v31 (website/calibrayt-static-2026-10-22)
preserve/2026-10-28/website-static-v1sync b6deb1b5b1b8f171ba1b6c9382783fd2bf346cbb Website static build, V1 sync (website/calibraytai-static-v1sync-2026-10-22)
preserve/2026-10-28/website-deploy-script-pinned 2e317ac528c212dbc572f9bf72dbcb1976716779 Pinned website deploy script (hosting/website-v1sync-2026-10-22)
preserve/2026-10-28/storybooks-site 4540c609d2419c1b9babb3777791abeb961aabb8 Storybook websites and installer (storybooks/site)
preserve/2026-10-28/airia-website-publish e5456c0855e0d12e291dcb135e0b63758cba3ad1 AiRIA website publish pack (publish/airia-website-595754a)
preserve/2026-10-28/airia-storybook-v15-publish 052c4fcdb75eff39865ef45b94df01b138168676 AiRIA Storybook v15 publish pack (publish/airia-storybook-v15)
preserve/2026-10-28/brayman-dark-logo-source 5ebbfdb1e961dc94d233dee2da0ea4de5b27783e Dark Brayman logo source (cursor/sidebar-navigation-refinement)
LIST
echo "PRESERVATION_TAGS=ok ($made created)"
