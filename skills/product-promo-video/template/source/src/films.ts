import { TOTAL } from './timeline';

// DELIVERABLES. One entry per finished video. id is also the file name: <slug>-<id>.mp4 in output/.
// kind 'main' = the whole timeline. kind 'cut' = parts of the main timeline [fromFrame, lengthFrames], concatenated.
// Name ids for humans: 'promo-60s', 'promo-15s', 'promo-6s', 'story-50s', 'teaser-20s', 'explainer-90s'.
export type Film = { id: string; kind: 'main' | 'cut'; parts?: [number, number][] };
export const FILMS: Film[] = [
  { id: 'demo-4s', kind: 'main' },
];
export const framesOf = (f: Film) => (f.kind === 'main' ? TOTAL : (f.parts ?? []).reduce((a, p) => a + p[1], 0));
