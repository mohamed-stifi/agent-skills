"""Video engine (demo-video skill): turns the chapter script (script.py, next to this file) into narrated, captioned
1080p MP4s.

Each segment is one of:
  card   - full-screen title card (Pillow), narrated
  slide  - full-screen slide: title + bullets and/or a row of boxes joined by arrows (Pillow), narrated
  term   - a real terminal session recorded by VHS (1920x900), framed with a header and a caption bar
  browser - a real Chromium used like a person (Playwright, scripts/browser.py), framed the same way
  api    - real HTTP calls typed as curl (| jq), then effect checks: a terminal scene
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

script.py must define CHAPTERS and WORKDIRS; optional: ENV, TITLE, FOOTER, AUTHOR, PROMPT, OUTPUT_NAME, SPOKEN,
VIEWER_HAS. Before a dry run or a recording, every typed command is checked: one the viewer doesn't have (a helper
written for the video, a function from a hidden setup) stops the run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import select
import shlex
import shutil
import subprocess
import sys
import textwrap
import time
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


def q_parts(text: str) -> list[str]:
    """Any text as VHS strings: split it into runs that each leave out one of " ' `, typed one after another."""
    parts, cur = [], ""
    for ch in text:
        if any(d not in cur + ch for d in "\"'`"):
            cur += ch
        else:
            parts.append(q(cur))
            cur = ch
    return parts + ([q(cur)] if cur else [])


def sh_quote(s: str) -> str:
    return "'" + s.replace("'", "'\\''") + "'"


def curl_cmd(base: str, c: dict) -> str:
    """One `api` call as the curl line a viewer would type: the full URL, the body, and jq to read the answer.
    `"status": True` uses `curl -si` instead, whose first line is the HTTP status."""
    url = c["path"] if c["path"].startswith(("http://", "https://")) else base.rstrip("/") + c["path"]
    method = c.get("method", "GET").upper()
    cmd = "curl -s" + ("i" if c.get("status") else "") + ("" if method == "GET" else f" -X {method}") + f" {url}"
    for k, v in c.get("headers", {}).items():
        cmd += " -H " + sh_quote(f"{k}: {v}")
    if "json" in c:
        cmd += " -H 'Content-Type: application/json' -d " + sh_quote(json.dumps(c["json"], ensure_ascii=False))
    if not c.get("status"):
        cmd += " | jq" + (" " + sh_quote(c["show"]) if c.get("show") else "")
    return cmd


# --- the viewer's commands: everything typed on screen must be something the viewer has too -----------------------
WRAPPERS = {"sudo", "env", "time", "exec", "command", "nohup", "xargs", "watch", "then", "do", "else", "!"}
DEFINED = re.compile(r"(?:^|[;&|\s])(?:function\s+)?([A-Za-z_][\w.-]*)\s*\(\)|\balias\s+([A-Za-z_][\w.-]*)=")


def typed_programs(cmd: str):
    """(program, its arguments) for each simple command of a shell line, after VAR=value and sudo/env/time."""
    lex = shlex.shlex(cmd, posix=True, punctuation_chars=";&|()")
    lex.whitespace_split = True
    try:
        words = list(lex)
    except ValueError:                                  # unbalanced quotes: let the dry run show the error
        return []
    out, cur = [], None
    for w in words:
        if set(w) <= set(";&|()"):
            cur = None
        elif cur is None:
            if re.fullmatch(r"[A-Za-z_]\w*=.*", w) or w in WRAPPERS or w.startswith(("-", "$")):
                continue
            cur = (w, [])
            out.append(cur)
        else:
            cur[1].append(w)
    return out


def origin(p: Path, workdirs: list[Path]):
    """Why a file is not the viewer's (None when it is: a system tool, or tracked or installed in the clone)."""
    p = p.resolve()
    if any(p.is_relative_to(ROOT / d) for d in ("src", "build")):
        return "a file of the video itself"
    for w in sorted(workdirs, key=lambda x: -len(x.parts)):
        if p.is_relative_to(w) and not ROOT.is_relative_to(w):
            git = lambda *a: subprocess.run(["git", "-C", str(w), *a, str(p)], capture_output=True).returncode == 0
            return None if git("ls-files", "--error-unmatch") or git("check-ignore", "-q") else \
                "a file added to the clone (not tracked by git, not made by its install)"
    return "a file of the video folder, outside the clone" if p.is_relative_to(ROOT) else None


