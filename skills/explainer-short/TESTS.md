# Test tasks for `explainer-short`

Run each one in a **fresh agent session** (no prior context) to measure the skill, not the agent's memory.
Each covers one script format. Pass = all checks below are true when you watch the MP4.

| # | Prompt (give exactly this) | Format tested |
|---|---|---|
| 1 | "Make a short video: How does HTTPS protect my password on public Wi-Fi?" | A — how it works |
| 2 | "Explainer short, X vs Y: RAG vs fine-tuning — which one should you use? Brand: Mohamed AI." | B — X vs Y + brand |
| 3 | "i want a video system design: how whatsapp know to show the 2 blue ticks (sent, delivered, read) when my friend phone is off" | C — system design, messy input |

## Pass checklist (per video)

- [ ] MP4 1080×1920 exists, duration 95–120 s, `.srt`, `cover.jpg`, `upload.md` exist
- [ ] Opens with the question; a named person/“you” + concrete input within ~10 s
- [ ] One board for the whole video: no hard cuts, ≤ 3 full clears
- [ ] Something changes every ~3 s; elements appear on the word that names them
- [ ] Spotlight dimming used; at least one state change on the same object; at least one moving Chip/Packet
- [ ] Titles 1–4 words with an accent keyword; no word-by-word subtitles; captions ≤ 7 words
- [ ] Main panels fill the width; no text you must squint at; nothing overlapping
- [ ] Ends with a one-sentence mental model, CTA, blurred end card with the right brand
- [ ] Agent asked ≤ 1 question, used ≤ 2 check→fix rounds, ≤ 2 voice runs

## Results — v1 (2026-11-12, Claude Opus agents, before the v1.1 fixes)

| # | Result | Duration | Fix rounds | Notes |
|---|---|---|---|---|
| 1 | ✅ rendered | 108 s | 0 (agent could not run Chrome; checked + rendered by the orchestrator) | Strong style match (spotlight, stickers, stepper recap). Panels too small. |
| 2 | ✅ rendered | 116 s | 1 | X vs Y on one board, policy-change twist. Panels too small, lower half underused. |
| 3 | ✅ rendered | 115 s | 2 | Tick states on the same bubble, offline queue, scale stat. Small text; facts from memory. |

Fixed in v1.1 from these runs: "fill the width" rule + scale check, rendered-size table, cue lint (`cues.mjs`, runs
first in `check.sh`), extra check frames are added (not replacing), sandbox/port guidance + stop rule,
venv auto-repair in `setup.sh`, "short = format" rule, required `plan.md`, facts-to-verify in `upload.md`,
bigger default `Tag`.
