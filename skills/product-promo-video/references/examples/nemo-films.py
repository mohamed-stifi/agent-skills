"""Scripts, sound-design cue sheets and music maps for every Nemo film.

Times are seconds from the start of each film. Event frames come from the scene code (60 fps):
seconds = scene start + frame / 60. Event = (time, kind, {params}). 'into' and 'antic' END at their time;
'riser' PEAKS at its time; everything else STARTS at its time.
"""

V = '<videos-root>'  # example only: paths in a real workspace come from engine.py
F = 60.0


def at(scene_start: float, frame: float) -> float:
    return round(scene_start + frame / F, 3)


# ═════════════════════════════ v1 · the incident film (53 s) ═════════════════════════════
S = dict(S01=0.0, S02=4.5, S03=12.0, S04=17.0, S05=21.5, S06=28.0, S07=33.5, S08=40.0, S09=47.0)

V1_LINES = [
    {'t': 1.70, 'text': '02:14 in the morning. A settlement job fails.', 'say': 'Two fourteen in the morning. A settlement job fails.'},
    {'t': 5.20, 'text': "Downstream: the liquidity report your central bank expects at six.", 'say': 'Downstream, the liquidity report your central bank expects at six.'},
    {'t': 9.90, 'text': 'The clock is already running.'},
    {'t': 12.30, 'text': 'Too fast for people alone.'},
    {'t': 14.35, 'text': 'Too risky for a bot acting alone.'},
    {'t': 17.40, 'text': 'Meet Nemo. The DataOps agent that works inside your perimeter, under your change control.',
     'say': 'Meet Nemo. The data ops agent that works inside your perimeter, under your change control.'},
    {'t': 23.00, 'text': 'It finds the cause, with the evidence to prove it.'},
    {'t': 28.60, 'text': 'Then policy decides. A regulatory feed is downstream, so a person must approve.'},
    {'t': 35.00, 'text': 'Rachid approves. Salma executes. Three identities, one audit trail.',
     'say': 'Rashid approves. Salma executes. Three identities, one audit trail.'},
    {'t': 41.00, 'text': 'The feed leaves at 04:52. Sixty-eight minutes to spare.',
     'say': 'The feed leaves at four fifty-two. Sixty-eight minutes to spare.'},
    {'t': 45.40, 'text': 'Faster than your runbook. Stricter than your auditor.'},
    {'t': 49.20, 'text': 'Nemo. Request a pilot.'},
]

