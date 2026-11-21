#!/usr/bin/env bash
# Checks on the skill's text: each test is a scenario of issue #8. usage: bash tests/skill-text.sh
set -uo pipefail
cd "$(dirname "$0")/.."
S=SKILL.md; R=references/pr-review.md
pass=0; fail=0
check() { if eval "$2"; then echo "ok   $1"; pass=$((pass+1)); else echo "FAIL $1"; fail=$((fail+1)); fi; }
count() { grep -c -F -- "$1" "$2" || true; }
desc=$(sed -n 's/^description: *//p' "$S")

check pr_review_mode_is_a_reference_file \
  '[ -f "$R" ] && grep -q "SKILL/references/pr-review.md" "$S" && ! grep -q "^## Review PRs.*a few at a time" "$S" && ! grep -q "closingIssuesReferences" "$S"'
check the_description_triggers_pr_review \
  'echo "$desc" | grep -q "PR review" && echo "$desc" | grep -q "give me PRs to review" && [ ${#desc} -le 450 ]'
check each_idea_is_stated_once \
  '[ "$(count "🤖 **Claude**" "$S")" = 1 ] && [ "$(count "Search open and closed issues" "$S")" = 1 ] && [ "$(count "minutes=110" "$S")" = 1 ] && [ "$(count "pinned" "$S")" = 1 ]'
check need_without_a_liaison \
  '[ "$(grep -n "NEED:" "$S" | head -1 | cut -d: -f1)" = "$(grep -n "\*\*Report\*\* =" "$S" | cut -d: -f1)" ] && ! grep -qiE "(send|tell) the parent" "$R" && ! grep -n "parent" "$R" | grep -v "without a liaison" | grep -q . && grep -q "Report" "$R"'
check self_update_targets_the_skills_repo \
  'sed -n "/^## Keep this skill current/,/^## /p" "$S" | grep -q "skills repo this folder comes from"'
check no_residue \
  '! grep -nE "give me next 5|authori[sz]ed|#[0-9]{2,}|decision pending|their words" "$S" "$R" && grep -q "default 5" "$R"'
check skill_md_is_half_its_size \
  '[ "$(wc -c < "$S")" -le 8000 ] && bash ../../scripts/validate.sh github-human-tasks >/dev/null'

echo "$pass passed, $fail failed"; [ "$fail" = 0 ]
