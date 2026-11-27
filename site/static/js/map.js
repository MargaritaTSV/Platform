// Home star map: choosing a star shows that topic's subtopics under the map.
// Without JavaScript every topic block stays visible.
(function () {
  "use strict";
  var blocks = document.querySelector(".topic-blocks");
  var stars = Array.from(document.querySelectorAll(".map-star, .map-aux-item"));
  if (!blocks || !stars.length) return;
  blocks.classList.add("has-js"); // CSS now shows one block at a time

  function select(key) {
    if (!stars.some(function (s) { return s.dataset.topic === key; })) return;
    blocks.querySelectorAll(".topic-block").forEach(function (block) {
      block.classList.toggle("is-active", block.dataset.topic === key);
    });
    stars.forEach(function (star) {
      var on = star.dataset.topic === key;
      star.classList.toggle("is-active", on);
      star.querySelector("button").setAttribute("aria-pressed", String(on));
    });
  }

  stars.forEach(function (star) {
    star.querySelector("button").addEventListener("click", function () {
      select(star.dataset.topic);
      // Kept in the address, so Back from a problem list returns to the same topic.
      history.replaceState(null, "", "#" + star.dataset.topic);
    });
  });
  window.addEventListener("hashchange", function () { select(location.hash.slice(1)); });
  select(location.hash.slice(1));
})();
