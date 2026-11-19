#!/usr/bin/env bash
# Objective checks of the finished films: duration, loudness, and what a listener hears (Whisper).
# usage: check.sh <workspace> [--lang en] [--no-asr]
source "$(dirname "$0")/_lib.sh"
need_ws "$1"; shift
LANG_ASR=en; ASR=1
while [ $# -gt 0 ]; do case "$1" in --lang) LANG_ASR="$2"; shift 2;; --no-asr) ASR=0; shift;; *) shift;; esac; done
fail=0; finals=()
for id in $(film_ids); do
  f="$SRC/out/audio/$id-final.mp4"; s="$SRC/out/$id.mp4"
  [ -f "$f" ] || { echo "MISSING $f"; fail=1; continue; }
  d1=$(dur_of "$s"); d2=$(dur_of "$f")
  loud=$(ffmpeg -hide_banner -i "$f" -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I:|Peak:)" | tr -s ' ' | tr '\n' ' ')
  echo "$id  silent ${d1}s  final ${d2}s  $loud"
  awk -v a="$d1" -v b="$d2" 'BEGIN{exit !((a-b)>0.05 || (b-a)>0.05)}' && { echo "  DURATION MISMATCH"; fail=1; }
  c="$SRC/out/audio/$id-captioned.mp4"
  if [ -f "$c" ]; then d3=$(dur_of "$c"); echo "  captioned ${d3}s"; awk -v a="$d1" -v b="$d3" 'BEGIN{exit !((a-b)>0.05 || (b-a)>0.05)}' && { echo "  CAPTIONED DURATION MISMATCH"; fail=1; }; fi
  finals+=("$f")
done
if [ "$ASR" = 1 ] && ((${#finals[@]})); then
  echo "-- what a listener hears (compare with the lines in source/audio/films.py):"
  (cd "$SRC/audio" && uv run --with faster-whisper python asr_check.py --lang "$LANG_ASR" "${finals[@]}" 2>&1 | grep -E "^==|^  ")
fi
[ "$fail" = 0 ] && echo "CHECK OK" || { echo "CHECK FAILED"; exit 1; }
