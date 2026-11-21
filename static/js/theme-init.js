/* Applies a saved theme choice BEFORE the page is painted.
   Loaded without `defer` in <head> on purpose: it must run before the
   browser draws anything, otherwise a visitor who chose light would see a
   dark flash first. Keep this file tiny. */
(function () {
  try {
    var saved = localStorage.getItem("theme");
    if (saved === "light" || saved === "dark") {
      document.documentElement.setAttribute("data-theme", saved);
    }
  } catch (error) {
    /* Storage blocked (private mode, settings): follow the system theme. */
  }
})();
