/* Resolve before CSS paints. Without JavaScript the stylesheet follows the OS. */
(() => {
  const root = document.documentElement;
  if (root.classList.contains("dark") || root.classList.contains("light")) return;
  let preference;
  try {
    preference = localStorage.getItem("theme");
  } catch {
    // Storage can be unavailable in private or restricted browser contexts.
  }
  root.classList.add(preference === "dark" ? "dark" : "light");
})();
