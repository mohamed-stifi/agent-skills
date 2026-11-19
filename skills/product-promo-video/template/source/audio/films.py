"""SCRIPT + CUE SHEET + MUSIC MAP for every film. Rewrite this file for each product (see references/audio.md).

Line   : {'t': start_s, 'text': caption shown, 'say': what the voice reads (optional respelling), 'allowOverrun': bool}
Event  : (time_s, kind, {params}). 'into' and 'antic' END at time; 'riser' PEAKS at time; others START at time.
         kinds: whoosh into arrive antic impact reveal stamp click tick pop thud error pass chime shimmer riser swoosh
                typing count countdown fly swell      params: dur, size, db, rise, step, pitch, soft, up, rate
Music  : [(start_s, end_s, kind)] with kind in busy | dark | drive | lift | resolve
Film   : id (= the id in src/films.ts), duration (s), lines, events, music, optional voice / lang / lang3 / speed / title
"""
from timing import at, joins, remap, starts

# Scene starts in seconds, from src/timeline.ts (id, frames)
S = starts([('S01', 240)])

DEMO_LINES = [
    {'t': 0.6, 'text': 'Your product, in one sentence.'},
]
DEMO_EVENTS = [
    (S['S01'], 'arrive', {}), (at(S['S01'], 26), 'impact', {'size': 0.8}), (at(S['S01'], 26), 'shimmer', {}),
    (at(S['S01'], 56), 'swoosh', {}),
]
DEMO_MUSIC = [(0.0, 4.0, 'resolve')]

FILMS = {
    'demo-4s': dict(id='demo-4s', title='Demo', duration=4.0, lines=DEMO_LINES, events=DEMO_EVENTS, music=DEMO_MUSIC),
}
