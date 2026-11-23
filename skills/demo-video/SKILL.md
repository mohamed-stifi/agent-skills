---
name: demo-video
description: Make videos that show a repo really being used and explain it, made to order - a demo of one feature or service, a step-by-step tutorial, a how-it-works explainer with live demos, a pilot (test record), or a guide to the whole project - for the audience the user names, plus a written doc. The agent first uses the thing for real, as its user or developer would, then records it with a local neural voice, captions and chapters. Use when the user asks to record, film or "make a video" of a repo, a feature or a service; for a demo, tutorial, walkthrough, onboarding, pilot or "show me how to use / how it works" video; or to understand and explain a project an agent built.
compatibility: macOS or Linux with ffmpeg/ffprobe, uv, vhs, jq, git; Kokoro voice files (~340 MB, fetched once by scripts/setup.sh). Docker or other services only if the repo needs them.
metadata:
  version: "3.1.0"
  author: mohamed-stifi
---

# Demo video

The user has a repo (built by an agent, open source, or from their team) and wants to *understand and show*
it: how to run it, how to use each feature, how it works. You make the video an engineer would record after
building the thing: you use it for real first, then show it step by step, worded for whoever will watch.
`SKILL` = this folder.

## 1. Read the request
Take three things from the user's words, and ask one short question only when one of them is unclear:
- **Subject:** one feature ("the `--audit` flag"), a service ("the audit service"), a group of parts (the UI
  and its APIs), or the whole project.
- **Video type:**

  | They say… | Type | Shape |
  |---|---|---|
  | "demo", "show the feature", "for the PR" | feature demo | the problem, then the feature used end to end on real data, then the result |
  | "tutorial", "how to use", "step by step", "onboarding" | tutorial | prerequisites, install, first use, each task in order, troubleshooting; every step on screen |
  | "explain", "how it works" | explainer | the parts and the flow as diagrams, each followed by a live demo of that part |
  | "pilot", "test it", "is it working", "QA" | pilot | what was tested, how, what works and what is broken, as proof |
  | "the whole project", "everything" | project guide | the big picture, then one chapter per feature (each also a stand-alone clip), then findings |

- **Audience:** teammates, end users, new developers, a reviewer, a manager. It sets the words (no jargon for
  end users, internals for developers) and the depth. Unstated: the user and their team.

Length follows the content, never a target: two minutes for one flag, an hour or more for a large project.

## 2. Map the repo (the feature map)
Read the README, docs and ADRs, the entry points (UI routes and pages, the API routes or OpenAPI spec, every
CLI `--help`), `docker-compose`/Makefile/CI, the env vars and the tests. Write the **feature map**: each
feature or service, how to start it, how its user reaches it (page, endpoint, command), and what it needs.
- **Whole project or several parts:** show the map and a chapter outline (one line each), and wait for the
  user's go before recording.
- **One feature:** say the plan in three lines and go on.

## 3. Ask for the hands-on needs, once, in the chat
List everything only the user can give, in one checklist, before you try anything: API keys and secrets
(they go in a git-ignored file in the clone, never on screen), logins and accounts, paid services, a device or
a machine, an approval, real data. Wait for the answers. Never invent a secret; if something can't be
provided, say how the video will work around it (a local model, sample data, skipping that part on screen).
**A sign-in** (a web app, Slack): run `bash run.sh browser.py login <url> <secrets>/site.json --until
'<url regex once signed in>'`. It opens a browser window named "Chromium" (or "Google Chrome for Testing"),
with no keychain prompt; tell the user that name. They sign in, it saves the session (mode 600) and closes;
browser scenes then load it with `"storage_state"`. One sign-in serves every scene.

## 4. Pilot run: use it for real
Clone the repo into `work/` (never the user's working copy; mention their uncommitted changes and leave them
alone), start what the subject needs, and use it as the audience would: the UI as a user in a real browser
(`browser` scenes: the cursor, the typing and the clicks on screen), a service or API with real requests and
the proof of their effect (`api` scenes: the curl command, the response, then the row or log line it
changed), the CLI in a terminal. Write down the exact steps that show each feature well, with short output.

**Act as the viewer, who knows little.** They will repeat what they see, from the doc, with nothing but the
project:
- Type only **commands the viewer has**: the project's own (README, Makefile, package scripts, its CLIs) and
  standard tools you tell them to install. Never a helper script, alias, function or `PATH` entry written for
  the video; the engine refuses them. When the project has no command for a step, show the real long one, or
  say on screen that none exists (a finding): never a new one.
- Ask an agent, a form or a search the way a user would ask, in their words, not a prompt tuned for the
  model. If only a tuned prompt works, that is a finding.
- Show failures and retries as they happen; never hide them in a wrapper or a hidden step.
- Start each chapter from where the viewer is: which folder (the prompt shows it), which terminal, what is
  running. Starting a service or setting a variable they need happens on screen; hidden `before` and
  `setup` steps only reset state off camera.
- Say what is new: explain each new command, flag, variable and file in one sentence the first time.
- **Environment problems** (a wrong default path, a missing env var): fix them in the clone and show the fix
  in the video, because viewers will hit them too.
