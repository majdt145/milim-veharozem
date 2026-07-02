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

## 5. Custom domain (when Mostafa hands over melimharozem.co.il)
1. Vercel → Project → Settings → Domains → add `melimharozem.co.il` + `www`.
2. At the registrar, set the DNS records Vercel shows (A / CNAME).
3. Flip `SITE_URL` in `build.py` to the domain, push (regenerates canonicals/OG/sitemap).
4. Re-verify the domain property in Search Console + resubmit sitemap.
5. Resend: verify the domain, then change `From:` in `api/form.js` to
   `forms@melimharozem.co.il` (removes the onboarding@resend.dev sender).

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
- New images: drop originals anywhere, run `python tools/optimize_images.py`
  (add an entry to JOBS), reference the `.webp`.
- Every push to `main` auto-deploys.
