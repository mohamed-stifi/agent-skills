import {FPS} from './theme';

export type Timing = {
  totalSec: number;
  sections: {id: string; start: number; end: number}[];
  words: {w: string; s: number; e: number; sec: string}[];
};

const norm = (s: string) => s.toLowerCase().replace(/^[^\w]+|[^\w]+$/g, '');

/**
 * Build the timing helpers for one video. All results are ABSOLUTE frames
 * (the whole video is one continuous canvas, no per-section offsets).
 *
 *   cue('hook', 'index')          -> frame when "index" is first spoken in section "hook"
 *   cue('hook', 'index', 2)       -> second time
 *   cue('hook', 'full scan')      -> phrase (consecutive words)
 *   cue('hook', 'index', 1, 'end')-> when the word ENDS
 *   sec('hook')                   -> {from, to} frames of the section
 *
 * A missing word throws an error naming the section and listing its words.
 */
export const makeTiming = (t: Timing) => {
  const f = (sec: number) => Math.round(sec * FPS);
  const tail = 75; // end card frames after the narration (2.5 s)
  const total = f(t.totalSec) + tail;

  const sec = (id: string) => {
    const s = t.sections.find((x) => x.id === id);
    if (!s) throw new Error(`section not found: "${id}". Sections: ${t.sections.map((x) => x.id).join(', ')}`);
    return {from: f(s.start), to: f(s.end)};
  };

  const cue = (id: string, phrase: string, nth = 1, edge: 'start' | 'end' = 'start') => {
    sec(id);
    const ws = t.words.filter((w) => w.sec === id);
    const want = phrase.split(/\s+/).map(norm);
    let hits = 0;
    for (let i = 0; i + want.length <= ws.length; i++) {
      if (want.every((p, k) => norm(ws[i + k].w) === p)) {
        hits++;
        if (hits === nth) return f(edge === 'start' ? ws[i].s : ws[i + want.length - 1].e);
      }
    }
    throw new Error(
      `cue not found: "${phrase}" #${nth} in section "${id}". Words: ${ws.map((w) => norm(w.w)).join(' ')}`,
    );
  };

  return {cue, sec, total, narrationEnd: f(t.totalSec), tail};
};
