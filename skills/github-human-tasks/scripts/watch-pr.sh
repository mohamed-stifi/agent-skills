#!/usr/bin/env bash
# Watch the pull requests under review (every open PR carrying LABEL, default "review:now") until
# the human acts on it.
#
#   REPO=owner/name MARK='<!-- proj-agent -->' [LABEL=review:now] watch-pr.sh STATE.json init
#   REPO=…          MARK=…                                          watch-pr.sh STATE.json watch [minutes] [seconds]
#
# Events (exit 0, printed as "EVENT …"): a new review of any state, a new unmarked PR comment or
# inline review comment (including one inside a PENDING, not yet sent, review: GitHub's REST API hides
# those, so they are read from the GraphQL review threads), a PR leaving the label (merged, closed or
# unlabelled), or a PR newly labelled.
# A comment counts as the human's when its body lacks MARK. No event before the deadline:
# "WATCH: no change". Every gh call is capped at 60 s; a failed poll is never an event.
set -uo pipefail
state=${1:?state file}; mode=${2:?init|watch}
: "${MARK:?set MARK, e.g. <!-- proj-agent -->}"; LABEL=${LABEL:-review:now}
REPO=${REPO:-$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)}
[ -n "$REPO" ] || { echo "set REPO=owner/name"; exit 2; }
export MARK LABEL
cap() { perl -e 'alarm shift; exec @ARGV' 60 "$@"; }
snap() { # prints a JSON list of {number,title,state,url,reviews,comments,inline}, one per labelled PR
  local ns n pv il out="["; local first=1
  ns=$(cap gh pr list -R "$REPO" --label "$LABEL" --state open --json number -q '.[].number' 2>/dev/null) || return 1
  for n in $ns; do
    pv=$(cap gh pr view "$n" -R "$REPO" --json number,title,state,url,reviews,comments 2>/dev/null) || return 1
    il=$(cap gh api "repos/$REPO/pulls/$n/comments" --paginate 2>/dev/null) || return 1
    th=$(cap gh api graphql -F owner="${REPO%%/*}" -F name="${REPO##*/}" -F n="$n" -f query='query($owner:String!,$name:String!,$n:Int!){repository(owner:$owner,name:$name){pullRequest(number:$n){reviewThreads(first:100){nodes{path line originalLine comments(first:50){nodes{id databaseId body state url author{login}}}}}}}}' -q '[.data.repository.pullRequest.reviewThreads.nodes[] as $t | $t.comments.nodes[] | {id,databaseId,body,state,url,login:.author.login,path:$t.path,line:($t.line // $t.originalLine)}]' 2>/dev/null) || return 1
    pv=$(python3 -c 'import json,sys; pv=json.loads(sys.argv[1]); pv["inline"]=json.loads(sys.argv[2] or "[]"); pv["threads"]=json.loads(sys.argv[3] or "[]"); print(json.dumps(pv))' "$pv" "$il" "$th")
    [ $first = 1 ] && first=0 || out="$out,"
    out="$out$pv"
  done
  echo "$out]"
}
compare() {
  python3 - "$state" "$1" <<'PY'
import json, os, sys
state_path, snap_path = sys.argv[1], sys.argv[2]
MARK, LABEL = os.environ["MARK"], os.environ["LABEL"]
old = json.load(open(state_path)) if os.path.exists(state_path) else None
cur = json.load(open(snap_path))
def ids(pr):
    seen = [ "r:"+str(r.get("id") or r.get("submittedAt")) for r in pr.get("reviews", []) ]
    seen += [ "c:"+c["url"] for c in pr.get("comments", []) ]
    seen += [ "i:"+str(c["id"]) for c in pr.get("inline", []) ]
    seen += [ "i:"+str(c["databaseId"]) if c.get("databaseId") else "t:"+c["id"] for c in pr.get("threads", []) ]
    return {"state": pr.get("state"), "seen": sorted(seen)}
new = {str(pr["number"]): ids(pr) for pr in cur}
ev = []
if old is not None:
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
        for c in pr.get("threads", []):
            k = "i:"+str(c["databaseId"]) if c.get("databaseId") else "t:"+c["id"]
            if k not in seen and MARK not in (c.get("body") or ""):
                body = " ".join((c.get("body") or "").split())
                st = "PENDING, not yet sent" if c.get("state") == "PENDING" else str(c.get("state")).lower()
                ev.append(f"EVENT #{n} line comment ({st}) on {c.get('path')}:{c.get('line')} by {c.get('login','?')}: {body[:600]}  {c.get('url','')}")
json.dump(new, open(state_path, "w"))
print("\n".join(ev))
PY
}
tmp=$(mktemp); trap 'rm -f "$tmp"' EXIT
if [ "$mode" = init ]; then
  snap > "$tmp" && [ -s "$tmp" ] || { echo "init: gh failed"; exit 1; }
  rm -f "$state"; compare "$tmp" >/dev/null
  python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print('watching', ', '.join('#'+n+' ('+str(len(v['seen']))+' seen)' for n,v in sorted(d.items(), key=lambda kv:int(kv[0]))) or 'no PR')" "$state"
  exit 0
fi
minutes=${3:-100}; every=${4:-90}
deadline=$(( $(date +%s) + minutes * 60 ))
while [ "$(date +%s)" -lt "$deadline" ]; do
  if snap > "$tmp" && [ -s "$tmp" ]; then
    ev=$(compare "$tmp")
    if [ -n "$ev" ]; then echo "$ev"; echo "WATCH: $(date -u +%H:%M:%S) events above"; exit 0; fi
  fi
  sleep "$every"
done
echo "WATCH: no change by $(date -u +%H:%M:%S)"; exit 0