def viewer_problems(chaps) -> list[str]:
    """Every typed command whose program (or script argument) the viewer does not have: a helper written for the
    recording, a function or alias from a hidden `setup`, or a video folder put on PATH. VIEWER_HAS lists files
    the viewer saw being made on screen earlier."""
    workdirs = [Path(os.path.expanduser(str(v))).resolve() for v in SCRIPT.WORKDIRS.values()]
    has = set(cfg("VIEWER_HAS", []))
    problems = []
    for chap in chaps:
        for i, seg in enumerate(map(as_term, chap["segments"])):
            if seg["type"] != "term":
                continue
            cwd = Path(os.path.expanduser(str(workdir(seg))))
            path = {**os.environ, **cfg("ENV", {}), **seg.get("env", {})}.get("PATH", os.environ.get("PATH", ""))
            hidden = {a or b for s in seg.get("setup", []) for a, b in DEFINED.findall(s)}
            for c in seg["cmds"]:
                cmd = c if isinstance(c, str) else c.get("cmd")
                for prog, args in typed_programs(cmd or ""):
                    where = f"chapter {chap['num']} scene {i}: `{prog}`"
                    if prog in has or Path(prog).name in has:
                        continue
                    if prog in hidden:
                        problems.append(f"{where} is defined in the scene's hidden setup")
                        continue
                    found = (cwd / os.path.expanduser(prog)) if "/" in prog else shutil.which(prog, path=path)
                    why = found and Path(found).exists() and origin(Path(found), workdirs)
                    if why:
                        problems.append(f"{where} is {why} ({Path(found).resolve()})")
                    for a in args:                     # bash helper.sh, jq -f filter.jq, curl -d @body.json
                        a = a.split("=", 1)[-1].lstrip("@")
                        if not a or a in has or Path(a).name in has:
                            continue
                        f = cwd / os.path.expanduser(a)
                        if f.is_file() and (r := origin(f, workdirs)) == "a file of the video itself":
                            problems.append(f"{where} reads {a}, {r}")
    return problems


def check_viewer_commands(chaps):
    problems = viewer_problems(chaps)
    if problems:
        print("These commands are not ones the viewer has, so they can't follow along:", *problems, sep="\n  - ")
        print("Type the project's real command instead (long is fine; explain it once). If the project has no command\n"
              "for this, say so on screen as a finding. A file the viewer made on screen earlier goes in VIEWER_HAS.")
        sys.exit(1)


def workdir(seg):
    cwd = seg.get("cwd") or "main"
    return SCRIPT.WORKDIRS.get(cwd, cwd)


def tape_for(seg, clip: Path, rc: Path | None = None) -> str:
    prompt = seg.get("prompt", cfg("PROMPT", "\\W"))                # default: the current folder's name
    setup = scene_setup(seg) + ["export PS1='\\[\\e[1;36m\\]" + prompt + "\\[\\e[0m\\] \\[\\e[1;33m\\]$\\[\\e[0m\\] '"]
    lines = [f"Output {clip.name}", 'Set Shell "bash"', "Set FontSize 22", f"Set Width {W}", f"Set Height {TERM_H}",
             'Set Theme "Catppuccin Mocha"', "Set Padding 28", "Set Framerate 15", "Set TypingSpeed 22ms",
             "Set CursorBlink false", "Set WaitTimeout 600s", r"Set WaitPattern /[>$]$/",
             "Hide"]
    for s in setup:
        lines += [f"Type {p}" for p in q_parts(s)] + ["Enter"]
        lines.append("Wait")
    start = rc_start(rc) if rc else "clear"             # from here on, each command's exit status goes to rc
    lines += [f"Type {p}" for p in q_parts(start)] + ["Enter", "Wait", "Sleep 300ms", "Show", "Sleep 600ms"]
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
        lines += [f"Type@{speed} {p}" for p in q_parts(cmd)] + ["Sleep 350ms", "Enter", "Wait", f"Sleep {pause}s"]
    lines.append("Sleep 1s")
    return "\n".join(lines) + "\n"


