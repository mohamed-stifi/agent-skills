"""What a recording started, and putting it all away afterwards (demo-video). Python stdlib + the docker CLI.

    python3 ledger.py snapshot REPO                 # before starting anything: the state things are found in
    python3 ledger.py status REPO                   # what the video owns that runs now (shown in INDEX.md)
    python3 ledger.py cleanup REPO [--dry] [--limit-gb 2]
    python3 ledger.py restore REPO PROJECT          # a checkpoint's volumes back, before the project starts again

Owned (cleanup checkpoints its data, then removes it): Docker Compose projects named `dv-*` or whose compose
folder is inside .video_demo_dir, with their containers, networks and volumes; processes started after the
snapshot whose working folder is inside .video_demo_dir.
Found (put back as it was): containers of Compose projects in a video's WORKDIRS outside .video_demo_dir: one
that was stopped is stopped again, one that was not there is removed; volumes are always kept.
Unknown (never touched, only reported): anything else that appeared after the snapshot.
"""

from __future__ import annotations

import gzip
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vdir  # noqa: E402

P, WD = "com.docker.compose.project", "com.docker.compose.project.working_dir"


def sh(*cmd, check=True, **kw) -> str:
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if check and r.returncode:
        raise RuntimeError(f"{' '.join(cmd)}: {r.stderr.strip()[:400]}")
    return r.stdout


def docker_ok() -> bool:
    return bool(shutil.which("docker")) and subprocess.run(["docker", "info"], capture_output=True).returncode == 0


def inspect(kind: str) -> list[dict]:
    ids = sh("docker", *({"container": ["ps", "-aq"], "volume": ["volume", "ls", "-q"],
                          "network": ["network", "ls", "-q"]}[kind])).split()
    return json.loads(sh("docker", kind, "inspect", *ids)) if ids else []


def under(path: str, root: Path) -> bool:
    try:
        return bool(path) and Path(path).resolve().is_relative_to(root.resolve())
    except OSError:
        return False


def created(x: dict) -> float:
    s = x.get("Created") or x.get("CreatedAt") or ""
    s = re.sub(r"(\.\d{6})\d*", r"\1", s).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s).timestamp()
    except ValueError:
        return 0.0


def labels(x: dict) -> dict:
    return (x.get("Config") or {}).get("Labels") or x.get("Labels") or {}


def owned(lab: dict, d: Path) -> bool:
    return lab.get(P, "").startswith("dv-") or under(lab.get(WD, ""), d)


def found_scope(lab: dict, s: dict, d: Path) -> bool:
    return not owned(lab, d) and any(under(lab.get(WD, ""), Path(w)) for w in s.get("workdirs", []) if not under(w, d))


def processes(d: Path, since: float) -> list[dict]:
    """Processes whose working folder is inside the video folder, started after `since` (never our own chain)."""
    mine, p = set(), os.getpid()
    while p > 1:
        mine.add(p)
        try:
            p = int(sh("ps", "-o", "ppid=", "-p", str(p)).strip() or 1)
        except (RuntimeError, ValueError):
            break
    out = []
    if sys.platform == "darwin":
        rows, pid = sh("lsof", "-a", "-d", "cwd", "-u", str(os.getuid()), "-Fpn", check=False), None
        pairs = []
        for line in rows.splitlines():
            if line.startswith("p"):
                pid = int(line[1:])
            elif line.startswith("n") and pid:
                pairs.append((pid, line[1:]))
    else:
        pairs = []
        for e in Path("/proc").glob("[0-9]*"):
            try:
                pairs.append((int(e.name), os.readlink(e / "cwd")))
            except OSError:
                pass
    for pid, cwd in pairs:
        if pid in mine or not under(cwd, d):
            continue
        info = sh("ps", "-o", "lstart=,command=", "-p", str(pid), check=False).strip()
        if not info:
            continue
        start = time.mktime(time.strptime(" ".join(info.split()[:5]), "%a %b %d %H:%M:%S %Y"))
        if start >= since - 1:
            out.append({"pid": pid, "cwd": cwd, "command": " ".join(info.split()[5:])[:200]})
    return out


