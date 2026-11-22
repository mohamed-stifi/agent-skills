"""Write the companion doc <OUTPUT_NAME>.md (+ doc/ screenshots) from script.py and the built chapters.

Run after engine.py:  bash run.sh make_doc.py
One section per chapter (with its start time in the video); per scene: the narration as prose, then what to
do yourself: commands in bash blocks, API calls as curl, browser steps as numbered steps, and a screenshot.
"""

import json
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD, DOC = ROOT / "build", ROOT / "doc"
sys.path.insert(0, str(Path(__file__).parent))
import script as S  # noqa: E402
from engine import number_steps  # noqa: E402   (same "Step k of N" text as the video)

name = getattr(S, "OUTPUT_NAME", "walkthrough")
title = getattr(S, "TITLE", "A guided video")


def clock(t):
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{int(t % 60):02d}" if t >= 3600 else f"{int(t // 60):02d}:{int(t % 60):02d}"


def prose(text):
    return " ".join(text.split())


def shot(num, i, dur):
    """A frame near the end of the scene: what the viewer sees once the step is done."""
    clip = BUILD / num / f"{i:02d}.mp4"
    if not clip.exists():
        return None
    DOC.mkdir(exist_ok=True)
    png = DOC / f"{num}-{i:02d}.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(dur - 0.8, 0):.2f}", "-i", str(clip),
                    "-frames:v", "1", "-vf", "scale=1280:-2", str(png)], check=False)
    return png if png.exists() else None


def browser_steps(seg):
    out = [f"Open <{seg['url']}>."]
    for st in seg.get("steps", []):
        if "goto" in st: out.append(f"Open <{st['goto']}>.")
        elif "click" in st: out.append(f"Click `{st['click']}`.")
        elif "hover" in st: out.append(f"Point at `{st['hover']}`.")
        elif "type" in st: out.append(f"Type “{st['type']}”" + (f" into `{st['into']}`." if st.get("into") else "."))
        elif "press" in st: out.append(f"Press `{st['press']}`.")
        elif "scroll" in st: out.append(f"Scroll to `{st['scroll']}`." if isinstance(st["scroll"], str) else "Scroll down.")
        elif "expect" in st: out.append(f"You should see “{st['expect']}”.")
        elif "callout" in st:
            mark = "⚠️ **Careful:** " if st.get("tone") == "warn" else (st.get("icon", "") + " ").lstrip()
            out.append(f"{mark}{st['callout']}" + ("" if st['callout'].endswith((".", "!", "?")) else "."))
        elif "arrow" in st or "underline" in st: out.append(f"Look at `{st.get('arrow') or st.get('underline')}`.")
        elif "blur" in st: out.append(f"(`{st['blur']}` holds a secret: it is blurred in the video; never share it.)")
        elif "highlight" in st: out.append(f"Look at `{st['highlight']}`.")
        elif "wait" in st and not isinstance(st["wait"], (int, float)): out.append(f"Wait for `{st['wait']}`.")
    return out


def curl(seg, c):
    cmd = f"curl -s -X {c.get('method', 'GET')} {seg['base'].rstrip('/')}{c['path']}"
    for k, v in c.get("headers", {}).items():
        cmd += f" -H '{k}: {v}'"
    if "json" in c:
        cmd += " -H 'Content-Type: application/json' -d '" + json.dumps(c["json"], ensure_ascii=False) + "'"
    if c.get("show"):
        cmd += f" | jq '{c['show']}'"
    return cmd


def req_to_curl(seg, line):
    """An effect check written with `req` becomes curl, which every reader has."""
    if not line.startswith("req "):
        return line
    a = shlex.split(line)[1:]
    call, i = {"method": a[0].upper(), "path": a[1]}, 2
    while i < len(a):
        if a[i] in ("-d", "--data"):
            call["json"] = json.loads(a[i + 1]) if not a[i + 1].startswith("@") else a[i + 1]
        elif a[i] in ("-H", "--header"):
            k, _, v = a[i + 1].partition(":")
            call.setdefault("headers", {})[k.strip()] = v.strip()
        elif a[i] == "--show":
            call["show"] = a[i + 1]
        i += 2
    return curl(seg, call)


def section(seg):
    lines = []
    t = seg["type"]
    if seg.get("step"):
        lines.append(f"### {seg['step']}")
    if t == "section":
        lines.append(f"**{(seg.get('icon', '') + ' ').lstrip()}{seg['title']}**")
    if t == "concept":
        if seg.get("title"):
            lines.append(f"**{seg['title']}**")
        lines += [f"- {(x.get('icon', '') + ' ').lstrip()}**{x['title']}**: {x.get('sub', '')}" for x in seg["tiles"]]
    if t == "card":
        lines.append(f"**{seg['title']}**" + (f": {seg['subtitle']}" if seg.get("subtitle") else ""))
    if t in ("slide", "diagram"):
        lines.append(f"**{seg['title']}**")
        lines += [f"- **{b['title']}**: " + "; ".join(b.get("body", [])) for b in seg.get("boxes", [])]
        lines += [("  - " if b.startswith("  ") else "- ") + b.strip() for b in seg.get("bullets", [])]
        if seg.get("note"):
            lines.append(f"> {seg['note']}")
    lines += ([""] if lines else []) + [prose(seg["say"])]
    if t == "term":
        cmds = [c if isinstance(c, str) else c.get("cmd") for c in seg["cmds"]]
        lines += ["", "```bash", *[c for c in cmds if c], "```"]
    if t == "api":
        lines += ["", "```bash", *[curl(seg, c) for c in seg["calls"]],
                  *[req_to_curl(seg, t) for t in seg.get("then", [])], "```"]
    if t == "browser":
        lines += [""] + [f"{k}. {s}" for k, s in enumerate(browser_steps(seg), 1)]
    return lines


metas = {m["num"]: m for m in (json.loads(p.read_text()) for p in BUILD.glob("*/meta.json"))}
out, t0 = [f"# {title}", "", f"The written companion of `{name}.mp4`: the same chapters and steps, to follow at your own "
           "pace or copy from. Each chapter links its clip in `chapters/`.", ""], 0.0
for chap in number_steps(S.CHAPTERS):
    m = metas.get(chap["num"])
    start = f" ({clock(t0)})" if m else ""
    out += [f"## {chap['num']} {chap['title']}{start}", ""]
    if m:
        out += [f"Video: [`chapters/{m['file']}`](chapters/{m['file']})", ""]
    for i, seg in enumerate(chap["segments"]):
        out += section(seg)
        if m and i < len(m["timeline"]):
            tl = m["timeline"][i]
            png = shot(chap["num"], i, tl["end"] - tl["start"])
            if png:
                out += ["", f"![{seg.get('caption') or seg.get('title', '')}](doc/{png.name})"]
        out.append("")
    if m:
        t0 += m["duration"]
(ROOT / f"{name}.md").write_text("\n".join(out).rstrip() + "\n")
print(f"wrote {ROOT / (name + '.md')}")
