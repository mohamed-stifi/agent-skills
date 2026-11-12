#!/usr/bin/env bash
# Tag a skill release after bumping metadata.version + adding a CHANGELOG entry and committing.
# usage: scripts/release.sh <skill>        -> creates git tag <skill>/v<version>  (push with: git push --tags)
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"
s="${1:?usage: release.sh <skill>}"
bash scripts/validate.sh "$s" >/dev/null || { bash scripts/validate.sh "$s"; exit 1; }
[ -z "$(git status --porcelain "skills/$s")" ] || { echo "commit your changes in skills/$s first"; exit 1; }
v="$(sed -n -E 's/^ +version: *"?([0-9.]+)"?/\1/p' "skills/$s/SKILL.md" | head -1)"
tag="$s/v$v"
git rev-parse -q --verify "refs/tags/$tag" >/dev/null && { echo "tag $tag exists — bump metadata.version first"; exit 1; }
git tag -a "$tag" -m "$s $v"
echo "tagged $tag  ->  git push origin $tag"
