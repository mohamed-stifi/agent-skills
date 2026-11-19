// Scene list of the MAIN film, in order. Lengths in frames at 60 fps. Hard cuts are hidden in whip-blur.
// file = the export name in src/scenes/<file>.tsx (also its file name).
export const SCENES: { id: string; file: string; dur: number }[] = [
  { id: 'S01', file: 'S01Example', dur: 240 },
];
export const TOTAL = SCENES.reduce((a, s) => a + s.dur, 0);
export const startOf = (id: string) => { let t = 0; for (const s of SCENES) { if (s.id === id) return t; t += s.dur; } return t; };
