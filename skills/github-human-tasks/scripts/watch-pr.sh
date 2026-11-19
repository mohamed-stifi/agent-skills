#!/usr/bin/env bash
# Watch the ONE pull request under review (the open PR carrying LABEL, default "review:now") until
# the human acts on it.
#
#   REPO=owner/name MARK='<!-- proj-agent -->' [LABEL=review:now] watch-pr.sh STATE.json init
#   REPO=…          MARK=…                                          watch-pr.sh STATE.json watch [minutes] [seconds]
#
# Events (exit 0, printed as "EVENT …"): a new review of any state, a new unmarked PR comment or
# inline review comment, the PR merged or closed, or the label moved to another PR.
# A comment counts as the human's when its body lacks MARK. No event before the deadline:
# "WATCH: no change". Every gh call is capped at 60 s; a failed poll is never an event.
set -uo pipefail
state=${1:?state file}; mode=${2:?init|watch}
: "${MARK:?set MARK, e.g. <!-- proj-agent -->}"; LABEL=${LABEL:-review:now}
REPO=${REPO:-$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)}
[ -n "$REPO" ] || { echo "set REPO=owner/name"; exit 2; }
export MARK LABEL
cap() { perl -e 'alarm shift; exec @ARGV' 60 "$@"; }
snap() { # prints one JSON object: {pr, state, reviews, comments, inline} or fails
  local n; n=$(cap gh pr list -R "$REPO" --label "$LABEL" --state open --json number -q '.[0].number' 2>/dev/null) || return 1
  if [ -z "$n" ]; then echo '{"pr":null}'; return 0; fi
  local pv il
  pv=$(cap gh pr view "$n" -R "$REPO" --json number,title,state,url,reviews,comments 2>/dev/null) || return 1
  il=$(cap gh api "repos/$REPO/pulls/$n/comments" --paginate 2>/dev/null) || return 1
  python3 -c 'import json,sys; pv=json.loads(sys.argv[1]); il=json.loads(sys.argv[2] or "[]"); pv["inline"]=il; print(json.dumps(pv))' "$pv" "$il"
}
compare() {
  python3 - "$state" "$1" <<'PY'
import json, os, sys
state_path, snap_path = sys.argv[1], sys.argv[2]
MARK, LABEL = os.environ["MARK"], os.environ["LABEL"]
old = json.load(open(state_path)) if os.path.exists(state_path) else None
cur = json.load(open(snap_path))
def ids(s):
    if s.get("pr") is None and "number" not in s: return {"pr": None, "state": None, "seen": []}
    seen = [ "r:"+str(r.get("id") or r.get("submittedAt")) for r in s.get("reviews", []) ]
    seen += [ "c:"+c["url"] for c in s.get("comments", []) ]
    seen += [ "i:"+str(c["id"]) for c in s.get("inline", []) ]
    return {"pr": s.get("number"), "state": s.get("state"), "seen": sorted(seen)}
new = ids(cur); ev = []
if old is not None:
    if old["pr"] != new["pr"]:
        ev.append(f"EVENT the '{LABEL}' PR changed: #{old['pr']} -> #{new['pr']}")
    else:
        seen = set(old["seen"])
        if old["state"] != new["state"]:
            ev.append(f"EVENT #{new['pr']} {old['state']} -> {new['state']}  {cur.get('url','')}")
        for r in cur.get("reviews", []):
            k = "r:"+str(r.get("id") or r.get("submittedAt"))
            if k not in seen and MARK not in (r.get("body") or ""):
                body = " ".join((r.get("body") or "").split())
                ev.append(f"EVENT #{new['pr']} review {r.get('state')} by {(r.get('author') or {}).get('login','?')}: {body[:600]}")
        for c in cur.get("comments", []):
            if "c:"+c["url"] not in seen and MARK not in (c.get("body") or ""):
                body = " ".join((c.get("body") or "").split())
                ev.append(f"EVENT #{new['pr']} comment by {(c.get('author') or {}).get('login','?')}: {body[:600]}  {c['url']}")
        for c in cur.get("inline", []):
            if "i:"+str(c["id"]) not in seen and MARK not in (c.get("body") or ""):
                body = " ".join((c.get("body") or "").split())
                ev.append(f"EVENT #{new['pr']} line comment on {c.get('path')}:{c.get('line') or c.get('original_line')} by {(c.get('user') or {}).get('login','?')}: {body[:600]}  {c.get('html_url','')}")
json.dump(new, open(state_path, "w"))
print("\n".join(ev))
PY
}
tmp=$(mktemp); trap 'rm -f "$tmp"' EXIT
if [ "$mode" = init ]; then
  snap > "$tmp" && [ -s "$tmp" ] || { echo "init: gh failed"; exit 1; }
  rm -f "$state"; compare "$tmp" >/dev/null
  python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print('watching PR', d['pr'], 'with', len(d['seen']), 'items seen')" "$state"
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
