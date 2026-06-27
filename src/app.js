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
  });
})();
