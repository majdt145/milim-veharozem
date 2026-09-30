# -*- coding: utf-8 -*-
"""Generate the 8 service pages (src/pages/<slug>.html), one per service.

Every body text is copied VERBATIM (raw attribute strings) from
src/pages/services.html (the clinic's wording) and workshops.html; only the
headings, titles/descriptions and the branch/CTA lines live here (in P).
The team block comes from team.html at build time (<!--TEAM:…--> in build.py).

services.html stays the single source for the service texts: after editing a
text there, re-run  python tools/gen_service_pages.py  then  python build.py.
Don't hand-edit the 8 generated pages (a re-run overwrites them)."""
import io, os, re

PAGES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "pages")
svc = io.open(os.path.join(PAGES, "services.html"), encoding="utf-8-sig").read()
wsh = io.open(os.path.join(PAGES, "workshops.html"), encoding="utf-8-sig").read()

# ---- treatments: 6 .svc-piece blocks, in page order ----
T = []
for block in re.findall(r'<div class="svc-piece (svc-t-\w+)">(.*?)</a>\s*</div>', svc, re.S):
    tint, b = block
    h3 = re.search(r'<h3><a href="[^"]*" data-he="([^"]*)" data-ar="([^"]*)"', b)
    p = re.search(r'</h3>\s*<p data-he="([^"]*)" data-ar="([^"]*)"', b)
    fit = re.search(r'class="rvs-fit">.*?<span data-he="([^"]*)" data-ar="([^"]*)"', b, re.S)
    T.append(dict(tint=tint, name=(h3.group(1), h3.group(2)), p=(p.group(1), p.group(2)),
                  fit=(fit.group(1), fit.group(2))))
# ---- assessments: 7 accordions ----
A = []
for b in re.findall(r'<details class="acc svc-acc svc-a\d">(.*?)</details>', svc, re.S):
    spans = re.findall(r'<span (?:class="tag" )?data-he="([^"]*)" data-ar="([^"]*)"', b)
    body = re.search(r'<div class="body"><p data-he="([^"]*)" data-ar="([^"]*)"', b)
    A.append(dict(name=spans[0], tag=spans[1], body=(body.group(1), body.group(2))))
assert len(T) == 6 and len(A) == 7, (len(T), len(A))
W = {he: ar for he, ar in re.findall(r'<h3 data-he="([^"]*)" data-ar="([^"]*)"', wsh)}

TOWNS_HE = "בעכו, מזרעה, שעב ומג'דל שמס"
TOWNS_AR = "في عكا، المزرعة، شعب ومجدل شمس"
BR = [("עכו", "عكا"), ("מזרעה", "المزرعة"), ("שעב", "شعب"), ("מג'דל שמס", "مجدل شمس")]

