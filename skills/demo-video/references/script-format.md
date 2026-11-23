# script.py format

`engine.py` imports `script.py` from the same folder. It needs `CHAPTERS` and `WORKDIRS`; everything
else is optional.

## Module settings

| Name | Required | Meaning |
|---|---|---|
| `CHAPTERS` | yes | list of chapter dicts, in order |
| `WORKDIRS` | yes | `{"main": "/abs/path/clone", "sim": ...}`; a segment's `cwd` names one (or is a path) |
| `ENV` | no | env vars exported in every terminal scene, before-hook and dry run |
| `TITLE`, `AUTHOR` | no | MP4 metadata; `TITLE` is also the README heading |
| `FOOTER` | no | small line at the bottom of title cards |
| `PROMPT` | no | the shell prompt text in terminal scenes (default `\\W`: the current folder's name) |
| `VIEWER_HAS` | no | file names the viewer made on screen earlier (e.g. `["fmt.sh"]`), so typing them is allowed |
| `OUTPUT_NAME` | no | base name of the final `.mp4` / `.srt` (default `walkthrough`) |
| `SPOKEN` | no | `{regex: replacement}` pronunciations, merged over the engine's built-in list |
| `README_NOTES` | no | markdown appended to README.md (requirements, what to start first) |

## Chapter

```python
{"num": "04", "slug": "ci-rules", "title": "The CI rules",
 "before": ["git checkout -q . && git clean -fdq", "docker compose up -d db"],   # optional
 "segments": [ ... ]}
```

- `num` is a two-digit string. Output goes to `chapters/04-ci-rules.mp4`, and `--only 04` selects it.
- `before` holds shell commands run (in `WORKDIRS["main"]`, with `ENV`) before recording or a dry run.
  Use it to reset state off camera (a clean database, a fault undone). What the viewer must do themselves
  (start a service, set a variable) belongs on screen, in a scene. They are skipped with `--reuse-terms`.
  Their output is hidden, so a failing hook only shows up as odd output in the scenes. Dry-run first.
- A chapter is rebuilt only when its dict or the voice settings (`VOICE_ENGINE`, `VOICE`, `SPEED`, `RATE`) change (a hash in `build/NN/meta.json`).
  Use `--force` to rebuild anyway, for example after the repo changed.

## Segments

Every segment has `type` and `say` (the narration). Its duration is `max(voice, picture)`, and the picture
holds its last frame until the voice ends.

### card: full-screen title

```python
card(kicker="REPO", title="A guided tour of REPO", subtitle="What it does ... `code` allowed", say="...")
```

### slide: title + bullets and/or boxes

```python
slide("The pipeline", "narration ...",
      bullets=["Top level with `code`", "  two leading spaces = sub-bullet"],
      boxes=[{"title": "Manifest", "body": ["`mcp/` `clis/`", "YAML in git"], "color": "blue"}, ...],
      rows=1,          # boxes laid out in N rows
      box_h=300,       # box height in px (body lines are ~44 px each, title takes 90)
      arrows=True,     # arrows between boxes in a row (False for "four kinds of X")
      note="Yellow call-out bar at the bottom",
      min=0)           # minimum seconds on screen
```

Layout limits at 1920×1080:
- Up to about 8 one-line bullets, or 5 boxes per row.
- Box body lines wrap inside the box. Long paths overflow, so split them across two body lines.
- Colours: `blue mauve peach green teal yellow red sky`.

### diagram: boxes that light up with the narration

```python
diagram("How a note is saved",
        "The page sends the note. The API checks it and stores it. Then the audit log records the change.",
        boxes=[{"title": "Page", "body": ["`index.html`"]},
               {"title": "API", "body": ["`POST /api/notes`"]},
               {"title": "Audit log", "body": ["`audit` table"]}],
        steps=[[0], [0, 1], [1, 2]])     # boxes lit during sentence 1, 2, 3 (default: box k in sentence k)
```

Same layout fields as `slide` (`rows`, `box_h`, `arrows`, `note`). Lit boxes are bold and coloured, the others
dimmed; an arrow lights when both its ends are lit. Each picture holds for exactly its sentence, because the
voice is made sentence by sentence. One sentence per step: write the narration to match the boxes.

### section: a short card between steps

```python
{"type": "section", "title": "Install the gateway", "icon": "⬇", "kicker": "Step 2", "color": "blue",
 "say": "Step two: install the gateway."}
```

A gradient (`blue`, `orange`, `green`, `purple`, `teal` or a hex colour) and one centred pill; at least 2.5 s.
Use it between steps or before a new part, not as a slide of text.

### concept: tiles for "what is X" and "A + B"

```python
{"type": "concept", "title": "Two pieces", "join": "+",
 "tiles": [{"icon": "⚙", "title": "Hidden setting", "sub": "inside the desktop app"},
           {"icon": "⚡", "title": "One free tool", "sub": "routes every request to a free model"}],
 "say": "Two pieces make it work: a hidden setting, plus one free tool."}
```

One to three tiles (icon, caps title, a short subtitle). Icons that render: ⚡ ⚙ ⚠ ✓ ★ { } ⬇ (and more in
Menlo / Apple Symbols / DejaVu Sans). Prefer this to a bullet slide when introducing parts.

### Numbered steps

`step="#Connect Claude"` on any segment shows a badge top right, numbered over the whole video:
`Step 3 of 5 · Connect Claude`. A `step` without `#` is shown as written.

### term: a real terminal scene, recorded by VHS

```python
term("Caption: the one-line point, `code` allowed",
     "Narration: what the viewer should look at.",
     ["plain command",                                  # typed, Enter, wait for prompt, 1.6 s pause
      {"cmd": "slow command | head -20", "pause": 4},   # longer pause to let viewers read
      {"sleep": 2},                                     # just wait
      {"clear": True}],                                 # clear screen off-camera
     step="step 1",          # pill in the top-right corner
     cwd="sim",              # a WORKDIRS key or an absolute path (default "main")
     env={"X": "1"},         # extra exports for this scene
     setup=["source .venv/bin/activate"],   # run hidden before the scene starts (only what the viewer did earlier)
     prompt="api",           # override the prompt text
     speedup=True)           # long-running scene: compress to ≈ narration length, badge "sped up ×N.N"
```

Terminal area: 1920×900 at font size 22, about 140 columns and 34 rows. Keep the output short: pipe
through `head`, `tail`, `jq '{only, the, fields}'`, `cut -c1-160`, and `grep -v` the noise. If output
scrolls off before the viewer can read it, split the scene or raise `pause`.

Quoting: any command works, whatever quotes it holds; the engine types it in parts VHS can quote.

**Only the viewer's commands.** Before a dry run or a recording, the engine checks every typed command (and
every file it reads, like `jq -f x.jq`): a program from the video folder (`src/`, `build/`, `work/bin/`), a file
added to the clone that git neither tracks nor ignores, or a function or alias from the scene's `setup` stops
the run with a list. Type the project's real command instead. A file the viewer made on screen earlier goes in
`VIEWER_HAS`.

