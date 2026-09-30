#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""i18n audit: find Hebrew text left on the ARABIC pages.

build.py bakes each language into its own static page (Hebrew at /, Arabic
at /ar/). A Hebrew letter in a text node of dist/ar/*.html means a source
node had no data-ar, so Arabic readers (and Google's Arabic index) see Hebrew.

Scans dist/ar/*.html and reports:
  1. text nodes containing Hebrew letters — FAIL (exit 1)
     (exempt: anything inside lang="he" or data-i18n-exempt, e.g. the
     "עברית" link of the language switch)
  2. alt / aria-label / placeholder / title attributes with Hebrew —
     informational (add data-alt-ar / data-aria-ar in src to translate)
  3. leftover data-he / data-ar attributes in any built page — FAIL
     (build.py strips them; one surviving means localize() missed a tag)

Run `python build.py` first.
"""
import glob
import os
import re
import sys
from html.parser import HTMLParser

HEB = re.compile(r"[֐-׿]")
SKIP_TAGS = {"script", "style"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "source", "track", "wbr"}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
try:
    sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1255
except Exception:
    pass


class Audit(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []  # (tag, exempt)
        self.findings = []
        self.attr_notes = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        # bool() matters: `stack and ...` on an empty stack returns the stack
        # OBJECT, which later grows truthy and would mark everything exempt.
        exempt = a.get("lang") == "he" or "data-i18n-exempt" in a \
            or bool(self.stack and self.stack[-1][1])
        if tag not in VOID:
            self.stack.append((tag, exempt))
        if exempt:
            return
        for attr in ("alt", "aria-label", "placeholder", "title"):
            if HEB.search(a.get(attr) or ""):
                self.attr_notes.append("%s=%r" % (attr, a[attr][:40]))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for k in range(len(self.stack) - 1, -1, -1):
            if self.stack[k][0] == tag:
                del self.stack[k:]
                break

    def handle_data(self, data):
        if not HEB.search(data):
            return
        if any(t in SKIP_TAGS for t, _ in self.stack):
            return
        if self.stack and self.stack[-1][1]:
            return
        path = ">".join(t for t, _ in self.stack[-4:])
        self.findings.append("%-38s %s" % (path, " ".join(data.split())[:60]))


bad = 0
notes = 0
for page in sorted(glob.glob(os.path.join(DIST, "ar", "*.html"))):
    p = Audit()
    p.feed(open(page, encoding="utf-8").read())
    if p.findings:
        print("\n== ar/%s — %d Hebrew text node(s)" % (os.path.basename(page), len(p.findings)))
        for f in p.findings:
            print("   " + f)
        bad += len(p.findings)
    if p.attr_notes:
        print("\n-- ar/%s — %d Hebrew attribute(s) (info)" % (os.path.basename(page), len(p.attr_notes)))
        for n in p.attr_notes:
            print("   " + n)
        notes += len(p.attr_notes)

leftover = re.compile(r'\sdata-(?:aria-|alt-)?(?:he|ar)="')
for page in sorted(glob.glob(os.path.join(DIST, "*.html")) + glob.glob(os.path.join(DIST, "ar", "*.html"))):
    n = len(leftover.findall(open(page, encoding="utf-8").read()))
    if n:
        print("\n== %s — %d leftover data-he/data-ar attribute(s)" % (os.path.relpath(page, DIST), n))
        bad += n

print("\n%s" % ("CLEAN — no Hebrew text on the Arabic pages." if bad == 0
                else "TOTAL: %d problem(s)." % bad))
if notes:
    print("(%d Hebrew alt/aria-label attribute(s) noted above — informational)" % notes)
sys.exit(1 if bad else 0)
