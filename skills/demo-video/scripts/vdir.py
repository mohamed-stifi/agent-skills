"""The video folder of a filmed repo, `<repo>/.video_demo_dir/`: everything demo-video makes and keeps there, and
the INDEX.md a later run reads first. Python stdlib only.

    python3 vdir.py init REPO [--import OLD_VIDEO_DIR [--slug SLUG]]   # create it (git-ignored), or bring in an old folder
    python3 vdir.py video REPO SLUG        # a new version folder videos/SLUG/vN/ with src/ ready; prints its path
    python3 vdir.py register VERSION_DIR   # record a built version in state.json (engine.py does this itself)
    python3 vdir.py note REPO "text"       # a finding or next step, shown in INDEX.md
    python3 vdir.py leftover REPO "text"   # something left outside on purpose (an account, a Slack app)
    python3 vdir.py index REPO             # rebuild INDEX.md from state.json

Layout: INDEX.md, state.json, features/ (the feature map, one file per feature), videos/<slug>/vN/ (src/ with
script.py and the engine copy, chapters/, the MP4, .srt, doc), work/ (the clones), secrets/ (mode 700: tokens,
saved sign-ins), logs/, run/ (locks, pid files). A `.gitignore` holding `*` keeps all of it out of git without
changing the repo's own files.
"""

from __future__ import annotations

import json
import os
import re
import runpy
import shutil
import subprocess
import sys
import time
from pathlib import Path

NAME = ".video_demo_dir"
LAYOUT = ("videos", "features", "work", "secrets", "logs", "run")
SRC_FILES = ("engine.py", "browser.py", "make_readme.py", "make_doc.py", "run.sh", "vdir.py")
HERE = Path(__file__).resolve().parent


def find(start) -> Path | None:
    """The .video_demo_dir that holds `start` (or that `start`'s repo holds)."""
    p = Path(start).resolve()
    for q in (p, *p.parents):
        if q.name == NAME:
            return q
        if (q / NAME).is_dir():
            return q / NAME
    return None


def load(d: Path) -> dict:
    f = d / "state.json"
    s = json.loads(f.read_text()) if f.exists() else {}
    for k, v in (("version", 1), ("repo", str(d.parent)), ("videos", {}), ("notes", []), ("leftovers", []),
                 ("running", [])):
        s.setdefault(k, v)
    return s


def save(d: Path, s: dict):
    tmp = d / "state.json.tmp"
    tmp.write_text(json.dumps(s, indent=1, ensure_ascii=False))
    tmp.replace(d / "state.json")


def dockerignore_warning(repo: Path) -> str | None:
    files = sorted({*repo.glob("Dockerfile*"), *repo.glob("*/Dockerfile*")})
    if not files:
        return None
    di = repo / ".dockerignore"
    lines = [x.strip() for x in di.read_text().splitlines()] if di.exists() else []
    if any(x == "*" or x.strip("/").removeprefix("**/").rstrip("*").rstrip("/") == NAME for x in lines):
        return None
    return (f"{files[0].relative_to(repo)} exists, and .dockerignore does not exclude {NAME}: a `docker build` of "
            f"the repo folder would also send the clones, videos and sign-ins. Ask the user to add this line to "
            f".dockerignore:\n    {NAME}/")


def init(repo, old=None, slug=None) -> Path:
    repo = Path(repo).resolve()
    d = repo / NAME
    for sub in LAYOUT:
        (d / sub).mkdir(parents=True, exist_ok=True)
    if not (d / ".gitignore").exists():
        (d / ".gitignore").write_text("*\n")                 # git ignores the whole folder; the repo is untouched
    os.chmod(d / "secrets", 0o700)
    save(d, load(d))
    if w := dockerignore_warning(repo):
        print("WARNING " + w)
    if old:
        bring_in(d, Path(old).resolve(), slug)
    index(d)
    print(f"{d}  (read {d / 'INDEX.md'} first)")
    return d


def versions(d: Path, slug: str) -> list[Path]:
    vd = d / "videos" / slug
    return sorted((p for p in vd.glob("v*") if re.fullmatch(r"v\d+", p.name)), key=lambda p: int(p.name[1:]))


