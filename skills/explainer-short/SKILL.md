---
name: explainer-short
description: Turn an idea or topic into a finished vertical explainer video (YouTube Shorts / Reels / TikTok, 1080x1920 MP4 + subtitles + cover) in the dark-canvas, hand-lettered, one-continuous-diagram tech-explainer style (like KodeKloud Shorts) — locally and free (Remotion + Kokoro TTS, no paid APIs, no video models, no face). Use whenever the user asks to make/generate/create a short, reel, explainer video, or "video about <topic>", wants to explain a technical concept (how X works, X vs Y, system design, interview question) as a video, or says "idea to video".
metadata:
  version: "1.1.0"
  author: mohamed-stifi
---

# Explainer Short (idea → finished video)

You produce ONE finished video per request by following the 7 steps below **in order, once**.
Every step has a command, an output and a stop condition. Do not invent extra steps.

Paths: `SKILL` = the folder containing this file. `STUDIO` = the video workspace
(default: `./explainer-studio` in the current project; reuse it if it exists). `SLUG` = kebab-case id
of the video, e.g. `how-https-works`.

## Hard limits (keeps the run short and cheap)

- Ask the user **at most one** question, and only if there is no topic at all. Otherwise decide
  yourself (length, format, brand) using the defaults below and state your choices in the final reply.
- `check.sh` → fix → `check.sh` at most **2 fix rounds**. Then render, and list any remaining issue in the reply.
- Regenerate the voice at most **2 times** (only for length or a mispronounced word).
- Do not edit `src/kit/` (except adding an icon). Do not install other packages or tools.
- Read `template/src/videos/example/` once (it is the reference implementation). Do not read the kit source; `references/kit-api.md` documents it.

"Short", "reel", "explainer short" = the vertical FORMAT, not the length mode. Use the "short" length mode only if
the user asks for a quick/very short/under-a-minute video or gives seconds.

