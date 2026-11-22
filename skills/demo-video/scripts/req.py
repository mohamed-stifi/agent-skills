"""req: one HTTP call shown the way a developer reads it (Python stdlib only). Used in `api` scenes.

    req METHOD PATH-or-URL [-d JSON | -d @file.json] [-H 'Name: value']... [--show JQ] [--lines N]

  → POST /api/notes                        the call, then its JSON body
    {"text": "Ship the audit report"}
  ← 201 Created · 14 ms                    green 2xx, yellow 3xx, red 4xx/5xx
  { "id": 1, … }                           the response, pretty; --show '.id' filters it with jq

A PATH is joined to $REQ_BASE (e.g. http://127.0.0.1:8000). Exit 0 whatever the status: the scene shows it.
"""

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

C = {"m": "\033[1;36m", "dim": "\033[2m", "ok": "\033[1;32m", "warn": "\033[1;33m", "bad": "\033[1;31m",
     "key": "\033[34m", "str": "\033[32m", "num": "\033[33m", "end": "\033[0m"}
if os.environ.get("NO_COLOR"):
    C = {k: "" for k in C}


def color_json(text: str) -> str:
    """Colour pretty JSON with jq when it is there, else plain."""
    if shutil.which("jq") and not os.environ.get("NO_COLOR"):
        r = subprocess.run(["jq", "-C", "."], input=text, capture_output=True, text=True)
        if r.returncode == 0:
            return r.stdout.rstrip()
    try:
        return json.dumps(json.loads(text), indent=2, ensure_ascii=False)
    except ValueError:
        return text


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    method, target = argv[0].upper(), argv[1]
    body, headers, show, lines = None, {}, None, 30
    i = 2
    while i < len(argv):
        a = argv[i]
        if a in ("-d", "--data"):
            body = argv[i + 1]
            if body.startswith("@"):
                body = open(body[1:]).read()
            i += 2
        elif a in ("-H", "--header"):
            k, _, v = argv[i + 1].partition(":")
            headers[k.strip()] = v.strip()
            i += 2
        elif a == "--show":
            show = argv[i + 1]; i += 2
        elif a == "--lines":
            lines = int(argv[i + 1]); i += 2
        else:
            sys.exit(f"req: unknown option {a}")
    base = os.environ.get("REQ_BASE", "").rstrip("/")
    url = target if "://" in target else f"{base}{target if target.startswith('/') else '/' + target}"
    shown = target if "://" not in target else url
    if body is not None:
        headers.setdefault("Content-Type", "application/json")

    print(f"{C['m']}→ {method}{C['end']} {shown}")
    if body is not None:
        try:
            print("  " + json.dumps(json.loads(body), ensure_ascii=False))
        except ValueError:
            print("  " + body)
    req = urllib.request.Request(url, data=body.encode() if body is not None else None, method=method,
                                 headers=headers)
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            status, reason, raw = r.status, r.reason, r.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        status, reason, raw = e.code, e.reason, e.read().decode(errors="replace")
    except (urllib.error.URLError, OSError) as e:
        print(f"{C['bad']}← no response{C['end']} {C['dim']}{getattr(e, 'reason', e)}{C['end']}")
        return 0
    ms = (time.monotonic() - t0) * 1000
    col = C["ok"] if status < 300 else C["warn"] if status < 400 else C["bad"]
    print(f"{col}← {status} {reason}{C['end']} {C['dim']}· {ms:.0f} ms{C['end']}")
    if not raw.strip():
        return 0
    if show and shutil.which("jq"):
        r = subprocess.run(["jq", "-C" if not os.environ.get("NO_COLOR") else "-M", show], input=raw,
                           capture_output=True, text=True)
        out = (r.stdout or r.stderr).rstrip()
    else:
        out = color_json(raw)
    rows = out.splitlines()
    print("\n".join(rows[:lines]))
    if len(rows) > lines:
        print(f"{C['dim']}  … {len(rows) - lines} more lines{C['end']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
