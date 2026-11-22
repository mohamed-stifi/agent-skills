# Changelog — demo-video (formerly repo-walkthrough-video)

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
