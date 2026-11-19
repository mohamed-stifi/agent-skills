# Video types

Pick from the user's words; default **promo**. Each type is one main timeline plus optional cut-downs (`src/films.ts`).
Lengths are targets at 60 fps; stay within ±5 %.

| Type | When the user says | Main film | Default cuts | Story shape |
|---|---|---|---|---|
| **promo** (default) | "promo", "ad", "video for my product", nothing specific | ≤ 60 s (≈ 3480–3600 f) | 15 s + 6 s | hook → problem → turn → 3–4 chapters → trust → promise → CTA |
| **story** | "story", "use case", "customer case", "show one scenario" | 45–55 s | none | one real scenario end to end: the moment it breaks → the product acts → the human decides → the outcome with a number |
| **teaser** | "teaser", "launch", "coming soon", "announcement" | 15–25 s | 6 s | 3 beats: tension image → reveal (name + one line) → date/CTA; no features |
| **explainer** | "how it works", "explain", "walkthrough of the product" | 60–90 s | none | question → the mechanism in 3–5 steps (one diagram that grows) → why it is safe → CTA |
| **vertical** | "vertical", "9:16", "reel", "TikTok", "Shorts", "Stories" | same as the type asked, re-composed | — | same story; run `setup.sh --format 9:16 --slug <slug>-vertical`; design scenes for a tall frame (big type, one column), never letterbox a 16:9 film |
| **square** | "square", "1:1", "feed post" | same as asked | — | `--format 1:1`, as vertical |

Anything else the user asks for (a hiring video, an investor teaser, a feature drop, a webinar opener): pick the closest
shape above, keep the rules, and say in the final reply which shape you used.

## Cut-downs (from the main timeline, never re-animated)
- 15 s = hook (first ~5 s) + the promise scene (~6 s) + CTA (~4 s).
- 6 s = promise headline (~3 s) + CTA (~3 s).
- Define them in `src/films.ts` as `[fromFrame, lengthFrames]` parts; cut inside motion blur when you can, else put an
  `into` whoosh on the join (see `timing.joins()` in `source/audio/timing.py`).

## Film ids (= file names the viewer sees)
`promo-60s`, `promo-15s`, `promo-6s`, `story-50s`, `teaser-20s`, `explainer-80s`, use the real rounded length.
