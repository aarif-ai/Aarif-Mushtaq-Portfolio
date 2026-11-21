/* "Save as PDF" button on resume.html.
   Opens the browser's print dialog, where "Save as PDF" is a destination.
   The print stylesheet (site.css, @media print) makes the page an A4 sheet.
   The button is hidden in the HTML and shown here, so it only appears when
   JavaScript can make it work. (No inline onclick: the CSP forbids it.) */
(function () {
  var button = document.querySelector(".print-button");
  if (!button || typeof window.print !== "function") return;

  button.addEventListener("click", function () {
    window.print();
  });
  button.hidden = false;
})();
