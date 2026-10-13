const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { describe, test } = require('node:test');

const { REPO_ROOT, tempDir } = require('../../../../../helpers/fixture');

const {
  MAX_TOKEN_SETTING,
  readLatestContextTokens,
  resolveContextThreshold,
  resolveContextInterval,
} = require(path.join(REPO_ROOT, 'plugins/praxis/hooks/scripts/lib/transcript-context.js'));

const DEFAULT_THRESHOLD = 160000;
const DEFAULT_INTERVAL = 60000;

/** Write `records` as a JSONL transcript; strings are written as raw lines. */
function transcript(t, records) {
  const file = path.join(tempDir(t), 'session.jsonl');
  const lines = records.map(r => (typeof r === 'string' ? r : JSON.stringify(r)));
  fs.writeFileSync(file, `${lines.join('\n')}\n`);
  return file;
}

const assistant = usage => ({ type: 'assistant', message: { role: 'assistant', usage } });

describe('readLatestContextTokens', () => {
  test('sums the three prompt fields of the latest usage record, ignoring output', t => {
    const file = transcript(t, [
      assistant({ input_tokens: 1, cache_read_input_tokens: 1, cache_creation_input_tokens: 1 }),
      assistant({
        input_tokens: 100,
        cache_read_input_tokens: 20000,
        cache_creation_input_tokens: 3000,
        output_tokens: 999999,
      }),
    ]);
    assert.deepEqual(readLatestContextTokens(file), { tokens: 23100 });
  });

  test('skips later records with no usable usage, and malformed lines', t => {
    const file = transcript(t, [
      assistant({ input_tokens: 5000 }),
      { type: 'user', message: { role: 'user', content: 'hi' } },
      assistant({ input_tokens: 0, output_tokens: 10 }),
      assistant({ input_tokens: 'many', cache_read_input_tokens: null }),
      '{"type": "assistant", "message": {"usage": {"input_tokens": 77',
      '',
    ]);
    assert.deepEqual(readLatestContextTokens(file), { tokens: 5000 });
  });

  test('takes the largest single iteration, not the cross-iteration sum', t => {
    const file = transcript(t, [
      assistant({
        input_tokens: 30,
        cache_read_input_tokens: 180000,
        cache_creation_input_tokens: 2000,
        iterations: [
          { input_tokens: 10, cache_read_input_tokens: 90000, cache_creation_input_tokens: 2000 },
          { input_tokens: 20, cache_read_input_tokens: 90000 },
          null,
        ],
      }),
    ]);
    assert.deepEqual(readLatestContextTokens(file), { tokens: 92010 });
  });

  test('falls back to the top-level fields when no iteration carries tokens', t => {
    const file = transcript(t, [assistant({ input_tokens: 4200, iterations: [{}, { output_tokens: 3 }] })]);
    assert.deepEqual(readLatestContextTokens(file), { tokens: 4200 });
  });

  test('drops the partial first line of a truncated tail, even when its rest parses', t => {
    // Whole, this line is not JSON; cut after its first byte, it is a usage record.
    const corrupt = `x${JSON.stringify(assistant({ input_tokens: 5 }))}`;
    const file = transcript(t, [assistant({ input_tokens: 999 }), corrupt]);
    const tailBytes = Buffer.byteLength(`${corrupt}\n`) - 1;
    assert.equal(readLatestContextTokens(file, { tailBytes }), null);
    assert.deepEqual(readLatestContextTokens(file), { tokens: 999 });
  });

  test('returns null for a missing file, an empty path or a transcript with no usage', t => {
    assert.equal(readLatestContextTokens(path.join(tempDir(t), 'absent.jsonl')), null);
    assert.equal(readLatestContextTokens(''), null);
    assert.equal(readLatestContextTokens(undefined), null);
    assert.equal(readLatestContextTokens(transcript(t, [{ type: 'user' }])), null);
  });
});

describe('resolveContextThreshold', () => {
  test('reads a positive integer within range', () => {
    assert.equal(resolveContextThreshold({ COMPACT_CONTEXT_THRESHOLD: '200000' }), 200000);
    assert.equal(resolveContextThreshold({ COMPACT_CONTEXT_THRESHOLD: String(MAX_TOKEN_SETTING) }), MAX_TOKEN_SETTING);
  });

  test('takes 0 as the off switch', () => {
    assert.equal(resolveContextThreshold({ COMPACT_CONTEXT_THRESHOLD: '0' }), 0);
  });

  test('falls back to the default for absent, invalid and out-of-range values', () => {
    for (const raw of [undefined, '', 'abc', '-5', String(MAX_TOKEN_SETTING + 1)]) {
      assert.equal(resolveContextThreshold({ COMPACT_CONTEXT_THRESHOLD: raw }), DEFAULT_THRESHOLD, String(raw));
    }
    assert.equal(resolveContextThreshold(undefined), DEFAULT_THRESHOLD);
  });
});

describe('resolveContextInterval', () => {
  test('reads a positive integer within range', () => {
    assert.equal(resolveContextInterval({ COMPACT_CONTEXT_INTERVAL: '5000' }), 5000);
  });

  test('falls back to the default for 0, absent, invalid and out-of-range values', () => {
    for (const raw of ['0', undefined, '', 'abc', '-1', String(MAX_TOKEN_SETTING + 1)]) {
      assert.equal(resolveContextInterval({ COMPACT_CONTEXT_INTERVAL: raw }), DEFAULT_INTERVAL, String(raw));
    }
    assert.equal(resolveContextInterval(undefined), DEFAULT_INTERVAL);
  });
});
