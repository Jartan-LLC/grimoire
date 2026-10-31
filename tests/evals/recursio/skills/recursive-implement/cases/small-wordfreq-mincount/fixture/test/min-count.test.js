// SPDX-License-Identifier: MIT
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { run } from '../src/cli.js';

const read = () => 'the cat and the hat and the bat';

test('--min-count leaves out words seen fewer times', () => {
  assert.deepEqual(run(['f.txt', '--min-count', '2'], read), { status: 0, output: '3 the\n2 and\n', error: '' });
});

test('--min-count works with --top', () => {
  assert.equal(run(['f.txt', '--min-count', '2', '--top', '1'], read).output, '3 the\n');
});

test('--min-count defaults to 1', () => {
  assert.equal(run(['f.txt'], read).output, '3 the\n2 and\n1 bat\n1 cat\n1 hat\n');
});

test('--min-count must be a positive whole number', () => {
  for (const bad of ['0', 'x', '1.5', '-2']) {
    assert.equal(run(['f.txt', '--min-count', bad], read).status, 2, bad);
  }
});
