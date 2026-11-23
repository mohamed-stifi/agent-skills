#!/usr/bin/env bash
# Scenarios of issue #29: fail fast, a faithful dry run, detached recording, saved sign-ins, chapter markers.
# Needs uv (the engine's python env) and the Playwright browser; the recording checks also need vhs, ffmpeg
# and the voice model. Skipped without them.   usage: bash tests/failfast.sh
set -uo pipefail
SKILL=$(cd "$(dirname "$0")/.." && pwd)
pass=0; fail=0; skip=0
check() { if eval "$2"; then echo "ok   $1"; pass=$((pass+1)); else echo "FAIL $1"; fail=$((fail+1)); return 1; fi; }
T_DRY=(a_failure_inside_a_pipe_is_seen an_expected_failure_is_allowed a_failing_before_hook_stops_the_build
       a_service_killed_by_a_scene_is_caught a_dry_run_keeps_state_like_the_recording_does
       a_sign_in_is_saved_and_reused a_page_that_never_goes_quiet_still_opens chapter_markers_are_right_in_a_long_video
       the_time_is_estimated_before_recording)
T_REC=(a_failed_command_stops_the_recording_at_once a_detached_recording_survives_the_session_that_started_it
       only_one_recording_at_a_time)
ready=1; command -v uv >/dev/null && command -v ffmpeg >/dev/null || ready=0
[ $ready = 1 ] && { bash "$SKILL/scripts/run.sh" -c "from playwright.sync_api import sync_playwright as s
with s() as p: p.chromium.launch().close()" >/dev/null 2>&1 || ready=0; }
if [ $ready = 0 ]; then
  for t in "${T_DRY[@]}" "${T_REC[@]}"; do echo "skip $t (needs uv, ffmpeg and the Playwright browser)"; skip=$((skip+1)); done
  echo "$pass passed, $fail failed, $skip skipped"; [ "$fail" = 0 ]; exit
fi

V=$(mktemp -d "${TMPDIR:-/tmp}/dv-ff.XXXXXX"); P=$((20000 + RANDOM % 9000)); P2=$((P + 1)); P3=$((P + 2)); DEAD=$((P + 3))
FIX="$SKILL/tests/fixtures/notes_app.py"
python3 "$FIX" "$P" & APP=$!
cleanup() { kill $APP 2>/dev/null; [ -f "$V/app3.pid" ] && kill "$(cat "$V/app3.pid")" 2>/dev/null
            pkill -f "notes_app.py $P2" 2>/dev/null; wait $APP 2>/dev/null; rm -rf "$V"; }
trap cleanup EXIT
for _ in 1 2 3 4 5 6 7 8 9 10; do curl -s "http://127.0.0.1:$P/api/notes" >/dev/null 2>&1 && break; sleep 0.3; done
B="http://127.0.0.1:$P"
mkdir -p "$V/work" "$V/video/src" && cp "$SKILL"/scripts/{engine.py,browser.py,run.sh} "$V/video/src/"
cat > "$V/video/src/script.py" <<EOF
WORKDIRS = {"main": "$V/work"}
OUTPUT_NAME = "ff"
SERVICES = {"web2": {"check": "curl -sf http://127.0.0.1:$P2/api/notes"},
            "web3": {"check": "curl -sf http://127.0.0.1:$P3/api/notes"}}
DEAD = "curl -s http://127.0.0.1:$DEAD/x | jq ."
def term(*cmds, **kw): return {"type": "term", "caption": "c", "say": "A scene.", "cmds": list(cmds), **kw}
CHAPTERS = [
 {"num": "10", "slug": "fails", "title": "Fails", "segments": [term("echo one", DEAD, "echo three")]},
 {"num": "11", "slug": "after", "title": "After", "segments": [term("echo after")]},
 {"num": "20", "slug": "pipe", "title": "Pipe", "segments": [term("seq 100000 | head -1", DEAD)]},
 {"num": "21", "slug": "expected", "title": "Expected", "segments": [term({"cmd": DEAD, "fails": True}, "echo still-going")]},
 {"num": "22", "slug": "hook", "title": "Hook", "before": ["echo hook-said-no; exit 1"], "segments": [term("echo should-not-run")]},
 {"num": "23", "slug": "bare", "title": "Bare", "segments": [term("python3 $FIX $P2 > /dev/null 2>&1 &", "sleep 1.5"), term("echo next")]},
 {"num": "24", "slug": "nohup", "title": "Nohup", "segments": [
   term("nohup python3 $FIX $P3 > $V/app3.log 2>&1 &", "echo \$! > $V/app3.pid", "disown", "sleep 1.5"), term("echo next-ok")]},
 {"num": "25", "slug": "state", "title": "State", "segments": [term("mkdir -p sub", "cd sub", "pwd")]},
 {"num": "30", "slug": "who", "title": "Who", "segments": [
   {"type": "browser", "caption": "c", "say": "s", "url": "$B/whoami", "storage_state": "$V/state.json",
    "steps": [{"expect": "signed in as abc123"}]}]},
 {"num": "31", "slug": "live", "title": "Live", "segments": [
   {"type": "browser", "caption": "c", "say": "s", "url": "$B/live", "wait_until": "load", "steps": [{"expect": "live page"}]}]},
 {"num": "40", "slug": "detached", "title": "Detached", "segments": [term("sleep 3", "echo detached-done")]},
]
EOF
cd "$V/video/src"
dry() { bash run.sh engine.py --dry --only "$@" 2>&1 | grep -v Deprecat; }

t=a_failure_inside_a_pipe_is_seen; out=$(dry 20)
check $t 'echo "$out" | grep -q "^\$ seq 100000 | head -1   \[exit 141 | 0" && echo "$out" | grep -qF "STOPPED at chapter 20 scene 0: \`curl -s http://127.0.0.1:$DEAD/x | jq .\` exited 7 | 0"' \
  || echo "$out" | tail -8 | sed 's/^/     /'
t=an_expected_failure_is_allowed; out=$(dry 21)
check $t 'echo "$out" | grep -q "^    still-going$" && ! echo "$out" | grep -q STOPPED' || echo "$out" | tail -8 | sed 's/^/     /'
t=a_failing_before_hook_stops_the_build; out=$(dry 22)
check $t 'echo "$out" | grep -q "STOPPED at chapter 22, before-hook" && echo "$out" | grep -q hook-said-no && ! echo "$out" | grep -q should-not-run' \
  || echo "$out" | tail -8 | sed 's/^/     /'
t=a_service_killed_by_a_scene_is_caught; out=$(dry 23); ok24=$(dry 24)
check $t 'echo "$out" | grep -q "STOPPED at chapter 23 scene 0: the service \`web2\` stopped answering" && echo "$out" | grep -q "nohup <command>" \
  && ! echo "$out" | grep -q "^    next$" && echo "$ok24" | grep -q "^    next-ok$" && ! echo "$ok24" | grep -q STOPPED' \
  || { echo "$out" | tail -6 | sed 's/^/     /'; echo "$ok24" | tail -6 | sed 's/^/     /'; }
t=a_dry_run_keeps_state_like_the_recording_does; out=$(dry 25)
check $t 'echo "$out" | grep -qE "^    .*/work/sub$"' || echo "$out" | tail -6 | sed 's/^/     /'
t=the_time_is_estimated_before_recording
check $t 'echo "$out" | grep -qE "Recording these chapters will take about [0-9]+ min" && [ -s ../build/dry-times.json ]' || echo "$out" | tail -3 | sed 's/^/     /'

t=a_sign_in_is_saved_and_reused
login=$(bash run.sh browser.py login "$B/login" "$V/state.json" --until 'signed=1' --headless --minutes 1 2>&1)
mode=$(stat -f %Lp "$V/state.json" 2>/dev/null || stat -c %a "$V/state.json" 2>/dev/null)
who=$(dry 30)
sed 's/"storage_state": "[^"]*",//' script.py > script.nostate && cp script.py script.keep && cp script.nostate script.py
anon=$(dry 30); cp script.keep script.py
check $t '[ "$mode" = 600 ] && grep -q abc123 "$V/state.json" && echo "$who" | grep -q "ok    1. expect" && echo "$anon" | grep -q "FAIL  1"' \
  || { echo "$login" | tail -3; echo "mode=$mode"; echo "$who" | tail -4; echo "$anon" | tail -3; } | sed 's/^/     /'
t=a_page_that_never_goes_quiet_still_opens; s0=$(date +%s); out=$(dry 31); s1=$(date +%s)
check $t 'echo "$out" | grep -q "ok    1. expect" && [ $((s1 - s0)) -lt 25 ]' || { echo "$out" | tail -4; echo "took $((s1 - s0)) s"; } | sed 's/^/     /'

t=chapter_markers_are_right_in_a_long_video
mkdir -p "$V/video/chapters" "$V/video/build"
for n in 00 01; do ffmpeg -v error -y -f lavfi -i color=c=black:s=320x180:r=5 -f lavfi -i anullsrc=r=48000:cl=stereo -t 60 \
  -c:v libx264 -preset ultrafast -c:a aac "$V/video/chapters/$n-x.mp4"; done
marks=$(bash run.sh -c "
import sys, types; sys.path.insert(0, '.'); import engine
engine.SCRIPT = types.SimpleNamespace(OUTPUT_NAME='long', TITLE='t')
tl = [{'start': 0, 'end': 60, 'say': 'Hello there.', 'times': None}]
engine.assemble([{'file': f'{n}-x.mp4', 'num': n, 'title': 'T' + n, 'duration': 60.0, 'timeline': tl} for n in ('00', '01')])
" >/dev/null 2>&1; ffprobe -v error -show_chapters -of csv=p=0 "$V/video/long.mp4" | cut -d, -f4,6 | tr '\n' ' ')
check $t '[ "$marks" = "0.000000,60.000000 60.000000,120.000000 " ]' || echo "     markers: $marks"

M="${KOKORO_MODELS:-$HOME/.cache/kokoro}"
if command -v vhs >/dev/null && [ -s "$M/kokoro-v1.0.onnx" ]; then
  rm -rf ../chapters ../build
  t=a_failed_command_stops_the_recording_at_once
  out=$(bash run.sh engine.py --only 10 11 2>&1); rc=$?
  check $t '[ $rc != 0 ] && echo "$out" | grep -qF "STOPPED at chapter 10 scene 0: \`curl -s http://127.0.0.1:$DEAD/x | jq .\` exited 7 | 0" \
    && ! ls ../chapters/11-* >/dev/null 2>&1' || echo "$out" | tail -6 | sed 's/^/     /'

  t=a_detached_recording_survives_the_session_that_started_it
  set -m; ( bash run.sh engine.py --detach --only 40 >/dev/null 2>&1; sleep 120 ) & W=$!; set +m
  sleep 4; st1=$(bash run.sh engine.py --status 2>&1 | head -1)
  other=$(bash run.sh engine.py --dry --only 25 2>&1)
  kill -KILL -- -$W 2>/dev/null; wait $W 2>/dev/null
  for _ in $(seq 1 90); do st2=$(bash run.sh engine.py --status 2>&1 | head -1); case "$st2" in state=running*) sleep 2 ;; *) break ;; esac; done
  check $t 'echo "$st1" | grep -q "^state=running" && echo "$st2" | grep -q "^state=finished exit=0" && ls ../chapters/40-*.mp4 >/dev/null 2>&1' \
    || { echo "first: $st1"; echo "last: $st2"; tail -5 ../record.log; } | sed 's/^/     /'
  t=only_one_recording_at_a_time
  check $t 'echo "$other" | grep -q "Another recording or dry run is running here"' || echo "$other" | tail -3 | sed 's/^/     /'
else
  for t in "${T_REC[@]}"; do echo "skip $t (needs vhs and the voice model)"; skip=$((skip+1)); done
fi
echo "$pass passed, $fail failed, $skip skipped"; [ "$fail" = 0 ]
