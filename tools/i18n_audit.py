#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""i18n audit: find Hebrew text that would NOT switch in Arabic mode.

Scans built pages in dist/ and reports:
  1. text nodes containing Hebrew letters with no data-ar on the element
     or any ancestor (the JS toggle swaps the innermost data-ar holder)
  2. aria-label / alt / placeholder attributes with Hebrew but no
     matching data-aria-ar (aria-label) — informational

Run `python build.py` first. Exit code 1 if untranslated text remains.
"""
import glob
import os
import re
import sys
from html.parser import HTMLParser

HEB = re.compile(r"[֐-׿]")
SKIP_TAGS = {"script", "style"}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")


class Audit(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []  # (tag, covered_by_data_ar)
        self.findings = []
        self.attr_notes = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        # bool() matters: `stack and ...` on an empty stack returns the stack
        # OBJECT, which later grows truthy and would mark everything covered.
        # data-i18n-exempt marks text that must NOT switch (e.g. the language
        # buttons themselves — עברית stays Hebrew, عربي stays Arabic).
        covered = ("data-ar" in a) or ("data-i18n-exempt" in a) \
            or bool(self.stack and self.stack[-1][1])
        if tag not in ("br", "img", "input", "meta", "link", "hr", "i"):
            self.stack.append((tag, covered))
        label = a.get("aria-label", "")
        if HEB.search(label) and "data-aria-ar" not in a:
            self.attr_notes.append("aria-label=%r" % label[:40])
        for attr in ("alt", "placeholder"):
            if HEB.search(a.get(attr, "")):
                # alt/placeholder don't switch by design — note, don't fail
                self.attr_notes.append("%s=%r" % (attr, a[attr][:40]))
        # void-ish elements can still carry data-ar (e.g. <input>) — ignore

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
for page in sorted(glob.glob(os.path.join(DIST, "*.html"))):
    p = Audit()
    p.feed(open(page, encoding="utf-8").read())
    if p.findings:
        print("\n== %s — %d untranslated text node(s)" % (os.path.basename(page), len(p.findings)))
        for f in p.findings:
            print("   " + f)
        bad += len(p.findings)

print("\n%s" % ("CLEAN — every Hebrew text node switches to Arabic." if bad == 0
                else "TOTAL: %d untranslated node(s)." % bad))
sys.exit(1 if bad else 0)
