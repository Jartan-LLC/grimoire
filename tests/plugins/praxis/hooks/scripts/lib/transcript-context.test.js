// Tests for the strategic-compact hook's token accounting and setting resolvers.
//
// The silent-wrong failure modes here are a context size reported at twice its
// real value, and a threshold that reads as disabled when it is not.

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const {
  MAX_TOKEN_SETTING,
  readFileTail,
  extractUsageTokens,
  readLatestContextTokens,
  resolveContextThreshold,
  resolveContextInterval
} = require('../../../../../../plugins/praxis/hooks/scripts/lib/transcript-context');

const DEFAULT_THRESHOLD = 160000;
const DEFAULT_INTERVAL = 60000;

/** Write `contents` into a throwaway directory and hand back the path. */
function tempFile(contents, name = 'transcript.jsonl') {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'grimoire-transcript-'));
  const file = path.join(dir, name);
  fs.writeFileSync(file, contents);
  return { dir, file };
}

function withTempFile(contents, fn) {
  const { dir, file } = tempFile(contents);
  try {
    return fn(file);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

const usageRecord = usage => JSON.stringify({ message: { usage } });

test('extractUsageTokens sums the fields that partition the prompt', () => {
  const tokens = extractUsageTokens({
    message: { usage: { input_tokens: 1000, cache_read_input_tokens: 20000, cache_creation_input_tokens: 300 } }
  });
  assert.equal(tokens, 21300);
});

test('extractUsageTokens treats an absent or non-numeric field as zero', () => {
  assert.equal(extractUsageTokens({ message: { usage: { input_tokens: 500 } } }), 500);
  assert.equal(
    extractUsageTokens({ message: { usage: { input_tokens: 500, cache_read_input_tokens: 'lots' } } }),
    500
  );
});

test('extractUsageTokens returns zero when there is no usable usage block', () => {
  assert.equal(extractUsageTokens(null), 0);
  assert.equal(extractUsageTokens({}), 0);
  assert.equal(extractUsageTokens({ message: {} }), 0);
  assert.equal(extractUsageTokens({ message: { usage: null } }), 0);
  assert.equal(extractUsageTokens({ message: { usage: 'nope' } }), 0);
  assert.equal(extractUsageTokens({ message: { usage: {} } }), 0);
});

test('extractUsageTokens takes the largest iteration, not the aggregate', () => {
  // On a multi-iteration turn the top-level fields aggregate ACROSS iterations,
  // so summing them reports a context that was never that large -- 2.00x here.
  // Each iteration re-sends the prompt, so the largest single one is the truth.
  const tokens = extractUsageTokens({
    message: {
      usage: {
        input_tokens: 200000,
        iterations: [{ input_tokens: 100000 }, { input_tokens: 100000 }]
      }
    }
  });
  assert.equal(tokens, 100000);
});

test('extractUsageTokens sums each iteration across its own prompt fields', () => {
  const tokens = extractUsageTokens({
    message: {
      usage: {
        input_tokens: 999999,
        iterations: [
          { input_tokens: 10, cache_read_input_tokens: 20 },
          { input_tokens: 100, cache_read_input_tokens: 200, cache_creation_input_tokens: 5 }
        ]
      }
    }
  });
  assert.equal(tokens, 305);
});

test('extractUsageTokens falls back to the top level when no iteration is usable', () => {
  const usage = { input_tokens: 4200, iterations: [null, {}, 'junk'] };
  assert.equal(extractUsageTokens({ message: { usage } }), 4200);
  assert.equal(extractUsageTokens({ message: { usage: { input_tokens: 4200, iterations: [] } } }), 4200);
  assert.equal(extractUsageTokens({ message: { usage: { input_tokens: 4200, iterations: 'no' } } }), 4200);
});

test('readFileTail returns null for a file it cannot open', () => {
  assert.equal(readFileTail(path.join(os.tmpdir(), 'grimoire-does-not-exist-98217'), 1024), null);
});

test('readFileTail reads a whole file that fits, and reports it untruncated', () => {
  withTempFile('one\ntwo\n', file => {
    assert.deepEqual(readFileTail(file, 1024), { text: 'one\ntwo\n', truncated: false });
  });
});

test('readFileTail reads only the tail of a larger file, and says so', () => {
  withTempFile('0123456789', file => {
    assert.deepEqual(readFileTail(file, 4), { text: '6789', truncated: true });
  });
});

test('readFileTail reports an empty file as empty and untruncated', () => {
  withTempFile('', file => {
    assert.deepEqual(readFileTail(file, 1024), { text: '', truncated: false });
  });
});

test('readLatestContextTokens rejects a path that is not a usable string', () => {
  assert.equal(readLatestContextTokens(''), null);
  assert.equal(readLatestContextTokens(undefined), null);
  assert.equal(readLatestContextTokens(42), null);
});

test('readLatestContextTokens returns null for a missing transcript', () => {
  assert.equal(readLatestContextTokens(path.join(os.tmpdir(), 'grimoire-no-transcript-31337.jsonl')), null);
});

test('readLatestContextTokens takes the most recent usable record', () => {
  const lines = [
    usageRecord({ input_tokens: 111 }),
    usageRecord({ input_tokens: 222 }),
    usageRecord({ input_tokens: 333 })
  ];
  withTempFile(lines.join('\n') + '\n', file => {
    assert.deepEqual(readLatestContextTokens(file), { tokens: 333 });
  });
});

test('readLatestContextTokens scans past blank, unparsable and usage-free records', () => {
  const lines = [
    usageRecord({ input_tokens: 777 }),
    '{"message":{"usage":{}}}',
    'not json at all',
    '{"type":"user","message":{"content":"hi"}}',
    ''
  ];
  withTempFile(lines.join('\n') + '\n', file => {
    assert.deepEqual(readLatestContextTokens(file), { tokens: 777 });
  });
});

test('readLatestContextTokens returns null when no record carries usage', () => {
  withTempFile('{"type":"user"}\nnot json\n\n', file => {
    assert.equal(readLatestContextTokens(file), null);
  });
});

test('readLatestContextTokens distrusts the first line of a truncated tail', () => {
  // The first line of a tail read is almost certainly partial JSON. The guard is
  // unconditional, so a complete record sitting exactly on the cut is dropped
  // too -- deliberately, since the read cannot tell the two apart.
  const record = usageRecord({ input_tokens: 999999 });
  const contents = `noise\n${record}\nnot json\n`;
  withTempFile(contents, file => {
    const size = Buffer.byteLength(contents);
    // Cut exactly after "noise\n", so the record is the tail's first line.
    assert.equal(readLatestContextTokens(file, { tailBytes: size - 'noise\n'.length }), null);
    // Read whole, the same record is trusted and found.
    assert.deepEqual(readLatestContextTokens(file, { tailBytes: size }), { tokens: 999999 });
  });
});

test('readLatestContextTokens falls back to the default tail for an unusable tailBytes', () => {
  withTempFile(usageRecord({ input_tokens: 42 }) + '\n', file => {
    for (const tailBytes of [0, -1, 1.5, 'big', null]) {
      assert.deepEqual(readLatestContextTokens(file, { tailBytes }), { tokens: 42 }, `tailBytes=${tailBytes}`);
    }
  });
});

test('resolveContextThreshold defaults when the setting is absent', () => {
  assert.equal(resolveContextThreshold({}), DEFAULT_THRESHOLD);
  assert.equal(resolveContextThreshold({ COMPACT_CONTEXT_THRESHOLD: '' }), DEFAULT_THRESHOLD);
  assert.equal(resolveContextThreshold({ COMPACT_CONTEXT_THRESHOLD: null }), DEFAULT_THRESHOLD);
  assert.equal(resolveContextThreshold(undefined), DEFAULT_THRESHOLD);
});

test('resolveContextThreshold treats zero as a disable switch', () => {
  assert.equal(resolveContextThreshold({ COMPACT_CONTEXT_THRESHOLD: '0' }), 0);
});

test('resolveContextThreshold accepts an in-range value up to the maximum', () => {
  assert.equal(resolveContextThreshold({ COMPACT_CONTEXT_THRESHOLD: '90000' }), 90000);
  assert.equal(resolveContextThreshold({ COMPACT_CONTEXT_THRESHOLD: String(MAX_TOKEN_SETTING) }), MAX_TOKEN_SETTING);
});

test('resolveContextThreshold falls back for anything invalid or out of range', () => {
  for (const raw of ['-1', 'lots', String(MAX_TOKEN_SETTING + 1)]) {
    assert.equal(resolveContextThreshold({ COMPACT_CONTEXT_THRESHOLD: raw }), DEFAULT_THRESHOLD, raw);
  }
});

test('resolveContextInterval defaults when the setting is absent or invalid', () => {
  assert.equal(resolveContextInterval({}), DEFAULT_INTERVAL);
  assert.equal(resolveContextInterval(undefined), DEFAULT_INTERVAL);
  assert.equal(resolveContextInterval({ COMPACT_CONTEXT_INTERVAL: 'often' }), DEFAULT_INTERVAL);
  assert.equal(resolveContextInterval({ COMPACT_CONTEXT_INTERVAL: '-5' }), DEFAULT_INTERVAL);
  assert.equal(resolveContextInterval({ COMPACT_CONTEXT_INTERVAL: String(MAX_TOKEN_SETTING + 1) }), DEFAULT_INTERVAL);
});

test('resolveContextInterval has no disable switch, unlike the threshold', () => {
  // The interval only spaces out repeats; zero is not an off state for it.
  assert.equal(resolveContextInterval({ COMPACT_CONTEXT_INTERVAL: '0' }), DEFAULT_INTERVAL);
});

test('resolveContextInterval accepts an in-range value up to the maximum', () => {
  assert.equal(resolveContextInterval({ COMPACT_CONTEXT_INTERVAL: '25000' }), 25000);
  assert.equal(resolveContextInterval({ COMPACT_CONTEXT_INTERVAL: String(MAX_TOKEN_SETTING) }), MAX_TOKEN_SETTING);
});
