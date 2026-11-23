# Changelog — demo-video (formerly repo-walkthrough-video)

## 4.2.0 — 2026-11-23
- **Reuse of recorded scenes.** Each live recording (a capture) is kept in `.video_demo_dir/clips/` under a key
  made from its commands or browser steps, the code its chapter `covers` (committed, uncommitted, untracked),
  its `inputs`, the capture tools, and the scene before it (so a re-recorded scene re-records what follows,
  up to the next `fresh` chapter). Narration, numbering and voice changes record nothing live; another video
  reuses the same chapters.
- `engine.py --plan`: per chapter, reuse / re-voice / record again, with the reason (which files changed).
- "CHECK NARRATION" when a recording's screen text changed but its words did not.
- `engine.py --gc` removes recordings no version uses. `--reuse-terms` now means: use this scene's last
  recording even if its key changed. Before-hooks run only when a scene is recorded live.

## 4.1.0 — 2026-11-23
- **Cleanup of what the video owns** (`scripts/ledger.py`): `snapshot` before starting anything; `cleanup
  [--dry] [--limit-gb 2]` checkpoints the data of the video's own Compose projects, then removes their
  containers, networks and volumes and stops the processes started in the video folder since the snapshot; the
  user's stacks in the video's `WORKDIRS` go back exactly as found (stopped again, extra containers removed,
  volumes kept); anything else is only reported. `status` lists what runs; `restore` puts a checkpoint back.
- Clones get the Compose project name `dv-<clone>` in every scene and hook, so they never take over the user's
  own project of the same name.
- INDEX.md shows the checkpoints, the last cleanup and what was left alone.

## 4.0.0 — 2026-11-23
- **Breaking: one folder per repo.** Everything lives in `<repo>/.video_demo_dir/`, git-ignored by its own
  `.gitignore` (`*`): `INDEX.md` and `state.json`, `features/` (the feature map), `videos/<slug>/vN/` (each
  re-record is a new version), `work/` (clones, kept and refreshed), `secrets/` (mode 700), `logs/`, `run/`.
- `scripts/vdir.py` (stdlib): `init` (with a `.dockerignore` warning and `--import` of an old folder), `video`
  (a new version, starting from the last one's script), `register` (the engine calls it after a full build),
  `note`, `leftover`, `index`.
- SKILL.md step 0: read `INDEX.md` first and reuse what exists.
- The recording lock covers the whole repo; logs go to `logs/<slug>-vN.log`.

## 3.1.0 — 2026-11-23
- **Fail fast.** Each recorded command's exit codes are written invisibly; the first unexpected failure (also
  inside a pipe) stops the build after its scene. `{"cmd": …, "fails": True}` shows a failure on purpose. A
  failing `before` hook stops the build too.
- **A faithful dry run:** one interactive bash per scene on a terminal, closed at the end like VHS's, so a
  service started with a bare `&` dies in the dry run too; `cd` and variables carry over between commands.
- **`SERVICES`** health checks: a service that stops answering stops the build, with a `nohup … & disown` hint.
- **`--detach` / `--status`:** the recording runs as its own process (it survives the agent's session, keeps a
  Mac awake), one at a time (a lock).
- **Sign-ins:** `browser.py login <url> <file> --until <regex>` saves a session (mode 600) after the person
  signs in, without a keychain prompt; scenes load it with `storage_state`. `wait_until` for pages that never
  go quiet, `timeout` on waits, `headless`.
- **Chapter markers** stay right in long videos (`-movie_timescale 1000`).
- The dry run ends with an estimate of the recording time.

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
