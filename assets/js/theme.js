(function () {
  var root = document.documentElement;
  var button = document.getElementById("theme-toggle");

  function apply(theme) {
    root.setAttribute("data-theme", theme);
    button.setAttribute("aria-label", theme === "light" ? "switch to dark mode" : "switch to light mode");
    button.setAttribute("aria-pressed", theme === "light" ? "true" : "false");
  }

  apply(root.getAttribute("data-theme") === "light" ? "light" : "dark");

  button.addEventListener("click", function () {
    var next = root.getAttribute("data-theme") === "light" ? "dark" : "light";
    try { localStorage.setItem("theme", next); } catch (e) {}
    apply(next);
    document.dispatchEvent(new Event("themechange"));
  });
})();