Waiting: the engine waits until the last line ends in `$` or `>` (the prompt). A command that
prints such a line itself ends the wait early. Long commands are fine (timeout 600 s).

### browser: a real browser used like a person (Playwright)

```python
browser("Caption: the one-line point",
        "Narration: what the viewer should look at.",
        "http://127.0.0.1:8000/",                       # the page it opens first
        [{"type": "Ship the audit report", "into": "#text"},   # glide there, click, type key by key
         {"click": "text=Save"},                       # any Playwright selector: CSS, text=…, role=…
         {"expect": "Ship the audit report"},          # fails the dry run if the page never shows it
         {"highlight": "li", "seconds": 2}],           # frame an element so the viewer looks there
        step="step 2")
```

| Step | Does |
|---|---|
| `{"goto": url}` | open another page and wait for it to settle |
| `{"click": sel}` | glide the cursor there, ripple, click |
| `{"hover": sel}` | glide the cursor there (menus, tooltips) |
| `{"type": "text", "into": sel}` | click the field, clear it, type key by key (`"delay"`: ms per key, default 55) |
| `{"press": "Enter"}` | press a key or chord (`"Meta+K"`) |
| `{"scroll": sel}` / `{"scroll": 600}` | bring an element into view / scroll by pixels |
| `{"wait": sel}` / `{"wait": {"text": "Done"}}` / `{"wait": 2}` | until visible / seconds |
| `{"highlight": sel, "seconds": 2}` | an orange frame around it, the rest dimmed |
| `{"expect": "text"}` | the page must show this text (a check, also in the dry run) |
| `{"pause": 1.5}` | hold still |

