#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
מילים וחרוזים — tiny static-site generator (no Node needed).
Wraps each src/pages/*.html in src/layout.html, sets the active nav item,
fills <title>/<meta description>, and copies styles.css, app.js and assets/ to dist/.
Every page is built twice: Hebrew at the root (/services.html) and Arabic
under /ar/ (/ar/services.html), from the same source (see localize()).

Usage:  python build.py
"""
import os, re, shutil, glob, hashlib
from html import escape as _esc  # title/desc land in HTML attrs — escape so a literal " can't truncate them
from html.parser import HTMLParser


def _ver(path):
    """Short content hash of an asset, for cache-busting ?v= stamps."""
    h = hashlib.md5(open(path, "rb").read()).hexdigest()[:8]
    return h

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
DIST = os.path.join(ROOT, "dist")

# Canonical origin for canonicals / OG / sitemap / robots / llms.txt. The
# custom domain www.melimharozem.com (bought 2026-09-28) is the primary; the
# apex and the old milim-veharozem.vercel.app both 308 to it (Vercel domain
# settings + vercel.json).
SITE_URL = "https://www.melimharozem.com"

# Languages. Hebrew is the root site and the x-default; Arabic lives under
# /ar/. Each page carries reciprocal hreflang links to both (+ x-default),
# and the sitemap lists both with the same alternates.
LANGS = ("he", "ar")
SITE_NAME = {"he": "מילים וחרוזים", "ar": "ميليم وحاروزيم"}
OG_LOCALE = {"he": "he_IL", "ar": "ar_IL"}
HREFLANG = (("he", "he"), ("ar", "ar"), ("x-default", "he"))

# Hebrew homepage only: a visitor who explicitly chose Arabic in the language
# switch (app.js stores it) and arrives from OUTSIDE the site (typed the
# domain, a bookmark, a search result) lands on /ar/. Internal navigation to
# the Hebrew home is never redirected, and crawlers have no stored choice, so
# they always get the Hebrew page.
LANG_MEMORY = ("<script>(function(){try{if(localStorage.getItem('mvh_lang')==='ar'"
               "&&document.referrer.indexOf(location.origin)!==0)"
               "location.replace('/ar/'+location.search+location.hash);}catch(e){}})();</script>")


def page_path(name, lang):
    """Root-relative URL of a page: / · /services.html · /ar/ · /ar/services.html"""
    return ("/ar/" if lang == "ar" else "/") + ("" if name == "index.html" else name)


def page_url(name, lang):
    return SITE_URL + page_path(name, lang)

# Google Search Console HTML-file verification — served at the site root and
# fetched by GSC to prove ownership. The token is per Google account, so the
# same file verifies every property under it. Keep it even after verifying.
GOOGLE_SITE_VERIFICATION = "google3654382e4b01e65d.html"

# IndexNow ownership key (Bing, Yandex, Naver, Seznam — ChatGPT search reads
# Bing). Must stay stable and match the {key}.txt file at the site root.
# Ping after content deploys: POST https://api.indexnow.org/indexnow
INDEXNOW_KEY = "446ee9a335c6feb9e2eeb5fe87b29542"

# Content flags. TESTIMONIALS stays False until real consented parent quotes
# arrive from the clinic — the placeholder section is then swapped for them
# and this flips to True.
FLAGS = {"TESTIMONIALS": False}

META_RE = re.compile(r"^\s*<!--meta(.*?)-->", re.DOTALL)
FLAG_RE = re.compile(r"<!--IF:(\w+)-->(.*?)<!--ENDIF:\1-->", re.DOTALL)


def apply_flags(html):
    """Keep or drop <!--IF:NAME--> ... <!--ENDIF:NAME--> blocks per FLAGS."""
    return FLAG_RE.sub(lambda m: m.group(2) if FLAGS.get(m.group(1)) else "", html)


# ---------------------------------------------------------------------------
# Localization. The source marks every translatable node with data-he/data-ar
# (+ data-aria-* for aria-label, data-alt-* for alt). This used to be swapped
# in the browser; now each language is baked into its own static page, with
# the SAME rule the old runtime toggle used: only the innermost [data-ar] node
# gets data-ar as its innerHTML, so icons / tel: links / nested spans inside a
# container survive. The i18n attributes are then stripped from the output.
# ---------------------------------------------------------------------------
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "source", "track", "wbr"}
I18N_ATTR_RE = re.compile(r'\s+data-(?:aria-|alt-)?(?:he|ar)="[^"]*"')


class _Elements(HTMLParser):
    """Every element's start-tag span and content span, as absolute offsets
    into the source text, so localize() can splice it without re-serializing."""

    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.line_starts = [0] + [m.end() for m in re.finditer("\n", text)]
        self.stack, self.elems = [], []
        self.feed(text)
        self.close()

    def _pos(self):
        line, col = self.getpos()
        return self.line_starts[line - 1] + col

    def _el(self, tag, attrs):
        start = self._pos()
        el = {"tag": tag, "attrs": dict(attrs), "start": start,
              "tag_end": start + len(self.get_starttag_text()),
              "close": None, "implicit": False, "nested": False}
        if "data-ar" in el["attrs"]:
            for anc in self.stack:
                anc["nested"] = True  # an ancestor of a [data-ar] is never swapped
        self.elems.append(el)
        return el

    def handle_starttag(self, tag, attrs):
        el = self._el(tag, attrs)
        if tag not in VOID:
            self.stack.append(el)

    def handle_startendtag(self, tag, attrs):
        self._el(tag, attrs)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i]["tag"] == tag:
                for el in self.stack[i + 1:]:
                    el["implicit"] = True  # closed without its own end tag
                self.stack[i]["close"] = self._pos()
                del self.stack[i:]
                return


def _set_attr(tag_html, name, value):
    """Set one attribute's value inside a raw start tag (adds it if missing)."""
    value = _esc(value, quote=True)
    pat = re.compile(r'(\s%s=")[^"]*(")' % re.escape(name))
    if pat.search(tag_html):
        return pat.sub(lambda m: m.group(1) + value + m.group(2), tag_html, count=1)
    return re.sub(r"\s*/?>$", lambda m: ' %s="%s"%s' % (name, value, m.group(0)),
                  tag_html, count=1)