s1, s2, s3, s4, s5, s6, s7, s8, s9 = (S[k] for k in S)
V1_EVENTS = [
    # S01 hook
    (at(s1, 30), 'tick', {}), (at(s1, 90), 'antic', {}), (at(s1, 92), 'impact', {'size': 0.7}), (at(s1, 92), 'error', {}),
    (at(s1, 94), 'whoosh', {'dur': 0.4, 'db': -18}), (at(s1, 150), 'swoosh', {}), (at(s1, 270), 'into', {'dur': 0.3}),
    # S02 cascade
    (s2, 'arrive', {}), (at(s2, 40), 'whoosh', {'dur': 0.45}), (at(s2, 68), 'error', {'db': -21}),
    (at(s2, 110), 'whoosh', {'dur': 0.45}), (at(s2, 138), 'error', {'db': -20}),
    (at(s2, 196), 'antic', {}), (at(s2, 196), 'whoosh', {'dur': 0.55, 'db': -12}), (at(s2, 228), 'impact', {'size': 0.8}), (at(s2, 228), 'error', {}),
    (at(s2, 250), 'countdown', {'dur': 3.0, 'rate': 7}), (at(s2, 450), 'into', {}),
    # S03 problem
    (s3, 'arrive', {}), (at(s3, 8), 'thud', {}), (at(s3, 120), 'whoosh', {'dur': 0.45}), (at(s3, 146), 'impact', {'size': 0.5}),
    (at(s3, 242), 'swoosh', {}), (at(s3, 272), 'pop', {'up': False}), (s4, 'riser', {'dur': 1.1}),
    # S04 reveal
    (s4, 'reveal', {}), (s4, 'whoosh', {'dur': 0.4, 'rise': False}), (at(s4, 30), 'swoosh', {}),
    (at(s4, 150), 'tick', {}), (at(s4, 172), 'tick', {}), (at(s4, 194), 'tick', {}), (s5, 'into', {}),
    # S05 investigate
    (s5, 'arrive', {}), (at(s5, 46), 'typing', {'dur': 0.85}), (at(s5, 104), 'whoosh', {'dur': 0.2, 'db': -20}),
    (at(s5, 112), 'typing', {'dur': 0.85}), (at(s5, 170), 'whoosh', {'dur': 0.2, 'db': -20}), (at(s5, 178), 'typing', {'dur': 0.85}),
    (at(s5, 236), 'antic', {}), (at(s5, 238), 'whoosh', {'dur': 0.5}), (at(s5, 258), 'impact', {'size': 0.6}),
    (at(s5, 290), 'pop', {}), (s6, 'into', {}),
    # S06 policy gate
    (s6, 'arrive', {}), (at(s6, 40), 'thud', {}), (at(s6, 58), 'pass', {'step': 1}), (at(s6, 120), 'thud', {'pitch': 0.9}),
    (at(s6, 158), 'antic', {}), (at(s6, 160), 'whoosh', {'dur': 0.4}), (at(s6, 188), 'impact', {'size': 0.9}), (at(s6, 188), 'stamp', {'db': -14}),
    (at(s6, 206), 'swoosh', {}), (s7, 'into', {}),
    # S07 approval
    (s7, 'arrive', {}), (at(s7, 44), 'whoosh', {'dur': 0.35}), (at(s7, 134), 'click', {}), (at(s7, 138), 'stamp', {}),
    (at(s7, 140), 'chime', {'db': -19}), (at(s7, 176), 'whoosh', {'dur': 0.5}),
    (at(s7, 216), 'thud', {}), (at(s7, 245), 'thud', {'pitch': 1.12}), (at(s7, 267), 'thud', {'pitch': 1.26}), (s8, 'into', {}),
    # S08 promise
    (s8, 'arrive', {}), (at(s8, 24), 'swell', {'dur': 2.9}), (at(s8, 196), 'impact', {'size': 0.9}), (at(s8, 196), 'chime', {}),
    (at(s8, 210), 'whoosh', {'dur': 0.5}), (at(s8, 244), 'count', {'dur': 1.1}), (at(s8, 310), 'pop', {}),
    (at(s8, 340), 'whoosh', {'dur': 0.4}), (s9, 'into', {}),
    # S09 CTA
    (s9, 'arrive', {}), (at(s9, 20), 'whoosh', {'dur': 0.5, 'rise': False}), (at(s9, 54), 'impact', {'size': 1.1}),
    (at(s9, 54), 'shimmer', {}), (at(s9, 96), 'swoosh', {}), (at(s9, 160), 'pop', {}), (at(s9, 182), 'shimmer', {'db': -22}),
]

V1_MUSIC = [(0.0, 17.0, 'dark'), (17.0, 40.0, 'drive'), (40.0, 47.0, 'lift'), (47.0, 53.0, 'resolve')]


# ═════════════════════════════ v2 · the main film (58.5 s) ═════════════════════════════
T = dict(V01=0.0, V02=6.0, V03=14.0, V04=18.0, V05=25.0, V06=31.0, V07=36.5, V08=43.0, V09=48.0, V10=54.0)
v01, v02, v03, v04, v05, v06, v07, v08, v09, v10 = (T[k] for k in T)

# V01 drop schedule, copied from V01Week.tsx (38 blocks, gaps shrink: 10*(1-i/37)^2 + 0.6 frames)
_drops, _t = [], 16.0
for _i in range(38):
    _drops.append(_t)
    _t += 10 * (1 - _i / 37) ** 2 + 0.6
_exit = round(_drops[-1]) + 14

