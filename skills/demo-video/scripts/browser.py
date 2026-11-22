"""Drive a real Chromium like a person and record it (Playwright). Used by engine.py for `browser` scenes.

    python browser.py record SCENE.json OUT.webm     # record; prints {"trim": seconds before the first page}
    python browser.py dry SCENE.json                 # run every step headless, print each one, no video

SCENE.json: {"url": "http://…", "steps": [...], "width": 1920, "height": 900}
A step is one action (a selector is any Playwright selector: CSS, `text=Save`, `role=button[name="Save"]`):
  {"goto": "http://…"}                 {"click": sel}                 {"hover": sel}
  {"type": "hello", "into": sel}       {"press": "Enter"}             {"scroll": sel} or {"scroll": 600}
  {"wait": sel} / {"wait": {"text": "Saved"}} / {"wait": 2}          {"pause": 1.5}
  {"highlight": sel, "seconds": 2}     {"expect": "text the page must show"}
Each step may add "pause": seconds to wait after it (default 0.6). A visible cursor glides to every target and
ripples on a click; typing is one key at a time, so the viewer can follow.
"""

import json
import sys
import time
from pathlib import Path

from playwright.sync_api import TimeoutError as PWTimeout
from playwright.sync_api import sync_playwright

CURSOR_JS = """
(() => {
  if (window.__dv) return; window.__dv = true;
  const add = () => {
    const c = document.createElement('div'); c.id = '__dv_cursor';
    c.innerHTML = '<svg width="28" height="28" viewBox="0 0 24 24"><path d="M4 2l16 9-7 2-3 7z" fill="#111" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/></svg>';
    Object.assign(c.style, {position:'fixed', left:(window.__dvX||960)+'px', top:(window.__dvY||450)+'px', zIndex:2147483647,
      pointerEvents:'none', transition:'left .5s ease, top .5s ease', filter:'drop-shadow(0 2px 3px #0006)'});
    document.documentElement.appendChild(c);
  };
  if (document.body) add(); else document.addEventListener('DOMContentLoaded', add);
  window.__dvMove = (x, y) => { window.__dvX = x; window.__dvY = y; const c = document.getElementById('__dv_cursor');
    if (c) { c.style.left = x + 'px'; c.style.top = y + 'px'; } };
  window.__dvRipple = (x, y) => { const r = document.createElement('div');
    Object.assign(r.style, {position:'fixed', left:(x-22)+'px', top:(y-22)+'px', width:'44px', height:'44px', borderRadius:'50%',
      border:'4px solid #f59f00', zIndex:2147483646, pointerEvents:'none', transition:'transform .45s, opacity .45s'});
    document.documentElement.appendChild(r);
    requestAnimationFrame(() => { r.style.transform = 'scale(1.8)'; r.style.opacity = '0'; });
    setTimeout(() => r.remove(), 600); };
  window.__dvBox = (x, y, w, h, ms) => { const b = document.createElement('div');
    Object.assign(b.style, {position:'fixed', left:(x-8)+'px', top:(y-8)+'px', width:(w+16)+'px', height:(h+16)+'px',
      border:'4px solid #f59f00', borderRadius:'10px', boxShadow:'0 0 0 9999px #0003', zIndex:2147483645, pointerEvents:'none'});
    document.documentElement.appendChild(b); setTimeout(() => b.remove(), ms); };
})();
"""


def target(page, sel):
    loc = page.locator(sel).first
    loc.wait_for(state="visible", timeout=15000)
    loc.scroll_into_view_if_needed(timeout=5000)
    b = loc.bounding_box()
    return loc, b["x"] + b["width"] / 2, b["y"] + b["height"] / 2, b


def glide(page, x, y, show):
    if show:
        page.evaluate("([x, y]) => window.__dvMove && window.__dvMove(x, y)", [x, y])
        page.wait_for_timeout(550)
    page.mouse.move(x, y)


