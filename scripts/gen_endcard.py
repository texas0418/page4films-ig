#!/usr/bin/env python3
"""Render assets/mise-endcard.png, the Mise card publish.py appends to every
single-image post so it goes out as a 2-slide carousel.

This asset used to exist with no source, so its copy drifted from the carousel
version. It is now rendered by the very same `mise_slide()` that builds the
last slide of every carousel, which makes divergence impossible. Pages is 2,
so the chrome reads 02 / 02, matching what the published post actually is.

Run after editing the card in gen_carousels.py:
    .venv/bin/python scripts/gen_endcard.py
"""
import importlib.util
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GC = os.path.join(ROOT, "scripts", "gen_carousels.py")

spec = importlib.util.spec_from_file_location("gen_carousels", GC)
gen_carousels = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen_carousels)   # safe: its calls sit behind __main__

out = os.path.join(ROOT, "assets", "mise-endcard.png")
gen_carousels.mise_slide(2).save(out)
print("built", os.path.relpath(out, ROOT))
