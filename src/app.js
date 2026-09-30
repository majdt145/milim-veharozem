/* מילים וחרוזים — shared behavior: language switch (He/Ar) + mobile nav */
(function () {
  "use strict";

  /* Language = URL: Hebrew pages at /, Arabic at /ar/ — build.py bakes each
     language into its own static page, so nothing is swapped here. */
  var LANG = document.documentElement.lang === "ar" ? "ar" : "he";

  document.addEventListener("DOMContentLoaded", function () {
    /* language switch: remember the explicit choice (the Hebrew homepage
       honours it for visitors arriving from outside) and keep the #section */
    [].slice.call(document.querySelectorAll(".lang a[data-lang]")).forEach(function (a) {
      a.addEventListener("click", function () {
        try { localStorage.setItem("mvh_lang", a.getAttribute("data-lang")); } catch (e) {}
        if (location.hash) a.href = a.href.split("#")[0] + location.hash;
      });
    });

    /* mobile nav toggle */
    var hamb = document.querySelector(".hamb");
    var menu = document.getElementById("mainmenu");
    if (hamb && menu) {
      hamb.addEventListener("click", function () {
        var open = menu.classList.toggle("open");
        hamb.setAttribute("aria-expanded", open ? "true" : "false");
      });
      /* close menu when a link is tapped */
      menu.addEventListener("click", function (e) {
        if (e.target.tagName === "A") {
          menu.classList.remove("open");
          hamb.setAttribute("aria-expanded", "false");
        }
      });
    }

    initMotion();
    initCarousels();
    initForms();
    initNav();
  });

  /* ===== scroll-aware header: transparent ONLY at rest, solid the instant you
     scroll — so the nav never overlaps the hero text sliding underneath. The
     "hero sits behind the header" geometry lives in CSS and is always on, so we
     only toggle the header BACKGROUND here — never the layout. Fail-safe: if the
     header is missing we bail and it keeps its solid CSS default. */
  function initNav() {
    try {
      var root = document.documentElement;
      var header = document.querySelector("header.site");
      if (!header) return;

      function measure() { root.style.setProperty("--nav-h", header.offsetHeight + "px"); }
      measure();
      window.addEventListener("resize", measure, { passive: true });

      /* enable transparency, but suppress the one-time fade on first paint */
      root.classList.add("js-nav", "nav-no-anim");
      requestAnimationFrame(function () {
        requestAnimationFrame(function () { root.classList.remove("nav-no-anim"); });
      });

      /* solid as soon as the page moves off the very top (>8px); transparent at rest */
      var solid = null;
      function onScroll() {
        var y = window.scrollY || root.scrollTop || document.body.scrollTop || 0;
        var next = y > 8;
        if (next !== solid) { solid = next; header.classList.toggle("scrolled", next); }
      }
      window.addEventListener("scroll", onScroll, { passive: true });
      onScroll();
    } catch (e) {
      document.documentElement.classList.remove("js-nav");
    }
  }

  /* ===== forms: real submission to /api/form (Vercel function → Resend) ===== */
  function initForms() {
    var MAX_FILES_BYTES = 3.5 * 1024 * 1024;

    function show(form, sel) {
      [].slice.call(form.querySelectorAll(".done,.err")).forEach(function (el) { el.hidden = true; });
      var el = sel && form.querySelector(sel);
      if (el) el.hidden = false;
    }
    function setBusy(form, busy) {
      var btn = form.querySelector('button[type="submit"]');
      if (!btn) return;
      btn.disabled = busy;
      btn.setAttribute("aria-busy", busy ? "true" : "false");
      if (busy) {
        btn.__label = btn.innerHTML;  /* the page's own label, already in its language */
        btn.textContent = LANG === "ar" ? "جارٍ الإرسال…" : "שולח…";
      } else if (btn.__label != null) {
        btn.innerHTML = btn.__label;
      }
    }
    function readFiles(input) {
      var files = [].slice.call(input.files || []);
      var total = files.reduce(function (s, f) { return s + f.size; }, 0);
      if (total > MAX_FILES_BYTES) return Promise.reject("toobig");
      return Promise.all(files.map(function (f) {
        return new Promise(function (resolve, reject) {
          var r = new FileReader();
          r.onload = function () { resolve({ filename: f.name, contentBase64: String(r.result).split(",")[1] }); };
          r.onerror = function () { reject("readfail"); };
          r.readAsDataURL(f);
        });
      }));
    }

    [].slice.call(document.querySelectorAll("form[data-form]")).forEach(function (form) {
      form.addEventListener("submit", function (e) {
        e.preventDefault();
        var fields = {};
        [].slice.call(form.elements).forEach(function (el) {
          if (el.name && el.name !== "website" && el.type !== "file") fields[el.name] = el.value;
        });
        var fileInput = form.querySelector('input[type="file"]');
        var body = {
          formType: form.getAttribute("data-form"),
          lang: LANG,
          fields: fields,
          website: (form.querySelector('input[name="website"]') || {}).value || "",
        };
        setBusy(form, true);
        show(form, null);
        (fileInput ? readFiles(fileInput) : Promise.resolve([]))
          .then(function (attachments) {
            body.attachments = attachments;
            return fetch("/api/form", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(body),
            });
          })
          .then(function (r) { return r.json().catch(function () { return { ok: false }; }); })
          .then(function (data) {
            if (data.ok) { show(form, ".done"); form.reset(); }
            else if (data.error === "toobig" || data.error === "filetype") show(form, '.err[data-err="file"]');
            else show(form, '.err[data-err="send"]');
          })
          .catch(function (why) {
            show(form, why === "toobig" ? '.err[data-err="file"]' : '.err[data-err="send"]');
          })
          .then(function () { setBusy(form, false); });
      });
    });
  }

  /* ===== testimonial carousel (vanilla port of the Magic component) ===== */
  function initCarousels() {
    var reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
    [].slice.call(document.querySelectorAll("[data-carousel]")).forEach(function (c) {
      var track = c.querySelector(".carousel-track");
      if (!track) return;
      var slides = [].slice.call(track.children);
      var dots = [].slice.call(c.querySelectorAll(".dot"));
      var live = c.querySelector("[data-live]");
      var n = slides.length, i = 0, timer = null, paused = false;

      function render() {
        track.style.transform = "translateX(" + (-i * 100) + "%)";
        slides.forEach(function (s, k) { s.setAttribute("aria-hidden", k !== i ? "true" : "false"); });
        dots.forEach(function (d, k) {
          d.classList.toggle("on", k === i);
          d.setAttribute("aria-selected", k === i ? "true" : "false");
        });
        if (live) {
          live.textContent = LANG === "ar"
            ? "توصية " + (i + 1) + " من " + n
            : "המלצה " + (i + 1) + " מתוך " + n;
        }
      }
      function go(k) { i = (k + n) % n; render(); }

      var nextBtn = c.querySelector("[data-next]"), prevBtn = c.querySelector("[data-prev]");
      if (nextBtn) nextBtn.addEventListener("click", function () { go(i + 1); restart(); });
      if (prevBtn) prevBtn.addEventListener("click", function () { go(i - 1); restart(); });
      dots.forEach(function (d, k) { d.addEventListener("click", function () { go(k); restart(); }); });

      c.addEventListener("keydown", function (e) {
        if (e.key === "ArrowLeft") { e.preventDefault(); go(i + 1); restart(); }   /* RTL: left = forward */
        else if (e.key === "ArrowRight") { e.preventDefault(); go(i - 1); restart(); }
      });

      function start() { if (reduce || n < 2) return; stop(); timer = setInterval(function () { if (!paused) go(i + 1); }, 5000); }
      function stop() { if (timer) { clearInterval(timer); timer = null; } }
      function restart() { stop(); start(); }
      c.addEventListener("mouseenter", function () { paused = true; });
      c.addEventListener("mouseleave", function () { paused = false; });
      c.addEventListener("focusin", function () { paused = true; });
      c.addEventListener("focusout", function () { paused = false; });

      render();
      start();
    });
  }


  /* ===== motion layer: scroll-reveal, count-up, scroll bar, parallax ===== */
  function initMotion() {
    var root = document.documentElement;
    if (!root.classList.contains("anim")) return;
    try {

      var SEL = ".sec-head,.svc-piece,.ws-flyer,.jb-badge,.ct-stop,.step,.tst,.age-c,.why-item,.acc,.group-head,.partners,.ass-grid .pill";
      var els = [].slice.call(document.querySelectorAll(SEL));

      /* scroll-based reveal — shows in-view content immediately; no IntersectionObserver dependency */
      function reveal() {
        var vh = window.innerHeight || document.documentElement.clientHeight;
        els.forEach(function (el) {
          if (el.__shown) return;
          var r = el.getBoundingClientRect();
          if (r.top < vh * 0.92 && r.bottom > 0) {
            var sibs = el.parentNode ? [].slice.call(el.parentNode.children).filter(function (c) { return c.matches && c.matches(SEL) && !c.__shown; }) : [];
            el.style.animationDelay = Math.max(0, sibs.indexOf(el)) * 55 + "ms";
            el.classList.add("is-in");
            el.__shown = true;
          }
        });
      }

      /* count-up stats (skip year-like numbers) */
      var meta = document.querySelector(".hero-meta"), counted = false;
      function countUp() {
        if (counted || !meta) return;
        if (meta.getBoundingClientRect().top > (window.innerHeight || 800)) return;
        counted = true;
        [].slice.call(meta.querySelectorAll("b")).forEach(function (b) {
          var m = b.textContent.trim().match(/(\+?)(\d+)/); if (!m) return;
          var pre = m[1], target = parseInt(m[2], 10); if (target >= 1900) return; /* year — leave it */
          var t0 = null, dur = 1100; b.textContent = pre + "0";
          (function step(t) {
            if (!t0) t0 = t;
            var p = Math.min(1, (t - t0) / dur);
            b.textContent = pre + Math.round(target * (1 - Math.pow(1 - p, 3)));
            if (p < 1) requestAnimationFrame(step); else b.textContent = pre + target;
          })(performance.now ? performance.now() : Date.now());
        });
      }

      /* scroll progress bar */
      var bar = document.createElement("div");
      bar.className = "scrollbar";
      bar.setAttribute("aria-hidden", "true");
      document.body.appendChild(bar);

      /* parallax on CTA background photos + drive reveal/count-up each frame */
      var bgs = [].slice.call(document.querySelectorAll(".cta .bg"));
      var ticking = false;
      function frame() {
        var h = document.documentElement;
        var max = h.scrollHeight - h.clientHeight;
        bar.style.transform = "scaleX(" + (max > 0 ? h.scrollTop / max : 0) + ")";
        bgs.forEach(function (img) {
          var r = img.parentNode.getBoundingClientRect();
          if (r.bottom < 0 || r.top > window.innerHeight) return;
          var frac = (window.innerHeight - r.top) / (window.innerHeight + r.height);
          img.style.transform = "translateY(" + (frac - 0.5) * 60 + "px)";
        });
        reveal();
        countUp();
        ticking = false;
      }
      function onScroll() { if (!ticking) { ticking = true; requestAnimationFrame(frame); } }
      window.addEventListener("scroll", onScroll, { passive: true });
      window.addEventListener("resize", onScroll, { passive: true });
      window.addEventListener("load", frame);
      /* initial passes catch late layout/font shifts */
      frame(); setTimeout(frame, 150); setTimeout(frame, 600);
      /* hard failsafe — never leave any section hidden */
      setTimeout(function () { els.forEach(function (el) { if (!el.__shown) { el.classList.add("is-in"); el.__shown = true; } }); }, 2800);
    } catch (err) {
      /* anything goes wrong → reveal everything, no broken hidden content */
      root.classList.remove("anim");
    }
  }
})();

