# Launch runbook — מילים וחרוזים

Status: code is launch-ready (forms wired, SEO, a11y statement, WebP, full He/Ar parity).
Two accounts gate the launch — both are 5-minute signups done by the owner:

## 1. Vercel project (one-time)
1. Sign in at vercel.com with the GitHub account `majdt145`.
2. "Add New… → Project" → import `majdt145/milim-veharozem`.
3. Framework preset: **Other**. Build command / output dir are already in `vercel.json`
   (`python3 build.py` → `dist`) — don't override.
4. Deploy. Check the build log: if `python3` is missing, fallback = commit `dist/`
   and clear the build command.
5. The site is now at `https://milim-veharozem.vercel.app` (or similar — if the name
   differs, update `SITE_URL` in `build.py` and push).

## 2. Resend account (forms → email)
1. Create the account at resend.com **with the clinic inbox** (`melimharozem@gmail.com`)
   — free tier without a verified domain only delivers to the account's own email,
   so the account email must BE the receiving inbox.
2. Create an API key (Full access → Sending).
3. In Vercel → Project → Settings → Environment Variables add:
   - `RESEND_API_KEY` = the key
   - `FORM_TO_EMAIL` = melimharozem@gmail.com
   - `FORM_TO_JOBS_EMAIL` = melimharozemschools@gmail.com
4. Redeploy. Submit each of the 4 forms on the live site (callback ×2, workshop, job
   with a small PDF) and confirm all arrive — the job email must have the CV attached
   and the position in the subject.

## 3. Analytics
Vercel dashboard → Project → Analytics → Enable Web Analytics, then add to
`src/layout.html` before `</body>`:
`<script defer src="/_vercel/insights/script.js"></script>` and push.

## 4. Google Search Console
1. search.google.com/search-console → add property for the production URL.
2. Verify via the HTML-tag method (add the meta tag to `src/layout.html`, push).
3. Submit `sitemap.xml`.

## 5. Custom domain — `www.melimharozem.com` (connected 2026-09-28)
- Bought by the clinic at GoDaddy (the old `melimharozem.co.il` had expired).
- Vercel → Project → Settings → Domains: **`www.melimharozem.com` is primary**;
  `melimharozem.com` 308-redirects to it. `vercel.json` 308-redirects the old
  `milim-veharozem.vercel.app` there too.
- `SITE_URL` in `build.py` = `https://www.melimharozem.com` (canonicals/OG/sitemap/llms.txt).
- Search Console: URL-prefix property `https://www.melimharozem.com/`, verified by the
  HTML file `build.py` writes; submit `sitemap.xml`.
- IndexNow (Bing etc.): key in `build.py` (`INDEXNOW_KEY`); after content deploys, POST the
  changed URLs to `https://api.indexnow.org/indexnow`.
- **Done 2026-10-01:** Resend account = Majd's (`majdtannous1234`); `melimharozem.com` verified in
  region **eu-west-1 (Ireland)** via Auto configure (records in Vercel DNS: `resend._domainkey` TXT,
  `send` MX + SPF TXT). `api/form.js` sends From `forms@melimharozem.com`. Vercel env:
  `RESEND_API_KEY` + `FORM_TO_EMAIL=melimharozem@gmail.com` (Production). Before this, the project
  had NO key, so every form failed with `config` from launch until 2026-10-01.

## 6. Private-preview gate (Aug–Sep 2026, removed at launch)
To lock the site again, restore the gate from git — `git checkout b7ba8fe -- middleware.js`
(not a `>` redirect: PowerShell 5.1 would write it as UTF-16), commit, push. It is Basic Auth on every path (user `majd`), with the password in the `PREVIEW_PASS`
env var on Vercel.

## Content still owed by the clinic (all non-blocking)
| Item | Where it goes | Until then |
|---|---|---|
| Real consented testimonials | index — flip `FLAGS["TESTIMONIALS"]` in build.py + replace quotes | section hidden |
| Team photos (square, ≥600px, filename = name) | `team.html` rings → `<img>` | initials rings |
| Opening hours | JSON-LD in build.py | omitted |
| Accessibility coordinator name | accessibility.html | generic contact |

## Free-tier quotas
- Resend: 100 emails/day (plenty for a clinic site).
- Vercel Hobby: 100GB bandwidth/month.

## Maintenance
- Edit content in `src/pages/*.html` (Hebrew in `data-he`, Arabic in `data-ar`).
- Run `python tools/i18n_audit.py` after content changes — must stay CLEAN.
- Service pages (`speech-therapy.html` … `adhd-moxo.html`) are GENERATED from `services.html`: edit the text there, then `python tools/gen_service_pages.py` and `python build.py`. Their team block comes from `team.html` at build time.
- Arabic pages are built to `/ar/` (same source). Check hreflang with `python ~/.claude/skills/seo-lab/scripts/hreflang-check.py <origin>`.
- New images: drop originals anywhere, run `python tools/optimize_images.py`
  (add an entry to JOBS), reference the `.webp`.
- Every push to `main` auto-deploys.