def localize(html, lang, page):
    """Bake one language into a built page and strip the i18n attributes.
    Hebrew keeps its static text as-is (it IS the Hebrew); Arabic swaps in
    data-ar / data-aria-ar / data-alt-ar. Raises instead of guessing when a
    translatable node has no explicit end tag."""
    doc = _Elements(html)
    swaps, tag_edits = [], []
    for el in doc.elems:
        a = el["attrs"]
        if lang == "ar" and "data-ar" in a and not el["nested"]:
            if el["tag"] in VOID or el["close"] is None or el["implicit"]:
                raise ValueError("%s: <%s data-ar> at offset %d has no end tag"
                                 % (page, el["tag"], el["start"]))
            swaps.append((el["tag_end"], el["close"], a["data-ar"]))
        raw = html[el["start"]:el["tag_end"]]
        new = I18N_ATTR_RE.sub("", raw)
        if lang == "ar":
            if "data-aria-ar" in a:
                new = _set_attr(new, "aria-label", a["data-aria-ar"])
            if "data-alt-ar" in a:
                new = _set_attr(new, "alt", a["data-alt-ar"])
        if new != raw:
            tag_edits.append((el["start"], el["tag_end"], new))
    # a start tag inside a swapped node is replaced wholesale with that node
    edits = swaps + [e for e in tag_edits
                     if not any(lo <= e[0] < hi for lo, hi, _ in swaps)]
    for start, end, text in sorted(edits, reverse=True):
        html = html[:start] + text + html[end:]
    return html


TEAM_RE = re.compile(r"<!--TEAM:(.+?)-->")


def team_groups():
    """Hebrew group name (the h2 on team.html) -> that whole .tm-group block,
    so a service page shows exactly the people the team page does (one source,
    no drift). Used via <!--TEAM:קלינאות תקשורת--> in a page."""
    raw = open(os.path.join(SRC, "pages", "team.html"), encoding="utf-8-sig").read()
    _, body = parse_meta(raw)
    groups = {}
    for el in _Elements(body).elems:
        if el["tag"] == "div" and "tm-group" in el["attrs"].get("class", "").split() \
                and el["close"] is not None and not el["implicit"]:
            block = body[el["start"]:el["close"] + len("</div>")]
            h2 = re.search(r'<h2[^>]*data-he="([^"]+)"', block)
            if h2:
                groups[h2.group(1)] = block
    return groups


