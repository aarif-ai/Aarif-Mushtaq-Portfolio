/* Stat count-up (CLAUDE.md §4 item 4).
   The HTML already contains each final number. This script only animates
   it from 0, once, when the stats strip comes into view.
   Reduced motion, no JavaScript or no IntersectionObserver → nothing runs
   and the final numbers stay as they are. */
(function () {
  var strip = document.querySelector(".stats");
  var numbers = document.querySelectorAll(".stat-number[data-count]");
  if (!strip || !numbers.length) return;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  if (!("IntersectionObserver" in window)) return;

  var DURATION = 600; // ms, the longest animation CLAUDE.md allows

  /* Ease-out: fast at first, gently settling on the final number. */
  function easeOut(progress) {
    return 1 - Math.pow(1 - progress, 3);
  }

  function countUp(element) {
    var target = parseInt(element.getAttribute("data-count"), 10);
    if (isNaN(target)) return;

    // Fix the box to the final number's width so the layout never moves.
    // With tabular (equal-width) digits, 1ch is exactly one digit.
    element.style.minWidth = String(target).length + "ch";

    var start = performance.now();
    function step(now) {
      var progress = Math.min((now - start) / DURATION, 1);
      element.textContent = String(Math.round(target * easeOut(progress)));
      if (progress < 1) requestAnimationFrame(step);
    }
    element.textContent = "0";
    requestAnimationFrame(step);
  }

  /* Start once at least half the strip is visible, then stop watching. */
  var observer = new IntersectionObserver(function (entries) {
    if (!entries[0].isIntersecting) return;
    observer.disconnect();
    numbers.forEach(countUp);
  }, { threshold: 0.5 });

  observer.observe(strip);
})();
