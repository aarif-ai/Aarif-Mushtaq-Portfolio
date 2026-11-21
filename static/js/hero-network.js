/* Hero network canvas (CLAUDE.md §4 item 1).
   Slow drifting nodes joined by faint lines: a nod to teams of LLM agents.
   It is pure decoration (the canvas has aria-hidden="true") and must never
   look like data.

   Rules this file follows:
   - At most 60 nodes, fewer on small screens.
   - Device pixel ratio capped at 2 (sharp, but not 3x the pixels to draw).
   - Paused when the hero is off-screen (IntersectionObserver) or the tab is
     hidden (visibilitychange), so it costs nothing while you read elsewhere.
   - Reduced motion: one still frame is drawn, nothing moves. */
(function () {
  var canvas = document.querySelector(".hero-canvas");
  if (!canvas || !canvas.getContext) return;
  var ctx = canvas.getContext("2d");
  if (!ctx) return;

  var MAX_NODES = 60;
  var AREA_PER_NODE = 16000;   // CSS px² of hero per node → fewer on phones
  var LINK_DISTANCE = 140;     // nodes closer than this (CSS px) get a line
  var MIN_SPEED = 4;           // CSS px per second: slow drift
  var MAX_SPEED = 12;
  var NODE_RADIUS = 1.6;

  var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  var nodes = [];
  var width = 0;              // canvas size in CSS pixels
  var height = 0;
  var color = "";             // accent colour, read from the CSS tokens
  var heroVisible = false;
  var frameId = 0;            // id from requestAnimationFrame, 0 = stopped
  var lastTime = 0;

  /* ---------- setup ---------- */

  /* Read the theme's accent colour so the network matches dark/light. */
  function readColor() {
    color = getComputedStyle(canvas).getPropertyValue("--accent").trim() || "#5eead4";
  }

  function randomBetween(min, max) {
    return min + Math.random() * (max - min);
  }

  function makeNode() {
    var angle = Math.random() * Math.PI * 2;
    var speed = randomBetween(MIN_SPEED, MAX_SPEED);
    return {
      x: Math.random() * width,
      y: Math.random() * height,
      vx: Math.cos(angle) * speed,
      vy: Math.sin(angle) * speed
    };
  }

  /* Match the canvas to its on-screen size. Existing nodes keep their
     relative positions; nodes are added or removed to fit the new area. */
  function resize() {
    var rect = canvas.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return; // not laid out yet
    var ratio = Math.min(window.devicePixelRatio || 1, 2);
    var oldWidth = width || rect.width;
    var oldHeight = height || rect.height;

    width = rect.width;
    height = rect.height;
    canvas.width = Math.round(width * ratio);
    canvas.height = Math.round(height * ratio);
    // Draw in CSS pixels; the browser scales up to the real pixel grid.
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);

    nodes.forEach(function (node) {
      node.x = (node.x / oldWidth) * width;
      node.y = (node.y / oldHeight) * height;
    });

    var wanted = Math.min(MAX_NODES, Math.round((width * height) / AREA_PER_NODE));
    while (nodes.length < wanted) nodes.push(makeNode());
    nodes.length = wanted;

    draw();
  }

  /* ---------- drawing ---------- */

  function draw() {
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = color;
    ctx.strokeStyle = color;
    ctx.lineWidth = 1;

    // Lines first, so nodes sit on top. Closer pairs get stronger lines.
    for (var i = 0; i < nodes.length; i++) {
      for (var j = i + 1; j < nodes.length; j++) {
        var dx = nodes[i].x - nodes[j].x;
        var dy = nodes[i].y - nodes[j].y;
        var distance = Math.sqrt(dx * dx + dy * dy);
        if (distance < LINK_DISTANCE) {
          ctx.globalAlpha = (1 - distance / LINK_DISTANCE) * 0.22;
          ctx.beginPath();
          ctx.moveTo(nodes[i].x, nodes[i].y);
          ctx.lineTo(nodes[j].x, nodes[j].y);
          ctx.stroke();
        }
      }
    }

    ctx.globalAlpha = 0.5;
    nodes.forEach(function (node) {
      ctx.beginPath();
      ctx.arc(node.x, node.y, NODE_RADIUS, 0, Math.PI * 2);
      ctx.fill();
    });
    ctx.globalAlpha = 1;
  }

  /* Move every node by its speed × elapsed time; bounce off the edges. */
  function move(seconds) {
    nodes.forEach(function (node) {
      node.x += node.vx * seconds;
      node.y += node.vy * seconds;
      if (node.x < 0 || node.x > width) {
        node.vx = -node.vx;
        node.x = Math.max(0, Math.min(width, node.x));
      }
      if (node.y < 0 || node.y > height) {
        node.vy = -node.vy;
        node.y = Math.max(0, Math.min(height, node.y));
      }
    });
  }

  /* ---------- animation loop: runs only while it should ---------- */

  function frame(time) {
    // Cap the step so a long pause doesn't make nodes jump.
    var seconds = Math.min((time - lastTime) / 1000, 0.1);
    lastTime = time;
    move(seconds);
    draw();
    frameId = requestAnimationFrame(frame);
  }

  function shouldAnimate() {
    return heroVisible && !document.hidden && !reducedMotion.matches;
  }

  /* Start or stop the loop to match the current conditions. */
  function update() {
    if (shouldAnimate() && !frameId) {
      lastTime = performance.now();
      frameId = requestAnimationFrame(frame);
    } else if (!shouldAnimate() && frameId) {
      cancelAnimationFrame(frameId);
      frameId = 0;
    }
  }

  /* ---------- wiring ---------- */

  readColor();
  resize();
  canvas.classList.add("is-ready"); // fades the canvas in (CSS)

  if ("ResizeObserver" in window) {
    new ResizeObserver(resize).observe(canvas);
  } else {
    window.addEventListener("resize", resize);
  }

  if ("IntersectionObserver" in window) {
    new IntersectionObserver(function (entries) {
      heroVisible = entries[0].isIntersecting;
      update();
    }).observe(canvas);
  } else {
    heroVisible = true;
  }

  document.addEventListener("visibilitychange", update);
  reducedMotion.addEventListener("change", update);

  // Theme switched: by the toggle (data-theme on <html>) or by the system.
  function onThemeChange() {
    readColor();
    draw();
  }
  new MutationObserver(onThemeChange).observe(document.documentElement, {
    attributes: true,
    attributeFilter: ["data-theme"]
  });
  window.matchMedia("(prefers-color-scheme: light)").addEventListener("change", onThemeChange);

  update();
})();
