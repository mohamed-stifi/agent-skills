"""Script -> voiceover + word timings + subtitles. 100% local (Kokoro-82M, ONNX).

Usage (from the studio root):
  uv run --project voice voice/make_voice.py <slug>
Reads   src/videos/<slug>/script.json
Writes  public/<slug>/voice.wav, src/videos/<slug>/timing.json, out/<slug>/<slug>.srt

Each sentence is synthesized separately, so sentence and section boundaries are exact.
Word times inside a sentence are estimated from word length (good enough for cues).
"""

import json
import re
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

ROOT = Path(__file__).resolve().parent.parent
MODELS = Path(__file__).resolve().parent / "models"
SR = 24000
SILENCE = 0.012


def trim(samples: np.ndarray) -> np.ndarray:
    loud = np.where(np.abs(samples) > SILENCE)[0]
    if len(loud) == 0:
        return samples
    pad = 480  # keep 20 ms so words are not clipped
    return samples[max(loud[0] - pad, 0) : loud[-1] + pad]


def sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def spoken(token: str, pronounce: dict[str, str]) -> str:
    """Display token -> what the voice says. Keeps trailing punctuation."""
    m = re.match(r"^(.*?)([.,!?;:]*)$", token)
    core, punct = m.group(1), m.group(2)
    return pronounce.get(core, core) + punct


def weight(word: str) -> float:
    core = re.sub(r"[^\w ]", "", word)
    w = 1.0 + 0.35 * len(core)
    if word.endswith((",", ";", ":")):
        w += 1.5
    return w


def srt_time(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("usage: make_voice.py <slug>")
    slug = sys.argv[1]
    script_path = ROOT / "src/videos" / slug / "script.json"
    script = json.loads(script_path.read_text())
    pronounce = script.get("pronounce", {})
    voice, speed = script.get("voice", "am_michael"), float(script.get("speed", 1.0))
    gap_sentence = float(script.get("pauseBetweenSentencesSec", 0.15))
    gap_section = float(script.get("pauseAfterSectionSec", 0.4))
    lead_in = float(script.get("leadInSec", 0.3))

    kokoro = Kokoro(str(MODELS / "kokoro-v1.0.onnx"), str(MODELS / "voices-v1.0.bin"))
    chunks = [np.zeros(int(lead_in * SR), dtype=np.float32)]
    cursor = lead_in
    sections, words = [], []
    seen = set()

    for sec in script["sections"]:
        if sec["id"] in seen:
            sys.exit(f"duplicate section id: {sec['id']}")
        seen.add(sec["id"])
        start = cursor
        for sent in sentences(sec["text"]):
            tokens = sent.split()
            said = [spoken(t, pronounce) for t in tokens]
            audio, _ = kokoro.create(" ".join(said), voice=voice, speed=speed, lang="en-us")
            audio = trim(audio)
            dur = len(audio) / SR
            ws = [weight(w) for w in said]
            total, t = sum(ws), cursor
            for tok, w in zip(tokens, ws):
                d = dur * w / total
                words.append({"w": tok, "s": round(t, 3), "e": round(t + d, 3), "sec": sec["id"]})
                t += d
            chunks += [audio, np.zeros(int(gap_sentence * SR), dtype=np.float32)]
            cursor += dur + gap_sentence
        chunks.append(np.zeros(int(gap_section * SR), dtype=np.float32))
        cursor += gap_section
        sections.append({"id": sec["id"], "start": round(start, 3), "end": round(cursor, 3)})
        print(f"  {sec['id']:<14} {start:6.2f}s -> {cursor:6.2f}s")

    wav = ROOT / "public" / slug / "voice.wav"
    wav.parent.mkdir(parents=True, exist_ok=True)
    sf.write(wav, np.concatenate(chunks), SR)

    timing = {"totalSec": round(cursor, 3), "sections": sections, "words": words}
    (ROOT / "src/videos" / slug / "timing.json").write_text(json.dumps(timing, indent=1))

    # Subtitles for upload (YouTube/Facebook accept .srt). Max 7 words, break on punctuation.
    lines, cur = [], []
    for w in words:
        if cur and cur[0]["sec"] != w["sec"]:
            lines.append(cur); cur = []
        cur.append(w)
        if len(cur) >= 7 or re.search(r"[.,!?;:]$", w["w"]):
            lines.append(cur); cur = []
    if cur:
        lines.append(cur)
    srt = ROOT / "out" / slug / f"{slug}.srt"
    srt.parent.mkdir(parents=True, exist_ok=True)
    srt.write_text("\n".join(
        f"{i}\n{srt_time(l[0]['s'])} --> {srt_time(l[-1]['e'])}\n{' '.join(x['w'] for x in l)}\n"
        for i, l in enumerate(lines, 1)))

    n = len(words)
    print(f"Done: {cursor:.1f}s, {n} words, {n / cursor * 60:.0f} wpm -> public/{slug}/voice.wav")


if __name__ == "__main__":
    main()
