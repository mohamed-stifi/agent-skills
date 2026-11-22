#!/usr/bin/env bash
# Checks on the skill's text: each test is a scenario of issue #8 or #14. usage: bash tests/skill-text.sh
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
  '[ "$(count "🤖 **<your name>**" "$S")" = 1 ] && [ "$(count "Search open and closed issues" "$S")" = 1 ] && [ "$(count "minutes=110" "$S")" = 1 ] && [ "$(count "pinned" "$S")" = 1 ]'
check need_without_a_liaison \
  '[ "$(grep -n "NEED:" "$S" | head -1 | cut -d: -f1)" = "$(grep -n "\*\*Report\*\* =" "$S" | cut -d: -f1)" ] && ! grep -qiE "(send|tell) the parent" "$R" && ! grep -n "parent" "$R" | grep -v "without a liaison" | grep -q . && grep -q "Report" "$R"'
check preferences_are_kept_without_access_to_the_skills_repo \
  'sec=$(sed -n "/^## Remember the human/,/^## Stop/p" "$S"); echo "$sec" | grep -q "AGENTS.md" && echo "$sec" | grep -q "push access" && echo "$sec" | grep -q "once the human agrees"'
check any_agent_signs_its_posts \
  '! grep -rniE "\*\*Claude\*\*|build agent" "$S" references/ && [ "$(count "🤖 **<your name>** (<your role>)" references/templates.md)" = 4 ]'
check an_issue_waiting_on_the_human_is_assigned_and_labelled_needs_human \
  'grep -q "assign the human" "$S" && grep -q "label it \`needs:human\`" "$S" && ! grep -rn "task-to" "$S" references/ scripts/'
check a_decision_hands_the_issue_back \
  'grep -q "remove \`needs:human\`, unassign the human" "$S" && grep -q "unassigned you" references/templates.md'
check replies_need_no_lookup_table \
  'sec=$(sed -n "/^## Handle a reply/,/^## After/p" "$S"); ! echo "$sec" | grep -q "^|" && [ "$(echo "$sec" | wc -l)" -le 5 ]'
check no_residue \
  '! grep -nE "give me next 5|authori[sz]ed|#[0-9]{2,}|decision pending|their words" "$S" "$R" && grep -q "default 5" "$R"'
check skill_md_is_half_its_size \
  '[ "$(wc -c < "$S")" -le 8000 ] && bash ../../scripts/validate.sh github-human-tasks >/dev/null'

echo "$pass passed, $fail failed"; [ "$fail" = 0 ]
