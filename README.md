# מילים וחרוזים — Website

Static, bilingual (Hebrew / Arabic, RTL) website for the **מילים וחרוזים** child-development clinic
(branches: Akko · Mazra'a · Majdal Shams). No framework, no Node — a tiny Python generator wraps page
content in a shared layout. Output is plain static HTML, deployable on any free host (Netlify, GitHub
Pages, etc.) and portable into any platform.

## Structure
```
src/
  layout.html        shared shell: <head>, utility bar, header/nav, footer, mobile bar
  styles.css         the whole design system (brand tokens + components)
  app.js             language toggle (He/Ar, saved to localStorage) + mobile nav
  pages/*.html       one file per page = just the <main> content + a <!--meta--> block
  assets/            logo.png + img/ photos
build.py             `python build.py` → writes dist/
dist/                generated site (this is what you deploy)
```

## Build & preview
```bash
python build.py
python -m http.server 8792 --directory dist   # then open http://localhost:8792
```

## Add / edit a page
1. Create `src/pages/<name>.html`.
2. Start it with a meta block:
   ```html
   <!--meta
   title: <browser tab title>
   desc:  <SEO meta description>
   nav:   <home|services|team|workshops|schools|jobs|contact>
   -->
   ```
3. Write only the page body (sections). Header/footer come from `layout.html`.
4. Run `python build.py`.

## Bilingual
Any element with `data-he` / `data-ar` swaps text when the visitor toggles language.
Default is Hebrew; choice is remembered. Both languages are RTL.

## Status (2026-06-27)
- ✅ Design system + build pipeline + **homepage** (`index.html`).
- ⬜ Pages to build next: `services` (+ assessment/treatment detail), `team`, `workshops`,
  `schools` (גפ"ן), `jobs` (דרושים — with CV upload), `contact`.

## Before launch (needs real data)
- Replace placeholder testimonials with real, consented quotes.
- Wire the contact + CV-upload forms to a real endpoint (e.g. Formspree / Netlify Forms) so
  submissions email the clinic with the job title.
- Add real team photos (label which photo = which person).
- Verify partner names are formal partnerships.
