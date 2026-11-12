// Timing helpers for THIS video. Import {cue, sec} from './t' (or '../t' in stages/).
import {makeTiming} from '../../kit';
import timing from './timing.json';

export const {cue, sec, total, narrationEnd} = makeTiming(timing);
