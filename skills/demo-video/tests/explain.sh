#!/usr/bin/env bash
# Scenarios of issue #19: diagrams in time with the narration, the companion doc, the video-type recipes.
# The recipe check runs anywhere; the built video needs uv, vhs, ffmpeg, the voice model and the Playwright
# browser, and is skipped without them.  usage: bash tests/explain.sh
set -uo pipefail
SKILL=$(cd "$(dirname "$0")/.." && pwd)
pass=0; fail=0; skip=0
check() { if eval "$2"; then echo "ok   $1"; pass=$((pass+1)); else echo "FAIL $1"; fail=$((fail+1)); return 1; fi; }

R="$SKILL/references/video-types.md"
check a_recipe_shapes_each_type \
  '(for h in "## Feature demo" "## Tutorial" "## How it works (explainer)" "## Pilot (test record)" "## Project guide"; do grep -qxF "$h" "$R" || exit 1; done
    sed -n "/^## Tutorial/,/^## How/p" "$R" > /tmp/.dv-tut.$$; for w in Prerequisites "Install and configure" "One task per chapter" Troubleshooting; do grep -q "$w" /tmp/.dv-tut.$$ || exit 1; done
    rm -f /tmp/.dv-tut.$$; grep -q "references/video-types.md" "$SKILL/SKILL.md")'

M="${KOKORO_MODELS:-$HOME/.cache/kokoro}"
ready=1
for t in uv vhs ffmpeg ffprobe; do command -v $t >/dev/null || ready=0; done
[ -s "$M/kokoro-v1.0.onnx" ] || ready=0
[ $ready = 1 ] && { bash "$SKILL/scripts/run.sh" -c "from playwright.sync_api import sync_playwright as s
with s() as p: p.chromium.launch().close()" >/dev/null 2>&1 || ready=0; }
if [ $ready = 0 ]; then
  echo "skip the_diagram_follows_the_narration (needs uv, vhs, ffmpeg, the voice model and the browser)"
  echo "skip the_doc_can_be_followed_without_the_video (same)"; skip=2
  echo "$pass passed, $fail failed, $skip skipped"; [ "$fail" = 0 ]; exit
fi

V=$(mktemp -d "${TMPDIR:-/tmp}/dv-ex.XXXXXX"); PORT=$((20000 + RANDOM % 20000))
python3 "$SKILL/tests/fixtures/notes_app.py" "$PORT" & APP=$!
trap 'kill $APP 2>/dev/null; wait $APP 2>/dev/null; rm -rf "$V"' EXIT
mkdir -p "$V/video/src" && cp "$SKILL"/scripts/{engine.py,browser.py,req.py,make_doc.py,make_readme.py,run.sh} "$V/video/src/"
B="http://127.0.0.1:$PORT"
cat > "$V/video/src/script.py" <<EOF
WORKDIRS = {"main": "$V"}
TITLE = "Notes: how a note is saved"; OUTPUT_NAME = "notes-guide"
CHAPTERS = [
 {"num": "00", "slug": "flow", "title": "The flow", "segments": [
   {"type": "diagram", "title": "How a note is saved",
    "say": "First, the page sends the note. Next, the API checks it and stores it. Last, the audit log records the change.",
    "boxes": [{"title": "Page", "body": ["\`index.html\`"]}, {"title": "API", "body": ["\`POST /api/notes\`"]},
              {"title": "Audit log", "body": ["\`audit\` table"]}]}]},
 {"num": "01", "slug": "start", "title": "Start it", "segments": [
   {"type": "term", "caption": "Check the service is up", "say": "Check that the service answers.",
    "cmds": ["echo service up on $PORT"]}]},
 {"num": "02", "slug": "api", "title": "The API", "segments": [
   {"type": "api", "caption": "Create a note", "say": "Post a note.", "base": "$B",
    "calls": [{"method": "POST", "path": "/api/notes", "json": {"text": "From the API"}}],
    "then": ["req GET /api/audit --show 'length'"]}]},
 {"num": "03", "slug": "page", "title": "The page", "segments": [
   {"type": "browser", "caption": "Save a note from the page", "say": "Type a note and save it.", "url": "$B/",
    "steps": [{"type": "From the page", "into": "#text"}, {"click": "#save"}, {"expect": "From the page"}]}]},
]
EOF
cd "$V/video/src"
log=$(bash run.sh engine.py 2>&1) || echo "$log" | tail -5
doc=$(bash run.sh make_doc.py 2>&1)

t=the_diagram_follows_the_narration
res=$(bash run.sh -c "
import json, subprocess
from pathlib import Path
from PIL import Image, ImageChops, ImageStat
b = Path('$V/video/build/00')
times = json.loads((b / 'meta.json').read_text())['timeline'][0]['times']
pics = [Image.open(b / '00' / f'lit-{k}.png').convert('RGB') for k in range(3)]
best = []
for k, (a, e) in enumerate(times):
    f = b / f'mid-{k}.png'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{(a + e) / 2:.2f}', '-i', str(b / '00.mp4'), '-frames:v', '1', str(f)], check=True)
    fr = Image.open(f).convert('RGB')
    d = [sum(ImageStat.Stat(ImageChops.difference(fr, p)).mean) for p in pics]
    best.append(d.index(min(d)))
print(len(times), best)" 2>&1)
check $t '[ "$res" = "3 [0, 1, 2]" ]' || echo "     $res"

t=the_doc_can_be_followed_without_the_video
D="$V/video/notes-guide.md"
check $t '[ -s "$D" ] && grep -n "^## " "$D" | cut -d: -f2- | tr "\n" "|" | grep -q "^## 00 The flow (00:00)|## 01 Start it (00:[0-9][0-9])|## 02 The API (00:[0-9][0-9])|## 03 The page (00:[0-9][0-9])|$" \
  && grep -q "^echo service up on $PORT$" "$D" \
  && grep -qF "curl -s -X POST $B/api/notes -H '"'"'Content-Type: application/json'"'"' -d '"'"'{\"text\": \"From the API\"}'"'"'" "$D" \
  && grep -qF "curl -s -X GET $B/api/audit | jq '"'"'length'"'"'" "$D" && ! grep -q "^req " "$D" \
  && grep -q "^2\. Type “From the page” into \`#text\`\.$" "$D" \
  && [ "$(grep -c "^!\[.*\](doc/0[0-3]-00.png)$" "$D")" = 4 ] && [ "$(ls "$V/video/doc" | wc -l | tr -d " ")" = 4 ]' \
  || { echo "$doc" | tail -5 | sed 's/^/     /'; grep -n "^## \|curl\|^[0-9]\.\|!\[\|^echo" "$D" 2>/dev/null | head -20 | sed 's/^/     /'; }

[ -n "${KEEP:-}" ] && cp -R "$V/video/notes-guide.mp4" "$V/video/notes-guide.md" "$V/video/doc" "$KEEP/" 2>/dev/null && echo "kept in $KEEP"
echo "$pass passed, $fail failed, $skip skipped"; [ "$fail" = 0 ]
