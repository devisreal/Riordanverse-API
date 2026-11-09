/* Resolve before CSS paints. Without JavaScript the stylesheet follows the OS. */
(() => {
  const root = document.documentElement;
  if (!root.classList.contains("dark") && !root.classList.contains("light")) {
    let preference;
    try {
      preference = localStorage.getItem("theme");
    } catch {
      // Storage can be unavailable in private or restricted browser contexts.
    }
    root.classList.add(preference === "dark" ? "dark" : "light");
  }

  function bindControls() {
    const toggles = document.querySelectorAll("[data-theme-toggle]");
    const choices = document.querySelectorAll("[data-theme-choice]");

    function syncControls() {
      const theme = root.classList.contains("dark") ? "dark" : "light";
      const target = theme === "dark" ? "light" : "dark";
      toggles.forEach((button) => {
        const label = `Switch to ${target} mode`;
        button.setAttribute("aria-label", label);
        button.setAttribute("title", label);
        button.querySelectorAll("[data-theme-icon]").forEach((icon) => {
          icon.hidden = icon.getAttribute("data-theme-icon") !== target;
        });
      });
      choices.forEach((button) => {
        button.setAttribute("aria-pressed", String(button.getAttribute("data-theme-choice") === theme));
      });
    }

    function setTheme(theme) {
      if (theme !== "light" && theme !== "dark") return;
      root.classList.remove("light", "dark");
      root.classList.add(theme);
      try {
        localStorage.setItem("theme", theme);
      } catch {
        // The controls still work when the preference cannot be persisted.
      }
      syncControls();
    }

    toggles.forEach((button) => {
      button.addEventListener("click", () => {
        setTheme(root.classList.contains("dark") ? "light" : "dark");
      });
    });
    choices.forEach((button) => {
      button.addEventListener("click", () => {
        setTheme(button.getAttribute("data-theme-choice"));
      });
    });
    syncControls();
    toggles.forEach((button) => { button.hidden = false; });
    document.querySelectorAll("[data-theme-options]").forEach((container) => {
      container.hidden = false;
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bindControls, { once: true });
  } else {
    bindControls();
  }
})();
