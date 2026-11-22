"""Video engine (demo-video skill): turns the chapter script (script.py, next to this file) into narrated, captioned
1080p MP4s.

Each segment is one of:
  card   - full-screen title card (Pillow), narrated
  slide  - full-screen slide: title + bullets and/or a row of boxes joined by arrows (Pillow), narrated
  term   - a real terminal session recorded by VHS (1920x900), framed with a header and a caption bar
  browser - a real Chromium used like a person (Playwright, scripts/browser.py), framed the same way
  api    - real HTTP calls shown by `req` (request, status, response), then effect checks: a terminal scene
  diagram - a slide of boxes and arrows that lights up the parts each sentence talks about, in time with it
  section - a short card between steps: a gradient and one centred pill (icon + a few words)
  concept - two or three glowing tiles (icon, caps title, subtitle), optionally joined by "+", for "what is X"
A segment's `step` shows as a pill top right; `step="#Connect Claude"` is numbered across the whole video:
"Step 3 of 5 · Connect Claude".

Every segment gets its own voice-over (Kokoro-82M, a local neural voice; or macOS `say`); the picture is held on its
last frame until the voice ends, so narration and picture never drift. Segments -> chapters/NN-slug.mp4 -> the full walkthrough with
chapter markers and a subtitle track.

    python engine.py                    # build everything missing or changed, then assemble
    python engine.py --only 04 05       # (re)build chapters 04 and 05 only (no assembly)
    python engine.py --dry [--only 04]  # run every terminal command in plain bash and print the output (no video)
    python engine.py --force            # rebuild everything (e.g. after changing VOICE)
    python engine.py --reuse-terms      # keep recorded terminal clips, redo voice/frames (narration fixes)

Env: VOICE_ENGINE (kokoro | say, default kokoro), VOICE (default af_heart for kokoro, Samantha for say),
     SPEED (kokoro speed, default 1.0), RATE (say words per minute, default 172),
     KOKORO_MODELS (folder with kokoro-v1.0.onnx + voices-v1.0.bin, default ~/.cache/kokoro).

script.py must define CHAPTERS and WORKDIRS; optional: ENV, TITLE, FOOTER, AUTHOR, PROMPT, OUTPUT_NAME, SPOKEN.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent          # the video folder (this file lives in <video>/src)
BUILD = ROOT / "build"
CHAPTERS = ROOT / "chapters"
W, H = 1920, 1080
HEAD, TERM_H = 76, 900                                 # header bar, terminal height; caption bar = the rest
CAP_Y = HEAD + TERM_H
VOICE_ENGINE = os.environ.get("VOICE_ENGINE", "kokoro")
VOICE = os.environ.get("VOICE", "af_heart" if VOICE_ENGINE == "kokoro" else "Samantha")
SPEED = float(os.environ.get("SPEED", "1.0"))
RATE = os.environ.get("RATE", "172")
KOKORO_MODELS = Path(os.environ.get("KOKORO_MODELS", str(Path.home() / ".cache" / "kokoro")))
SENTENCE_GAP = 0.18                                    # seconds of silence between sentences
_KOKORO = None
FPS = 30
REUSE_TERMS = False
SCRIPT = None                                          # the imported script.py

# Catppuccin Mocha, matching the VHS theme
C = dict(bg="#1e1e2e", mantle="#181825", crust="#11111b", surface="#313244", overlay="#6c7086", text="#cdd6f4",
         sub="#a6adc8", blue="#89b4fa", green="#a6e3a1", red="#f38ba8", yellow="#f9e2af", mauve="#cba6f7",
         peach="#fab387", teal="#94e2d5", sky="#89dceb")

FONT_SANS = ["/System/Library/Fonts/SFNS.ttf", "/System/Library/Fonts/Helvetica.ttc",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
FONT_MONO = ["/System/Library/Fonts/SFNSMono.ttf", "/System/Library/Fonts/Menlo.ttc",
             "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]


def cfg(name, default):
    return getattr(SCRIPT, name, default)


FONT_ICON = ["/System/Library/Fonts/Menlo.ttc", "/System/Library/Fonts/Apple Symbols.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]


def icon_font(ch: str, size: int) -> ImageFont.FreeTypeFont:
    """The first font that has a glyph for this icon (⚡ ⚙ ⚠ ✓ ★ { } ⬇ …)."""
    for p in FONT_ICON:
        if os.path.exists(p):
            f = ImageFont.truetype(p, size)
            a, z = (Image.new("L", (size * 2, size * 2)) for _ in range(2))
            ImageDraw.Draw(a).text((4, 4), ch, font=f, fill=255)
            ImageDraw.Draw(z).text((4, 4), "\uffff", font=f, fill=255)       # the font's "missing" box
            if a.getbbox() and a.tobytes() != z.tobytes():
                return f
    return font(size, "Bold")


def number_steps(chaps):
    """`step="#label"` -> "Step k of N · label", counted over the whole video (so the badge text is in each
    chapter's cache key)."""
    marked = [(ci, si) for ci, c in enumerate(chaps) for si, sg in enumerate(c["segments"])
              if str(sg.get("step", "")).startswith("#")]
    out = json.loads(json.dumps(chaps))
    for k, (ci, si) in enumerate(marked, 1):
        sg = out[ci]["segments"][si]
        sg["step"] = f"Step {k} of {len(marked)} · {sg['step'][1:].strip()}"
    return out


def gradient(color: str) -> Image.Image:
    """A dark radial gradient around a soft glow of `color`, like a section backdrop."""
    import numpy as np
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dist = np.sqrt(((xx - W * 0.42) / W) ** 2 + ((yy - H * 0.4) / H) ** 2) / 0.75
    t = np.clip(dist, 0, 1)[..., None]
    c = np.array(Image.new("RGB", (1, 1), color).getpixel((0, 0)), dtype=np.float32)
    edge = np.array([8, 10, 20], dtype=np.float32)
    return Image.fromarray((c * (1 - t) * 0.85 + edge * t).astype("uint8"), "RGB")


def glow_rounded(im, box, radius, rim, width=3, blur=18):
    """A rounded panel with a soft glow of `rim` around it."""
    from PIL import ImageFilter
    halo = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(halo).rounded_rectangle(box, radius=radius, outline=rim, width=width + 6)
    im.alpha_composite(halo.filter(ImageFilter.GaussianBlur(blur)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle(box, radius=radius, fill=(16, 22, 42, 235), outline=rim, width=width)
    return d


SECTION_COLORS = {"blue": "#2650c8", "orange": "#c2611a", "green": "#2b8a3e", "purple": "#7048e8", "teal": "#1c7e86"}


def picture_section(seg, chap, out: Path):
    im = gradient(SECTION_COLORS.get(seg.get("color", "blue"), seg.get("color", "#2650c8"))).convert("RGBA")
    icon, text = seg.get("icon", ""), seg["title"]
    ft = font(54, "Bold")
    d = ImageDraw.Draw(im)
    fi = icon_font(icon, 50) if icon else None
    iw = d.textlength(icon, font=fi) + 26 if icon else 0
    tw = iw + d.textlength(text, font=ft)
    x0, y0 = (W - tw) // 2 - 48, H // 2 - 56
    d = glow_rounded(im, [x0, y0, x0 + tw + 96, y0 + 112], 56, "#f5a524")
    if icon:
        d.text((x0 + 48, y0 + 26), icon, font=fi, fill="#ffd43b")
    d.text((x0 + 48 + iw, y0 + 22), text, font=ft, fill="#ffffff")
    if seg.get("kicker"):
        k = seg["kicker"].upper()
        d.text(((W - d.textlength(k, font=font(30, "Semibold"))) // 2, y0 - 70), k, font=font(30, "Semibold"),
               fill="#c9d4ff")
    im.convert("RGB").save(out)


def picture_concept(seg, chap, out: Path):
    tiles, join = seg["tiles"], seg.get("join", "")
    im = gradient(SECTION_COLORS.get(seg.get("color", "blue"), seg.get("color", "#2650c8"))).convert("RGBA")
    d = ImageDraw.Draw(im)
    if seg.get("title"):
        d.text(((W - d.textlength(seg["title"], font=font(56, "Bold"))) // 2, 110), seg["title"],
               font=font(56, "Bold"), fill="#ffffff")
    n, tw, th, gap = len(tiles), 520, 400, 150 if join else 70
    x = (W - (n * tw + (n - 1) * gap)) // 2
    y = (H - th) // 2 + (30 if seg.get("title") else 0)
    for i, t in enumerate(tiles):
        rim = t.get("rim", ["#5c8dff", "#71bcd9", "#b197fc"][i % 3])
        d = glow_rounded(im, [x, y, x + tw, y + th], 34, rim, width=2, blur=22)
        if t.get("icon"):
            fi = icon_font(t["icon"], 110)
            d.text((x + (tw - d.textlength(t["icon"], font=fi)) // 2, y + 50), t["icon"], font=fi,
                   fill=t.get("icon_color", "#ffd43b" if i % 2 else "#a5d8ff"))
        ty = y + 205
        for line in wrap(d, t["title"].upper(), font(40, "Bold"), tw - 60)[:2]:
            d.text((x + (tw - d.textlength(line, font=font(40, "Bold"))) // 2, ty), line, font=font(40, "Bold"),
                   fill="#ffffff")
            ty += 52
        for line in wrap(d, t.get("sub", ""), font(28), tw - 70)[:3]:
            d.text((x + (tw - d.textlength(line, font=font(28))) // 2, ty + 8), line, font=font(28), fill="#c3cbe6")
            ty += 38
        if join and i < n - 1:
            d.text((x + tw + (gap - d.textlength(join, font=font(80, "Bold"))) // 2, y + th // 2 - 52), join,
                   font=font(80, "Bold"), fill="#c3cbe6")
        x += tw + gap
    im.convert("RGB").save(out)


def font(size: int, weight: str = "Regular", mono: bool = False) -> ImageFont.FreeTypeFont:
    path = next((p for p in (FONT_MONO if mono else FONT_SANS) if os.path.exists(p)), None)
    f = ImageFont.truetype(path, size) if path else ImageFont.load_default(size)
    try:
        f.set_variation_by_name(weight)                 # SF fonts are variable: Regular/Medium/Semibold/Bold
    except Exception:
        pass
    return f


def wrap(draw, text, fnt, width, mono=None):
    """Word-wrap rich text: `code` is measured in the monospace font it is drawn with; a code span may break at
    its spaces (each word stays code)."""
    mono = mono or font(fnt.size - 3, mono=True)
    text = re.sub(r"`([^`]*)`", lambda m: " ".join(f"`{w}`" for w in m.group(1).split(" ")), text)
    words = re.findall(r"[^\s`]*`[^`]*`[^\s`]*|\S+", text)

    def measure(t):
        return sum(draw.textlength(part, font=mono if i % 2 else fnt) for i, part in enumerate(t.split("`")))

    lines, cur = [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if measure(t) <= width or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def rich(draw, xy, text, fnt, fill, code_fill=None, mono=None):
    """Draw text where `backticked` parts are monospace and coloured."""
    x, y = xy
    for i, part in enumerate(re.split(r"`", text)):
        if not part:
            continue
        if i % 2:
            f2 = mono or font(fnt.size - 2, "Regular", mono=True)
            draw.text((x, y + 2), part, font=f2, fill=code_fill or C["peach"])
            x += draw.textlength(part, font=f2)
        else:
            draw.text((x, y), part, font=fnt, fill=fill)
            x += draw.textlength(part, font=fnt)
    return x


# ---------------------------------------------------------------- pictures

def picture_card(seg, chap, out: Path):
    im = Image.new("RGB", (W, H), C["crust"])
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 18, H], fill=C["blue"])
    d.rectangle([18, 0, 26, H], fill=C["mauve"])
    y = 300
    if seg.get("kicker"):
        d.text((160, y), seg["kicker"].upper(), font=font(34, "Semibold"), fill=C["blue"])
        y += 70
    for line in wrap(d, seg["title"], font(96, "Bold"), W - 320):
        d.text((160, y), line, font=font(96, "Bold"), fill=C["text"])
        y += 116
    y += 20
    for line in wrap(d, seg.get("subtitle", ""), font(42), W - 320):
        rich(d, (160, y), line, font(42), C["sub"])
        y += 60
    d.text((160, H - 110), cfg("FOOTER", "a guided tour for the team"), font=font(28), fill=C["overlay"])
    im.save(out)


def box(d, x, y, w, h, title, body, color, dim=False):
    if dim:                                     # a diagram part the narration is not on yet
        color = C["surface"]
    d.rounded_rectangle([x, y, x + w, y + h], radius=22, fill=C["mantle"] if not dim else C["bg"], outline=color,
                        width=4 if dim else 7)
    d.text((x + 28, y + 24), title, font=font(40, "Bold"), fill=color if not dim else C["overlay"])
    yy = y + 90
    for line in body:
        for wl in wrap(d, line, font(31), w - 56, mono=font(28, mono=True)):
            rich(d, (x + 28, yy), wl, font(31), C["text"] if not dim else C["overlay"],
                 code_fill=None if not dim else C["overlay"], mono=font(28, mono=True))
            yy += 44


def arrow(d, x1, y1, x2, y2, color):
    d.line([x1, y1, x2, y2], fill=color, width=5)
    a = math.atan2(y2 - y1, x2 - x1)
    L = 22
    p1 = (x2 - L * math.cos(a - 0.45), y2 - L * math.sin(a - 0.45))
    p2 = (x2 - L * math.cos(a + 0.45), y2 - L * math.sin(a + 0.45))
    d.polygon([(x2, y2), p1, p2], fill=color)


def header(d, chap, seg=None):
    d.rectangle([0, 0, W, HEAD], fill=C["mantle"])
    d.text((40, 20), f"{chap['num']}  {chap['title']}", font=font(30, "Semibold"), fill=C["blue"])
    step = (seg or {}).get("step", "")
    if step:                                    # the step badge, top right
        tw = d.textlength(step, font=font(28, "Semibold"))
        d.rounded_rectangle([W - tw - 80, 14, W - 36, 62], radius=24, fill=C["blue"])
        d.text((W - tw - 58, 20), step, font=font(28, "Semibold"), fill=C["crust"])


def picture_slide(seg, chap, out: Path):
    im = Image.new("RGB", (W, H), C["bg"])
    d = ImageDraw.Draw(im)
    header(d, chap, seg)
    d.text((96, 120), seg["title"], font=font(64, "Bold"), fill=C["text"])
    y = 240
    boxes = seg.get("boxes")
    if boxes and not seg.get("bullets"):        # centre a box-only slide in the free space
        rows_ = seg.get("rows", 1)
        block = rows_ * (seg.get("box_h", 300) + 60) - 60
        bottom = H - 170 if seg.get("note") else H - 60
        y = max(240, 240 + (bottom - 240 - block) // 2)
    if boxes:                                   # a row (or rows) of boxes joined by arrows
        rows = seg.get("rows", 1)
        per = (len(boxes) + rows - 1) // rows
        gap = 70
        bw = (W - 192 - gap * (per - 1)) // per
        bh = seg.get("box_h", 300)
        colors = [C["blue"], C["mauve"], C["peach"], C["green"], C["teal"], C["yellow"], C["red"], C["sky"]]
        for i, b in enumerate(boxes):
            r, c = divmod(i, per)
            x = 96 + c * (bw + gap)
            yy = y + r * (bh + 60)
            col = C.get(b.get("color", ""), colors[i % len(colors)])
            lit = seg.get("lit")                # diagram: only these boxes are lit; None = all
            box(d, x, yy, bw, bh, b["title"], b.get("body", []), col, dim=lit is not None and i not in lit)
            if c < per - 1 and i < len(boxes) - 1 and seg.get("arrows", True):
                on = lit is None or (i in lit and i + 1 in lit)
                arrow(d, x + bw + 8, yy + bh // 2, x + bw + gap - 8, yy + bh // 2, C["overlay"] if on else C["surface"])
        y += rows * (bh + 60) + 10
    for b in seg.get("bullets", []):
        sub = b.startswith("  ")                # two leading spaces = sub-bullet
        fnt = font(32 if sub else 38, "Regular" if sub else "Medium")
        x0 = 160 if sub else 110
        d.ellipse([x0 - 30, y + 17, x0 - 16, y + 31], fill=C["overlay"] if sub else C["blue"])
        for line in wrap(d, b.strip(), fnt, W - x0 - 120):
            rich(d, (x0, y), line, fnt, C["sub"] if sub else C["text"], mono=font(fnt.size - 3, mono=True))
            y += 50 if not sub else 44
        y += 14
    if seg.get("note"):
        d.rounded_rectangle([96, H - 150, W - 96, H - 60], radius=16, fill=C["surface"])
        rich(d, (130, H - 128), seg["note"], font(32, "Medium"), C["yellow"], mono=font(29, mono=True))
    im.save(out)


def picture_frame(seg, chap, out: Path):
    """Transparent overlay for a terminal segment: header bar on top (+ step pill), caption bar at the bottom."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    header(d, chap, seg)
    d.rectangle([0, CAP_Y, W, H], fill=C["crust"])
    d.rectangle([0, CAP_Y, 10, H], fill=C["yellow"])
    cap = seg.get("caption", "")
    fnt = font(34, "Medium")
    if len(wrap(d, cap, fnt, W - 120)) > 1:      # two lines: shrink so they fit the bar
        fnt = font(29, "Medium")
    lines = wrap(d, cap, fnt, W - 120)[:2]
    y = CAP_Y + (H - CAP_Y - 46 * len(lines)) // 2
    for line in lines:
        rich(d, (50, y), line, fnt, C["text"], code_fill=C["peach"], mono=font(fnt.size - 3, mono=True))
        y += 46
    im.save(out)


# ---------------------------------------------------------------- audio / video helpers

def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        sys.exit(f"FAILED: {' '.join(map(str, cmd))}\n{r.stdout[-3000:]}\n{r.stderr[-3000:]}")
    return r.stdout


def duration(p: Path) -> float:
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]))


# How the voice should pronounce common tokens. script.py can add or override entries with SPOKEN = {...}.
BASE_SPOKEN = {
    r"\bMCP\b": "M C P", r"\bCLI\b": "C L I", r"\bCLIs\b": "C L Is", r"\bCI\b": "C I", r"\bCD\b": "C D",
    r"\bDAG\b": "dag", r"\bDAGs\b": "dags", r"\bjq\b": "J Q", r"\bYAML\b": "yammel", r"\bJSON\b": "jason",
    r"\buv\b": "U V", r"\bSQL\b": "sequel", r"\bPII\b": "P I I", r"\bADR\b": "A D R", r"\bADRs\b": "A D Rs",
    r"\bVHS\b": "V H S", r"\bAPI\b": "A P I", r"\bAPIs\b": "A P Is", r"\bpytest\b": "pie-test",
    r"\bpsql\b": "P S Q L", r"\bLLM\b": "L L M", r"\bID\b": "I D", r"\bids\b": "I Ds", r"\bsha256\b": "shah 256",
    r"\bpreprod\b": "pre-prod", r"\bREADME\b": "read me", r"\bnpm\b": "N P M", r"\bURL\b": "U R L",
    r"\bHTTP\b": "H T T P", r"\bk8s\b": "kubernetes", r"\bSemVer\b": "semver", r"\bTTL\b": "T T L",
    r"\b(\w+)\.md\b": r"\1 dot M D", r"\b(\w+)\.json\b": r"\1 dot jason", r"\b(\w+)\.ya?ml\b": r"\1 dot yammel",
    r"->": " to ", r"\be\.g\.": "for example", r"\bi\.e\.": "that is",
}


def spoken(text: str) -> str:
    """What the voice should say: no backticks, acronyms and file names spelled for the ear."""
    s = text.replace("`", "")
    for a, b in {**BASE_SPOKEN, **cfg("SPOKEN", {})}.items():
        s = re.sub(a, b, s)
    return s


def sentences(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"(?<=[.!?])\s+", text.strip()) if p.strip()]


def kokoro():
    global _KOKORO
    if _KOKORO is None:
        from kokoro_onnx import Kokoro
        onnx, voices = KOKORO_MODELS / "kokoro-v1.0.onnx", KOKORO_MODELS / "voices-v1.0.bin"
        if not (onnx.exists() and voices.exists()):
            sys.exit(f"Kokoro model files are missing in {KOKORO_MODELS}: run the skill's scripts/setup.sh "
                     "(or set KOKORO_MODELS, or VOICE_ENGINE=say)")
        _KOKORO = Kokoro(str(onnx), str(voices))
    return _KOKORO


def voice(text: str, out: Path) -> tuple[float, list[tuple[float, float]]]:
    """Narrate text into out (48 kHz stereo WAV). Returns the duration and each sentence's (start, end)."""
    parts = sentences(text) or [text]
    raw = out.with_suffix(".raw.wav")
    if VOICE_ENGINE == "kokoro":
        import numpy as np
        import soundfile as sf
        sr, chunks, times, t = 24000, [], [], 0.0
        for p in parts:
            audio, sr = kokoro().create(spoken(p), voice=VOICE, speed=SPEED, lang="en-us")
            loud = np.where(np.abs(audio) > 0.012)[0]               # trim silence, keep 20 ms
            if len(loud):
                audio = audio[max(loud[0] - 480, 0): loud[-1] + 480]
            d = len(audio) / sr
            times.append((round(t, 3), round(t + d, 3)))
            chunks += [audio, np.zeros(int(SENTENCE_GAP * sr), dtype=np.float32)]
            t += d + SENTENCE_GAP
        sf.write(raw, np.concatenate(chunks), sr)
    else:                                                           # macOS say: one take, times by length
        raw = out.with_suffix(".aiff")
        run(["say", "-v", VOICE, "-r", RATE, "-o", str(raw), spoken(text)])
        total, n = duration(raw), sum(len(p) for p in parts) or 1
        times, t = [], 0.0
        for p in parts:
            d = total * len(p) / n
            times.append((round(t, 3), round(t + d, 3)))
            t += d
    run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af", "apad=pad_dur=0.6", "-ar", "48000", "-ac", "2",
         str(out)])
    raw.unlink()
    return duration(out), times


def q(text: str) -> str:
    """Quote for a VHS tape: VHS strings take no escapes, so pick a delimiter the text does not contain."""
    for d in ('"', "'", "`"):
        if d not in text:
            return d + text + d
    raise ValueError(f"cannot quote for VHS (contains \" ' and `): {text}")


def workdir(seg):
    cwd = seg.get("cwd") or "main"
    return SCRIPT.WORKDIRS.get(cwd, cwd)


def tape_for(seg, clip: Path) -> str:
    env = seg.get("env", {})
    prompt = seg.get("prompt", cfg("PROMPT", "repo"))
    setup = [f"cd {workdir(seg)}",
             "export PS1='\\[\\e[1;36m\\]" + prompt + "\\[\\e[0m\\] \\[\\e[1;33m\\]$\\[\\e[0m\\] '",
             "export TERM=xterm-256color COLUMNS=140", "export UV_NO_PROGRESS=1"]
    setup += [f"export {k}={v}" for k, v in {**cfg("ENV", {}), **env}.items()]
    setup += seg.get("setup", [])
    lines = [f"Output {clip.name}", 'Set Shell "bash"', "Set FontSize 22", f"Set Width {W}", f"Set Height {TERM_H}",
             'Set Theme "Catppuccin Mocha"', "Set Padding 28", "Set Framerate 15", "Set TypingSpeed 22ms",
             "Set CursorBlink false", "Set WaitTimeout 600s", r"Set WaitPattern /[>$]$/",
             "Hide"]
    for s in setup:
        lines.append(f"Type {q(s)} Enter")
        lines.append("Wait")
    lines += ['Type "clear" Enter', "Wait", "Sleep 300ms", "Show", "Sleep 600ms"]
    for c in seg["cmds"]:
        if isinstance(c, dict):
            if "sleep" in c:
                lines.append(f"Sleep {c['sleep']}s")
                continue
            if c.get("clear"):
                lines += ["Hide", 'Type "clear" Enter', "Wait", "Show"]
                continue
            cmd, pause = c["cmd"], c.get("pause", 1.6)
        else:
            cmd, pause = c, 1.6
        speed = "12ms" if len(cmd) > 90 else "22ms"
        lines += [f"Type@{speed} {q(cmd)}", "Sleep 350ms", "Enter", "Wait", f"Sleep {pause}s"]
    lines.append("Sleep 1s")
    return "\n".join(lines) + "\n"


def as_term(seg):
    """An `api` scene is a terminal scene: one `req` call per entry of `calls`, then the `then` effect checks."""
    if seg["type"] != "api":
        return seg
    cmds = []
    for c in seg["calls"]:
        cmd = f"req {c.get('method', 'GET')} {c['path']}"
        if "json" in c:
            body = json.dumps(c["json"], ensure_ascii=False)
            if "'" in body:                                  # VHS can't escape: put the body in a file
                f = BUILD / "bodies" / (hashlib.sha256(body.encode()).hexdigest()[:10] + ".json")
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(body)
                cmd += f" -d @{f}"
            else:
                cmd += f" -d '{body}'"
        for k, v in c.get("headers", {}).items():
            cmd += f" -H '{k}: {v}'"
        if c.get("show"):
            cmd += f" --show '{c['show']}'"
        cmds.append({"cmd": cmd, "pause": c.get("pause", 2.5)})
    setup = [f'req() {{ python3 {Path(__file__).with_name("req.py")} "$@"; }}', f"export REQ_BASE={seg['base']}"]
    return {**seg, "type": "term", "cmds": cmds + list(seg.get("then", [])), "setup": setup + seg.get("setup", [])}


def make_segment(seg, chap, idx: int, out: Path):
    seg = as_term(seg)
    tmp = BUILD / chap["num"] / f"{idx:02d}"
    tmp.mkdir(parents=True, exist_ok=True)
    voice_wav = tmp / "voice.wav"
    vdur, _times = voice(seg["say"], voice_wav)
    if seg["type"] == "diagram":                # one picture per sentence, each held while it is spoken
        n = len(seg["boxes"])
        steps = seg.get("steps") or [[min(k, n - 1)] for k in range(len(_times))]
        total = max(vdur, seg.get("min", 0)) + 0.4
        starts = [0.0] + [a for a, _ in _times[1:]]
        lst = tmp / "lit.txt"
        rows = []
        for k, a in enumerate(starts):
            png = tmp / f"lit-{k}.png"
            picture_slide({**seg, "lit": set(steps[min(k, len(steps) - 1)])}, chap, png)
            end = starts[k + 1] if k + 1 < len(starts) else total
            rows += [f"file '{png}'", f"duration {end - a:.3f}"]
        rows.append(f"file '{tmp / f'lit-{len(starts) - 1}.png'}'")   # concat needs the last file twice
        lst.write_text("\n".join(rows) + "\n")
        run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-i", str(voice_wav),
             "-t", f"{total:.2f}", "-vf", f"fps={FPS},format=yuv420p", "-c:v", "libx264", "-preset", "slow",
             "-crf", "16", "-tune", "stillimage", "-c:a", "aac", "-b:a", "192k", "-af", "apad", str(out)])
        return total, _times
    if seg["type"] in ("card", "slide", "section", "concept"):
        png = tmp / "pic.png"
        {"card": picture_card, "slide": picture_slide, "section": picture_section,
         "concept": picture_concept}[seg["type"]](seg, chap, png)
        dur = max(vdur, seg.get("min", 2.5 if seg["type"] == "section" else 0)) + 0.4
        run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", str(FPS), "-i", str(png), "-i", str(voice_wav),
             "-t", f"{dur:.2f}", "-vf", "format=yuv420p", "-c:v", "libx264", "-preset", "slow", "-crf", "16",
             "-tune", "stillimage", "-c:a", "aac", "-b:a", "192k", "-af", "apad", "-shortest", str(out)])
        return dur, _times
    trim = 0.0
    if seg["type"] == "browser":
        clip, meta = tmp / "screen.webm", tmp / "browser.json"
        if not (REUSE_TERMS and clip.exists() and meta.exists()):
            scene = tmp / "scene.json"
            scene.write_text(json.dumps({"url": seg["url"], "steps": seg.get("steps", []), "width": W,
                                         "height": TERM_H}))
            outp = run([sys.executable, str(Path(__file__).with_name("browser.py")), "record", str(scene), str(clip)])
            res = json.loads(outp.strip().splitlines()[-1])
            if not res.get("ok"):
                sys.exit(f"browser scene failed in chapter {chap['num']}:\n{outp}")
            meta.write_text(json.dumps(res))
        trim = json.loads(meta.read_text()).get("trim", 0.0)
    else:                                       # terminal
        clip = tmp / "term.mp4"
        tape = tmp / "seg.tape"
        if not (REUSE_TERMS and clip.exists()):     # --reuse-terms: keep the recording, redo voice and frame
            tape.write_text(tape_for(seg, clip))
            run(["vhs", str(tape)], cwd=tmp)        # VHS wants a bare Output file name: run it in the folder
    cdur = duration(clip) - trim
    frame = tmp / "frame.png"
    speed = ""
    if seg.get("speedup") and cdur > max(vdur, 25) * 1.2:
        factor = cdur / max(vdur, 25)
        speed = f"setpts=PTS/{factor:.3f},"
        cdur = cdur / factor + 10                       # hold the final answer on screen
        seg = {**seg, "step": f"{seg.get('step', '')}  ·  sped up ×{factor:.1f}".strip(" ·")}
    picture_frame(seg, chap, frame)
    dur = max(vdur, cdur) + 0.3
    vf = (f"[0:v]{speed}fps={FPS},pad={W}:{H}:0:{HEAD}:color={C['bg']},"
          f"tpad=stop_mode=clone:stop_duration={dur:.2f}[t];[t][1:v]overlay=0:0,format=yuv420p[v]")
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{trim:.2f}", "-i", str(clip), "-loop", "1", "-i", str(frame),
         "-i", str(voice_wav),
         "-filter_complex", vf, "-map", "[v]", "-map", "2:a", "-af", "apad", "-t", f"{dur:.2f}",
         "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-c:a", "aac", "-b:a", "192k", str(out)])
    return dur, _times


def srt_time(t: float) -> str:
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s % 1) * 1000):03d}"


