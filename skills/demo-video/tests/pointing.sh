#!/usr/bin/env bash
# Scenarios of issue #25: zoom, callouts, the ✓ on expect, blur, numbered steps, section and concept cards, the
# script rules. The recipe check runs anywhere; the rest needs uv and the Playwright browser (skipped in CI).
# usage: bash tests/pointing.sh
set -uo pipefail
SKILL=$(cd "$(dirname "$0")/.." && pwd)
pass=0; fail=0; skip=0
check() { if eval "$2"; then echo "ok   $1"; pass=$((pass+1)); else echo "FAIL $1"; fail=$((fail+1)); return 1; fi; }

R="$SKILL/references/video-types.md"
check the_recipes_carry_the_script_rules \
  '(for w in "Number the steps aloud" "imperative with the exact label" "proof that it worked" "warning at the moment it applies" "Define each new term"; do grep -q "$w" "$R" || exit 1; done)'

ready=1; command -v uv >/dev/null && command -v ffmpeg >/dev/null || ready=0
[ $ready = 1 ] && { bash "$SKILL/scripts/run.sh" -c "from playwright.sync_api import sync_playwright as s
with s() as p: p.chromium.launch().close()" >/dev/null 2>&1 || ready=0; }
if [ $ready = 0 ]; then
  for t in zoom_makes_the_target_bigger_then_returns a_callout_appears_next_to_its_target a_passing_expect_shows_a_check_mark \
           a_blurred_secret_is_unreadable steps_are_numbered_across_the_video section_cards_and_concept_tiles_render; do
    echo "skip $t (needs uv, ffmpeg and the Playwright browser)"; skip=$((skip+1)); done
  echo "$pass passed, $fail failed, $skip skipped"; [ "$fail" = 0 ]; exit
fi

V=$(mktemp -d "${TMPDIR:-/tmp}/dv-pt.XXXXXX"); PORT=$((20000 + RANDOM % 20000))
python3 "$SKILL/tests/fixtures/notes_app.py" "$PORT" & APP=$!
trap 'kill $APP 2>/dev/null; wait $APP 2>/dev/null; rm -rf "$V"' EXIT
sleep 1
cat > "$V/scene.json" <<EOF
{"url": "http://127.0.0.1:$PORT/", "steps": [
 {"pause": 1},
 {"type": "sk-live-1234567890", "into": "#text"}, {"pause": 1},
 {"callout": "Never show a key", "icon": "⚠️", "tone": "warn", "at": "#text", "seconds": 2},
 {"blur": "#text"}, {"pause": 1.5},
 {"zoom": "#save", "scale": 2}, {"pause": 1}, {"click": "#save"},
 {"zoom": false}, {"pause": 1},
 {"expect": "sk-live-1234567890"}, {"pause": 1}]}
EOF
rec=$(bash "$SKILL/scripts/run.sh" "$SKILL/scripts/browser.py" record "$V/scene.json" "$V/clip.webm" 2>&1)
saved=$(curl -s "http://127.0.0.1:$PORT/api/notes")
# per frame (every 0.25 s): amber callout rim, green ✓ rim, orange Save button, contrast of the input field
stats=$(bash "$SKILL/scripts/run.sh" -c "
import json, subprocess, numpy as np
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', '$V/clip.webm', '-vf', 'fps=4', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                     capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, 900, 1920, 3).astype(int)
def near(f, c, tol=28): return int((np.abs(f - np.array(c)).max(axis=2) < tol).sum())
out = [dict(amber=near(f, (245, 159, 0)), green=near(f, (64, 192, 87)), orange=near(f, (232, 89, 12), 18),
            text=float(f[125:168, 530:1280].std())) for f in fr]
print(json.dumps(out))")
res=$(python3 - "$stats" <<'PY'
import json, statistics as st, sys
f = json.loads(sys.argv[1])
amb = [i for i, x in enumerate(f) if x["amber"] > 400]
amb = [i for k, i in enumerate(amb) if i == amb[0] + k]       # the callout's own run (the click ripple is amber too)
grn = [i for i, x in enumerate(f) if x["green"] > 400]
base = st.median(x["orange"] for x in f[:4]) or 1
zoomed = max(x["orange"] for x in f)
after_amber = [x["text"] for x in f[amb[-1] + 3: amb[-1] + 7]] if amb else []   # past the 0.3 s fade-out
r = {"callout": bool(amb) and f[0]["amber"] < 50 and f[-1]["amber"] < 50,
     "check": bool(grn) and bool(amb) and grn[0] > amb[-1] and f[0]["green"] < 50,
     "zoom": zoomed >= 3 * base and abs(f[-1]["orange"] - base) <= 0.3 * base,
     "blur": bool(after_amber) and st.median(after_amber) < 0.6 * f[amb[0]]["text"]}
print(" ".join(k for k, v in r.items() if v), "|", f"orange {base}->{zoomed}->{f[-1]['orange']}",
      f"text {f[amb[0]]['text'] if amb else '?'}->{after_amber[:1]}")
PY
)
echo "$rec" | grep -q '"ok": true' || echo "     recording: $rec"
check zoom_makes_the_target_bigger_then_returns 'echo "$res" | grep -q "zoom" && echo "$saved" | grep -q "sk-live-1234567890"' || echo "     $res"
check a_callout_appears_next_to_its_target 'echo "$res" | grep -q "callout"' || echo "     $res"
check a_passing_expect_shows_a_check_mark 'echo "$res" | grep -q "check"' || echo "     $res"
check a_blurred_secret_is_unreadable 'echo "$res" | grep -q "blur"' || echo "     $res"

out=$(cd "$SKILL/scripts" && bash run.sh -c "
import sys; sys.path.insert(0, '.'); import engine
from pathlib import Path
from PIL import Image
import numpy as np
chs = engine.number_steps([{'num': '01', 'title': 'a', 'segments': [{'step': '#Install'}, {'step': 'plain'}]},
                           {'num': '02', 'title': 'b', 'segments': [{'step': '#Connect'}, {'step': '#Test it'}]}])
print('|'.join(s['step'] for c in chs for s in c['segments']))
chap = {'num': '03', 'title': 'x'}
engine.picture_section({'title': 'Install the gateway', 'icon': '⬇'}, chap, Path('$V/section.png'))
engine.picture_concept({'join': '+', 'tiles': [{'icon': '⚙', 'title': 'A', 'sub': 'a'}, {'icon': '⚡', 'title': 'B', 'sub': 'b'}]},
                       chap, Path('$V/concept.png'))
s, c = (np.asarray(Image.open('$V/' + n).convert('RGB')).astype(int) for n in ('section.png', 'concept.png'))
amber = int((np.abs(s - np.array((245, 165, 36))).max(axis=2) < 30).sum())
panel = int((np.abs(c - np.array((16, 22, 42))).max(axis=2) < 6).sum())
print(s.shape[:2], amber > 2000, panel > 2 * 520 * 400 * 0.6)" 2>&1 | grep -v Deprecat)
check steps_are_numbered_across_the_video 'echo "$out" | grep -qF "Step 1 of 3 · Install|plain|Step 2 of 3 · Connect|Step 3 of 3 · Test it"' || echo "     $out"
check section_cards_and_concept_tiles_render 'echo "$out" | grep -qF "(1080, 1920) True True"' || echo "     $out"

echo "$pass passed, $fail failed, $skip skipped"; [ "$fail" = 0 ]
