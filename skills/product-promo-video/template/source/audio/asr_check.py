"""Hear the film as a listener would: transcribe it with Whisper and compare with the script.
usage: uv run --with faster-whisper python asr_check.py [--lang en] <film.mp4> [...]
Mis-heard words (a name, a unit, a term) need a respelling in films.py 'say'.
"""
import subprocess
import sys

import numpy as np
from faster_whisper import WhisperModel

args = sys.argv[1:]
lang = 'en'
if '--lang' in args:
    lang = args[args.index('--lang') + 1]
    args = [a for a in args if a not in ('--lang', lang)]
m = WhisperModel('small.en' if lang == 'en' else 'small', device='cpu', compute_type='int8')
for p in args:
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-ac', '1', '-ar', '16000', '-f', 's16le', '-'],
                         capture_output=True, check=True).stdout
    audio = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    segs, _ = m.transcribe(audio, beam_size=5, vad_filter=True, language=lang)
    print('==', p.split('/')[-1], flush=True)
    for s in segs:
        print(f'  {s.start:5.1f}-{s.end:5.1f} {s.text.strip()}', flush=True)
