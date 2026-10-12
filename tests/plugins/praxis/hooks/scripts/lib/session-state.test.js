const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { describe, test } = require('node:test');

const { REPO_ROOT, tempDir } = require('../../../../../helpers/fixture');

const { sessionId, sweepStaleState } = require(
  path.join(REPO_ROOT, 'plugins/praxis/hooks/scripts/lib/session-state.js'),
);

const DAY_MS = 24 * 60 * 60 * 1000;
const NOW = 1_700_000_000_000;

/** Set an environment variable for the rest of test `t`. */
function setEnv(t, name, value) {
  const previous = process.env[name];
  if (value === undefined) delete process.env[name];
  else process.env[name] = value;
  t.after(() => {
    if (previous === undefined) delete process.env[name];
    else process.env[name] = previous;
  });
}

describe('sessionId', () => {
  test('keeps only filename-safe characters', () => {
    assert.equal(sessionId('abc-123_XYZ'), 'abc-123_XYZ');
    assert.equal(sessionId('../../etc/passwd'), 'etcpasswd');
    assert.equal(sessionId('a b\tc/d\\e:f.g'), 'abcdefg');
  });

  test('falls back to CLAUDE_SESSION_ID, sanitised the same way, when the payload has none', t => {
    setEnv(t, 'CLAUDE_SESSION_ID', 'env/../id');
    for (const raw of [undefined, null, '', 42, {}]) assert.equal(sessionId(raw), 'envid', String(raw));
  });

  test("falls back to 'default' when nothing usable is left", t => {
    setEnv(t, 'CLAUDE_SESSION_ID', undefined);
    assert.equal(sessionId(undefined), 'default');
    assert.equal(sessionId('../..//'), 'default');
    setEnv(t, 'CLAUDE_SESSION_ID', '///');
    assert.equal(sessionId(undefined), 'default');
  });
});

describe('sweepStaleState', () => {
  /** A temp dir standing in for os.tmpdir(), with `files` ({name: age in ms}) aged against NOW. */
  function stateDir(t, files) {
    const dir = tempDir(t);
    setEnv(t, 'TMPDIR', dir);
    t.mock.method(Date, 'now', () => NOW);
    for (const [name, ageMs] of Object.entries(files)) {
      const file = path.join(dir, name);
      fs.writeFileSync(file, '1');
      const mtime = (NOW - ageMs) / 1000;
      fs.utimesSync(file, mtime, mtime);
    }
    return dir;
  }

  test('removes files with a swept prefix older than the retention, and nothing else', t => {
    const dir = stateDir(t, {
      'claude-a-old': 15 * DAY_MS,
      'claude-a-fresh': 13 * DAY_MS,
      'claude-b-old': 15 * DAY_MS,
      'other-old': 15 * DAY_MS,
    });
    sweepStaleState(['claude-a-', 'claude-b-'], [], 14);
    assert.deepEqual(fs.readdirSync(dir).sort(), ['claude-a-fresh', 'other-old']);
  });

  test('keeps a file exactly at the cutoff and removes one a second older', t => {
    const dir = stateDir(t, { 'p-edge': 14 * DAY_MS, 'p-older': 14 * DAY_MS + 1000 });
    sweepStaleState(['p-'], [], 14);
    assert.deepEqual(fs.readdirSync(dir), ['p-edge']);
  });

  test('preserves the files in `keep`, matched by basename', t => {
    const dir = stateDir(t, { 'p-mine': 30 * DAY_MS, 'p-theirs': 30 * DAY_MS });
    sweepStaleState(['p-'], [path.join('/elsewhere', 'p-mine')], 14);
    assert.deepEqual(fs.readdirSync(dir), ['p-mine']);
  });

  test('leaves directories alone, even with a swept prefix', t => {
    const dir = stateDir(t, {});
    fs.mkdirSync(path.join(dir, 'p-dir'));
    const mtime = (NOW - 30 * DAY_MS) / 1000;
    fs.utimesSync(path.join(dir, 'p-dir'), mtime, mtime);
    sweepStaleState(['p-'], [], 14);
    assert.deepEqual(fs.readdirSync(dir), ['p-dir']);
  });

  test('does not throw when the temp directory cannot be read', t => {
    setEnv(t, 'TMPDIR', path.join(tempDir(t), 'missing'));
    assert.doesNotThrow(() => sweepStaleState(['p-'], [], 14));
  });
});
