---
name: video-style-extractor
description: Study a set of reference videos (YouTube/Shorts/TikTok links or local mp4 files) and write a precise, reusable style guide (topics, hooks, script structure, pacing, visuals, motion, colors, rules) that an agent can follow to make new videos in the same style. Runs locally and free (yt-dlp, ffmpeg, faster-whisper). Use when the user shares example videos and says "I like this style", "analyze these videos", "clone/copy the style of", "make videos like these", or wants a style guide from examples.
metadata:
  version: "1.0.0"
  author: mohamed-stifi
---

# Video Style Extractor (examples → style.md)

Output: `<WORK>/style.md`, filled from `references/style-template.md`, backed by evidence from the videos.
One pass, in order. No re-downloads, no second analysis pass.

`SKILL` = this folder. `WORK` = a new folder for this study, e.g. `./style-research/<name>`.

## Step 1 — Collect (automatic, ~1 min per video the first time)

```bash
bash SKILL/scripts/collect.sh WORK <url> <url> ...      # or: collect.sh WORK urls.txt
```
Creates `videos/`, `sheets/<id>.jpg` (contact sheet: 1 frame every 3 s, read left→right, top→bottom),
`subs/<id>.txt` (timestamped transcript), and `metrics.md` (duration, words, words-per-minute, hard cuts,
first lines = hooks, last lines = CTAs). Local mp4 files: put them in `WORK/videos/` and run with no urls.
If downloads fail with 403/429, wait a minute and re-run (it skips finished work). Network problems in a
sandbox → run the command outside the sandbox.

## Step 2 — Read the numbers

Read `WORK/metrics.md` fully. These numbers are facts; the style guide must agree with them
(length, wpm, cuts per video).

## Step 3 — Look and read (budget-aware)

- ≤ 8 videos: view every contact sheet and read every transcript yourself.
- > 8 videos: split into 2–3 groups and, if your agent can run sub-agents, give each group to one with the
  headings of `references/style-template.md` as the required output; otherwise view all sheets but read
  only 6 transcripts in full (highest views first) and skim the rest via the hooks/CTAs in `metrics.md`.
- Open 3–5 single frames at full size (`frames/<id>/f_NNN.jpg`) to read exact colors, fonts and sizes.

## Step 4 — Write style.md

Fill every heading of `references/style-template.md`. Rules:
- Every claim cites evidence: a count ("21/23 videos"), a number from metrics, or a short quote (≤15 words).
- Separate **style** (copy it) from **content/brand** (never copy: logos, names, channel identity, exact scripts).
- End with 12–20 imperative, testable rules for scripts and 12–20 for visuals.
- If the target pipeline is the `explainer-short` skill, add a section "Mapping to explainer-short" listing
  what changes in its `references/script-guide.md`, `references/visual-guide.md` or kit (`theme.ts` colors, fonts).

## Step 5 — Reply

Give the path to `style.md` and a 5-line summary. Stop. (Raw videos stay in `WORK/videos`; tell the user they
can delete them — they are only needed for re-analysis.)
