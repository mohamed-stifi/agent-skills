---
name: github-human-tasks
description: Route what only a person can decide or do to them through GitHub issues, watch those issues, and act on their replies, in a format they confirmed they understand. Use when an agent working in a GitHub repo is blocked on a product decision, an account or payment, or anything needing the human's identity; when the user says "ask me in an issue", "make it a GitHub issue", "watch my replies", or names a label like task-to-<name>; or when replying in such an issue.
metadata:
  version: "1.9.2"
  author: mohamed-stifi
---

# GitHub human tasks (decisions and person-only tasks, as watched issues)

The human reads and answers on GitHub, not in the terminal. You open the issue, watch it, act on the reply,
and close the loop. `SKILL` = this folder. `REPO` = `owner/name`. `LABEL` = `task-to-<owner>` (the user's
name, e.g. `task-to-mohamed`). `MARK` = `<!-- <project>-agent -->`.

## When to use, and when not
- **Use** only when you are truly blocked on the human: a product choice the specs leave open, or a task
  needing their account, money, identity or machine.
- **First try to unblock yourself:** `gh` for repo setup, a tunnel (`cloudflared`) for online services,
  a local model (Ollama) for LLM tests, an installer or CLI. Say what you tried in the issue.
- **Don't** open issues for engineering choices with a sensible default. Take the default and leave it
  open for review in the PR ("defaulted, review").
- **Never** write local Markdown guides for the human. Every guide is an issue.

## Setup (once per repo)
```bash
gh label create "$LABEL" --color D93F0B --description "Waiting on <owner>" --force
gh label create needs:human --color FBCA04 --force
```
- **Issue forms, optional:** copy `SKILL/references/forms/*.yml` into `.github/ISSUE_TEMPLATE/` and replace
  `task-to-OWNER` with `LABEL`. They only
  show in GitHub's "New issue" page once they are on the default branch.
- **Tracking issue:** keep one pinned issue listing every human issue with its status (open, decided,
  built, PR).

## Open an issue
1. **Verify first.**
   - Read the code for what it does TODAY; never trust an issue's or spec's claim about behaviour.
   - Check the spec's exact meaning of every value you'll mention (e.g. is 5 the most or least critical?).
2. **Write the body from `SKILL/references/templates.md`:**
   - for decisions: **the words → the question → a story → what we found → what others do → choose**;
   - for person-only tasks: **why a person → what was tried → numbered steps with what you'll see → how to
     say done**.
3. **Research what others do,** with a web search: standards, well-known tools, papers. Lead with the best
   practice, then map your build onto it. Link the sources.
4. **Every body and comment you post starts** with the visible header `🤖 **Claude** (<project> build agent)`
   and contains `MARK`. Go straight from the header to the content: no apology or meta preamble
   ("Sorry, that was written for engineers…", "Here it is plainly"), even when rewriting.
   - The header lets the human tell your messages from theirs.
   - Your `gh` posts use their account, so `MARK` is the only way the watcher tells you apart.
5. **Create it:** title `Decision: …` or `Task: …`; labels `LABEL`, `needs:human` and the area/phase/type
   labels. `gh` can time out: search by title before retrying, and read the number and title back.
6. Add it to the tracking issue.

## Watch
```bash
REPO=owner/name LABEL=task-to-<owner> MARK='<!-- proj-agent -->' \
  bash SKILL/scripts/watch.sh STATE.json init           # snapshot; existing comments count as seen
REPO=… LABEL=… MARK=… bash SKILL/scripts/watch.sh STATE.json watch 110 120   # background job
```
- **What it does:** it polls every labelled issue, open and closed. It exits on the first `EVENT`: an
  unmarked comment, a close or reopen, or a label added or removed. With no event it exits after the window
  with `WATCH: no change`.
- **How to run it:** as a long background job (timeout above the window), never blocking on it. After you
  handle its events, start it again.
- **After you change a label or state yourself, re-run `init`** before restarting the watcher. GitHub search
  lags, so one harmless "no longer labelled" event can still appear: ignore it and restart.

## Handle a reply
Read the whole issue, then reply in the same issue, with the header and `MARK`:

| The human wrote… | You do |
|---|---|
| a question ("what is X?", "is this only a test?") | answer plainly: define the term, use a story; then re-offer the choice |
| "I don't understand" | rewrite the issue in the full template, after re-checking the code; no apology preamble |
| "what's the state? what do I decide?" | a short summary: what's settled, the one open choice, the options |
| "is this important?" | a one-line verdict first (urgent / useful / not needed) and exactly what it blocks or not; then the choice again with a **"later"** option added |
| a choice ("1", "option 1, plus 2 for later") | map it exactly onto the options; if ambiguous, ask one question |
| "done" / closed the issue (a task) | verify the effect (e.g. re-run what was blocked), confirm in the issue |
| feedback on format or process | apply it now, and **update this skill** (below) |

## After a decision
1. **Reply** `Recorded: option N`, then in plain words: what happens now, who builds it, what proves it.
2. **Relabel:** remove `LABEL` and `needs:human`, add `type:feature`/`type:chore`; then re-`init` the
   watcher.
3. **Keep the issue open** until the implementing PR closes it: the PR body has `Closes #N` and cites the
   reply's link. A draft PR built as evidence becomes ready, its title loses any "decision pending" prefix,
   and it joins the normal merge order.
4. **Follow-ups:** a "later" part of the choice becomes its own issue, linked both ways.
5. Update the tracking issue and your project memory.

