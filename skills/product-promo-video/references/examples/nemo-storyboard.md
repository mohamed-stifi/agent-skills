# Nemo DataOps Agent — main film v2 · storyboard

1920×1080 · 60 fps · 3510 frames (58.5 s) · English · silent (music later) · every pixel drawn in React/SVG, no screenshots.

v1 (`../nemo-agent-video-v1`) is the 53 s "incident story" and stays as it is. **v2 is the main film.** v1 sold *trust*
on one incident. v2 sells the **outcome**, *your team's week back*, and uses trust as the reason to believe it.

**The one sentence the viewer must leave with:**
> Leave the toil to Nemo. Keep the business for your people.

**Who watches:** a head of data, CIO or operations director at a bank or a telecom operator. They should think: "This is
what I want in my team: my engineers on the business, the routine work handled by an agent I control."

## Structure

| # | Beat | Scene | Frames | Ground | Owner |
|---|------|-------|--------|--------|-------|
| V01 | HOOK | The week that toil eats | 360 | white | A |
| V02 | PROBLEM | The scale of toil, and the dilemma | 480 | ink | A |
| V03 | TURN | NEMO | 240 | yellow → white | B |
| V04 | SOLUTION 1/4 | RUN — the night incident, handled | 420 | white | B |
| V05 | SOLUTION 2/4 | MIGRATE — no cutover without proof | 360 | white | B |
| V06 | SOLUTION 3/4 | COST — savings measured, not promised | 330 | white | C |
| V07 | SOLUTION 4/4 | MORNING BRIEF — 1,284 jobs, 3 need you | 390 | white | C |
| V08 | TRUST | You choose how much it does alone | 300 | white | C |
| V09 | PROMISE | The week, given back | 360 | white | A |
| V10 | CTA | Request a pilot | 270 | ink | C |

The film **opens and closes on the same calendar week** (V01 and V09). The viewer sees *their own week* before and after.
That bookend is the core of the persuasion: build it with care and make V09 the exact visual inverse of V01.

## Non-negotiable rules (same as v1, every scene)

1. **One subject per moment.** One thing to read at any instant. Supporting items are smaller, muted (asphalt/dMuted)
   or off-frame. If two things animate at once, one of them is the camera.
2. **Motion leads the eye**: the camera travels *along* what to read next (a line drawing, a counter, a cursor, a
   marker). Never pull attention to an unrelated corner.
3. **Camera = `<Camera keys=[...]>` (`src/kit/Camera.tsx`).** Build each scene as a world plane and fly over it.
   Perspective tilt (`rx`, `ry` up to ±30°) on approaches; *land frontal* when text must be read. Lay out the world at
   readable size and fly to it; do not fake zooms by scaling elements.
4. **Easing vocabulary only (`src/kit/ease.ts`).** `snap` (anticipation + overshoot) only on the 1–2 decisive moves per
   scene: overshoot means "this is the answer", anticipation means "something is coming". `whip` for travel,
   `land`/`pop` for entries, `drift` for holds (never fully still), `pushIn` for exits.
5. **Transitions hidden in speed.** Last ~14–18 frames: accelerating push into a focus point (zoom ×5–60; blur comes
   from speed). First ~16–20 frames: arrive from that state. The background colour at each cut must match the table above
   (V02→V03 cuts on full yellow; V09→V10 cuts on ink). Exit keys sit on the scene's last frame.
6. **Signage identity:** square corners; no shadows, gradients, rounded corners or emoji. Structure from rules: a 3 px
   ink rule opens a block, 1 px hairline rows, 1.5 px ink boxes. Display: Barlow Condensed 800, uppercase, −0.02em.
   Body: Barlow. Labels, ids and times: IBM Plex Mono, uppercase labels 0.08em. Colours only from `C`. **Yellow** only
   for the brand, a human decision, a policy gate, the selected item, and "the business work that matters" (V01/V09).
7. **Hierarchy:** one headline (110–200 px display) · one supporting line (Barlow 30–44 px) · details mono 16–22 px.
   Nothing under 16 px on screen at the moment it is read (account for zoom). Tabular numbers for anything that counts.
8. **Chapters V04–V07** show `ChapterTag` (`src/kit/ui.tsx`, screen space, outside the camera) for their whole length,
   e.g. `<ChapterTag n={1} name="Run" line="Nights without the 02:14 page" frame={frame} end={dur} />`.
   The four chapters share one rhythm: **arrive → one proof moment (the decisive snap) → one headline → exit.**
   Each chapter ends on a single big headline (≤ 6 words) that states the benefit.