def snapshot(repo):
    d = vdir.find(repo) or vdir.init(repo)
    s = vdir.load(d)
    cons = inspect("container") if docker_ok() else []
    s["snapshot"] = {"at": time.time(), "containers": {c["Name"].lstrip("/"): {
        "running": c["State"]["Running"], "project": labels(c).get(P, "")} for c in cons}}
    vdir.save(d, s)
    print(f"snapshot: {len(cons)} containers recorded as found")


def status(repo, quiet=False) -> list[dict]:
    d = vdir.find(repo) or sys.exit("no .video_demo_dir: run vdir.py init first")
    s = vdir.load(d)
    run = []
    if docker_ok():
        for c in inspect("container"):
            if c["State"]["Running"] and owned(labels(c), d):
                run.append({"kind": "container", "name": c["Name"].lstrip("/"),
                            "stop": f"python3 ledger.py cleanup {s['repo']}"})
    for p in processes(d, s.get("snapshot", {}).get("at", 0)):
        run.append({"kind": "process", "name": f"{p['pid']} {p['command'][:60]}", "stop": f"kill {p['pid']}"})
    s["running"] = run
    vdir.save(d, s)
    vdir.index(d)
    if not quiet:
        print(*(f"{r['kind']} {r['name']}" for r in run), sep="\n") if run else print("nothing owned is running")
    return run


def size_of(volumes: list[str]) -> int:
    rows = json.loads(sh("docker", "system", "df", "-v", "--format", "{{json .}}", check=False) or "{}")
    sizes = {v.get("Name"): v.get("Size", "0B") for v in rows.get("Volumes") or []}
    total = 0
    for v in volumes:
        m = re.fullmatch(r"([\d.]+)\s*([kKMGT]?B)", sizes.get(v, "0B").strip())
        if m:
            total += int(float(m.group(1)) * {"B": 1, "kB": 1e3, "KB": 1e3, "MB": 1e6, "GB": 1e9, "TB": 1e12}[m.group(2)])
    return total


def checkpoint(d: Path, project: str, cons: list[dict], vols: list[dict], limit: float, dry: bool) -> str:
    names = [v["Name"] for v in vols]
    if not names:
        return f"{project}: no volumes"
    size = size_of(names)
    if size > limit * 1e9:
        return f"{project}: checkpoint skipped, {size / 1e9:.2f} GB is over the {limit:g} GB limit"
    if dry:
        return f"{project}: would save {len(names)} volume(s), {size / 1e6:.1f} MB"
    out = d / "state" / project
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    ids = [c["Id"] for c in cons]
    if ids:
        sh("docker", "stop", "-t", "20", *ids, check=False)       # stopped: the files are consistent
    saved = []
    for v in vols:
        user = next(((c, m) for c in cons for m in c.get("Mounts", []) if m.get("Name") == v["Name"]), None)
        if not user:
            continue
        c, m = user
        with gzip.open(out / f"{v['Name']}.tar.gz", "wb") as f:
            f.write(subprocess.run(["docker", "cp", f"{c['Id']}:{m['Destination']}", "-"], capture_output=True,
                                   check=True).stdout)
        saved.append({"name": v["Name"], "labels": v.get("Labels") or {}, "dest": m["Destination"],
                      "image": c["Config"]["Image"], "file": f"{v['Name']}.tar.gz"})
    (out / "meta.json").write_text(json.dumps({"project": project, "saved": time.strftime("%Y-%m-%d %H:%M"),
                                               "size": size, "volumes": saved}, indent=1))
    return f"{project}: checkpoint saved ({len(saved)} volume(s), {size / 1e6:.1f} MB) in state/{project}/"


