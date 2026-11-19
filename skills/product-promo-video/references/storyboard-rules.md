# Storyboard and motion rules (copy this block into STORYBOARD.md unchanged)

1. **One subject per moment.** One thing to read at any instant. Supporting items are smaller, muted or off-frame.
   If two things animate at once, one of them is the camera.
2. **Motion leads the eye.** The camera travels along what to read next (a line drawing, a counter, a cursor, a marker).
   Never pull attention to an unrelated corner.
3. **Camera = `<Camera keys=[...]>` (`src/kit/Camera.tsx`).** Each scene is a world plane; fly over it. Perspective
   tilt (`rx`, `ry` up to ±30°) on approaches; land frontal (0°) when text must be read. Lay the world out at readable
   size and fly to it; never fake a zoom by scaling elements.
4. **Easing vocabulary only (`src/kit/ease.ts`).** `snap` (anticipation + overshoot) on the 1–2 decisive moves per
   scene only: overshoot means "this is the answer", anticipation means "something is coming". `whip` for travel,
   `land`/`pop` for entries, `drift` for holds (a hold is never fully still), `pushIn` for exits.
5. **Cuts hidden in speed.** Last 14–18 frames: accelerating push into a focus point (zoom ×5–60; blur comes from speed).
   First 16–20 frames: arrive from that state. The ground colour at each cut must match the next scene's start.
   Put exit keys on the scene's last frame.
6. **Brand identity from `src/kit/tokens.ts` only.** The accent colour is reserved for the brand mark, a decision, the
   selected item and the CTA. House style: square corners, no shadows/gradients/emoji, structure from rules (3 px ink rule
   opens a block, 1 px hairline rows, 1.5 px boxes), display type uppercase −0.02em, mono for ids/times/labels.
   With a product brand, follow ITS rules (radius, shadows, type) instead, consistently.
7. **Hierarchy:** one headline (110–200 px display) · one supporting line (30–44 px) · details 16–22 px.
   Nothing under 16 px on screen at the moment it is read (account for zoom). Tabular numbers for anything that counts.
8. **UI drawn with precision**, never screenshots: aligned rows, real values, paddings in multiples of 4.
9. **Chapters** show `<ChapterTag>` in screen space (outside the camera) and hide it (`end` prop) before a close-up
   would put it over content.
10. **Only true facts** from the facts bank.

## Scene brief format (one block per scene in STORYBOARD.md)
```
## S04 · RUN — the night incident, handled (420 f, white)  [B]
Subject: one change card telling the whole night in 7 s.
- World: … (sizes in px, exact copy, exact values)
- f0–22 arrive from blur …
- f128–158 decisive snap onto … (anticipation pull-back first)
- f304 headline (150 px): "HANDLED BEFORE THE MORNING."
- f404–419 exit push into … → cut on white
```

## Splitting work between subagents
3 groups, each 3–4 scenes, grouped so a group owns both ends of any shared element (e.g. the bookend scenes share
one component file, `Week.tsx`, owned by one group). Group A: hook + problem + promise · B: turn + chapters 1–2 ·
C: chapters 3–4 + trust + CTA.
