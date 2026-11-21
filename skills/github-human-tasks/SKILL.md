---
name: github-human-tasks
description: Route decisions and tasks only a person can do (accounts, payments, identity) to the human as GitHub issues, watch them, and act on their replies; also run PR review sets with them. Use when blocked on the human in a GitHub repo, when asked to "ask me in an issue", "watch my replies" or "give me PRs to review", when a task-to-<name> or review:now label is named, or when replying in such an issue.
metadata:
  version: "2.0.0"
  author: mohamed-stifi
---

# GitHub human tasks

The human reads and answers on GitHub, not in the terminal: you open the issue, watch it, act on the reply and
close the loop. `SKILL` = this folder. `REPO` = `owner/name`. `LABEL` = `task-to-<owner>` (e.g.
`task-to-mohamed`). `MARK` = `<!-- <project>-agent -->`. **Report** = a `NEED:` line to your parent when you
run as the liaison (see Delegate), otherwise a message to the user.

**Every post** (issue, comment, PR note) starts with `🤖 **Claude** (<project> build agent)`, contains `MARK`
and goes straight to the content, with no apology or meta preamble. The header tells the human your posts from
theirs; `MARK` is the watcher's only way to, since `gh` posts as them.

## When to use, and when not
- **Use** only when truly blocked on the human: a product choice the specs leave open, or a task needing their
  account, money, identity or machine.
- **First try to unblock yourself** (`gh`, a tunnel such as `cloudflared`, a local model, an installer or CLI)
  and say in the issue what you tried.
- **Don't** open issues for engineering choices with a sensible default: take it, flag it in the PR ("defaulted, review").
- **Never** write local Markdown guides for the human: every guide is an issue.

## Setup (once per repo)
```bash
gh label create "$LABEL" --color D93F0B --description "Waiting on <owner>" --force
gh label create needs:human --color FBCA04 --force
```
- **Tracking issue:** one pinned issue lists every human issue with its status (open, decided, built, PR).
  Update it whenever an issue opens, is decided or spawns a follow-up.
- **Issue forms (optional):** copy `SKILL/references/forms/*.yml` to `.github/ISSUE_TEMPLATE/` and replace
  `task-to-OWNER` with `LABEL`; they show on GitHub's "New issue" page once on the default branch.

## Open an issue
1. **Verify first:** read the code for what it does today (never trust an issue's or spec's claim), and check
   the spec's meaning of every value you mention (is 5 the most or the least critical?).
2. **Research what others do** with a web search (standards, well-known tools, papers): lead with the best
   practice, then map your build onto it, with links.
3. **Write the body from `SKILL/references/templates.md`:** a decision is the words → the question → a story →
   what we found → what others do → choose; a person-only task is why a person → what was tried → numbered
   steps with what you'll see → how to say done.
4. **Create it:** title `Decision: …` or `Task: …`; labels `LABEL`, `needs:human` and the area/phase/type
   labels. Search open and closed issues by title first (one issue per decision), and again before retrying a
   create that timed out; read the number back.

## Watch
```bash
export REPO=owner/name LABEL=task-to-<owner> MARK='<!-- proj-agent -->'
bash SKILL/scripts/watch.sh STATE.json init    # first run: existing comments count as seen
bash SKILL/scripts/watch.sh STATE.json watch   # background job; args [minutes=110] [poll seconds=120]
```
- It polls every labelled issue, open and closed, and exits on the first `EVENT` (an unmarked comment, a close
  or reopen, the label added or removed), or after the window with `WATCH: no change`. Exit 3 (`WATCH: every
  poll failed` and the error) means broken, not quiet.
- Run it as a long background job (timeout above the window), never blocking; restart it after its events.
- After you change a label or state yourself, re-run `init`: it adopts your change and keeps every reply not
  yet reported. One "no longer labelled" event from GitHub's search lag is harmless: restart.

## Handle a reply
Read the whole issue, then reply in it:

| The human wrote… | You do |
|---|---|
| a question ("what is X?", "is this only a test?") | answer plainly: define the term, use a story; then re-offer the choice |
| "I don't understand" | re-check the code, then rewrite the issue in the full template |
| "what's the state? what do I decide?" | a short summary: what's settled, the one open choice, the options |
| "is this important?" | a one-line verdict first (urgent / useful / not needed) and exactly what it blocks or not; then the choice again with a **"later"** option added |
| a choice ("1", "option 1, plus 2 for later") | map it exactly onto the options; if ambiguous, ask one question |
| "done" / closed the issue (a task) | verify the effect (e.g. re-run what was blocked), confirm in the issue |
| feedback on format or process | apply it now, and update this skill (below) |

## After a decision
1. **Reply** with the "Recording a decision" template: `Recorded: option N`, what happens now, who builds it,
   what proves it. Record it in your project notes or memory, if you keep them.
2. **Relabel:** remove `LABEL` and `needs:human`, add `type:feature`/`type:chore`; re-run `init`.
3. **Keep the issue open** until the implementing PR closes it (`Closes #N`, citing the reply's link). A draft
   PR built as evidence becomes ready, drops any "pending" mark from its title and joins the merge order. With
   the `issue-driven-prs` skill, the build work gets its own change issue, which links to this one.
4. **Follow-ups:** a "later" part of the choice becomes its own issue, linked both ways.

## Review PRs with the human
When the human reviews PRs, read `SKILL/references/pr-review.md` and follow it: open sets of N (default 5)
labelled `review:now`, a guide per PR, the PR watcher, merging on their word, and what to check before a merge.

## Delegate the liaison (keep the main agent's context clean)
When the main agent runs other work (e.g. a build with many delegates), hand this whole skill to **one**
liaison sub-agent: it runs both watchers, opens review sets, writes guides, merges on the human's word,
answers questions and keeps this skill current. It never edits code. It ends **every** turn with one line:
- `STATUS: waiting (open: #a #b; issues watched: N)` when nothing needs the parent;
- `NEED:` plus bullets, only for a **product decision** the human took (issue, option, one line), a **change
  request** on a PR that needs code, a **merge conflict**, a **blocker**, or a **skill update** (version, rule).

The parent records product decisions in its own memory, routes code work, and stops its own watchers first, so
only one agent answers the human.

## Keep this skill current
When the human corrects or adds to how you work together here (format, labels, header, cadence, what to
include), in the same session and in the skills repo this folder comes from (not the project you work in):
edit minimally (`SKILL.md`, `references/`, the forms); bump `metadata.version` (patch for wording, minor for a
new rule) and add a `CHANGELOG.md` entry; run that repo's `scripts/validate.sh github-human-tasks` and commit.
Also update the project's copied issue forms, if any. Never record the human's private details here.

## Stop conditions
- **One watcher of each kind at a time.** Each run is bounded; stop once no issue carries `LABEL` and no PR
  carries `review:now`.
- **`gh` failures:** at most 3–4 retries per call with a pause, then report and move on.
- **Never decide for the human** what you asked them; never post secrets, tokens or real customer data; use
  fictional tenants in stories.
