#!/usr/bin/env bash
# Scenarios of issue #31: cleanup removes only what the video owns, puts back what it found, saves checkpoints.
# Needs Docker (with a local image: busybox, alpine or postgres:16; else it pulls busybox) and python3; the
# compose-name check also needs uv. Skipped without Docker.   usage: bash tests/cleanup.sh
set -uo pipefail
SKILL=$(cd "$(dirname "$0")/.." && pwd)
pass=0; fail=0; skip=0
check() { if eval "$2"; then echo "ok   $1"; pass=$((pass+1)); else echo "FAIL $1"; fail=$((fail+1)); return 1; fi; }
T=(compose_projects_get_the_videos_own_names cleanup_removes_only_what_the_video_owns a_stack_that_was_stopped_stays_stopped
   a_checkpoint_is_saved_and_restored a_checkpoint_over_the_size_limit_is_skipped index_says_nothing_is_left_running)
if ! docker info >/dev/null 2>&1; then
  for t in "${T[@]}"; do echo "skip $t (needs Docker)"; skip=$((skip+1)); done
  echo "$pass passed, $fail failed, $skip skipped"; [ "$fail" = 0 ]; exit
fi
IMG=$(docker images --format '{{.Repository}}:{{.Tag}}' | grep -E '^(busybox|alpine):|^postgres:16$' | head -1)
[ -n "$IMG" ] || { docker pull -q busybox >/dev/null && IMG=busybox; }
V=$(mktemp -d "${TMPDIR:-/tmp}/dv-cl.XXXXXX"); V=$(cd "$V" && pwd -P); RID=$RANDOM
LG="python3 $SKILL/scripts/ledger.py"; VD="python3 $SKILL/scripts/vdir.py"
R="$V/repo"; mkdir -p "$R" && git -C "$R" init -q && $VD init "$R" >/dev/null
D="$R/.video_demo_dir"; APP="$D/work/app"; FOUND="$V/found"; mkdir -p "$APP" "$FOUND"
cat > "$APP/compose.yaml" <<EOF
services:
  db: {image: "$IMG", entrypoint: ["sleep", "3600"], volumes: ["data:/data"]}
volumes: {data: {}}
EOF
cat > "$FOUND/compose.yaml" <<EOF
name: dvtest-found-$RID
services:
  svc: {image: "$IMG", entrypoint: ["sleep", "3600"], volumes: ["keep:/keep"]}
  extra: {image: "$IMG", entrypoint: ["sleep", "3600"]}
volumes: {keep: {}}
EOF
fin() { docker rm -f "dvtest-user-$RID" >/dev/null 2>&1; (cd "$FOUND" && docker compose down -v >/dev/null 2>&1)
        (cd "$APP" && COMPOSE_PROJECT_NAME=dv-app docker compose down -v >/dev/null 2>&1); docker volume rm -f dv-app_data >/dev/null 2>&1
        pkill -f "sleep 30$RID" 2>/dev/null; rm -rf "$V"; }
trap fin EXIT
(cd "$FOUND" && docker compose up -d svc >/dev/null 2>&1 && docker compose stop >/dev/null 2>&1)   # found: created, stopped

t=compose_projects_get_the_videos_own_names
if command -v uv >/dev/null; then
  v=$($VD video "$R" app | tail -1)
  cat > "$v/src/script.py" <<EOF
WORKDIRS = {"main": "$APP", "found": "$FOUND"}
CHAPTERS = [{"num": "00", "slug": "up", "title": "Up", "segments": [
  {"type": "term", "caption": "c", "say": "s", "cmds": ["docker compose up -d 2>&1 | tail -1"]}]}]
EOF
  out=$(cd "$v/src" && bash run.sh engine.py --dry 2>&1)
  check $t '[ -n "$(docker ps -q --filter label=com.docker.compose.project=dv-app)" ] && grep -q "\"snapshot\"" "$D/state.json" \
    && grep -qF "$FOUND" "$D/state.json"' || echo "$out" | tail -5 | sed 's/^/     /'
