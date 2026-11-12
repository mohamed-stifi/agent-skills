# Script guide — how these videos talk

Measured on 23 reference Shorts (see `style-evidence/narration.md`): median 170 s, ~590 words, ~14 words per
sentence, 0 greetings, 23/23 follow ONE concrete scenario from start to end, analogies in only 6/23.
Tone: a calm senior engineer at a whiteboard. Literal step-by-step data flow, not metaphors.

## Length

| Mode | Duration | Words (at speed 1.18 ≈ 187 wpm) | Sections |
|---|---|---|---|
| **default** | 95–120 s | 300–370 | 7–9 |
| short | 55–70 s | 170–215 | 5–6 |
| full (reference length) | 160–175 s | 500–540 | 9–12 |

## 1. Pick the format (title formula)

| Format | Title | Use when |
|---|---|---|
| A. Interview — how it works | `Interview: How X Actually Works` / `How Does X <verb>?` | one mechanism (DNS, indexing, cookies, attention) |
| B. X vs Y | `X vs Y` / `X vs Y: Which Should You Use?` | two options for the same job |
| C. System design ladder | `System Design: How <famous product> <does Y>` | scale problems: problem → fix → new problem → fix |
| D. What's new | `What Is the New X?` / `Why <Company> Moved Away From X` | news, a new protocol/tool/feature |

Best-performing in the references: new/trending AI & web topics, then fundamentals people "use but can't explain".
Title names a familiar product or protocol and promises the hidden mechanism ("Actually", "Knows", "Detects"). ≤60 chars.

## 2. Beats (sections) — default format A

| # | id (suggested) | % of time | What happens |
|---|---|---|---|
| 1 | `hook` | 3 % | The question, ≤12 words. Or a news fact. Or "A lot of people think X…". No greeting. |
| 2 | `scenario` | 10 % | "Let's say <Name> …" + one concrete input + the desired outcome. End with the question restated in example terms: "So how does <system> know …?" |
| 3 | `naive` | 12 % | The obvious approach or common belief, and exactly why it fails (with one number). "You might think … That's correct, but …" |
| 4–6 | `step1`…`step3` | 45 % | The mechanism hop by hop ON the example: who sends what to whom. Name each term only after its need is shown: "This is called X." Max 4 new terms. |
| 7 | `twist` | 15 % | "But what if …?" — a second problem / scale-up of the same example ("now 10 million users") and its fix. |
| 8 | `recap` | 6 % | One-sentence mental model: "So remember: …" / "Easy way to remember: …" |
| 9 | `cta` | 2 % | "If this helped, follow for more." (one line) |

**Format B (X vs Y):** hook → shared scenario → `x` "Let's start with X" (same example) → `y` "Now let's see Y"
(same example) → `both` "If you notice, in both cases …" → `diff` "The biggest difference is …" → `tradeoff`
→ `recap` "Use X if …, use Y if …" → `cta`.

**Format C (ladder):** hook (scaled question) → user journey → `simple` design → `problem1` "This works, but …" →
`fix1` → `problem2` "But what if someone …?" → `fix2` (the clever trick) → `limit` → `recap` → `cta`.

**Short mode:** hook → scenario → 2–3 mechanism beats → recap → cta (drop naive/twist).

## 3. Sentence rules

1. ~10–16 words per sentence, never > 18. One idea per sentence.
2. Start ≥ 30 % of sentences with **So / But / Now / Then / Let's**. Other signposts: "Let's say", "Instead of",
   "That's why", "That's where X comes in", "If you notice", "Once …", "Imagine …", "Actually".
3. 3–5 rhetorical questions, each one opens a new beat ("So how does it know …?", "But what if …?").
4. Repeat the running example's name/value ≥ 6 times (default length). Never drift to "a user".
5. 4–8 round, concrete numbers (10 million rows, 20 GB, 1 second) and do one calculation aloud
   ("3 steps instead of 9", "so we only send the remaining 6 GB").
6. Components may "talk": "The resolver says: I don't know, but ask the .com servers."
7. At most one analogy, one clause long. No jokes, no hype ("insane", "game-changer"), no "in this video".
8. Mention the visuals at most twice ("like this"). The audio must make sense alone.
9. Plain words. Expand every acronym once with its purpose ("RPO — how much data you can afford to lose").

## 4. Running example (mandatory)

- A first name (Maya, Alan, Nina, Omar, Sara…) **or** "you", plus ONE concrete input that can be drawn:
  a message ("my payment failed twice"), an id (`session_id=abc123`), a value (20 GB file, 14 GB uploaded),
  a URL (`shop.example`), a row ("Nina, Sydney").
- Use fictional names and `.example` domains for anything personal. Real products/protocols are fine as subjects.
- Reuse it in every beat; for the twist, scale the SAME example up.

## 4b. Facts

- Prefer mechanisms over statistics. Use a number only if you are confident; round it and anchor it ("over 100 billion
  messages a day, as of 2020"). If the agent has web search, verify the 1–2 key numbers; otherwise list them in
  `upload.md` under "Facts to verify". Never invent product internals — say "for example" or "a typical design".

## 5. script.json rules (the voice pipeline depends on them)

- Each sentence ends with `.`, `!` or `?`; sentences are synthesized one by one (exact timing per sentence).
- Show-form in text, say-form in `pronounce`: `"429": "four twenty nine"`, `"API": "A P I"`, `"JSON": "Jason"`,
  `"SQL": "sequel"`, `"k8s": "kubernetes"`, `"abc123": "A B C one two three"`, `"/24": "slash twenty four"`.
  Keys match whole tokens (trailing punctuation is ignored). Write big numbers in words if no key fits ("ten million").
- Avoid symbols the voice can't read inside sentences: `→ / & % #`. Write "to", "and", "percent".
- Plan the visual cue words while writing: each beat should contain the exact words you will `cue()`
  (the name of each element at the moment it should appear).

## 6. Self-check before running the voice (all must be YES)

- [ ] Title follows a formula and is ≤ 60 chars.
- [ ] Sentence 1 is the question/fact (≤ 16 words); a named person or "you" + concrete input by sentence 3.
- [ ] The question is restated in example terms by ~15 % of the script.
- [ ] Each new term is named after its need is shown; ≤ 4 new terms.
- [ ] One misconception or naive approach is broken (not in short mode).
- [ ] One twist / scale-up at 65–80 % (not in short mode).
- [ ] Ends with a one-sentence mental model, then the CTA.
- [ ] Word count within the mode's range.
