/* Progressive enhancements only: navigation and all examples remain usable without JS. */
(() => {
  const menu = document.getElementById("site-menu");
  const summary = menu.querySelector("summary");
  const content = document.getElementById("page-content");
  const mobile = window.matchMedia("(max-width: 767px)");
  const status = document.getElementById("copy-status");
  document.body.dataset.enhanced = "true";

  const syncMenu = () => {
    const open = menu.open && mobile.matches;
    summary.setAttribute("aria-expanded", String(open));
    summary.setAttribute("aria-label", open ? "Close navigation" : "Open navigation");
    document.body.classList.toggle("menu-visible", open);
    content.inert = open;
  };
  menu.addEventListener("toggle", syncMenu);
  syncMenu();
  menu.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      menu.open = false;
      syncMenu();
      // Anchor navigation should also move keyboard focus, not just scroll.
      if (link.hash && link.origin === location.origin && link.pathname === location.pathname) {
        const target = document.getElementById(link.hash.slice(1));
        if (target) {
          target.setAttribute("tabindex", "-1");
          target.focus({ preventScroll: true });
        }
      }
    });
  });
  document.addEventListener("keydown", (event) => {
    if (!menu.open || !mobile.matches) return;
    if (event.key === "Escape") {
      menu.open = false;
      syncMenu();
      summary.focus();
    } else if (event.key === "Tab") {
      const controls = [summary, ...menu.querySelectorAll("a")];
      const first = controls[0];
      const last = controls[controls.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
  });
  mobile.addEventListener("change", () => {
    if (!mobile.matches) menu.open = false;
    syncMenu();
  });

  document.querySelectorAll("[data-code-tabs]").forEach((consoleElement) => {
    const tablist = consoleElement.querySelector(".code-tabs");
    const tabs = [...tablist.querySelectorAll("[data-tab]")];
    const copy = consoleElement.querySelector(".console-mobile-copy");
    let selected = 0;
    tablist.hidden = false;
    tablist.setAttribute("role", "tablist");
    const updateTabs = () => {
      tabs.forEach((tab, index) => {
        const active = index === selected;
        const panel = document.getElementById(tab.dataset.tab);
        tab.setAttribute("role", "tab");
        tab.setAttribute("aria-selected", String(active));
        tab.tabIndex = active ? 0 : -1;
        panel.dataset.active = String(active);
        // Both panels stay visible on desktop, so do not retain mobile tab semantics there.
        if (mobile.matches) {
          panel.setAttribute("role", "tabpanel");
          panel.setAttribute("aria-labelledby", tab.id);
        } else {
          panel.removeAttribute("role");
          panel.removeAttribute("aria-labelledby");
        }
      });
      copy.dataset.copyTarget = selected === 0 ? "request-code" : "response-code";
      copy.setAttribute("aria-label", selected === 0 ? "Copy request" : "Copy JSON");
    };
    tabs.forEach((tab, index) => {
      tab.addEventListener("click", () => { selected = index; updateTabs(); });
      tab.addEventListener("keydown", (event) => {
        if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
        event.preventDefault();
        if (event.key === "Home") selected = 0;
        else if (event.key === "End") selected = tabs.length - 1;
        else selected = (selected + (event.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length;
        updateTabs();
        tabs[selected].focus();
      });
    });
    mobile.addEventListener("change", updateTabs);
    updateTabs();
  });

  document.querySelectorAll("[data-copy-target]").forEach((button) => {
    button.hidden = false;
    const label = button.querySelector("[data-copy-label]");
    const original = label.textContent;
    let reset;
    button.addEventListener("click", async () => {
      const target = document.getElementById(button.dataset.copyTarget);
      if (!target) return;
      clearTimeout(reset);
      try {
        if (!navigator.clipboard?.writeText) throw new Error("Clipboard unavailable");
        await navigator.clipboard.writeText(target.textContent.trim());
        label.textContent = "Copied!";
        status.textContent = `${button.getAttribute("aria-label")}: copied to clipboard.`;
      } catch {
        // Selecting the snippet is an honest fallback on non-secure HTTP origins or denied access.
        const selection = window.getSelection();
        const range = document.createRange();
        range.selectNodeContents(target);
        selection.removeAllRanges();
        selection.addRange(range);
        target.focus();
        label.textContent = "Select & copy";
        status.textContent = "Clipboard unavailable. Code selected; copy it manually.";
      }
      reset = setTimeout(() => { label.textContent = original; }, 2200);
    });
  });
})();
