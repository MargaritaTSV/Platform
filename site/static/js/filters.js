// Filters for one subtopic page. The choice lives in the address (?difficulty=2&grade=10).
(function () {
  "use strict";
  var form = document.getElementById("filters");
  if (!form) return;
  var selects = Array.from(form.querySelectorAll("select"));
  var items = Array.from(document.querySelectorAll(".problem-item"));

  function matches(item, name, value) {
    // A problem for grades 9-11 is shown when the visitor picks 10.
    if (name === "grade") return +item.dataset.gradeLow <= +value && +value <= +item.dataset.gradeHigh;
    return item.dataset[name] === value;
  }

  function apply() {
    var shown = 0;
    var query = new URLSearchParams(location.search);
    selects.forEach(function (s) {
      if (s.value) query.set(s.name, s.value); else query.delete(s.name);
    });
    items.forEach(function (item) {
      var on = selects.every(function (s) { return !s.value || matches(item, s.name, s.value); });
      item.hidden = !on;
      if (!on) return;
      shown += 1;
      item.querySelector(".row-num").textContent = shown;
      item.classList.toggle("is-first", shown === 1);
    });
    document.getElementById("shown").textContent = shown;
    document.getElementById("nothing").hidden = shown > 0;
    var text = query.toString();
    history.replaceState(null, "", location.pathname + (text ? "?" + text : "") + location.hash);
  }

  var query = new URLSearchParams(location.search);
  selects.forEach(function (s) {
    var wanted = query.get(s.name);
    // An unknown value in the address is ignored.
    if (Array.from(s.options).some(function (o) { return o.value === wanted; })) s.value = wanted;
    s.addEventListener("change", apply);
  });
  form.addEventListener("submit", function (e) { e.preventDefault(); });
  // The reset event fires before the values are cleared.
  form.addEventListener("reset", function () { setTimeout(apply, 0); });
  form.hidden = false;
  apply();
  // Hiding rows above a linked problem moves it, so scroll to it again.
  var target = location.hash && document.getElementById(decodeURIComponent(location.hash.slice(1)));
  if (target) target.scrollIntoView();
})();
