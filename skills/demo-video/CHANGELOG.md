# Changelog — demo-video (formerly repo-walkthrough-video)

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