**Point where to look** (drawn only when recording; the dry run checks their targets):

| Step | Does |
|---|---|
| `{"zoom": sel, "scale": 2}` / `{"zoom": False}` | the page scales up around the target (sharp: the browser redraws it), then back; clicks still land |
| `{"callout": "2-5 words", "at": sel, "icon": "⚡", "tone": "info", "seconds": 3}` | a pill next to the target (no `at`: at the top); tones `info` (cyan), `warn` (amber), `ok` (green) |
| `{"arrow": sel, "from": "left", "seconds": 2}` | a lavender arrow pointing at the target from `left`, `right`, `top` or `bottom` |
| `{"underline": sel, "seconds": 2}` | a lavender bar drawn under the target |
| `{"blur": sel}` | blur a secret for the rest of the scene (also in the dry run) |

`highlight` draws a glowing frame with corner brackets and dims the rest; a passing `expect` shows a green
✓ pill with the text it found, the on-screen proof that the step worked. Typical order for one action:
zoom in → highlight or arrow → act (type, click) → expect (✓) → zoom out.

Every step waits 0.6 s after it (`"pause": N` on the step changes that). The page is 1920×900, like a
terminal scene. The engine trims the blank start and holds the last frame until the narration ends.

**A dry run is real.** `--dry` runs every step in a headless browser, so a note it saves is saved. Reset the
app's state in the chapter's `before` hook (restart it, reset its database), so the recording starts clean.
A failing step stops the scene and prints its number, the step, the page URL and the reason.

### api: real HTTP calls, then the proof of their effect

```python
api("Create a note, then see it in the audit log",
    "We post a note. The service answers 201 with its id. Then the audit log shows the new event.",
    "http://127.0.0.1:8000",                                     # the base URL of each call
    [{"method": "POST", "path": "/api/notes", "json": {"text": "Ship the audit report"}},
     {"method": "POST", "path": "/api/notes", "json": {"text": ""}, "status": True},   # curl -si: the 422
     {"method": "GET", "path": "/api/notes", "show": "map(.text)"}],          # | jq 'map(.text)'
    then=["curl -s http://127.0.0.1:8000/api/audit | jq '.[-1]'",  # effect checks: any shell command,
          "sqlite3 work/app/app.db 'select count(*) from notes'"],  # e.g. the database or a log
    step="step 3")
```

Each call is typed as the curl line a viewer would use, with the full URL:
`curl -s -X POST http://127.0.0.1:8000/api/notes -H 'Content-Type: application/json' -d '{"text": "…"}' | jq`.
The response is pretty and coloured by `jq`; `"show"` gives jq a filter (`| jq 'map(.text)'`). `"status": True`
types `curl -si` instead, whose first line is the HTTP status (no jq): use it where the status is the point,
such as a 422. `"headers"` adds `-H` lines and `"pause"` sets the reading time (default 2.5 s). `then` lists the
**effect checks**: show what the calls changed (a row, a log line, a file, another endpoint) instead of saying
it. They are typed as written, so they too must be commands the viewer has. The doc shows the same lines.

## Narration style

- The voice is Kokoro (`VOICE=af_heart`, `SPEED=1.0`; other voices: `am_michael`, `bf_emma`, …), about 150–170
  words per minute. `VOICE_ENGINE=say` uses macOS `say` instead. Most segments are 2–5 sentences.
- Open a chapter with *why* it exists, then *what to look at*, then *what it means*.
- Name what is on screen: "Look at the skills: zero." If a command's output changes, update the words.
- Be honest about failures: "This fails today, and here is why." (In a pilot they are the point; in a demo,
  the user decides first.)
- Match the audience: plain words for end users, internals for developers.
- Spell acronyms the voice mangles, either in the text ("C L I") or through `SPOKEN`.

## The findings chapter

The last chapter collects everything that testing surfaced, numbered, each with one line of "why it
matters". Typical categories:
- CI is red on `main`, and which rules fail
- silent failures (a feature drops things without a warning)
- crashes or tracebacks where a clean error belongs
- hard-coded personal paths, or wrong defaults for the documented layout
- missing configuration that other teams will hit

Then a "your next steps" slide.
