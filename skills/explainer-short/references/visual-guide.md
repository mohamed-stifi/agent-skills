# Visual guide — how these videos look and move

Measured on 23 reference Shorts (see `style-evidence/visuals.md`): **0 hard cuts in 23/23**, one dark board
built up piece by piece, something changes every **1.5–3 s**, focus shown by **dimming the rest to ~30 %**,
**no word-by-word subtitles in 23/23**, 3–4 accent colors per video, each bound to one thing.

## The 16 rules

1. **One board, no cuts.** Elements persist, get re-labelled, re-highlighted, moved. At most 3 full clears per video
   (usually at a format change, e.g. X → Y → trade-off). Anchors (the user, the server) survive clears when they can.
2. **Build top → bottom as a data flow** (client → service → storage) or side by side for comparisons.
3. **Fill the width.** Main panels are full width (x 60, w 960) or half width (w 465) — never a small card floating in
   the middle (references: panels span 92–94 % of the width). Panel height ≥ 160; labels inside ≥ 30 px.
   Content lives in **y 280–1480**, x 60–1020. Title slot y≈150. Bottom ~22 % stays empty except one caption,
   a stepper or a big stat. Leave ~45 % of the board black: 2–5 panels on screen, sparse inside.
4. **Stage title**: 1–4 words, top slot, one keyword in its accent: `<Title>Where **QUERY** helps</Title>`.
   ~4 titles per video; swap them at section starts (cross-fade). Some stages need no title.
5. **Accents**: pick 3–4. Bind each to ONE entity for the whole video (X = cyan, Y = purple, model = pink).
   amber = the current item / the answer · red = failure/attack · green = success/ok.
6. **Every element appears on the word that names it** (`cue`). A new element, highlight or move every 1.5–3 s.
7. **Focus = dim the rest** (`<Canvas focus>` plan, ids on `<El>`) + optionally a `Focus` dashed box or `active`.
   Never leave the whole board at full brightness while the voice talks about one part.
8. **Change state on the same object**, don't replace it: `<Panel state="error" status="crashed">`, ✓/✗, a bar fills,
   a token disappears, a lock opens (icon `lock`→`unlock`).
9. **Data moves.** Requests, tokens, ids travel as `Chip`s along `Arrow` paths (`Packet`), labelled with the real
   payload (`GET /weather`, `session_id=abc123`, `create_ticket`).
10. **Code/config** in a `Code` window, typed in, with the ONE discussed substring highlighted (`marks`).
11. **Scale** = `IconGrid` of ≥ 20 tiny icons or a `BigStat`. Never just say "millions".
12. **Steps/hops** = numbered `Badge`s on the path, or a `Stepper` for multi-step solutions.
13. **Captions** (`Takeaway`) ≤ 7 words, only for key claims (2–6 per video), right under the diagram. No subtitles.
14. **Open** (0–3 s): `Hook` question + one hero icon/logo — or start inside the scenario. First panel by 3–6 s.
15. **Real products**: use `LogoTile` (initials, brand-ish color) or a `Panel` with the product name. Never fetch logos.
16. **End**: the full final diagram stays lit during the recap; then `EndCard` blurs it (automatic).

## Planning stages (do this before coding)

Write one line per section: `section → what is added / what moves / what gets focus / what leaves`.
Example (format A, "How DNS finds an IP"):

```
hook      Hook "How does your browser find google.com?" + globe icon
scenario  Laptop panel (Sara) bottom; Browser url=google.com; Chip "google.com ?" pops
naive     "one big server" Panel center → state=error status="overloaded"; IconGrid 30 laptops hitting it
step1     error panel leaves; Resolver panel middle; Packet laptop→resolver "google.com?"; focus resolver
step2     Root / .com / ns1.google.com panels in a column right; numbered hops 1-2-3 with Packets; dim done hops
step3     answer Chip "142.250.183.238" travels back resolver→laptop; Browser loads
twist     Cache Tag "TTL 300 s" on resolver; second request stops at resolver (Focus); BigStat "1 hop instead of 4"
recap     everything un-dimmed; Title "Big picture"; Takeaway "Ask, cache, answer."
cta       (EndCard is automatic after narration)
```

