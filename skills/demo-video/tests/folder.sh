#!/usr/bin/env bash
# Scenarios of issue #30: everything in <repo>/.video_demo_dir with an INDEX.md. Needs python3 and git (runs in
# CI); the built-video check also needs uv, vhs-free card scenes, ffmpeg and the voice model.
# usage: bash tests/folder.sh
set -uo pipefail
SKILL=$(cd "$(dirname "$0")/.." && pwd)
pass=0; fail=0; skip=0
check() { if eval "$2"; then echo "ok   $1"; pass=$((pass+1)); else echo "FAIL $1"; fail=$((fail+1)); return 1; fi; }
V=$(mktemp -d "${TMPDIR:-/tmp}/dv-fo.XXXXXX"); trap 'rm -rf "$V"' EXIT
VD="python3 $SKILL/scripts/vdir.py"
R="$V/repo"; mkdir -p "$R" && git -C "$R" init -q && echo hi > "$R/a.txt" && git -C "$R" add a.txt \
  && git -C "$R" -c user.name=t -c user.email=t@t commit -qm init
mode() { stat -c %a "$1" 2>/dev/null || stat -f %Lp "$1"; }

t=the_folder_is_set_up_once_and_hidden_from_git
out=$($VD init "$R" 2>&1)
D="$R/.video_demo_dir"
check $t '[ -z "$(git -C "$R" status --porcelain)" ] && [ "$(cat "$D/.gitignore")" = "*" ] && [ "$(mode "$D/secrets")" = 700 ] \
  && for s in videos features work secrets logs run; do [ -d "$D/$s" ] || exit 1; done && [ -s "$D/INDEX.md" ] && [ -s "$D/state.json" ]' \
  || { echo "$out"; git -C "$R" status --porcelain; ls -la "$D"; } | sed 's/^/     /'

t=a_re_record_keeps_the_old_version
v1=$($VD video "$R" notes-demo | tail -1); echo 'TITLE = "Notes v1"; OUTPUT_NAME = "notes"' > "$v1/src/script.py"
sum1=$(cat "$v1"/src/* | shasum | cut -c1-12)
v2=$($VD video "$R" notes-demo | tail -1)
check $t '[ "$(basename "$v1")" = v1 ] && [ "$(basename "$v2")" = v2 ] && [ "$(cat "$v1"/src/* | shasum | cut -c1-12)" = "$sum1" ] \
  && grep -q "Notes v1" "$v2/src/script.py" && [ -s "$v2/src/engine.py" ] && [ -s "$v2/src/vdir.py" ]' \
  || { echo "v1=$v1 v2=$v2"; ls "$v2/src"; } | sed 's/^/     /'

t=index_is_rebuilt_from_the_state
cat > "$v1/src/script.py" <<EOF
TITLE = "Notes: saving a note"; OUTPUT_NAME = "notes"; VIDEO_TYPE = "tutorial"; WORKDIRS = {"main": "$R"}
EOF
mkdir -p "$v1/build/00" "$v1/build/01" "$v1/chapters"; : > "$v1/notes.mp4"; : > "$v1/notes.md"
echo '{"num": "00", "title": "Start it", "file": "00-start.mp4", "duration": 52.0, "timeline": []}' > "$v1/build/00/meta.json"
echo '{"num": "01", "title": "Save a note", "file": "01-save.mp4", "duration": 70.5, "timeline": []}' > "$v1/build/01/meta.json"
$VD register "$v1" >/dev/null
$VD note "$R" "The 422 on an empty note is shown on purpose."
$VD leftover "$R" "A Slack app named zops-test in the test workspace."
head=$(git -C "$R" rev-parse --short HEAD)
I="$D/INDEX.md"
check $t 'grep -qF "| **notes-demo**: Notes: saving a note | v1 (latest) | tutorial |" "$I" && grep -qF "| **notes-demo** | v2 (draft, not recorded yet) |" "$I" && grep -qF "main@$head" "$I" && grep -qF "| 2:02 | 2 |" "$I" \
  && grep -qF "[video](videos/notes-demo/v1/notes.mp4)" "$I" && grep -qF "0:52 **01** Save a note" "$I" \
  && grep -qF "shown on purpose" "$I" && grep -qF "zops-test" "$I"' || sed 's/^/     /' "$I"

t=a_docker_build_would_send_the_folder
R2="$V/repo2"; mkdir -p "$R2" && git -C "$R2" init -q && echo "FROM scratch" > "$R2/Dockerfile" && echo "node_modules" > "$R2/.dockerignore"
w=$($VD init "$R2" 2>&1); echo ".video_demo_dir/" >> "$R2/.dockerignore"; w2=$($VD init "$R2" 2>&1)
check $t 'echo "$w" | grep -q "^WARNING Dockerfile exists, and .dockerignore does not exclude .video_demo_dir" && ! echo "$w2" | grep -q WARNING \
  && [ "$(cat "$R2/.dockerignore" | head -1)" = node_modules ]' || { echo "$w"; echo "$w2"; } | sed 's/^/     /'

t=an_old_video_folder_is_brought_in
O="$V/old-video"; mkdir -p "$O/src" "$O/chapters" "$O/work/clone"
echo 'TITLE = "Zops pilot"; OUTPUT_NAME = "zops-pilot"' > "$O/src/script.py"; : > "$O/zops-pilot.mp4"; echo secret > "$O/work/clone/.env"
R3="$V/repo3"; mkdir -p "$R3" && git -C "$R3" init -q
$VD init "$R3" --import "$O" >/dev/null 2>&1
check $t '[ -f "$R3/.video_demo_dir/videos/zops-pilot/v1/zops-pilot.mp4" ] && [ ! -e "$R3/.video_demo_dir/videos/zops-pilot/v1/work" ] \
  && grep -qF "| **zops-pilot**: Zops pilot | v1 (latest) |" "$R3/.video_demo_dir/INDEX.md" && grep -q "Brought in" "$R3/.video_demo_dir/INDEX.md"' \
  || cat "$R3/.video_demo_dir/INDEX.md" 2>/dev/null | sed 's/^/     /'

t=a_built_video_is_registered_by_the_engine
M="${KOKORO_MODELS:-$HOME/.cache/kokoro}"
if command -v uv >/dev/null && command -v ffmpeg >/dev/null && [ -s "$M/kokoro-v1.0.onnx" ]; then
  v=$($VD video "$R" card-demo | tail -1)
  cat > "$v/src/script.py" <<EOF
TITLE = "A card"; OUTPUT_NAME = "card"; WORKDIRS = {"main": "$R"}
CHAPTERS = [{"num": "00", "slug": "hello", "title": "Hello", "segments": [{"type": "card", "title": "Hello", "say": "Hello."}]}]
EOF
  log=$(cd "$v/src" && bash run.sh engine.py 2>&1)
  check $t '[ -s "$v/card.mp4" ] && grep -qF "| **card-demo**: A card | v1 (latest) |" "$D/INDEX.md" && [ -e "$D/run/record.lock" ]' \
    || { echo "$log" | tail -4; grep card "$D/INDEX.md"; } | sed 's/^/     /'
else
  echo "skip $t (needs uv, ffmpeg and the voice model)"; skip=$((skip+1))
fi
echo "$pass passed, $fail failed, $skip skipped"; [ "$fail" = 0 ]
