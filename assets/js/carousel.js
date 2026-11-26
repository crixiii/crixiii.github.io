(function () {
  var root = document.querySelector(".posters");
  if (!root) return;
  var figures = Array.prototype.slice.call(root.children).filter(function (el) { return el.tagName === "FIGURE"; });
  if (figures.length < 2) return;

  var track = document.createElement("div");
  track.className = "track";
  figures.forEach(function (f) { track.appendChild(f); });
  root.appendChild(track);
  root.classList.add("carousel");
  root.tabIndex = 0;
  root.setAttribute("role", "region");
  root.setAttribute("aria-label", root.getAttribute("data-label") || "posters and outreach");

  var nav = document.createElement("div");
  nav.className = "carousel-nav";
  nav.innerHTML = '<button class="car-btn" type="button" aria-label="previous">&#8249;</button><div class="car-dots"></div><button class="car-btn" type="button" aria-label="next">&#8250;</button>';
  root.parentNode.insertBefore(nav, root.nextSibling);
  var prev = nav.children[0], dots = nav.children[1], next = nav.children[2];

  figures.forEach(function (f, i) {
    var dot = document.createElement("button");
    dot.className = "car-dot";
    dot.type = "button";
    dot.setAttribute("aria-label", "go to item " + (i + 1));
    dot.addEventListener("click", function () { go(i); });
    dots.appendChild(dot);
    var img = f.querySelector("img");
    if (img) img.loading = "lazy";
  });

  var index = 0;
  function layout() {
    var f = figures[0];
    var width = f.offsetWidth;
    var gap = parseFloat(getComputedStyle(track).columnGap) || 0;
    var shift = root.clientWidth / 2 - width / 2 - index * (width + gap);
    track.style.transform = "translateX(" + shift + "px)";
  }
  function go(i) {
    index = Math.max(0, Math.min(figures.length - 1, i));
    figures.forEach(function (f, k) {
      f.classList.toggle("active", k === index);
      f.setAttribute("aria-hidden", k === index ? "false" : "true");
    });
    Array.prototype.forEach.call(dots.children, function (d, k) {
      if (k === index) d.setAttribute("aria-current", "true"); else d.removeAttribute("aria-current");
    });
    prev.disabled = index === 0;
    next.disabled = index === figures.length - 1;
    layout();
  }

  prev.addEventListener("click", function () { go(index - 1); });
  next.addEventListener("click", function () { go(index + 1); });
  root.addEventListener("keydown", function (e) {
    if (e.key === "ArrowLeft") { go(index - 1); e.preventDefault(); }
    if (e.key === "ArrowRight") { go(index + 1); e.preventDefault(); }
  });

  figures.forEach(function (f, i) {
    f.addEventListener("click", function (e) {
      if (i !== index) { e.preventDefault(); go(i); }
    });
  });

  var startX = null, moved = false;
  root.addEventListener("pointerdown", function (e) { startX = e.clientX; moved = false; });
  root.addEventListener("pointermove", function (e) {
    if (startX !== null && Math.abs(e.clientX - startX) > 8) moved = true;
  });
  root.addEventListener("pointerup", function (e) {
    if (startX === null) return;
    var dx = e.clientX - startX;
    startX = null;
    if (Math.abs(dx) > 40) go(index + (dx < 0 ? 1 : -1));
  });
  root.addEventListener("pointercancel", function () { startX = null; });
  root.addEventListener("click", function (e) {
    if (moved) { e.preventDefault(); e.stopPropagation(); moved = false; }
  }, true);

  window.addEventListener("resize", layout);
  window.addEventListener("load", layout);
  go(0);
})();
