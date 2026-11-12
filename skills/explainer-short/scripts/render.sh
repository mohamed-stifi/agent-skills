#!/usr/bin/env bash
# Final render (MP4 1080x1920 + cover.jpg).  usage: render.sh <studio-dir> <slug>
set -euo pipefail
STUDIO="${1:?usage: render.sh <studio-dir> <slug>}"; SLUG="${2:?slug required}"
cd "$STUDIO"
node scripts/registry.mjs >/dev/null
mkdir -p "out/$SLUG"
npx remotion render src/index.ts "$SLUG" "out/$SLUG/$SLUG.mp4" --crf=18 --log=error
npx remotion still src/index.ts "$SLUG" "out/$SLUG/cover.jpg" --frame=45 --log=error >/dev/null 2>&1 || true
ffprobe -v error -show_entries format=duration,size -of default=nw=1 "out/$SLUG/$SLUG.mp4"
echo "VIDEO: $STUDIO/out/$SLUG/$SLUG.mp4"
echo "SUBS:  $STUDIO/out/$SLUG/$SLUG.srt"
echo "COVER: $STUDIO/out/$SLUG/cover.jpg"
