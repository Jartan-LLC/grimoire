// SPDX-License-Identifier: BSD-3-Clause
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { run } from '../src/cli.ts';
import { formatSize } from '../src/sizefmt.ts';

test('si sizes go up in powers of 1000', () => {
  assert.equal(formatSize(999, { si: true }), '999 B');
  assert.equal(formatSize(1500, { si: true }), '1.5 kB');
  assert.equal(formatSize(1_000_000, { si: true }), '1.0 MB');
  assert.equal(formatSize(2_500_000_000_000, { si: true, precision: 2 }), '2.50 TB');
});

test('--si on the command line, anywhere', () => {
  assert.deepEqual(run(['--si', '1500']), { status: 0, output: '1.5 kB\n', error: '' });
  assert.equal(run(['1500', '--si', '--precision', '0']).output, '2 kB\n');
});

test('without --si nothing changes', () => {
  assert.equal(run(['1536']).output, '1.5 KiB\n');
});
