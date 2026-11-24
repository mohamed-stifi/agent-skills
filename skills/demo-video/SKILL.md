---
name: demo-video
description: Make videos that show a repo really being used and explain it, made to order - a demo of one feature or service, a step-by-step tutorial, a how-it-works explainer with live demos, a pilot (test record), or a guide to the whole project - for the audience the user names, plus a written doc. The agent first uses the thing for real, as its user or developer would, then records it with a local neural voice, captions and chapters. Use when the user asks to record, film or "make a video" of a repo, a feature or a service; for a demo, tutorial, walkthrough, onboarding, pilot or "show me how to use / how it works" video; or to understand and explain a project an agent built.
compatibility: macOS or Linux with ffmpeg/ffprobe, uv, vhs, jq, git; Kokoro voice files (~340 MB, fetched once by scripts/setup.sh). Docker or other services only if the repo needs them.
metadata:
  version: "4.3.0"
  author: mohamed-stifi
---

# Demo video

The user has a repo (built by an agent, open source, or from their team) and wants to *understand and show*
it: how to run it, how to use each feature, how it works. You make the video an engineer would record after
building the thing: you use it for real first, then show it step by step, worded for whoever will watch.
`SKILL` = this folder; `VD` = `<repo>/.video_demo_dir`, where everything you make and keep lives.

## 0. Start from what was already done
```bash
python3 SKILL/scripts/vdir.py init <repo>     # creates VD once (git ignores it through its own .gitignore)
```
Then **read `VD/INDEX.md`** before anything else: the videos already made (which commit each shows, their
chapters), the features already mapped (`VD/features/`), notes and findings, saved sign-ins, and what was left
outside on purpose. Reuse them: a mapped feature needs only a check that it still works; a request close to an
existing video starts from that video's script (a new version, below). If `init` warns about `.dockerignore`,
pass the line it gives to the user (a Docker build of the repo would send the folder). An older demo-video
folder: `vdir.py init <repo> --import <old folder>` brings it in as `videos/<slug>/v1`.

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
Save it as one file per feature, `VD/features/<feature>.md` (first line: a one-line summary; then how to start
it, reach it, what it needs, its source folders, and the commit you checked it at), so the next run reuses it.
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

**Outside services** (Slack, a cloud console, an OAuth app, a webhook, a model provider): a new viewer has to
set them up too, so each one gets its own **setup chapter**, recorded before the chapters that use it.
- **Steps the agent can do alone** happen on screen, as the viewer would do them. Examples: creating the app
  from the repo's manifest, choosing scopes, installing it, inviting the bot to a channel. Values the viewer
  must copy (tokens, IDs) go into the git-ignored secrets file and are named on screen, never shown.
- **Steps only the user can do** (sign in, a confirmation code, a payment, an admin approval) are done
  **together**. Say in the chat exactly what they will do and in which window, then wait. The sign-in itself
  uses `browser.py login` above, which is not recorded, so the user's email and codes never appear. At that
  point the chapter shows one line ("Sign in to Slack with your own account"), then continues from the
  signed-in page.
- The doc gets the same chapter as a written step list, so a reader can set the service up without the video.