Defaults: length **95–120 s** (300–370 words; "short" = 55–70 s, "full" = the reference length 160–175 s — see
`references/script-guide.md`), voice `am_michael` speed 1.18, brand = the user's name/channel if known, else `"YourBrand"`.
The style rules come from measuring 23 reference videos; the evidence is in `references/style-evidence/` (humans only — you don't need to read it).

## Step 1 — Setup (once per machine, ~3 min first time, ~2 s after)

```bash
bash SKILL/scripts/setup.sh STUDIO
```
Stop condition: last line `READY: …`. If it prints `MISSING TOOLS`, tell the user exactly what to install and stop.
(Set `KOKORO_MODELS=<dir>` first if the voice model files already exist somewhere, to skip a 340 MB download.)

## Step 2 — Plan (no code yet)

Read `references/script-guide.md`. Then write `STUDIO/src/videos/SLUG/plan.md` (≤ 25 lines, after Step 3 creates the folder):
1. **Title** in one of the formats (How X works · X vs Y · Interview: … · System design: how <product> does X).
2. **Running example**: a named person + a concrete product/input/value used from start to end.
3. **Beats** (sections) with ids, 6–9 of them, each = one idea.
4. **Stages**: read `references/visual-guide.md`, then write one line per section:
   `section → added / moved / focus (spotlight ids) / leaves` (see "Planning stages" there). Pick 3–4 accents and bind each to one thing.

## Step 3 — Script

```bash
bash SKILL/scripts/new_video.sh STUDIO SLUG
```
Write `STUDIO/src/videos/SLUG/script.json` (format: see the example's `script.json`). Rules that break things:
- `sections[].id` unique, simple (`hook`, `scenario`, `mechanism`, …). Last section is the CTA.
- Write numbers/symbols as you want them **shown** and map them to how they are **said** in `pronounce`
  (`"429": "four twenty nine"`, `"API": "A P I"`, `"SQL": "sequel"`, `"k8s": "kubernetes"`).
- Sentences ≤ 18 words. Only `. ! ?` end sentences (each sentence is synthesized separately).
Self-check against the rule list at the end of `script-guide.md` before moving on.

## Step 4 — Voice

```bash
bash SKILL/scripts/voice.sh STUDIO SLUG
```
Prints each section's start/end and `Done: <sec>s, <words> words, <wpm> wpm`. Stop condition: duration within
the target ±15 %. Too long → cut sentences (not speed) and run once more.

## Step 5 — Visuals

Read `references/kit-api.md` and the example (`STUDIO/src/videos/example/Video.tsx` + `stages/*.tsx`).
Write `STUDIO/src/videos/SLUG/Video.tsx` + one file per stage in `stages/`. Non-negotiable:
- Every element's `at` comes from `cue(section, word)` or `sec(section).from` — never hard-coded seconds.
- One continuous canvas: things persist, move, dim and get re-used. No full-screen clears except between stages.
- Something visibly changes at least every ~3 s of narration (new element, highlight, state change, move).
- Focus = Spotlight plan on `<Canvas focus>` (dim the rest) — the main device of the style.
- No subtitles. Captions (`Takeaway`) ≤ 7 words, 2–6 per video.
- Keep content in the safe zone (x 60–1020, y 280–1480; title ≈150; caption just under the diagram).
- Fill the width: main panels w 960 (or 2 × 465). Nothing smaller than 26 px.

## Step 6 — Check (max 2 fix rounds)

`check.sh` and `render.sh` start a local server + headless Chrome. In a sandboxed agent, run both commands
**outside the sandbox**. If your environment cannot do that at all (`No available ports found`, Chrome won't start,
unsandboxed calls refused): stop after Step 5, and tell the user to run `check.sh` then `render.sh` themselves
(give both full commands). Do not try workarounds.

```bash
bash SKILL/scripts/check.sh STUDIO SLUG          # optional 3rd arg: "12.5,30,41" = extra seconds to inspect
```
It lints every `cue()` against the voice timing (instant), typechecks, renders ~3 frames per section + end card, and writes `out/SLUG/check/sheet.jpg`
(+ `NN.jpg` single frames). **Look at the sheet image** (and 2–3 single frames at full size). Fix only what fails:

| Check | Fails when |
|---|---|
| overlap | text/boxes collide or are cut by the screen edge |
| scale | the diagram uses < 80 % of the width or leaves y 900–1400 empty in a busy section; text you must squint at in a 540 px wide frame |
| readability | any label smaller than ~28 px, or text over a busy area |
| sync | an element appears before its word, or a frame shows an empty/stale canvas while narration talks about something |
| continuity | a stage looks unrelated to the previous one (everything replaced) when the story continues |
| focus | the thing being talked about is not highlighted (Focus / amber / dim others) |
| density | a frame with > 9 visible elements, or > 2 lines of takeaway text |

Type errors / `cue not found` errors print the fix (the list of valid words). Fix and re-run.

## Step 7 — Render + deliver

```bash
bash SKILL/scripts/render.sh STUDIO SLUG
```
(If headless Chrome is blocked by a sandbox, re-run this command outside the sandbox.)
Then write `STUDIO/out/SLUG/upload.md`: title (= the video title, ≤ 60 chars, 1 emoji at the end allowed),
2-sentence description, 5 hashtags, and a "Facts to verify" list (every number/claim you stated from memory).

**Final reply** (short): the MP4 path, duration, the SRT/cover/upload.md paths, the choices you made
(format, length, running example), and any known issue left. Then stop.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `cue not found: "x" #1 in section "y". Words: …` | use a word from the printed list, or the right section |
| a word is mispronounced | add it to `pronounce` and re-run step 4 |
| `Cannot find module './timing.json'` | step 4 not run for this SLUG |
| composition `SLUG` not found | run `voice.sh` (it registers the video) |
| Chrome / `SIGABRT` / `ENOTFOUND remotion.media` / `No available ports found` | sandbox blocks the browser/port: run the command unsandboxed (see Step 6) |
| `failed to canonicalize path …/voice/.venv/bin/python3` or other uv/venv errors | delete `STUDIO/voice/.venv` and re-run `setup.sh` |
| a frame shows text overflowing a panel | give the `<El>` a bigger `h`, fewer lines, or smaller font (≥ 26 px) |
| video too long/short | edit the script (≈3.1 words per second at speed 1.18), re-run step 4 |
