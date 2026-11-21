#!/usr/bin/env bash
# Checks on the issue forms and templates: each test is a scenario of issue #9. usage: bash tests/forms.sh
set -uo pipefail
cd "$(dirname "$0")/../references"
DEC=forms/decision.yml; TASK=forms/human-task.yml; TPL=templates.md
pass=0; fail=0
check() { if eval "$2"; then echo "ok   $1"; pass=$((pass+1)); else echo "FAIL $1"; fail=$((fail+1)); fi; }
# required FILE ID: the form field with this id has `required: true` (plain text, no YAML library needed)
required() { python3 -c 'import re,sys
blocks = re.split(r"\n  - type: ", open(sys.argv[1]).read())
sys.exit(0 if any(re.search(r"\n    id: %s\n" % sys.argv[2], b) and "required: true" in b for b in blocks) else 1)' "$1" "$2"; }

check a_form_sets_the_title_prefix \
  'grep -qx "title: \"Decision: \"" "$DEC" && grep -qx "title: \"Task: \"" "$TASK"'
check forms_carry_no_projects_words \
  '! grep -nE "D-03|E-26|policy-plane|FactSet|cassette|[Kk]ill switch" "$DEC" "$TASK"'
check forms_and_templates_use_the_same_headings \
  'grep -q "label: When it'"'"'s done" "$TASK" && grep -q "^### When it'"'"'s done" "$TPL" && required "$DEC" found && grep -q "^### What we found" "$TPL"'
check templates_state_the_header_rule_once \
  'sed -n "1,6p" "$TPL" | grep -q "SKILL.md" && ! grep -qi "apology" "$TPL"'

echo "$pass passed, $fail failed"; [ "$fail" = 0 ]