else
  echo "skip $t (needs uv)"; skip=$((skip+1))
  $VD init "$R" >/dev/null; python3 -c "import sys; sys.path.insert(0,'$SKILL/scripts'); import vdir; vdir.add_workdirs(vdir.find('$R'), ['$APP','$FOUND'])"
  $LG snapshot "$R" >/dev/null; (cd "$APP" && COMPOSE_PROJECT_NAME=dv-app docker compose up -d >/dev/null 2>&1)
fi

# what happens during the run: data in the owned volume, the found stack started (and one more service), a
# process in the clone, and a container the user starts meanwhile
docker exec "$(docker ps -q --filter label=com.docker.compose.project=dv-app | head -1)" sh -c 'echo 42 rows > /data/rows.txt'
(cd "$FOUND" && docker compose start svc >/dev/null 2>&1 && docker compose up -d extra >/dev/null 2>&1)
(cd "$APP" && nohup sleep 30$RID >/dev/null 2>&1 &)
docker run -d --name "dvtest-user-$RID" --entrypoint sleep "$IMG" 3600 >/dev/null
sleep 1
out=$($LG cleanup "$R" 2>&1)
state() { x=$(docker inspect -f '{{.State.Status}}' "$1" 2>/dev/null | head -1); echo "${x:-absent}"; }
idx1=$(cat "$D/INDEX.md")

t=cleanup_removes_only_what_the_video_owns
check $t '[ -z "$(docker ps -aq --filter label=com.docker.compose.project=dv-app)" ] && ! docker volume inspect dv-app_data >/dev/null 2>&1 \
  && ! pgrep -f "sleep 30$RID" >/dev/null && [ "$(state dvtest-user-$RID)" = running ] && echo "$out" | grep -q "container dvtest-user-$RID (not the video" ' \
  || echo "$out" | sed 's/^/     /'
t=a_stack_that_was_stopped_stays_stopped
check $t '[ "$(state dvtest-found-$RID-svc-1)" = exited ] && [ "$(state dvtest-found-$RID-extra-1)" = absent ] \
  && docker volume inspect dvtest-found-${RID}_keep >/dev/null 2>&1' || { echo "svc: $(state dvtest-found-$RID-svc-1) extra: $(state dvtest-found-$RID-extra-1)"; echo "$out"; } | sed 's/^/     /'
t=a_checkpoint_is_saved_and_restored
rest=$($LG restore "$R" dv-app 2>&1)
rows=$(docker run --rm -v dv-app_data:/data --entrypoint cat "$IMG" /data/rows.txt 2>&1)
check $t '[ -s "$D/state/dv-app/meta.json" ] && ls "$D"/state/dv-app/*.tar.gz >/dev/null 2>&1 && [ "$rows" = "42 rows" ] \
  && [ "$(docker volume inspect -f "{{index .Labels \"com.docker.compose.project\"}}" dv-app_data)" = dv-app ]' \
  || { echo "$rest"; echo "rows: $rows"; ls "$D/state/dv-app" 2>&1; } | sed 's/^/     /'
t=a_checkpoint_over_the_size_limit_is_skipped
(cd "$APP" && COMPOSE_PROJECT_NAME=dv-app docker compose up -d >/dev/null 2>&1)
out2=$($LG cleanup "$R" --limit-gb 0.0000000001 2>&1)
check $t 'echo "$out2" | grep -q "dv-app: checkpoint skipped" && grep -q "checkpoint skipped" "$D/INDEX.md" \
  && [ -z "$(docker ps -aq --filter label=com.docker.compose.project=dv-app)" ]' || { echo "$out2"; grep -A4 "^## Checkpoints" "$D/INDEX.md"; } | sed 's/^/     /'
t=index_says_nothing_is_left_running
st=$($LG status "$R" 2>&1)
check $t 'echo "$st" | grep -q "nothing owned is running" && sed -n "/^## Running now/,/^## Checkpoints/p" "$D/INDEX.md" | grep -q "^Nothing\.$" \
  && grep -q "Last cleanup" "$D/INDEX.md" && echo "$idx1" | grep -q "not the video.s, left alone: container dvtest-user-$RID"' || sed -n "/^## Running now/,/^## Saved/p" "$D/INDEX.md" | sed 's/^/     /'
echo "$pass passed, $fail failed, $skip skipped"; [ "$fail" = 0 ]