def subtitle_chunks(text: str, start: float, end: float, times=None):
    """Split a narration into sentence chunks: at the voice's real sentence times when known, else by length."""
    text = text.replace("`", "")
    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", text) if p.strip()]
    if times and len(times) == len(parts):
        for (a, b), p in zip(times, parts):
            pieces = textwrap.wrap(p, 110) if len(p) > 110 else [p]
            n = sum(len(x) for x in pieces) or 1
            t = start + a
            for x in pieces:
                d = (b - a) * len(x) / n
                yield t, t + d, x
                t += d
        return
    chunks = []
    for p in parts:
        chunks += textwrap.wrap(p, 110) if len(p) > 110 else [p]
    total = sum(len(c) for c in chunks) or 1
    t, span = start, max(end - start - 0.6, 0.5)
    for c in chunks:
        d = span * len(c) / total
        yield t, t + d, c
        t += d


def run_hooks(chap):
    for hook in chap.get("before", []):
        subprocess.run(hook, shell=True, executable="/bin/bash", cwd=SCRIPT.WORKDIRS.get("main"),
                       env={**os.environ, **cfg("ENV", {})}, capture_output=True)


def build_chapter(chap, force=False):
    CHAPTERS.mkdir(exist_ok=True)
    out = CHAPTERS / f"{chap['num']}-{chap['slug']}.mp4"
    meta = BUILD / chap["num"] / "meta.json"
    key = hashlib.sha256(json.dumps([chap, VOICE_ENGINE, VOICE, SPEED, RATE], sort_keys=True).encode()).hexdigest()
    if out.exists() and meta.exists() and json.loads(meta.read_text()).get("key") == key and not force:
        print(f"= {out.name} (unchanged)")
        return json.loads(meta.read_text())
    print(f"> chapter {chap['num']} {chap['title']}", flush=True)
    if not REUSE_TERMS:
        run_hooks(chap)
    segs, timeline, t = [], [], 0.0
    for i, seg in enumerate(chap["segments"]):
        p = BUILD / chap["num"] / f"{i:02d}.mp4"
        print(f"  - {i:02d} {seg['type']:5} {seg.get('title') or seg.get('caption', '')[:70]}", flush=True)
        d, times = make_segment(seg, chap, i, p)
        segs.append(p)
        timeline.append({"start": t, "end": t + d, "say": seg["say"], "times": times})
        t += d
    lst = BUILD / chap["num"] / "list.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in segs))
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy",
         "-movflags", "+faststart", str(out)])
    m = {"key": key, "num": chap["num"], "title": chap["title"], "file": out.name, "duration": t,
         "timeline": timeline}
    meta.write_text(json.dumps(m, indent=1))
    print(f"  = {out.name} {t / 60:.1f} min", flush=True)
    return m


