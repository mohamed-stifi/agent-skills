# Changelog — issue-driven-prs

## 1.1.0 — 2026-11-24
- **Challenge the tests before opening a PR:** someone other than the author breaks the changed code on
  purpose (mutation testing); only tests that catch the breaks count, and the PR body carries the report.
- Tests are named after the scenario's behavior, so they read as documentation.

## 1.0.0 — 2026-11-21
- First release: an issue first (Vocabulary, Behaviors as Given / When / Then, Why, Impact), a tracking issue
  with one sub-issue per PR or stack layer, scenarios mapped to tests in the PR body, `Closes` only when every
  scenario is covered, stack rules so a layer closes only its own issue, issue forms, and a two-line AGENTS.md
  pointer so repos do not copy the method.