## Review PRs with the human, a few at a time
When the human reviews PRs, keep **five** open for them at a time (their words: "give me next 5 PRs to review,
not only one or two"; they may ask for another number), in merge order (the bottom of each stack first). Open
each one as soon as it is verified: never hold ready PRs back for a slower one, and never leave the human with
fewer than five while verified PRs exist. Number each guide ("Review 6, 2 of 5 open now: #a → #b → #c") and say
which one must merge first when one is stacked on another:
- **Make it findable:** put the label `review:now` on exactly those PRs, and assign them to the human. GitHub's
  "Assigned to me" page then shows it, and so does `…/pulls?q=is:open+label:review:now`. Give both links.
- **Guide comment:** the approved template, shortened: the words, what the PR does as a story, what to check
  (minutes, not hours), how to answer. If every PR was opened from the human's own account (your `gh` uses
  it), GitHub disables **Approve**, so the answer is a comment: **merge**, or plain words.
- **Watch it:** `REPO=… MARK=… bash SKILL/scripts/watch-pr.sh STATE.json init`, then `… watch 100 90` in the
  background. It follows every open PR carrying `review:now`, and exits on a review, an unmarked comment
  or line comment, a PR leaving or joining the label.
- **Look ahead, but do not assign early.** While a set is under review, prepare the next one: pick it,
  trial-merge it against the default branch and the open set, run its checks, and write its guides, and hold
  them unposted. Do not label or assign it, so the human's list shows only what they are reviewing now. The moment
  they merge the current set, re-run the trial merge (the base moved), then label, assign and post the next set's
  guides at once, and start preparing the one after it. Fixes that other people must make (a refresh, a rework)
  are requested while the set is still under review, so the next set is ready on time.
- **Merged PRs stay watched for a while.** The human often comments on a PR after it merged. Pass the last few
  merged PR numbers as `EXTRA_PRS="70 89 119"` to `watch-pr.sh` (also to `init`), so their new comments are seen.
- **On "merge":** merge with the repo's method (merge commit if it says so), check that the base was right
  (retarget a stacked PR to the default branch once its base has merged). A "merge" on a PR whose base PR
  isn't merged yet waits until that one is. When the open set is done, open the next set the same way:
  label, assign, guides, `init`, restart the watcher.
- **Before every merge, read what it would close.** Run `gh pr view N --json closingIssuesReferences` on the
  PR you are about to merge (it targets the default branch by then, so the list is real: a stacked PR shows
  an empty list until its base merges). If it closes an issue while a PR of the same issue is still open above
  it in the stack, **hold the merge** and send the parent a `NEED:` naming the PR, the issue and the sentence
  that does it. A stack's description repeats "the top PR closes #N" in every layer, and GitHub reads that as a
  closing keyword when the first layer merges. The fix is in the body (write "closes issue N", with no `#`, on
  every layer but the top). The liaison cannot edit bodies or reopen issues. After a merge, check that the
  issues it closed are the ones you expected.
- **A recorded default that promises future work must point at an open issue.** When the human merges on a guide
  that said "default: X, later" (a test, a migration, a follow-up PR, a decision), record the defaults on the PR,
  and for each one that promises work check that an open issue exists (search before you file). If none does,
  file it: an engineering issue (phase and area labels, a link back to the merged PR) for build work, or a
  `Decision:` issue in the approved format when it needs the human's word (for example a change to a shared
  contract). Link it from the PR note and from the tracking issue, and tell the parent in a `NEED:` in the same
  turn. Work that belongs in an open PR (a test for the next part of a stack) goes to the parent as a `NEED:`
  naming the PR. Never write "I have asked" in a note before that `NEED:` is sent, and cite the issue that
  really holds the work (check its number and state first).
- **On anything else:** answer in the PR in plain words; change code only when asked, then say what changed.

## Delegate the liaison (keep the main agent's context clean)
When the main agent runs other work (e.g. a build with many delegates), hand this whole skill to **one**
liaison sub-agent: it runs both watchers, opens review sets, writes guides, merges on the human's word,
answers questions and keeps this skill current. It never edits code. It ends **every** turn with exactly one
line for its parent:
- `STATUS: waiting (open: #a #b; issues watched: N)` when nothing needs the parent;
- `NEED:` plus bullets, only for: a **product decision** the human took (issue, option, one line), a
  **change request** on a PR that needs code, a **merge conflict**, a **blocker**, or a **skill update**
  (version and rule).
The parent records product decisions in its own memory and routes code work; it stops its own watchers
first, so only one agent answers the human.

## Keep this skill current
When the human corrects or adds to how you work together in these issues (format, labels, header,
cadence, what to include), in the same session:
- edit this folder minimally (`SKILL.md`, `references/templates.md`, the forms);
- bump `metadata.version`: a patch for wording, a minor for a new rule;
- add a `CHANGELOG.md` line;
- run the repo's `scripts/validate.sh github-human-tasks` and commit.

Also update the repo's issue forms if it has them. Never record the human's private details here.

## Stop conditions
- **One watcher at a time.** Each run is bounded (default 110 min). You restart it yourself after handling
  events, and stop once no issue carries `LABEL`.
- **No duplicates:** one issue per decision. Before creating, search open and closed issues by title.
- **`gh` failures:** at most 3–4 retries per call with a pause, then report and move on. A failed poll is
  never treated as an event.
- **Never decide for the human** what you asked them, and never post secrets, tokens or real customer data.
  Use fictional tenants in stories.
