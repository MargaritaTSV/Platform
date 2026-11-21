// Area page: when arriving with ?sub=<key> (from a subtopic on the home page),
// show only that subtopic's problems and mark it in the rail. Progressive
// enhancement — with JS off, the page shows every problem in the area.
(function () {
  "use strict";

  var list = document.querySelector(".problem-list");
  if (!list) return;

  var sub = new URLSearchParams(window.location.search).get("sub");
  if (!sub) return;

  var rows = list.querySelectorAll(".problem-row");
  var shown = 0;
  for (var i = 0; i < rows.length; i++) {
    var match = rows[i].getAttribute("data-subtopic") === sub;
    rows[i].style.display = match ? "" : "none";
    if (match) shown++;
  }

  // Drawn row rules sit between rows; hide them so there are no dangling rules.
  var rules = list.querySelectorAll(".row-rule");
  for (var r = 0; r < rules.length; r++) rules[r].style.display = "none";

  // Highlight the active subtopic in the rail.
  var railItems = document.querySelectorAll(".rail-item");
  for (var j = 0; j < railItems.length; j++) {
    railItems[j].classList.toggle(
      "is-active",
      railItems[j].getAttribute("data-sub") === sub
    );
  }

  // If nothing matched, show the empty message.
  if (shown === 0 && list.getAttribute("data-empty")) {
    var p = document.createElement("p");
    p.className = "empty mono";
    p.textContent = list.getAttribute("data-empty");
    list.appendChild(p);
  }
})();
