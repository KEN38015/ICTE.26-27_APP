// Runs in <head> before the page draws, so a saved dark/light choice never flashes.
(function () {
  try {
    var saved = localStorage.getItem("ssa-theme");
    if (saved === "dark" || saved === "light") document.documentElement.setAttribute("data-theme", saved);
  } catch (e) { /* storage blocked: fall back to the system setting */ }
})();
