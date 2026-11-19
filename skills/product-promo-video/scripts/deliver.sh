#!/usr/bin/env bash
# Put the finished videos where people can find them, and version everything.
#   output/          ONLY the final videos (for non-technical viewers)
#   output-extras/   subtitles, transcripts, captions, audio mix, contact sheets
#   <cwd>/promo-videos/<slug>/   a copy of output/ in the folder the user was working in (unless --no-copy / --to DIR)
# usage: deliver.sh <workspace> [--to DIR] [--no-copy]
source "$(dirname "$0")/_lib.sh"
need_ws "$1"; shift
DEST="$CWD/promo-videos/$SLUG"; COPY=1
while [ $# -gt 0 ]; do case "$1" in --to) DEST="$2"; shift 2;; --no-copy) COPY=0; shift;; *) echo "unknown option $1"; exit 1;; esac; done
A="$SRC/out/audio"
rm -f "$WS/output/"*.mp4
mkdir -p "$WS/output" "$WS/output-extras/sheets"
n=0
for id in $(film_ids); do
  [ -f "$A/$id-final.mp4" ] || { echo "skip $id (no final; run audio.sh)"; continue; }
  cp "$A/$id-final.mp4" "$WS/output/$SLUG-$id.mp4"; n=$((n + 1))
  [ -f "$A/$id-captioned.mp4" ] && cp "$A/$id-captioned.mp4" "$WS/output/$SLUG-$id-captioned.mp4"
  for ext in .srt .vtt -transcript.md -captions.json -mix.wav; do [ -f "$A/$id$ext" ] && cp "$A/$id$ext" "$WS/output-extras/$SLUG-$id$ext"; done
  [ -f "$SRC/stills/$id-sheet.png" ] && cp "$SRC/stills/$id-sheet.png" "$WS/output-extras/sheets/"
done
[ "$n" -gt 0 ] || { echo "NOTHING TO DELIVER"; exit 1; }
if [ "$COPY" = 1 ]; then mkdir -p "$DEST" && rm -f "$DEST/"*.mp4 && cp "$WS/output/"*.mp4 "$DEST/"; fi
cd "$WS" && git add -A >/dev/null && git -c user.name="${GIT_AUTHOR_NAME:-promo-video}" -c user.email="${GIT_AUTHOR_EMAIL:-promo-video@localhost}" \
  commit -qm "deliver $(date '+%F %H:%M')" >/dev/null 2>&1 || true
echo "DELIVERED"
for f in "$WS/output/"*.mp4; do printf '  %-48s %6.1fs\n' "$(basename "$f")" "$(dur_of "$f")"; done
echo "workspace: $WS/output"
[ "$COPY" = 1 ] && echo "copied to: $DEST"
