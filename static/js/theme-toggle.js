/* Theme toggle button (CLAUDE.md §4 item 8).
   - The button is "Light theme": aria-pressed="true" means light is on.
   - Until the visitor clicks, the site follows the system theme.
   - The choice is saved in localStorage; theme-init.js re-applies it on
     the next page load before anything is painted. */
(function () {
  var root = document.documentElement;
  var button = document.querySelector(".theme-toggle");
  if (!button) return;

  var systemLight = window.matchMedia("(prefers-color-scheme: light)");

  /* The theme on screen right now: the saved choice, or the system's. */
  function currentTheme() {
    var chosen = root.getAttribute("data-theme");
    if (chosen === "light" || chosen === "dark") return chosen;
    return systemLight.matches ? "light" : "dark";
  }

  /* Keep the button's on/off state in line with the theme on screen. */
  function updateButton() {
    button.setAttribute("aria-pressed", String(currentTheme() === "light"));
  }

  function saveChoice(theme) {
    try {
      localStorage.setItem("theme", theme);
    } catch (error) {
      /* Can't save: the choice lasts until the page is closed. */
    }
  }

  button.addEventListener("click", function () {
    var next = currentTheme() === "light" ? "dark" : "light";

    /* Turn on colour transitions just for this switch (see site.css §8). */
    root.classList.add("theme-changing");
    root.setAttribute("data-theme", next);
    saveChoice(next);
    updateButton();
    window.setTimeout(function () {
      root.classList.remove("theme-changing");
    }, 400);
  });

  /* If the system theme changes and the visitor hasn't chosen, follow it. */
  systemLight.addEventListener("change", updateButton);

  updateButton();
  button.hidden = false; /* Shown only when JavaScript can make it work. */
})();
