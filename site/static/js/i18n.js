/* StellarTask — tiny, dependency-free language preference helper.
 * The site works fully with JS disabled: "/", "/en/" and "/ru/" are
 * static, self-contained pages and the RU/EN links are plain <a> tags.
 * This script only adds two conveniences on top of that:
 *   1. remember the language the visitor picks, in localStorage.
 *   2. on a first visit to "/", send RU-preferring visitors to "/ru/".
 */
(function () {
  "use strict";

  var STORAGE_KEY = "stellartask:lang";

  function getStored() {
    try {
      return window.localStorage.getItem(STORAGE_KEY);
    } catch (err) {
      return null;
    }
  }

  function setStored(lang) {
    try {
      window.localStorage.setItem(STORAGE_KEY, lang);
    } catch (err) {
      /* localStorage unavailable (private mode, disabled, etc) - ignore */
    }
  }

  function langFromHref(href) {
    return /^\/ru\//.test(href) ? "ru" : "en";
  }

  // Remember the choice whenever a visitor uses the RU/EN switch.
  document.addEventListener("click", function (event) {
    var el = event.target;
    while (el && el !== document.documentElement) {
      if (el.classList && el.classList.contains("lang-link")) {
        var href = el.getAttribute("href") || "/";
        setStored(langFromHref(href));
        return;
      }
      el = el.parentNode;
    }
  });

  // First-visit redirect, only from the default (English) entry page, and
  // only when the visitor has not already told us (or themselves) a
  // language choice.
  var path = window.location.pathname;
  var isDefaultEntry = path === "/" || path === "/index.html";
  if (!isDefaultEntry) {
    return;
  }

  var stored = getStored();
  if (stored) {
    if (stored === "ru") {
      window.location.replace("/ru/");
    }
    return;
  }

  var browserLang = (window.navigator.language || window.navigator.userLanguage || "")
    .slice(0, 2)
    .toLowerCase();

  if (browserLang === "ru") {
    setStored("ru");
    window.location.replace("/ru/");
  } else {
    setStored("en");
  }
})();
