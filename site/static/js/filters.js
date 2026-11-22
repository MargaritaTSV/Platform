// Area page: subtopic / grade / olympiad filters (combined with AND), plus
// the ?sub= deep link from the home page. Progressive enhancement — with JS
// off, every control is inert and every problem row shows.
//
// Grade and olympiad are not (yet) available as raw data attributes from the
// build, so this script enriches each row from /data/index.json (the one
// data file the frontend is allowed to read) matched by data-id, and uses
// that same data to populate the grade/olympiad <select> options for this
// area. If the fetch fails (offline, file:// etc.) the subtopic filter still
// works from the attributes already in the markup.
(function () {
  "use strict";

  var list = document.querySelector(".problem-list");
  if (!list) return;

  var rows = Array.prototype.slice.call(list.querySelectorAll(".problem-row"));
  var rules = Array.prototype.slice.call(list.querySelectorAll(".row-rule"));
  var railItems = Array.prototype.slice.call(document.querySelectorAll(".rail-item"));

  var subSelect = document.getElementById("filter-subtopic");
  var gradeSelect = document.getElementById("filter-grade");
  var olympiadSelect = document.getElementById("filter-olympiad");
  var clearBtn = document.getElementById("filter-clear");

  var params = new URLSearchParams(window.location.search);
  var pending = {
    sub: params.get("sub") || "",
    grade: params.get("grade") || "",
    olympiad: params.get("olympiad") || ""
  };

  var emptyMessageEl = null;

  function fieldOf(select) {
    if (!select) return "";
    return select.getAttribute("data-filter") || "";
  }

  function currentValues() {
    return {
      sub: subSelect ? subSelect.value : "",
      grade: gradeSelect ? gradeSelect.value : "",
      olympiad: olympiadSelect ? olympiadSelect.value : ""
    };
  }

  function updateUrl(values) {
    var next = new URLSearchParams(window.location.search);
    ["sub", "grade", "olympiad"].forEach(function (key) {
      if (values[key]) {
        next.set(key, values[key]);
      } else {
        next.delete(key);
      }
    });
    var qs = next.toString();
    var url = window.location.pathname + (qs ? "?" + qs : "") + window.location.hash;
    window.history.replaceState(null, "", url);
  }

  function showEmptyMessage(show) {
    if (show) {
      if (!emptyMessageEl) {
        emptyMessageEl = document.createElement("p");
        emptyMessageEl.className = "empty mono";
        emptyMessageEl.textContent = list.getAttribute("data-empty") || "";
        list.appendChild(emptyMessageEl);
      }
      emptyMessageEl.style.display = "";
    } else if (emptyMessageEl) {
      emptyMessageEl.style.display = "none";
    }
  }

  function applyFilters(skipUrlUpdate) {
    var values = currentValues();
    var anyActive = !!(values.sub || values.grade || values.olympiad);
    var shown = 0;

    for (var i = 0; i < rows.length; i++) {
      var row = rows[i];
      var match =
        (!values.sub || row.getAttribute("data-subtopic") === values.sub) &&
        (!values.grade || row.getAttribute("data-grade") === values.grade) &&
        (!values.olympiad || row.getAttribute("data-olympiad") === values.olympiad);
      row.style.display = match ? "" : "none";
      if (match) shown++;
    }

    // Drawn row rules sit between consecutive rows in document order; once
    // some rows are hidden they would dangle, so hide every rule while any
    // filter is active and restore them once filters are cleared.
    for (var r = 0; r < rules.length; r++) {
      rules[r].style.display = anyActive ? "none" : "";
    }

    for (var j = 0; j < railItems.length; j++) {
      railItems[j].classList.toggle(
        "is-active",
        !!values.sub && railItems[j].getAttribute("data-sub") === values.sub
      );
    }

    showEmptyMessage(shown === 0);

    if (!skipUrlUpdate) updateUrl(values);
  }

  function addOption(select, value, label) {
    if (!select || !value) return;
    var exists = false;
    for (var i = 0; i < select.options.length; i++) {
      if (select.options[i].value === value) {
        exists = true;
        break;
      }
    }
    if (exists) return;
    var opt = document.createElement("option");
    opt.value = value;
    opt.textContent = label;
    select.appendChild(opt);
  }

  function enrichFromIndex() {
    var areaKey = list.getAttribute("data-area");
    if (!window.fetch) return;

    fetch("/data/index.json")
      .then(function (res) {
        return res.ok ? res.json() : null;
      })
      .then(function (data) {
        if (!data || !data.problems) return;

        var byId = {};
        for (var i = 0; i < data.problems.length; i++) {
          var p = data.problems[i];
          if (areaKey && p.area !== areaKey) continue;
          byId[p.id] = p;
        }

        var grades = [];
        var olympiads = [];

        for (var r = 0; r < rows.length; r++) {
          var row = rows[r];
          var p2 = byId[row.getAttribute("data-id")];
          if (!p2) continue;
          if (p2.grade && !row.getAttribute("data-grade")) {
            row.setAttribute("data-grade", p2.grade);
          }
          if (p2.olympiad && !row.getAttribute("data-olympiad")) {
            row.setAttribute("data-olympiad", p2.olympiad);
          }
          var g = row.getAttribute("data-grade");
          var o = row.getAttribute("data-olympiad");
          if (g && grades.indexOf(g) < 0) grades.push(g);
          if (o && olympiads.indexOf(o) < 0) olympiads.push(o);
        }

        grades.sort();
        olympiads.sort();

        for (var gi = 0; gi < grades.length; gi++) {
          addOption(gradeSelect, grades[gi], grades[gi]);
        }
        for (var oi = 0; oi < olympiads.length; oi++) {
          addOption(olympiadSelect, olympiads[oi], olympiads[oi].toUpperCase());
        }

        // Now that options exist, apply the grade/olympiad values from the URL.
        if (gradeSelect && pending.grade) gradeSelect.value = pending.grade;
        if (olympiadSelect && pending.olympiad) olympiadSelect.value = pending.olympiad;
        applyFilters(true);
      })
      .catch(function () {
        /* offline or blocked fetch: subtopic-only filtering still works */
      });
  }

  // Initial state from the URL (subtopic options already exist server-side).
  if (subSelect && pending.sub) subSelect.value = pending.sub;

  [subSelect, gradeSelect, olympiadSelect].forEach(function (select) {
    if (!select) return;
    select.addEventListener("change", function () {
      applyFilters();
    });
  });

  if (clearBtn) {
    clearBtn.addEventListener("click", function () {
      if (subSelect) subSelect.value = "";
      if (gradeSelect) gradeSelect.value = "";
      if (olympiadSelect) olympiadSelect.value = "";
      applyFilters();
    });
  }

  applyFilters(true);
  if (pending.sub || pending.grade || pending.olympiad) updateUrl(currentValues());
  enrichFromIndex();
})();
