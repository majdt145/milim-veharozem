// מילים וחרוזים — form relay: receives site form submissions as JSON and
// emails the clinic via the Resend REST API. Zero dependencies on purpose —
// no package.json, so the repo needs no Node toolchain locally.
//
// Env vars (set in Vercel):
//   RESEND_API_KEY     — Resend secret key
//   FORM_TO_EMAIL      — inbox for callback + workshop forms
//   FORM_TO_JOBS_EMAIL — inbox for job applications (falls back to FORM_TO_EMAIL)

const MAX_ATTACH_BYTES = 3.5 * 1024 * 1024; // total, decoded — stays under Vercel's 4.5MB body cap
const ALLOWED_EXT = /\.(pdf|doc|docx|jpg|jpeg|png)$/i;

const SUBJECTS = {
  callback: (f) => `פנייה חדשה מהאתר — ${f.name} (${f.branch || "לא צוין סניף"})`,
  workshop: (f) => `בקשת סדנה — ${f.name}`,
  job: (f) => `מועמדות: ${f.position || "לא צוין תפקיד"} — ${f.name}`,
};

const FIELD_LABELS = {
  name: "שם",
  phone: "טלפון",
  branch: "סניף",
  message: "הודעה",
  position: "תפקיד",
  email: "דוא״ל",
};

function esc(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

function renderHtml(formType, fields, lang) {
  const rows = Object.entries(fields)
    .filter(([k, v]) => v && FIELD_LABELS[k])
    .map(([k, v]) =>
      `<tr><td style="padding:6px 10px;font-weight:bold;white-space:nowrap">${FIELD_LABELS[k]}</td>` +
      `<td style="padding:6px 10px">${esc(v)}</td></tr>`)
    .join("");
  const typeLine = { callback: "טופס חזרו אליי", workshop: "טופס בקשת סדנה", job: "טופס מועמדות (דרושים)" }[formType];
  return `<div dir="rtl" style="font-family:Arial,sans-serif;font-size:15px;color:#34282f">
    <p><b>${typeLine}</b> · שפת הגולש: ${lang === "ar" ? "ערבית" : "עברית"}</p>
    <table style="border-collapse:collapse;background:#faf5ef;border-radius:8px">${rows}</table>
    <p style="color:#6f636a;font-size:12px">נשלח אוטומטית מהאתר milim-veharozem</p>
  </div>`;
}

module.exports = async (req, res) => {
  if (req.method !== "POST") {
    res.status(405).json({ ok: false, error: "method" });
    return;
  }
  try {
    const { formType, lang, fields = {}, attachments = [], website } = req.body || {};

    // honeypot: the hidden "website" input must stay empty; bots fill it.
    // Pretend success so bots don't adapt.
    if (website) { res.status(200).json({ ok: true }); return; }

    if (!SUBJECTS[formType]) { res.status(400).json({ ok: false, error: "type" }); return; }
    if (!fields.name || !fields.phone) { res.status(400).json({ ok: false, error: "fields" }); return; }

    let files = [];
    if (formType === "job") {
      let total = 0;
      for (const a of attachments) {
        if (!a || !a.filename || !a.contentBase64) continue;
        if (!ALLOWED_EXT.test(a.filename)) { res.status(400).json({ ok: false, error: "filetype" }); return; }
        total += Math.floor(a.contentBase64.length * 0.75);
        if (total > MAX_ATTACH_BYTES) { res.status(400).json({ ok: false, error: "toobig" }); return; }
        files.push({ filename: a.filename, content: a.contentBase64 });
      }
      if (files.length === 0) { res.status(400).json({ ok: false, error: "nofile" }); return; }
    }

    const to = formType === "job"
      ? (process.env.FORM_TO_JOBS_EMAIL || process.env.FORM_TO_EMAIL)
      : process.env.FORM_TO_EMAIL;
    if (!process.env.RESEND_API_KEY || !to) {
      res.status(500).json({ ok: false, error: "config" });
      return;
    }

    const payload = {
      from: "אתר מילים וחרוזים <onboarding@resend.dev>", // switch to forms@<domain> after domain verify (see docs/launch.md)
      to: [to],
      subject: SUBJECTS[formType](fields),
      html: renderHtml(formType, fields, lang),
      ...(fields.email ? { reply_to: fields.email } : {}),
      ...(files.length ? { attachments: files } : {}),
    };

    const r = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${process.env.RESEND_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!r.ok) {
      const detail = await r.text().catch(() => "");
      console.error("resend error", r.status, detail.slice(0, 300));
      res.status(502).json({ ok: false, error: "send" });
      return;
    }
    res.status(200).json({ ok: true });
  } catch (e) {
    console.error("form handler error", e && e.message);
    res.status(500).json({ ok: false, error: "server" });
  }
};