def restore(repo, project):
    d = vdir.find(repo) or sys.exit("no .video_demo_dir")
    meta = json.loads((d / "state" / project / "meta.json").read_text())
    for v in meta["volumes"]:
        if subprocess.run(["docker", "volume", "inspect", v["name"]], capture_output=True).returncode == 0:
            print(f"{v['name']}: exists already, left as it is")
            continue
        sh("docker", "volume", "create", *[x for k, val in v["labels"].items() for x in ("--label", f"{k}={val}")],
           v["name"])
        tmp = f"dv-restore-{os.getpid()}"
        sh("docker", "create", "--name", tmp, "-v", f"{v['name']}:{v['dest']}", "--entrypoint", "true", v["image"])
        try:
            data = gzip.decompress((d / "state" / project / v["file"]).read_bytes())
            subprocess.run(["docker", "cp", "-", f"{tmp}:{posixpath.dirname(v['dest'].rstrip('/')) or '/'}"],
                           input=data, capture_output=True, check=True)
        finally:
            sh("docker", "rm", "-f", tmp, check=False)
        print(f"{v['name']}: restored from the checkpoint of {meta['saved']}")


def cleanup(repo, dry=False, limit=2.0) -> dict:
    d = vdir.find(repo) or sys.exit("no .video_demo_dir: run vdir.py init first")
    s = vdir.load(d)
    snap = s.get("snapshot") or {"at": 0, "containers": {}}
    rep = {"checkpoints": [], "removed": [], "restored": [], "unknown": [], "processes": []}
    if docker_ok():
        cons, vols, nets = inspect("container"), inspect("volume"), inspect("network")
        projects = sorted({labels(x).get(P) for x in cons + vols + nets if owned(labels(x), d) and labels(x).get(P)})
        for pr in projects:
            pc = [c for c in cons if labels(c).get(P) == pr]
            pv = [v for v in vols if labels(v).get(P) == pr]
            rep["checkpoints"].append(checkpoint(d, pr, pc, pv, limit, dry))
            for kind, items, rm in (("container", pc, ["rm", "-f"]), ("network", [n for n in nets if labels(n).get(P) == pr],
                                    ["network", "rm"]), ("volume", pv, ["volume", "rm", "-f"])):
                for x in items:
                    name = (x.get("Name") or "").lstrip("/")
                    rep["removed"].append(f"{kind} {name}")
                    if not dry:
                        sh("docker", *rm, x.get("Id") or name, check=False)
        for c in cons:
            name, lab = c["Name"].lstrip("/"), labels(c)
            if owned(lab, d):
                continue
            was = snap["containers"].get(name)
            if found_scope(lab, s, d):
                if was is None:
                    rep["restored"].append(f"removed {name} (not there before)")
                    dry or sh("docker", "rm", "-f", c["Id"], check=False)
                elif was["running"] != c["State"]["Running"]:
                    rep["restored"].append(f"{'started' if was['running'] else 'stopped'} {name} (as found)")
                    dry or sh("docker", "start" if was["running"] else "stop", c["Id"], check=False)
            elif was is None and created(c) > snap["at"] > 0:
                rep["unknown"].append(f"container {name} (not the video's: left alone)")
    for p in processes(d, snap["at"]):
        rep["processes"].append(f"{p['pid']} {p['command'][:80]}")
        if not dry:
            try:
                os.kill(p["pid"], 15)
            except ProcessLookupError:
                pass
    if not dry:
        time.sleep(1)
        for p in processes(d, snap["at"]):
            try:
                os.kill(p["pid"], 9)
            except ProcessLookupError:
                pass
        s = vdir.load(d)
        s["running"], s["last_cleanup"] = [], {"at": time.strftime("%Y-%m-%d %H:%M"), **rep}
        s.pop("snapshot", None)                               # the next run takes a fresh one
        vdir.save(d, s)
        vdir.index(d)
    for k, v in rep.items():
        print(f"{k}:", *(v or ["none"]), sep="\n  ")
    return rep


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2:
        sys.exit(__doc__)
    if a[0] == "snapshot":
        snapshot(a[1])
    elif a[0] == "status":
        status(a[1])
    elif a[0] == "cleanup":
        cleanup(a[1], "--dry" in a, float(a[a.index("--limit-gb") + 1]) if "--limit-gb" in a else 2.0)
    elif a[0] == "restore":
        restore(a[1], a[2])
    else:
        sys.exit(__doc__)