def scene_setup(seg):
    """The hidden lines that start every terminal scene, in VHS and in the dry run alike."""
    lines = [f"cd {workdir(seg)}", "export TERM=xterm-256color COLUMNS=140", "export UV_NO_PROGRESS=1"]
    lines += [f"export {k}={v}" for k, v in {**cfg("ENV", {}), **seg.get("env", {})}.items()]
    return lines + seg.get("setup", [])


def rc_start(rc: Path) -> str:
    """Hidden: empty the status file, then after every command append its exit codes, one per command of the
    pipe (PIPESTATUS), before any PROMPT_COMMAND the scene already has. Nothing shows on screen."""
    assert "'" not in str(rc) and '"' not in str(rc), rc
    return (f": > {rc}; PROMPT_COMMAND='__dv_s=\"${{PIPESTATUS[*]}}\"; echo \"$__dv_s\" >> {rc}'"
            '"${PROMPT_COMMAND:+; $PROMPT_COMMAND}"; clear')


def typed(seg):
    """The typed commands of a terminal scene in order, as dicts; None for a hidden `clear`."""
    for c in seg["cmds"]:
        if isinstance(c, dict) and "sleep" in c:
            continue
        yield None if isinstance(c, dict) and c.get("clear") else (c if isinstance(c, dict) else {"cmd": c})


BACKGROUND = re.compile(r"(^|[^&>])&(\s*$|\s*;|\s+\S)")


def stop(where: str, what: str, chap=None):
    """Stop the build at the first failure, so no broken scene gets recorded after it."""
    hint = ""
    started = [c.get("cmd", "") for s in (chap or {}).get("segments", []) if s.get("cmds")
               for c in typed(s) if c and BACKGROUND.search(c.get("cmd", ""))]
    if any("nohup" not in c and "disown" not in c for c in started):
        hint = ("\nHint: a program started with `&` stops when its scene's terminal closes. Start it the way a "
                "person leaves a service running: `nohup <command> > <log> 2>&1 &` then `disown`.")
    sys.exit(f"STOPPED at {where}: {what}{hint}\nIf this failure is meant to be shown, mark the command "
             '{"cmd": ..., "fails": True}.')


def failed(c: dict, statuses: list[int]) -> bool:
    """A command failed when its last part did, or an earlier part of its pipe did (SIGPIPE, 141, aside)."""
    return not c.get("fails") and bool(statuses) and (
        statuses[-1] != 0 or any(x not in (0, 141) for x in statuses[:-1]))


def check_statuses(seg, where, chap, rc: Path):
    lines = rc.read_text().splitlines()[1:] if rc.exists() else []      # [0]: the hidden line that started it
    for c, line in zip(typed(seg), lines):
        st = [int(x) for x in line.split() if x.isdigit()]
        if c and failed(c, st):
            stop(where, f"`{c['cmd']}` exited {' | '.join(map(str, st))}", chap)


SERVICE_UP: set = set()


def check_services(where, chap, baseline=False):
    """Each SERVICES check that has passed once must keep passing (a service killed by a scene is caught at
    once). After a chapter's before-hooks, the checks only set the new baseline."""
    for name, svc in cfg("SERVICES", {}).items():
        r = subprocess.run(svc["check"], shell=True, executable="/bin/bash", cwd=SCRIPT.WORKDIRS.get("main"),
                           env={**os.environ, **cfg("ENV", {})}, capture_output=True, timeout=svc.get("timeout", 20))
        if r.returncode == 0:
            SERVICE_UP.add(name)
        elif baseline:
            SERVICE_UP.discard(name)
        elif name in SERVICE_UP:
            stop(where, f"the service `{name}` stopped answering (`{svc['check']}` exited {r.returncode})", chap)


def after_scene(seg, where, chap):
    for name in seg.get("stops", []):                   # a scene that stops a service on purpose
        SERVICE_UP.discard(name)
    check_services(where, chap)


