---
name: repo-walkthrough-video
description: Test every function of a code repository for real, then record a narrated, captioned, chaptered 1080p walkthrough video (MP4 + SRT + per-chapter files + README) that explains the project to humans and the team. Terminal scenes are real commands recorded with VHS, the voice is macOS `say`, slides are drawn with Pillow, and ffmpeg assembles everything with chapter markers and a subtitle track. Use this skill whenever the user asks to record, film, screencast, or "take a video" of a repo or its features, wants an onboarding / demo / walkthrough / tour video of a codebase, wants to "test everything and show it", or wants a video explaining a project for a team, even if they don't name VHS or ffmpeg.
compatibility: macOS (uses `say` and SF fonts), plus vhs, ffmpeg/ffprobe, Python 3 with Pillow, jq. Docker only if the repo's features need it.
metadata:
  version: "1.0.0"
  author: mohamed-stifi
---

# Repo walkthrough video

The goal is a video a teammate can watch to understand a repo: what it is for, how its parts fit
together, and every function run for real, including what is broken today. Two jobs are mixed in this,
and they should happen in this order:

1. **Test the repo for real.** Every command shown in the video has really been run and its output read.
2. **Record it as a story.** Chapters follow the shape of the system, and each one is narrated.

A video that only shows commands that succeed misleads the team. The failures you find while testing
are often the most valuable part of the video, so give them their own closing chapter.

## Output layout

Work in a folder **outside** the repo. The user picks it; if they don't, use a sibling such as
`<parent-of-repo>/video/`, because a disk-root path like `/video` is often read-only on macOS.

```
video/
├── <name>-walkthrough.mp4    # full video: chapters + mov_text subtitle track
├── <name>-walkthrough.srt    # same narration, also usable as a transcript
├── chapters/NN-slug.mp4      # one file per chapter
├── README.md                 # chapter index with start times, how to re-record
├── src/                      # engine.py, make_readme.py, script.py (+ helpers)
├── work/                     # throwaway clone(s) of the repo: every command runs here
└── build/                    # intermediate files (per-segment voice, frames, clips)
```

Never run the demo commands on the user's working copy. Clone it into `work/` (`git clone <repo> work/<name>`)
so the video can break things on purpose (bad manifests, injected faults) and reset with
`git checkout . && git clean -fd`. If the user's checkout has uncommitted changes, mention them and leave them alone.

## Step 1: Check the tools, and tell the user what is missing

```bash
which vhs ffmpeg ffprobe jq; python3 -c "import PIL; print(PIL.__version__)"; say -v '?' | head -3
```

If anything is missing, **tell the user what to install, and why**, before installing it
(`brew install vhs ffmpeg jq`). For Pillow, don't touch the system Python. Run the engine through uv instead:
`uv run --no-project --with pillow python engine.py ...`. Wrap it in a shell function (`py() { uv run
--no-project --with pillow python "$@"; }`), because a variable holding the command won't expand as one. The same goes for anything the repo needs, such as
Docker running, a simulator stack, or credentials. Ask the user for those, and never invent a secret.
A premium voice (System Settings → Accessibility → Spoken Content, e.g. "Ava (Premium)") sounds much
better than the default `Samantha`. Offer it, but don't block on it; `VOICE=... engine.py --force` re-voices later.

## Step 2: Understand and test the repo before you write a word of narration

Read the README, the docs or ADRs, the CLI entry points (`--help` of every subcommand), the test markers,
the Makefile and the CI config. Build an inventory of **every function** a user can exercise: each CLI
subcommand, each test suite, each integration, each failure mode the code defends against.

Then run all of it in `work/`, and write down:
- the exact commands that show each feature well, with short output (pipe through `jq`, `head`, `tail`, `cut -c1-160`)
- what fails, and whether it is a real bug or just your environment (wrong default path, missing env var).
  Fix environment problems in the clone or with env vars, and make that fix **visible in the video**,
  because the team will hit it too.
- how to break each safety rule on purpose (a fixture, a `sed` on a copy), so the video can show the rule firing

These notes become the findings chapter. Keep them as a list of numbered, concrete items.

## Step 3: Plan the chapters

Follow the system's own pipeline, not the folder listing. A shape that worked well:

| # | Chapter | Contents |
|---|---|---|
| 00 | Welcome | title card, then a "what you will see" slide |
| 01 | Big picture | a one-sentence purpose, the pipeline as boxes and arrows, a repo-layout terminal scene |
| 02 | Setup | install, the CLI grouped by purpose, the fast test suite |
| … | one chapter per pipeline stage | real commands, plus a "break it on purpose" scene per rule |
| … | live / integration | the real backing services, end to end |
| N-1 | Contracts / hand-off | what other teams rely on |
| N | Findings and next steps | the numbered findings list, then what to do next |

Aim for 1–3 minutes per chapter and 15–25 minutes in total. A chapter is one idea; a segment is one
screen plus one narration. Show the user this outline (chapter titles and one line each) before recording.

