import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import { test } from 'node:test';

const source = readFileSync(new URL('../static/website/js/theme.js', import.meta.url), 'utf8');
class Element {
  constructor(attrs = {}, children = []) {
    this.attrs = { ...attrs };
    this.children = children;
    this.hidden = Object.hasOwn(attrs, 'hidden');
    this.listeners = new Map();
  }
  getAttribute(name) { return this.attrs[name] ?? null; }
  setAttribute(name, value) { this.attrs[name] = String(value); }
  querySelectorAll(selector) {
    const attr = selector.slice(1, -1);
    return this.children.filter(child => Object.hasOwn(child.attrs, attr));
  }
  addEventListener(name, listener) {
    this.listeners.set(name, [...(this.listeners.get(name) ?? []), listener]);
  }
  click() { for (const listener of this.listeners.get('click') ?? []) listener(); }
}
function setup({ preference = null, classes = [], storageFailure = false, readyState = 'loading', noControls = false } = {}) {
  const classNames = new Set(classes);
  const root = { classList: {
    contains: name => classNames.has(name),
    add: (...names) => names.forEach(name => classNames.add(name)),
    remove: (...names) => names.forEach(name => classNames.delete(name)),
  } };
  const toggles = noControls ? [] : Array.from({ length: 2 }, () => new Element({ 'data-theme-toggle': '', hidden: '' }, [
    new Element({ 'data-theme-icon': 'light' }), new Element({ 'data-theme-icon': 'dark' }),
  ]));
  const choices = noControls ? [] : ['light', 'dark'].map(theme => new Element({ 'data-theme-choice': theme }));
  const containers = noControls ? [] : [new Element({ 'data-theme-options': '', hidden: '' }, choices)];
  const listeners = new Map();
  const document = {
    documentElement: root, readyState,
    querySelectorAll: selector => ({ '[data-theme-toggle]': toggles, '[data-theme-choice]': choices, '[data-theme-options]': containers })[selector],
    addEventListener(name, callback, options) { listeners.set(name, { callback, options }); },
  };
  const writes = [];
  let reads = 0;
  const context = { document, localStorage: {
    getItem(key) { reads++; assert.equal(key, 'theme'); if (storageFailure) throw Error('storage blocked'); return preference; },
    setItem(key, value) { if (storageFailure) throw Error('storage blocked'); writes.push([key, value]); },
  } };
  vm.runInNewContext(source, context, { filename: 'theme.js' });
  return {
    classes: classNames, toggles, choices, containers, writes, context,
    reads: () => reads,
    ready() {
      const listener = listeners.get('DOMContentLoaded');
      assert.ok(listener);
      assert.equal(listener.options.once, true);
      listener.callback();
    },
  };
}
function checkControls(env, theme) {
  assert.deepEqual([...env.classes], [theme]);
  const target = theme === 'light' ? 'dark' : 'light';
  for (const button of env.toggles) {
    assert.equal(button.hidden, false);
    assert.equal(button.getAttribute('aria-label'), `Switch to ${target} mode`);
    assert.equal(button.getAttribute('title'), `Switch to ${target} mode`);
    assert.equal(button.getAttribute('aria-pressed'), null);
    for (const icon of button.children) assert.equal(icon.hidden, icon.getAttribute('data-theme-icon') !== target);
  }
  for (const choice of env.choices) assert.equal(choice.getAttribute('aria-pressed'), String(choice.getAttribute('data-theme-choice') === theme));
  for (const container of env.containers) assert.equal(container.hidden, false);
}
for (const [label, preference, expected] of [
  ['default light (no OS lookup)', null, 'light'], ['saved dark', 'dark', 'dark'],
  ['saved light', 'light', 'light'], ['invalid preference', 'sepia', 'light'],
]) {
  test(label, () => {
    const env = setup({ preference });
    assert.deepEqual([...env.classes], [expected]); // Synchronous, before DOMContentLoaded.
    assert.ok(env.toggles.every(button => button.hidden && !button.listeners.size));
    assert.ok(env.containers.every(container => container.hidden));
    assert.deepEqual(env.writes, []);
    env.ready();
    checkControls(env, expected);
    assert.deepEqual(Object.keys(env.context).sort(), ['document', 'localStorage']);
  });
}
for (const theme of ['light', 'dark']) {
  test(`explicit root ${theme} wins without storage read`, () => {
    const env = setup({ classes: [theme], preference: theme === 'dark' ? 'light' : 'dark' });
    assert.deepEqual([...env.classes], [theme]);
    assert.equal(env.reads(), 0);
    env.ready(); checkControls(env, theme);
  });
}
test('toggle twice synchronizes all controls and persists', () => {
  const env = setup(); env.ready();
  env.toggles[0].click(); checkControls(env, 'dark');
  env.toggles[1].click(); checkControls(env, 'light');
  assert.deepEqual(env.writes, [['theme', 'dark'], ['theme', 'light']]);
});
test('direct choices synchronize controls, including repeated selection', () => {
  const env = setup(); env.ready();
  env.choices[1].click(); checkControls(env, 'dark');
  env.choices[1].click(); checkControls(env, 'dark');
  env.choices[0].click(); checkControls(env, 'light');
  assert.deepEqual(env.writes, [['theme', 'dark'], ['theme', 'dark'], ['theme', 'light']]);
});
test('blocked reads and writes do not prevent controls working', () => {
  const env = setup({ storageFailure: true });
  assert.deepEqual([...env.classes], ['light']);
  env.ready(); checkControls(env, 'light');
  env.toggles[0].click(); checkControls(env, 'dark');
  env.choices[0].click(); checkControls(env, 'light');
});
test('missing localStorage is tolerated', () => {
  const env = setup(); delete env.context.localStorage;
  env.ready(); env.toggles[0].click(); checkControls(env, 'dark');
});
test('already-ready document binds immediately', () => checkControls(setup({ readyState: 'complete' }), 'light'));
test('pages without controls are safe', () => { const env = setup({ noControls: true }); env.ready(); });
