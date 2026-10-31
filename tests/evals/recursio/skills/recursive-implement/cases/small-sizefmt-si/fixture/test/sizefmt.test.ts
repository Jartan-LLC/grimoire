// SPDX-License-Identifier: BSD-3-Clause
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { run } from '../src/cli.ts';
import { formatSize } from '../src/sizefmt.ts';

test('powers of 1024', () => {
  assert.equal(formatSize(512), '512 B');
  assert.equal(formatSize(1536), '1.5 KiB');
  assert.equal(formatSize(3 * 1024 ** 3), '3.0 GiB');
  assert.equal(formatSize(5 * 1024 ** 5), '5120.0 TiB');
});

test('precision', () => {
  assert.equal(formatSize(1536, { precision: 3 }), '1.500 KiB');
});

test('several sizes, one line each', () => {
  assert.deepEqual(run(['512', '1536', '--precision', '0']), { status: 0, output: '512 B\n2 KiB\n', error: '' });
});

test('bad input exits 2', () => {
  assert.equal(run(['1.5']).status, 2);
  assert.equal(run(['--precision', 'x', '1']).status, 2);
  assert.equal(run([]).status, 2);
});
