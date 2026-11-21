#!/usr/bin/env bash
# Tests for scripts/watch.sh and scripts/watch-pr.sh against a stub `gh` (no network, no account).
# Each test is a scenario of issue #7. usage: bash tests/watchers.sh
set -uo pipefail
HERE=$(cd "$(dirname "$0")/.." && pwd)
W=${W:-"$HERE/scripts/watch.sh"}; WP=${WP:-"$HERE/scripts/watch-pr.sh"}
T=$(mktemp -d "${TMPDIR:-/tmp}/ght-test.XXXXXX"); trap 'rm -rf "$T"' EXIT
mkdir -p "$T/bin"
# The stub behaves like gh where it matters: `pr list` returns 30 by default, `api --paginate` without
# --slurp or --jq prints each page's array back to back, `pr view` of a missing PR fails.
cat > "$T/bin/gh" <<'EOF'
#!/bin/sh
echo "$*" >> "$STUB/calls"
[ -f "$STUB/fail" ] && { echo "HTTP 401: Bad credentials (https://api.github.com/graphql)" >&2; exit 1; }
case "$1 $2" in
  "issue list") cat "$STUB/issues.json" ;;
  "pr list") lim=30; prev=; for a; do [ "$prev" = --limit ] && lim=$a; prev=$a; done
             [ -f "$STUB/prs.txt" ] && head -n "$lim" "$STUB/prs.txt"; true ;;
  "pr view") [ -f "$STUB/pr-$3.json" ] || { echo "no pull requests found" >&2; exit 1; }; cat "$STUB/pr-$3.json" ;;
  "api "*) n=$(echo "$2" | sed 's|.*/pulls/\([0-9]*\)/comments|\1|'); f="$STUB/inline-$n.pages"
           [ -f "$f" ] || echo '[]' > "$f"
           case "$*" in
             *--slurp*) printf '['; paste -sd, "$f"; printf ']\n' ;;
             *--jq*) python3 -c 'import json,sys
for line in open(sys.argv[1]):
    for x in json.loads(line): print(json.dumps(x))' "$f" ;;
             *) tr -d '\n' < "$f" ;;
           esac ;;
  "repo view") echo o/r ;;
  *) echo "stub gh: unexpected: $*" >&2; exit 1 ;;
esac
EOF
chmod +x "$T/bin/gh"
export PATH="$T/bin:$PATH" REPO=o/r LABEL=task-to-x MARK='<!-- p-agent -->'
pass=0; fail=0
ok() { echo "ok   $1"; pass=$((pass+1)); }
ko() { echo "FAIL $1"; echo "$2" | sed 's/^/     /'; fail=$((fail+1)); }
fresh() { export STUB="$T/$1"; rm -rf "$STUB"; mkdir -p "$STUB"; ST="$STUB/state.json"; }
issue() { # $1 = extra comments (JSON, each starting with a comma)
  printf '[{"number":5,"title":"Decision: x","state":"OPEN","url":"u5","comments":[{"url":"c1","body":"<!-- p-agent --> q","author":{"login":"h"}}%s]}]' "$1" > "$STUB/issues.json"
}
pr() { # $1 = number, $2 = extra comments
  printf '{"number":%s,"title":"PR %s","state":"OPEN","url":"p%s","reviews":[],"comments":[{"url":"pc%s","body":"<!-- p-agent --> guide","author":{"login":"h"}}%s]}' "$1" "$1" "$1" "$1" "$2" > "$STUB/pr-$1.json"
}

t=re_init_keeps_an_unhandled_issue_reply; fresh $t
issue ""; bash "$W" "$ST" init >/dev/null
issue ',{"url":"c2","body":"1","author":{"login":"h"}}'; bash "$W" "$ST" init >/dev/null
out=$(bash "$W" "$ST" watch 0 1); echo "$out" | grep -q 'new comment by h .*: 1 ' && ok $t || ko $t "$out"

t=first_init_marks_existing_comments_as_seen; fresh $t
issue ',{"url":"c2","body":"old reply","author":{"login":"h"}}'; bash "$W" "$ST" init >/dev/null
out=$(bash "$W" "$ST" watch 0 1); echo "$out" | grep -q '^WATCH: no change' && ok $t || ko $t "$out"

t=a_zero_minute_window_polls_once; fresh $t
issue ""; bash "$W" "$ST" init >/dev/null
issue ',{"url":"c2","body":"done","author":{"login":"h"}}'
out=$(bash "$W" "$ST" watch 0 1); echo "$out" | grep -q 'EVENT #5 new comment' && ok $t || ko $t "$out"

t=re_init_keeps_an_unhandled_pr_comment; fresh $t
echo 7 > "$STUB/prs.txt"; pr 7 ""; bash "$WP" "$ST" init >/dev/null
pr 7 ',{"url":"pc2","body":"merge","author":{"login":"h"}}'; bash "$WP" "$ST" init >/dev/null
out=$(bash "$WP" "$ST" watch 0 1); echo "$out" | grep -q 'EVENT #7 comment by h: merge' && ok $t || ko $t "$out"

t=line_comments_over_several_pages_are_read; fresh $t
echo 7 > "$STUB/prs.txt"; pr 7 ""
echo '[{"id":1,"path":"a.sh","line":3,"body":"<!-- p-agent --> note","user":{"login":"h"}}]' > "$STUB/inline-7.pages"
bash "$WP" "$ST" init >/dev/null
echo '[{"id":2,"path":"a.sh","line":9,"body":"why this?","user":{"login":"h"}}]' >> "$STUB/inline-7.pages"
out=$(bash "$WP" "$ST" watch 0 1); echo "$out" | grep -q 'line comment on a.sh:9 by h: why this?' && ok $t || ko $t "$out"

t=more_than_30_labelled_prs; fresh $t
for i in $(seq 1 31); do echo "$i" >> "$STUB/prs.txt"; pr "$i" ""; done
bash "$WP" "$ST" init >/dev/null
pr 31 ',{"url":"pc2","body":"merge","author":{"login":"h"}}'
out=$(bash "$WP" "$ST" watch 0 1); echo "$out" | grep -q 'EVENT #31 comment by h: merge' && ok $t || ko $t "$out"

t=every_poll_failed_is_not_no_change; fresh $t
issue ""; bash "$W" "$ST" init >/dev/null; touch "$STUB/fail"
out=$(bash "$W" "$ST" watch 0 1); code=$?
[ "$code" = 3 ] && echo "$out" | grep -q 'WATCH: every poll failed.*Bad credentials' && ok $t || ko $t "exit $code: $out"

t=a_mistyped_extra_prs_number_is_refused_at_init; fresh $t
echo 7 > "$STUB/prs.txt"; pr 7 ""
out=$(EXTRA_PRS=99999 bash "$WP" "$ST" init 2>&1); code=$?
[ "$code" = 1 ] && echo "$out" | grep -q '#99999' && ok $t || ko $t "exit $code: $out"

t=the_watcher_follows_needs_human_by_default; fresh $t   # issue #14
issue ""; out=$(env -u LABEL bash "$W" "$ST" init 2>&1)
grep -qs -- "issue list .*--label needs:human" "$STUB/calls" && ok $t || ko $t "$out $(cat "$STUB/calls" 2>/dev/null)"

echo "$pass passed, $fail failed"; [ "$fail" = 0 ]
