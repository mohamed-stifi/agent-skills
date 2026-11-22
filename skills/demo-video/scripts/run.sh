#!/usr/bin/env bash
# Python with everything the engine needs, without touching the system Python:  run.sh engine.py --dry
# (uv caches the environment, so only the first run downloads packages.)
exec uv run --quiet --no-project --python 3.12 \
  --with pillow --with kokoro-onnx --with soundfile --with playwright \
  python "$@"
