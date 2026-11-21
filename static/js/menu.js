/* Mobile "Menu" button for the header links (below 48rem; CSS decides).
   - Adds .has-menu to the header: only then does CSS hide the links behind
     the button. Without JavaScript the links simply stay visible.
   - aria-expanded tells screen readers whether the panel is open.
   - Closes when a link is chosen, and on Escape (focus returns to the button). */
(function () {
  var header = document.querySelector(".site-header");
  var button = document.querySelector(".menu-toggle");
  var nav = document.getElementById("site-nav");
  if (!header || !button || !nav) return;

  function setOpen(open) {
    header.classList.toggle("menu-open", open);
    button.setAttribute("aria-expanded", String(open));
  }

  header.classList.add("has-menu");

  button.addEventListener("click", function () {
    setOpen(button.getAttribute("aria-expanded") !== "true");
  });

  nav.addEventListener("click", function (event) {
    if (event.target.closest("a")) setOpen(false);
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && header.classList.contains("menu-open")) {
      setOpen(false);
      button.focus();
    }
  });
})();
