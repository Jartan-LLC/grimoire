// Process contract for the skill-activation hook.
//
// The whole script is a gate on the incoming event, so there is nothing to
// import: the contract IS the behaviour. A hook that throws breaks the user's
// turn, and no other check in this repository can see that.

const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const SCRIPT = path.resolve(__dirname, '../../../../../plugins/praxis/hooks/scripts/suggest-skills.js');

/**
 * Spawn the hook and assert exit 0 plus either no stdout or exactly one
 * well-formed JSON object. JSON.parse is the "exactly one" half -- two
 * concatenated objects do not parse.
 */
function spawnHook(stdin) {
  const r = spawnSync(process.execPath, [SCRIPT], { input: stdin, encoding: 'utf8' });

  assert.equal(r.status, 0, `exited ${r.status}, signal ${r.signal}; stderr: ${r.stderr}`);
  const out = r.stdout.trim();
  if (out === '') return null;

  const payload = JSON.parse(out);
  assert.equal(typeof payload, 'object');
  assert.notEqual(payload, null);
  return payload;
}

test('contract: malformed JSON on stdin', () => {
  assert.equal(spawnHook('{"hook_event_name": '), null);
});

test('contract: empty stdin', () => {
  assert.equal(spawnHook(''), null);
});

test('contract: a payload with no event name', () => {
  // An unread or unparsed payload leaves the event unknown, and guessing would
  // label the output with an event that did not happen.
  assert.equal(spawnHook(JSON.stringify({ transcript_path: '/nowhere' })), null);
  assert.equal(spawnHook(JSON.stringify({ hook_event_name: '' })), null);
});

test('contract: a prompt submission emits exactly one JSON object', () => {
  const payload = spawnHook(JSON.stringify({ hook_event_name: 'UserPromptSubmit' }));
  assert.equal(payload.hookSpecificOutput.hookEventName, 'UserPromptSubmit');
  assert.match(payload.hookSpecificOutput.additionalContext, /load them with Skill/);
});

test('contract: a session start says nothing unless a compact caused it', () => {
  assert.equal(spawnHook(JSON.stringify({ hook_event_name: 'SessionStart', source: 'startup' })), null);
  assert.equal(spawnHook(JSON.stringify({ hook_event_name: 'SessionStart' })), null);

  const payload = spawnHook(JSON.stringify({ hook_event_name: 'SessionStart', source: 'compact' }));
  assert.equal(payload.hookSpecificOutput.hookEventName, 'SessionStart');
});
