#!/usr/bin/env bash
# Watch the issues labelled LABEL until the human does something on one of them.
#
#   REPO=owner/name LABEL=task-to-<owner> MARK='<!-- proj-agent -->' watch.sh STATE.json init
#   REPO=…          LABEL=…               MARK=…                      watch.sh STATE.json watch [minutes] [seconds]
#
# A comment counts as the human's when its body lacks MARK (the agent posts through the same GitHub
# account, so the author can't tell them apart). Events end the watch (exit 0, printed as "EVENT …"):
# a new unmarked comment, an issue closed or reopened, an issue newly labelled or unlabelled.
# No event before the deadline: prints "WATCH: no change" and exits 0. A failed poll (network) is
# skipped, never an event. Bounded: default 110 minutes, polling every 120 s.
set -uo pipefail
state=${1:?state file}; mode=${2:?init|watch}
: "${LABEL:?set LABEL, e.g. task-to-<owner>}"; : "${MARK:?set MARK, e.g. <!-- proj-agent -->}"
REPO=${REPO:-$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)}
[ -n "$REPO" ] || { echo "set REPO=owner/name"; exit 2; }
export LABEL MARK
snap() {
  gh issue list -R "$REPO" --label "$LABEL" --state all --limit 200 \
    --json number,title,state,comments,url 2>/dev/null
}
compare() { # $1 = snapshot file; updates the state file; prints events
  python3 - "$state" "$1" <<'PY'
import json, os, sys
state_path, snap_path = sys.argv[1], sys.argv[2]
MARK, LABEL = os.environ["MARK"], os.environ["LABEL"]
old = json.load(open(state_path)) if os.path.exists(state_path) else None
cur = {}
for it in json.load(open(snap_path)):
    cur[str(it["number"])] = {"title": it["title"], "state": it["state"], "url": it["url"],
                              "comments": {c["url"]: c for c in it.get("comments", [])}}
events = []
if old is not None:
    for n, it in cur.items():
        o = old.get(n)
        if o is None:
            events.append(f"EVENT #{n} newly labelled {LABEL}: {it['title']}  {it['url']}")
            continue
        if o["state"] != it["state"]:
            events.append(f"EVENT #{n} {o['state']} -> {it['state']}: {it['title']}  {it['url']}")
        for url, c in it["comments"].items():
            if url in o["comment_urls"] or MARK in (c.get("body") or ""):
                continue
            who = (c.get("author") or {}).get("login", "?")
            body = " ".join((c.get("body") or "").split())
            events.append(f"EVENT #{n} new comment by {who} at {c.get('createdAt', '?')}: {body[:600]}  {url}")
    for n, o in old.items():
        if n not in cur:
            events.append(f"EVENT #{n} no longer labelled {LABEL}: {o['title']}")
json.dump({n: {"title": it["title"], "state": it["state"], "url": it["url"],
               "comment_urls": sorted(it["comments"])} for n, it in cur.items()},
          open(state_path, "w"), indent=1)
print("\n".join(events))
PY
}
tmp=$(mktemp); trap 'rm -f "$tmp"' EXIT
if [ "$mode" = init ]; then
  snap > "$tmp" && [ -s "$tmp" ] || { echo "init: gh failed"; exit 1; }
  rm -f "$state"; compare "$tmp" >/dev/null
  python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print('watching', len(d), 'issues:', ' '.join('#'+n for n in sorted(d, key=int)))" "$state"
  exit 0
fi
minutes=${3:-110}; every=${4:-120}
deadline=$(( $(date +%s) + minutes * 60 ))
while [ "$(date +%s)" -lt "$deadline" ]; do
  if snap > "$tmp" && [ -s "$tmp" ]; then
    ev=$(compare "$tmp")
    if [ -n "$ev" ]; then echo "$ev"; echo "WATCH: $(date -u +%H:%M:%S) events above"; exit 0; fi
  fi
  sleep "$every"
done
echo "WATCH: no change by $(date -u +%H:%M:%S)"; exit 0
