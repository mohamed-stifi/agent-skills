#!/usr/bin/env bash
# Scaffold a new skill.  usage: scripts/new-skill.sh <name> "<one-line: what it does + when to use it>"
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
name="${1:?usage: new-skill.sh <name> \"<description>\"}"; desc="${2:?description required}"
[[ "$name" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]] || { echo "name: lowercase-with-dashes"; exit 1; }
d="$REPO/skills/$name"; [ -e "$d" ] && { echo "exists: $d"; exit 1; }
mkdir -p "$d/references" "$d/scripts"
cat > "$d/SKILL.md" <<MD
---
name: $name
description: $desc
metadata:
  version: "0.1.0"
  author: mohamed-stifi
---

# ${name}

## When to use

## Steps
1.

## Stop conditions
MD
printf '# Changelog — %s\n\n## 0.1.0 — %s\n- First draft.\n' "$name" "$(date +%F)" > "$d/CHANGELOG.md"
echo "created $d — edit SKILL.md, then: scripts/validate.sh $name"
