#!/usr/bin/env bash
# Scenarios of issue #17: a real browser scene of tests/fixtures/notes_app.py, recorded into a video.
# Skipped when uv, vhs, ffmpeg, the voice model or the Playwright browser are missing (CI).  usage: bash tests/browser.sh
set -uo pipefail
SKILL=$(cd "$(dirname "$0")/.." && pwd)
M="${KOKORO_MODELS:-$HOME/.cache/kokoro}"
for t in uv ffmpeg ffprobe; do command -v $t >/dev/null || { echo "skip browser tests (no $t)"; exit 0; }; done
[ -s "$M/kokoro-v1.0.onnx" ] || { echo "skip browser tests (no voice model in $M)"; exit 0; }
bash "$SKILL/scripts/run.sh" -c "from playwright.sync_api import sync_playwright as s
with s() as p: p.chromium.launch().close()" >/dev/null 2>&1 || { echo "skip browser tests (no Playwright browser: run scripts/setup.sh)"; exit 0; }

V=$(mktemp -d "${TMPDIR:-/tmp}/dv-br.XXXXXX"); PORT=$((20000 + RANDOM % 20000))
app() { python3 "$SKILL/tests/fixtures/notes_app.py" "$PORT" & APP=$!; sleep 1; }
trap 'kill $APP 2>/dev/null; wait $APP 2>/dev/null; rm -rf "$V"' EXIT
mkdir -p "$V/video/src" && cp "$SKILL"/scripts/{engine.py,browser.py,make_readme.py,run.sh} "$V/video/src/"
pass=0; fail=0
check() { if eval "$2"; then echo "ok   $1"; pass=$((pass+1)); else echo "FAIL $1"; fail=$((fail+1)); return 1; fi; }
script() { # $1 = steps (python list), $2 = narration
cat > "$V/video/src/script.py" <<EOF
WORKDIRS = {"main": "$V"}
OUTPUT_NAME = "notes-demo"
CHAPTERS = [{"num": "00", "slug": "save", "title": "Saving a note", "segments": [
  {"type": "browser", "caption": "Type a note, then \`Save\`", "say": "$2",
   "url": "http://127.0.0.1:$PORT/", "steps": $1}]}]
EOF
}
cd "$V/video/src"

t=a_dry_run_checks_every_step_without_recording
app; script '[{"type": "x", "into": "#text"}, {"click": "#nope"}]' "Short."
out=$(bash run.sh engine.py --dry 2>&1)
check $t 'echo "$out" | grep -q "FAIL  2. {\"click\": \"#nope\"}  at http://127.0.0.1:$PORT/" && [ ! -e "$V/video/chapters" ]' \
  || echo "$out" | tail -4 | sed 's/^/     /'
kill $APP; wait $APP 2>/dev/null

t=a_browser_scene_records_real_use
app; script '[{"type": "Ship the audit report", "into": "#text"}, {"click": "#save"}, {"expect": "Ship the audit report"}]' \
  "Type the note and press Save. It appears in the list right away, saved by the real app."
log=$(bash run.sh engine.py 2>&1)
notes=$(curl -s "http://127.0.0.1:$PORT/api/notes")
size=$(ffprobe -v error -select_streams v -show_entries stream=width,height -of csv=p=0 "$V/video/notes-demo.mp4" 2>/dev/null)
check $t 'echo "$notes" | grep -q "Ship the audit report" && [ "$size" = "1920,1080" ]' || echo "$log" | tail -5 | sed 's/^/     /'

t=the_picture_lasts_as_long_as_the_voice
vd=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$V/video/build/00/00/voice.wav" 2>/dev/null)
cd_=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$V/video/chapters/00-save.mp4" 2>/dev/null)
check $t 'python3 -c "import sys; sys.exit(0 if float(\"$cd_\") >= float(\"$vd\") else 1)"' || echo "     clip $cd_ < voice $vd"

[ -n "${KEEP:-}" ] && cp "$V/video/notes-demo.mp4" "$KEEP/" && echo "kept $KEEP/notes-demo.mp4"
echo "$pass passed, $fail failed"; [ "$fail" = 0 ]