def as_term(seg):
    """An `api` scene is a terminal scene: one curl line per entry of `calls`, then the `then` effect checks."""
    if seg["type"] != "api":
        return seg
    cmds = [{"cmd": curl_cmd(seg["base"], c), "pause": c.get("pause", 2.5)} for c in seg["calls"]]
    return {**seg, "type": "term", "cmds": cmds + list(seg.get("then", []))}


# Scene options passed to browser.py: a saved sign-in, when the first page counts as open, a visible window.
BROWSER_OPTS = ("storage_state", "wait_until", "headless")


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
                                         "height": TERM_H, **{k: seg[k] for k in BROWSER_OPTS if k in seg}}))
            outp = run([sys.executable, str(Path(__file__).with_name("browser.py")), "record", str(scene), str(clip)])
            res = json.loads(outp.strip().splitlines()[-1])
            if not res.get("ok"):
                stop(f"chapter {chap['num']} scene {idx}", f"a browser step failed:\n{outp}", chap)
            meta.write_text(json.dumps(res))
        trim = json.loads(meta.read_text()).get("trim", 0.0)
    else:                                       # terminal
        clip = tmp / "term.mp4"
        tape = tmp / "seg.tape"
        if not (REUSE_TERMS and clip.exists()):     # --reuse-terms: keep the recording, redo voice and frame
            rc = tmp / "status.txt"
            tape.write_text(tape_for(seg, clip, rc))
            run(["vhs", str(tape)], cwd=tmp)        # VHS wants a bare Output file name: run it in the folder
            check_statuses(seg, f"chapter {chap['num']} scene {idx}", chap, rc)
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
        r = subprocess.run(hook, shell=True, executable="/bin/bash", cwd=SCRIPT.WORKDIRS.get("main"),
                           env={**os.environ, **cfg("ENV", {})}, capture_output=True, text=True)
        if r.returncode:
            stop(f"chapter {chap['num']}, before-hook", f"`{hook[:200]}` exited {r.returncode}\n"
                 + (r.stdout + r.stderr)[-1500:] + "\n(add `|| true` where a failure is fine)")
    check_services(f"chapter {chap['num']}", chap, baseline=True)


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
        if seg["type"] in ("term", "api", "browser"):
            after_scene(seg, f"chapter {chap['num']} scene {i}", chap)
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
         "language=eng", "-movie_timescale", "1000", "-movflags", "+faststart", str(final)])
    print(f"\n{final}  {t0 / 60:.1f} min")
    return t0


class Terminal:
    """One interactive bash on a terminal (a pty) per scene, as in VHS: `cd` and variables carry over between
    commands, and closing it at the end hangs up its jobs, so a service started with a bare `&` dies here too."""

    def __init__(self, seg):
        import pty
        self.pid, self.fd = pty.fork()
        if self.pid == 0:                                   # the child: bash without readline (no echo of input)
            os.execvpe("bash", ["bash", "--noprofile", "--norc", "--noediting", "-i"],
                       {**os.environ, "PS1": "", "PS2": ""})
        self.send("stty -echo; PROMPT_COMMAND='printf \"\\n__DV_RC %s\\n\" \"${PIPESTATUS[*]}\"'")
        self.read(30)
        for line in scene_setup(seg):
            self.send(line)
            self.read(120)

    def send(self, line):
        os.write(self.fd, (line + "\n").encode())

    def read(self, timeout):
        buf, end = b"", time.monotonic() + timeout
        while True:
            m = re.search(rb"__DV_RC ([0-9 ]*)\r?\n", buf)
            if m:
                out = buf[:m.start()].decode(errors="replace").replace("\r", "").strip("\n")
                return out, [int(x) for x in m.group(1).split()]
            if time.monotonic() > end:
                raise TimeoutError(buf.decode(errors="replace")[-600:])
            if select.select([self.fd], [], [], 1)[0]:
                try:
                    chunk = os.read(self.fd, 65536)
                except OSError:
                    chunk = b""
                if not chunk:
                    raise EOFError(buf.decode(errors="replace")[-600:])
                buf += chunk

    def close(self):
        os.close(self.fd)                                   # bash gets SIGHUP and passes it to its jobs
        for _ in range(50):
            if os.waitpid(self.pid, os.WNOHANG)[0]:
                return
            time.sleep(0.1)
        os.kill(self.pid, 9)
        os.waitpid(self.pid, 0)


