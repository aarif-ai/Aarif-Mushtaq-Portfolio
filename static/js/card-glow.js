/* Card glow (CLAUDE.md §4 item 5).
   A soft radial highlight follows the mouse over a card. JS only stores the
   pointer position in two CSS variables (--glow-x, --glow-y); site.css
   draws the glow and fades it in on hover.
   Off for touch screens, pens and reduced motion. */
(function () {
  var finePointer = window.matchMedia("(hover: hover) and (pointer: fine)");
  var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  if (!finePointer.matches || reducedMotion.matches) return;

  document.querySelectorAll(".card-glow").forEach(function (card) {
    card.addEventListener("pointermove", function (event) {
      if (event.pointerType !== "mouse") return; // touch / pen: no glow
      var rect = card.getBoundingClientRect();
      card.style.setProperty("--glow-x", event.clientX - rect.left + "px");
      card.style.setProperty("--glow-y", event.clientY - rect.top + "px");
    });
  });
})();
