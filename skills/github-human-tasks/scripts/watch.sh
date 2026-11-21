#!/usr/bin/env bash
# Watch the issues labelled LABEL (default "needs:human") until the human does something on one of them.
#
#   REPO=owner/name MARK='<!-- proj-agent -->' [LABEL=needs:human] watch.sh STATE.json init
#   REPO=…          MARK=…                                         watch.sh STATE.json watch [minutes] [seconds]
#
# A comment counts as the human's when its body lacks MARK (the agent posts through the same GitHub
# account, so the author can't tell them apart). Events end the watch (exit 0, printed as "EVENT …"):
# a new unmarked comment, an issue closed or reopened, an issue newly labelled or unlabelled.
# `init` with an existing state file adopts label and state changes but keeps unmarked comments that
# were never reported, so the next `watch` still shows them; delete the state file for a fresh start.
# No event: "WATCH: no change" (exit 0). Every poll failed: "WATCH: every poll failed" (exit 3).
# Bounded: default 110 minutes, polling every 120 s; `watch 0` polls once.
set -uo pipefail
state=${1:?state file}; mode=${2:?init|watch}
: "${MARK:?set MARK, e.g. <!-- proj-agent -->}"; LABEL=${LABEL:-needs:human}
. "$(dirname "$0")/watch-lib.sh"
need_repo
export LABEL MARK
snap() {
  cap gh issue list -R "$REPO" --label "$LABEL" --state all --limit 500 --json number,title,state,comments,url
}
compare() { # $1 = init|watch, $2 = snapshot file
  python3 - "$state" "$2" "$1" <<'PY'
import json, os, sys
state_path, snap_path, mode = sys.argv[1:4]
MARK, LABEL = os.environ["MARK"], os.environ["LABEL"]
old = json.load(open(state_path)) if os.path.exists(state_path) else None
cur = {}
for it in json.load(open(snap_path)):
    cur[str(it["number"])] = {"title": it["title"], "state": it["state"], "url": it["url"],
                              "comments": {c["url"]: c for c in it.get("comments", [])}}
marked = lambda c: MARK in (c.get("body") or "")
events, seen, kept = [], {}, 0
for n, it in cur.items():
    o = (old or {}).get(n)
    if mode == "init" and o is not None:   # keep what the watcher never reported
        seen[n] = [u for u, c in it["comments"].items() if u in o["comment_urls"] or marked(c)]
        kept += len(it["comments"]) - len(seen[n])
    else:
        seen[n] = list(it["comments"])
if mode == "watch" and old is not None:
    for n, it in cur.items():
        o = old.get(n)
        if o is None:
            events.append(f"EVENT #{n} newly labelled {LABEL}: {it['title']}  {it['url']}")
            continue
        if o["state"] != it["state"]:
            events.append(f"EVENT #{n} {o['state']} -> {it['state']}: {it['title']}  {it['url']}")
        for url, c in it["comments"].items():
            if url in o["comment_urls"] or marked(c):
                continue
            who = (c.get("author") or {}).get("login", "?")
            body = " ".join((c.get("body") or "").split())
            events.append(f"EVENT #{n} new comment by {who} at {c.get('createdAt', '?')}: {body[:600]}  {url}")
    for n, o in old.items():
        if n not in cur:
            events.append(f"EVENT #{n} no longer labelled {LABEL}: {o['title']}")
with open(state_path + ".tmp", "w") as f:
    json.dump({n: {"title": it["title"], "state": it["state"], "url": it["url"],
                   "comment_urls": sorted(seen[n])} for n, it in cur.items()}, f, indent=1)
os.replace(state_path + ".tmp", state_path)
if mode == "init":
    line = f"watching {len(cur)} issues: " + " ".join("#" + n for n in sorted(cur, key=int))
    print(line + (f"; {kept} unreported comment(s) kept for the next watch" if kept else ""))
else:
    print("\n".join(events))
PY
}
case "$mode" in
  init) watch_main init ;;
  watch) watch_main watch "${3:-110}" "${4:-120}" ;;
  *) echo "mode must be init or watch"; exit 2 ;;
esac
