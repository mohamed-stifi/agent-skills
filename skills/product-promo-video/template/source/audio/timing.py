"""Helpers for films.py: turn scene frames into seconds, and carry cue sheets into cut-downs."""
F = 60.0  # frames per second of the films


def at(scene_start: float, frame: float) -> float:
    """seconds = scene start (s) + frame inside the scene / 60."""
    return round(scene_start + frame / F, 3)


def starts(scenes: list[tuple[str, int]]) -> dict[str, float]:
    """[('S01', 270), ('S02', 450), ...] (frames, as in src/timeline.ts) -> {'S01': 0.0, 'S02': 4.5, ...} in seconds."""
    out, t = {}, 0
    for sid, dur in scenes:
        out[sid] = round(t / F, 3)
        t += dur
    return out


def remap(events: list, parts: list[tuple[int, int]]) -> list:
    """Cue sheet of the main film -> cue sheet of a cut. parts = [(fromFrame, lengthFrames)] exactly as in src/films.ts."""
    out, cursor = [], 0.0
    for (a, ln) in parts:
        a_s, ln_s = a / F, ln / F
        for ev in events:
            t = ev[0]
            if a_s <= t < a_s + ln_s - 0.02:
                out.append((round(t - a_s + cursor, 3),) + tuple(ev[1:]))
        cursor += ln_s
    return out


def joins(parts: list[tuple[int, int]]) -> list[float]:
    """Times (s) where the parts of a cut meet: put an 'into' whoosh there to sell the hard cut."""
    out, t = [], 0.0
    for (_, ln) in parts[:-1]:
        t += ln / F
        out.append(round(t, 3))
    return out
