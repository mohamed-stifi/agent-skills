#!/usr/bin/env bash
# Download reference videos + build everything an agent needs to study a style.
# usage: collect.sh <work-dir> <url-or-file-with-urls> [more urls...]
# Output in <work-dir>: videos/, sheets/<id>.jpg (1 frame / 3 s), subs/<id>.txt (timestamped transcript),
#                       subs/<id>.json (word timings), metrics.md (pace, length, cuts, colors)
set -euo pipefail
WORK="${1:?usage: collect.sh <work-dir> <url|urls.txt> ...}"; shift
HERE="$(cd "$(dirname "$0")" && pwd)"
for t in ffmpeg ffprobe uv; do command -v $t >/dev/null || { echo "MISSING: $t"; exit 1; }; done
mkdir -p "$WORK"/{videos,frames,sheets,subs}
cd "$WORK"
: > urls.txt
for a in "$@"; do if [ -f "$a" ]; then grep -v '^\s*$' "$a" >> urls.txt; else echo "$a" >> urls.txt; fi; done
echo "[1/4] download $(wc -l < urls.txt | tr -d ' ') videos (<=720p, no subtitles: they get rate-limited; we transcribe locally)"
uvx yt-dlp -i -q --no-warnings -f "bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[height<=720]/b" --merge-output-format mp4 \
  --write-info-json --sleep-requests 1 -o "videos/%(id)s.%(ext)s" -a urls.txt || true
echo "[2/4] frames + contact sheets"
for f in videos/*.mp4; do id=$(basename "$f" .mp4); [ -f "sheets/$id.jpg" ] && continue
  mkdir -p "frames/$id"
  ffmpeg -loglevel error -y -i "$f" -vf "fps=1/3,scale=270:-2" "frames/$id/f_%03d.jpg"
  ffmpeg -loglevel error -y -pattern_type glob -i "frames/$id/f_*.jpg" -vf "tile=10x6:padding=4:color=white" -frames:v 1 "sheets/$id.jpg"
done
echo "[3/4] transcribe locally (faster-whisper small.en; first run downloads ~500 MB)"
uv run --script "$HERE/transcribe.py"
echo "[4/4] metrics"
uv run --script "$HERE/metrics.py" > metrics.md
cat metrics.md
echo "DONE: $WORK  (now read sheets/*.jpg + subs/*.txt and follow SKILL.md step 3)"
