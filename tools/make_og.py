#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""One-shot generator for the social share image + favicon set.

Reads src/assets/logo.png, writes:
  src/assets/og.jpg                  1200x630 (WhatsApp/Facebook share card)
  src/assets/icons/favicon.ico       32x32
  src/assets/icons/icon-192.png      192x192
  src/assets/icons/icon-512.png      512x512
  src/assets/icons/apple-touch-icon.png  180x180

Run locally (`python tools/make_og.py`) and commit the outputs — the Vercel
build stays stdlib-only.
"""
import os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "src", "assets")
ICONS = os.path.join(ASSETS, "icons")
CREAM = (252, 238, 224)  # --cream, the brand background

logo = Image.open(os.path.join(ASSETS, "logo.png")).convert("RGBA")


def on_cream(size, logo_frac):
    """Logo centered on a cream canvas; logo height = logo_frac of canvas height."""
    canvas = Image.new("RGB", size, CREAM)
    target_h = int(size[1] * logo_frac)
    scale = target_h / logo.height
    lg = logo.resize((int(logo.width * scale), target_h), Image.LANCZOS)
    if lg.width > size[0] * 0.9:  # never wider than 90%
        scale = (size[0] * 0.9) / logo.width
        lg = logo.resize((int(logo.width * scale), int(logo.height * scale)), Image.LANCZOS)
    canvas.paste(lg, ((size[0] - lg.width) // 2, (size[1] - lg.height) // 2), lg)
    return canvas


os.makedirs(ICONS, exist_ok=True)

on_cream((1200, 630), 0.78).save(os.path.join(ASSETS, "og.jpg"), "JPEG", quality=88)

for px, name in ((512, "icon-512.png"), (192, "icon-192.png"), (180, "apple-touch-icon.png")):
    on_cream((px, px), 0.86).save(os.path.join(ICONS, name), "PNG")

on_cream((32, 32), 0.94).save(os.path.join(ICONS, "favicon.ico"), sizes=[(32, 32)])

for f in ("og.jpg", os.path.join("icons", "favicon.ico"), os.path.join("icons", "icon-192.png"),
          os.path.join("icons", "icon-512.png"), os.path.join("icons", "apple-touch-icon.png")):
    p = os.path.join(ASSETS, f)
    print("%-32s %6.1f KB" % (f, os.path.getsize(p) / 1024))
