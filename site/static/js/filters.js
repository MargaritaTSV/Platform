// Filters and numbered pages for one subtopic. The choice lives in the address (?difficulty=2&grade=10&p=2).
// Without a filter the page is plain HTML. With one, rows are collected from the subtopic's other pages.
(function () {
  "use strict";
  var form = document.getElementById("filters");
  if (!form) return;
  var selects = Array.from(form.querySelectorAll("select"));
  var rows = JSON.parse(document.getElementById("rows").textContent);
  var list = document.getElementById("rows-list");
  var pager = document.getElementById("pager");
  var base = list.dataset.base;
  var current = +list.dataset.page;
  var perPage = +list.dataset.perPage;
  var pages = {}; // page number -> promise of its list of problems
  pages[current] = Promise.resolve(list.cloneNode(true));
  var latest = 0;

  function byId(id) { return document.getElementById(id); }

  function matches(row, name, value) {
    // A problem for grades 9-11 is shown when the visitor picks 10.
    if (name === "grade") return row.grade_low <= +value && +value <= row.grade_high;
    return String(row[name]) === value;
  }

  function pageUrl(n) { return base + (n > 1 ? n + "/" : ""); }

  function address(query) {
    var text = query.toString();
    return base + (text ? "?" + text : "");
  }

  // shortcut: a rare combination can need up to 20 pages per view; add the row HTML to a data file if that is slow.
  function load(n) {
    if (!pages[n]) {
      pages[n] = fetch(pageUrl(n)).then(function (response) {
        if (!response.ok) throw new Error(response.status + " " + response.url);
        return response.text();
      }).then(function (html) {
        return new DOMParser().parseFromString(html, "text/html").getElementById("rows-list");
      }).catch(function (error) {
        delete pages[n];
        throw error;
      });
    }
    return pages[n];
  }

  function link(n, query) {
    var wanted = new URLSearchParams(query);
    if (n > 1) wanted.set("p", n); else wanted.delete("p");
    return address(wanted);
  }

  // The same page numbers as pager() in build.py.
  function drawPager(page, count, query) {
    if (!pager) return; // one page in total, so one page of results too
    pager.hidden = count < 2;
    var parts = [];
    var last = 0;
    [1, page - 1, page, page + 1, count].forEach(function (n) {
      if (n <= last || n > count) return;
      if (n > last + 1) parts.push(Object.assign(document.createElement("span"), { textContent: "…" }));
      var a = Object.assign(document.createElement("a"), { href: link(n, query), textContent: n });
      if (n === page) a.setAttribute("aria-current", "page");
      parts.push(a);
      last = n;
    });
    pager.querySelector(".pager-numbers").replaceChildren.apply(pager.querySelector(".pager-numbers"), parts);
    [[".pager-prev", page - 1], [".pager-next", page + 1]].forEach(function (pair) {
      var a = pager.querySelector(pair[0]);
      a.hidden = pair[1] < 1 || pair[1] > count;
      a.href = link(pair[1], query);
    });
  }

  async function show() {
    var turn = ++latest;
    var query = new URLSearchParams(location.search);
    var found = rows.filter(function (row) {
      return selects.every(function (s) { return !s.value || matches(row, s.name, s.value); });
    });
    var count = Math.max(1, Math.ceil(found.length / perPage));
    var page = Math.min(Math.max(parseInt(query.get("p"), 10) || 1, 1), count);
    var start = (page - 1) * perPage;
    byId("shown").textContent = found.length;
    byId("nothing").hidden = found.length > 0;
    byId("load-failed").hidden = true;
    byId("loading").hidden = false;
    list.hidden = true;
    if (pager) pager.hidden = true;
    try {
      var items = await Promise.all(found.slice(start, start + perPage).map(async function (row, i) {
        var holder = await load(row.page);
        // Fails if the site was rebuilt since this page was opened and the problem moved.
        var item = holder.querySelector('.problem-title[id="' + row.id + '"]').closest(".problem-item");
        item = document.importNode(item, true);
        item.querySelector(".row-num").textContent = start + i + 1;
        return item;
      }));
      if (turn !== latest) return; // the filters changed again
      list.replaceChildren.apply(list, items);
      list.hidden = false;
      drawPager(page, count, query);
    } catch (error) {
      console.error(error);
      if (turn !== latest) return;
      byId("load-failed").hidden = false;
    }
    byId("loading").hidden = true;
  }

  function change() {
    var query = new URLSearchParams(location.search);
    selects.forEach(function (s) {
      if (s.value) query.set(s.name, s.value); else query.delete(s.name);
    });
    query.delete("p");
    if (selects.every(function (s) { return !s.value; })) {
      location.assign(address(query)); // back to the plain first page
      return;
    }
    history.replaceState(null, "", address(query));
    show();
  }

  var query = new URLSearchParams(location.search);
  selects.forEach(function (s) {
    var wanted = query.get(s.name);
    // An unknown value in the address is ignored.
    if (Array.from(s.options).some(function (o) { return o.value === wanted; })) s.value = wanted;
    s.addEventListener("change", change);
  });
  form.addEventListener("submit", function (e) { e.preventDefault(); });
  // The reset event fires before the values are cleared.
  form.addEventListener("reset", function () { setTimeout(change, 0); });
  form.hidden = false;

  var id = decodeURIComponent(location.hash.slice(1));
  function toTarget() {
    var target = id && byId(id);
    if (target) target.scrollIntoView();
  }
  if (selects.some(function (s) { return s.value; })) {
    history.replaceState(null, "", address(query) + location.hash);
    show().then(toTarget);
  } else {
    // New problems push old ones to later pages, so a saved #id link may point at the wrong page.
    var linked = rows.find(function (row) { return row.id === id; });
    if (linked && linked.page !== current) location.replace(pageUrl(linked.page) + location.search + location.hash);
    else toTarget(); // the filter form appearing moved it
  }
})();
