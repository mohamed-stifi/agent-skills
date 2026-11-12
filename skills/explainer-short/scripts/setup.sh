#!/usr/bin/env bash
# One-time setup of a video studio (safe to re-run: it skips what is already done).
# usage: setup.sh <studio-dir>
# Optional env: KOKORO_MODELS=<dir with kokoro-v1.0.onnx + voices-v1.0.bin> to avoid re-downloading (~340 MB).
set -euo pipefail
STUDIO="${1:?usage: setup.sh <studio-dir>}"
SKILL="$(cd "$(dirname "$0")/.." && pwd)"

missing=()
for t in node npm npx ffmpeg ffprobe uv; do command -v "$t" >/dev/null || missing+=("$t"); done
if ((${#missing[@]})); then
  echo "MISSING TOOLS: ${missing[*]}"
  echo "Install: node 18+ (nodejs.org or 'brew install node'), ffmpeg ('brew install ffmpeg' / 'apt install ffmpeg'),"
  echo "         uv ('curl -LsSf https://astral.sh/uv/install.sh | sh'). Then re-run this script."
  exit 1
fi

mkdir -p "$STUDIO"
STUDIO="$(cd "$STUDIO" && pwd)"
if [ ! -f "$STUDIO/package.json" ]; then
  echo "[1/5] copying template -> $STUDIO"
  cp -R "$SKILL/template/." "$STUDIO/"
else
  echo "[1/5] studio exists; refreshing kit + scripts only"
  cp -R "$SKILL/template/src/kit/." "$STUDIO/src/kit/"
  cp -R "$SKILL/template/scripts/." "$STUDIO/scripts/"
  cp "$SKILL/template/voice/make_voice.py" "$STUDIO/voice/"
fi
cd "$STUDIO"

echo "[2/5] npm packages"
[ -d node_modules/remotion ] || npm install --no-audit --no-fund --loglevel=error

echo "[3/5] voice model (Kokoro-82M, local)"
mkdir -p voice/models
for f in kokoro-v1.0.onnx voices-v1.0.bin; do
  if [ ! -s "voice/models/$f" ]; then
    if [ -n "${KOKORO_MODELS:-}" ] && [ -s "$KOKORO_MODELS/$f" ]; then cp "$KOKORO_MODELS/$f" voice/models/
    else curl -L --fail -o "voice/models/$f" "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/$f"; fi
  fi
done

echo "[4/5] python env for the voice"
uv sync --project voice --quiet || { echo "  venv broken -> recreating"; rm -rf voice/.venv; uv sync --project voice --quiet; }

echo "[5/5] headless browser for rendering"
npx remotion browser ensure >/dev/null

node scripts/registry.mjs >/dev/null
echo "READY: $STUDIO"
