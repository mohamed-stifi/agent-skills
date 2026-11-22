"""Write <video>/README.md: what is here, the chapter index with start times, and how to re-record.

Run after engine.py has built every chapter:  python make_readme.py
Reads build/*/meta.json (written by engine.py) and TITLE / OUTPUT_NAME / README_NOTES from script.py.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).parent))
import script as S  # noqa: E402

name = getattr(S, "OUTPUT_NAME", "walkthrough")
title = getattr(S, "TITLE", "A guided video tour")
notes = getattr(S, "README_NOTES", "").strip()

metas = sorted((json.loads(p.read_text()) for p in (ROOT / "build").glob("*/meta.json")), key=lambda m: m["num"])
rows, t = [], 0.0
for m in metas:
    rows.append(f"| {int(t // 60):02d}:{int(t % 60):02d} | {m['num']} | {m['title']} | "
                f"[`chapters/{m['file']}`](chapters/{m['file']}) | {m['duration'] / 60:.1f} min |")
    t += m["duration"]

(ROOT / "README.md").write_text(f"""# {title}

A narrated, captioned video (1920×1080, H.264 + AAC). Everything shown was really run.

- **`{name}.mp4`**: the full video ({t / 60:.0f} min), with chapter markers and an English subtitle track
  (use your player's chapter and subtitle menus, e.g. QuickTime or VLC)
- **`{name}.srt`**: the narration as subtitles, also useful as a transcript
- **`chapters/`**: each chapter as its own file

## Chapters

| Starts | # | Chapter | File | Length |
|---|---|---|---|---|
{chr(10).join(rows)}

## How it was made, and how to re-record a chapter

Terminal scenes are recorded by [VHS](https://github.com/charmbracelet/vhs) on throwaway clones in `work/`
(never on a working copy), the voice is Kokoro (local, neural), slides are drawn with Pillow, ffmpeg assembles it.

```bash
cd src
bash run.sh engine.py --dry --only 05     # run a chapter's actions for real and print their output
bash run.sh engine.py --only 05           # re-record chapter 05
bash run.sh engine.py                     # rebuild what changed and re-assemble the full video
bash run.sh engine.py --only 05 --reuse-terms   # narration fix only: keep the screen recordings
VOICE=am_michael bash run.sh engine.py --force  # another Kokoro voice
bash run.sh make_readme.py                # refresh this file
```

- `src/script.py`: the words and the commands of every chapter (edit this)
- `src/engine.py`: script → narrated, captioned MP4s
{notes}
""")
print(f"wrote {ROOT / 'README.md'}")