def do(page, step, show):
    """Run one step. Returns a short description for the dry-run log."""
    if "goto" in step:
        page.goto(step["goto"], wait_until="networkidle")
        return f"goto {step['goto']}"
    if "click" in step:
        _, x, y, _ = target(page, step["click"])
        glide(page, x, y, show)
        if show:
            page.evaluate("([x, y]) => window.__dvRipple && window.__dvRipple(x, y)", [x, y])
        page.mouse.click(x, y)
        return f"click {step['click']}"
    if "hover" in step:
        _, x, y, _ = target(page, step["hover"])
        glide(page, x, y, show)
        return f"hover {step['hover']}"
    if "type" in step:
        if step.get("into"):
            loc, x, y, _ = target(page, step["into"])
            glide(page, x, y, show)
            loc.click()
            loc.fill("")
        page.keyboard.type(step["type"], delay=step.get("delay", 55 if show else 0))
        return f"type {step['type']!r}" + (f" into {step['into']}" if step.get("into") else "")
    if "press" in step:
        page.keyboard.press(step["press"])
        return f"press {step['press']}"
    if "scroll" in step:
        if isinstance(step["scroll"], (int, float)):
            page.mouse.wheel(0, step["scroll"])
        else:
            page.locator(step["scroll"]).first.scroll_into_view_if_needed(timeout=10000)
        return f"scroll {step['scroll']}"
    if "wait" in step:
        w = step["wait"]
        if isinstance(w, (int, float)):
            page.wait_for_timeout(int(w * 1000))
        elif isinstance(w, dict) and "text" in w:
            page.get_by_text(w["text"]).first.wait_for(state="visible", timeout=30000)
        else:
            page.locator(w).first.wait_for(state="visible", timeout=30000)
        return f"wait {w}"
    if "highlight" in step:
        _, x, y, b = target(page, step["highlight"])
        ms = int(step.get("seconds", 2) * 1000)
        if show:
            glide(page, x, y, show)
            page.evaluate("([x, y, w, h, ms]) => window.__dvBox(x, y, w, h, ms)",
                          [b["x"], b["y"], b["width"], b["height"], ms])
            page.wait_for_timeout(ms)
        return f"highlight {step['highlight']}"
    if "expect" in step:
        page.get_by_text(step["expect"]).first.wait_for(state="visible", timeout=15000)
        return f"expect {step['expect']!r}"
    if "pause" in step:
        page.wait_for_timeout(int(step["pause"] * 1000) if show else 0)
        return f"pause {step['pause']}"
    raise ValueError(f"unknown step: {step}")


def run(scene, out=None):
    w, h = scene.get("width", 1920), scene.get("height", 900)
    show = out is not None
    with sync_playwright() as p:
        browser = p.chromium.launch()
        kw = {"viewport": {"width": w, "height": h}, "device_scale_factor": 1}
        if show:
            kw.update(record_video_dir=str(Path(out).parent / "pw-video"), record_video_size={"width": w, "height": h})
        ctx = browser.new_context(**kw)
        ctx.add_init_script(CURSOR_JS)
        page = ctx.new_page()
        t0 = time.monotonic()
        page.goto(scene["url"], wait_until="networkidle")
        trim = time.monotonic() - t0 if show else 0
        if show:
            page.wait_for_timeout(800)
        ok = True
        for i, step in enumerate(scene.get("steps", []), 1):
            try:
                what = do(page, step, show)
                if show and set(step) != {"pause"}:          # a pure pause step already waited
                    page.wait_for_timeout(int(step.get("pause", 0.6) * 1000))
                if not show:
                    print(f"  ok   {i:2d}. {what}")
            except (PWTimeout, ValueError, Exception) as e:   # report the failing step, not a stack trace
                msg = str(e).splitlines()[0][:200]
                print(f"  FAIL {i:2d}. {json.dumps(step)}  at {page.url}\n         {msg}")
                ok = False
                break
        if show:
            page.wait_for_timeout(1200)
        video = page.video
        ctx.close()
        browser.close()
        if show:
            Path(video.path()).replace(out)
            print(json.dumps({"trim": round(trim, 2), "ok": ok}))
        return ok


if __name__ == "__main__":
    mode, scene_path = sys.argv[1], sys.argv[2]
    scene = json.loads(Path(scene_path).read_text())
    if mode == "dry":
        sys.exit(0 if run(scene) else 1)
    sys.exit(0 if run(scene, sys.argv[3]) else 1)
