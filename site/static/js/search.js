// Search over the whole bank (Pagefind). The words are kept in the address (?q=).
(function () {
  "use strict";
  var box = document.querySelector(".search");
  if (!box) return;
  var input = box.querySelector("input");
  var list = box.querySelector(".search-results");
  var status = box.querySelector(".search-status");
  var library;
  var latest = 0;
  var LIMIT = 20;

  function say(name, total) {
    box.querySelector(".search-total").textContent = total || "";
    status.querySelectorAll("[data-state]").forEach(function (el) {
      el.hidden = el.dataset.state !== name;
    });
  }

  function both(ru, en) {
    var fragment = document.createDocumentFragment();
    [["ru", ru], ["en", en]].forEach(function (pair) {
      var span = document.createElement("span");
      span.className = pair[0];
      span.lang = pair[0];
      span.textContent = pair[1];
      fragment.appendChild(span);
    });
    return fragment;
  }

  function row(data) {
    var item = document.createElement("li");
    var link = document.createElement("a");
    link.href = data.url;
    var title = document.createElement("span");
    title.className = "serif result-title";
    title.textContent = data.meta.title;
    var place = document.createElement("span");
    place.className = "mono result-place";
    place.appendChild(both(data.meta.ru, data.meta.en));
    var excerpt = document.createElement("span");
    excerpt.className = "result-excerpt";
    // Pagefind returns the excerpt HTML-escaped, with <mark> around the found words.
    excerpt.innerHTML = data.excerpt;
    link.append(title, place, excerpt);
    item.appendChild(link);
    return item;
  }

  async function search() {
    var words = input.value.trim();
    var turn = ++latest;
    var query = new URLSearchParams(location.search);
    if (words) query.set("q", words); else query.delete("q");
    var text = query.toString();
    history.replaceState(null, "", location.pathname + (text ? "?" + text : "") + location.hash);
    if (!words) { list.replaceChildren(); say(""); return; }
    try {
      library = library || await import("/pagefind/pagefind.js");
      var found = await library.search(words);
      var data = await Promise.all(found.results.slice(0, LIMIT).map(function (r) { return r.data(); }));
      if (turn !== latest) return; // a newer search has started
      list.replaceChildren.apply(list, data.map(row));
      var total = found.results.length;
      say(total === 0 ? "none" : total > LIMIT ? "more" : "found", total);
    } catch (error) {
      console.error(error);
      if (turn === latest) { list.replaceChildren(); say("failed"); }
    }
  }

  var timer;
  input.addEventListener("input", function () {
    clearTimeout(timer);
    timer = setTimeout(search, 200);
  });
  box.querySelector("form").addEventListener("submit", function (e) {
    e.preventDefault();
    clearTimeout(timer);
    search();
  });
  box.hidden = false;
  input.value = new URLSearchParams(location.search).get("q") || "";
  if (input.value) search();
})();