V2_LINES = [
    {'t': 0.40, 'text': 'Reruns. Tickets. Row counts. Cost reports.', 'say': 'Re-runs. Tickets. Row counts. Cost reports.'},
    {'t': 3.70, 'text': 'Your best engineers spend their week on this.'},
    {'t': 6.70, 'text': 'Over 1,200 jobs a night. 43 systems to watch.',
     'say': 'Over twelve hundred jobs a night. Forty-three systems to watch.'},
    {'t': 10.60, 'text': 'Too much for people. Too risky for a bot.'},
    {'t': 14.50, 'text': 'Meet Nemo. The DataOps agent that takes the toil, under your control.',
     'say': 'Meet Nemo. The data ops agent that takes the toil, under your control.'},
    {'t': 19.20, 'text': 'A job fails at night: Nemo finds the cause, a person approves, and the report still leaves on time.',
     'say': 'A job fails at night. Nemo finds the cause, a person approves, and the report still leaves on time.'},
    {'t': 25.50, 'text': 'In a migration, the cutover stays locked until every check passes.', 'say': 'In a migration, the cut-over stays locked until every check passes.'},
    {'t': 31.40, 'text': 'Savings are replayed, then measured: nearly 14,000 dirhams a month, from one job.',
     'say': 'Savings are replayed, then measured. Nearly fourteen thousand deer-hams a month, from one job.'},
    {'t': 37.00, 'text': 'And every morning, one brief. 1,284 jobs overnight. Three need you.',
     'say': 'And every morning, one brief. Twelve hundred jobs overnight. Three need you.'},
    {'t': 43.30, 'text': 'You choose how much it does alone. Every action approved, verified and logged.'},
    {'t': 48.60, 'text': 'Give your team its week back.'},
    {'t': 51.20, 'text': 'Leave the toil to Nemo. Keep the business for your people.', 'allowOverrun': True},
    {'t': 55.80, 'text': 'Request a pilot.'},
]
# caption shows the exact count when the voice rounds it
V2_LINES[8]['text'] = 'And every morning, one brief. 1,200+ jobs overnight. Three need you.'

