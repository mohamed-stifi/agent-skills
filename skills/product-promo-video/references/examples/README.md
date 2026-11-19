# Example scenes and cue sheet (approved work)

Scenes from two real films made with this workflow (Nemo, a DataOps agent for banks and telecom operators). They show
the quality bar: world planes, camera keys with deliberate `snap`s, one subject per moment, precise UI drawn in code.
They were written with the house-style token names (`C.yellow`, `C.green`, `C.red`, `C.asphalt`, `NemoMark`), which
`tokens.ts` / `ui.tsx` still alias. In new scenes use `C.accent`, `C.ok`, `C.stop`, `C.muted`, `BrandMark`.

| File | Shows |
|---|---|
| `Week.tsx` + `V01Week.tsx` + `V09Promise.tsx` | the bookend: a calendar eaten by chores, then given back (shared component, inverse scenes) |
| `V04Run.tsx` | a whole incident on one card; anticipation + snap onto an approval stamp; ChapterTag |
| `V05Migrate.tsx` | twelve cells flipping with accelerating rhythm; a gate that opens |
| `V07Brief.tsx` | a message card read top to bottom; counters |
| `S06PolicyGate.tsx` | a marker that anticipates, then snaps to the answer |
| `S07Approval.tsx` | a faithful console panel redraw; drawn cursor; click → stamp; three identities |
| `nemo-storyboard.md` | a complete storyboard (structure, rules, facts bank, per-scene beats) |
| `nemo-films.py` | a complete audio file: scripts, cue sheets from scene frames, music maps, cut-down remapping |

Copy techniques into new files. Do not import from here.
