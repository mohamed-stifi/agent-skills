# Roles: who does what (delegate everything heavy)

The **orchestrator** is the agent the user talks to, often the most expensive model. It plans, briefs, reads short
reports, decides and talks to the user. It does **not** read the sources, write scenes, or loop on renders. Every heavy
step goes to a subagent on a **cheaper model that is good enough** for that job:

| Tier | Use for | Example models (pick what your agent offers) |
|---|---|---|
| **mid** | research, story writing, scene building, visual review, audio script | Sonnet-class |
| **small** | running scripts and reporting results (setup, renders, captions, checks, delivery) | Haiku-class |

- Can choose a model per subagent → use the tier above.
- Subagents but no model choice → still delegate (the orchestrator's context stays small, so each call costs less).
- No subagents at all → the orchestrator does the role itself, with the same brief as its checklist.

## The contract between agents: files, not transcripts
Every role writes its result into the workspace and a **report of ≤ 40 lines** in `WS/reports/<role>.md`:
what was done, the decisions taken, the numbers asked for, what is not verified, and open questions.
The orchestrator reads **only the reports** (plus the few files named in "Orchestrator checks" below), never the
subagents' full output. Every subagent brief includes:

```
WORKSPACE: <WS>. If your file tools cannot reach it, author files in a scratch folder you can write to and copy them
with the shell; copy images back to the scratch folder to view them.
Write your report (≤ 40 lines) to <WS>/reports/<role>.md and end your answer with its path.
Bounded work: <the max rounds for this role>. When a limit is hit, stop and report what remains.
```

Run subagents in the **foreground** (several in one message still run in parallel). Background subagents can lose their
shell in some hosts.

## R0 · Operator (small): setup, renders, captions, checks, delivery
Brief: "Run exactly these commands from <the user's working directory>, in order. Report the last lines of each:
`bash SKILL/scripts/<script> …`. Do not edit any file. If a command fails, run it once more; if it fails again, stop
and report the error text."
Orchestrator checks: the success line of each script (`READY`, `ok …`, `CHECK OK`, `DELIVERED`).

## R1 · Researcher (mid): sources → `brief.md` + brand tokens
Brief: "Read <sources: URL(s), repo path, documents>. Fill <WS>/brief.md using the template already in it and the
rules in SKILL/references/story-and-script.md (Facts discipline) and SKILL/references/brand.md. Facts bank: at least 8
facts, each with its exact value and the source you read it in; no facts from memory. Apply the brand to
<WS>/source/src/kit/tokens.ts (+ fonts.ts and package.json if fonts change), or keep the house style and say why.
Max 30 minutes of reading."
Report: the one-sentence product, the audience, the 3 strongest facts, the bookend idea, brand decision.
Orchestrator checks: read `brief.md`'s top three sections and the facts table (not the sources).
Accept, or send one revision request ("missing: …, unsupported: F4, F7").

## R2 · Story writer (mid): `brief.md` → `STORYBOARD.md`, `src/timeline.ts`, `src/films.ts`
Brief: "Write the <type> film for <product> from <WS>/brief.md. Read SKILL/references/video-types.md,
story-and-script.md, storyboard-rules.md and, once, SKILL/references/examples/nemo-storyboard.md. Fill
<WS>/STORYBOARD.md (structure table with owner groups A/B/C, the rules block unchanged, the facts used, one brief per
scene with frame numbers, the decisive snap, the headline, the exit and the cut colour). Set SCENES in
source/src/timeline.ts and the deliverables in source/src/films.ts. Also draft the voice-over lines with start times
in the storyboard (a 'Voice' line per scene)."
Report: the one sentence, the structure table, total frames, the hook and the promise in one line each.
Orchestrator checks: the report only. Judge: does the hook show the buyer's own pain? Does the promise mirror the
hook? One proof moment per chapter? Accept, or one revision.

## R3 · Scene builders (mid ×3, parallel): `STORYBOARD.md` → `src/scenes/*.tsx`
Brief: `SKILL/references/scene-brief.md`, one per group A/B/C, all in one message.
Orchestrator checks: each report lists its scenes, the frame numbers of snaps/stamps/counts/whips/exits, deviations.

## R4 · Reviewer (mid): assemble, inspect, fix
Brief: "Run `bash SKILL/scripts/render.sh <WS> all`. Inspect every source/stills/<film>-sheet.png and full frames of
each decisive moment (`npx remotion still …`). Apply SKILL/references/qa.md (picture). Fix problems directly in the
scene files (smallest change that works), re-render the scene, then the films. Max 2 fix rounds."
Report: issues found → fixed / left, with the scene and frame.
Orchestrator checks: the report; optionally open ONE sheet per film for a sanity look.

## R5 · Audio producer (mid): `films.py`, voice, music, sound, pronunciation
Brief: "Write <WS>/source/audio/films.py following SKILL/references/audio.md and the complete example
SKILL/references/examples/nemo-films.py: voice lines from STORYBOARD.md's 'Voice' lines, timed to the beats; the cue
sheet from the frame numbers in <WS>/reports/scenes-*.md and reviewer.md; the music map; cut-downs via remap().
Run `bash SKILL/scripts/audio.sh <WS>` then `bash SKILL/scripts/check.sh <WS>`. Fix every mis-heard word with a `say`
respelling or a rephrase. Max 2 pronunciation rounds."
Report: the final script (time + line), mis-heard words and their fixes, loudness, CHECK result.
Orchestrator checks: the script lines (they are the words the customer hears) and `CHECK OK`.

## Orchestrator's own work (keep it to this)
1. Resolve the request into settings (defaults table in SKILL.md); never ask about defaults.
2. Write each brief (fill the templates above; ≤ 30 lines each) and launch the roles in order.
3. Read reports, accept or send one revision per role (max one, then accept with notes).
4. Map user feedback to roles (step 10) and re-launch only those.
5. Write the final reply.

## Parallelism
- R0 setup ∥ nothing (needed first) → R1 → R2 → R3 (×3 parallel) → R4 → R5 → R0 captions + check + deliver.
- During a feedback round, independent fixes (e.g. a scene fix and a voice-line fix) run in parallel.
