#!/usr/bin/env bash
# Create (or reopen) the workspace for one product. Safe to re-run: it never overwrites your scenes.
# usage: setup.sh "<product name>" [--format 16:9|9:16|1:1] [--slug name]
# env  : PROMO_HOME (default ~/.product-promo-videos) · KOKORO_MODELS=<dir with the 2 model files> to skip the download
# Prints WORKSPACE=<path> and READY on success.
source "$(dirname "$0")/_lib.sh"
PRODUCT="${1:-}"; shift || true
FORMAT="16:9"; SLUG=""
while [ $# -gt 0 ]; do case "$1" in
  --format) FORMAT="$2"; shift 2;; --slug) SLUG="$2"; shift 2;; *) echo "unknown option $1"; exit 1;; esac; done

missing=()
for t in node npm npx ffmpeg ffprobe uv git curl; do command -v "$t" >/dev/null || missing+=("$t"); done
if ((${#missing[@]})); then
  echo "MISSING TOOLS: ${missing[*]}"
  echo "Install: node 18+ (nodejs.org), ffmpeg (ffmpeg.org / brew / apt / winget), uv (docs.astral.sh/uv), git, curl."
  exit 1
fi

CWD="$(pwd -P)"
KEY="$(printf '%s' "$CWD" | sed -E 's#[/\\:]+#-#g')"
if [ -z "$SLUG" ]; then
  SLUG="$(printf '%s' "$PRODUCT" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g')"
  [ -n "$SLUG" ] || SLUG="session-$(date +%Y%m%d-%H%M)"
fi
WS="$PROMO_HOME/$KEY/$SLUG"
mkdir -p "$WS"
cd "$WS"

if [ ! -f .promo.env ]; then
  echo "[1/6] new workspace $WS"
  cp -R "$SKILL/template/source" source
  cp "$SKILL/template/brief.md" "$SKILL/template/STORYBOARD.md" .
  sed "s#{{PRODUCT}}#${PRODUCT:-$SLUG}#g; s#{{CWD}}#$CWD#g; s#{{SLUG}}#$SLUG#g" "$SKILL/template/README.md" > README.md
  cp "$SKILL/template/gitignore" .gitignore
  mkdir -p output output-extras reports
  printf '# Reports\nOne file per role (references/roles.md), each <= 40 lines.\n' > reports/README.md
  case "$FORMAT" in
    16:9) W=1920; H=1080;; 9:16) W=1080; H=1920;; 1:1) W=1080; H=1080;; *) echo "format must be 16:9, 9:16 or 1:1"; exit 1;;
  esac
  sed -i.bak -E "s/^export const W = [0-9]+;/export const W = $W;/; s/^export const H = [0-9]+;/export const H = $H;/" source/src/kit/tokens.ts
  NAME_UP="$(printf '%s' "${PRODUCT:-$SLUG}" | tr '[:lower:]' '[:upper:]')"
  sed -i.bak "s#name: 'PRODUCT'#name: '${NAME_UP//\'/}'#" source/src/kit/tokens.ts && rm -f source/src/kit/tokens.ts.bak
  { echo "PRODUCT='${PRODUCT//\'/}'"; echo "SLUG='$SLUG'"; echo "CWD='$CWD'"; echo "FORMAT='$FORMAT'"; echo "CREATED='$(date +%F)'"; } > .promo.env
else
  echo "[1/6] workspace exists, keeping your files: $WS"
fi

echo "[2/6] npm packages"
[ -d source/node_modules/remotion ] || (cd source && npm install --no-audit --no-fund --loglevel=error)

echo "[3/6] voice model (Kokoro-82M, shared cache $PROMO_MODELS)"
mkdir -p "$PROMO_MODELS"
for f in kokoro-v1.0.onnx voices-v1.0.bin; do
  if [ ! -s "$PROMO_MODELS/$f" ]; then
    if [ -n "${KOKORO_MODELS:-}" ] && [ -s "$KOKORO_MODELS/$f" ]; then cp "$KOKORO_MODELS/$f" "$PROMO_MODELS/"
    else curl -L --fail -o "$PROMO_MODELS/$f" "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/$f"; fi
  fi
done

echo "[4/6] python env for the audio"
uv sync --project source/audio --quiet || { rm -rf source/audio/.venv; uv sync --project source/audio --quiet; }

echo "[5/6] headless browser for rendering"
(cd source && npx remotion browser ensure >/dev/null)

echo "[6/6] git"
[ -d .git ] || git init -q
git add -A >/dev/null && git -c user.name="${GIT_AUTHOR_NAME:-promo-video}" -c user.email="${GIT_AUTHOR_EMAIL:-promo-video@localhost}" \
  commit -qm "setup" >/dev/null 2>&1 || true
echo "WORKSPACE=$WS"
echo "READY"