V2_EVENTS = (
    # V01 the week: one soft knock per block landing (pitch rises with the pile-up), then the squeeze
    [(at(v01, d + 8), 'thud', {'pitch': 0.9 + 0.5 * i / 37, 'db': -24 + 4 * i / 37}) for i, d in enumerate(_drops)]
    + [
        (at(v01, _exit - 4), 'antic', {}), (at(v01, _exit), 'whoosh', {'dur': 0.4, 'rise': False}), (at(v01, _exit + 22), 'impact', {'size': 0.5}),
        (at(v01, _exit + 12), 'thud', {'pitch': 1.4}), (at(v01, 207), 'swoosh', {}),
        (v02, 'riser', {'dur': 1.0, 'db': -16}), (v02, 'into', {'dur': 0.3}), (v02, 'impact', {'size': 0.8, 'db': -11}),
    ]
    # V02 scale and dilemma
    + [
        (at(v02, 26), 'count', {'dur': 0.9}), (at(v02, 80), 'whoosh', {'dur': 0.45}), (at(v02, 110), 'count', {'dur': 0.6}),
        (at(v02, 150), 'antic', {}), (at(v02, 156), 'whoosh', {'dur': 0.4}), (at(v02, 188), 'impact', {'size': 0.8}), (at(v02, 188), 'count', {'dur': 0.7}),
        (at(v02, 252), 'whoosh', {'dur': 0.45}), (at(v02, 280), 'thud', {}),
        (at(v02, 332), 'antic', {}), (at(v02, 338), 'whoosh', {'dur': 0.45}), (at(v02, 364), 'impact', {'size': 0.6}), (at(v02, 364), 'error', {'db': -20}),
        (at(v02, 422), 'swoosh', {}), (at(v02, 452), 'pop', {'up': False}), (v03, 'riser', {'dur': 1.0}),
    ]
    # V03 reveal
    + [(v03, 'reveal', {}), (v03, 'whoosh', {'dur': 0.4, 'rise': False}), (at(v03, 28), 'swoosh', {}),
       (at(v03, 140), 'tick', {}), (at(v03, 164), 'tick', {}), (v04, 'into', {})]
    # V04 run
    + [
        (v04, 'arrive', {}), (at(v04, 24), 'error', {}), (at(v04, 66), 'pop', {}), (at(v04, 98), 'tick', {}),
        (at(v04, 124), 'antic', {}), (at(v04, 128), 'whoosh', {'dur': 0.45}), (at(v04, 154), 'stamp', {}), (at(v04, 154), 'impact', {'size': 0.6, 'db': -14}),
        (at(v04, 184), 'pop', {}), (at(v04, 224), 'antic', {}), (at(v04, 228), 'whoosh', {'dur': 0.45}),
        (at(v04, 250), 'count', {'dur': 0.75}), (at(v04, 296), 'chime', {}), (at(v04, 304), 'swoosh', {}), (v05, 'into', {}),
    ]
    # V05 migrate: two failures, then ten passes climbing a scale, then the gate opens
    + [
        (v05, 'arrive', {}), (at(v05, 30), 'error', {}), (at(v05, 54), 'whoosh', {'dur': 0.35, 'db': -18}),
        (at(v05, 102), 'error', {}), (at(v05, 124), 'whoosh', {'dur': 0.35, 'db': -18}),
    ]
    + [(at(v05, f), 'pass', {'step': i}) for i, f in enumerate((172, 186, 198, 208, 217, 225, 232, 238, 243, 248))]
    + [
        (at(v05, 250), 'antic', {}), (at(v05, 254), 'whoosh', {'dur': 0.35}), (at(v05, 268), 'impact', {'size': 0.9}), (at(v05, 268), 'stamp', {'db': -14}),
        (at(v05, 314), 'swoosh', {}), (v06, 'into', {}),
    ]
    # V06 cost
    + [
        (v06, 'arrive', {}), (at(v06, 56), 'whoosh', {'dur': 0.45, 'rise': False}), (at(v06, 96), 'thud', {}),
        (at(v06, 104), 'pass', {'step': 2}), (at(v06, 124), 'pass', {'step': 3}), (at(v06, 144), 'pass', {'step': 4}),
        (at(v06, 184), 'antic', {}), (at(v06, 190), 'whoosh', {'dur': 0.3}), (at(v06, 192), 'count', {'dur': 0.75}),
        (at(v06, 236), 'impact', {'size': 0.9}), (at(v06, 236), 'chime', {'db': -18}), (at(v06, 262), 'swoosh', {}), (v07, 'into', {}),
    ]
    # V07 brief
    + [
        (v07, 'arrive', {}), (at(v07, 32), 'count', {'dur': 0.7}), (at(v07, 98), 'pass', {'step': 4}),
        (at(v07, 166), 'antic', {}), (at(v07, 174), 'whoosh', {'dur': 0.3}), (at(v07, 178), 'impact', {'size': 0.7}),
        (at(v07, 176), 'pop', {}), (at(v07, 190), 'pop', {}), (at(v07, 204), 'pop', {}), (at(v07, 256), 'swoosh', {}), (v08, 'into', {}),
    ]
    # V08 control
    + [(v08, 'arrive', {})]
    + [(at(v08, 8 + 12 * i), 'thud', {'pitch': 0.9 + 0.1 * i, 'db': -23}) for i in range(5)]
    + [
        (at(v08, 36), 'pop', {}), (at(v08, 52), 'tick', {}), (at(v08, 80), 'antic', {}), (at(v08, 84), 'whoosh', {'dur': 0.4}),
        (at(v08, 112), 'impact', {'size': 0.8}), (at(v08, 112), 'stamp', {'db': -15}),
        (at(v08, 160), 'tick', {}), (at(v08, 176), 'tick', {}), (at(v08, 192), 'tick', {}), (at(v08, 214), 'swoosh', {}), (v09, 'into', {}),
    ]
    # V09 the week given back: blocks fly to the lane, the yellow returns (the payoff), the promise
    + [(v09, 'arrive', {}), (at(v09, 16), 'whoosh', {'dur': 0.5, 'rise': False})]
    + [(at(v09, 40 + 110 * (i / 38) ** 0.8), 'fly', {}) for i in range(0, 39, 2)]
    + [(at(v09, 46 + 110 * (i / 38) ** 0.8), 'tick', {'soft': True, 'db': -27}) for i in range(0, 39, 3)]
    + [
        (at(v09, 148), 'swoosh', {}), (at(v09, 170), 'antic', {}), (at(v09, 196), 'impact', {'size': 1.2}), (at(v09, 196), 'shimmer', {}),
        (at(v09, 206), 'pop', {}), (at(v09, 222), 'pop', {}), (at(v09, 238), 'pop', {}),
        (v10, 'riser', {'dur': 0.6, 'db': -18}), (v10, 'into', {}),
    ]
    # V10 CTA
    + [(v10, 'arrive', {}), (at(v10, 54), 'impact', {'size': 1.1}), (at(v10, 54), 'shimmer', {}), (at(v10, 78), 'swoosh', {}),
       (at(v10, 128), 'pop', {}), (at(v10, 150), 'shimmer', {'db': -22})]
)

