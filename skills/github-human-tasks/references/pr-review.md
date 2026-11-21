# Review PRs with the human

Read this when the human reviews PRs. `SKILL`, `REPO`, `MARK`, the post header and **Report** are defined in
`SKILL.md`.

## The open set
Keep N verified PRs open for review (default 5, or the number the human asks for), in merge order (the bottom
of each stack first). Open each one as soon as it is verified: never hold ready PRs back for a slower one, and
never leave the human with fewer than N while verified PRs exist.
- **Make it findable:** label exactly those PRs `review:now` and assign them to the human. Give both links:
  GitHub's "Assigned to me" page and `https://github.com/REPO/pulls?q=is:open+label:review:now`.
- **Guide comment** on each PR: the approved template, shortened: the words, what the PR does as a story, what
  to check (minutes, not hours), how to answer. Number it ("Review 6, 2 of 5 open now: #a → #b → #c") and say
  which must merge first when one is stacked on another. If every PR was opened from the human's own account
  (your `gh` uses it), GitHub disables **Approve**, so the answer is a comment: **merge**, or plain words.
- **Look ahead, but do not assign early:** while a set is under review, pick the next one, trial-merge it
  against the default branch and the open set, run its checks and write its guides, all unposted, unlabelled
  and unassigned, so the human's list shows only what they review now. When the current set merges, re-run
  the trial merge (the base moved), then label, assign and post at once, and start on the set after it. Ask
  others for fixes (a refresh, a rework) while the set is still under review, so the next set is ready on time.

## Watch it
```bash
export REPO=owner/name MARK='<!-- proj-agent -->' EXTRA_PRS="70 89 119"   # the last few merged PRs
bash SKILL/scripts/watch-pr.sh STATE.json init
bash SKILL/scripts/watch-pr.sh STATE.json watch   # background job; args [minutes=100] [poll seconds=90]
```
It follows every open PR labelled `review:now`, plus `EXTRA_PRS` (the human often comments after a merge), and
exits on a review, an unmarked comment or line comment, or a PR leaving or joining the label. Exit 3 means
every poll failed. `init` keeps comments not yet reported, so re-run it whenever the set or `EXTRA_PRS` changes.

## Merging
- **On "merge":** check the PR's base is right, then merge with the repo's method (a merge commit if it says
  so). A "merge" on a PR whose base PR isn't merged yet waits for that one; once a base merges, retarget the
  PR above it to the default branch.
  When the set is done, open the next the same way: label, assign, guides, `init`, restart the watcher.
- **Before every merge, read what it would close:** `gh pr view N --json closingIssuesReferences`. The list is
  real only once the PR targets the default branch, and GitHub fills it lazily after a retarget: read an empty
  list again before trusting it. If the PR would close an issue whose own PR is still open higher in the
  stack, **hold the merge** and report the PR, the issue and the sentence that does it. The cure is in that
  body ("closes issue N", without `#`, on every layer but the top). The liaison never edits PR bodies (except
  the re-save below) or reopens issues; without a liaison, fix the body yourself.
- **After a merge,** check that the issues it closed are the ones you expected.
- **A stack top whose own `Closes #N` is still not listed** after it retargeted: re-save its body unchanged
  (`gh pr view N --json body --jq .body > f && gh pr edit N --body-file f`; never change its text), then
  read the list again and fix your guide's "closes" sentence. Still empty: report it, and after the merge
  the parent (without a liaison, you) closes the issue by hand.

## Defaults that promise work
When the human merges on a guide that said "default: X, later" (a test, a migration, a follow-up PR, a
decision), record the defaults on the PR. For each that promises work, find the open issue that holds it
(search first; check its number and state). None: file one, an engineering issue (phase and area labels, a
link to the merged PR) or a `Decision:` issue when it needs the human, link it from the PR note and the
tracking issue, and report it in the same turn. Work that belongs in an open PR (a test for the next layer of
a stack) is reported naming that PR. Never write "I have asked" before the report is sent.

## Anything else
Answer in the PR in plain words; change code only when asked, then say what changed.
