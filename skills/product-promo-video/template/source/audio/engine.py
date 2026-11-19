"""Promo film audio engine: voice (Kokoro-82M, local) + synthesized music bed + synced sound design + captions.

usage (from source/audio):
  uv run python engine.py                  # every film in films.py
  uv run python engine.py promo-60s        # one film
  uv run python engine.py --voices         # list the installed Kokoro voices
Films are defined in films.py (script, cue sheet, music map). Everything is generated here: no samples, no licences.
Inputs : source/out/<id>.mp4 (the silent render).   Outputs: source/out/audio/<id>-final.mp4, -mix.wav, .srt, .vtt,
         -transcript.md, -captions.json.
Voice  : Kokoro-82M ONNX from $PROMO_MODELS (default ~/.product-promo-videos/.cache/kokoro). Another TTS model:
         put tts_custom.py next to this file with  say(text, voice, speed, lang) -> (float ndarray, sample_rate).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

SR = 48000
ROOT = Path(__file__).resolve().parent          # source/audio
SOURCE = ROOT.parent                             # source/
MODELS = Path(os.environ.get('PROMO_MODELS', str(Path.home() / '.product-promo-videos' / '.cache' / 'kokoro')))
rng = np.random.default_rng(20261118)


# ───────────────────────────── DSP helpers ─────────────────────────────

def n_(d: float) -> int:
    return max(1, int(round(d * SR)))


def t_(d: float) -> np.ndarray:
    return np.arange(n_(d)) / SR


def fft_filter(x: np.ndarray, lo: float | None = None, hi: float | None = None, order: int = 2) -> np.ndarray:
    n = len(x)
    N = 1 << (n - 1).bit_length()
    X = np.fft.rfft(x, N)
    f = np.fft.rfftfreq(N, 1 / SR)
    m = np.ones_like(f)
    if lo:
        m *= 1 / np.sqrt(1 + (lo / np.maximum(f, 1e-3)) ** (2 * order))
    if hi:
        m *= 1 / np.sqrt(1 + (f / hi) ** (2 * order))
    return np.fft.irfft(X * m, N)[:n]


def fft_conv(x: np.ndarray, h: np.ndarray) -> np.ndarray:
    n = len(x) + len(h) - 1
    N = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, N) * np.fft.rfft(h, N), N)[: len(x)]


def norm(x: np.ndarray, peak: float = 1.0) -> np.ndarray:
    m = np.max(np.abs(x)) or 1.0
    return x * (peak / m)


def env_ad(n: int, a: float, d: float, curve: float = 1.0) -> np.ndarray:
    """attack (s) then exponential-ish decay to 0 at the end."""
    t = np.arange(n) / SR
    att = np.clip(t / max(a, 1e-4), 0, 1)
    dec = np.exp(-np.maximum(t - a, 0) / max(d, 1e-4) * curve)
    return att * dec


def fade(x: np.ndarray, fin: float = 0.005, fout: float = 0.02) -> np.ndarray:
    x = x.copy()
    a, b = min(len(x), n_(fin)), min(len(x), n_(fout))
    x[:a] *= np.linspace(0, 1, a)
    x[len(x) - b:] *= np.linspace(1, 0, b)
    return x


def sweep_noise(dur: float, f0: float, f1: float, bw_oct: float = 0.7) -> np.ndarray:
    """Noise whose band centre glides f0 -> f1 (exponential), via STFT masking."""
    n = n_(dur)
    W, hop = 1024, 256
    x = rng.standard_normal(n + W)
    win = np.hanning(W)
    freqs = np.fft.rfftfreq(W, 1 / SR)
    out = np.zeros(len(x))
    wsum = np.zeros(len(x))
    for s in range(0, len(x) - W, hop):
        p = min(1.0, s / n)
        fc = f0 * (f1 / f0) ** p
        m = np.exp(-0.5 * (np.log2(np.maximum(freqs, 1) / fc) / bw_oct) ** 2)
        y = np.fft.irfft(np.fft.rfft(x[s:s + W] * win) * m) * win
        out[s:s + W] += y
        wsum[s:s + W] += win ** 2
    return out[:n] / np.maximum(wsum[:n], 1e-3)


def additive(freq: float, dur: float, rolloff: float = 1.0, kmax: int = 40, decay_k: float = 0.0, odd: bool = False) -> np.ndarray:
    t = t_(dur)
    out = np.zeros_like(t)
    K = int(min(kmax, 12000 / max(freq, 1)))
    for k in range(1, K + 1):
        if odd and k % 2 == 0:
            continue
        a = 1 / k ** rolloff
        if decay_k:
            a = a * np.exp(-t * decay_k * k)
        out += a * np.sin(2 * np.pi * k * freq * t + rng.uniform(0, 2 * np.pi))
    return out


def midi(m: float) -> float:
    return 440.0 * 2 ** ((m - 69) / 12)


def make_ir(dur: float = 1.8, bright: float = 5000) -> np.ndarray:
    n = n_(dur)
    t = np.arange(n) / SR
    ir = np.zeros((n, 2))
    for c in range(2):
        noise = fft_filter(rng.standard_normal(n), lo=150, hi=bright)
        ir[:, c] = noise * np.exp(-t * 6.9 / dur)
    ir[: n_(0.012)] = 0  # pre-delay
    return ir / np.sqrt(np.sum(ir ** 2, axis=0))


IR = make_ir()


def reverb(st: np.ndarray, wet: float) -> np.ndarray:
    out = st.copy()
    for c in range(2):
        out[:, c] = st[:, c] * (1 - wet * 0.3) + fft_conv(st[:, c], IR[:, c]) * wet
    return out


def pan(mono: np.ndarray, p: float = 0.0) -> np.ndarray:
    """p in [-1, 1], equal power."""
    a = (p + 1) * np.pi / 4
    return np.stack([mono * np.cos(a), mono * np.sin(a)], axis=1)


def place(bus: np.ndarray, sig: np.ndarray, at: float, gain: float = 1.0) -> None:
    if sig.ndim == 1:
        sig = pan(sig, 0)
    i = int(round(at * SR))
    if i >= len(bus):
        return
    if i < 0:
        sig, i = sig[-i:], 0
    j = min(len(bus), i + len(sig))
    bus[i:j] += sig[: j - i] * gain


def db(x: float) -> float:
    return 10 ** (x / 20)


# ───────────────────────────── sound design ─────────────────────────────

def s_whoosh(dur: float = 0.45, rise: bool = True, peak: float = 0.62, bright: float = 1.0, p0: float = -0.5, p1: float = 0.5) -> np.ndarray:
    f0, f1 = (260 * bright, 3200 * bright) if rise else (3000 * bright, 300 * bright)
    x = sweep_noise(dur, f0, f1, 0.8)
    n = len(x)
    t = np.linspace(0, 1, n)
    e = np.where(t < peak, (t / peak) ** 2.2, ((1 - t) / (1 - peak)) ** 1.4)
    x = norm(x * e)
    a = np.linspace(p0, p1, n)
    ang = (a + 1) * np.pi / 4
    return np.stack([x * np.cos(ang), x * np.sin(ang)], axis=1)


def s_into(dur: float = 0.3) -> np.ndarray:
    """accelerating whoosh that peaks exactly at the cut (end of the clip)."""
    return s_whoosh(dur, True, 0.96, 1.2, 0.0, 0.0)


def s_arrive(dur: float = 0.35) -> np.ndarray:
    return s_whoosh(dur, False, 0.08, 1.0, 0.0, 0.0)


def s_antic(dur: float = 0.22) -> np.ndarray:
    """reverse swell: the inhale before a decisive move."""
    x = sweep_noise(dur, 1800, 700, 0.9)
    t = np.linspace(0, 1, len(x))
    return pan(norm(x * t ** 3) * 0.6)


def s_impact(size: float = 1.0) -> np.ndarray:
    d = 0.9 + 0.8 * size
    t = t_(d)
    f = 38 + (95 * size + 40) * np.exp(-t * 28)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * (4.2 / size))
    click = fft_filter(rng.standard_normal(len(t)), lo=900, hi=7000) * np.exp(-t * 90)
    body = fft_filter(rng.standard_normal(len(t)), lo=120, hi=1400) * np.exp(-t * 18)
    x = norm(boom * 1.0 + click * 0.35 + body * 0.25 * size)
    return reverb(pan(x), 0.25 + 0.2 * size)


def s_reveal() -> np.ndarray:
    hit = s_impact(1.4)
    chord = sum(additive(midi(m), 2.2, 1.2, 14, decay_k=0.9) for m in (60, 64, 67, 71, 74, 79))
    chord = fft_filter(chord, hi=6000) * env_ad(len(chord), 0.004, 1.1)
    st = reverb(pan(norm(chord) * 0.55, 0), 0.6)
    out = np.zeros((max(len(hit), len(st)), 2))
    out[: len(hit)] += hit
    out[: len(st)] += st
    return out


def s_stamp() -> np.ndarray:
    t = t_(0.35)
    f = 62 + 70 * np.exp(-t * 40)
    thump = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 16)
    knock = fft_filter(rng.standard_normal(len(t)), lo=280, hi=1700) * np.exp(-t * 55)
    snap = fft_filter(rng.standard_normal(len(t)), lo=2500, hi=9000) * np.exp(-t * 160)
    return reverb(pan(norm(thump + knock * 0.8 + snap * 0.35)), 0.18)


def s_click() -> np.ndarray:
    t = t_(0.06)
    x = fft_filter(rng.standard_normal(len(t)), lo=1500, hi=6000) * np.exp(-t * 260) + 0.5 * np.sin(2 * np.pi * 2300 * t) * np.exp(-t * 180)
    return pan(norm(x))


def s_tick(freq: float = 3200, soft: bool = False) -> np.ndarray:
    t = t_(0.05)
    x = fft_filter(rng.standard_normal(len(t)), lo=2500, hi=8000) * np.exp(-t * 400) + 0.6 * np.sin(2 * np.pi * freq * t) * np.exp(-t * 220)
    return pan(norm(x) * (0.5 if soft else 1.0), rng.uniform(-0.15, 0.15))


def s_pop(up: bool = True) -> np.ndarray:
    t = t_(0.12)
    f = (520 + 520 * np.clip(t / 0.05, 0, 1)) if up else (900 - 300 * np.clip(t / 0.05, 0, 1))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_ad(len(t), 0.002, 0.035)
    return reverb(pan(norm(x), rng.uniform(-0.2, 0.2)), 0.15)


def s_thud(pitch: float = 1.0) -> np.ndarray:
    t = t_(0.18)
    f = (130 + 90 * np.exp(-t * 60)) * pitch
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 26)
    x += fft_filter(rng.standard_normal(len(t)), lo=350, hi=1600) * np.exp(-t * 90) * 0.5
    return pan(norm(x), rng.uniform(-0.3, 0.3))


def s_error() -> np.ndarray:
    a = additive(196, 0.09, 1.0, 9, odd=True) * env_ad(n_(0.09), 0.002, 0.05)
    b = additive(174.6, 0.13, 1.0, 9, odd=True) * env_ad(n_(0.13), 0.002, 0.07)
    x = np.concatenate([a, np.zeros(n_(0.015)), b])
    return reverb(pan(norm(fft_filter(x, hi=3500))), 0.12)


PENTA = [72, 74, 76, 79, 81, 84, 86, 88, 91, 93, 96]


def s_pass(step: int = 0) -> np.ndarray:
    m = PENTA[min(step, len(PENTA) - 1)]
    x = additive(midi(m), 0.5, 1.6, 6, decay_k=1.5) * env_ad(n_(0.5), 0.002, 0.12)
    return reverb(pan(norm(x), rng.uniform(-0.25, 0.25)), 0.25)


def s_chime() -> np.ndarray:
    out = np.zeros(n_(1.4))
    for i, m in enumerate((76, 79, 84)):
        x = additive(midi(m), 1.2, 1.5, 6, decay_k=0.8) * env_ad(n_(1.2), 0.003, 0.4)
        o = n_(0.06 * i)
        out[o:o + len(x)] += x
    return reverb(pan(norm(out)), 0.4)


def s_shimmer() -> np.ndarray:
    out = np.zeros(n_(2.0))
    for i, m in enumerate((84, 88, 91, 95, 98)):
        x = np.sin(2 * np.pi * midi(m) * t_(1.6)) * env_ad(n_(1.6), 0.01, 0.5)
        o = n_(0.045 * i)
        out[o:o + len(x)] += x
    return reverb(pan(norm(out)), 0.7)


def s_riser(dur: float = 1.0) -> np.ndarray:
    x = sweep_noise(dur, 220, 7000, 0.9)
    t = np.linspace(0, 1, len(x))
    x = norm(x * t ** 2.4)
    tone = np.sin(2 * np.pi * np.cumsum(220 * 4 ** t) / SR) * t ** 2.4 * 0.25
    return reverb(pan(norm(x + tone)), 0.3)


def s_swoosh() -> np.ndarray:
    return s_whoosh(0.32, True, 0.45, 1.6, -0.2, 0.2) * 0.6


def s_typing(dur: float) -> np.ndarray:
    out = np.zeros(n_(dur + 0.1))
    t = 0.0
    while t < dur:
        c = fft_filter(rng.standard_normal(n_(0.012)), lo=1800, hi=7000) * np.exp(-np.arange(n_(0.012)) / SR * 500)
        i = n_(t)
        out[i:i + len(c)] += c * rng.uniform(0.45, 1.0)
        t += rng.uniform(0.038, 0.075)
    return pan(norm(out))


def s_count(dur: float, rate0: float = 22, rate1: float = 6) -> np.ndarray:
    """ticks of a fast counter that decelerates as it lands."""
    out = np.zeros((n_(dur + 0.1), 2))
    t = 0.0
    while t < dur:
        p = t / dur
        place(out, s_tick(2600 + 900 * p, soft=True) * (0.55 + 0.45 * (1 - p)), t)
        t += 1 / (rate0 + (rate1 - rate0) * p)
    return out


def s_countdown(dur: float, rate: float = 8) -> np.ndarray:
    out = np.zeros((n_(dur + 0.1), 2))
    k = 0
    while k / rate < dur:
        place(out, s_tick(1700 if k % 2 else 2100, soft=True), k / rate)
        k += 1
    return out


def s_fly() -> np.ndarray:
    return s_whoosh(0.22, True, 0.5, 1.8, rng.uniform(-0.6, 0), 0.7) * 0.5


def s_drone_swell(dur: float) -> np.ndarray:
    t = t_(dur)
    x = np.sin(2 * np.pi * 110 * t) + 0.5 * np.sin(2 * np.pi * 165 * t) + 0.25 * np.sin(2 * np.pi * 220 * t * (1 + 0.5 * t / dur))
    return pan(norm(x * (t / dur) ** 2))


SFX = {
    'whoosh': lambda dur=0.45, **k: s_whoosh(dur, **k),
    'into': lambda dur=0.3, **k: s_into(dur),
    'arrive': lambda dur=0.35, **k: s_arrive(dur),
    'antic': lambda dur=0.22, **k: s_antic(dur),
    'impact': lambda size=1.0, **k: s_impact(size),
    'reveal': lambda **k: s_reveal(),
    'stamp': lambda **k: s_stamp(),
    'click': lambda **k: s_click(),
    'tick': lambda soft=False, **k: s_tick(soft=soft),
    'pop': lambda up=True, **k: s_pop(up),
    'thud': lambda pitch=1.0, **k: s_thud(pitch),
    'error': lambda **k: s_error(),
    'pass': lambda step=0, **k: s_pass(step),
    'chime': lambda **k: s_chime(),
    'shimmer': lambda **k: s_shimmer(),
    'riser': lambda dur=1.0, **k: s_riser(dur),
    'swoosh': lambda **k: s_swoosh(),
    'typing': lambda dur=0.8, **k: s_typing(dur),
    'count': lambda dur=0.8, **k: s_count(dur),
    'countdown': lambda dur=3.0, rate=8, **k: s_countdown(dur, rate),
    'fly': lambda **k: s_fly(),
    'swell': lambda dur=2.0, **k: s_drone_swell(dur),
}

# default levels (dB) per sound
LEVEL = {
    'whoosh': -14, 'into': -13, 'arrive': -16, 'antic': -20, 'impact': -9, 'reveal': -8, 'stamp': -10, 'click': -16,
    'tick': -22, 'pop': -20, 'thud': -20, 'error': -17, 'pass': -17, 'chime': -15, 'shimmer': -18, 'riser': -14,
    'swoosh': -20, 'typing': -26, 'count': -22, 'countdown': -27, 'fly': -24, 'swell': -24,
}


# ───────────────────────────── music ─────────────────────────────

BPM = 120
BEAT = 60 / BPM
CHORDS = {  # midi notes for pad voicing, bass root
    'Am': ([57, 60, 64, 69], 45), 'F': ([53, 57, 60, 65], 41), 'C': ([55, 60, 64, 67], 48), 'G': ([55, 59, 62, 67], 43),
    'Cadd9': ([55, 60, 62, 64, 67], 48), 'Fmaj7': ([53, 57, 60, 64], 41), 'Dm': ([57, 62, 65, 69], 50),
}


def pad_chord(notes: list[int], dur: float, bright: float = 1.0, att: float = 0.35, rel: float = 0.8) -> np.ndarray:
    total = dur + rel
    out = np.zeros((n_(total), 2))
    for m in notes:
        for cents, p in ((-8, -0.6), (0, 0.0), (8, 0.6)):
            f = midi(m) * 2 ** (cents / 1200)
            x = additive(f, total, 1.7, int(10 * bright) + 4)
            out += pan(x, p)
    t = np.arange(len(out)) / SR
    e = np.clip(t / att, 0, 1) * np.where(t > dur, np.exp(-(t - dur) / (rel / 3)), 1.0)
    return out * e[:, None]


def pluck(m: int, dur: float = 0.5, bright: float = 1.0) -> np.ndarray:
    x = additive(midi(m), dur, 1.3, int(10 * bright) + 2, decay_k=1.1) * env_ad(n_(dur), 0.002, dur / 3.5)
    return x


def bass_note(m: int, dur: float) -> np.ndarray:
    x = additive(midi(m), dur, 1.25, 10) * env_ad(n_(dur), 0.004, dur / 2.2)
    return fft_filter(x, hi=900)


def kick() -> np.ndarray:
    t = t_(0.42)
    f = 44 + 90 * np.exp(-t * 32)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.5)


def hat(open_: bool = False) -> np.ndarray:
    d = 0.16 if open_ else 0.05
    t = t_(d)
    return fft_filter(rng.standard_normal(len(t)), lo=7000, hi=14000) * np.exp(-t * (18 if open_ else 75))


def music(sections: list[tuple[float, float, str]], total: float) -> np.ndarray:
    bus = np.zeros((n_(total + 3), 2))
    K, H, HO = kick(), hat(), hat(True)
    for (a, b, kind) in sections:
        dur = b - a
        nb = int(np.ceil(dur / BEAT))
        if kind == 'busy':  # daytime calendar: a pluck ostinato that tightens
            notes = [69, 72, 76, 81, 76, 72]
            for i in range(nb * 4):
                tt = a + i * BEAT / 4
                if tt >= b:
                    break
                p = (tt - a) / dur
                if i % 2 and p < 0.45:
                    continue
                place(bus, pan(pluck(notes[i % len(notes)], 0.35, 0.8), (-0.3 if i % 2 else 0.3)), tt, 0.10 + 0.12 * p)
                if i % 2 == 0:
                    place(bus, pan(H, 0.4), tt, 0.04 + 0.05 * p)
            place(bus, pad_chord([57, 64], dur, 0.4, 1.0, 0.4), a, 0.045)
        elif kind == 'dark':  # night: drone, then a pulse, then hats
            t = t_(dur + 0.6)
            drone = np.sin(2 * np.pi * 55 * t) + 0.35 * np.sin(2 * np.pi * 110 * t) + 0.12 * np.sin(2 * np.pi * 82.4 * t)
            drone *= np.clip(t / 0.8, 0, 1) * np.clip((dur + 0.6 - t) / 0.6, 0, 1)
            place(bus, pan(drone), a, 0.16)
            for i in range(nb * 2):
                tt = a + i * BEAT / 2
                p = (tt - a) / dur
                if tt >= b:
                    break
                if p > 0.22:
                    place(bus, pan(bass_note(33 if (i // 8) % 4 != 3 else 34, 0.24)), tt, 0.20 + 0.1 * p)
                if p > 0.55:
                    place(bus, pan(H, 0.35), tt + BEAT / 4, 0.05 + 0.04 * p)
                if p > 0.7 and i % 4 == 0:
                    place(bus, pan(K), tt, 0.32)
            hi = np.sin(2 * np.pi * midi(88) * t) * 0.5 + np.sin(2 * np.pi * midi(89) * t) * 0.5
            hi *= np.clip((t - dur * 0.5) / (dur * 0.5), 0, 1) ** 2 * np.clip((dur + 0.6 - t) / 0.6, 0, 1)
            place(bus, pan(hi), a, 0.012)
        elif kind in ('drive', 'lift'):
            prog = ['Am', 'F', 'C', 'G'] if kind == 'drive' else ['F', 'G', 'C', 'Cadd9']
            bar = 4 * BEAT
            nbars = int(np.ceil(dur / bar))
            arp_oct = 0 if kind == 'drive' else 12
            for k in range(nbars):
                ta = a + k * bar
                if ta >= b:
                    break
                bl = min(bar, b - ta)
                name = prog[k % 4]
                notes, root = CHORDS[name]
                place(bus, pad_chord(notes, bl, 0.8 if kind == 'drive' else 1.1, 0.12, 0.5), ta, 0.022 if kind == 'drive' else 0.03)
                for i in range(8):
                    tt = ta + i * BEAT / 2
                    if tt >= b:
                        break
                    place(bus, pan(bass_note(root - 12 if i % 2 == 0 else root, 0.24)), tt, 0.26)
                    arp = notes[i % len(notes)] + 12 + arp_oct
                    place(bus, pan(pluck(arp, 0.4), 0.35 if i % 2 else -0.35), tt, 0.08 if kind == 'drive' else 0.10)
                    if i % 2 == 0:
                        place(bus, pan(K), tt, 0.42)
                    else:
                        place(bus, pan(H, 0.3), tt, 0.07)
                    if kind == 'lift' and i == 7:
                        place(bus, pan(HO, -0.3), tt, 0.05)
        elif kind == 'resolve':
            notes, root = CHORDS['Cadd9']
            fadeout = min(2.0, dur * 0.5)
            pc = pad_chord(notes + [72, 76], dur, 1.2, 0.05, 1.5)
            place(bus, pc, a, 0.032)
            place(bus, pan(bass_note(36, min(dur, 3.0)) * 1.0), a, 0.32)
            motif = [79, 76, 72, 74, 76]
            for i, m in enumerate(motif):
                tt = a + 0.5 + i * BEAT
                if tt < b - 0.5:
                    place(bus, pan(pluck(m, 0.9), 0.2 * (i % 2 * 2 - 1)), tt, 0.11)
            # fade the tail of this section to silence at the film's end
            i0, i1 = n_(b - fadeout), n_(b)
            if i1 <= len(bus):
                bus[i0:i1] *= np.linspace(1, 0, i1 - i0)[:, None] ** 1.5
                bus[i1:] = 0
    bus = reverb(bus, 0.28)
    return bus[: n_(total)]


# ───────────────────────────── voice ─────────────────────────────

_kokoro = None


def kokoro():
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        _kokoro = Kokoro(str(MODELS / 'kokoro-v1.0.onnx'), str(MODELS / 'voices-v1.0.bin'))
    return _kokoro


def resample_24_48(x: np.ndarray) -> np.ndarray:
    n = len(x)
    X = np.fft.rfft(x)
    Y = np.zeros(n + 1, dtype=complex)
    Y[: len(X)] = X
    return np.fft.irfft(Y, 2 * n) * 2


def trim(x: np.ndarray, thr: float = 0.01) -> np.ndarray:
    loud = np.where(np.abs(x) > thr)[0]
    if len(loud) == 0:
        return x
    pad = n_(0.025)
    return x[max(0, loud[0] - pad): loud[-1] + pad]


try:  # optional: another TTS model (any language), same interface
    sys.path.insert(0, str(ROOT))
    import tts_custom  # type: ignore
except ImportError:
    tts_custom = None


def say(text: str, voice: str, speed: float, lang: str = 'en-us') -> np.ndarray:
    if tts_custom is not None:
        audio, sr = tts_custom.say(text, voice, speed, lang)
    else:
        audio, sr = kokoro().create(text, voice=voice, speed=speed, lang=lang)
    if sr not in (24000, 48000):  # generic resample to 48 kHz
        audio = np.interp(np.arange(0, len(audio), sr / SR), np.arange(len(audio)), np.asarray(audio, dtype=np.float64))
        sr = SR
    x = resample_24_48(np.asarray(audio, dtype=np.float64)) if sr == 24000 else np.asarray(audio, dtype=np.float64)
    x = trim(x)
    x = fft_filter(x, lo=75, order=2)
    rms = np.sqrt(np.mean(x ** 2)) or 1
    return fade(x * (db(-19) / rms), 0.004, 0.03)


def build_voice(lines: list[dict], total: float, voice: str, base_speed: float, lang: str = 'en-us'):
    bus = np.zeros(n_(total + 2))
    placed = []
    for i, ln in enumerate(lines):
        start = ln['t']
        nxt = lines[i + 1]['t'] if i + 1 < len(lines) else total - 0.2
        avail = nxt - start - 0.12
        speed = ln.get('speed', base_speed)
        x = say(ln.get('say', ln['text']), voice, speed, lang)
        d = len(x) / SR
        if d > avail and not ln.get('allowOverrun'):
            speed2 = min(1.22, speed * d / avail * 1.01)
            x = say(ln.get('say', ln['text']), voice, speed2, lang)
            d2 = len(x) / SR
            print(f"  ! line {i} '{ln['text'][:40]}…' {d:.2f}s > {avail:.2f}s, re-voiced at {speed2:.2f} -> {d2:.2f}s")
            d = d2
        i0 = n_(start)
        bus[i0:i0 + len(x)] += x[: max(0, len(bus) - i0)]
        placed.append({'start': round(start, 3), 'end': round(start + d, 3), 'text': ln['text']})
        print(f"  {start:6.2f}s -> {start + d:6.2f}s  {ln['text']}")
    return bus[: n_(total)], placed


# ───────────────────────────── captions ─────────────────────────────

def chunks(text: str, maxw: int = 7) -> list[str]:
    out, cur = [], []
    for w in text.split():
        cur.append(w)
        if len(cur) >= maxw or (re.search(r'[.,!?;:]$', w) and len(cur) >= 3):
            out.append(' '.join(cur))
            cur = []
    if cur:
        if out and len(cur) <= 2:
            out[-1] += ' ' + ' '.join(cur)
        else:
            out.append(' '.join(cur))
    return out


def cues_for(placed: list[dict]) -> list[dict]:
    cues = []
    for p in placed:
        parts = chunks(p['text'])
        weights = [len(x) + 6 for x in parts]
        tot = sum(weights)
        t = p['start']
        span = p['end'] - p['start']
        for x, w in zip(parts, weights):
            d = span * w / tot
            cues.append({'start': round(t, 3), 'end': round(t + d, 3), 'text': x})
            t += d
    # hold each cue a little longer when there is room (max 0.6 s), never overlapping
    for i, c in enumerate(cues):
        nxt = cues[i + 1]['start'] if i + 1 < len(cues) else c['end'] + 0.6
        c['end'] = round(min(nxt - 0.04, c['end'] + 0.6), 3)
    return cues


def ts(t: float, sep: str = ',') -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f'{h:02}:{m:02}:{s:02}{sep}{ms:03}'


def write_caption_files(cues: list[dict], placed: list[dict], base: Path, title: str) -> None:
    base.with_suffix('.srt').write_text('\n'.join(f"{i}\n{ts(c['start'])} --> {ts(c['end'])}\n{c['text']}\n" for i, c in enumerate(cues, 1)))
    base.with_suffix('.vtt').write_text('WEBVTT\n\n' + '\n'.join(f"{ts(c['start'], '.')} --> {ts(c['end'], '.')}\n{c['text']}\n" for c in cues))
    md = [f'# {title} · transcript', '', '| Time | Voice-over |', '|---|---|']
    md += [f"| {ts(p['start'])[3:8]} | {p['text']} |" for p in placed]
    md += ['', 'Voice: Kokoro-82M (local, open-weight). Music and sound design synthesized for this film; no samples, no licences.', '']
    Path(str(base) + '-transcript.md').write_text('\n'.join(md))


# ───────────────────────────── mix ─────────────────────────────

def envelope(x: np.ndarray, win: float) -> np.ndarray:
    k = n_(win)
    c = np.cumsum(np.concatenate([[0], np.abs(x)]))
    e = (c[k:] - c[:-k]) / k
    return np.concatenate([e, np.full(len(x) - len(e), e[-1] if len(e) else 0)])


def build(film: dict, voice_override: str | None = None) -> None:
    total = film['duration']
    out_dir = Path(film.get('out_dir', SOURCE / 'out' / 'audio'))
    out_dir.mkdir(parents=True, exist_ok=True)
    base = out_dir / film.get('base', film['id'])
    film.setdefault('video', str(SOURCE / 'out' / f"{film['id']}.mp4"))
    if not Path(film['video']).exists():
        sys.exit(f"missing silent render {film['video']}: run render.sh first")
    voice = voice_override or film.get('voice', 'af_heart')
    lang = film.get('lang', 'en-us')
    print(f"== {film['id']} ({total}s)")

    print('voice:')
    vbus, placed = build_voice(film['lines'], total, voice, film.get('speed', 1.0), lang)

    print('music…')
    mbus = music(film['music'], total)
    mrms = np.sqrt(np.mean(mbus ** 2)) or 1
    mbus *= db(-27) / mrms

    print('sound design…')
    sbus = np.zeros((n_(total + 3), 2))
    for ev in film['events']:
        t, kind = ev[0], ev[1]
        kw = ev[2] if len(ev) > 2 else {}
        sig = SFX[kind](**{k: v for k, v in kw.items() if k not in ('db', 'end')})
        lvl = kw.get('db', LEVEL[kind])
        anchor_end = kind in ('into', 'riser', 'antic') or kw.get('end', False)
        at = t - len(sig) / SR if anchor_end and kind in ('into', 'antic') else t
        if kind == 'riser':
            at = t - kw.get('dur', 1.0)
        place(sbus, sig, at, db(lvl))
    sbus = sbus[: n_(total)]

    # ducking: music -7 dB and sound design -3 dB under the voice
    env = envelope(vbus, 0.06)
    g = np.clip(env / (db(-30)), 0, 1)
    g = envelope(g, 0.25)
    mg = 1 - (1 - db(-7)) * g
    sg = 1 - (1 - db(-3)) * g
    mix = mbus * mg[:, None] + sbus * sg[:, None] + pan(vbus, 0) * np.sqrt(2)
    # gentle bus limiter
    peak = np.max(np.abs(mix))
    if peak > 0.98:
        mix *= 0.98 / peak
    wav = Path(str(base) + '-mix.wav')
    sf.write(wav, mix.astype(np.float32), SR, subtype='FLOAT')

    cues = cues_for(placed)
    write_caption_files(cues, placed, base, film.get('title', film['id']))
    (Path(str(base) + '-captions.json')).write_text(json.dumps({'fps': 60, 'cues': cues}, indent=1))

    # loudness-normalise to -14 LUFS (web/social), then mux with the silent video + a soft subtitle track
    final = Path(str(base) + '-final.mp4')
    cmd = ['ffmpeg', '-v', 'error', '-y', '-i', film['video'], '-i', str(wav), '-i', str(base.with_suffix('.srt')),
           '-map', '0:v:0', '-map', '1:a:0', '-map', '2:s:0', '-c:v', 'copy',
           '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', '-ar', '48000', '-c:a', 'aac', '-b:a', '256k',
           '-c:s', 'mov_text', '-metadata:s:s:0', f'language={film.get("lang3", "eng")}', '-metadata:s:a:0', f'language={film.get("lang3", "eng")}',
           '-t', f'{total:.3f}', '-movflags', '+faststart', str(final)]  # not -shortest: the subtitle track ends early
    subprocess.run(cmd, check=True)
    print(f'  -> {final}')


if __name__ == '__main__':
    args = sys.argv[1:]
    if '--voices' in args:
        print('\n'.join(sorted(kokoro().get_voices())))
        sys.exit(0)
    voice = None
    if '--voice' in args:
        voice = args[args.index('--voice') + 1]
        args = [a for a in args if a not in ('--voice', voice)]
    from films import FILMS
    ids = args or list(FILMS)
    for fid in ids:
        if fid not in FILMS:
            sys.exit(f"unknown film '{fid}'. Films: {', '.join(FILMS)}")
        build(FILMS[fid], voice)