## Step 4: Write `src/script.py`

Copy the bundled scripts into the video folder:

```bash
mkdir -p video/src && cp <skill-dir>/scripts/{engine.py,make_readme.py,agent.jq} video/src/
cp <skill-dir>/scripts/script_template.py video/src/script.py
```

`script.py` holds all the words and all the commands. `engine.py` turns it into video. Read
`references/script-format.md` for the full segment schema, the slide layouts and the narration style.
`scripts/script_template.py` shows every segment type with a working example; build the rest of the chapters
in the same shape (Step 3 gives the chapter outline).

Narration rules that matter most:
- Write for the ear: short sentences, no markdown, and spell out acronyms the voice mispronounces
  (`"M C P"`, `"C L I"`), or add them to `SPOKEN` in `script.py`.
- Say what the viewer should *look at* ("Look at the skills: zero"). The voice and the picture must
  agree, so if you change a command's output (a count, a speed factor), fix the sentence too.
- Captions (the bottom bar of a terminal scene) are one line that states the point, with `code` in backticks.

## Step 5: Dry-run, then record

```bash
cd video/src                          # `py` = Python with Pillow (see Step 1)
py engine.py --dry                    # runs every terminal command in plain bash and prints the output, no video
py engine.py --dry --only 04          # one chapter
py engine.py --only 04                # record one chapter (fast feedback on the look)
py engine.py                          # everything missing or changed, then assemble the full video
py engine.py --only 07 --reuse-terms  # keep the VHS clips, redo only the voice and frames (narration fixes)
py make_readme.py                     # writes README.md with the chapter index
```

Always dry-run first. It is minutes instead of an hour, and it catches every command that errors, hangs or
prints too much. Record one chapter first and look at frames before the full build:

```bash
ffmpeg -v error -ss 20 -i chapters/04-*.mp4 -frames:v 1 build/check.png   # then Read the PNG
```

A full build takes a long time (about 40 minutes for 21 minutes of video). Run it in the background and
wait on its completion notice rather than polling. Chapters are cached by a hash of their script, so
re-running rebuilds only what changed.

## Step 6: Verify and hand over

```bash
ffprobe -v error -show_chapters -show_streams -of compact video/<name>-walkthrough.mp4 | head -40
```

Check the following:
- the duration
- 1920×1080 h264, aac, and a mov_text subtitle stream
- one chapter marker per chapter
- sample frames from a few chapters: no text overflowing boxes, captions within two lines

Then tell the user the exact paths of the MP4, the `chapters/` folder, the SRT and the README. Add how to
open it (`open video/<name>-walkthrough.mp4`; QuickTime or VLC show the chapter and subtitle menus) and
the findings list. Mention any containers or services you left running, and how to stop them.

## Pitfalls already solved (keep these in mind when editing the engine)

- **Sandboxed shells:** vhs, Docker, `uv` caches and `say` often fail under a command sandbox ("Operation not
  permitted", Docker socket errors). Those commands need to run outside it. `open` is blocked too, so give
  the user the command to run themselves.
- **VHS frame drops:** the default 50 fps drops frames on long scenes. The engine uses `Set Framerate 15`.
- **VHS `Output` must be a bare file name.** Run `vhs` with `cwd` set to the output folder.
- **VHS strings have no escapes.** `json.dumps` quoting breaks PS1 escape sequences. Use `q()` in the
  engine, which picks a `"`, `'` or `` ` `` delimiter that the text doesn't contain.
- **`Wait` hangs** if the pattern doesn't match the prompt. The engine sets a PS1 that ends in `$` and
  uses `WaitPattern /[>$]$/`. Commands that print a final line ending in `$` or `>` can end a wait
  early, so add a `pause` there.
- **Long-running scenes** (an AI agent, a pipeline run): set `"speedup": True` on the segment. The engine
  speeds the clip up to roughly the narration length and stamps `sped up ×N.N` in the header, so say that
  it is sped up.
- **Text overflow on slides:** `wrap()` measures code spans in the monospace font. Keep box bodies short,
  and split long paths across two lines.
- **Wait loops:** a `pgrep -f <pattern>` loop matches itself. Wait on a PID or a file instead.
- **Before-hooks** (`"before": [...]` on a chapter) prepare state: reset a DB container, trigger a
  pipeline, inject a fault. Put the **undo** (reset, un-inject) in the same chapter, so a rebuild of one
  chapter never leaves the platform broken.
- **Secrets** needed by the demo go in a git-ignored file in the clone (for example `dev-vault.env`). Never show
  their values on screen, and never commit them.

## Showing an AI agent at work (optional)

If the repo builds or configures an agent, the strongest scene is the agent diagnosing a real, injected
failure. Run it headless with stream-json output, and format the stream with the bundled `agent.jq`
(one line per tool call, then the answer):

```bash
claude -p "<question>" --output-format stream-json --verbose | jq -rj -f /path/to/video/src/agent.jq
```

Mark that segment `"speedup": True`, and reset the fault afterwards in the same chapter.
