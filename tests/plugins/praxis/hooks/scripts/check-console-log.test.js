// Tests for the console.log hook: the report/carry-forward split, and the
// process contract every shipped hook entry point owes its caller.
//
// applyCooldown is where a wrong answer is silent -- a finding suppressed
// forever, or one repeated on every edit. Whether the advice is good advice, and
// what the default cooldown should be, are judgment calls and deliberately not
// asserted here.

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const SCRIPT = path.resolve(
  __dirname,
  '../../../../../plugins/praxis/hooks/scripts/check-console-log.js'
);
const { applyCooldown } = require(SCRIPT);

const COOLDOWN = 10;

const finding = (file, text) => ({ file, lineNumber: 1, text, key: `${file}:${text}` });
const A = finding('src/a.js', 'console.log(a)');
const B = finding('src/b.js', 'console.log(b)');

const GIT_ENV = {
  GIT_AUTHOR_NAME: 'Grimoire Fixture',
  GIT_AUTHOR_EMAIL: 'fixture@example.invalid',
  GIT_COMMITTER_NAME: 'Grimoire Fixture',
  GIT_COMMITTER_EMAIL: 'fixture@example.invalid'
};

/**
 * Spawn the hook and assert the contract it owes its caller: exit 0, and either
 * nothing on stdout or exactly one well-formed JSON object. JSON.parse is the
 * "exactly one" half -- two concatenated objects do not parse.
 */
function spawnHook({ stdin = '', cwd, env = {} } = {}) {
  const r = spawnSync(process.execPath, [SCRIPT], {
    input: stdin,
    cwd,
    encoding: 'utf8',
    env: { ...process.env, ...env }
  });

  assert.equal(r.status, 0, `exited ${r.status}, signal ${r.signal}; stderr: ${r.stderr}`);
  const out = r.stdout.trim();
  if (out === '') return null;

  const payload = JSON.parse(out);
  assert.equal(typeof payload, 'object');
  assert.notEqual(payload, null);
  return payload;
}

