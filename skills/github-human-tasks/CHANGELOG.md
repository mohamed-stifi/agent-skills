# Changelog — github-human-tasks

## 2.0.0 — 2026-11-21
- PR review mode (review sets, the PR watcher, merging, closing-keyword checks, defaults that promise work)
  moved to `references/pr-review.md`; SKILL.md points to it and is 44% smaller (13,876 → about 7,800 chars).
- The description names PR review sets and "give me PRs to review", so the skill triggers for them.
- Each rule stated once: the post header and `MARK`, the tracking issue, search-before-create, the watcher
  arguments (now defaults in the commands). **Report** is defined up front: a `NEED:` to the parent as the
  liaison, otherwise a message to the user, so the PR rules work without a liaison.
- "Keep this skill current" names the skills repo this folder comes from, not the project.
- One project's history removed from the rules (the human's quote, PR numbers, "the parent authorised"); the
  set size is "N, default 5". The rules themselves are unchanged.

## 1.10.0 — 2026-11-21
- Watchers never lose a reply: `init` with an existing state file adopts label and state changes but keeps
  unmarked comments it never reported (both scripts), so SKILL.md's restart paragraph shrinks to one sentence.
- `watch-pr.sh` reads line comments over several pages (`--paginate --jq '.[]'`; plain `--paginate` glued the
  pages' arrays into invalid JSON), follows up to 500 labelled PRs (was gh's default 30), and refuses an
  `EXTRA_PRS` number that is not a PR at `init`.
- A window where every poll failed ends with `WATCH: every poll failed` and the error, exit 3, instead of
  `WATCH: no change`. `watch 0` polls once. State files are written atomically.
- Shared `scripts/watch-lib.sh`; `tests/watchers.sh` runs both watchers against a stub `gh` (CI runs it).

## 1.9.5 — 2026-11-21
- After a decision: the build work follows the `issue-driven-prs` skill when it is available (one line; triggers
  and description unchanged).

## 1.9.4 — 2026-11-20
- A stack top whose "Closes #N" is not registered after it retargets to the default branch: re-save its body
  unchanged (`gh pr view N --json body --jq .body > f && gh pr edit N --body-file f`), never altering the
  text. This is the one PR-body edit the liaison may make, authorised by the parent after it worked for #153
  and #202.

## 1.9.3 — 2026-11-20
- Never lose the human's comment to a restart (a real miss: two "marge" comments sat unseen for 20 and 6 minutes
  because an `init` run just after them marked them as seen): do not `init` just to add PRs to the list, list
  the human's unhandled comments on every tracked PR before any `init`, and once after any restart.
- GitHub computes a PR's closing-issues list lazily after a retarget (a top PR read `[]`, then `[31]` minutes
  later): re-read before trusting an empty list, and tell the parent when a top PR still lists nothing.

## 1.9.2 — 2026-11-20
- Before every merge, read `gh pr view N --json closingIssuesReferences`; hold the merge and send a `NEED:` if
  it closes an issue while a same-issue PR is still open above it (the parent's rule, after #156's description
  line "#163 … closes #31" closed #31 when part 1 merged, and an audit found #19, #25, #30 and #36 closed by a
  lower layer the same day). The cure is in the body ("closes issue N", no `#`, except on the top PR). A
  stacked PR's list is empty until its base merges, so the check is made at merge time.

## 1.9.1 — 2026-11-20
- A recorded default that promises future work must point at an open issue (the parent's rule, after a default
  on a merged PR promised a test and I wrote "I have asked" before asking, and an earlier note cited a closed
  issue for a follow-up that lived in another): search for the issue, file it if none exists (engineering issue,
  or a `Decision:` issue when it needs the human), link it from the PR note and the tracking issue, and send the
  parent a `NEED:` in the same turn. Never say "I have asked" before the `NEED:` is sent.

## 1.9.0 — 2026-11-20
- Five at a time (the human's request: "give me next 5 PRs to review, not only one or two"): the default set size
  is five, not one. Open each PR the moment it is verified, never hold ready PRs back for a slower one, and keep
  five open while verified PRs exist.

## 1.8.0 — 2026-11-20
- Look ahead (the human's request): while a review set is open, prepare the next one (trial merge, checks,
  guides) without labelling or assigning it, and assign it the moment the current set merges. Also, `watch-pr.sh`
  accepts `EXTRA_PRS`, so comments on just-merged PRs are seen (the human's request came on a merged PR and was
  missed for an hour).

## 1.7.0 — 2026-11-19
- Removed 1.6.0's pending-review rule and its `watch-pr.sh` change, at the human's request: the question that
  went unanswered was in a review they had not sent, which was their slip, not a gap in the method. `SKILL.md` and
  `watch-pr.sh` are back to their 1.5.0 text; the 1.6.0 entry below stays as history.

## 1.6.0 — 2026-11-19
- A question in a review the human has not yet sent ("Pending") was invisible: GitHub's REST API hides pending
  line comments. `watch-pr.sh` now also reads the GraphQL review threads and reports them as
  `line comment (PENDING, not yet sent)`. New rules: query `reviewThreads` before calling a review empty, answer
  in a PR comment and ask the human to press "Finish your review", and answer every open review question before
  merging.

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
