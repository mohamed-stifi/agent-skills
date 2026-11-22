#!/usr/bin/env bash
# Check what demo-video needs; with no flag, also fetch the voice model files (once, ~340 MB, shared cache).
# usage: setup.sh [--check]      --check: report only, download nothing (exit 1 if anything is missing)
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
MODELS="${KOKORO_MODELS:-$HOME/.cache/kokoro}"
check=0; [ "${1:-}" = --check ] && check=1
bad=0

missing=()
for t in ffmpeg ffprobe uv vhs jq git; do command -v "$t" >/dev/null || missing+=("$t"); done
if ((${#missing[@]})); then
  echo "MISSING tools: ${missing[*]}  ->  brew install ${missing[*]}"; bad=1
else
  echo "ok   tools: ffmpeg ffprobe uv vhs jq git"
fi

need=()
for f in kokoro-v1.0.onnx voices-v1.0.bin; do [ -s "$MODELS/$f" ] || need+=("$f"); done
if ((${#need[@]})); then
  if ((check)); then
    echo "MISSING voice model in $MODELS: ${need[*]} (run setup.sh without --check to download ~340 MB)"; bad=1
  else
    mkdir -p "$MODELS"
    for f in "${need[@]}"; do
      echo "downloading $f -> $MODELS"
      curl -L --fail --progress-bar -o "$MODELS/$f.part" \
        "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/$f" \
        && mv "$MODELS/$f.part" "$MODELS/$f" || { echo "FAILED to download $f"; bad=1; }
    done
  fi
fi
[ "$bad" = 0 ] && echo "ok   voice model: $MODELS"

if command -v uv >/dev/null && ((!check)); then
  bash "$HERE/run.sh" -c "import PIL, kokoro_onnx, soundfile" && echo "ok   python env (Pillow, kokoro-onnx, soundfile)" \
    || { echo "FAILED to prepare the python env (see the error above)"; bad=1; }
fi
if command -v uv >/dev/null && ((!check)); then      # the browser for `browser` scenes (~100 MB, once)
  bash "$HERE/run.sh" -m playwright install chromium >/dev/null && echo "ok   browser (Playwright Chromium)" \
    || { echo "FAILED to install the Playwright browser"; bad=1; }
fi
exit "$bad"
