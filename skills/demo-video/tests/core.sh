#!/usr/bin/env bash
# Scenarios of issue #16. Checks that need the voice model, uv or vhs are skipped when those are missing (CI).
# usage: bash tests/core.sh
set -uo pipefail
SKILL=$(cd "$(dirname "$0")/.." && pwd); REPO=$(cd "$SKILL/../.." && pwd)
T=$(mktemp -d "${TMPDIR:-/tmp}/dv-core.XXXXXX"); trap 'rm -rf "$T"' EXIT
pass=0; fail=0; skip=0
check() { if eval "$2"; then echo "ok   $1"; pass=$((pass+1)); else echo "FAIL $1"; fail=$((fail+1)); return 1; fi; }
skipped() { echo "skip $1 ($2)"; skip=$((skip+1)); }
S="$SKILL/SKILL.md"
section() { sed -n "/^## $1/,/^## [0-9A-Z]/p" "$S"; }

check the_request_picks_the_subject_type_and_audience \
  '(sec=$(section "1. Read the request"); for w in "**Subject:**" "**Video type:**" "**Audience:**" "feature demo" "tutorial" "explainer" "pilot" "project guide" "Length follows the content"; do echo "$sec" | grep -qF -- "$w" || exit 1; done)'
check a_large_subject_starts_with_the_feature_map \
  'section "2. Map the repo" | tr "\n" " " | tr -s " " | grep -q "wait for the user.s go before recording"'
check hands_on_needs_are_asked_first_in_the_chat \
  'sec=$(section "3. Ask for the hands-on needs"); echo "$sec" | grep -q "before you try anything" && echo "$sec" | grep -q "Never invent a secret"'

t=the_voice_is_a_neural_voice
M="${KOKORO_MODELS:-$HOME/.cache/kokoro}"
if command -v uv >/dev/null && [ -s "$M/kokoro-v1.0.onnx" ] && command -v ffprobe >/dev/null; then
  out=$(cd "$SKILL/scripts" && bash run.sh -c "
import sys; sys.path.insert(0, '.'); import engine
from pathlib import Path
assert engine.VOICE_ENGINE == 'kokoro', engine.VOICE_ENGINE
d, times = engine.voice('First sentence here. And a second one.', Path('$T/v.wav'))
print(len(times), d > 1)" 2>&1)
  fmt=$(ffprobe -v error -show_entries stream=sample_rate,channels -of csv=p=0 "$T/v.wav" 2>/dev/null)
  check $t '[ "$out" = "2 True" ] && [ "$fmt" = "48000,2" ]' || echo "     $out $fmt"
else
  skipped $t "needs uv, ffprobe and the Kokoro model in $M"
fi

t=the_old_name_still_installs
mkdir -p "$T/agent"; ln -s "$REPO/skills/repo-walkthrough-video" "$T/agent/repo-walkthrough-video"
ln -s "/elsewhere/not-ours" "$T/agent/someone-elses-link"
out=$(bash "$REPO/scripts/install.sh" demo-video --dir "$T/agent" 2>&1)
check $t '[ ! -L "$T/agent/repo-walkthrough-video" ] && [ -L "$T/agent/demo-video" ] && [ -L "$T/agent/someone-elses-link" ]' \
  || echo "$out" | sed 's/^/     /'

echo "$pass passed, $fail failed, $skip skipped"; [ "$fail" = 0 ]
