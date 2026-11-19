# Shared helpers. Sourced by the other scripts.
set -euo pipefail
SKILL="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROMO_HOME="${PROMO_HOME:-$HOME/.product-promo-videos}"
export PROMO_MODELS="${PROMO_MODELS:-$PROMO_HOME/.cache/kokoro}"

need_ws() {
  WS="${1:?usage: $(basename "$0") <workspace> ...}"
  WS="$(cd "$WS" && pwd -P)"
  [ -f "$WS/.promo.env" ] || { echo "not a promo workspace (no .promo.env): $WS"; exit 1; }
  # shellcheck disable=SC1091
  . "$WS/.promo.env"
  SRC="$WS/source"
}

# film ids declared in source/src/films.ts  ({ id: 'promo-60s', ... })
film_ids() { sed -n -E "s/.*\{ *id: *'([^']+)'.*/\1/p" "$SRC/src/films.ts"; }

dur_of() { ffprobe -v error -show_entries format=duration -of csv=p=0 "$1" 2>/dev/null || echo 0; }

render_one() { # id outfile [extra remotion args...]
  local id="$1" out="$2"; shift 2
  local tries=0
  until (cd "$SRC" && npx remotion render src/index.ts "$id" "$out" --codec=h264 --crf=16 \
         --concurrency="${CONCURRENCY:-4}" --timeout=120000 "$@" 2>&1 | tail -2); do
    tries=$((tries + 1)); [ "$tries" -ge 2 ] && { echo "RENDER FAILED: $id"; return 1; }
    echo "render failed, retrying once: $id"
  done
  [ -s "$SRC/$out" ] || { echo "RENDER FAILED (no file): $id"; return 1; }
}