- **Real bugs:** in a pilot, they are the content. In a demo or tutorial, tell the user before recording and
  ask: show it, work around it, or fix it first.

## 5. Write the script, dry-run, record
Set up the video folder outside the repo (the user picks it; else `<parent-of-repo>/video/`):

```bash
bash SKILL/scripts/setup.sh            # tools, voice model (once), python env; says what to install
mkdir -p video/src && cp SKILL/scripts/{engine.py,browser.py,make_readme.py,make_doc.py,run.sh} video/src/
cp SKILL/scripts/script_template.py video/src/script.py
```

Shape the chapters with the type's recipe and follow its script rules in `SKILL/references/video-types.md`.
**Point where to look** in every scene: zoom on the field being used, highlight or arrow the button, a callout
for the key fact or warning, a ✓ when a step worked, numbered step badges and a section card between steps
(`script-format.md` lists them). `script.py` holds every word
and every action; `engine.py` turns it into video. Read `SKILL/references/script-format.md` for the scene
types (`browser`, `api`, `term`, `diagram`, `slide`, `card`) and the narration rules.

```bash
cd video/src
bash run.sh engine.py --dry            # runs every action for real, prints the output, makes no video
bash run.sh engine.py --only 03        # record one chapter, then look at frames before the rest
bash run.sh engine.py --detach         # record everything missing or changed in the background, then the video
bash run.sh engine.py --status         # running? which chapter? how did it end?
bash run.sh make_readme.py && bash run.sh make_doc.py   # README index, and the companion doc
```

Always dry-run first. The dry run runs each scene like the recording does (one terminal per scene, closed at
its end) and stops at the first command that fails; declare each long-running service the video starts in
`SERVICES` with a health check, so one that dies is caught at once. It ends with an estimate of the recording
time: **tell the user how long and how heavy** (services, a local model, a browser) before recording. Record
long videos with `--detach`: the recording survives the end of your session, keeps the computer awake, and
only one runs at a time; check it with `--status`, never with a shell loop. A recording also stops at the
first failed command, so it never records an hour of errors. Check a recorded chapter by reading frames
(`ffmpeg -v error -ss 20 -i chapters/03-*.mp4 -frames:v 1 build/check.png`). Chapters are cached by a hash of
their script, so re-runs rebuild only what changed, and a stopped recording resumes where it stopped.

## 6. Verify and hand over
`ffprobe -v error -show_chapters -show_streams -of compact video/<name>.mp4` must show 1920×1080 h264, aac, a
mov_text subtitle track and one marker per chapter; sample a few frames for overflow. Then give the user the
paths (the MP4, `chapters/`, the `.srt`, the companion doc `<name>.md` with its screenshots, the README), how to open it (QuickTime or VLC show chapters and
subtitles), what you found, and any service you left running with how to stop it.

## Output layout
```
video/
├── <name>.mp4            # all chapters, with chapter markers and a subtitle track
├── <name>.srt            # the narration as subtitles (also a transcript)
├── <name>.md, doc/       # the companion doc and its screenshots
├── chapters/NN-slug.mp4  # each chapter as a stand-alone clip
├── README.md             # chapter index with start times, how to re-record
├── src/                  # script.py (the words and actions) and the engine that records it
├── work/                 # throwaway clone(s): every action runs here
└── build/                # intermediate files
```

## Pitfalls already solved
- **Sandboxed shells:** vhs, Docker, uv caches and the voice often fail under a command sandbox ("Operation not
  permitted"); run them outside it. `open` is blocked too: give the user the command.
- **VHS:** 15 fps (50 drops frames), `Output` is a bare file name (the engine runs vhs in the folder), strings
  take no escapes (the engine types any quotes in parts), and `Wait` needs the prompt to end in `$`: a command
  whose last line ends in `$` or `>` ends the wait early, so add a `pause`.
- **A dry run really acts:** it types, clicks and saves. Reset the app's state in the chapter's `before`
  hook so the recording starts clean. A `before` hook that fails stops the build (`|| true` where it may).
- **A service started on screen** dies when its scene's terminal closes if it was started with a bare `&`.
  Start it the way a person leaves one running: `nohup <command> > <log> 2>&1 &` then `disown` (or the
  project's own way: `docker compose up -d`, a `make` target).
- **A failure shown on purpose** (a 422, a `grep` that finds nothing): mark it `{"cmd": …, "fails": True}`.
- **Pages that never go quiet** (chat apps, live dashboards): `"wait_until": "load"` on the scene.
- **Long-running scenes** (an agent, a pipeline): `"speedup": True` compresses the clip to the narration and
  stamps "sped up ×N"; say so in the narration.
- **Wait loops:** `pgrep -f` matches itself; wait on a PID or a file.
- **Before-hooks** that break things on purpose keep their undo in the same chapter, so rebuilding one chapter
  never leaves the system broken.

## Showing an AI agent at work
If the repo builds an agent, ask it the way its users do (its chat UI, its CLI, its Slack bot), with a real
question about a real, injected problem, and reset the fault in the same chapter. Show its tool calls with what
the project offers (a verbose flag, its logs, its UI); if it offers nothing, say so as a finding. Long runs go in
a `speedup` scene.
