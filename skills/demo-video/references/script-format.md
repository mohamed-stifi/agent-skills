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
| `PROMPT` | no | the shell prompt text in terminal scenes (default `repo`) |
| `OUTPUT_NAME` | no | base name of the final `.mp4` / `.srt` (default `walkthrough`) |
| `SPOKEN` | no | `{regex: replacement}` pronunciations, merged over the engine's built-in list |
| `README_NOTES` | no | markdown appended to README.md (requirements, helper scripts) |

## Chapter

```python
{"num": "04", "slug": "ci-rules", "title": "The CI rules",
 "before": ["git checkout -q . && git clean -fdq", "docker compose up -d db"],   # optional
 "segments": [ ... ]}
```

- `num` is a two-digit string. Output goes to `chapters/04-ci-rules.mp4`, and `--only 04` selects it.
- `before` holds shell commands run (in `WORKDIRS["main"]`, with `ENV`) before recording or a dry run.
  Use it to reset state, start containers or trigger a pipeline. They are skipped with `--reuse-terms`.
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
     setup=["source .venv/bin/activate"],   # run hidden before the scene starts
     prompt="api",           # override the prompt text
     speedup=True)           # long-running scene: compress to ≈ narration length, badge "sped up ×N.N"
```

Terminal area: 1920×900 at font size 22, about 140 columns and 34 rows. Keep the output short: pipe
through `head`, `tail`, `jq '{only, the, fields}'`, `cut -c1-160`, and `grep -v` the noise. If output
scrolls off before the viewer can read it, split the scene or raise `pause`.

Quoting: a command may contain any two of `"`, `'` and `` ` `` but not all three, because VHS strings
have no escapes. Move such a command into a small script file.

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

Every step waits 0.6 s after it (`"pause": N` on the step changes that). The page is 1920×900, like a
terminal scene. The engine trims the blank start and holds the last frame until the narration ends.

**A dry run is real.** `--dry` runs every step in a headless browser, so a note it saves is saved. Reset the
app's state in the chapter's `before` hook (restart it, reset its database), so the recording starts clean.
A failing step stops the scene and prints its number, the step, the page URL and the reason.

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
