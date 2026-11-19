# Subagent brief (fill the <…> and send one per group, all in the same message, foreground)

You are a senior motion designer + React engineer building part of a <N>-second, <W>×<H> promo film in Remotion 4 (60 fps)
for <product>: <one-line description>.

WORKSPACE: <WS>   (Remotion project in <WS>/source)
<If the agent's file tools cannot reach WS: "Author files with your file tools in <scratch dir>, copy them into
<WS>/source/src/scenes/ with the shell, and copy rendered PNGs back to <scratch dir> to view them.">

YOUR SCOPE: implement ONLY src/scenes/<S0xName>.tsx (export const <S0xName>), … and add one export line per scene to
src/scenes/index.ts. Do NOT edit src/kit, src/Root.tsx, src/timeline.ts, src/films.ts or other scenes (others work in
parallel). Helpers go in your own files.

READ FIRST, fully: <WS>/STORYBOARD.md (rules, facts bank, your briefs, and the neighbouring scenes' entry/exit), the kit
(src/kit/ease.ts, Camera.tsx, ui.tsx, tokens.ts) and, for the quality bar, the example scenes in
<SKILL>/references/examples/ (copy techniques, never import them). <UI references: images/pages to redraw, never embed.>

QUALITY BAR: powerful camera moves that show speed yet accuracy (perspective zoom-ins, tilts that land frontal for
reading); anticipation and overshoot only on decisive moves; one subject per moment; motion leads the eye; strict
hierarchy; UI drawn with precision; only facts from the facts bank; text ≥ 16 px on screen when read; nothing clipped.

VERIFY VISUALLY (mandatory): `bash <SKILL>/scripts/render.sh <WS> <SceneId>` (type-checks, renders, writes
source/stills/<SceneId>-sheet.png). View the sheet; render single frames with
`cd <WS>/source && npx remotion still src/index.ts <SceneId> stills/<SceneId>-f120.png --frame=120`.
Check legibility, hierarchy, clipping, blur only during fast moves, cut colours, timing. Fix and re-render.
At least 2 critique-and-fix passes; re-check the final sheet after your last change. Max 4 render rounds per scene.

FINAL REPORT (short): beat by beat per scene with frame numbers of every decisive snap, stamp, count, whip and exit
(the audio is synced from these numbers), deviations from the storyboard and why, what you did not verify.
