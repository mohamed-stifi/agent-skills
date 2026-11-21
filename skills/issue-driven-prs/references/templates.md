# Templates

Plain words, short sections. Write for a reviewer who did not do the work.

## Change issue (one PR)

```markdown
## Vocabulary
- **<Principal term>**: <one sentence>.
  - **<Sub-term>**: <one sentence>.
  - **<Sub-term>**: <one sentence>.

## Behaviors
**Scenario: <name, becomes the test name>**
- Given <state>
- When <action>
- Then <observable result>

**Scenario: <a failure or refusal case>**
- Given <state>
- When <action>
- Then <observable result>

## Why
<The problem today, who has it, what happens if nothing is done.>

## Impact
- **Changes**: <files, APIs, data, settings>.
- **Who**: <users, teams, people who upgrade>.
- **Not changed**: <what deliberately stays the same>.
- **Risk / migration**: <if any>.
```

## Tracking issue (several PRs, a theme branch or a stack)

```markdown
## Vocabulary
- **<Principal term>**: <one sentence>.
  - **<Sub-term>**: <one sentence>.

## Plan
One sub-issue per PR, in merge order:
- [ ] #<n> <part 1>
- [ ] #<n> <part 2>
- [ ] #<n> <part 3>

## Why
<The problem as a whole.>

## Impact
<What changes overall, for whom, what does not.>
```

Each sub-issue is a change issue, with `Part of #<tracking>` at the top of its Impact.

## PR body (one PR)

```markdown
Closes #<n>            <!-- or "Part of #<n>" when some scenarios stay open -->

## What
<What changed, in the issue's words.>

## Scenarios covered
| Scenario | Test |
|---|---|
| <name> | `<file>::<test name>` |

## Not covered
- <scenario>: <reason>; stays open in #<n> (or moved to #<m>).
```

## PR body (a layer of a stack)

```markdown
Closes #<this layer's sub-issue>
Part of #<tracking>

## What
## Scenarios covered
| Scenario | Test |
|---|---|

## Merge order
Layer <k> of <total>: merge after the PR for issue <n>, without "#" in notes like this one.
```

## AGENTS.md pointer (paste into a repo)

```markdown
## Issue first
Before any change that will become a pull request, use the `issue-driven-prs` skill: open (or find) the issue
with Vocabulary, Behaviors (Given / When / Then), Why and Impact, then open PRs that close it.
```