def assemble(metas):
    name = cfg("OUTPUT_NAME", "walkthrough")
    final = ROOT / f"{name}.mp4"
    lst = BUILD / "all.txt"
    lst.write_text("".join(f"file '{CHAPTERS / m['file']}'\n" for m in metas))
    ffmeta = [";FFMETADATA1", f"title={cfg('TITLE', 'A guided tour')}", f"artist={cfg('AUTHOR', 'the team')}"]
    srt, n, t0 = [], 1, 0.0
    for m in metas:
        ffmeta += ["[CHAPTER]", "TIMEBASE=1/1000", f"START={int(t0 * 1000)}",
                   f"END={int((t0 + m['duration']) * 1000)}", f"title={m['num']} {m['title']}"]
        for seg in m["timeline"]:
            for a, b, c in subtitle_chunks(seg["say"], t0 + seg["start"], t0 + seg["end"], seg.get("times")):
                srt.append(f"{n}\n{srt_time(a)} --> {srt_time(b)}\n{c}\n")
                n += 1
        t0 += m["duration"]
    (BUILD / "meta.txt").write_text("\n".join(ffmeta) + "\n")
    srt_path = ROOT / f"{name}.srt"
    srt_path.write_text("\n".join(srt))
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-i", str(BUILD / "meta.txt"),
         "-i", str(srt_path), "-map", "0:v", "-map", "0:a", "-map", "2:s", "-map_metadata", "1",
         "-map_chapters", "1", "-c:v", "copy", "-c:a", "copy", "-c:s", "mov_text", "-metadata:s:s:0",
         "language=eng", "-movflags", "+faststart", str(final)])
    print(f"\n{final}  {t0 / 60:.1f} min")
    return t0


