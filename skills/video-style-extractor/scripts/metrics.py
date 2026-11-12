# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Objective numbers about the reference set (markdown to stdout). Run from the work dir."""
import glob, json, os, re, subprocess, statistics as st

def cuts(path):
    out = subprocess.run(["ffmpeg", "-i", path, "-vf", "select='gt(scene,0.3)',showinfo", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    return out.count("pts_time")

def bg(path):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", "20", "-i", path, "-frames:v", "1", "-vf", "scale=1:1",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return "#%02X%02X%02X" % tuple(raw[:3]) if len(raw) >= 3 else "?"

rows = []
for f in sorted(glob.glob("subs/*.json")):
    d = json.load(open(f)); vid = d["id"]
    W = [w for s in d["segments"] for w in s["words"]]
    info = json.load(open(f"videos/{vid}.info.json")) if os.path.exists(f"videos/{vid}.info.json") else {}
    mp4 = f"videos/{vid}.mp4"
    if not W: continue
    speech = W[-1][2] - W[0][1]
    first = " ".join(s["text"] for s in d["segments"])[:160]
    last = d["segments"][-1]["text"]
    rows.append(dict(id=vid, title=info.get("title", ""), views=info.get("view_count", 0), dur=d["duration"],
                     words=len(W), wpm=len(W) / speech * 60, cuts=cuts(mp4), avgcolor=bg(mp4),
                     wh=f'{info.get("width")}x{info.get("height")}', first=first, last=last))

print("# Reference metrics\n")
print("| id | title | views | sec | words | wpm | hard cuts | avg color | size |")
print("|---|---|---|---|---|---|---|---|---|")
for r in rows:
    print(f"| {r['id']} | {r['title'][:50]} | {r['views']:,} | {r['dur']:.0f} | {r['words']} | {r['wpm']:.0f} | {r['cuts']} | {r['avgcolor']} | {r['wh']} |")
if rows:
    print(f"\n**Median:** {st.median(r['dur'] for r in rows):.0f} s, {st.median(r['words'] for r in rows):.0f} words, "
          f"{st.median(r['wpm'] for r in rows):.0f} wpm, {st.median(r['cuts'] for r in rows):.0f} hard cuts per video.\n")
    print("## First ~160 chars (hooks)\n")
    for r in rows: print(f"- **{r['id']}**: {r['first']}")
    print("\n## Last line (CTA)\n")
    for r in rows: print(f"- **{r['id']}**: {r['last']}")
