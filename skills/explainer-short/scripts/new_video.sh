#!/usr/bin/env bash
# Create a new video folder from the starter.  usage: new_video.sh <studio-dir> <slug>
set -euo pipefail
STUDIO="${1:?usage: new_video.sh <studio-dir> <slug>}"; SLUG="${2:?slug required}"
[[ "$SLUG" =~ ^[a-z0-9][a-z0-9-]*$ ]] || { echo "slug must be lowercase letters, digits, dashes (e.g. how-dns-works)"; exit 1; }
D="$STUDIO/src/videos/$SLUG"
[ -e "$D" ] && { echo "exists: $D (edit it, or pick another slug)"; exit 1; }
mkdir -p "$D/stages"
cp "$STUDIO/src/videos/_starter/script.json" "$STUDIO/src/videos/_starter/t.ts" "$D/"
sed "s/__SLUG__/$SLUG/" "$STUDIO/src/videos/_starter/Video.tsx" > "$D/Video.tsx"
echo "created: $D  (write script.json next, then run voice.sh)"