def new_version(repo, slug) -> Path:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug):
        sys.exit(f"slug must be lowercase letters, digits and dashes: {slug!r}")
    d = find(repo) or init(repo)
    old = versions(d, slug)
    dest = d / "videos" / slug / f"v{int(old[-1].name[1:]) + 1 if old else 1}"
    (dest / "src").mkdir(parents=True)
    for f in SRC_FILES:
        shutil.copy2(HERE / f, dest / "src" / f)
    prev = old[-1] / "src" / "script.py" if old else None
    shutil.copy2(prev if prev and prev.exists() else HERE / "script_template.py", dest / "src" / "script.py")
    print(dest)
    return dest


def git(path, *args) -> str:
    r = subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def probe_chapters(mp4: Path) -> list[dict]:
    if not shutil.which("ffprobe") or not mp4.exists():
        return []
    r = subprocess.run(["ffprobe", "-v", "error", "-show_chapters", "-of", "json", str(mp4)], capture_output=True, text=True)
    out = []
    for c in json.loads(r.stdout or "{}").get("chapters", []):
        num, _, title = c.get("tags", {}).get("title", "").partition(" ")
        out.append({"num": num, "title": title, "duration": float(c["end_time"]) - float(c["start_time"])})
    return out


def register(version_dir) -> dict:
    v = Path(version_dir).resolve()
    d = find(v)
    if not d:
        sys.exit(f"{v} is not inside a {NAME}")
    src = v / "src"
    conf = runpy.run_path(str(src / "script.py")) if (src / "script.py").exists() else {}
    name = conf.get("OUTPUT_NAME", "walkthrough")
    metas = sorted((json.loads(p.read_text()) for p in (v / "build").glob("*/meta.json")), key=lambda m: m["num"])
    chapters = ([{"num": m["num"], "title": m["title"], "duration": m["duration"], "file": f"chapters/{m['file']}"}
                 for m in metas] or probe_chapters(v / f"{name}.mp4"))
    shows = {}
    for key, path in conf.get("WORKDIRS", {}).items():
        p = Path(os.path.expanduser(str(path)))
        head = git(p, "rev-parse", "--short", "HEAD") if p.exists() else ""
        shows[key] = {"path": str(p), "commit": head or "unknown",
                      "dirty": bool(head and git(p, "status", "--porcelain", "--untracked-files=no")),
                      "branch": git(p, "rev-parse", "--abbrev-ref", "HEAD") if head else ""}
    files = {k: str((v / f).relative_to(d)) for k, f in
             (("video", f"{name}.mp4"), ("subtitles", f"{name}.srt"), ("doc", f"{name}.md"), ("readme", "README.md"))
             if (v / f).exists()}
    entry = {"title": conf.get("TITLE", name), "type": conf.get("VIDEO_TYPE", ""), "recorded": time.strftime("%Y-%m-%d %H:%M"),
             "length": round(sum(c["duration"] for c in chapters), 1), "chapters": chapters, "shows": shows,
             "files": files, "path": str(v.relative_to(d))}
    s = load(d)
    s["videos"].setdefault(v.parent.name, {})[v.name] = entry
    save(d, s)
    index(d)
    return entry


def bring_in(d: Path, old: Path, slug=None):
    """An older demo-video folder (before .video_demo_dir) becomes videos/<slug>/v1 (its clones are not copied)."""
    conf = runpy.run_path(str(old / "src" / "script.py")) if (old / "src" / "script.py").exists() else {}
    slug = slug or re.sub(r"[^a-z0-9]+", "-", conf.get("OUTPUT_NAME", old.name).lower()).strip("-")
    dest = d / "videos" / slug / f"v{len(versions(d, slug)) + 1}"
    shutil.copytree(old, dest, symlinks=True, ignore=shutil.ignore_patterns("work", "__pycache__"))
    register(dest)
    note(d, f"Brought in {old} as {dest.relative_to(d)} (clones not copied).")


def note(d: Path, text: str, key="notes"):
    s = load(d)
    s[key].append({"at": time.strftime("%Y-%m-%d %H:%M"), "text": text})
    save(d, s)
    index(d)


