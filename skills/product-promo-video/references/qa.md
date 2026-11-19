# QA: what to check, and known pitfalls

## Picture (after render.sh; look at every sheet)
- [ ] One subject per moment; nothing competing during a read.
- [ ] No text clipped by the frame while it is being read (chips, rows, headlines), no label over content
      (e.g. a ChapterTag over a zoomed card → end it earlier).
- [ ] Blur only during fast moves; holds razor sharp.
- [ ] Cut colours match (the last frame of a scene = the first frame of the next).
- [ ] Every number on screen is in the facts bank.
- [ ] End card: last ~40 frames perfectly still.

## Sound (after audio.sh + check.sh)
- [ ] Every line heard as written (Whisper); respell and re-voice, max 2 rounds.
- [ ] Final duration = silent duration (± 0.05 s), captioned too.
- [ ] Loudness about −14 LUFS, peak ≤ −1 dBFS.
- [ ] You cannot listen: say so in the reply and ask the user to listen with headphones.

## Known pitfalls (all hit in real runs)
- **Background subagents can lose their shell** in some hosts: run scene subagents in the foreground (several in one
  message still run in parallel).
- **File tools blocked outside the working directory**: author in a temp/scratch folder, copy with the shell.
- **Parallel renders can stall** at 0 %: use `CONCURRENCY=3`, retry once (render.sh does), render the films one at a time.
- **`delayRender` timeouts** on captioned renders under load: render.sh passes `--timeout=120000`; if a render still
  fails the old file is NOT valid: check durations (`check.sh`).
- **`ffmpeg -shortest` with a subtitle track** truncates the film at the last caption: the engine uses `-t <duration>`.
- **macOS ships bash 3.2**: scripts avoid `mapfile`; keep it that way when editing them.
- **No libass in some ffmpeg builds**: burned-in captions are drawn by Remotion (`Captioned.tsx`), not ffmpeg.
- Kokoro mispronounces initialisms and some names: always run check.sh.
