#!/usr/bin/env bash
# Scenarios of issue #18 (API calls typed as curl since #27), against tests/fixtures/notes_app.py. The dry-run
# checks need uv; the recorded scene also needs vhs, ffmpeg and the voice model. Skipped without them.
# usage: bash tests/api.sh
set -uo pipefail
SKILL=$(cd "$(dirname "$0")/.." && pwd)
pass=0; fail=0; skip=0
check() { if eval "$2"; then echo "ok   $1"; pass=$((pass+1)); else echo "FAIL $1"; fail=$((fail+1)); return 1; fi; }
plain() { sed $'s/\033\\[[0-9;]*m//g'; }
T=(an_api_call_is_shown_as_a_developer_sees_it an_error_response_is_readable the_effect_is_shown_not_claimed)
if ! command -v uv >/dev/null || ! command -v jq >/dev/null; then
  for t in "${T[@]}"; do echo "skip $t (needs uv and jq)"; skip=$((skip+1)); done
  echo "$pass passed, $fail failed, $skip skipped"; [ "$fail" = 0 ]; exit
fi

V=$(mktemp -d "${TMPDIR:-/tmp}/dv-api.XXXXXX"); PORT=$((20000 + RANDOM % 20000))
python3 "$SKILL/tests/fixtures/notes_app.py" "$PORT" & APP=$!
trap 'kill $APP 2>/dev/null; wait $APP 2>/dev/null; rm -rf "$V"' EXIT
for _ in 1 2 3 4 5 6 7 8 9 10; do curl -s "http://127.0.0.1:$PORT/api/notes" >/dev/null 2>&1 && break; sleep 0.3; done
B="http://127.0.0.1:$PORT"
mkdir -p "$V/video/src" && cp "$SKILL"/scripts/{engine.py,run.sh} "$V/video/src/"
cat > "$V/video/src/script.py" <<EOF
WORKDIRS = {"main": "$V"}
OUTPUT_NAME = "api-demo"
CHAPTERS = [{"num": "00", "slug": "audit", "title": "The audit log", "segments": [
  {"type": "api", "caption": "A new note lands in the audit log", "say": "We post a note, then read the audit log.",
   "base": "$B", "calls": [{"method": "POST", "path": "/api/notes", "json": {"text": "Ship the audit report"}},
                           {"method": "POST", "path": "/api/notes", "json": {"text": ""}, "status": True}],
   "then": ["curl -s $B/api/audit | jq '.[-1].event'"]}]}]
EOF
cd "$V/video/src"
dry=$(bash run.sh engine.py --dry 2>&1 | plain)

check an_api_call_is_shown_as_a_developer_sees_it \
  'echo "$dry" | grep -qF "\$ curl -s -X POST $B/api/notes -H '"'"'Content-Type: application/json'"'"' -d '"'"'{\"text\": \"Ship the audit report\"}'"'"' | jq" \
   && echo "$dry" | grep -qE "^ +\"id\": 1,?$"' || echo "$dry" | sed 's/^/     /'
check an_error_response_is_readable \
  'echo "$dry" | grep -A1 -F "\$ curl -si -X POST" | tail -1 | grep -qE "HTTP/1\.[01] 422" && echo "$dry" | grep -q "text is required"' \
  || echo "$dry" | sed 's/^/     /'

t=the_effect_is_shown_not_claimed
M="${KOKORO_MODELS:-$HOME/.cache/kokoro}"
if command -v vhs >/dev/null && [ -s "$M/kokoro-v1.0.onnx" ]; then
  log=$(bash run.sh engine.py 2>&1)
  check $t 'echo "$dry" | grep -A1 "api/audit" | grep -q "\"note.created\"" && [ -s "$V/video/api-demo.mp4" ]' \
    || { echo "$dry" | tail -8 | sed 's/^/     /'; echo "$log" | tail -3 | sed 's/^/     /'; }
else
  echo "skip $t (needs vhs and the voice model)"; skip=$((skip+1))
fi
[ -n "${KEEP:-}" ] && [ -s "$V/video/api-demo.mp4" ] && cp "$V/video/api-demo.mp4" "$KEEP/" && echo "kept $KEEP/api-demo.mp4"
echo "$pass passed, $fail failed, $skip skipped"; [ "$fail" = 0 ]