V2_MUSIC = [(0.0, 6.0, 'busy'), (6.0, 14.0, 'dark'), (14.0, 48.0, 'drive'), (48.0, 54.0, 'lift'), (54.0, 58.5, 'resolve')]


# ═════════════════════════════ cut-downs (from v2 frames) ═════════════════════════════

def remap(events, parts):
    """parts: [(from_s, len_s)] of the main film, concatenated. Keep events inside each part, shifted."""
    out, cursor = [], 0.0
    for (a, ln) in parts:
        for ev in events:
            t = ev[0]
            if a <= t < a + ln - 0.02:
                out.append((round(t - a + cursor, 3),) + tuple(ev[1:]))
        cursor += ln
    return out


C15 = [(0.0, 296 / F), (2880 / F, 360 / F), (3240 / F, 244 / F)]
j1, j2 = C15[0][1], C15[0][1] + C15[1][1]
C15_EVENTS = [e for e in remap(V2_EVENTS, C15) if not (j1 - 0.6 < e[0] < j1 and e[1] in ('riser',))] + [
    (j1, 'into', {}), (j2, 'into', {}),
]
C15_LINES = [
    {'t': 0.30, 'text': 'Reruns. Tickets. Cost reports.', 'say': 'Re-runs. Tickets. Cost reports.'},
    {'t': 2.60, 'text': "That's your best engineers' week."},
    {'t': 5.40, 'text': 'Hand the toil to an agent you control.'},
    {'t': 8.40, 'text': 'Leave the toil to Nemo. Keep the business for your people.'},
    {'t': 12.40, 'text': 'Request a pilot.'},
]
C15_MUSIC = [(0.0, j1, 'busy'), (j1, j2, 'lift'), (j2, 15.0, 'resolve')]

C6 = [(3070 / F, 170 / F), (3240 / F, 190 / F)]
k1 = C6[0][1]
C6_EVENTS = remap(V2_EVENTS, C6) + [(k1, 'into', {})]
C6_LINES = [
    {'t': 0.35, 'text': 'Leave the toil to Nemo. Keep the business for your people.'},
    {'t': 4.10, 'text': 'Request a pilot.'},
]
C6_MUSIC = [(0.0, k1, 'lift'), (k1, 6.0, 'resolve')]


FILMS = {
    'v1': dict(id='v1', title='Nemo · the incident film (v1)', duration=53.0, base='nemo-agent-promo-v1',
               video=f'{V}/nemo-agent-video-v1/out/nemo-agent-promo-v1.mp4', out_dir=f'{V}/nemo-agent-video-v1/out',
               lines=V1_LINES, events=V1_EVENTS, music=V1_MUSIC, speed=1.0),
    'v2': dict(id='v2', title='Nemo · main film (v2)', duration=58.5, base='nemo-main-film-v2',
               video=f'{V}/nemo-agent-video-v2/out/nemo-main-film-v2.mp4', out_dir=f'{V}/nemo-agent-video-v2/out',
               lines=V2_LINES, events=V2_EVENTS, music=V2_MUSIC, speed=1.0),
    'c15': dict(id='c15', title='Nemo · 15 s cut (v2)', duration=15.0, base='nemo-cut-15s-v2',
                video=f'{V}/nemo-agent-video-v2/out/nemo-cut-15s-v2.mp4', out_dir=f'{V}/nemo-agent-video-v2/out',
                lines=C15_LINES, events=C15_EVENTS, music=C15_MUSIC, speed=1.0),
    'c6': dict(id='c6', title='Nemo · 6 s cut (v2)', duration=6.0, base='nemo-cut-6s-v2',
               video=f'{V}/nemo-agent-video-v2/out/nemo-cut-6s-v2.mp4', out_dir=f'{V}/nemo-agent-video-v2/out',
               lines=C6_LINES, events=C6_EVENTS, music=C6_MUSIC, speed=1.0),
}
