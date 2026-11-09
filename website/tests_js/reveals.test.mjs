import assert from 'node:assert/strict';
import { test } from 'node:test';
import { initReveals } from '../static_src/src/reveals.mjs';

class Events {
  listeners = new Map();
  addEventListener(type, callback) {
    if (!this.listeners.has(type)) this.listeners.set(type, new Set());
    this.listeners.get(type).add(callback);
  }
  removeEventListener(type, callback) { this.listeners.get(type)?.delete(callback); }
  dispatch(type, properties = {}) {
    const event = { type, ...properties };
    for (const callback of [...(this.listeners.get(type) ?? [])]) callback(event);
  }
}

class Style {
  opacity = '';
  transform = '';
  setProperty(name, value) { this[name] = String(value); }
  getPropertyValue(name) { return this[name] ?? ''; }
  getPropertyPriority() { return ''; }
  removeProperty(name) { const old = this[name]; this[name] = ''; return old; }
}

class Element extends Events {
  constructor({ group, stagger = false, reveal = false, top = 100, opacity = '', transform = '' } = {}, children = []) {
    super();
    this.dataset = {};
    if (group !== undefined) this.dataset.revealGroup = group;
    if (reveal) this.dataset.reveal = '';
    if (stagger) this.dataset.revealStagger = '';
    this.children = children;
    for (const child of children) child.parentElement = this;
    this.style = new Style();
    Object.assign(this.style, { opacity, transform });
    this.top = top;
    this.nodeType = 1;
  }
  animations = [];
  animate() {}
  getAnimations() { return this.animations; }
  matches(selector) {
    return (selector === '[data-reveal]' && 'reveal' in this.dataset)
      || (selector === '[data-reveal-group]' && 'revealGroup' in this.dataset)
      || (selector === '[data-reveal-stagger]' && 'revealStagger' in this.dataset);
  }
  closest(selector) {
    for (let node = this; node; node = node.parentElement) if (node.matches(selector)) return node;
    return null;
  }
  contains(target) { return target === this || this.children.some(child => child.contains(target)); }
  querySelectorAll(selector) {
    return this.children.flatMap(child => [
      ...(child.matches(selector) ? [child] : []), ...child.querySelectorAll(selector),
    ]);
  }
  getBoundingClientRect() {
    return { top: this.top, bottom: this.top + 40, left: 0, right: 100, width: 100, height: 40 };
  }
}

const target = (options = {}, children = []) => new Element({ reveal: true, ...options }, children);
const group = (name, children) => new Element({ group: name }, children);

function setup(groups, { reduced = false, missing, throwAnimation = false } = {}) {
  const doc = new Events();
  const root = new Element({}, groups);
  doc.querySelectorAll = selector => root.querySelectorAll(selector);
  doc.documentElement = { clientHeight: 800, clientWidth: 1200 };
  const media = new Events();
  media.matches = reduced;
  media.media = '(prefers-reduced-motion: reduce)';
  media.addListener = callback => media.addEventListener('change', callback);
  media.removeListener = callback => media.removeEventListener('change', callback);
  const observers = [];
  class IntersectionObserver {
    constructor(callback, options) {
      if (missing === 'broken IO') throw new Error('observer unavailable');
      this.callback = callback;
      this.options = options;
      this.observed = new Set();
      this.unobserved = [];
      this.disconnects = 0;
      observers.push(this);
    }
    observe(element) { this.observed.add(element); }
    unobserve(element) { this.unobserved.push(element); this.observed.delete(element); }
    disconnect() { this.disconnects++; this.observed.clear(); }
    // Deliberately permit delivery of queued/stale entries after disconnect/unobserve.
    emit(elements, isIntersecting = true) {
      this.callback(elements.map(element => ({
        target: element, isIntersecting, intersectionRatio: isIntersecting ? 1 : 0,
      })), this);
    }
  }
  class BrowserElement extends Element {}
  if (missing === 'WAAPI') {
    BrowserElement.prototype.animate = undefined;
    for (const element of root.querySelectorAll('[data-reveal]')) element.animate = undefined;
  }
  const win = Object.assign(new Events(), {
    innerHeight: 800, innerWidth: 1200, Element: BrowserElement, HTMLElement: BrowserElement,
    IntersectionObserver, matchMedia: () => media,
  });
  if (missing === 'IO') delete win.IntersectionObserver;
  if (missing === 'matchMedia') delete win.matchMedia;
  const calls = [];
  function animate(element, keyframes, options) {
    const observer = observers[0];
    // Check ordering inside animate, not just the eventual observer state.
    if (observer?.observed.has(element)) assert.fail('unobserve must happen before animate');
    let resolve;
    const finished = new Promise(done => { resolve = done; });
    const call = {
      element, keyframes, options, cancelled: 0,
      control: {
        finished,
        then: (...args) => finished.then(...args),
        cancel() { call.cancelled++; resolve(); },
        stop() { call.cancelled++; resolve(); },
      },
      finish: resolve,
    };
    calls.push(call);
    element.animations.push(call.control);
    // Model animation-side inline writes so restoration is observable.
    element.style.opacity = '0';
    element.style.transform = 'translateY(14px)';
    if (throwAnimation) throw new Error('animation unavailable');
    return call.control;
  }
  let cleanup;
  return {
    doc, win, media, calls, observers,
    start() { cleanup = initReveals({ animate, win, doc }); assert.equal(typeof cleanup, 'function'); return cleanup; },
    cleanup() { cleanup(); },
    preference(matches) { media.matches = matches; media.dispatch('change', { matches }); },
    focus(element) { doc.dispatch('focusin', { target: element }); },
  };
}

