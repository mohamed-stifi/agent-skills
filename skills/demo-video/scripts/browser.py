"""Drive a real Chromium like a person and record it (Playwright). Used by engine.py for `browser` scenes.

    python browser.py record SCENE.json OUT.webm     # record; prints {"trim": seconds before the first page}
    python browser.py dry SCENE.json                 # run every step headless, print each one, no video
    python browser.py login URL STATE.json --until REGEX [--minutes 15]
        # opens a visible browser at URL for the person to sign in; when the page URL matches REGEX, saves the
        # session (cookies, storage) to STATE.json (mode 600) and closes. Scenes load it with "storage_state".

SCENE.json: {"url": "http://…", "steps": [...], "width": 1920, "height": 900,
             "storage_state": "STATE.json", "wait_until": "load"}
  storage_state: a saved sign-in (see login).  wait_until: when the first page counts as open: "networkidle"
  (default), "load" or "domcontentloaded"; pages that keep a connection open (chat apps) never reach
  networkidle, so use "load".
A step is one action (a selector is any Playwright selector: CSS, `text=Save`, `role=button[name="Save"]`):
  {"goto": "http://…"}                 {"click": sel}                 {"hover": sel}
  {"type": "hello", "into": sel}       {"press": "Enter"}             {"scroll": sel} or {"scroll": 600}
  {"wait": sel} / {"wait": {"text": "Saved"}} / {"wait": 2}  (+ "timeout": seconds, default 30)   {"pause": 1.5}
  {"goto": "http://…", "wait_until": "load"}
  {"highlight": sel, "seconds": 2}     {"expect": "text the page must show"}   (shows ✓ and the text)
Pointing (drawn only when recording; the dry run checks their targets):
  {"zoom": sel, "scale": 2} / {"zoom": false}      the page scales up around sel (sharp: done by the browser)
  {"callout": "2-5 words", "at": sel, "icon": "⚡", "tone": "info|warn|ok", "seconds": 3}   (no "at": top)
  {"arrow": sel, "from": "left|right|top|bottom", "seconds": 2}     {"underline": sel, "seconds": 2}
  {"blur": sel}                                      blur a secret for the rest of the scene (also in dry runs)
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
  const layer = (el, ms) => { el.style.pointerEvents = 'none'; el.style.zIndex = 2147483645;
    document.documentElement.appendChild(el); if (ms) setTimeout(() => { el.style.opacity = '0';
      setTimeout(() => el.remove(), 300); }, ms); return el; };
  // highlight frame: glowing cyan rim with corner brackets, the rest dimmed a little
  window.__dvBox = (x, y, w, h, ms) => { const b = document.createElement('div'), p = 10;
    Object.assign(b.style, {position:'fixed', left:(x-p)+'px', top:(y-p)+'px', width:(w+2*p)+'px', height:(h+2*p)+'px',
      border:'2px solid #bbffff', borderRadius:'8px', boxShadow:'0 0 18px 4px #71bcd9, 0 0 0 9999px #0000002e',
      transition:'opacity .3s'});
    for (const [v, hz] of [['top','left'],['top','right'],['bottom','left'],['bottom','right']]) {
      const c = document.createElement('div');
      Object.assign(c.style, {position:'absolute', width:'22px', height:'22px', [v]:'-8px', [hz]:'-8px',
        ['border' + v[0].toUpperCase() + v.slice(1)]:'5px solid #bbffff', ['border' + hz[0].toUpperCase() + hz.slice(1)]:'5px solid #bbffff'});
      b.appendChild(c); }
    layer(b, ms); };
  // callout pill: icon + a few bold words, rim coloured by tone, popped above (or below) the target
  window.__dvCallout = (text, icon, tone, box, ms) => { const rim = {info:'#71bcd9', warn:'#f59f00', ok:'#40c057'}[tone] || '#71bcd9';
    const b = document.createElement('div'); b.textContent = (icon ? icon + '  ' : '') + text;
    Object.assign(b.style, {position:'fixed', padding:'14px 26px', borderRadius:'999px', background:'#161b2e', color:'#fff',
      font:'700 30px -apple-system, system-ui, sans-serif', letterSpacing:'.3px', whiteSpace:'nowrap',
      border:'2px solid ' + rim, boxShadow:'0 0 22px 2px ' + rim + ', 0 8px 24px #0008', opacity:'0',
      transform:'scale(.85)', transition:'opacity .25s, transform .25s'});
    layer(b, ms); const r = b.getBoundingClientRect(), W = innerWidth;
    let x = box ? box.x + box.width / 2 - r.width / 2 : W / 2 - r.width / 2;
    let y = box ? (box.y - r.height - 26 > 10 ? box.y - r.height - 26 : box.y + box.height + 26) : 36;
    b.style.left = Math.max(16, Math.min(W - r.width - 16, x)) + 'px'; b.style.top = y + 'px';
    requestAnimationFrame(() => { b.style.opacity = '1'; b.style.transform = 'scale(1)'; }); };
  // arrow: a lavender arrow pointing at the target from one side
  window.__dvArrow = (box, from, ms) => { const L = 150, cx = box.x + box.width / 2, cy = box.y + box.height / 2;
    const end = {left:[box.x - 10, cy], right:[box.x + box.width + 10, cy], top:[cx, box.y - 10], bottom:[cx, box.y + box.height + 10]}[from];
    const d = {left:[-1,0], right:[1,0], top:[0,-1], bottom:[0,1]}[from], st = [end[0] + d[0]*L, end[1] + d[1]*L];
    const ns = 'http://www.w3.org/2000/svg', svg = document.createElementNS(ns, 'svg');
    Object.assign(svg.style, {position:'fixed', left:'0', top:'0', width:'100vw', height:'100vh', overflow:'visible', transition:'opacity .3s'});
    const a = Math.atan2(end[1] - st[1], end[0] - st[0]), k = 22, s1 = a - 0.5, s2 = a + 0.5;
    svg.innerHTML = `<g stroke="#c9a9f4" stroke-width="7" stroke-linecap="round" fill="none" style="filter:drop-shadow(0 2px 4px #0007)">
      <line x1="${st[0]}" y1="${st[1]}" x2="${end[0]}" y2="${end[1]}"/>
      <polyline points="${end[0]-k*Math.cos(s1)},${end[1]-k*Math.sin(s1)} ${end[0]},${end[1]} ${end[0]-k*Math.cos(s2)},${end[1]-k*Math.sin(s2)}"/></g>`;
    layer(svg, ms); };
  // underline: a lavender bar drawn left to right under the target
  window.__dvUnderline = (box, ms) => { const u = document.createElement('div');
    Object.assign(u.style, {position:'fixed', left:box.x + 'px', top:(box.y + box.height + 6) + 'px', width:'0px', height:'6px',
      borderRadius:'3px', background:'#c9a9f4', boxShadow:'0 0 10px #c9a9f4', transition:'width .5s ease, opacity .3s'});
    layer(u, ms); requestAnimationFrame(() => { u.style.width = box.width + 'px'; }); };
  // zoom: scale the page (not the overlays) so the target sits near the centre, clamped to the page edges
  window.__dvZoom = (box, s, animate) => { const b = document.body;
    b.style.transition = animate ? 'transform .8s cubic-bezier(.4,0,.2,1)' : 'none';
    if (!box) { b.style.transform = 'none'; return; }
    b.style.transform = 'none'; const r = b.getBoundingClientRect(), W = innerWidth, H = innerHeight;
    const bw = Math.max(r.width, W), bh = Math.max(r.height, H);
    let tx = W / 2 - r.left - s * (box.x + box.width / 2 - r.left), ty = H / 2 - r.top - s * (box.y + box.height / 2 - r.top);
    tx = Math.min(-r.left, Math.max(W - r.left - s * bw, tx)); ty = Math.min(-r.top, Math.max(H - r.top - s * bh, ty));
    b.style.transformOrigin = '0 0'; void b.offsetWidth;
    b.style.transform = `translate(${tx}px, ${ty}px) scale(${s})`; };
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
        page.goto(step["goto"], wait_until=step.get("wait_until", "networkidle"))
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
            page.get_by_text(w["text"]).first.wait_for(state="visible", timeout=step.get("timeout", 30) * 1000)
        else:
            page.locator(w).first.wait_for(state="visible", timeout=step.get("timeout", 30) * 1000)
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
        loc = page.get_by_text(step["expect"]).first
        loc.wait_for(state="visible", timeout=15000)
        if show:                                   # the proof, on screen: a check mark next to what was found
            page.evaluate("([t, b]) => window.__dvCallout(t, '✓', 'ok', b, 1800)", [step["expect"], loc.bounding_box()])
            page.wait_for_timeout(1800)
        return f"expect {step['expect']!r}"
    if "zoom" in step:
        if step["zoom"] in (False, None, "out"):
            page.evaluate("(a) => window.__dvZoom(null, 1, a)", show)
            page.wait_for_timeout(900 if show else 50)
            return "zoom out"
        page.evaluate("(a) => window.__dvZoom(null, 1, false)", False)     # measure the target unzoomed
        _, _, _, b = target(page, step["zoom"])
        page.evaluate("([b, s, a]) => window.__dvZoom(b, s, a)", [b, step.get("scale", 2), show])
        page.wait_for_timeout(900 if show else 50)
        return f"zoom ×{step.get('scale', 2)} on {step['zoom']}"
    if "callout" in step:
        b = target(page, step["at"])[3] if step.get("at") else None
        ms = int(step.get("seconds", 3) * 1000)
        if show:
            page.evaluate("([t, i, k, b, ms]) => window.__dvCallout(t, i, k, b, ms)",
                          [step["callout"], step.get("icon", ""), step.get("tone", "info"), b, ms])
            page.wait_for_timeout(ms)
        return f"callout {step['callout']!r}" + (f" at {step['at']}" if step.get("at") else "")
    if "arrow" in step or "underline" in step:
        kind = "arrow" if "arrow" in step else "underline"
        _, x, y, b = target(page, step[kind])
        ms = int(step.get("seconds", 2) * 1000)
        if show:
            if kind == "arrow":
                page.evaluate("([b, f, ms]) => window.__dvArrow(b, f, ms)", [b, step.get("from", "left"), ms])
            else:
                page.evaluate("([b, ms]) => window.__dvUnderline(b, ms)", [b, ms])
            page.wait_for_timeout(ms)
        return f"{kind} {step[kind]}"
    if "blur" in step:
        target(page, step["blur"])[0].evaluate("e => { e.style.filter = 'blur(9px)'; }")
        return f"blur {step['blur']}"
    if "pause" in step:
        page.wait_for_timeout(int(step["pause"] * 1000) if show else 0)
        return f"pause {step['pause']}"
    raise ValueError(f"unknown step: {step}")


def run(scene, out=None):
    w, h = scene.get("width", 1920), scene.get("height", 900)
    show = out is not None
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=scene.get("headless", True))
        kw = {"viewport": {"width": w, "height": h}, "device_scale_factor": 1}
        if scene.get("storage_state"):                 # a saved sign-in, loaded into a throwaway context
            kw["storage_state"] = scene["storage_state"]
        if show:
            kw.update(record_video_dir=str(Path(out).parent / "pw-video"), record_video_size={"width": w, "height": h})
        ctx = browser.new_context(**kw)
        ctx.add_init_script(CURSOR_JS)
        page = ctx.new_page()
        t0 = time.monotonic()
        page.goto(scene["url"], wait_until=scene.get("wait_until", "networkidle"))
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


def login(url, state, until, minutes=15, headless=False):
    """A person signs in once in a visible browser; the session is saved for the scenes. Playwright's Chromium
    uses a mock keychain, so macOS asks for no keychain password, and no debug port is opened."""
    import os
    import re
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        ctx = browser.new_context(viewport={"width": 1280, "height": 860})
        page = ctx.new_page()
        page.goto(url, wait_until="load")
        print(f"A browser window named \"Chromium\" (or \"Google Chrome for Testing\") is open at {url}.\n"
              f"Sign in there. It closes by itself once the address matches {until!r}.", flush=True)
        end = time.monotonic() + minutes * 60
        while time.monotonic() < end:
            if any(re.search(until, pg.url) for pg in ctx.pages):
                page.wait_for_timeout(1500)            # let the last cookies land
                Path(state).parent.mkdir(parents=True, exist_ok=True)
                ctx.storage_state(path=state)
                os.chmod(state, 0o600)
                print(f"signed in: session saved to {state}")
                browser.close()
                return True
            page.wait_for_timeout(1000)
        browser.close()
        print(f"timed out after {minutes} min: no page matched {until!r}")
        return False


if __name__ == "__main__":
    if sys.argv[1] == "login":
        import argparse
        ap = argparse.ArgumentParser(prog="browser.py login")
        ap.add_argument("url"), ap.add_argument("state")
        ap.add_argument("--until", required=True, help="regex the address must match once signed in")
        ap.add_argument("--minutes", type=float, default=15)
        ap.add_argument("--headless", action="store_true", help="for tests only")
        a = ap.parse_args(sys.argv[2:])
        sys.exit(0 if login(a.url, a.state, a.until, a.minutes, a.headless) else 1)
    mode, scene_path = sys.argv[1], sys.argv[2]
    scene = json.loads(Path(scene_path).read_text())
    if mode == "dry":
        sys.exit(0 if run(scene) else 1)
    sys.exit(0 if run(scene, sys.argv[3]) else 1)
