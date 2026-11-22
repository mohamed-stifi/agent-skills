# Video types: the chapter shape of each

Pick the type from the request (SKILL.md, step 1), then shape the chapters here. Length follows the content:
cut what doesn't help this audience, never pad to a length. Each chapter is one idea and also works as a
stand-alone clip, so open each with one sentence of context.

Scenes: `browser` for anything with a UI, `api` for services and endpoints, `term` for CLIs, logs and
databases, `diagram` for how parts fit, `slide`/`card` for words. Prefer showing over telling: a slide only
where nothing can be shown.

## Feature demo
For a PR, a release note, docs, or "show me X". One feature or service, end to end, on real data.

| # | Chapter | Shows |
|---|---|---|
| 00 | What and why | a card: the feature in one sentence and who it is for; the problem it solves (a slide, or the "before" on screen) |
| 01 | It working | the feature used for real, start to finish, as its user would (browser/api/term); the result highlighted |
| 02 | Variations | options, edge cases, the error a user will meet and its message (only the ones that matter) |
| 03 | Where it lives | optional, for developers: the entry point and files, one diagram of the flow |

Usually 2–10 minutes. No findings chapter unless the user asked; a bug found during the pilot is raised
with the user before recording.

## Tutorial
For someone who will follow along: every step on screen, in order, nothing assumed.

| # | Chapter | Shows |
|---|---|---|
| 00 | What you will build or do | a card, then the end result first (a few seconds of it) |
| 01 | Prerequisites | what to install and have (accounts, keys, versions), and how to check each (`--version`) |
| 02 | Install and configure | every command and setting, from a fresh clone; the env file without secret values |
| 03… | One task per chapter | the tasks in the order a newcomer needs them, each ending with how to see it worked |
| N | Troubleshooting | the errors the pilot run hit and how to fix each, then where to go next |

Narrate actions as instructions ("Now type…", "Click Save"), slower than a demo: `pause` longer, one action
per sentence. The companion doc matters most here: readers copy the commands from it.

## How it works (explainer)
For understanding: the parts, how they connect, what happens to one request or record as it flows through.

| # | Chapter | Shows |
|---|---|---|
| 00 | The question | a card: what we will understand, in plain words |
| 01 | The big picture | a `diagram` of the parts, lit one by one as each is named |
| 02… | One part per chapter | the part's diagram box lit, then a live demo of just that part (its API, its table, its log) |
| N | One thing end to end | a single request or record followed through every part, the diagram lit at each hop |

Alternate diagram → demo → diagram, so every box on the picture is seen working. Depth follows the audience:
inputs and outputs for users, data structures and calls for developers.

## Pilot (test record)
For "is it working?", QA, or proof before a release: what was tested, how, and what happened.

| # | Chapter | Shows |
|---|---|---|
| 00 | Scope | what is under test, the environment, what was not tested and why |
| 01… | One feature per chapter | each check run for real: the action, the expected result, the actual result |
| N-1 | Failures | each failure reproduced on screen, with whether it is a bug or the environment |
| N | Verdict | a slide: works / broken / untested, numbered, each with one line of why it matters |

Show failures plainly; they are the point. Keep the commands that prove each result on screen.

## Project guide
For "the whole project" or onboarding a team to something an agent built. Show the feature map and the
outline to the user first (SKILL.md, step 2) and wait for their go.

| # | Chapter | Shows |
|---|---|---|
| 00 | Welcome | what the project is for, who uses it, what the video covers |
| 01 | The big picture | a `diagram` of the parts (UI, API, workers, database, models), lit one by one |
| 02 | Run it | setup from a fresh clone to everything running, the way a teammate will do it |
| 03… | One feature per chapter | each feature as a short feature demo (see above), in the order users meet them |
| N-1 | Under the hood | optional: the parts developers will change, one explainer each |
| N | What we found, next steps | the pilot's findings (works / broken / missing), then where to start |

Can run to hours for a big project: that is fine, because each chapter is its own clip and the companion
doc has an index with start times.
