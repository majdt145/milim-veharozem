/* מילים וחרוזים — shared behavior: language toggle (He/Ar) + mobile nav */
(function () {
  "use strict";

  function applyLang(l) {
    document.querySelectorAll(".lang button").forEach(function (b) {
      b.classList.toggle("on", b.dataset.lang === l);
    });
    document.documentElement.lang = l === "ar" ? "ar" : "he";
    document.documentElement.dir = "rtl"; /* both He & Ar are RTL */
    document.querySelectorAll("[data-" + l + "]").forEach(function (el) {
      // only swap the innermost translatable node, so decorative emoji /
      // tel: links / nested spans in a container are never destroyed
      if (el.querySelector("[data-" + l + "]")) return;
      el.innerHTML = el.getAttribute("data-" + l);
    });
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
  });

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
    if (!root.classList.contains("anim") || !("IntersectionObserver" in window)) return;
    try {
      var SEL =
        ".sec-head,.card,.step,.tst,.branch,.member,.age-c,.why-item,.acc,.job,.prog .p,.group-head,.partners,.ass-grid .pill";

      /* staggered reveal */
      var io = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (e) {
            if (!e.isIntersecting) return;
            var el = e.target;
            var sibs = el.parentNode
              ? [].slice.call(el.parentNode.children).filter(function (c) { return c.matches && c.matches(SEL); })
              : [];
            var idx = sibs.indexOf(el);
            el.style.transitionDelay = Math.max(0, idx) * 55 + "ms";
            el.classList.add("is-in");
            io.unobserve(el);
          });
        },
        { threshold: 0.12, rootMargin: "0px 0px -7% 0px" }
      );
      [].slice.call(document.querySelectorAll(SEL)).forEach(function (el) { io.observe(el); });

      /* count-up stats (skip year-like numbers) */
      var meta = document.querySelector(".hero-meta");
      if (meta) {
        var io2 = new IntersectionObserver(
          function (es) {
            es.forEach(function (e) {
              if (!e.isIntersecting) return;
              io2.disconnect();
              [].slice.call(meta.querySelectorAll("b")).forEach(function (b) {
                var m = b.textContent.trim().match(/(\+?)(\d+)/);
                if (!m) return;
                var pre = m[1], target = parseInt(m[2], 10);
                if (target >= 1900) return; /* year — leave it */
                var t0 = null, dur = 1100;
                b.textContent = pre + "0";
                (function step(t) {
                  if (!t0) t0 = t;
                  var p = Math.min(1, (t - t0) / dur);
                  var v = Math.round(target * (1 - Math.pow(1 - p, 3))); /* ease-out cubic */
                  b.textContent = pre + v;
                  if (p < 1) requestAnimationFrame(step);
                  else b.textContent = pre + target;
                })(performance.now ? performance.now() : Date.now());
              });
            });
          },
          { threshold: 0.5 }
        );
        io2.observe(meta);
      }

      /* scroll progress bar */
      var bar = document.createElement("div");
      bar.className = "scrollbar";
      bar.setAttribute("aria-hidden", "true");
      document.body.appendChild(bar);

      /* gentle parallax on CTA background photos */
      var bgs = [].slice.call(document.querySelectorAll(".cta .bg"));
      var ticking = false;
      function onScroll() {
        var h = document.documentElement;
        var max = h.scrollHeight - h.clientHeight;
        bar.style.transform = "scaleX(" + (max > 0 ? h.scrollTop / max : 0) + ")";
        bgs.forEach(function (img) {
          var r = img.parentNode.getBoundingClientRect();
          if (r.bottom < 0 || r.top > window.innerHeight) return;
          var frac = (window.innerHeight - r.top) / (window.innerHeight + r.height); /* 0..1 */
          img.style.transform = "translateY(" + (frac - 0.5) * 60 + "px)";
        });
        ticking = false;
      }
      window.addEventListener(
        "scroll",
        function () { if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } },
        { passive: true }
      );
      onScroll();
    } catch (err) {
      /* anything goes wrong → reveal everything, no broken hidden content */
      root.classList.remove("anim");
    }
  }
})();
