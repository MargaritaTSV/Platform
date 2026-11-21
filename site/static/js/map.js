// Home star map: clicking a topic (star) reveals that area's subtopics in the
// block under the map. Progressive enhancement — with JS off, every topic
// block is shown and each star is a plain link to that area's problem list.
(function () {
  "use strict";

  var blocks = document.querySelector(".topic-blocks");
  if (!blocks) return;

  var stars = document.querySelector(".map-stars");
  blocks.classList.add("has-js"); // CSS now shows one block at a time

  function activate(key) {
    var blockList = blocks.querySelectorAll(".topic-block");
    for (var i = 0; i < blockList.length; i++) {
      blockList[i].classList.toggle(
        "is-active",
        blockList[i].getAttribute("data-area") === key
      );
    }
    if (stars) {
      var starList = stars.querySelectorAll(".map-star");
      for (var j = 0; j < starList.length; j++) {
        var on = starList[j].getAttribute("data-area") === key;
        starList[j].classList.toggle("is-active", on);
        var link = starList[j].querySelector(".map-star-link");
        if (link) link.setAttribute("aria-pressed", on ? "true" : "false");
      }
    }
  }

  if (stars) {
    stars.addEventListener("click", function (e) {
      var link = e.target.closest ? e.target.closest(".map-star-link") : null;
      if (!link) return;
      e.preventDefault(); // stay on the home page; just swap the subtopics
      activate(link.getAttribute("data-area"));
    });
  }
})();
