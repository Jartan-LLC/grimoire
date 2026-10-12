const assert = require('node:assert/strict');
const path = require('node:path');
const { describe, test } = require('node:test');

const { REPO_ROOT } = require('../../../../helpers/fixture');

const { applyCooldown } = require(path.join(REPO_ROOT, 'plugins/praxis/hooks/scripts/check-console-log.js'));

const COOLDOWN = 10;

const finding = (file, text) => ({ file, lineNumber: 1, text, key: `${file}:${text}` });
const A = finding('a.js', 'console.log(a)');
const B = finding('b.js', 'console.log(b)');

describe('applyCooldown', () => {
  test('reports a finding new to the session even while the cooldown runs', () => {
    const { report, state } = applyCooldown([A, B], { seen: [A.key], cooldown: 5 }, COOLDOWN);
    assert.deepEqual(report, [B]);
    assert.deepEqual(state, { seen: [A.key, B.key], cooldown: COOLDOWN });
  });

  test('withholds an already-reported finding while the cooldown runs, counting it down', () => {
    const { report, state } = applyCooldown([A], { seen: [A.key], cooldown: 3 }, COOLDOWN);
    assert.deepEqual(report, []);
    assert.deepEqual(state, { seen: [A.key], cooldown: 2 });
  });

  test('repeats every present finding once the cooldown has run out, and restarts it', () => {
    const { report, state } = applyCooldown([A, B], { seen: [A.key], cooldown: 0 }, COOLDOWN);
    assert.deepEqual(report, [A, B]);
    assert.deepEqual(state, { seen: [A.key, B.key], cooldown: COOLDOWN });
  });

  test('forgets a finding that disappeared, so its return counts as new', () => {
    const gone = applyCooldown([], { seen: [A.key], cooldown: 5 }, COOLDOWN);
    assert.deepEqual(gone, { report: [], state: { seen: [], cooldown: 4 } });
    const back = applyCooldown([A], gone.state, COOLDOWN);
    assert.deepEqual(back.report, [A]);
  });

  test('never counts the cooldown below zero', () => {
    assert.deepEqual(applyCooldown([], { seen: [], cooldown: 0 }, COOLDOWN).state.cooldown, 0);
  });
});