def breadcrumb_ld(name, lang, meta, metas):
    """BreadcrumbList for pages with a `parent` (home › parent › page)."""
    import json
    ar = lang == "ar"
    crumb = lambda m: (m.get("crumb_ar") if ar else None) or m.get("crumb") or m.get("title", "")
    chain = [("index.html", "الرئيسية" if ar else "בית")]
    if meta.get("parent") in metas:
        chain.append((meta["parent"], crumb(metas[meta["parent"]])))
    chain.append((name, crumb(meta)))
    items = [{"@type": "ListItem", "position": i + 1, "name": n, "item": page_url(p, lang)}
             for i, (p, n) in enumerate(chain)]
    return '<script type="application/ld+json">%s</script>' % json.dumps(
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items},
        ensure_ascii=False)


def rebase_ar(html, pages):
    """Arabic pages live one folder down (/ar/). Point shared files at the
    root and page links at their Arabic twins; leave absolute / external /
    mailto: / tel: / #fragment links alone."""
    def fix(m):
        attr, q, url = m.group(1), m.group(2), m.group(3)
        path, hash_, frag = url.partition("#")
        if path.split("?")[0] in ("styles.css", "app.js") or path.startswith("assets/"):
            url = "/" + url
        elif path in pages:
            url = page_path(path, "ar") + hash_ + frag
        return "%s=%s%s%s" % (attr, q, url, q)
    return re.sub(r'\b(href|src)=(["\'])([^"\'#:/?][^"\']*)\2', fix, html)


# Structured data for Google: the organization + its four physical branches.
# Injected on index + contact only (the pages that describe the clinic itself).
# openingHours intentionally omitted until the clinic confirms real hours;
# street addresses only where the clinic has given one.
# Every way people spell the clinic's name in searches — Latin (the domain,
# the Instagram handle, the common "milim" misspelling) and Arabic (our own
# rendering + the one kesher.org.il uses). Search engines read these as the
# same entity.
NAME_VARIANTS = ["Milim VeHaruzim", "melimharozem", "milimharozem",
                 "Melim Harozem", "ميليم وحاروزيم", "ميليم في حروزيم"]


def jsonld(services=()):
    import json
    org = {
        "@type": "MedicalOrganization",
        "@id": SITE_URL + "/#org",
        "name": "מילים וחרוזים בע״מ",
        "alternateName": NAME_VARIANTS,
        "description": "יחידה להתפתחות הילד — אבחון וטיפול רב-תחומי מלידה ועד גיל 18",
        "url": SITE_URL + "/",
        "logo": SITE_URL + "/assets/icons/icon-512.png",
        "image": SITE_URL + "/assets/og.jpg",
        "email": "melimharozem@gmail.com",
        "telephone": "+972-50-657-1203",
        "foundingDate": "2016",
        "availableLanguage": ["he", "ar"],
        # The clinic's own social profiles — ties the brand entity Google already
        # knows (the Facebook page ranks for the name) to this site.
        "sameAs": [
            "https://www.facebook.com/melimharozem/",
            "https://www.instagram.com/melimharozem/",
        ],
    }
    # the service pages (meta `service_type`), so the entity lists what it offers
    if services:
        org["availableService"] = [
            {"@type": stype, "name": name, "url": page_url(p, "he")}
            for p, name, stype in services
        ]
    def clinic(name, name_en, tel, street=None, locality=None):
        c = {
            "@type": "MedicalClinic",
            "name": "מילים וחרוזים — " + name,
            "alternateName": name_en,
            "parentOrganization": {"@id": SITE_URL + "/#org"},
            "telephone": tel,
            "url": SITE_URL + "/contact.html",
            "medicalSpecialty": ["Pediatric", "SpeechPathology", "Physiotherapy", "Psychiatric"],
            "availableLanguage": ["he", "ar"],
        }
        addr = {"@type": "PostalAddress", "addressCountry": "IL"}
        if street: addr["streetAddress"] = street
        if locality: addr["addressLocality"] = locality
        c["address"] = addr
        return c
    # Google's site-name signal: the name shown above the URL in search
    # results (otherwise it falls back to the bare domain "melimharozem.com").
    website = {
        "@type": "WebSite",
        "@id": SITE_URL + "/#website",
        "name": "מילים וחרוזים",
        "alternateName": NAME_VARIANTS,
        "url": SITE_URL + "/",
        "inLanguage": ["he", "ar"],
        "publisher": {"@id": SITE_URL + "/#org"},
    }
    graph = {"@context": "https://schema.org", "@graph": [
        website,
        org,
        clinic("עכו", "Milim VeHaruzim Akko", "+972-50-657-1203",
               "קניון עזריאלי, רחוב החרושת 2, קומה 4", "עכו"),
        clinic("מזרעה", "Milim VeHaruzim Mazra'a", "+972-53-587-3804",
               "רחוב אלאנביאא 11", "מזרעה"),
        clinic("שעב", "Milim VeHaruzim Sha'ab", "+972-50-657-1203",
               None, "שעב"),
        clinic("מג'דל שמס", "Milim VeHaruzim Majdal Shams", "+972-54-895-5099",
               None, "מג'דל שמס"),
    ]}
    return '<script type="application/ld+json">%s</script>' % json.dumps(graph, ensure_ascii=False)


