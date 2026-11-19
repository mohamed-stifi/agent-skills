# Changelog — github-human-tasks

## 1.5.0 — 2026-11-19
- Delegation protocol (the human's request): one liaison sub-agent runs the whole loop and reports to its parent
  only `STATUS:` or `NEED:` (product decisions, change requests, conflicts, blockers, skill updates).

## 1.4.0 — 2026-11-19
- The human chooses how many PRs to review at once (they asked for 3, related and in order): number the guides,
  state the merge order, and hold a stacked PR's merge until its base is merged. `watch-pr.sh` follows every
  PR under `review:now`.

## 1.3.0 — 2026-11-19
- PR review with the human, one at a time: the `review:now` label plus assigning the human (findable from
  "Assigned to me"), a guide comment, answering by a "merge" comment when Approve is disabled, and `watch-pr.sh`,
  which follows the labelled PR and exits on reviews, comments, line comments, merge or close.

## 1.2.1 — 2026-11-19
- Fix: `watch.sh` caps each `gh` call at 60 s (`perl` alarm, since macOS has no `timeout`). One hung network
  call used to keep the watcher alive past its window until the agent's background limit killed it.

## 1.2.0 — 2026-11-19
- A new kind of reply: "is this important?" gets a one-line verdict (urgent / useful / not needed), what it blocks,
  then the choice again with a "later" option.

## 1.1.0 — 2026-11-19
- New rule from the human: no apology or meta preamble ("Sorry, that was written for engineers. Here it is
  plainly."). Go straight from the header to the content, including in rewrites.

## 1.0.0 — 2026-11-19
- First version, from a real build where the human answered ~15 decisions on GitHub:
  - the flow: open, watch, handle a reply, record the decision, close via PR;
  - the approved body format: words → question → story → what we found → what others do → choose;
  - a visible 🤖 header plus a hidden marker on every agent post, since posts share the human's account;
  - `watch.sh` with event exit, re-init after your own label changes, and bounded windows;
  - issue forms for decisions and person-only tasks;
  - the rule to update this skill whenever the human changes how you work together.