function original(element, opacity = '', transform = '') {
  assert.equal(element.style.opacity, opacity, 'original inline opacity restored');
  assert.equal(element.style.transform, transform, 'original inline transform restored');
}
function animationContract(call, delay) {
  assert.deepEqual(call.keyframes, { opacity: [0, 1], transform: ['translateY(14px)', 'none'] });
  assert.equal(call.options.duration, 0.4);
  assert.deepEqual(call.options.ease, [0.22, 1, 0.36, 1]);
  assert.ok(Math.abs(call.options.delay - delay) < 1e-9, `expected delay ${delay}, got ${call.options.delay}`);
}
const settle = async () => { await Promise.resolve(); await Promise.resolve(); await Promise.resolve(); };

test('hero viewport targets start immediately; offscreen hero and all scroll targets share one observer', () => {
  const visible = target();
  const below = target({ top: 900 });
  const above = target({ top: -100 });
  const scroll = target();
  const env = setup([group('hero', [visible, below, above]), group('scroll', [scroll])]);
  env.start();
  assert.deepEqual(env.calls.map(call => call.element), [visible]);
  animationContract(env.calls[0], 0);
  assert.equal(env.observers.length, 1);
  assert.equal(env.observers[0].options.threshold, 0.12);
  assert.equal(env.observers[0].options.rootMargin, '0px 0px -24px 0px');
  assert.deepEqual(new Set(env.observers[0].observed), new Set([below, above, scroll]));
  for (const element of [below, above, scroll]) original(element);
  env.cleanup();
});

test('intersection animates each target once, unobserves before start, and ignores exits and re-entry', () => {
  const element = target();
  const env = setup([group('scroll', [element])]);
  env.start();
  const observer = env.observers[0];
  observer.emit([element], false);
  assert.equal(env.calls.length, 0);
  original(element);
  observer.emit([element, element]);
  assert.equal(env.calls.length, 1);
  assert.ok(observer.unobserved.includes(element));
  observer.emit([element], false);
  observer.emit([element]);
  assert.equal(env.calls.length, 1);
  env.cleanup();
});

test('non-card reveals retain the bounded per-batch stagger', () => {
  const first = Array.from({ length: 7 }, () => target());
  const second = Array.from({ length: 3 }, () => target());
  const env = setup([group('scroll', first), group('scroll', second)]);
  env.start();
  env.observers[0].emit([...first.slice(0, 6), ...second]);
  first.slice(0, 6).forEach((element, index) => animationContract(
    env.calls.find(call => call.element === element), Math.min(index * 0.05, 0.15),
  ));
  second.forEach((element, index) => animationContract(
    env.calls.find(call => call.element === element), index * 0.05,
  ));
  env.observers[0].emit([first[6]]);
  animationContract(env.calls.at(-1), 0);
  env.cleanup();
});

test('every card has a distinct DOM-order delay across unordered observer batches and grids', () => {
  const first = Array.from({ length: 6 }, () => target());
  const second = Array.from({ length: 3 }, () => target());
  const env = setup([group('scroll', [
    new Element({ stagger: true }, first), new Element({ stagger: true }, second),
  ])]);
  env.start();
  env.observers[0].emit([first[2], first[0], first[1], second[0]]);
  env.observers[0].emit([first[5], first[3], first[4], second[2], second[1]]);
  for (const cards of [first, second]) {
    cards.forEach((element, index) => animationContract(
      env.calls.find(call => call.element === element), index * 0.08,
    ));
  }
  const count = env.calls.length;
  env.observers[0].emit([...first, ...second]);
  assert.equal(env.calls.length, count, 'staggered cards still never replay');
  env.cleanup();
});