## 4. Pilot run: use it for real
First, before starting anything: `python3 SKILL/scripts/ledger.py snapshot <repo>`. It records what already
runs (the user's own stacks, running or stopped), so the cleanup at the end can put it back exactly as found.
A clone's Docker Compose project gets the name `dv-<clone>` in every scene and hook, so it can never take over
the user's own project of the same name; when you start a clone's stack by hand, pass the same name
(`COMPOSE_PROJECT_NAME=dv-<clone>`). A project with a checkpoint (see `INDEX.md`) is restored first, instead
of rebuilt: `python3 SKILL/scripts/ledger.py restore <repo> dv-<clone>`, then start it.

Clone the repo into `VD/work/<name>` (never the user's working copy; mention their uncommitted changes and
leave them alone; a clone already there is refreshed with `git fetch` and `git checkout`, not cloned again), start what the subject needs, and use it as the audience would: the UI as a user in a real browser
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
Each video is `VD/videos/<slug>/vN/`; a re-record is a new version, so nothing recorded is ever deleted:

```bash
bash SKILL/scripts/setup.sh                         # tools, voice model (once), python env; says what to install
python3 SKILL/scripts/vdir.py video <repo> <slug>   # prints VD/videos/<slug>/vN: src/ holds the engine and a
                                                    # script.py (the last version's, or the template)
```
Keep tokens and saved sign-ins in `VD/secrets/` (mode 700), never in `src/`. Set `VIDEO_TYPE` in script.py
(demo, tutorial, explainer, pilot, guide) for the index.

Shape the chapters with the type's recipe and follow its script rules in `SKILL/references/video-types.md`.
**Point where to look** in every scene: zoom on the field being used, highlight or arrow the button, a callout
for the key fact or warning, a ✓ when a step worked, numbered step badges and a section card between steps
(`script-format.md` lists them). `script.py` holds every word
and every action; `engine.py` turns it into video. Read `SKILL/references/script-format.md` for the scene
types (`browser`, `api`, `term`, `diagram`, `slide`, `card`) and the narration rules.

```bash
cd VD/videos/<slug>/vN/src
bash run.sh engine.py --plan           # per chapter: reuse, re-voice, or record again, and why
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
(`ffmpeg -v error -ss 20 -i chapters/03-*.mp4 -frames:v 1 build/check.png`). A stopped recording resumes where it stopped.

**Reuse.** Every scene's live recording (a *capture*) is kept in `VD/clips/`, under a key made from what shapes
its picture: its commands or browser steps, the code its chapter `covers` (committed, uncommitted and untracked
files), any `inputs` (git-ignored settings, `cmd:` outputs), the capture tools, and the scene before it. So:
- a narration, numbering or voice change records nothing live; the chapter is only re-voiced and re-framed;
- a change in covered code records that chapter again, and the chapters after it up to the next `fresh` one
  (whose `before` hook resets the state); give each chapter a narrow `covers` and mark `fresh` the ones that
  start from scratch;
- a new video that reuses chapters of others (feature A + B) copies those chapters (same commands, same clone,
  each run starting at a `fresh` chapter) and records only the new ones.
Run `--plan` first and tell the user what will be recorded again and why. A recording whose screen changed while
its words did not is flagged "CHECK NARRATION": read the new frames and fix the words. A chapter recorded again
after reused ones runs without their effects: restore the checkpoint (`ledger.py restore`) or start it fresh.
`engine.py --gc` removes kept recordings no version uses any more.

## 6. Verify and hand over
`ffprobe -v error -show_chapters -show_streams -of compact <name>.mp4` must show 1920×1080 h264, aac, a
mov_text subtitle track and one marker per chapter; sample a few frames for overflow. Then give the user the
paths (the MP4, `chapters/`, the `.srt`, the companion doc `<name>.md` with its screenshots, the README), how to open it (QuickTime or VLC show chapters and
subtitles), and what you found. A full build registers the
version in `VD/INDEX.md` by itself; add what the next run must know with `vdir.py note <repo> "…"` (findings,
next steps) and `vdir.py leftover <repo> "…"` (an account or app you created outside, such as a Slack app).

**Then clean up**, so nothing made for the video keeps running:
```bash
python3 SKILL/scripts/ledger.py cleanup <repo> --dry   # what it would do: read it
python3 SKILL/scripts/ledger.py cleanup <repo>         # checkpoint, remove, put back
```
It saves the data of the video's own containers (`dv-*` projects, or a compose folder inside `VD`) as files in
`VD/state/` (up to `--limit-gb`, default 2), then removes those containers, networks and volumes, and stops the
processes started in `VD` since the snapshot. What it found (the user's stacks in a `WORKDIRS` folder outside
`VD`) goes back exactly as found: stopped again, extra containers removed, volumes kept. Anything else is
never touched, only listed. If the dry run lists a process or container you are not sure the video started,
ask the user before the real run. `INDEX.md` then shows "Running now: Nothing", the checkpoints and the
last cleanup; tell the user, with any leftover outside (an account, an app).

## Output layout
```
<repo>/.video_demo_dir/           # git-ignored by its own .gitignore ("*"); the repo's files are untouched
├── INDEX.md                      # read first: videos, features, notes, sign-ins, leftovers (generated)
├── state.json                    # the same, for scripts
├── features/<feature>.md         # the feature map, one file per feature
├── videos/<slug>/vN/             # one folder per version of a video
│   ├── <name>.mp4, <name>.srt    # the video (chapter markers, subtitle track) and its subtitles
│   ├── <name>.md, doc/           # the companion doc and its screenshots
│   ├── chapters/NN-slug.mp4      # each chapter as a stand-alone clip
│   ├── README.md                 # chapter index with start times
│   ├── src/                      # script.py (the words and actions) and the engine that records it
│   └── build/                    # intermediate files
├── work/<name>/                  # the clones: every action runs here; kept and refreshed
├── secrets/                      # tokens and saved sign-ins (mode 700)
├── clips/<key>/                  # kept recordings (captures), reused across chapters, versions and videos
├── state/<project>/              # checkpoints: the data of the video's own containers, as files
├── logs/, run/                   # recording logs; the lock and pid files
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