def clock(t: float) -> str:
    t = int(t)
    return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}" if t >= 3600 else f"{t // 60}:{t % 60:02d}"


def index(d: Path):
    s = load(d)
    repo = Path(s["repo"]).name
    out = [f"# Video folder of {repo}", "",
           "Read this first. It lists what demo-video already made in this repo, what is still running, and what "
           "was left outside on purpose. It is generated from `state.json` (`vdir.py index`); don't edit it by hand.",
           "", "## Videos", ""]
    drafts = sorted((v.parent.name, v.name) for v in (d / "videos").glob("*/v*")
                    if re.fullmatch(r"v\d+", v.name) and v.name not in s["videos"].get(v.parent.name, {}))
    if not s["videos"] and not drafts:
        out.append("None yet.")
    else:
        out += ["| Video | Version | Type | Recorded | Shows | Length | Chapters | Files |", "|---|---|---|---|---|---|---|---|"]
        for slug, vs in sorted(s["videos"].items()):
            last = max(vs, key=lambda x: int(x[1:]))
            for ver in sorted(vs, key=lambda x: int(x[1:])):
                e = vs[ver]
                shows = ", ".join(f"{k}@{x['commit']}{'+changes' if x['dirty'] else ''}" for k, x in e["shows"].items())
                files = " ".join(f"[{k}]({p})" for k, p in e["files"].items()) or f"`{e['path']}`"
                out.append(f"| **{slug}**: {e['title']} | {ver}{' (latest)' if ver == last else ''} | {e['type'] or '-'} | "
                           f"{e['recorded']} | {shows or '-'} | {clock(e['length'])} | {len(e['chapters'])} | {files} |")
        out += [f"| **{slug}** | {ver} (draft, not recorded yet) | | | | | | `videos/{slug}/{ver}/src/script.py` |"
                for slug, ver in drafts]
        for slug, vs in sorted(s["videos"].items()):
            ver = max(vs, key=lambda x: int(x[1:]))
            e, t = vs[ver], 0.0
            out += ["", f"### {slug} {ver}: chapters", ""]
            for c in e["chapters"]:
                out.append(f"- {clock(t)} **{c['num']}** {c['title']}" + (f" ([clip]({e['path']}/{c['file']}))" if c.get("file") else ""))
                t += c["duration"]
    feats = sorted((d / "features").glob("*.md"))
    out += ["", "## Features mapped", ""]
    out += [f"- [{f.stem}](features/{f.name}): {next((x.lstrip('# ').strip() for x in f.read_text().splitlines() if x.strip()), '')}"
            for f in feats] or ["None yet (step 2 of the skill writes one file per feature)."]
    out += ["", "## Running now", ""]
    out += [f"- {r['kind']} `{r['name']}`: stop with `{r.get('stop', '?')}`" for r in s["running"]] or \
           ["Nothing recorded as running."]
    out += ["", "## Left outside on purpose", ""]
    out += [f"- {x['at']}: {x['text']}" for x in s["leftovers"]] or ["Nothing."]
    secrets = sorted(p.name for p in (d / "secrets").glob("*") if p.is_file())
    out += ["", "## Saved sign-ins and secrets", ""]
    out += [f"- `secrets/{n}` (delete it with `rm {NAME}/secrets/{n}`)" for n in secrets] or ["None."]
    out += ["", "## Notes", ""]
    out += [f"- {x['at']}: {x['text']}" for x in s["notes"]] or ["None."]
    out += ["", "## How to continue", "",
            "- A new video, or a new version of one: `python3 <skill>/scripts/vdir.py video <repo> <slug>`; the new "
            "version starts from the last one's script.",
            "- Clones live in `work/`: `git -C work/<name> fetch && git -C work/<name> checkout <commit>` refreshes one.",
            ""]
    tmp = d / "INDEX.md.tmp"
    tmp.write_text("\n".join(out))
    tmp.replace(d / "INDEX.md")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    cmd = a[0]
    if cmd == "init":
        old = a[a.index("--import") + 1] if "--import" in a else None
        init(a[1], old, a[a.index("--slug") + 1] if "--slug" in a else None)
    elif cmd == "video":
        new_version(a[1], a[2])
    elif cmd == "register":
        print(json.dumps(register(a[1]), indent=1)[:2000])
    elif cmd in ("note", "leftover"):
        d = find(a[1]) or sys.exit(f"no {NAME} at {a[1]}: run init first")
        note(d, a[2], "notes" if cmd == "note" else "leftovers")
    elif cmd == "index":
        index(find(a[1]) or sys.exit(f"no {NAME} at {a[1]}"))
    else:
        sys.exit(__doc__)
