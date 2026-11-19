---
name: product-promo-video
description: Turn a product (a website link, a repo or docs folder, or a short brief) into finished promotional videos — a story-driven 16:9 film of 60 s or less with 15 s and 6 s cut-downs by default, or a story, teaser, explainer, vertical 9:16 or square video — with powerful camera motion, UI drawn in code (no screenshots), the product's own brand, a local voice-over (Kokoro TTS), synthesized music and synced sound design, captions, subtitles and a transcript. Local and free (Remotion, Kokoro, ffmpeg). Use whenever the user asks to make, create or generate a promo video, product video, ad, launch teaser, demo film, explainer or "video for my product/app/startup", gives a product link or repo and wants a video of it, or asks for a voice-over, music or captions on such a video.
metadata:
  version: "1.0.0"
  author: mohamed-stifi
---

# Product promo video (product → finished videos)

You produce one set of finished videos per request by following the 9 steps below **in order, once**, then stop.
Feedback rounds (step 10) re-enter at the earliest affected step. Every step has a command, an output and a stop condition.

`SKILL` = the folder of this file. `WS` = the workspace printed by `setup.sh`.
Shell scripts are bash (macOS, Linux, Windows via Git Bash or WSL).

## Defaults (use them unless the user says otherwise; never ask about them)

| Setting | Default |
|---|---|
| Workspace (everything, git-versioned) | `~/.product-promo-videos/<working-dir path with / → ->/<product-slug>` (no product name → `session-<date-time>`) |
| Final videos only | `WS/output/`; everything else (subtitles, transcripts, audio masters, contact sheets) in `WS/output-extras/` |
| Copy for the user | `output/` is copied to `<working dir>/promo-videos/<slug>/` (or where the user said) |
| Type | **promo**: main film ≤ 60 s + 15 s + 6 s cuts (other types: `references/video-types.md`) |
| Format | 1920×1080 (16:9), 60 fps, H.264 CRF 16 |
| Language | English |
| Look | the product's own brand if the source has one; else the house style (white, ink, one yellow accent, Barlow) |
| Voice | Kokoro-82M `af_heart`, speed 1.0 (another model/voice/language only if the user names it) |
| Music + sound | synthesized by the engine, synced to the animation; mix −14 LUFS |
| Captions | soft subtitle track in every video + a `-captioned` version with burned-in captions + `.srt`/`.vtt` + transcript |
| CTA | "Request a demo →", no URL unless given |
| Approval checkpoint | none (show the script/storyboard first only if the user asks) |
| Subagents | if you can spawn them: 3 scene builders in parallel, in the **foreground**, on a strong mid-size model (e.g. Sonnet); a small model only for mechanical tasks. If you cannot: build the scenes yourself, group by group |

Ask the user **at most one** question, and only when there is no product at all to work from.

## Step 1 — Setup (≈ 3 min first time, seconds after)
```bash
bash SKILL/scripts/setup.sh "<Product name>" [--format 16:9|9:16|1:1] [--slug <name>]
```
Run it from the user's working directory (that is where the final copy goes). Stop condition: last lines
`WORKSPACE=…` and `READY`. `MISSING TOOLS` → tell the user exactly what to install and stop.
Re-running on an existing workspace keeps all files (use it to continue or iterate).

## Step 2 — Research → `WS/brief.md`
Read the sources the user gave: the URL (fetch the page and its main CSS), the repo/docs (README, docs/, design docs,
example scenarios), any brief. Fill `WS/brief.md`: product in one sentence, audience and buyer, **facts bank** (every
fact with its exact value and source), story material (the pain as a scene-able moment, proof moments, the bookend
image), brand (`references/brand.md`), settings. Apply the brand to `source/src/kit/tokens.ts` (+ fonts).
Stop condition: ≥ 8 facts with sources, brand decided (product brand or "house style"). Max 30 minutes of reading.

