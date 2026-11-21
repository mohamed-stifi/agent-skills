# Shared by watch.sh and watch-pr.sh (sourced, not run). The caller sets `state` and defines:
#   snap             print the JSON snapshot on stdout (gh errors on stderr); non-zero on failure
#   compare MODE F   read snapshot file F, update $state, print events (watch) or a summary (init)
# Exit codes: 0 event or no change, 1 init failed, 2 usage, 3 every poll of the window failed.
cap() { perl -e 'alarm shift; exec @ARGV' 60 "$@"; }   # cap any command at 60 s (macOS has no `timeout`)

need_repo() {
  REPO=${REPO:-$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)}
  [ -n "$REPO" ] || { echo "set REPO=owner/name"; exit 2; }
}

# poll MODE: one snapshot and comparison; events or summary in $out, the error in $errf on failure
poll() {
  snap > "$tmp" 2> "$errf" && [ -s "$tmp" ] || return 1
  out=$(compare "$1" "$tmp" 2> "$errf") || return 1
}

# watch_main MODE MINUTES EVERY
watch_main() {
  tmp=$(mktemp "${TMPDIR:-/tmp}/ght-watch.XXXXXX") || { echo "mktemp failed"; exit 1; }
  errf="$tmp.err"; trap 'rm -f "$tmp" "$errf"' EXIT
  if [ "$1" = init ]; then
    poll init || { echo "init: failed: $(tail -n 1 "$errf")"; exit 1; }
    echo "$out"; exit 0
  fi
  local deadline polls=0 failed=0
  deadline=$(( $(date +%s) + $2 * 60 ))
  while :; do   # at least one poll, so `watch 0` checks once
    polls=$((polls + 1))
    if poll watch; then
      if [ -n "$out" ]; then echo "$out"; echo "WATCH: $(date -u +%H:%M:%S) events above"; exit 0; fi
    else
      failed=$((failed + 1))
    fi
    [ $(( $(date +%s) + $3 )) -lt "$deadline" ] || break
    sleep "$3"
  done
  if [ "$failed" = "$polls" ]; then
    echo "WATCH: every poll failed ($polls): $(tail -n 1 "$errf")"; exit 3
  fi
  local note=""; [ "$failed" = 0 ] || note=" ($failed of $polls polls failed)"
  echo "WATCH: no change by $(date -u +%H:%M:%S)$note"; exit 0
}
