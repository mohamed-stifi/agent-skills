#!/usr/bin/env bash
# Voice + music + sound design + captions for the films in source/audio/films.py.
# usage: audio.sh <workspace> [film-id ...] [--voice <name>]      (default: every film)
# Needs the silent renders (render.sh). Outputs in source/out/audio/.
source "$(dirname "$0")/_lib.sh"
need_ws "$1"; shift
cd "$SRC/audio" && uv run python engine.py "$@" 2>&1 | grep -v -i "warning"
