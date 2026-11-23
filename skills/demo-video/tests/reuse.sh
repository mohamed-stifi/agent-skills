#!/usr/bin/env bash
# Scenarios of issue #32: reuse recorded scenes when nothing they show has changed. Needs uv, vhs, ffmpeg and the
# voice model (each build records small terminal scenes). Skipped without them.   usage: bash tests/reuse.sh
set -uo pipefail
SKILL=$(cd "$(dirname "$0")/.." && pwd)
pass=0; fail=0; skip=0
check() { if eval "$2"; then echo "ok   $1"; pass=$((pass+1)); else echo "FAIL $1"; fail=$((fail+1)); return 1; fi; }
T=(a_narration_change_runs_nothing_live a_change_in_covered_code_re_records_its_chapter
   a_re_recorded_chapter_re_records_the_ones_that_depend_on_it changed_screen_text_flags_the_narration
   two_features_combined_reuse_their_chapters the_clip_cache_stays_bounded)
M="${KOKORO_MODELS:-$HOME/.cache/kokoro}"
if ! command -v uv >/dev/null || ! command -v vhs >/dev/null || ! command -v ffmpeg >/dev/null || [ ! -s "$M/kokoro-v1.0.onnx" ]; then
  for t in "${T[@]}"; do echo "skip $t (needs uv, vhs, ffmpeg and the voice model)"; skip=$((skip+1)); done
  echo "$pass passed, $fail failed, $skip skipped"; [ "$fail" = 0 ]; exit
fi
V=$(mktemp -d "${TMPDIR:-/tmp}/dv-re.XXXXXX"); V=$(cd "$V" && pwd -P); trap 'rm -rf "$V"' EXIT
VD="python3 $SKILL/scripts/vdir.py"
R="$V/repo"; mkdir -p "$R" && git -C "$R" init -q && $VD init "$R" >/dev/null
A="$R/.video_demo_dir/work/app"; mkdir -p "$A/api" "$A/web"
echo "api v1" > "$A/api/app.txt"; echo "web v1" > "$A/web/page.txt"; echo "readme" > "$A/README.txt"
git -C "$A" init -q && git -C "$A" add . && git -C "$A" -c user.name=t -c user.email=t@t commit -qm init
head() { cat <<EOF
WORKDIRS = {"main": "$A"}
OUTPUT_NAME = "$1"
def term(say, *cmds): return {"type": "term", "caption": "c", "say": say, "cmds": list(cmds)}
EOF
}
CH00='{"num": "00", "slug": "api", "title": "The API", "fresh": True, "covers": ["api/"], "segments": [term(SAY00, "cat api/app.txt")]}'
CH01='{"num": "01", "slug": "web", "title": "The page", "covers": ["web/"], "segments": [term("The page.", "cat web/page.txt")]}'
CH02='{"num": "02", "slug": "two", "title": "Two", "fresh": True, "covers": ["web/"], "segments": [term("Two.", "echo two")]}'
v=$($VD video "$R" first | tail -1)
write() { { head first; echo "SAY00 = \"$1\""; echo "CHAPTERS = [$CH00, $CH01, $CH02]"; } > "$v/src/script.py"; }
write "The API answers."
cd "$v/src"
b0=$(bash run.sh engine.py 2>&1)
live0=$(echo "$b0" | grep -c "live: recording now")

t=a_narration_change_runs_nothing_live
write "The API answers, as you can see."
p1=$(bash run.sh engine.py --plan 2>&1); b1=$(bash run.sh engine.py 2>&1)
check $t '[ "$live0" = 3 ] && echo "$p1" | grep -q "^00 The API: re-voice and re-frame only" && echo "$p1" | grep -q "^01 The page: reuse" \
  && ! echo "$b1" | grep -q "live: recording now" && echo "$b1" | grep -q "reused recording"' \
  || { echo "first build live: $live0"; echo "$p1"; echo "$b1" | tail -5; } | sed 's/^/     /'

t=a_change_in_covered_code_re_records_its_chapter
echo "outside" >> "$A/README.txt"; pout=$(bash run.sh engine.py --plan 2>&1)
echo "api v2" > "$A/api/app.txt"; pin=$(bash run.sh engine.py --plan 2>&1)
check $t 'echo "$pout" | grep -q "^00 The API: reuse" && echo "$pin" | grep -q "^00 The API: RECORD AGAIN" \
  && echo "$pin" | grep -q "scene 0: code it covers changed: api/app.txt"' || { echo "$pout"; echo "$pin"; } | sed 's/^/     /'

t=a_re_recorded_chapter_re_records_the_ones_that_depend_on_it
check $t 'echo "$pin" | grep -q "^01 The page: RECORD AGAIN" && echo "$pin" | grep -q "it follows a scene that is recorded again" \
  && echo "$pin" | grep -q "^02 Two: reuse"' || echo "$pin" | sed 's/^/     /'

t=changed_screen_text_flags_the_narration
b2=$(bash run.sh engine.py 2>&1); p2=$(bash run.sh engine.py --plan 2>&1)
check $t 'echo "$b2" | grep -q "CHECK NARRATION: chapter 00 scene 0" && echo "$p2" | grep -q "CHECK NARRATION: scene 0" \
  && [ "$(echo "$b2" | grep -c "live: recording now")" = 2 ]' || { echo "$b2" | grep -E "live|reused|CHECK|^>" ; echo "$p2"; } | sed 's/^/     /'

t=two_features_combined_reuse_their_chapters
w=$($VD video "$R" combo | tail -1)
CH03='{"num": "03", "slug": "new", "title": "New", "fresh": True, "segments": [term("New.", "echo combined")]}'
{ head combo; echo "SAY00 = 'x'"; echo "CHAPTERS = [$CH02, $CH03]"; } > "$w/src/script.py"
bc=$(cd "$w/src" && bash run.sh engine.py 2>&1)
check $t '[ "$(echo "$bc" | grep -c "live: recording now")" = 1 ] && [ "$(echo "$bc" | grep -c "reused recording")" = 1 ] && [ -s "$w/combo.mp4" ]' \
  || echo "$bc" | grep -E "live|reused|^>|STOP|Error" | sed 's/^/     /'

t=the_clip_cache_stays_bounded
n0=$(ls "$R/.video_demo_dir/clips" | wc -l | tr -d ' '); g=$(bash run.sh engine.py --gc 2>&1); n1=$(ls "$R/.video_demo_dir/clips" | wc -l | tr -d ' ')
b3=$(bash run.sh engine.py 2>&1)
check $t '[ "$n0" = 6 ] && [ "$n1" = 4 ] && ! echo "$b3" | grep -q "live: recording now"' || { echo "before $n0 after $n1: $g"; echo "$b3" | tail -3; } | sed 's/^/     /'
echo "$pass passed, $fail failed, $skip skipped"; [ "$fail" = 0 ]
