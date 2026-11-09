/* Content stays visible by default: only a running effect changes its appearance. */
export function initReveals({ animate, win = window, doc = document }) {
  const noop = () => {};
  if (!win.matchMedia || !win.IntersectionObserver || !win.Element?.prototype.animate) return noop;
  const motion = win.matchMedia("(prefers-reduced-motion: reduce)");
  if (motion.matches) return noop;

  const elements = [...doc.querySelectorAll("[data-reveal]")];
  // Stable grid positions keep every card distinct, even across observer batches.
  const cardDelays = new Map();
  const gridPositions = new Map();
  elements.forEach((element) => {
    const grid = element.closest("[data-reveal-stagger]");
    if (!grid) return;
    const index = gridPositions.get(grid) || 0;
    const hero = element.closest("[data-reveal-group]")?.dataset.revealGroup === "hero";
    cardDelays.set(element, (hero ? 0.15 : 0) + index * 0.08);
    gridPositions.set(grid, index + 1);
  });
  const seen = new WeakSet();
  const active = new Map();
  let disabled = false;
  let observer;

  const restore = (element, styles) => {
    for (const [name, value, priority] of styles) {
      if (value) element.style.setProperty(name, value, priority);
      else element.style.removeProperty(name);
    }
  };
  const finish = (element) => {
    seen.add(element);
    observer.unobserve(element);
    const effect = active.get(element);
    if (!effect) return;
    active.delete(element);
    effect.controls.cancel();
    restore(element, effect.styles);
  };
  const reveal = (element, delay) => {
    if (disabled || motion.matches || seen.has(element)) return;
    seen.add(element);
    observer.unobserve(element);
    // Never fade a keyboard-focused control or an ancestor containing it.
    if (element.contains(doc.activeElement)) return;
    const styles = ["opacity", "transform"].map((name) => [
      name, element.style.getPropertyValue(name), element.style.getPropertyPriority(name),
    ]);
    const previous = new Set(element.getAnimations());
    try {
      const controls = animate(element, {
        opacity: [0, 1],
        transform: ["translateY(14px)", "none"],
      }, { duration: 0.4, delay: cardDelays.get(element) ?? delay, ease: [0.22, 1, 0.36, 1] });
      active.set(element, { controls, styles });
      controls.then(() => {
        if (active.get(element)?.controls !== controls) return;
        active.delete(element);
        restore(element, styles);
      });
    } catch {
      // Also unwind partially-created native effects if an animation cannot start.
      element.getAnimations().filter((effect) => !previous.has(effect)).forEach((effect) => effect.cancel());
      restore(element, styles);
    }
  };

  try {
    observer = new win.IntersectionObserver((entries) => {
      const stagger = new Map();
      entries.filter((entry) => entry.isIntersecting).forEach(({ target }) => {
        if (seen.has(target)) return;
        const group = target.closest("[data-reveal-group]");
        const index = stagger.get(group) || 0;
        reveal(target, Math.min(index * 0.05, 0.15));
        stagger.set(group, index + 1);
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -24px 0px" });
  } catch {
    return noop;
  }

  const onFocus = (event) => {
    elements.filter((element) => element.contains(event.target)).forEach(finish);
  };
  const cleanup = () => {
    disabled = true;
    observer.disconnect();
    [...active.keys()].forEach(finish);
    motion.removeEventListener("change", onPreference);
    doc.removeEventListener("focusin", onFocus);
    win.removeEventListener("pagehide", cleanup);
  };
  const onPreference = () => {
    // Once motion is disabled, leave everything static until a real page reload.
    if (motion.matches) cleanup();
  };
  motion.addEventListener("change", onPreference);
  doc.addEventListener("focusin", onFocus);
  win.addEventListener("pagehide", cleanup);

  let index = 0;
  elements.forEach((element) => {
    const group = element.closest("[data-reveal-group]");
    const rect = element.getBoundingClientRect();
    const visible = rect.width > 0 && rect.height > 0
      && rect.top < win.innerHeight && rect.bottom > 0
      && rect.left < win.innerWidth && rect.right > 0;
    if (group?.dataset.revealGroup === "hero" && visible) {
      reveal(element, Math.min(index++ * 0.05, 0.15));
    } else {
      observer.observe(element);
    }
  });
  return cleanup;
}