def estimate(times, chaps):
    """Recording time ≈ the live work measured here + typing, pauses and rendering per scene."""
    extra = 0.0
    for chap in chaps:
        for seg in map(as_term, chap["segments"]):
            extra += len(seg.get("say", "").split()) / 2.6               # rendering ≈ the narration's length
            for c in (typed(seg) if seg["type"] == "term" else []):
                if c:
                    extra += 0.35 + len(c["cmd"]) * 0.022 + c.get("pause", 1.6)
            extra += 6 if seg["type"] in ("term", "browser") else 1
    live = sum(times.values())
    return live, live + extra


def dry(chaps):
    times = {}
    for chap in chaps:
        print(f"\n######## {chap['num']} {chap['title']}", flush=True)
        t0 = time.monotonic()
        run_hooks(chap)
        for i, seg in enumerate(map(as_term, chap["segments"])):
            where = f"chapter {chap['num']} scene {i}"
            if seg["type"] == "browser":
                print(f"$ browser {seg['url']}")
                scene = BUILD / "dry-scene.json"
                BUILD.mkdir(exist_ok=True)
                scene.write_text(json.dumps({"url": seg["url"], "steps": seg.get("steps", []),
                                             **{k: seg[k] for k in BROWSER_OPTS if k in seg}}))
                r = subprocess.run([sys.executable, str(Path(__file__).with_name("browser.py")), "dry", str(scene)],
                                   capture_output=True, text=True)
                print((r.stdout + r.stderr).rstrip(), flush=True)
                if r.returncode:
                    stop(where, "a browser step failed (above)", chap)
                after_scene(seg, where, chap)
                continue
            if seg["type"] != "term":
                continue
            term = Terminal(seg)
            try:
                for c in typed(seg):
                    if not c:
                        continue
                    if len(c["cmd"]) > 1000:
                        print(f"  (note: a {len(c['cmd'])}-character command; a terminal takes about 1,000 per line)")
                    term.send(c["cmd"])
                    try:
                        outp, st = term.read(c.get("timeout", 900))
                    except (TimeoutError, EOFError) as e:
                        stop(where, f"`{c['cmd']}` did not finish ({type(e).__name__}); last output:\n{e}", chap)
                    lines = outp.splitlines()
                    print(f"$ {c['cmd']}   [exit {' | '.join(map(str, st))}, {len(lines)} lines]")
                    for line in lines[:40]:
                        print("    " + line[:150])
                    sys.stdout.flush()
                    if failed(c, st):
                        stop(where, f"`{c['cmd']}` exited {' | '.join(map(str, st))}", chap)
                    check_services(where, chap)            # see services come up inside the scene too
            finally:
                term.close()
            after_scene(seg, where, chap)
        times[chap["num"]] = time.monotonic() - t0
        print(f"   (chapter {chap['num']}: {times[chap['num']]:.0f} s of live work)", flush=True)
    live, total = estimate(times, chaps)
    BUILD.mkdir(exist_ok=True)
    (BUILD / "dry-times.json").write_text(json.dumps(times))
    print(f"\nLive work: {live / 60:.1f} min. Recording these chapters will take about {total / 60:.0f} min "
          f"(rough: live work + typing, pauses and rendering). Tell the user before starting.")


# --- one recording at a time, and recordings that outlive the agent's session ----------------------------------
LOCK, PIDFILE, STATUS, LOG = (ROOT / "record.lock", ROOT / "record.pid", ROOT / "record.status.json",
                              ROOT / "record.log")


