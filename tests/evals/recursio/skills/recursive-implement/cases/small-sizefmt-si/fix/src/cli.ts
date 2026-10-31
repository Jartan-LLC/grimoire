// SPDX-License-Identifier: BSD-3-Clause
// The sizefmt command, kept free of process state so tests can run it.
import { formatSize } from './sizefmt.ts';

export type Result = { status: number; output: string; error: string };

const USAGE = 'usage: sizefmt [--precision N] [--si] SIZE...';

function usage(message: string): Result {
  return { status: 2, output: '', error: `sizefmt: ${message}\n${USAGE}\n` };
}

export function run(argv: string[]): Result {
  let precision = 1;
  let si = false;
  const sizes: number[] = [];
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === '--precision') {
      precision = Number(argv[i + 1]);
      if (!Number.isInteger(precision) || precision < 0 || precision > 6) return usage('--precision needs a whole number from 0 to 6');
      i += 1;
    } else if (argv[i] === '--si') {
      si = true;
    } else if (/^\d+$/.test(argv[i])) {
      sizes.push(Number(argv[i]));
    } else {
      return usage(`not a size: ${argv[i]}`);
    }
  }
  if (sizes.length === 0) return usage('give at least one size');
  return { status: 0, output: sizes.map((size) => `${formatSize(size, { precision, si })}\n`).join(''), error: '' };
}
