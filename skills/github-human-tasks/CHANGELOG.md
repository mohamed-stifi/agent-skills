# Changelog — github-human-tasks

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
