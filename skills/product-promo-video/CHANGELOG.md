# Changelog — product-promo-video

## 1.0.0 — 2026-11-19
- First version, distilled from two real films (Nemo: a 53 s incident film and a 58.5 s main film with 15 s and 6 s cuts).
- Workspace per product under `~/.product-promo-videos/<working-dir>/<slug>/`, git-versioned; `output/` holds only the
  final videos, `output-extras/` the rest; final copy into `<working dir>/promo-videos/<slug>/`.
- Video types: promo (default), story, teaser, explainer, vertical 9:16, square 1:1.
- Kit: 3D camera with speed-based motion blur, 7-easing vocabulary, brand tokens (product brand or house style),
  UI primitives, ChapterTag, burned-in captions composition.
- Audio engine: Kokoro-82M voice (af_heart default, any Kokoro language, or a custom TTS via `tts_custom.py`),
  synthesized music (busy/dark/drive/lift/resolve), 22 synthesized sound effects synced from scene frames, ducking,
  −14 LUFS master, soft subtitle track, .srt/.vtt/transcript.
- Checks: contact sheets, Whisper pronunciation check, loudness and duration checks.
- Fixes learned in the real runs: foreground subagents, scratch-folder authoring when file tools are blocked,
  render retry + 120 s delayRender timeout, `-t` instead of `-shortest` with subtitle tracks, bash 3.2 compatible scripts.
