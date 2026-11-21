/* Header highlight for the section you are reading.
   Rule: the current section is the last one whose top edge has passed a
   line 40% down the screen; at the very bottom of the page it is the last
   section (a short Contact section may never reach that line).
   The matching header link gets aria-current="true" (site.css adds an
   underline as well as colour). Not an animation, so it also runs with
   reduced motion. */
(function () {
  var links = Array.prototype.slice.call(
    document.querySelectorAll('.nav-list a[href^="#"]')
  );
  if (!links.length) return;

  var sections = links.map(function (link) {
    return document.getElementById(link.getAttribute("href").slice(1));
  });
  var currentIndex = -1;
  var ticking = false;

  /* Mark link number `index` as current (-1 = none). */
  function setCurrent(index) {
    if (index === currentIndex) return;
    currentIndex = index;
    links.forEach(function (link, i) {
      if (i === index) {
        link.setAttribute("aria-current", "true");
      } else {
        link.removeAttribute("aria-current");
      }
    });
  }

  /* Work out which section is current right now. */
  function update() {
    ticking = false;
    var line = window.innerHeight * 0.4;
    var root = document.documentElement;
    var atBottom = window.innerHeight + window.scrollY >= root.scrollHeight - 2;

    var index = -1;
    if (atBottom) {
      index = sections.length - 1;
    } else {
      sections.forEach(function (section, i) {
        if (section && section.getBoundingClientRect().top <= line) index = i;
      });
    }
    setCurrent(index);
  }

  /* Scroll fires many times per frame; work at most once per frame. */
  function onScroll() {
    if (!ticking) {
      ticking = true;
      window.requestAnimationFrame(update);
    }
  }

  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", onScroll);
  update();
})();

/* Contact "Copy" button for the email address.
   Shown only when the Clipboard API exists (it stays hidden without JS or
   on old browsers; the mailto link works either way). On success the label
   reads "Copied" for 2 seconds and the aria-live region next to it
   announces it to screen readers. If copying fails, nothing changes. */
(function () {
  var button = document.querySelector(".copy-button");
  if (!button || !navigator.clipboard || !navigator.clipboard.writeText) return;

  var label = button.textContent;
  var status = button.nextElementSibling; // <span aria-live="polite">
  var timer = 0;

  button.addEventListener("click", function () {
    navigator.clipboard.writeText(button.getAttribute("data-copy")).then(function () {
      var copied = button.getAttribute("data-copied");
      button.textContent = copied;
      status.textContent = copied;
      window.clearTimeout(timer);
      timer = window.setTimeout(function () {
        button.textContent = label;
        status.textContent = "";
      }, 2000);
    }, function () { /* copy refused: the mailto link still works */ });
  });

  button.hidden = false;
})();
