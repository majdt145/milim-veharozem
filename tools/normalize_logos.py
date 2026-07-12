#!/usr/bin/env python3
"""
Normalize partner logos for the homepage strip so they all read the SAME
visual size regardless of how much padding each source file baked in.

For every image in --src it:
  1. trims to the logo's content bounding box (handles transparency + white bg),
  2. flattens onto white (matches the white .pt-logo tiles, no alpha halos),
  3. scales the content to a fixed height (so every mark is the same size),
  4. adds a tiny uniform margin,
  5. saves an optimized .webp named after the file's stem.

Then reference it in src/pages/index.html as a .pt-logo tile:
  <span class="chip pt-logo"><img src="assets/partners/<stem>.webp" alt="<name>"
        loading="lazy" decoding="async"></span>

Usage:
  python tools/normalize_logos.py --src "path/to/raw/logos" \
                                  --out src/assets/partners
"""
import argparse, os, glob
from PIL import Image, ImageChops

TARGET_H = 120   # content height every logo is scaled to (display ~30px @ CSS)
MARGIN   = 3     # tiny breathing room so content fills the tile like the SVGs
WHITE_TH = 243   # r,g,b all above this = background white
ALPHA_TH = 20    # alpha above this = real content


def content_bbox(im_rgba):
    boxes = []
    a = im_rgba.getchannel("A")
    if a.getextrema()[0] < 250:                       # has transparency
        boxes.append(a.point(lambda v: 255 if v > ALPHA_TH else 0).getbbox())
    flat = Image.new("RGB", im_rgba.size, (255, 255, 255))
    flat.paste(im_rgba, mask=a)
    r, g, b = flat.split()
    nw = lambda c: c.point(lambda v: 255 if v <= WHITE_TH else 0)  # not-white mask
    mask = ImageChops.lighter(ImageChops.lighter(nw(r), nw(g)), nw(b))
    boxes.append(mask.getbbox())
    boxes = [x for x in boxes if x]
    if not boxes:
        return None, flat
    l = min(x[0] for x in boxes); t = min(x[1] for x in boxes)
    rr = max(x[2] for x in boxes); bb = max(x[3] for x in boxes)
    return (l, t, rr, bb), flat


def process(path, out_dir):
    stem = os.path.splitext(os.path.basename(path))[0]
    im = Image.open(path).convert("RGBA")
    bbox, flat = content_bbox(im)
    crop = flat.crop(bbox or (0, 0, im.width, im.height))
    new_w = max(1, round(crop.width * TARGET_H / crop.height))
    crop = crop.resize((new_w, TARGET_H), Image.LANCZOS)
    canvas = Image.new("RGB", (new_w + 2 * MARGIN, TARGET_H + 2 * MARGIN), (255, 255, 255))
    canvas.paste(crop, (MARGIN, MARGIN))
    out = os.path.join(out_dir, stem + ".webp")
    canvas.save(out, "WEBP", quality=88, method=6)
    return stem, canvas.size, os.path.getsize(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="folder of raw logo images")
    ap.add_argument("--out", default="src/assets/partners")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    exts = ("*.png", "*.jpg", "*.jpeg", "*.webp", "*.gif", "*.bmp")
    files = [f for e in exts for f in glob.glob(os.path.join(a.src, e))]
    for f in sorted(files):
        try:
            stem, size, sz = process(f, a.out)
            print(f"{stem:14s} -> {size[0]}x{size[1]}  {sz//1024}KB")
        except Exception as e:
            print(f"{os.path.basename(f):20s} ERR {e}")
    print(f"done: {len(files)} logos -> {a.out}")


if __name__ == "__main__":
    main()