## Step 3 — Story and storyboard → `WS/STORYBOARD.md`, `src/timeline.ts`, `src/films.ts`
Read `references/video-types.md`, `references/story-and-script.md`, `references/storyboard-rules.md` and, once, the
example `references/examples/nemo-storyboard.md`. Write the storyboard: the one sentence, the structure table (scene,
beat, frames, ground colour, owner group), the rules block (copied unchanged), the facts the film uses, then one brief
per scene (world, beats with frame numbers, the decisive snap, the headline, the exit and the cut colour).
Set `SCENES` in `source/src/timeline.ts` and the deliverables in `source/src/films.ts` (ids like `promo-60s`,
cut parts in frames). Delete the example scene from `src/scenes/` and `src/scenes/index.ts` once real scenes exist.
Commit: `git -C WS add -A && git -C WS commit -m storyboard`.
Stop condition: total length within ±5 % of the type's target; every scene has one subject and an exit.

## Step 4 — Build the scenes
Split the scenes into 3 groups (`references/storyboard-rules.md`, last section). For each group send the brief in
`references/scene-brief.md`, filled in, to one subagent: all in one message, foreground. Without subagents, do the
groups yourself in order with the same brief as your checklist.
Stop condition: every scene file exists, is exported from `src/scenes/index.ts`, type-checks, and its group reported
the frame numbers of its snaps, stamps, counts, whips and exits.

## Step 5 — Assemble and review (max 2 fix rounds)
```bash
bash SKILL/scripts/render.sh WS all
```
Look at every `source/stills/<film>-sheet.png` and at full frames of the decisive moments
(`npx remotion still … --frame=N`). Check `references/qa.md` (picture). Fix in the scene files, re-render the scene,
then the films. Commit `review`.
Stop condition: no clipped text being read, no overlaps, cut colours match, facts all from the bank.

## Step 6 — Audio (max 2 pronunciation rounds)
Write `source/audio/films.py` (`references/audio.md`; full example: `references/examples/nemo-films.py`): per film the
voice lines timed to the beats, the cue sheet from the reported frame numbers, the music map. Cut-downs reuse the main
cue sheet with `remap()` plus an `into` at each join.
```bash
bash SKILL/scripts/audio.sh WS
bash SKILL/scripts/check.sh WS           # durations, loudness, and Whisper: what a listener hears
```
Fix every mis-heard word with a `say` respelling (or a rephrased line) and run both again.
Stop condition: `CHECK OK` and every line heard as written (or 2 rounds done: list what remains).

## Step 7 — Burned-in captions
```bash
bash SKILL/scripts/captions.sh WS
bash SKILL/scripts/check.sh WS --no-asr  # captioned durations must match too
```
Stop condition: `CHECK OK`.

## Step 8 — Deliver
```bash
bash SKILL/scripts/deliver.sh WS [--to <folder the user named>] [--no-copy]
```
Stop condition: `DELIVERED` and the list of videos.

## Step 9 — Reply (for non-technical people)
Lead with the videos: one line each with its path and what it is for (`-captioned` = muted social feeds). Then the
story in 4–6 lines, the defaults you used (type, look, voice, language), what you could not verify (you cannot hear
the mix: ask them to listen with headphones), and how to give feedback: "say what you felt and where (e.g. 0:12 too
fast)". No code, no Remotion details unless asked.

## Step 10 — Feedback rounds
Map each note to a scene, a line or a sound (timestamps → scene via `src/timeline.ts`). Re-enter at the earliest
affected step: wording or voice → 6; music/sound level → 6; a scene's look or motion → 4/5 for that scene only, then
6–8; story order → 3. Every round ends with `deliver.sh` (one git commit per delivery, so earlier versions stay
recoverable with `git -C WS log`). Max 3 rounds per request; then summarise what changed.

## Rules that are never relaxed
- Every number, name and claim comes from the facts bank (cited sources). No invented metrics, logos, testimonials, URLs.
- No screenshots or embedded raster UI: redraw it.
- `output/` contains only finished videos.
- Bounded loops: the max rounds above. When a limit is hit, deliver what works and list the open issues.

## Files
- `scripts/` setup.sh · render.sh · audio.sh · check.sh · captions.sh · deliver.sh (`_lib.sh` shared)
- `template/` the workspace: `source/` (Remotion project: `src/kit` camera, easings, UI, tokens; `src/Captioned.tsx`;
  `audio/` engine.py, films.py, timing.py, asr_check.py), `brief.md`, `STORYBOARD.md`, `README.md`
- `references/` video-types · story-and-script · storyboard-rules · scene-brief · brand · audio · qa · examples/
