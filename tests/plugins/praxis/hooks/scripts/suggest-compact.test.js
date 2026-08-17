// Process contract for the strategic-compact hook.
//
// The resolvers it composes are unit-tested in lib/transcript-context.test.js.
// What is left here is the contract: exit 0 and at most one JSON object, whatever
// arrives on stdin, with both signals sharing the single payload a hook is
// allowed. Every spawn gets its own temp directory, since the hook writes
// per-session state there.
//
// The thresholds and the wording are tuning, not facts, so only the disable
// switch and the shape of the payload are asserted.

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const SCRIPT = path.resolve(__dirname, '../../../../../plugins/praxis/hooks/scripts/suggest-compact.js');

/** Spawn the hook with isolated state, asserting exit 0 and at most one JSON object. */
function spawnHook({ stdin = '', env = {} } = {}) {
  const state = fs.mkdtempSync(path.join(os.tmpdir(), 'grimoire-compact-'));
  try {
    const r = spawnSync(process.execPath, [SCRIPT], {
      input: stdin,
      encoding: 'utf8',
      env: { ...process.env, TMPDIR: state, TMP: state, TEMP: state, ...env }
    });

    assert.equal(r.status, 0, `exited ${r.status}, signal ${r.signal}; stderr: ${r.stderr}`);
    const out = r.stdout.trim();
    if (out === '') return null;

    const payload = JSON.parse(out);
    assert.equal(typeof payload, 'object');
    assert.notEqual(payload, null);
    return payload;
  } finally {
    fs.rmSync(state, { recursive: true, force: true });
  }
}

/** A one-record transcript reporting `tokens` of context. */
function transcript(tokens) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'grimoire-compact-tx-'));
  const file = path.join(dir, 'transcript.jsonl');
  fs.writeFileSync(file, JSON.stringify({ message: { usage: { input_tokens: tokens } } }) + '\n');
  return { dir, file };
}

function withTranscript(tokens, fn) {
  const { dir, file } = transcript(tokens);
  try {
    return fn(file);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

test('contract: malformed JSON on stdin', () => {
  assert.equal(spawnHook({ stdin: '{"session_id": ' }), null);
});

test('contract: empty stdin', () => {
  assert.equal(spawnHook({ stdin: '' }), null);
});

test('contract: a payload with no transcript_path', () => {
  assert.equal(spawnHook({ stdin: JSON.stringify({ session_id: 'contract-test' }) }), null);
});

test('contract: a transcript_path that is not a string', () => {
  assert.equal(spawnHook({ stdin: JSON.stringify({ session_id: 'x', transcript_path: 42 }) }), null);
});

test('contract: a transcript_path pointing at nothing', () => {
  const absent = path.join(os.tmpdir(), 'grimoire-compact-absent-4471.jsonl');
  assert.equal(spawnHook({ stdin: JSON.stringify({ session_id: 'x', transcript_path: absent }) }), null);
});

test('contract: the count signal emits exactly one JSON object', () => {
  const payload = spawnHook({
    stdin: JSON.stringify({ session_id: 'contract-test' }),
    env: { COMPACT_THRESHOLD: '1' }
  });
  assert.equal(payload.hookSpecificOutput.hookEventName, 'PreToolUse');
  assert.match(payload.hookSpecificOutput.additionalContext, /1 tool calls reached/);
});

test('contract: both signals share the one payload a hook is allowed', () => {
  withTranscript(400000, file => {
    const payload = spawnHook({
      stdin: JSON.stringify({ session_id: 'contract-test', transcript_path: file }),
      env: { COMPACT_THRESHOLD: '1', COMPACT_CONTEXT_THRESHOLD: '1000' }
    });
    const context = payload.hookSpecificOutput.additionalContext;
    assert.match(context, /Context ~400k tokens/);
    assert.match(context, /1 tool calls reached/);
  });
});

test('contract: COMPACT_CONTEXT_THRESHOLD=0 silences the context signal', () => {
  withTranscript(400000, file => {
    assert.equal(
      spawnHook({
        stdin: JSON.stringify({ session_id: 'contract-test', transcript_path: file }),
        env: { COMPACT_CONTEXT_THRESHOLD: '0' }
      }),
      null
    );
  });
});

test('contract: a transcript below the threshold says nothing', () => {
  withTranscript(1000, file => {
    assert.equal(
      spawnHook({
        stdin: JSON.stringify({ session_id: 'contract-test', transcript_path: file }),
        env: { COMPACT_CONTEXT_THRESHOLD: '160000' }
      }),
      null
    );
  });
});