def hreflang_links(name, fmt):
    """The page's full language cluster (he, ar, x-default) — identical on
    both versions, which is what makes the pairs reciprocal."""
    return "".join(fmt % (code, page_url(name, lang)) for code, lang in HREFLANG)


def write_sitemap(pages):
    urls = "".join(
        "  <url><loc>%s</loc>\n%s  </url>\n" % (
            page_url(p, lang),
            hreflang_links(p, '    <xhtml:link rel="alternate" hreflang="%s" href="%s"/>\n'))
        for lang in LANGS for p in sorted(pages)
    )
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
           '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n%s</urlset>\n' % urls)
    open(os.path.join(DIST, "sitemap.xml"), "w", encoding="utf-8").write(xml)
    open(os.path.join(DIST, "robots.txt"), "w", encoding="utf-8").write(
        "User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % SITE_URL)
    open(os.path.join(DIST, INDEXNOW_KEY + ".txt"), "w", encoding="utf-8").write(INDEXNOW_KEY)
    # Google Search Console ownership file (HTML-file method)
    open(os.path.join(DIST, GOOGLE_SITE_VERIFICATION), "w", encoding="utf-8").write(
        "google-site-verification: " + GOOGLE_SITE_VERIFICATION + "\n")


# Page order for llms.txt (anything not listed follows alphabetically).
LLMS_ORDER = ["index.html", "services.html",
              "speech-therapy.html", "occupational-therapy.html", "physiotherapy.html",
              "psychology.html", "emotional-therapy.html", "learning-assessment.html",
              "autism-assessment.html", "adhd-moxo.html",
              "team.html", "workshops.html",
              "schools.html", "jobs.html", "contact.html",
              "accessibility.html", "privacy.html"]


def write_llms(page_meta):
    """llms.txt — AI-search discovery file. Page lines reuse each page's own
    title/desc, so it never drifts from the site's (the clinic's) wording.
    page_meta: lang -> {name: (title, desc)}"""
    he = page_meta["he"]
    order = ([p for p in LLMS_ORDER if p in he] +
             sorted(p for p in he if p not in LLMS_ORDER))
    lines = [
        "# מילים וחרוזים — Milim VeHaruzim",
        "",
        "> " + he.get("index.html", ("", ""))[1],
        "",
        "Multidisciplinary child-development unit: assessment and therapy from birth "
        "to age 18 (speech therapy, occupational therapy, physiotherapy, psychology, "
        "emotional therapy, social work). Branches in the north: Akko, Mazra'a, "
        "Sha'ab, Majdal Shams. The site is in Hebrew, with a full Arabic version "
        "under %s/ar/." % SITE_URL,
        "",
        "- Phone / WhatsApp: 050-657-1203",
        "- Email: melimharozem@gmail.com",
    ]
    for lang, heading in (("he", "Pages (Hebrew)"), ("ar", "Pages (Arabic)")):
        lines += ["", "## " + heading, ""]
        for p in order:
            title, desc = page_meta[lang][p]
            lines.append("- [%s](%s): %s" % (title, page_url(p, lang), desc))
    open(os.path.join(DIST, "llms.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")


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

    # static assets (+ content-hash versions for cache-busting).
    # CSS/JS get a conservative slim: comments + indentation stripped, one
    # declaration per line kept intact. Fail-open: any error ships the
    # original file untouched.
    ver = {}
    for fname in ("styles.css", "app.js"):
        src_file = os.path.join(SRC, fname)
        text = open(src_file, encoding="utf-8").read()
        try:
            slim = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
            slim = "\n".join(l.strip() for l in slim.splitlines() if l.strip())
        except Exception:
            slim = text
        open(os.path.join(DIST, fname), "w", encoding="utf-8").write(slim)
        ver[fname] = _ver(src_file)
    if os.path.isdir(os.path.join(SRC, "assets")):
        shutil.copytree(os.path.join(SRC, "assets"), os.path.join(DIST, "assets"))
    # crawlers and browsers still request /favicon.ico at the root directly.
    # mark.ico = the logo's heart + child only (no text — unreadable at 16–48px),
    # sizes 16/32/48; Google Search wants icons in multiples of 48px.
    ico = os.path.join(SRC, "assets", "icons", "mark.ico")
    if os.path.exists(ico):
        shutil.copyfile(ico, os.path.join(DIST, "favicon.ico"))

    pages = sorted(glob.glob(os.path.join(SRC, "pages", "*.html")))
    names = [os.path.basename(p) for p in pages]
    os.makedirs(os.path.join(DIST, "ar"), exist_ok=True)
    page_meta = {lang: {} for lang in LANGS}  # lang -> name -> (title, desc), for llms.txt
    sources = []
    for path in pages:
        raw = open(path, encoding="utf-8-sig").read()  # utf-8-sig strips a stray BOM
        meta, body = parse_meta(raw)
        sources.append((os.path.basename(path), meta, apply_flags(body)))
    metas = {name: meta for name, meta, _ in sources}
    services = [(name, meta.get("crumb", meta.get("title")), meta["service_type"])
                for name, meta, _ in sources if meta.get("service_type")]
    teams = team_groups()

    for name, meta, body in sources:
        def team(m):
            if m.group(1) not in teams:
                raise ValueError("%s: no team group named %r on team.html" % (name, m.group(1)))
            return teams[m.group(1)]
        body = TEAM_RE.sub(team, body)

        for lang in LANGS:
            html = layout
            # cache-bust asset refs so browsers never serve a stale CSS/JS
            html = html.replace('href="styles.css"', 'href="styles.css?v=%s"' % ver["styles.css"])
            html = html.replace('src="app.js"', 'src="app.js?v=%s"' % ver["app.js"])
            # title/desc are injected into HTML attributes (og:*/description).
            # HTML-escape them so a literal " (e.g. גפ"ן) can't close the
            # attribute early and silently truncate the tag.
            title = meta.get("title", "מילים וחרוזים")
            desc = meta.get("desc", "")
            if lang == "ar":
                title, desc = meta.get("title_ar", title), meta.get("desc_ar", desc)
            page_meta[lang][name] = (title, desc)
            alt = "ar" if lang == "he" else "he"
            html = html.replace("{{LANG}}", lang)
            html = html.replace("{{TITLE}}", _esc(title))
            html = html.replace("{{DESC}}", _esc(desc))
            html = html.replace("{{SITE_NAME}}", SITE_NAME[lang])
            html = html.replace("{{OG_LOCALE}}", OG_LOCALE[lang])
            html = html.replace("{{OG_LOCALE_ALT}}", OG_LOCALE[alt])
            html = html.replace("{{CANONICAL}}", page_url(name, lang))
            html = html.replace("{{HREFLANG}}", hreflang_links(
                name, '<link rel="alternate" hreflang="%s" href="%s">\n').rstrip("\n"))
            # the language switch: plain links between the two versions
            for l in LANGS:
                html = html.replace("{{HREF_%s}}" % l.upper(), page_path(name, l))
                html = html.replace("{{ON_%s}}" % l.upper(),
                                    ' class="on" aria-current="true"' if l == lang else "")
            # a visitor who explicitly picked Arabic and later arrives at the
            # bare homepage from outside the site gets /ar/ (see app.js)
            html = html.replace("{{LANG_MEMORY}}\n", LANG_MEMORY + "\n"
                                if (lang, name) == ("he", "index.html") else "")
            html = html.replace("{{SITE_URL}}", SITE_URL)
            ld = jsonld(services) if name in ("index.html", "contact.html") else ""
            if meta.get("parent"):
                ld += breadcrumb_ld(name, lang, meta, metas)
            html = html.replace("{{JSONLD}}", ld)
            html = html.replace("{{CONTENT}}", body)

            # active nav item
            nav = meta.get("nav", "")
            if nav:
                html = html.replace(
                    'data-nav="%s"' % nav,
                    'data-nav="%s" class="active" aria-current="page"' % nav,
                )

            html = localize(html, lang, name)
            if lang == "ar":
                html = rebase_ar(html, names)
            out = os.path.join(DIST, "ar", name) if lang == "ar" else os.path.join(DIST, name)
            open(out, "w", encoding="utf-8").write(html)

    write_sitemap(names)
    write_llms(page_meta)

    print("Built %d page(s) x %d languages: %s" % (len(names), len(LANGS), ", ".join(names)))
    print("Output: %s (+ ar/, sitemap.xml, robots.txt, llms.txt, IndexNow key)" % DIST)


if __name__ == "__main__":
    build()