## Layout grid (1080 × 1920)

| Layout | Coordinates |
|---|---|
| full-width panel | x 60, w 960 |
| two columns | x 60 / 555, w 465 (gap 30) |
| three columns | x 60 / 385 / 710, w 310 |
| vertical stack | rows at y 300, 620, 940, 1260 (h ≤ 280) — arrows between at panel centers |
| actor at bottom | center (540, 1250), icon 140 + label ≈ 200 px tall |
| caption | `Takeaway y` = ~60 px under the lowest element of the diagram (default 1520 if the diagram reaches the bottom) |

Text sizes: titles 84, panel labels 42, body/labels ≥ 30, mono values ≥ 26. Nothing smaller than 26 (it becomes unreadable on a phone).

## Patterns (copy and adapt)

**Spotlight plan** (rule 7) — ids on elements, plan on the canvas:
```tsx
<Canvas brand={script.brand} focus={[
  [cue('step1', 'resolver'), ['laptop', 'resolver', 'a1']],
  [cue('step2', 'root'), ['resolver', 'root', 'a2']],
  [sec('recap').from, []],                // [] = everything lit again
]}>
  <El id="resolver" at={cue('step1','resolver')} x={60} y={620} w={960} h={240}><Panel label="resolver" icon="server" /></El>
  <Arrow id="a1" … />   {/* Arrow accepts the same dim/focus through its id prop: see kit-api */}
```

**State change on the same object** (rule 8):
```tsx
const crashed = cue('naive', 'crashes');
const S: React.FC = () => { const f = useCurrentFrame();
  return <Panel label="one big server" icon="server" state={f >= crashed ? 'error' : 'normal'} status={f >= crashed ? 'crashed' : 'running'} />; };
```

**Hop by hop with numbered badges** (rule 9, 12):
```tsx
{hops.map((h, i) => (<React.Fragment key={i}>
  <Arrow at={h.at} path={h.path} color={c.cyan} />
  <Packet at={h.at + 4} dur={22} out={h.at + 26} path={h.path}><Chip>google.com?</Chip></Packet>
  <El at={h.at} x={h.path[0][0] - 60} y={h.path[0][1]} enter="pop"><Badge n={i + 1} /></El>
</React.Fragment>))}
```

**X vs Y** (format B): same scenario twice. Stage X builds the full flow in X's accent; at the "Now let's see Y" cue,
X's middle part leaves (or dims) and Y's part slides in at the same place in Y's accent; the scenario anchors
(person, target system) never move. For "in both cases", show both mini-flows side by side (two columns).

**Ladder** (format C): keep a `Stepper` at y≈1420 listing the fixes; each new problem turns a component `state="error"`,
each fix adds one new panel and lights the next step.

**Table scan / index**: `<Table scan={{at, dur}} hl={[{row, at}]}>` then `<Counter>` "9 checks" vs "3 steps".

**Tree**: Nodes in rows (root y 400, level-2 y 640, leaves y 880) + `Arrow`s from parent bottom-center to child top-center;
the search path = amber `Arrow`s + `Badge`s, other branches dimmed.

**Sequence (handshake)**: two `Actor`s at the top (x 230 / 850), dashed vertical lines (`Arrow` head={false} dashed)
down to y 1400; each message = horizontal `Arrow` + `Chip` label, every ~110 px lower, on its cue.

## Don'ts

- No word-by-word subtitles, no full-screen text slides, no stock photos, no emoji as visuals.
- No camera moves except ≤ 2 slow push-ins (`Camera`) on a detail; no spinning/bouncing.
- Mockups (`Browser`, `Phone`) are parts of the board (35–60 % width), not full screen.
- No hard-coded seconds; no element that appears before its word; nothing important below y = 1600.
- Do not copy any channel's logo, mascot, names or end card. Brand = the user's.
