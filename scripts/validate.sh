#!/usr/bin/env bash
# Check every skill: frontmatter, version, changelog, size, and no personal paths/secrets. Runs in CI.
# usage: scripts/validate.sh [skill...]
set -uo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"
fail=0; err() { echo "ERROR $1"; fail=1; }; warn() { echo "warn  $1"; }
list=("$@"); ((${#list[@]})) || for d in skills/*/; do list+=("$(basename "$d")"); done
for s in "${list[@]}"; do
  f="skills/$s/SKILL.md"
  [ -f "$f" ] || { err "$s: missing SKILL.md"; continue; }
  fm="$(awk 'NR==1 && $0!="---"{exit} NR>1 && $0=="---"{exit} NR>1{print}' "$f")"
  [ -n "$fm" ] || { err "$s: SKILL.md must start with --- frontmatter ---"; continue; }
  name="$(echo "$fm" | sed -n 's/^name: *//p')"
  desc="$(echo "$fm" | sed -n 's/^description: *//p')"
  ver="$(echo "$fm" | sed -n -E 's/^ +version: *"?([^"]*)"?/\1/p')"
  [ "$name" = "$s" ] || err "$s: frontmatter name '$name' must equal the folder name"
  [[ "$name" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]] || err "$s: name must be lowercase-with-dashes"
  [ -n "$desc" ] || err "$s: description is empty"
  [ "${#desc}" -le 1024 ] || err "$s: description is ${#desc} chars (max 1024)"
  [[ "$ver" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || err "$s: metadata.version must be semver (x.y.z), got '$ver'"
  [ -f "skills/$s/CHANGELOG.md" ] || err "$s: missing CHANGELOG.md"
  grep -q "^## $ver" "skills/$s/CHANGELOG.md" 2>/dev/null || err "$s: CHANGELOG.md has no '## $ver' entry"
  lines=$(wc -l < "$f"); [ "$lines" -le 500 ] || warn "$s: SKILL.md is $lines lines (keep it under 500; move detail to references/)"
  while IFS= read -r big; do err "$s: file over 10 MB: $big"; done < <(find "skills/$s" -type f -size +10M)
  # privacy guard: personal absolute paths and things that look like real secrets
  hits="$(grep -rn -I -E '/Users/[A-Za-z0-9._-]+/|/home/[a-z0-9._-]+/|ghp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY' "skills/$s" | grep -v '/Users/<' || true)"
  [ -z "$hits" ] || { err "$s: personal path or secret-like string:"; echo "$hits" | cut -c1-160 | sed 's/^/        /'; }
  echo "ok    $s v$ver"
done
[ "$fail" = 0 ] && echo "ALL OK" || { echo "VALIDATION FAILED"; exit 1; }
