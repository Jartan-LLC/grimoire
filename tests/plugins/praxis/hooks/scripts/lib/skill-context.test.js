const assert = require('node:assert/strict');
const path = require('node:path');
const { describe, test } = require('node:test');

const { REPO_ROOT } = require('../../../../../helpers/fixture');

const { contextFor, fileTypeImperative, IMPERATIVE, SUBAGENT_IMPERATIVE } = require(
  path.join(REPO_ROOT, 'plugins/praxis/hooks/scripts/lib/skill-context.js'),
);

const output = (event, text) => ({ hookSpecificOutput: { hookEventName: event, additionalContext: text } });

describe('contextFor', () => {
  test('gives the main thread its imperative on every prompt', () => {
    assert.deepEqual(contextFor({ hook_event_name: 'UserPromptSubmit' }), output('UserPromptSubmit', IMPERATIVE));
  });

  test('gives a subagent its own imperative, labelled with its event', () => {
    const got = contextFor({ hook_event_name: 'SubagentStart', agent_type: 'general-purpose' });
    assert.deepEqual(got, output('SubagentStart', SUBAGENT_IMPERATIVE));
    assert.notEqual(SUBAGENT_IMPERATIVE, IMPERATIVE);
  });

  test('re-arms after a compact, and stays silent on any other session start', () => {
    assert.deepEqual(contextFor({ hook_event_name: 'SessionStart', source: 'compact' }), output('SessionStart', IMPERATIVE));
    for (const source of ['startup', 'resume', 'clear', undefined]) {
      assert.equal(contextFor({ hook_event_name: 'SessionStart', source }), null, `source ${source}`);
    }
  });

  test('says nothing for an event it does not serve or a payload with no event', () => {
    for (const input of [{ hook_event_name: 'PreToolUse' }, { hook_event_name: 'toString' }, { hook_event_name: 7 }, {}, null]) {
      assert.equal(contextFor(input), null, JSON.stringify(input));
    }
  });
});

describe('fileTypeImperative', () => {
  test('names the type and ends as the subagent imperative does', () => {
    const text = fileTypeImperative('.py');
    assert.match(text, /^This work now touches `\.py` files: /);
    const tail = 'load with Skill those not already in your context. If none apply, say so. When unsure, load.';
    assert.ok(text.endsWith(tail), text);
    assert.ok(SUBAGENT_IMPERATIVE.endsWith(tail), SUBAGENT_IMPERATIVE);
  });

  test('names no type when given none', () => {
    assert.match(fileTypeImperative(null), /^This work now touches a new type of file: name the skills that apply to it and load /);
  });
});
