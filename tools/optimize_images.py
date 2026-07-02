#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""One-shot image optimizer: JPG/PNG -> WebP at real display size.

Run locally (`python tools/optimize_images.py`) and commit the outputs;
HTML/CSS references are updated separately. Originals stay in git history.

Sizing: CTA backgrounds render full-width (cap 1600px); the why-us photo
renders ~1100px (cap 1200); logos render 56px (header) and ~500px (hero),
shipped at 2x for retina.
"""
import os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "src", "assets")

JOBS = [
    # (source, dest, max_width, quality, keep_alpha)
    ("img/joy.jpg",     "img/joy.webp",     1600, 80, False),
    ("img/group.jpg",   "img/group.webp",   1600, 80, False),
    ("img/play.jpg",    "img/play.webp",    1600, 80, False),
    ("img/session.jpg", "img/session.webp", 1200, 82, False),
    ("logo.png",        "logo.webp",         320, 90, True),   # header: 56px tall -> ~2x
    ("logo-hero.png",   "logo-hero.webp",   1000, 90, True),   # hero art -> 2x
]

for src, dst, maxw, q, alpha in JOBS:
    sp, dp = os.path.join(A, src), os.path.join(A, dst)
    im = Image.open(sp)
    im = im.convert("RGBA" if alpha else "RGB")
    if im.width > maxw:
        im = im.resize((maxw, int(im.height * maxw / im.width)), Image.LANCZOS)
    im.save(dp, "WEBP", quality=q, method=6)
    print("%-22s %4dpx  %6.1f KB  ->  %-22s %6.1f KB" % (
        src, im.width, os.path.getsize(sp) / 1024, dst, os.path.getsize(dp) / 1024))
