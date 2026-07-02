/* מילים וחרוזים — shared behavior: language toggle (He/Ar) + mobile nav */
(function () {
  "use strict";

  function applyLang(l) {
    document.querySelectorAll(".lang button").forEach(function (b) {
      b.classList.toggle("on", b.dataset.lang === l);
      b.setAttribute("aria-pressed", b.dataset.lang === l ? "true" : "false");
    });
    document.documentElement.lang = l === "ar" ? "ar" : "he";
    document.documentElement.dir = "rtl"; /* both He & Ar are RTL */
    document.querySelectorAll("[data-" + l + "]").forEach(function (el) {
      // only swap the innermost translatable node, so decorative emoji /
      // tel: links / nested spans in a container are never destroyed
      if (el.querySelector("[data-" + l + "]")) return;
      el.innerHTML = el.getAttribute("data-" + l);
    });
    document.querySelectorAll("[data-aria-" + l + "]").forEach(function (el) {
      el.setAttribute("aria-label", el.getAttribute("data-aria-" + l));
    });
    var md = document.querySelector('meta[name="description"]');
    if (md && md.getAttribute("data-desc-" + l)) md.setAttribute("content", md.getAttribute("data-desc-" + l));
    try { localStorage.setItem("mvh_lang", l); } catch (e) {}
  }

  window.setLang = function (l) { applyLang(l); };

  document.addEventListener("DOMContentLoaded", function () {
    /* restore saved language */
    var saved = "he";
    try { saved = localStorage.getItem("mvh_lang") || "he"; } catch (e) {}
    if (saved === "ar") applyLang("ar");

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
  });

  /* ===== forms: real submission to /api/form (Vercel function → Resend) ===== */
  function initForms() {
    var MAX_FILES_BYTES = 3.5 * 1024 * 1024;

    function currentLang() {
      try { return localStorage.getItem("mvh_lang") === "ar" ? "ar" : "he"; } catch (e) { return "he"; }
    }
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
      var l = currentLang();
      btn.textContent = busy
        ? (l === "ar" ? "جارٍ الإرسال…" : "שולח…")
        : (btn.getAttribute("data-" + l) || btn.getAttribute("data-he"));
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
          lang: currentLang(),
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
        if (live) live.textContent = "המלצה " + (i + 1) + " מתוך " + n;
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

      var SEL = ".sec-head,.card,.step,.tst,.branch,.member,.age-c,.why-item,.acc,.job,.prog .p,.group-head,.partners,.ass-grid .pill";
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
