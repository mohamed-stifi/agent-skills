#!/usr/bin/env bash
# Scenarios of issue #18, against tests/fixtures/notes_app.py. The `req` checks need only python3 (they run in
# CI); the recorded scene needs uv, vhs, ffmpeg and the voice model, and is skipped without them.
# usage: bash tests/api.sh
set -uo pipefail
SKILL=$(cd "$(dirname "$0")/.." && pwd)
V=$(mktemp -d "${TMPDIR:-/tmp}/dv-api.XXXXXX"); PORT=$((20000 + RANDOM % 20000))
python3 "$SKILL/tests/fixtures/notes_app.py" "$PORT" & APP=$!
trap 'kill $APP 2>/dev/null; wait $APP 2>/dev/null; rm -rf "$V"' EXIT
for _ in 1 2 3 4 5 6 7 8 9 10; do curl -s "http://127.0.0.1:$PORT/api/notes" >/dev/null 2>&1 && break; sleep 0.3; done
export REQ_BASE="http://127.0.0.1:$PORT"
req() { python3 "$SKILL/scripts/req.py" "$@"; }
pass=0; fail=0; skip=0
check() { if eval "$2"; then echo "ok   $1"; pass=$((pass+1)); else echo "FAIL $1"; fail=$((fail+1)); return 1; fi; }
plain() { sed $'s/\033\\[[0-9;]*m//g'; }

t=an_api_call_is_shown_as_a_developer_sees_it
out=$(req POST /api/notes -d '{"text": "Ship the audit report"}' | plain)
check $t 'echo "$out" | grep -q "^→ POST /api/notes$" && echo "$out" | grep -q "{\"text\": \"Ship the audit report\"}" && echo "$out" | grep -qE "^← 201 Created · [0-9]+ ms$" && echo "$out" | grep -q "\"id\": 1"' \
  || echo "$out" | sed 's/^/     /'

t=an_error_response_is_readable
raw=$(req POST /api/notes -d '{"text": ""}')
check $t 'echo "$raw" | grep -q $'"'"'\033\[1;31m← 422'"'"' && echo "$raw" | plain | grep -q "text is required"' \
  || echo "$raw" | plain | sed 's/^/     /'

t=the_effect_is_shown_not_claimed
M="${KOKORO_MODELS:-$HOME/.cache/kokoro}"
if command -v uv >/dev/null && command -v vhs >/dev/null && [ -s "$M/kokoro-v1.0.onnx" ]; then
  mkdir -p "$V/video/src" && cp "$SKILL"/scripts/{engine.py,req.py,run.sh} "$V/video/src/"
  cat > "$V/video/src/script.py" <<EOF
WORKDIRS = {"main": "$V"}
OUTPUT_NAME = "api-demo"
CHAPTERS = [{"num": "00", "slug": "audit", "title": "The audit log", "segments": [
  {"type": "api", "caption": "A new note lands in the audit log", "say": "We post a note, then read the audit log.",
   "base": "$REQ_BASE", "calls": [{"method": "POST", "path": "/api/notes", "json": {"text": "Second note"}}],
   "then": ["req GET /api/audit --show '.[-1].event'"]}]}]
EOF
  cd "$V/video/src"
  dry=$(bash run.sh engine.py --dry 2>&1 | plain)
  log=$(bash run.sh engine.py 2>&1)
  check $t 'echo "$dry" | grep -q "← 201 Created" && echo "$dry" | grep -A3 "api/audit" | grep -q "\"note.created\"" && [ -s "$V/video/api-demo.mp4" ]' \
    || { echo "$dry" | tail -8 | sed 's/^/     /'; echo "$log" | tail -3 | sed 's/^/     /'; }
else
  echo "skip $t (needs uv, vhs and the voice model)"; skip=$((skip+1))
fi
[ -n "${KEEP:-}" ] && [ -s "$V/video/api-demo.mp4" ] && cp "$V/video/api-demo.mp4" "$KEEP/" && echo "kept $KEEP/api-demo.mp4"
echo "$pass passed, $fail failed, $skip skipped"; [ "$fail" = 0 ]
