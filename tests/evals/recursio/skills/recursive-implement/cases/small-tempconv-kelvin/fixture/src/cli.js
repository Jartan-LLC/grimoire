// @ts-check
// The tempconv command, kept free of process state so tests can run it.
import { parseArgs } from 'node:util';
import { convert, formatTemp } from './tempconv.js';

function fail(message) {
  return { status: 2, output: '', error: `tempconv: ${message}\n` };
}

export function run(argv) {
  let parsed;
  try {
    parsed = parseArgs({
      args: argv,
      options: { from: { type: 'string' }, to: { type: 'string' } },
      allowPositionals: true,
    });
  } catch {
    return fail('bad option');
  }
  const { values, positionals } = parsed;
  if (values.from === undefined || values.to === undefined) return fail('--from and --to are required');
  if (positionals.length !== 1) return fail('give one value');
  const text = positionals[0];
  const value = Number(text);
  if (text.trim() === '' || !Number.isFinite(value)) return fail(`${text} is not a number`);
  let result;
  try {
    result = convert(value, values.from, values.to);
  } catch (error) {
    return fail(error.message);
  }
  return { status: 0, output: `${formatTemp(result)}\n`, error: '' };
}
