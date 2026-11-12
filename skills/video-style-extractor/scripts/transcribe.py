# /// script
# requires-python = ">=3.10"
# dependencies = ["faster-whisper", "numpy"]
# ///
"""Transcribe videos/*.mp4 -> subs/<id>.json (words) + subs/<id>.txt. Run from the work dir."""
import glob, json, os, subprocess
import numpy as np
from faster_whisper import WhisperModel

def load(f):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", f, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.float32)

model = WhisperModel("small.en", device="cpu", compute_type="int8", download_root="models")
for f in sorted(glob.glob("videos/*.mp4")):
    vid = os.path.basename(f)[:-4]
    if os.path.exists(f"subs/{vid}.json"):
        continue
    segs, info = model.transcribe(load(f), word_timestamps=True)
    S = [{"start": s.start, "end": s.end, "text": s.text.strip(),
          "words": [[w.word, round(w.start, 2), round(w.end, 2)] for w in s.words]} for s in segs]
    json.dump({"id": vid, "duration": info.duration, "segments": S}, open(f"subs/{vid}.json", "w"))
    open(f"subs/{vid}.txt", "w").write("\n".join(f"[{s['start']:6.1f}] {s['text']}" for s in S))
    print("  transcribed", vid, flush=True)
