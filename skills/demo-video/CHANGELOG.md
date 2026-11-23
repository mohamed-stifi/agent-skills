# Changelog — demo-video (formerly repo-walkthrough-video)

## 3.0.0 — 2026-11-23
- **Only the viewer's commands on screen.** Before a dry run or a recording, the engine checks every typed
  command: a helper written for the video (a script in `src/`, `build/` or `work/bin/`, a file added to the
  clone that git neither tracks nor ignores, a function or alias from a hidden `setup`) stops the run with a
  list. `VIEWER_HAS` names files the viewer made on screen earlier.
- **Breaking:** `api` scenes type the real `curl … | jq` line with the full URL (`"status": True`: `curl -si`), the
  same line as the doc. `scripts/req.py` and `scripts/agent.jq` are removed; `then` checks and agent scenes
  that used them must use the project's or the system's commands.
- Any command can be typed, whatever quotes it holds (no more script files to dodge VHS quoting).
- The default prompt shows the current folder's name, so viewers see where each command runs.
- SKILL.md: act as the viewer, who knows little: only their commands, questions asked the way a user would,
  failures and retries shown, each chapter starting from where they are, each new command explained once. An
  agent is asked the way its users ask it.

## 2.4.0 — 2026-11-22
- Point where to look, from a style study of the user's reference videos: browser steps `zoom` (the page scales
  up around a target, sharp, then back; clicks still land), `callout` (a pill with an icon and a few words,
  `info`/`warn`/`ok`), `arrow`, `underline`, `blur` (secrets), and a ✓ callout when an `expect` passes. The
  `highlight` frame is restyled: a cyan glow with corner brackets.
- `step="#label"` is numbered across the whole video: "Step 3 of 5 · label", in the video and the doc.
- `section` cards (a gradient and one pill, between steps) and `concept` tiles (icon, caps title, subtitle,
  optionally joined by "+"); icons from Menlo / Apple Symbols / DejaVu Sans.
- `references/video-types.md`: 14 script rules for every guide (numbered steps aloud, exact labels as
  imperatives, a proof per step, warnings when they apply, terms defined on first use, …).
- The companion doc shows step badges, warnings, blurred-secret notes, "You should see …", sections and tiles.

## 2.3.0 — 2026-11-22
- `diagram` scenes: boxes and arrows that light up the parts each sentence names, in time with the voice (one
  picture per sentence; `steps` picks the boxes lit per sentence, default box k in sentence k).
- `scripts/make_doc.py` writes the companion doc `<name>.md` and `doc/` screenshots: one section per chapter
  with its start time and clip, the narration as prose, commands in bash blocks, API calls and `req` effect
  checks as curl, browser steps as numbered steps, a screenshot per scene.
- `references/video-types.md`: the chapter shape of each video type (feature demo, tutorial, explainer, pilot,
  project guide); SKILL.md points to it.
- Tests: `check()` now returns failure, so a failing check prints its diagnostics.

## 2.2.0 — 2026-11-22
- `api` scenes: real HTTP calls shown the way a developer reads them, through `scripts/req.py` (stdlib only):
  `→ METHOD path` and the body, `← status reason · time` (green, yellow or red), then the response, pretty and
  coloured (`show`: a jq filter). `then` lists the **effect checks** that show what the calls changed (a row,
  a log line, another endpoint). The scene is recorded as a terminal scene, so the dry run covers it.

## 2.1.0 — 2026-11-22
- `browser` scenes: a real Chromium (Playwright, `scripts/browser.py`) uses the app like a person: a visible
  cursor glides to each target and ripples on a click, typing is key by key, `highlight` frames an element.
  Steps: goto, click, hover, type, press, scroll, wait, highlight, expect, pause. Framed like terminal scenes;
  the blank start is trimmed and the last frame holds until the narration ends.
- `--dry` runs every browser step headless and stops at the first failing step with its number, the step, the
  URL and the reason. A dry run really acts, so reset the app's state in the chapter's `before` hook.
- `setup.sh` installs the Playwright browser; `run.sh` adds Playwright.

## 2.0.0 — 2026-11-22
- Renamed from `repo-walkthrough-video` and rebuilt around the request: the agent reads the subject (a feature,
  a service, several parts, the whole project), the video type (feature demo, tutorial, explainer, pilot,
  project guide) and the audience, maps the repo's features, asks for everything that needs the user's hands
  in one chat checklist before trying, and pilots the subject for real before recording. Length follows the
  content.
- Voice: Kokoro-82M (local, neural; `VOICE=af_heart`) instead of macOS `say` (still there: `VOICE_ENGINE=say`).
  Each sentence is voiced separately, so subtitles use the real sentence times.
- `scripts/setup.sh` checks the tools and fetches the voice model once into `~/.cache/kokoro` (shared,
  `KOKORO_MODELS`); `scripts/run.sh` runs the engine with its Python packages through uv.
- `scripts/install.sh` (repo) removes a dangling link left by the rename.

## 1.0.0 — 2026-11-12
- First version in this repo: test every function of a repo for real, then record a narrated, chaptered 1080p
  walkthrough (VHS terminal scenes, macOS `say`, Pillow slides, ffmpeg chapters + subtitles).
- The example script from a private project is not included; `scripts/script_template.py` is the reference.