def take_lock():
    import fcntl
    fd = os.open(LOCK, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        holder = os.read(fd, 200).decode(errors="replace").strip()
        sys.exit(f"Another recording or dry run is running here ({holder or 'unknown pid'}); one at a time. "
                 f"See: bash run.sh engine.py --status")
    os.ftruncate(fd, 0)
    os.write(fd, f"pid {os.getpid()}".encode())
    return fd                                               # held until this process ends


def alive(pid: int) -> bool:
    r = subprocess.run(["ps", "-o", "command=", "-p", str(pid)], capture_output=True, text=True)
    return r.returncode == 0 and "engine.py" in r.stdout


def status():
    info = json.loads(PIDFILE.read_text()) if PIDFILE.exists() else None
    tail = LOG.read_text(errors="replace").splitlines()[-200:] if LOG.exists() else []
    chap = next((x for x in reversed(tail) if x.startswith("> chapter")), "")
    if info and alive(info["pid"]):
        print(f"state=running pid={info['pid']} since={time.strftime('%H:%M', time.localtime(info['started']))} "
              f"{chap}")
    elif STATUS.exists():
        st = json.loads(STATUS.read_text())
        print(f"state={'finished' if st['exit'] == 0 else 'failed'} exit={st['exit']} "
              f"ended={time.strftime('%H:%M', time.localtime(st['ended']))}")
    else:
        print("state=none (no detached recording here)")
    print(*("  " + x for x in tail[-4:]), sep="\n")


def detach(argv):
    """Start the recording as its own process: a new session whose parent exits at once, so it is not a child
    of the agent's shell any more; `caffeinate -i` keeps a Mac awake while it runs."""
    os.close(take_lock())                                   # refuse now if one is already running
    args = [x for x in argv if x != "--detach"]
    wrap = ["caffeinate", "-i"] if shutil.which("caffeinate") else []
    STATUS.unlink(missing_ok=True)
    with open(LOG, "a") as log:
        log.write(f"\n==== {time.strftime('%Y-%m-%d %H:%M:%S')} engine.py {' '.join(args)}\n")
        p = subprocess.Popen(wrap + ["bash", "run.sh", "engine.py", "--detached-child", *args],   # run.sh: same env
                             cwd=Path(__file__).parent, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                             start_new_session=True)
    PIDFILE.write_text(json.dumps({"pid": p.pid, "args": args, "started": time.time()}))
    print(f"Recording in the background (pid {p.pid}); it keeps going if this session ends.\n"
          f"Log: {LOG}\nCheck: bash run.sh engine.py --status")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", help="chapter numbers, e.g. --only 04 05")
    ap.add_argument("--dry", action="store_true", help="run the terminal commands in bash, print output, no video")
    ap.add_argument("--force", action="store_true", help="rebuild even unchanged chapters")
    ap.add_argument("--no-assemble", action="store_true")
    ap.add_argument("--reuse-terms", action="store_true", help="keep recorded terminal and browser scenes, redo voice/frames")
    ap.add_argument("--detach", action="store_true", help="record in the background, outliving this session")
    ap.add_argument("--status", action="store_true", help="is a detached recording running? how did the last end?")
    ap.add_argument("--detached-child", action="store_true", help=argparse.SUPPRESS)
    a = ap.parse_args()
    if a.status:
        status()
        sys.exit()
    REUSE_TERMS = a.reuse_terms
    sys.path.insert(0, str(Path(__file__).parent))
    import script as SCRIPT  # noqa: E402
    chaps = [c for c in number_steps(SCRIPT.CHAPTERS) if not a.only or c["num"] in a.only]
    check_viewer_commands(chaps)
    if a.detach:
        detach(sys.argv[1:])
        sys.exit()
    lock = take_lock()
    if a.dry:
        dry(chaps)
        sys.exit()
    code = 1
    try:
        BUILD.mkdir(exist_ok=True)
        if (BUILD / "dry-times.json").exists():
            times = json.loads((BUILD / "dry-times.json").read_text())
            live, total = estimate({k: v for k, v in times.items() if k in {c["num"] for c in chaps}}, chaps)
            print(f"Estimated recording time: about {total / 60:.0f} min.", flush=True)
        metas = [build_chapter(c, force=a.force) for c in chaps]
        if not a.no_assemble and not a.only:
            assemble(metas)
        code = 0
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else 1
        if not isinstance(e.code, int) and e.code:
            print(e.code, file=sys.stderr)
    finally:
        if a.detached_child:
            STATUS.write_text(json.dumps({"exit": code, "ended": time.time()}))
    sys.exit(code)