def dry(chaps):
    for chap in chaps:
        print(f"\n######## {chap['num']} {chap['title']}")
        run_hooks(chap)
        for seg in map(as_term, chap["segments"]):
            if seg["type"] == "browser":
                print(f"$ browser {seg['url']}")
                scene = BUILD / "dry-scene.json"
                BUILD.mkdir(exist_ok=True)
                scene.write_text(json.dumps({"url": seg["url"], "steps": seg.get("steps", [])}))
                r = subprocess.run([sys.executable, str(Path(__file__).with_name("browser.py")), "dry", str(scene)],
                                   capture_output=True, text=True)
                print((r.stdout + r.stderr).rstrip())
                continue
            if seg["type"] != "term":
                continue
            env = {**os.environ, **cfg("ENV", {}), **seg.get("env", {})}
            pre = "; ".join(seg.get("setup", []))
            for c in seg["cmds"]:
                cmd = c if isinstance(c, str) else c.get("cmd")
                if not cmd:
                    continue
                r = subprocess.run(f"{pre}\n{cmd}" if pre else cmd, shell=True, executable="/bin/bash",
                                   cwd=workdir(seg), env=env, capture_output=True, text=True, timeout=900)
                outp = (r.stdout + r.stderr).rstrip().splitlines()
                print(f"$ {cmd}   [exit {r.returncode}, {len(outp)} lines]")
                for line in outp[:40]:
                    print("    " + line[:150])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", help="chapter numbers, e.g. --only 04 05")
    ap.add_argument("--dry", action="store_true", help="run the terminal commands in bash, print output, no video")
    ap.add_argument("--force", action="store_true", help="rebuild even unchanged chapters")
    ap.add_argument("--no-assemble", action="store_true")
    ap.add_argument("--reuse-terms", action="store_true", help="keep recorded terminal and browser scenes, redo voice/frames")
    a = ap.parse_args()
    REUSE_TERMS = a.reuse_terms
    sys.path.insert(0, str(Path(__file__).parent))
    import script as SCRIPT  # noqa: E402
    chaps = [c for c in number_steps(SCRIPT.CHAPTERS) if not a.only or c["num"] in a.only]
    if a.dry:
        dry(chaps)
        sys.exit()
    BUILD.mkdir(exist_ok=True)
    metas = [build_chapter(c, force=a.force) for c in chaps]
    if not a.no_assemble and not a.only:
        assemble(metas)
