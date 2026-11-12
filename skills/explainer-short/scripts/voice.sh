#!/usr/bin/env bash
# Script -> voice.wav + timing.json + .srt, then register the video.  usage: voice.sh <studio-dir> <slug>
set -euo pipefail
STUDIO="${1:?usage: voice.sh <studio-dir> <slug>}"; SLUG="${2:?slug required}"
cd "$STUDIO"
uv run --project voice --quiet voice/make_voice.py "$SLUG"
node scripts/registry.mjs
