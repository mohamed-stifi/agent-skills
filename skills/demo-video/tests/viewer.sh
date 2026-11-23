#!/usr/bin/env bash
# Scenarios of issue #27: only the viewer's commands on screen. The rules check runs anywhere; the rest needs uv
# (the engine's python env), and the typing checks also need vhs. Skipped without them.
# usage: bash tests/viewer.sh
set -uo pipefail
SKILL=$(cd "$(dirname "$0")/.." && pwd)
pass=0; fail=0; skip=0
check() { if eval "$2"; then echo "ok   $1"; pass=$((pass+1)); else echo "FAIL $1"; fail=$((fail+1)); return 1; fi; }

check the_rules_tell_the_agent_to_act_as_a_new_user \
  '(for w in "commands the viewer has" "never a new one" "the way a user would ask" "retries" "where the viewer is" "explain each new command"; do
      grep -q "$w" "$SKILL/SKILL.md" "$SKILL/references/video-types.md" || { echo "     missing: $w"; exit 1; }; done
    ! grep -rq "req\.py\|agent\.jq\|small script file" "$SKILL/SKILL.md" "$SKILL/references")'

if ! command -v uv >/dev/null; then
  for t in an_api_call_is_typed_as_curl a_call_whose_status_matters_shows_the_status_line \
           a_helper_is_refused_before_anything_is_recorded the_projects_own_commands_pass a_file_made_on_screen_is_allowed \
           any_command_can_be_typed_exactly the_prompt_shows_where_the_viewer_is; do
    echo "skip $t (needs uv)"; skip=$((skip+1)); done
  echo "$pass passed, $fail failed, $skip skipped"; [ "$fail" = 0 ]; exit
fi

V=$(mktemp -d "${TMPDIR:-/tmp}/dv-vw.XXXXXX"); PORT=$((20000 + RANDOM % 20000))
python3 "$SKILL/tests/fixtures/notes_app.py" "$PORT" & APP=$!
trap 'kill $APP 2>/dev/null; wait $APP 2>/dev/null; rm -rf "$V"' EXIT
for _ in 1 2 3 4 5 6 7 8 9 10; do curl -s "http://127.0.0.1:$PORT/api/notes" >/dev/null 2>&1 && break; sleep 0.3; done
B="http://127.0.0.1:$PORT"

# the clone: a tracked script, an installed (git-ignored) tool, and files git doesn't know
C="$V/clone"; mkdir -p "$C/scripts" "$C/node_modules/.bin"
printf '#!/bin/sh\necho hello from the project\n' > "$C/scripts/hello.sh"
printf '#!/bin/sh\necho installed tool\n' > "$C/node_modules/.bin/tool"
printf '#!/bin/sh\necho made on screen\n' > "$C/made.sh"
printf '#!/bin/sh\necho extra\n' > "$C/extra.sh"
chmod +x "$C/scripts/hello.sh" "$C/node_modules/.bin/tool" "$C/made.sh" "$C/extra.sh"
echo node_modules/ > "$C/.gitignore"
git -C "$C" init -q && git -C "$C" add .gitignore scripts && git -C "$C" -c user.name=t -c user.email=t@t commit -qm init
# the video folder, with a helper written for the recording on PATH
mkdir -p "$V/video/src" "$V/video/work/bin" && cp "$SKILL"/scripts/{engine.py,make_doc.py,run.sh} "$V/video/src/"
printf '#!/bin/sh\necho helper\n' > "$V/video/work/bin/ask-as"; chmod +x "$V/video/work/bin/ask-as"
echo '.' > "$V/video/src/pretty.jq"
cat > "$V/video/src/script.py" <<EOF
WORKDIRS = {"main": "$C"}
OUTPUT_NAME = "viewer"
ENV = {"PATH": "$V/video/work/bin:$C/node_modules/.bin:" + __import__("os").environ["PATH"]}
VIEWER_HAS = ["made.sh"]
CHAPTERS = [
 {"num": "01", "slug": "helpers", "title": "Helpers", "segments": [
   {"type": "term", "caption": "c", "say": "s", "setup": ["greet() { echo hi; }"],
    "cmds": ["ask-as amina.json 'is it up?'", "greet", "echo '{}' | jq -f $V/video/src/pretty.jq", "./extra.sh"]}]},
 {"num": "02", "slug": "own", "title": "Own", "segments": [
   {"type": "term", "caption": "c", "say": "s", "cmds": ["./scripts/hello.sh", "tool", "echo ok | grep ok", "./made.sh"]}]},
 {"num": "03", "slug": "api", "title": "API", "segments": [
   {"type": "api", "caption": "c", "say": "s", "base": "$B",
    "calls": [{"method": "POST", "path": "/api/notes", "json": {"text": "it's here"}, "show": ".id"},
              {"method": "POST", "path": "/api/notes", "json": {"text": ""}, "status": True}],
    "then": ["curl -s $B/api/notes | jq length"]}]},
]
EOF
cd "$V/video/src"
bad=$(bash run.sh engine.py --dry --only 01 2>&1); bad_rc=$?
own=$(bash run.sh engine.py --dry --only 02 2>&1); own_rc=$?
api=$(bash run.sh engine.py --dry --only 03 2>&1)
plain() { sed $'s/\033\\[[0-9;]*m//g'; }

