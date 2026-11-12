# Changelog — explainer-short

## 1.1.0 — 2026-11-12
Fixes from 3 test runs (see `TESTS.md`):
- `check.sh` runs a cue linter first (`cues.mjs`): wrong cue words fail in ~1 s with the list of valid words.
- `check.sh` extra seconds are added to the default frames (they used to replace them).
- Rules: "fill the width" + scale check; rendered-size table in `kit-api.md`; cue tokenization documented.
- Sandbox guidance for check/render + a stop rule when Chrome cannot run; venv auto-repair in `setup.sh`.
- "Short" = the vertical format, not the length mode; `plan.md` required; "Facts to verify" in `upload.md`.
- Kit: bigger default `Tag`; font licenses (OFL) shipped next to the fonts.

## 1.0.0 — 2026-11-12
- First version: style measured on 23 reference Shorts; Remotion kit (Spotlight, states, Packet, Sticker, IconGrid,
  Stepper, EndCard…), Kokoro voice with word timings, `cue()` sync, 7-step bounded procedure.
