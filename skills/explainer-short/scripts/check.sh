#!/usr/bin/env bash
# Cue lint + typecheck + check frames + contact sheet.
# usage: check.sh <studio-dir> <slug> [sec,sec,...]   (extra seconds are ADDED to the default frames)
set -euo pipefail
STUDIO="${1:?usage: check.sh <studio-dir> <slug> [sec,sec,...]}"; SLUG="${2:?slug required}"
cd "$STUDIO"
node scripts/registry.mjs >/dev/null
node scripts/cues.mjs "$SLUG" || { echo "Fix the cues above (use a word from the printed list), then re-run check.sh"; exit 1; }
ERR="$(npx tsc --noEmit -p . 2>&1 | grep -E "src/(videos/$SLUG|kit)/" || true)"
if [ -n "$ERR" ]; then echo "$ERR" | head -30; echo "TYPE ERRORS above - fix them, then re-run check.sh"; exit 1; fi
node scripts/stills.mjs "$SLUG" "${3:-}" 2>&1 | grep -v -E "webpack|PackFileCacheStrategy|snapshot" || true
