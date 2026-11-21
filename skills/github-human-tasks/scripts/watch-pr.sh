#!/usr/bin/env bash
# Watch the pull requests under review (every open PR carrying LABEL, default "review:now") until
# the human acts on it.
#
#   REPO=owner/name MARK='<!-- proj-agent -->' [LABEL=review:now] watch-pr.sh STATE.json init
#   REPO=…          MARK=…                                          watch-pr.sh STATE.json watch [minutes] [seconds]
#   EXTRA_PRS="70 89"  (optional, both modes): PR numbers followed whatever their state or label, for
#   example the last merged ones, since the human often comments after a merge. `init` refuses a
#   number that is not a PR.
#
# Events (exit 0, printed as "EVENT …"): a new review of any state, a new unmarked PR comment or
# inline review comment, a PR leaving the label (merged, closed or unlabelled), or a PR newly labelled.
# A comment counts as the human's when its body lacks MARK. `init` with an existing state file keeps
# unmarked comments and reviews that were never reported; delete the state file for a fresh start.
# No event: "WATCH: no change" (exit 0). Every poll failed: "WATCH: every poll failed" (exit 3).
# Default 100 minutes, polling every 90 s; `watch 0` polls once. Every gh call is capped at 60 s.
set -uo pipefail
state=${1:?state file}; mode=${2:?init|watch}
: "${MARK:?set MARK, e.g. <!-- proj-agent -->}"; LABEL=${LABEL:-review:now}
. "$(dirname "$0")/watch-lib.sh"
need_repo
export MARK LABEL
snap() { # prints a JSON list of {number,title,state,url,reviews,comments,inline}, one per watched PR
  local ns n out="[" first=1
  ns=$(cap gh pr list -R "$REPO" --label "$LABEL" --state open --limit 500 --json number -q '.[].number') || return 1
  ns=$(printf '%s\n' $ns ${EXTRA_PRS:-} | grep -E '^[0-9]+$' | sort -un)
  for n in $ns; do
    cap gh pr view "$n" -R "$REPO" --json number,title,state,url,reviews,comments > "$tmp.pv" || return 1
    # --jq '.[]' prints one comment per line across all pages (plain --paginate glues pages' arrays together)
    cap gh api "repos/$REPO/pulls/$n/comments" --paginate --jq '.[]' > "$tmp.il" || return 1
    [ $first = 1 ] && first=0 || out="$out,"
    out="$out$(python3 -c 'import json,sys
pv = json.load(open(sys.argv[1]))
pv["inline"] = [json.loads(l) for l in open(sys.argv[2]) if l.strip()]
print(json.dumps(pv))' "$tmp.pv" "$tmp.il")" || return 1
  done
  rm -f "$tmp.pv" "$tmp.il"
  echo "$out]"
}
compare() { # $1 = init|watch, $2 = snapshot file
  python3 - "$state" "$2" "$1" <<'PY'
import json, os, sys
state_path, snap_path, mode = sys.argv[1:4]
MARK, LABEL = os.environ["MARK"], os.environ["LABEL"]
old = json.load(open(state_path)) if os.path.exists(state_path) else None
cur = json.load(open(snap_path))
def items(pr):  # (key, body) for every review, comment and line comment
    for r in pr.get("reviews", []): yield "r:" + str(r.get("id") or r.get("submittedAt")), r.get("body") or ""
    for c in pr.get("comments", []): yield "c:" + c["url"], c.get("body") or ""
    for c in pr.get("inline", []): yield "i:" + str(c["id"]), c.get("body") or ""
new, kept = {}, 0
for pr in cur:
    n, o = str(pr["number"]), (old or {}).get(str(pr["number"]))
    keys = [k for k, _ in items(pr)]
    if mode == "init" and o is not None:   # keep what the watcher never reported
        seen = [k for k, b in items(pr) if k in o["seen"] or MARK in b]
        kept += len(keys) - len(seen)
    else:
        seen = keys
    new[n] = {"state": pr.get("state"), "seen": sorted(seen)}
ev = []
if mode == "watch" and old is not None:
    for n in sorted(set(old) - set(new), key=int):
        ev.append(f"EVENT #{n} no longer under '{LABEL}' (merged, closed or unlabelled)")
    for n in sorted(set(new) - set(old), key=int):
        ev.append(f"EVENT #{n} newly under '{LABEL}'")
    for pr in cur:
        n = str(pr["number"])
        if n not in old: continue
        seen = set(old[n]["seen"])
        for r in pr.get("reviews", []):
            k = "r:"+str(r.get("id") or r.get("submittedAt"))
            if k not in seen and MARK not in (r.get("body") or ""):
                body = " ".join((r.get("body") or "").split())
                ev.append(f"EVENT #{n} review {r.get('state')} by {(r.get('author') or {}).get('login','?')}: {body[:600]}")
        for c in pr.get("comments", []):
            if "c:"+c["url"] not in seen and MARK not in (c.get("body") or ""):
                body = " ".join((c.get("body") or "").split())
                ev.append(f"EVENT #{n} comment by {(c.get('author') or {}).get('login','?')}: {body[:600]}  {c['url']}")
        for c in pr.get("inline", []):
            if "i:"+str(c["id"]) not in seen and MARK not in (c.get("body") or ""):
                body = " ".join((c.get("body") or "").split())
                ev.append(f"EVENT #{n} line comment on {c.get('path')}:{c.get('line') or c.get('original_line')} by {(c.get('user') or {}).get('login','?')}: {body[:600]}  {c.get('html_url','')}")
with open(state_path + ".tmp", "w") as f:
    json.dump(new, f)
os.replace(state_path + ".tmp", state_path)
if mode == "init":
    line = "watching " + (", ".join(f"#{n} ({len(v['seen'])} seen)" for n, v in sorted(new.items(), key=lambda kv: int(kv[0]))) or "no PR")
    print(line + (f"; {kept} unreported comment(s) kept for the next watch" if kept else ""))
else:
    print("\n".join(ev))
PY
}
case "$mode" in
  init)
    for n in ${EXTRA_PRS:-}; do
      cap gh pr view "$n" -R "$REPO" --json number >/dev/null 2>&1 || { echo "init: EXTRA_PRS: #$n is not a PR in $REPO"; exit 1; }
    done
    watch_main init ;;
  watch) watch_main watch "${3:-100}" "${4:-90}" ;;
  *) echo "mode must be init or watch"; exit 2 ;;
esac