# slug: crumb, h1, lead, blocks, team group, workshops, related, service_type, title/desc
P = {
 "speech-therapy.html": dict(
   crumb=("קלינאות תקשורת", "علاج النطق"),
   h1=("קלינאות תקשורת לילדים", "علاج النطق للأطفال"),
   lead=T[0]["p"], blocks=[("t", 0), ("a", 0)], team="קלינאות תקשורת", ws=[],
   stype="MedicalTherapy",
   title=("קלינאית תקשורת לילדים " + TOWNS_HE + " | מילים וחרוזים",
          "علاج النطق للأطفال " + TOWNS_AR + " | ميليم وحاروزيم"),
   desc=("אבחון וטיפול בקלינאות תקשורת מלידה ועד גיל 18: איחור שפתי, היגוי, שטף דיבור, קול ותקשורת, כולל ליווי הורים. סניפים בעכו, מזרעה, שעב ומג'דל שמס.",
         "تشخيص وعلاج النطق من الولادة حتى عمر 18: تأخّر لغوي، نطق، طلاقة كلام، صوت وتواصل، مع مرافقة الأهل. فروع في عكا، المزرعة، شعب ومجدل شمس.")),
 "occupational-therapy.html": dict(
   crumb=("ריפוי בעיסוק", "العلاج الوظيفي"),
   h1=("ריפוי בעיסוק לילדים", "العلاج الوظيفي للأطفال"),
   lead=T[1]["p"], blocks=[("t", 1), ("a", 1)], team="ריפוי בעיסוק",
   ws=["מוכנות לכיתה א׳", "סדנאות כתיבה"], stype="MedicalTherapy",
   title=("ריפוי בעיסוק לילדים " + TOWNS_HE + " | מילים וחרוזים",
          "العلاج الوظيفي للأطفال " + TOWNS_AR + " | ميليم وحاروزيم"),
   desc=("אבחון וטיפול בריפוי בעיסוק מלידה ועד גיל 18: מוטוריקה עדינה וגסה, גרפומוטוריקה, ויסות חושי, קשיי כתיבה ומוכנות לכיתה א׳. סניפים בעכו, מזרעה, שעב ומג'דל שמס.",
         "تشخيص وعلاج وظيفي من الولادة حتى عمر 18: حركة دقيقة وكبيرة، الكتابة، التنظيم الحسّي والاستعداد للصف الأول. فروع في عكا، المزرعة، شعب ومجدل شمس.")),
 "physiotherapy.html": dict(
   crumb=("פיזיותרפיה התפתחותית", "علاج طبيعي تطوّري"),
   h1=("פיזיותרפיה התפתחותית לתינוקות וילדים", "علاج طبيعي تطوّري للرضّع والأطفال"),
   lead=T[2]["p"], blocks=[("t", 2)], team="פיזיותרפיה",
   ws=["פיזיותרפיה לגיל הרך", "עיסוי תינוקות"], stype="MedicalTherapy",
   title=("פיזיותרפיה התפתחותית לתינוקות וילדים " + TOWNS_HE + " | מילים וחרוזים",
          "علاج طبيعي تطوّري للرضّع والأطفال " + TOWNS_AR + " | ميليم وحاروزيم"),
   desc=("פיזיותרפיה התפתחותית לתינוקות ופעוטות: עיכוב מוטורי, אבני דרך, חיזוק ויציבה, וליווי הורים. סדנאות פיזיותרפיה לגיל הרך ועיסוי תינוקות. עכו, מזרעה, שעב ומג'דל שמס.",
         "علاج طبيعي تطوّري للرضّع والأطفال: تأخّر حركي، مراحل نموّ، تقوية وقوام ومرافقة الأهل. ورشات علاج طبيعي للطفولة المبكرة وتدليك الرضّع. عكا، المزرعة، شعب ومجدل شمس.")),
 "psychology.html": dict(
   crumb=("טיפול ואבחון פסיכולוגי", "علاج وتشخيص نفسي"),
   h1=("טיפול ואבחון פסיכולוגי לילדים ובני נוער", "علاج وتشخيص نفسي للأطفال والمراهقين"),
   lead=T[3]["p"], blocks=[("t", 3), ("a", 4)], team="פסיכולוגיה", ws=[],
   stype="MedicalTherapy",
   title=("טיפול ואבחון פסיכולוגי לילדים " + TOWNS_HE + " | מילים וחרוזים",
          "علاج وتشخيص نفسي للأطفال " + TOWNS_AR + " | ميليم وحاروزيم"),
   desc=("טיפול פסיכולוגי לילדים ובני נוער — רגשי, נפשי והתנהגותי, טיפולים דיאדיים והדרכת הורים — ואבחון פסיכו-דיאגנוסטי. סניפים בעכו, מזרעה, שעב ומג'דל שמס.",
         "علاج نفسي للأطفال والمراهقين — عاطفي ونفسي وسلوكي، علاجات ثنائية وإرشاد الأهل — وتشخيص نفسي-تشخيصي. فروع في عكا، المزرعة، شعب ومجدل شمس.")),
 "emotional-therapy.html": dict(
   crumb=("טיפול רגשי ועבודה סוציאלית", "علاج عاطفي وعمل اجتماعي"),
   h1=("טיפול רגשי, טיפול באומנות ועבודה סוציאלית", "علاج عاطفي، علاج بالفنون وعمل اجتماعي"),
   lead=T[4]["p"], blocks=[("t", 4), ("t", 5)], team="עבודה סוציאלית וטיפול רגשי", ws=[],
   stype="MedicalTherapy",
   title=("טיפול רגשי ובאומנות והדרכת הורים " + TOWNS_HE + " | מילים וחרוזים",
          "علاج عاطفي وبالفنون وإرشاد الأهل " + TOWNS_AR + " | ميليم وحاروزيم"),
   desc=("פסיכותרפיה במשחק, טיפול באומנות וטיפול רגשי-התנהגותי, וליווי משפחות, הדרכת הורים וקבוצות טיפוליות בידי עובדות סוציאליות. עכו, מזרעה, שעב ומג'דל שמס.",
         "علاج نفسي باللعب، علاج بالفنون وعلاج عاطفي سلوكي، ومرافقة العائلات وإرشاد الأهل ومجموعات علاجية. عكا، المزرعة، شعب ومجدل شمس.")),
 "learning-assessment.html": dict(
   crumb=("אבחון דידקטי ופסיכו-דידקטי", "تشخيص ديداكتي ونفسي-ديداكتي"),
   h1=("אבחון דידקטי ופסיכו-דידקטי", "تشخيص ديداكتي ونفسي-ديداكتي"),
   lead=("אבחונים לזיהוי לקויות למידה ומקורות הקושי בלמידה — עם המלצות להתאמות ולהמשך.",
         "تشخيصات لتحديد صعوبات التعلّم ومصادر الصعوبة في التعلّم — مع توصيات للملاءمات وللاستمرار."),
   blocks=[("a", 2), ("a", 3)], team=None, ws=[], stype="MedicalTest",
   title=("אבחון דידקטי ופסיכו-דידקטי — לקויות למידה " + TOWNS_HE + " | מילים וחרוזים",
          "تشخيص ديداكتي ونفسي-ديداكتي — صعوبات تعلّم " + TOWNS_AR + " | ميليم وحاروزيم"),
   desc=("אבחון דידקטי ואבחון פסיכו-דידקטי: קריאה, כתיבה, הבנת הנקרא וחשבון, יכולות קוגניטיביות, והמלצות להתאמות בדרכי היבחנות. עכו, מזרעה, שעב ומג'דל שמס.",
         "تشخيص ديداكتي ونفسي-ديداكتي: القراءة والكتابة والفهم المقروء والحساب، القدرات الإدراكية، وتوصيات لملاءمات في طرق الامتحان. عكا، المزرعة، شعب ومجدل شمس.")),
 "autism-assessment.html": dict(
   crumb=("אבחון ASD (אוטיזם)", "تشخيص التوحّد ASD"),
   h1=("אבחון ASD (אוטיזם) לילדים", "تشخيص التوحّد (ASD) للأطفال"),
   lead=("אבחון פסיכולוגי התפתחותי לבדיקת מאפיינים של הפרעה בספקטרום האוטיזם, בכלים סטנדרטיים כמו ADOS.",
         "تشخيص نفسي تطوّري لفحص سمات اضطراب طيف التوحّد، بأدوات معيارية مثل ADOS."),
   blocks=[("a", 5)], team=None, ws=[], stype="MedicalTest",
   title=("אבחון אוטיזם (ASD) לילדים " + TOWNS_HE + " | מילים וחרוזים",
          "تشخيص التوحّد (ASD) للأطفال " + TOWNS_AR + " | ميليم وحاروزيم"),
   desc=("אבחון ASD (אוטיזם) בידי פסיכולוג התפתחותי: הערכה חברתית, תקשורתית, רגשית והתנהגותית, כלי ADOS, ראיון הורים ומידע מהמסגרת החינוכית. עכו, מזרעה, שעב ומג'דל שמס.",
         "تشخيص التوحّد (ASD) لدى أخصائي نفسي تطوّري: تقييم اجتماعي وتواصلي وعاطفي وسلوكي، أداة ADOS، مقابلة الأهل ومعلومات من الإطار التربوي. عكا، المزرعة، شعب ومجدل شمس.")),
 "adhd-moxo.html": dict(
   crumb=("אבחון קשב וריכוז MOXO", "تشخيص الانتباه والتركيز MOXO"),
   h1=("בדיקת קשב וריכוז MOXO", "فحص الانتباه والتركيز MOXO"),
   lead=("בדיקה ממוחשבת של כ-15–20 דקות להערכת קשב וריכוז (ADHD), ככלי עזר בתוך תהליך אבחוני רחב.",
         "فحص محوسب يستغرق نحو 15–20 دقيقة لتقييم الانتباه والتركيز (ADHD)، كأداة مساعدة ضمن عملية تشخيصية أوسع."),
   blocks=[("a", 6)], team=None, ws=[], stype="MedicalTest",
   title=("בדיקת קשב וריכוז MOXO (ADHD) " + TOWNS_HE + " | מילים וחרוזים",
          "فحص الانتباه والتركيز MOXO (ADHD) " + TOWNS_AR + " | ميليم وحاروزيم"),
   desc=("בדיקת MOXO ממוחשבת להערכת קשב וריכוז: קשב, תזמון, אימפולסיביות והיפראקטיביות. כ-15–20 דקות, תוצאה מיידית — כלי עזר, לא אבחנה מלאה ל-ADHD.",
         "فحص MOXO محوسب لتقييم الانتباه والتركيز: الانتباه، التوقيت، الاندفاعية وفرط الحركة. نحو 15–20 دقيقة ونتيجة فورية — أداة مساعدة وليس تشخيصًا كاملًا لـ ADHD.")),
}

