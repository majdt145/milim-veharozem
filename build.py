#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
מילים וחרוזים — tiny static-site generator (no Node needed).
Wraps each src/pages/*.html in src/layout.html, sets the active nav item,
fills <title>/<meta description>, and copies styles.css, app.js and assets/ to dist/.

Usage:  python build.py
"""
import os, re, shutil, glob

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
DIST = os.path.join(ROOT, "dist")

META_RE = re.compile(r"^\s*<!--meta(.*?)-->", re.DOTALL)


def parse_meta(text):
    """Pull the leading <!--meta ... --> block; return (meta_dict, body_without_meta)."""
    m = META_RE.match(text)
    meta = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        text = text[m.end():]
    return meta, text.strip()


def build():
    layout = open(os.path.join(SRC, "layout.html"), encoding="utf-8").read()

    # fresh dist — clear CONTENTS (not the dir itself, which may be locked on Windows
    # if a shell's cwd is inside it)
    os.makedirs(DIST, exist_ok=True)
    for entry in os.listdir(DIST):
        p = os.path.join(DIST, entry)
        if os.path.isdir(p):
            shutil.rmtree(p, ignore_errors=True)
        else:
            try:
                os.remove(p)
            except OSError:
                pass

    # static assets
    for fname in ("styles.css", "app.js"):
        shutil.copy2(os.path.join(SRC, fname), os.path.join(DIST, fname))
    if os.path.isdir(os.path.join(SRC, "assets")):
        shutil.copytree(os.path.join(SRC, "assets"), os.path.join(DIST, "assets"))

    pages = sorted(glob.glob(os.path.join(SRC, "pages", "*.html")))
    built = []
    for path in pages:
        name = os.path.basename(path)
        raw = open(path, encoding="utf-8").read()
        meta, body = parse_meta(raw)

        html = layout
        html = html.replace("{{TITLE}}", meta.get("title", "מילים וחרוזים"))
        html = html.replace("{{DESC}}", meta.get("desc", ""))
        html = html.replace("{{CONTENT}}", body)

        # active nav item
        nav = meta.get("nav", "")
        if nav:
            html = html.replace(
                'data-nav="%s"' % nav,
                'data-nav="%s" class="active" aria-current="page"' % nav,
            )

        out = os.path.join(DIST, name)
        open(out, "w", encoding="utf-8").write(html)
        built.append(name)

    print("Built %d page(s): %s" % (len(built), ", ".join(built)))
    print("Output: %s" % DIST)


if __name__ == "__main__":
    build()
