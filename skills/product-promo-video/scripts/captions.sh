#!/usr/bin/env bash
# Burned-in caption versions: the final film + captions drawn in the brand style, final audio copied back.
# usage: captions.sh <workspace> [film-id ...]      (default: every film)   Output: source/out/audio/<id>-captioned.mp4
source "$(dirname "$0")/_lib.sh"
need_ws "$1"; shift
ids=("$@"); ((${#ids[@]})) || ids=($(film_ids))  # bash 3.2 safe
for id in "${ids[@]}"; do
  A="$SRC/out/audio"
  [ -f "$A/$id-final.mp4" ] || { echo "missing $A/$id-final.mp4: run audio.sh first"; exit 1; }
  cp "$A/$id-final.mp4" "$A/$id-captions.json" "$SRC/public/"
  render_one "$id-captioned" "out/$id-captioned-silent.mp4" --muted
  d=$(dur_of "$A/$id-final.mp4")
  ffmpeg -v error -y -i "$SRC/out/$id-captioned-silent.mp4" -i "$A/$id-final.mp4" -map 0:v:0 -map 1:a:0 -c copy -t "$d" \
    -movflags +faststart "$A/$id-captioned.mp4"
  rm -f "$SRC/out/$id-captioned-silent.mp4"
  echo "ok $id-captioned $(dur_of "$A/$id-captioned.mp4")s (final ${d}s)"
done