POST="curl -s -X POST $B/api/notes -H 'Content-Type: application/json' -d '{\"text\": \"it'\\''s here\"}' | jq '.id'"
# (the doc uses the same curl_cmd; tests/explain.sh checks its lines end to end)
check an_api_call_is_typed_as_curl 'echo "$api" | grep -qF "\$ $POST" && echo "$api" | plain | grep -A1 -F "$POST" | tail -1 | grep -qE "^ +1$" \
  && grep -q "curl_cmd(seg\[\"base\"\], c)" "$SKILL/scripts/make_doc.py"' \
  || echo "$api" | head -12 | sed "s/^/     /"
check a_call_whose_status_matters_shows_the_status_line \
  'echo "$api" | grep -A1 -F "\$ curl -si -X POST" | tail -1 | grep -qE "^ +HTTP/1\.[01] 422" && echo "$api" | grep -q "text is required"' \
  || echo "$api" | sed "s/^/     /"
check a_helper_is_refused_before_anything_is_recorded \
  '[ "$bad_rc" != 0 ] && ! echo "$bad" | grep -q "^######## 01" && [ ! -d "$V/video/chapters" ] \
   && (for w in "\`ask-as\` is a file of the video folder, outside the clone" "\`greet\` is defined in the scene" \
               "reads $V/video/src/pretty.jq, a file of the video itself" "\`./extra.sh\` is a file added to the clone"; do
        echo "$bad" | grep -qF "$w" || { echo "     missing: $w"; exit 1; }; done)' \
  || echo "$bad" | sed "s/^/     /"
check the_projects_own_commands_pass '[ "$own_rc" = 0 ] && echo "$own" | grep -q "hello from the project" && echo "$own" | grep -q "installed tool"' \
  || echo "$own" | sed "s/^/     /"
check a_file_made_on_screen_is_allowed 'echo "$own" | grep -q "made on screen" && ! echo "$own" | grep -q made.sh.*is' \
  || echo "$own" | sed "s/^/     /"

if command -v vhs >/dev/null; then
  CMD="echo \"double\" 'single' '\`tick\`'"
  out=$(CMD="$CMD" bash run.sh -c "
import os, sys; sys.path.insert(0, '.'); import engine, script
from pathlib import Path
engine.SCRIPT = script
seg = {'type': 'term', 'cmds': [os.environ['CMD'], 'cd scripts', 'pwd']}
tape = engine.tape_for(seg, Path('$V/clip.webm')).replace('Output clip.webm', 'Output clip.txt')
Path('$V/t.tape').write_text(tape)" 2>&1 && cd "$V" && vhs t.tape >/dev/null 2>&1 && cat "$V/clip.txt")
  check any_command_can_be_typed_exactly 'echo "$out" | grep -qF "$ $CMD" && echo "$out" | grep -qxF "double single \`tick\`"' \
    || echo "$out" | tail -15 | sed "s/^/     /"
  check the_prompt_shows_where_the_viewer_is 'echo "$out" | grep -qF "clone \$ cd scripts" && echo "$out" | grep -qF "scripts \$ pwd"' \
    || echo "$out" | tail -15 | sed "s/^/     /"
else
  echo "skip any_command_can_be_typed_exactly (needs vhs)"; echo "skip the_prompt_shows_where_the_viewer_is (needs vhs)"; skip=$((skip+2))
fi
echo "$pass passed, $fail failed, $skip skipped"; [ "$fail" = 0 ]
