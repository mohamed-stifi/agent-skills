#!/usr/bin/env bash
# Type-check, render silent videos, and make a contact sheet of each.
# usage: render.sh <workspace> [all | <film-id> | <scene-id>]...     (default: all films)
# Outputs: source/out/<id>.mp4 and source/stills/<id>-sheet.png (every 15th frame).
source "$(dirname "$0")/_lib.sh"
need_ws "$1"; shift
(cd "$SRC" && npx tsc -p .) || { echo "TYPECHECK FAILED"; exit 1; }
targets=("$@"); { ((${#targets[@]})) && [ "${targets[0]}" != all ]; } || targets=($(film_ids))  # bash 3.2 safe
mkdir -p "$SRC/out" "$SRC/stills"
for id in "${targets[@]}"; do
  render_one "$id" "out/$id.mp4"
  n=$(ffprobe -v error -count_packets -select_streams v:0 -show_entries stream=nb_read_packets -of csv=p=0 "$SRC/out/$id.mp4")
  rows=$(( (n / 15 + 5) / 6 )); [ "$rows" -ge 1 ] || rows=1
  ffmpeg -v error -y -i "$SRC/out/$id.mp4" -vf "select=not(mod(n\,15)),scale=384:-1,tile=6x$rows" -frames:v 1 -update 1 "$SRC/stills/$id-sheet.png"
  echo "ok $id $(dur_of "$SRC/out/$id.mp4")s  sheet: source/stills/$id-sheet.png"
done
