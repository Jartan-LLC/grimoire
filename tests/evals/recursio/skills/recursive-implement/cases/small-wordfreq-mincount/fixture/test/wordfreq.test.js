// SPDX-License-Identifier: MIT
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { run } from '../src/cli.js';
import { countWords, top } from '../src/wordfreq.js';

test('words are counted in lower case', () => {
  assert.deepEqual([...countWords("It's it IT").entries()], [["it's", 1], ['it', 2]]);
});

test('most frequent first, ties alphabetical', () => {
  assert.deepEqual(top(countWords('b a b c a b')), [['b', 3], ['a', 2], ['c', 1]]);
});

test('--top keeps the first N', () => {
  assert.equal(run(['f.txt', '--top', '1'], () => 'b a b').output, '2 b\n');
});

test('a bad --top is a usage error', () => {
  assert.equal(run(['f.txt', '--top', '0'], () => 'b').status, 2);
});

test('an unreadable file exits 2', () => {
  const result = run(['missing.txt'], () => {
    throw new Error('ENOENT');
  });
  assert.equal(result.status, 2);
});