test('hero overview cards stagger individually after the introductory entrance', () => {
  const cards = Array.from({ length: 3 }, () => target());
  const env = setup([group('hero', [new Element({ stagger: true }, cards)])]);
  env.start();
  env.calls.forEach((call, index) => animationContract(call, 0.15 + index * 0.08));
  env.cleanup();
});

test('immediate hero animations use the same bounded stagger', () => {
  const elements = Array.from({ length: 6 }, () => target());
  const env = setup([group('hero', elements)]);
  env.start();
  assert.equal(env.calls.length, elements.length);
  env.calls.forEach((call, index) => animationContract(call, Math.min(index * 0.05, 0.15)));
  env.cleanup();
});

test('initial reduced motion leaves everything visible without animations or observers', () => {
  const elements = [target(), target({ top: 900 })];
  const env = setup([group('hero', elements)], { reduced: true });
  env.start();
  assert.equal(env.calls.length, 0);
  assert.equal(env.observers.length, 0);
  elements.forEach(element => original(element));
  env.preference(false);
  assert.equal(env.calls.length, 0);
  assert.equal(env.observers.length, 0);
  env.cleanup();
});

test('live reduced motion cancels active effects, restores styles, and permanently disables reveals', async () => {
  const active = target({ opacity: '0.8', transform: 'scale(1.1)' });
  const pending = target();
  const env = setup([group('hero', [active]), group('scroll', [pending])]);
  env.start();
  env.preference(true);
  await settle();
  assert.ok(env.observers[0].disconnects > 0);
  assert.ok(env.calls[0].cancelled > 0);
  original(active, '0.8', 'scale(1.1)');
  original(pending);
  env.preference(false);
  env.observers[0].emit([pending, active]);
  assert.equal(env.calls.length, 1);
  env.cleanup();
});

for (const descendant of [false, true]) {
  test(`focus on ${descendant ? 'a descendant' : 'the target'} skips pending reveals and cancels active ones`, async () => {
    const pendingControl = new Element();
    const activeControl = new Element();
    const pending = target({}, [pendingControl]);
    const active = target({ opacity: '0.9', transform: 'scale(1)' }, [activeControl]);
    const env = setup([group('hero', [active]), group('scroll', [pending])]);
    env.start();
    env.focus(descendant ? pendingControl : pending);
    original(pending);
    env.observers[0].emit([pending]);
    assert.equal(env.calls.length, 1);
    env.focus(descendant ? activeControl : active);
    await settle();
    assert.ok(env.calls[0].cancelled > 0);
    original(active, '0.9', 'scale(1)');
    env.observers[0].emit([active, pending]);
    assert.equal(env.calls.length, 1);
    env.cleanup();
  });
}

for (const missing of ['WAAPI', 'IO', 'matchMedia', 'broken IO']) {
  test(`missing ${missing} leaves targets visible without animation`, () => {
    const elements = [target(), target({ top: 900 })];
    const env = setup([group('hero', elements)], { missing });
    env.start();
    assert.equal(env.calls.length, 0);
    assert.equal(env.observers.length, 0);
    elements.forEach(element => original(element));
    env.cleanup();
  });
}

test('normal completion restores pre-existing inline opacity and transform', async () => {
  const element = target({ opacity: '0.75', transform: 'rotate(2deg)' });
  const env = setup([group('hero', [element])]);
  env.start();
  env.calls[0].finish();
  await settle();
  original(element, '0.75', 'rotate(2deg)');
  env.cleanup();
});

test('thrown animate restores styles and does not replay the target', () => {
  const element = target({ opacity: '0.85', transform: 'scale(1)' });
  const env = setup([group('scroll', [element])], { throwAnimation: true });
  env.start();
  assert.doesNotThrow(() => env.observers[0].emit([element]));
  original(element, '0.85', 'scale(1)');
  assert.ok(env.calls[0].cancelled > 0, 'partially started native effect is cancelled');
  env.observers[0].emit([element]);
  assert.equal(env.calls.length, 1);
  env.cleanup();
});

for (const pagehide of [false, true]) {
  test(`${pagehide ? 'pagehide (including BFCache)' : 'explicit cleanup'} disconnects, cancels, restores, and prevents replay`, async () => {
    const active = target();
    const pending = target();
    const env = setup([group('hero', [active]), group('scroll', [pending])]);
    env.start();
    if (pagehide) env.win.dispatch('pagehide', { persisted: true });
    else env.cleanup();
    await settle();
    assert.ok(env.observers[0].disconnects > 0);
    assert.ok(env.calls[0].cancelled > 0);
    original(active);
    original(pending);
    env.win.dispatch('pageshow', { persisted: true });
    env.preference(false);
    env.observers[0].emit([active, pending]);
    assert.equal(env.calls.length, 1);
    assert.doesNotThrow(() => env.cleanup(), 'cleanup is idempotent');
  });
}
