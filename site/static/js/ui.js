// The ru/en button changes interface text only; problems keep their own language.
(function () {
  "use strict";
  var root = document.documentElement;

  function show(lang) {
    root.lang = lang;
    document.title = lang === "en" ? root.dataset.titleEn : root.dataset.titleRu;
    document.querySelectorAll("[data-set-lang]").forEach(function (button) {
      button.setAttribute("aria-pressed", String(button.dataset.setLang === lang));
    });
    document.querySelectorAll("[data-text-ru]").forEach(function (el) {
      el.textContent = lang === "en" ? el.dataset.textEn : el.dataset.textRu;
    });
    document.querySelectorAll("[data-label-ru]").forEach(function (el) {
      el.setAttribute("aria-label", lang === "en" ? el.dataset.labelEn : el.dataset.labelRu);
    });
  }

  document.querySelectorAll("[data-set-lang]").forEach(function (button) {
    button.addEventListener("click", function () {
      var lang = button.dataset.setLang;
      show(lang);
      try { localStorage.setItem("lang", lang); } catch (e) { /* private mode: not remembered */ }
    });
  });

  show(root.lang === "en" ? "en" : "ru");
  // A page restored by Back/Forward keeps the old language otherwise.
  window.addEventListener("pageshow", function () {
    try { show(localStorage.getItem("lang") === "en" ? "en" : "ru"); } catch (e) { /* keep current */ }
  });
})();
