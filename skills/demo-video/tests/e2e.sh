#!/usr/bin/env bash
# End to end: build a real two-chapter video of a tiny repo (a card, then a terminal scene) and check the MP4.
# Skipped when vhs, uv, ffmpeg or the voice model are missing (CI). Takes about a minute.  usage: bash tests/e2e.sh
set -uo pipefail
SKILL=$(cd "$(dirname "$0")/.." && pwd)
M="${KOKORO_MODELS:-$HOME/.cache/kokoro}"
for t in vhs uv ffmpeg ffprobe git; do command -v $t >/dev/null || { echo "skip e2e (no $t)"; exit 0; }; done
[ -s "$M/kokoro-v1.0.onnx" ] || { echo "skip e2e (no voice model in $M)"; exit 0; }
V=$(mktemp -d "${TMPDIR:-/tmp}/dv-e2e.XXXXXX"); trap 'rm -rf "$V"' EXIT

# a tiny repo with one CLI, cloned into work/ the way the skill does it
mkdir -p "$V/origin" && cd "$V/origin" && git init -q && cat > greet.sh <<'EOF'
#!/usr/bin/env bash
echo "Hello, ${1:-world}!"
EOF
chmod +x greet.sh && git add . && git -c user.email=t@t -c user.name=t commit -qm init
mkdir -p "$V/video/src" "$V/video/work" && git clone -q "$V/origin" "$V/video/work/greet"
cp "$SKILL"/scripts/{engine.py,make_readme.py,run.sh} "$V/video/src/"
cat > "$V/video/src/script.py" <<EOF
WORKDIRS = {"main": "$V/video/work/greet"}
TITLE = "greet: a demo"; OUTPUT_NAME = "greet-demo"; PROMPT = "greet"
CHAPTERS = [
 {"num": "00", "slug": "intro", "title": "Welcome", "segments": [
   {"type": "card", "kicker": "greet", "title": "Saying hello", "subtitle": "One command, one greeting.",
    "say": "This is greet. It says hello."}]},
 {"num": "01", "slug": "use", "title": "Using it", "segments": [
   {"type": "term", "caption": "Pass a name to \`greet.sh\`", "say": "Run it with a name. It greets that name.",
    "cmds": ["./greet.sh team"]}]},
]
EOF
cd "$V/video/src"
pass=0; fail=0
check() { if eval "$2"; then echo "ok   $1"; pass=$((pass+1)); else echo "FAIL $1"; fail=$((fail+1)); fi; }
dry=$(bash run.sh engine.py --dry 2>&1)
check dry_run_runs_the_command_for_real 'echo "$dry" | grep -q "Hello, team!"'
log=$(bash run.sh engine.py 2>&1); bash run.sh make_readme.py >/dev/null 2>&1
mp4="$V/video/greet-demo.mp4"
streams=$(ffprobe -v error -show_entries stream=codec_name,width,height -of csv=p=0 "$mp4" 2>/dev/null | tr '\n' ' ')
check the_video_has_picture_voice_and_subtitles 'echo "$streams" | grep -q "h264,1920,1080" && echo "$streams" | grep -q "aac" && echo "$streams" | grep -q "mov_text"' \
  || echo "$log" | tail -5 | sed 's/^/     /'
check one_chapter_marker_per_chapter '[ "$(ffprobe -v error -show_chapters -of csv=p=0 "$mp4" 2>/dev/null | wc -l | tr -d " ")" = 2 ]'
check subtitles_follow_the_narration 'grep -q "It greets that name." "$V/video/greet-demo.srt"'
check the_readme_indexes_the_chapters 'grep -q "01-use.mp4" "$V/video/README.md"'
echo "$pass passed, $fail failed"; [ "$fail" = 0 ]