/* =========================================================================
   Accessibility widget (aw-) + Cookie banner (ck-)
   Self-contained IIFE with its own try/catch so a failure here can NEVER
   break the site's core JS above. Fail-open: button just stays inert,
   banner stays hidden (it's hidden-by-default in the HTML).
   ========================================================================= */
(function () {
  "use strict";
  try {
    var KEY = "mv-a11y", CKEY = "mv-consent";
    var DEFAULTS = { fs: 0, dark: false, gray: false, links: false, spacing: false, stopmotion: false };
    var BOOL = ["dark", "gray", "links", "spacing", "stopmotion"];
    var FS_PCT = ["100%", "112%", "125%"];

    function read() {
      try {
        var s = JSON.parse(localStorage.getItem(KEY) || "{}");
        var out = {}; for (var k in DEFAULTS) out[k] = (k in s) ? s[k] : DEFAULTS[k];
        out.fs = Math.max(0, Math.min(2, out.fs | 0));
        return out;
      } catch (e) { var d = {}; for (var j in DEFAULTS) d[j] = DEFAULTS[j]; return d; }
    }
    function save(s) { try { localStorage.setItem(KEY, JSON.stringify(s)); } catch (e) {} }

    /* apply state → classes on <html>, keeping the pre-paint script in sync */
    function apply(s) {
      var h = document.documentElement;
      h.classList.remove("aw-fs1", "aw-fs2", "aw-dark", "aw-gray", "aw-links", "aw-spacing", "aw-stopmotion");
      if (s.fs === 1) h.classList.add("aw-fs1");
      if (s.fs === 2) h.classList.add("aw-fs2");
      if (s.dark) h.classList.add("aw-dark");
      if (s.gray) h.classList.add("aw-gray");
      if (s.links) h.classList.add("aw-links");
      if (s.spacing) h.classList.add("aw-spacing");
      if (s.stopmotion) {
        h.classList.add("aw-stopmotion");
        h.classList.remove("anim");   /* stop JS-gated motion too */
        pauseMedia(true);
      } else {
        pauseMedia(false);
      }
    }

    /* pause/resume any hero (or other) <video> when motion is stopped */
    function pauseMedia(stop) {
      try {
        [].slice.call(document.querySelectorAll("video")).forEach(function (v) {
          if (stop) { try { v.pause(); } catch (e) {} }
          else if (v.autoplay && v.paused) { try { v.play().catch(function () {}); } catch (e) {} }
        });
      } catch (e) {}
    }

    document.addEventListener("DOMContentLoaded", function () {
      try {
        initWidget();
        initCookie();
      } catch (e) { /* fail-open: leave the page fully usable */ }
    });

    function initWidget() {
      var btn = document.getElementById("aw-btn");
      var panel = document.getElementById("aw-panel");
      if (!btn || !panel) return;
      var title = document.getElementById("aw-title");
      var closeBtn = document.getElementById("aw-close");
      var state = read();

      /* reflect saved state into the panel controls + apply to <html> */
      apply(state);
      renderControls();

      function renderControls() {
        /* text-size stepper */
        var val = document.getElementById("aw-fs-val");
        if (val) val.textContent = FS_PCT[state.fs];
        var dn = document.getElementById("aw-fs-dn"), up = document.getElementById("aw-fs-up");
        if (dn) dn.disabled = state.fs <= 0;
        if (up) up.disabled = state.fs >= 2;
        /* switches */
        [].slice.call(panel.querySelectorAll(".aw-switch")).forEach(function (sw) {
          var k = sw.getAttribute("data-set");
          sw.setAttribute("aria-checked", state[k] ? "true" : "false");
        });
      }

      function commit() { save(state); apply(state); renderControls(); }

      /* ---- open / close ---- */
      var open = false;
      function openPanel() {
        panel.hidden = false;
        btn.setAttribute("aria-expanded", "true");
        open = true;
        if (title) title.focus();
        document.addEventListener("keydown", onKey);
        document.addEventListener("mousedown", onOutside);
      }
      function closePanel(returnFocus) {
        panel.hidden = true;
        btn.setAttribute("aria-expanded", "false");
        open = false;
        document.removeEventListener("keydown", onKey);
        document.removeEventListener("mousedown", onOutside);
        if (returnFocus !== false) btn.focus();
      }
      function onKey(e) {
        if (e.key === "Escape") { e.preventDefault(); closePanel(true); }
      }
      function onOutside(e) {
        if (!open) return;
        if (panel.contains(e.target) || btn.contains(e.target)) return;
        closePanel(false);
      }

      btn.addEventListener("click", function () { open ? closePanel(true) : openPanel(); });
      if (closeBtn) closeBtn.addEventListener("click", function () { closePanel(true); });

      /* ---- text size ---- */
      var dn = document.getElementById("aw-fs-dn"), up = document.getElementById("aw-fs-up");
      if (dn) dn.addEventListener("click", function () { if (state.fs > 0) { state.fs--; commit(); } });
      if (up) up.addEventListener("click", function () { if (state.fs < 2) { state.fs++; commit(); } });

      /* ---- toggles ---- */
      [].slice.call(panel.querySelectorAll(".aw-switch")).forEach(function (sw) {
        sw.addEventListener("click", function () {
          var k = sw.getAttribute("data-set");
          state[k] = !state[k];
          commit();
        });
      });

      /* ---- reset ---- */
      var reset = document.getElementById("aw-reset");
      if (reset) reset.addEventListener("click", function () {
        state = {}; for (var k in DEFAULTS) state[k] = DEFAULTS[k];
        try { localStorage.removeItem(KEY); } catch (e) {}
        /* restore motion class if the environment allows it */
        try {
          if (window.matchMedia && !matchMedia("(prefers-reduced-motion:reduce)").matches) {
            document.documentElement.classList.add("anim");
          }
        } catch (e) {}
        apply(state); renderControls();
      });
    }

    function initCookie() {
      var banner = document.getElementById("ck-banner");
      if (!banner) return;
      var seen = false;
      try { seen = !!localStorage.getItem(CKEY); } catch (e) { seen = true; /* no storage → don't nag */ }
      if (seen) return;                       /* already consented → stay hidden */
      banner.hidden = false;                  /* show only on first visit; no focus steal */
      var accept = document.getElementById("ck-accept");
      if (accept) accept.addEventListener("click", function () {
        try { localStorage.setItem(CKEY, "1"); } catch (e) {}
        banner.hidden = true;
      });
    }
  } catch (e) { /* widget/banner disabled; site remains fully usable */ }
})();