def esc(s):  # for NEW strings only (copied strings are already attribute-escaped)
    return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")

def t(he, ar, tag="span", cls="", raw=False):
    """a translatable node; raw=True means he/ar are already attribute-escaped"""
    h, a = (he, ar) if raw else (esc(he), esc(ar))
    c = ' class="%s"' % cls if cls else ""
    return '<%s%s data-he="%s" data-ar="%s">%s</%s>' % (tag, c, h, a, h, tag)

WA_SVG = re.search(r'(<svg viewBox="0 0 24 24" aria-hidden="true" style="width:19px;height:19px;fill:currentColor">.*?</svg>)', svc, re.S).group(1)
HEART = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.6l-1-1a5.5 5.5 0 1 0-7.8 7.8l1 1L12 21l7.8-7.8 1-1a5.5 5.5 0 0 0 0-7.8z"/></svg>'
CTA = re.search(r'(<!-- CTA -->.*</section>)', svc, re.S).group(1)

def page(slug, d):
    out = []
    out.append("<!--meta\ntitle: %s\ntitle_ar: %s\ndesc: %s\ndesc_ar: %s\nnav: services\ncrumb: %s\ncrumb_ar: %s\nparent: services.html\nservice_type: %s\n-->\n"
               % (d["title"][0], d["title"][1], d["desc"][0], d["desc"][1], d["crumb"][0], d["crumb"][1], d["stype"]))
    lead_raw = d["lead"] is T[0]["p"] or any(d["lead"] is x["p"] for x in T)
    out.append('<section class="phero"><div class="wrap">\n'
               '  <div class="crumb">%s › %s › %s</div>\n'
               '  %s\n  %s\n'
               '  <div class="hero-cta svd-cta">\n'
               '    <a href="contact.html" class="btn btn-gold" data-he="לקביעת אבחון / התייעצות ›" data-ar="لحجز تشخيص / استشارة ›">לקביעת אבחון / התייעצות ›</a>\n'
               '    <a href="https://wa.me/972506571203" class="btn btn-wa">%s <span data-he="וואטסאפ" data-ar="واتساب">וואטסאפ</span></a>\n'
               '  </div>\n</div></section>\n'
               % ('<a href="index.html" data-he="בית" data-ar="الرئيسية">בית</a>',
                  '<a href="services.html" data-he="השירותים שלנו" data-ar="خدماتنا">השירותים שלנו</a>',
                  t(*d["crumb"]), t(*d["h1"], tag="h1"), t(*d["lead"], tag="p", raw=lead_raw), WA_SVG))
    out.append('<div class="slg-band" role="note">%s<span data-he="הדרך להתפתחות הילד מתחילה בהורה." data-ar="طريق تطوّر الطفل يبدأ من الأهل.">הדרך להתפתחות הילד מתחילה בהורה.</span></div>\n' % HEART)
    blocks = []
    tint_default = T[{"speech-therapy.html": 0, "occupational-therapy.html": 1, "physiotherapy.html": 2,
                      "psychology.html": 3, "emotional-therapy.html": 4}.get(slug, 0)]["tint"]
    for kind, i in d["blocks"]:
        if kind == "t":
            x = T[i]
            blocks.append('    <article class="svd-block %s">\n      %s\n      %s\n      <p class="svd-fit"><b data-he="למי זה מתאים?" data-ar="لمن يناسب؟">למי זה מתאים?</b> %s</p>\n      <span class="svc-age" data-he="מלידה עד גיל 18" data-ar="من الولادة حتى عمر 18">מלידה עד גיל 18</span>\n    </article>'
                          % (x["tint"], t(*x["name"], tag="h2", raw=True), t(*x["p"], tag="p", raw=True), t(*x["fit"], raw=True)))
        else:
            x = A[i]
            blocks.append('    <article class="svd-block %s">\n      <h2>%s %s</h2>\n      %s\n    </article>'
                          % (tint_default, t(*x["name"], raw=True), t(*x["tag"], cls="svd-tag", raw=True), t(*x["body"], tag="p", raw=True)))
    side = ['    <div class="svd-card">\n      <h2 class="svd-h" data-he="הסניפים שלנו" data-ar="فروعنا">הסניפים שלנו</h2>\n'
            '      <p data-he="ארבעה סניפים בצפון — צרו קשר ונתאם לכם את הסניף והמועד המתאימים." data-ar="أربعة فروع في الشمال — تواصلوا معنا وننسّق لكم الفرع والموعد المناسبين.">ארבעה סניפים בצפון — צרו קשר ונתאם לכם את הסניף והמועד המתאימים.</p>\n'
            '      <ul class="svd-branches">%s</ul>\n'
            '      <a href="contact.html" class="btn btn-gold" data-he="קביעת תור ›" data-ar="حجز موعد ›">קביעת תור ›</a>\n'
            '      <a class="svd-tel" href="tel:0506571203" dir="ltr">050-657-1203</a>\n    </div>'
            % "".join('<li><a href="contact.html">%s</a></li>' % t(he, ar) for he, ar in BR)]
    if d["ws"]:
        side.append('    <div class="svd-card">\n      <h2 class="svd-h" data-he="סדנאות בתחום" data-ar="ورشات في هذا المجال">סדנאות בתחום</h2>\n      <ul class="svd-links">%s</ul>\n    </div>'
                    % "".join('<li><a href="workshops.html">%s</a></li>' % t(w, W[w], raw=True) for w in d["ws"]))
    out.append('<section class="svd"><div class="wrap svd-grid">\n  <div class="svd-main">\n%s\n  </div>\n  <aside class="svd-side">\n%s\n  </aside>\n</div></section>\n'
               % ("\n".join(blocks), "\n".join(side)))
    if d["team"]:
        out.append('<section class="tm-page svd-team"><div class="wrap">\n'
                   '  <p class="svd-kicker" data-he="הצוות שלנו בתחום" data-ar="فريقنا في هذا المجال">הצוות שלנו בתחום</p>\n'
                   '  <!--TEAM:%s-->\n'
                   '  <p class="svd-more"><a href="team.html" data-he="לכל הצוות ›" data-ar="كل الفريق ›">לכל הצוות ›</a></p>\n'
                   '</div></section>\n' % d["team"])
    rel = [(s, P[s]["crumb"]) for s in P if s != slug]
    out.append('<section class="svd-related"><div class="wrap">\n  <h2 data-he="שירותים נוספים" data-ar="خدمات أخرى">שירותים נוספים</h2>\n  <div class="svd-chips">%s</div>\n</div></section>\n'
               % "".join('<a href="%s">%s</a>' % (s, t(*c)) for s, c in rel))
    out.append("\n" + CTA + "\n")
    return "".join(out)

for slug, d in P.items():
    io.open(os.path.join(PAGES, slug), "w", encoding="utf-8", newline="\n").write(page(slug, d))
print("wrote", len(P), "pages:", ", ".join(P))