9. **Reuse v1's craft.** v1's scene code is in `src/scenes-v1/` (S01Hook … S09CTA): read the relevant ones and reuse
   techniques and components (decision panel, approval stamp, NEMO reveal, CTA end card). Copy code into your own files;
   do not import from `scenes-v1`.
10. **Only true facts.** Every figure below comes from the product plan's worked examples. Do not invent percentages,
   "hours saved" or customer names.

## Facts bank (use exactly)

- Tenant **Atlas Bank** (Casablanca), cluster `prod-b2`. People: Salma Idrissi (on-call engineer), Rachid Benjelloun
  (change manager), Imane Tazi (Finance Reporting owner), Khadija Bennani (risk and controls officer), Youssef Amrani
  (platform lead).
- Scale: **367 tools on 43 estate systems**; a night batch of **1,284 jobs**; **no shell on production**.
- **Run:** 02:14 `settlement_load_daily` fails (out of memory; input 3.1× the 30-day median, 412 GB). The cause is found
  by 02:16. Change `CHG-48213`: executor memory 8g → 14g. Approved by Rachid Benjelloun **02:31:12**, executed by Salma
  Idrissi **02:31:40**. `reg_liquidity_feed` submitted **04:52**, **68 min** before the 06:00 deadline.
- **Migrate:** `MIG-0007`, Teradata `FINDW` → lakehouse, wave W6, 57 objects. Parallel-run cycles on
  `FINDW.REG_LIQUIDITY_DAILY`: **cycle 1 FAIL** (`sum(hqla_amount_mad)` differs by 1,904,455.20; 212 keys; cause:
  lower-case `ccy_code`); **cycle 2 FAIL** (3 rows differ by 0.01: rounding; Imane Tazi declines a tolerance: "a
  regulatory amount must match exactly"); **cycles 3–12 PASS**, ten in a row. The cutover gate stays `deny` until
  10/10 passes and the owner signs. Rule: *no cutover without reconciliation*.
- **Cost:** saving `SAV-0142`, nightly Spark job `risk_exposure_calc`: 600 → 320 vcores, 2,112 → 704 GB memory. Replay
  in the sandbox: output identical by partition checksum; deadline slack 190 → 181 min. Proposed as pull request
  `risk/spark-jobs!88`; Khadija Bennani accepted. **Measured** over 14 runs: **13,903 MAD a month, 105 % of the
  estimate**. Rule: *it never counts a saving it has not measured.*
- **Morning brief:** `Morning brief · Data Platform · Thu 12 Nov 2026 · 07:30 — AMBER`. Overnight: **1,284 jobs ran:
  1,281 OK at first attempt, 3 failed, 2 late; 2 of the 3 recovered.** `reg_liquidity_feed` met with 68 min slack.
  **Needs you today (3):** 1 Approve or reject `APR-9931` (rerun `crm_segment_refresh` after the cast fix), Youssef
  Amrani, by 10:00 · 2 Post-implementation review of `CHG-48213`, Salma Idrissi and Rachid Benjelloun · 3 Sign or reject
  the learned runbook `RBP-0147`, Youssef Amrani. Median time to first analysis **2 min 51 s**.
- **Autonomy ladder:** L0 observe · L1 recommend · L2 act with approval · L3 act in an envelope (pre-approved runbooks)
  · L4 autonomous. Verdicts: allow < ask_reviewer < ask_human < deny; strictest wins; any error is a deny. Three
  identities on every change: the agent proposes, a person approves, another executes. Hash-chained audit log.
- **Deployment:** on-premises, open-weight model on the customer's own GPUs, restricted data never leaves; FR / EN.

---

## V01 · HOOK — "The week that toil eats" (360 f, white)  [A]

Subject: a calendar week filling up with grey.

- World: a team calendar drawn like the console (Monday–Friday columns, hours 08:00–20:00 plus a narrow "night" band
  at the bottom; mono day headers `MON 9 NOV` … `FRI 13 NOV`; hairline grid; a 3 px ink rule under the header; top label
  `DATA PLATFORM · ATLAS BANK · WEEK 46`).
- f0: frame starts close on Monday morning (zoom ~2.4, rx 18°, slight ry), almost empty. One **yellow** block sits there:
  `Liquidity data product · the project that matters` (Barlow 600, ink on yellow).
- f20–200: grey toil blocks (C.concrete fill, 1.5 px asphalt left bar, mono 16–18 px labels) drop in fast, with
  accelerating rhythm (`land`, each 10–14 f, the gaps between them shrinking), while the camera pulls back and squares up
  to show the whole week. Labels are real chores: `rerun settlement_load_daily`, `ticket: stg.settlements stale`,
  `Teradata row counts, wave W6`, `Spark sizing review`, `HDFS at 78 %, plan space`, `handover notes`,
  `02:14 page: prod-b2`, `reconcile FINDW`, `Kafka lag on cdr.raw`, `cost report for finance`… (16–24 blocks; the night
  band gets red-edged ones). The yellow block is **squeezed**: it shrinks with each drop, then is pushed out of the
  week (slides off with `snap`, the decisive move).
- f200–300: headline in screen space above a dimmed calendar (calendar at 35 %):
  `YOUR BEST ENGINEERS` / `SPEND THEIR WEEK ON THIS.` (`Rise`, 150 px, ink).
- f300–360: the camera dives (`pushIn`) into the red-edged night block `02:14 page: prod-b2`. Its fill turns ink as the
  zoom fills the frame, so the cut lands on **ink**.

## V02 · PROBLEM — the scale of toil, and the dilemma (480 f, ink)  [A]

Subject: three numbers, one at a time, then one line.

- f0–20 arrive from blur on ink.
- f20–250: three counters, **one at a time** on a world strip; the camera `whip`s from one to the next. Each is a
  huge mono/display number (220 px, dFg, tabular) that counts up fast, plus a Barlow 34 px dMuted line under it:
  `1,284` / `jobs every night` → `43` / `systems to watch` → `367` / `operations someone has to run safely`.
  Each counter lands with `land`; the third one's arrival uses `snap` (it is the heaviest).
- f250–420: reuse v1 S03's structure: `TOO MUCH FOR PEOPLE.` (150 px) then the camera snaps down to
  `TOO RISKY FOR A BOT.` ("BOT." in dRed), with mono lines under them: `nights, migrations, costs, reports` and
  `no shell on production · no unapproved change`. Never both at full weight.
- f420–480: pull back, both lines dim; a **yellow bar** wipes in between them, collapses into a square, and the camera
  pushes into it: the cut lands on **full yellow**. (Copy v1 S03's exit technique.)

## V03 · TURN — NEMO (240 f, yellow → white)  [B]

Reuse v1 S04's reveal, tightened to 240 f: start inside the yellow square (full yellow), snap out onto white, `NEMO`
300 px slides out from behind the square, a 3 px rule draws, then the supporting line (Barlow 500, 48 px):
`The DataOps agent that takes the toil, under your control.` Then a mono row:
`FOR BANKS AND TELECOM OPERATORS · INSIDE YOUR PERIMETER`. Exit: push to white.

## V04 · RUN — the night incident, handled (420 f, white)  [B]

ChapterTag `1 · Run · Nights without the 02:14 page`. Subject: one change card telling the whole night in 7 s.

- One card (about 1400×700): header mono `CHG-48213 · settlement_load_daily · prod-b2 · tier 2`. Three stacked steps
  that the camera reads top to bottom, each a row with time, actor and finding:
  `02:14` **Failed** · out of memory on 3.1× input (412 GB) — red marker
  `02:16` **Cause found · fix proposed** · executor memory `8g → 14g` (red strikethrough → green) — the Run agent
  `02:31:12` **Approved** · Rachid Benjelloun — this row's marker is a yellow stamp landing with `snap` (decisive), and
  `02:31:40` Executed by Salma Idrissi follows it.
- Then the camera snaps to the result strip: `04:52 · reg_liquidity_feed submitted` with a big green
  `68 MIN TO SPARE`.
- Headline (≤ 6 words, 140 px): `HANDLED BEFORE THE MORNING.` The card dims beneath it.
- Exit push toward the right (white).

## V05 · MIGRATE — no cutover without proof (360 f, white)  [B]

ChapterTag `2 · Migrate · Teradata to the lakehouse, with proof`. Subject: a row of twelve reconciliation cycles.

- Header: `MIG-0007 · FINDW → lakehouse · wave W6 · 57 objects`, object `FINDW.REG_LIQUIDITY_DAILY`.
- Twelve square cells in a row (each ~96 px, mono cycle number under it). Cycle 1 flips **red FAIL**; the camera dips
  to read its finding: `sum(hqla_amount_mad) differs by 1,904,455.20 · 212 keys · cause: lower-case ccy_code · fixed`.
  Cycle 2 flips red: `3 rows differ by 0.01 · rounding · tolerance declined by the owner`. Then cycles 3–12 flip
  **green** in fast succession (accelerating, the camera riding along the row: speed with accuracy). A counter
  `PASSES IN A ROW 10/10` ticks with them.
- A gate element at the end of the row: `CUTOVER GATE`, shown `DENY` (red) until 10/10, then it opens to
  `READY · waits for the owner's signature` (yellow: a human decision) with `snap`.
- Headline: `NO CUTOVER WITHOUT PROOF.` (140 px). Exit push (white).

## V06 · COST — savings measured, not promised (330 f, white)  [C]

ChapterTag `3 · Cost · Savings you can audit`. Subject: one number, earned.

- Card `SAV-0142 · risk_exposure_calc · nightly Spark job`. Two bars (or a before/after pair of rows) shrink with
  `snap`: `600 → 320 vcores`, `2,112 → 704 GB`. Under them, three green check rows appear one by one (mono 20 px):
  `replay output identical · partition checksum`, `deadline slack 190 → 181 min`, `pull request risk/spark-jobs!88 ·
  accepted by Khadija Bennani`.
- The decisive moment: a big number counts up **`13,903 MAD`** `a month` (display 180 px, tabular) with a label
  `MEASURED OVER 14 RUNS · 105 % OF THE ESTIMATE`.
- Headline: `SAVINGS MEASURED, NOT PROMISED.` (130 px). Exit push (white).

## V07 · MORNING BRIEF — 1,284 jobs, 3 need you (390 f, white)  [C]

ChapterTag `4 · Brief · Every morning at 07:30`. Subject: the brief message, read down to "Needs you today".

- One message card styled like a chat/console message (square, 1.5 px ink border, header row with the NEMO mark
  small): `Morning brief · Data Platform · Thu 12 Nov 2026 · 07:30` and an `AMBER` tag.
- The camera reads down: first `1,284 jobs ran · 1,281 OK at first attempt · 3 failed · 2 recovered` (the number counts),
  then `reg_liquidity_feed · met · 68 min slack` (green), then the **Needs you today (3)** block with a yellow left bar
  and its three items (APR-9931 · CHG-48213 review · RBP-0147), each with the person's name. The camera snaps onto
  `Needs you today (3)`: the decisive move.
- Headline: `WHILE YOU SLEPT: 1,284 JOBS. 3 NEED YOU.` (two lines, 120 px). Exit push (white).

## V08 · TRUST — you choose how much it does alone (300 f, white)  [C]

Subject: the autonomy ladder.

- Five steps rising left → right like a staircase (each a block with `L0`–`L4` Level badge and its name: observe,
  recommend, act with approval, act in an envelope, autonomous). A yellow marker climbs L0 → L1 → L2 with `snap` on
  arriving at L2 and stops; L3 and L4 stay outlined (`unlocked only with rehearsal, verification and verified rollback`).
- Under it, three short proof chips appear one at a time (mono 20 px):
  `strictest rule wins · any error is a deny` · `agent proposes · a person approves · another executes` ·
  `hash-chained audit log`.
- Headline: `YOU CHOOSE HOW MUCH IT DOES ALONE.` (120 px). Exit push (white).

## V09 · PROMISE — the week, given back (360 f, white)  [A]

The exact inverse of V01: the same calendar component, same labels.

- f0–20 arrive on the full calendar, full of grey (V01's final state).
- f20–150: a black lane labelled `NEMO` (ink, with the yellow square) slides in along the right edge. The grey toil
  blocks **lift off and fly into the lane** in waves (each block: `whip` with a slight arc, staggered, accelerating),
  and in the lane they become small ink rows with a green check (`rerun settlement_load_daily ✓` drawn as a square
  check icon, not an emoji). The camera follows the first block's flight, then pulls back.
- f150–230: the yellow block returns (`snap`: the film's emotional payoff) and **grows** to fill its day; more yellow
  business blocks appear (`Liquidity data product`, `New risk dashboard for the board`, `Customer 360 for retail`,
  `Iceberg roadmap`).
- f230–330: headline: `LEAVE THE TOIL TO NEMO.` / `KEEP THE BUSINESS FOR YOUR PEOPLE.` (`Rise`, 120 px). "NEMO."
  with the yellow square before it, or the word underlined in yellow.
- f330–360: push into the ink NEMO lane: the cut lands on **ink**.

## V10 · CTA (270 f, ink)  [C]

Reuse v1 S09: the NemoMark lands (`snap`); the tagline (Rise, 64 px, dFg): `Your people on the business. The toil on Nemo.`;
the `Request a pilot →` button (yellow) with one outline pulse; a mono row `ON-PREMISES · YOUR GPUS · YOUR CHANGE CONTROL
· FOR BANKS AND TELECOM OPERATORS`. The last 40 frames are a perfectly still end card.