/** A throwaway repository plus an isolated temp directory for the hook's state. */
function withFixture(fn) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'grimoire-console-'));
  const repo = path.join(dir, 'repo');
  const state = path.join(dir, 'state');
  fs.mkdirSync(repo);
  fs.mkdirSync(state);

  const git = args => {
    const r = spawnSync('git', args, { cwd: repo, encoding: 'utf8', env: { ...process.env, ...GIT_ENV } });
    assert.equal(r.status, 0, `git ${args.join(' ')} failed: ${r.stderr}`);
  };
  git(['init', '-q']);
  git(['config', 'commit.gpgsign', 'false']);
  fs.writeFileSync(path.join(repo, 'README.md'), 'fixture\n');
  git(['add', '-A']);
  git(['commit', '-qm', 'fixture']);

  try {
    return fn({ repo, env: { TMPDIR: state, TMP: state, TEMP: state } });
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

test('applyCooldown reports a finding new to the session immediately', () => {
  const { report, state } = applyCooldown([A], { seen: [], cooldown: 0 }, COOLDOWN);
  assert.deepEqual(report, [A]);
  assert.deepEqual(state, { seen: [A.key], cooldown: COOLDOWN });
});

test('applyCooldown holds a repeat back until the cooldown elapses', () => {
  const { report, state } = applyCooldown([A], { seen: [A.key], cooldown: 3 }, COOLDOWN);
  assert.deepEqual(report, []);
  assert.deepEqual(state, { seen: [A.key], cooldown: 2 });
});

test('applyCooldown releases a repeat once the cooldown reaches zero', () => {
  const { report, state } = applyCooldown([A], { seen: [A.key], cooldown: 0 }, COOLDOWN);
  assert.deepEqual(report, [A]);
  assert.deepEqual(state, { seen: [A.key], cooldown: COOLDOWN });
});

test('applyCooldown restarts the cooldown whenever it reports something', () => {
  // Otherwise a finding is announced and then immediately repeated on the next
  // edit.
  const { state } = applyCooldown([A], { seen: [], cooldown: 4 }, COOLDOWN);
  assert.equal(state.cooldown, COOLDOWN);
});

test('applyCooldown reports the fresh finding while the repeat is still cooling', () => {
  const { report, state } = applyCooldown([A, B], { seen: [B.key], cooldown: 5 }, COOLDOWN);
  assert.deepEqual(report, [A]);
  assert.deepEqual(state.seen.sort(), [A.key, B.key].sort());
  assert.equal(state.cooldown, COOLDOWN);
});

test('applyCooldown stops decrementing at zero', () => {
  const { report, state } = applyCooldown([A], { seen: [A.key], cooldown: 0 }, COOLDOWN);
  assert.deepEqual(report, [A]);

  const quiet = applyCooldown([], { seen: [], cooldown: 0 }, COOLDOWN);
  assert.deepEqual(quiet.report, []);
  assert.equal(quiet.state.cooldown, 0);
});

test('applyCooldown drops a finding that has disappeared out of seen', () => {
  const { state } = applyCooldown([], { seen: [A.key, B.key], cooldown: 3 }, COOLDOWN);
  assert.deepEqual(state.seen, []);
  assert.equal(state.cooldown, 2);
});

test('applyCooldown counts a reintroduced statement as new again', () => {
  // Keyed on the line's text rather than its number, so an edit above a debug
  // statement is not a new finding -- but removing and re-adding it is.
  let state = applyCooldown([A], { seen: [], cooldown: 0 }, COOLDOWN).state;
  assert.deepEqual(state.seen, [A.key]);

  state = applyCooldown([], state, COOLDOWN).state;
  assert.deepEqual(state.seen, []);

  const again = applyCooldown([A], state, COOLDOWN);
  assert.deepEqual(again.report, [A]);
  assert.equal(again.state.cooldown, COOLDOWN);
});

test('applyCooldown rebuilds seen from what is present, never growing it', () => {
  const { state } = applyCooldown([A], { seen: [A.key, 'src/gone.js:console.log(gone)'], cooldown: 0 }, COOLDOWN);
  assert.deepEqual(state.seen, [A.key]);
});

test('applyCooldown honours the cooldown length it is handed', () => {
  assert.equal(applyCooldown([A], { seen: [], cooldown: 0 }, 3).state.cooldown, 3);
});

test('contract: malformed JSON on stdin', () => {
  withFixture(({ repo, env }) => {
    assert.equal(spawnHook({ stdin: '{not json', cwd: repo, env }), null);
  });
});

test('contract: empty stdin', () => {
  withFixture(({ repo, env }) => {
    assert.equal(spawnHook({ stdin: '', cwd: repo, env }), null);
  });
});

test('contract: a payload with no transcript_path and no session_id', () => {
  withFixture(({ repo, env }) => {
    assert.equal(spawnHook({ stdin: JSON.stringify({ hook_event_name: 'PostToolUse' }), cwd: repo, env }), null);
  });
});

test('contract: outside a git repository', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'grimoire-console-bare-'));
  try {
    assert.equal(
      spawnHook({ stdin: '{}', cwd: dir, env: { TMPDIR: dir, TMP: dir, TEMP: dir } }),
      null
    );
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

test('contract: a real finding travels as exactly one JSON object', () => {
  withFixture(({ repo, env }) => {
    fs.mkdirSync(path.join(repo, 'src'));
    fs.writeFileSync(path.join(repo, 'src', 'app.js'), 'console.log("debug");\n');

    const payload = spawnHook({ stdin: JSON.stringify({ session_id: 'contract-test' }), cwd: repo, env });
    assert.equal(payload.hookSpecificOutput.hookEventName, 'PostToolUse');
    assert.match(payload.hookSpecificOutput.additionalContext, /console\.log found in src\/app\.js/);
  });
});
