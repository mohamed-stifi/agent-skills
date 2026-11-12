#!/usr/bin/env bash
# Install skills (or bundles of skills) from this repo into one or more agents.
#
# usage: scripts/install.sh <skill|bundle>... [--agent NAME]... [--project DIR] [--copy] [--ref TAG] [--dir PATH]
#   <skill>        a folder in skills/            e.g. explainer-short
#   <bundle>       a file in bundles/<name>.txt   e.g. idea-to-video
#   all            every skill in skills/
#   --agent        claude (default) | opencode | codex | hermes | agents | all   (repeatable)
#   --project DIR  install into DIR/.claude/skills (etc.) instead of your home folder
#   --copy         copy files (default: symlink, so `git pull` here updates every agent = one source of truth)
#   --ref TAG      install a pinned version (implies --copy), e.g. --ref explainer-short/v1.1.0
#   --dir PATH     install into an explicit skills folder (any other agent)
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
names=(); agents=(); project=""; mode=link; ref=""; dirs=()
while (($#)); do
  case "$1" in
    --agent) agents+=("$2"); shift 2 ;;
    --project) project="$(cd "$2" && pwd)"; shift 2 ;;
    --copy) mode=copy; shift ;;
    --ref) ref="$2"; mode=copy; shift 2 ;;
    --dir) dirs+=("$2"); shift 2 ;;
    -h|--help) sed -n '2,14p' "$0"; exit 0 ;;
    *) names+=("$1"); shift ;;
  esac
done
((${#names[@]})) || { sed -n '2,14p' "$0"; exit 1; }
((${#agents[@]} + ${#dirs[@]})) || agents=(claude)

# expand bundles / "all"
skills=()
for n in "${names[@]}"; do
  if [ "$n" = all ]; then for d in "$REPO"/skills/*/; do skills+=("$(basename "$d")"); done
  elif [ -f "$REPO/bundles/$n.txt" ]; then while read -r s; do [[ -z "$s" || "$s" == \#* ]] || skills+=("$s"); done < "$REPO/bundles/$n.txt"
  elif [ -d "$REPO/skills/$n" ]; then skills+=("$n")
  else echo "unknown skill or bundle: $n  (see skills/ and bundles/)"; exit 1; fi
done

# agent -> skills folder
base="${project:-$HOME}"
for a in ${agents[@]+"${agents[@]}"}; do
  case "$a" in
    claude)   dirs+=("$base/.claude/skills") ;;
    opencode) [ -n "$project" ] && dirs+=("$base/.opencode/skills") || dirs+=("$HOME/.config/opencode/skills") ;;
    codex)    dirs+=("$base/.codex/skills") ;;
    hermes)   dirs+=("$HOME/.hermes/skills/agent-skills") ;;
    agents)   dirs+=("$base/.agents/skills") ;;
    all)      dirs+=("$base/.claude/skills" "$base/.codex/skills" "$base/.agents/skills") ;;
    *) echo "unknown agent: $a"; exit 1 ;;
  esac
done

for d in ${dirs[@]+"${dirs[@]}"}; do
  mkdir -p "$d"
  for s in "${skills[@]}"; do
    dest="$d/$s"
    if [ -e "$dest" ] || [ -L "$dest" ]; then
      if [ -L "$dest" ] || [ -f "$dest/.installed-from-agent-skills" ]; then rm -rf "$dest"
      else echo "SKIP $dest (exists and was not installed by this script; remove it yourself)"; continue; fi
    fi
    if [ -n "$ref" ]; then
      mkdir -p "$dest"; git -C "$REPO" archive "$ref" "skills/$s" | tar -x -C "$dest" --strip-components=2
      echo "$ref" > "$dest/.installed-from-agent-skills"
    elif [ "$mode" = copy ]; then
      cp -R "$REPO/skills/$s" "$dest"; git -C "$REPO" rev-parse --short HEAD > "$dest/.installed-from-agent-skills" 2>/dev/null || touch "$dest/.installed-from-agent-skills"
    else
      ln -s "$REPO/skills/$s" "$dest"
    fi
    v="$(grep -m1 -E '^\s+version:' "$REPO/skills/$s/SKILL.md" | sed -E 's/.*"?([0-9]+\.[0-9]+\.[0-9]+)"?.*/\1/')"
    echo "OK   $s v$v -> $dest ($([ -n "$ref" ] && echo "pinned $ref" || echo $mode))"
  done
done
