"""The video: chapters -> segments. Edit the words or the commands here, then
`bash run.sh engine.py --dry --only NN` (check the actions) and `bash run.sh engine.py --only NN` (record).

Every terminal command is real and runs in a throwaway clone of the repo (work/), never in a working copy.
See <skill>/references/script-format.md for every field.
"""

V = "/ABS/PATH/TO/video"                               # the video folder (absolute: VHS cd's into WORKDIRS)
WORKDIRS = {"main": f"{V}/work/REPO"}                  # segment "cwd" picks one of these (default "main")
ENV = {}                                               # exported in every terminal scene and before-hook

TITLE = "REPO: a guided tour"                          # MP4 title metadata + README heading
FOOTER = "REPO  ·  a guided tour for the team"         # bottom line of title cards
AUTHOR = "the team"
PROMPT = "REPO"                                        # shell prompt shown in terminal scenes
OUTPUT_NAME = "REPO-walkthrough"                       # -> REPO-walkthrough.mp4 / .srt
SPOKEN = {}                                            # extra pronunciations, e.g. {r"\bk8s\b": "kubernetes"}
README_NOTES = ""                                      # extra lines for README.md (requirements, helpers)

CLEAN = "git checkout -q . && git clean -fdq"          # handy before-hook: reset the clone


def term(caption, say, cmds, **kw):
    return {"type": "term", "caption": caption, "say": say, "cmds": cmds, **kw}


def browser(caption, say, url, steps, **kw):
    """A real browser used like a person; steps are listed in references/script-format.md."""
    return {"type": "browser", "caption": caption, "say": say, "url": url, "steps": steps, **kw}


def api(caption, say, base, calls, then=(), **kw):
    """Real HTTP calls shown as request -> status -> response, then `then`: commands that show the effect."""
    return {"type": "api", "caption": caption, "say": say, "base": base, "calls": calls, "then": list(then), **kw}


def diagram(title, say, boxes, steps=None, **kw):
    """Boxes and arrows that light up as the narration names them: steps[k] = box indices lit during sentence k
    (default: sentence k lights box k)."""
    return {"type": "diagram", "title": title, "say": say, "boxes": boxes, "steps": steps, **kw}


def section(title, say, icon="", **kw):
    """A short card between steps: gradient + one pill. kw: kicker, color."""
    return {"type": "section", "title": title, "say": say, "icon": icon, **kw}


def concept(say, tiles, title="", join="", **kw):
    """1-3 tiles {"icon", "title", "sub"} for "what is X" / "A + B" moments."""
    return {"type": "concept", "say": say, "tiles": tiles, "title": title, "join": join, **kw}


def slide(title, say, **kw):
    return {"type": "slide", "title": title, "say": say, **kw}


def card(kicker, title, subtitle, say):
    return {"type": "card", "kicker": kicker, "title": title, "subtitle": subtitle, "say": say}


CHAPTERS = [
{"num": "00", "slug": "intro", "title": "Welcome", "segments": [
    card("REPO", "A guided tour of REPO",
         "What it does, how each part works, and how to test every function yourself.",
         "Welcome. This video is a guided tour of the REPO repository, for everyone on the team. "
         "Every command you will see is run for real, including the ones that fail today."),
    slide("What you will see",
          "Here is the plan. First the big picture, then each part of the pipeline, then what we found.",
          bullets=["The big picture", "Setup and the CLI", "…one bullet per chapter…", "What we found"],
          note="Each chapter is also a separate file in chapters/."),
]},
{"num": "01", "slug": "big-picture", "title": "The big picture", "segments": [
    slide("The pipeline",
          "This is the pipeline, from left to right. Every chapter is one box of it.",
          boxes=[{"title": "Input", "body": ["`src/`", "what goes in"]},
                 {"title": "Check", "body": ["`tool validate`"]},
                 {"title": "Output", "body": ["what comes out"]}],
          box_h=300, note="Keep this picture in mind."),
    term("The repo layout: each folder is one part of the pipeline",
         "Let's look at the repo itself. Each top level folder maps to one part of the pipeline.",
         ["ls", {"cmd": "tree -L 2 -d -I '__pycache__|node_modules|.venv'", "pause": 3}],
         step="repo tour"),
]},
{"num": "02", "slug": "setup", "title": "Setup", "before": [CLEAN], "segments": [
    term("Install, then run the fast tests",
         "Setup is one command. Then the fast tests, which need nothing else running.",
         ["make install 2>&1 | tail -3", {"cmd": "make test 2>&1 | tail -5", "pause": 4}], step="step 1"),
]},
# ... one chapter per pipeline stage, a live/integration chapter, contracts, then:
{"num": "09", "slug": "findings", "title": "Findings and next steps", "segments": [
    slide("What we found while testing",
          "While testing every function for this video, we found these issues. ...",
          bullets=["1. `main` is red: ...", "  why it matters / how to reproduce", "2. ..."]),
    slide("Your next steps",
          "To get started yourself: ...",
          bullets=["Run the fast tests", "Read `docs/`", "Pick a finding and fix it"]),
]},
]
