---
name: issue-driven-prs
description: Start every pull request from a GitHub issue written first - Vocabulary (the principal term and its sub-terms), Behaviors (Given / When / Then scenarios), Why and Impact - split big work into a tracking issue with one sub-issue per PR or stack layer, link each PR with Closes #n and the test that proves each scenario, and keep stacked PRs from closing the wrong issue. Use before any code, docs or config change that will become a PR in a GitHub repo; when asked to "open an issue first", "write the spec issue", "plan this as issues", "make a tracking issue"; when the repo's AGENTS.md says issue first; or when opening, stacking or merging PRs that close issues.
metadata:
  version: "1.1.0"
  author: mohamed-stifi
---

# Issue-driven PRs (an issue first, then PRs that close it)

Every PR starts from an issue that says, before any code, **what** will change, **why**, and **how we will
know it works**. People agree on the what in the issue; review of the PR is then about the how. `SKILL` = this
folder. `REPO` = `owner/name`.

## When to use, and when not
- **Use** before the first commit of any change that will end in a PR: a feature, a fix, docs, a refactor, a
  dependency, a config change.
- **An issue already exists?** Use it. Add the sections it lacks before you start.
- **A choice only a person can make** (product, money, an account, their identity): ask them. With the
  `github-human-tasks` skill that is a `Decision:` or `Task:` issue; link it from the change issue and wait.
- **More work found inside an open PR's scope:** update that PR's issue (its scenarios), don't open another.

## 1. Size the change
- **Fits in one PR** (one purpose, reviewable in one sitting): one **change issue**.
- **Needs several PRs**, a theme branch or a stack: a **tracking issue** that lists one **sub-issue** per PR
  as a task list (`- [ ] #n`). The tracking issue holds the shared vocabulary, the overall why and impact;
  each sub-issue has its own four sections, narrowed to its PR.
- **Search first**, open and closed: `gh issue list -R REPO --state all --search "<words> in:title"`.

## 2. Read before you write
- Read the code for what it does **today**; never copy a spec's or an old issue's claim about behavior.
- Collect the words the repo already uses (README, glossary, ADRs, API contracts, schemas). You will reuse them.

## 3. Write the issue
Use `SKILL/references/templates.md`. Four sections, in this order:
1. **Vocabulary.** The principal term the change is about, in one sentence; then each sub-term it relies on,
   one sentence each. Reuse a word the repo already defines; never coin a synonym for it. Define every word a
   reviewer might ask about. These exact words then appear in code, tests, docs and the PR.
2. **Behaviors.** One scenario per behavior: `Scenario: <name>`, then Given (state), When (action), Then
   (observable result). Include failures, refusals and edge cases, not only the happy path. A Then says what
   someone can observe, not how the code does it. Each scenario name becomes a test name.
3. **Why.** The problem today, who has it, and what happens if nothing is done.
4. **Impact.** What changes and for whom (users, APIs, data, settings, security, other teams, people who
   upgrade), what deliberately does not, and any migration or risk.

Title: the change in plain words. Labels: the repo's own (type, area). Unsure about a behavior? Ask before you
write the code, not after.

## 4. Create it
```bash
gh issue create -R REPO --title "<the change>" --label <labels> --body-file issue.md
```
- `gh` can time out: search by title before retrying, and read the number back.
- **Tracking issue:** create the sub-issues first, then the tracking issue with their numbers in its task
  list (or create it first and edit the list in). Link each sub-issue to it in its Impact section.

## 5. Branch, commit, open the PR
- Branch and commit with the repo's conventions. In commit messages write `Part of #n` or `Refs #n`: a
  closing keyword in a commit closes the issue when that commit reaches the default branch.
- **Scenarios → tests, before opening.** Each scenario the PR covers maps to a test that proves it, named
  after the behavior, so the tests read as the documentation of what the code does. A scenario it does not
  cover is listed with the reason.
- **Challenge the tests, before opening.** A test that passes may still check nothing. Have a separate agent
  or reviewer (not the author) break the changed code on purpose: flip a condition, change a boundary, remove
  a call, return a wrong value. Then run the tests, with the language's mutation tool when there is one
  (Stryker, mutmut, PIT, cargo-mutants). Only tests that catch the breaks count. Each break that no test
  catches gets a test, or a reason in the PR.
- **PR body** (template in `SKILL/references/templates.md`): `Closes #n` when the PR covers **every**
  scenario of the issue; `Part of #n` when some stay open (they stay in the issue, with the reason, or move to
  a new issue you link). Then the scenarios covered, each with its test, and the mutation report (breaks tried, caught, not caught).

## 6. Stacks: each layer closes only its own issue
GitHub closes an issue when a PR merges into the default branch with `closes`, `fixes` or `resolves` (any
case, any tense) followed by `#n` **anywhere in its body**, notes included.
- Each layer's body: `Closes #<its own sub-issue>` and `Part of #<tracking>`. Nothing else with a closing word.
  Merge-order notes say "issue 31" or "#31's PR", never "the top PR closes #31".
- The top layer may also close the tracking issue, but only if every other sub-issue will be closed by then;
  otherwise close the tracking issue by hand when the last one closes.
- **Before each merge:** `gh pr view N -R REPO --json closingIssuesReferences`. The list is real only once the
  PR targets the default branch (a stacked PR shows `[]` until its base merges) and GitHub computes it lazily
  after a retarget: read it again before trusting an empty list. A top PR whose own `Closes` still is not
  listed: re-save its body unchanged (`gh pr view N --json body --jq .body > f && gh pr edit N --body-file f`).
  If it would close an issue another open PR owns, fix that body first.
- **After each merge:** retarget the next layer to the default branch if its base branch is gone, check the
  issues that closed are the expected ones, and tick the line in the tracking issue.

## 7. During review
- Review changes what the code must do: **update the issue's scenarios first**, say so in a PR comment, then
  change the code and the tests.
- Review asks for something outside the issue: a new issue, linked, not scope creep in this PR.

## 8. Adopt it in a repo
Add the two-line pointer from `SKILL/references/templates.md` to the repo's `AGENTS.md` (or `CLAUDE.md`), so
every assistant loads this skill instead of carrying the whole method in each repo. Optionally copy
`SKILL/references/forms/*.yml` into `.github/ISSUE_TEMPLATE/` (they show on GitHub's "New issue" page once on
the default branch).

## Stop conditions
- **One issue per change**, no duplicates: search before creating.
- **Never post** secrets, tokens, internal hostnames or real customer data in an issue or a PR; use invented
  examples in scenarios.
- **`gh` failures:** at most 3–4 retries per call with a pause, then report and move on.
- **Never invent agreement:** if a behavior is uncertain, it is a question in the issue, not a scenario.
