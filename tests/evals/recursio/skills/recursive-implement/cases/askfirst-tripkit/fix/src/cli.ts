// Copyright 2026 tripkit contributors. MIT licence.
// The tripkit command, kept free of process state so tests can run it.
import { parseRates } from './currency.ts';
import { TripError } from './errors.ts';
import { parseExpenses } from './expenses.ts';
import { balances, settle } from './settle.ts';

export type Result = { status: number; output: string; error: string };

const USAGE = 'usage: tripkit balances|settle EXPENSES --home CUR --rates FILE';

function fail(message: string): Result {
  return { status: 2, output: '', error: `tripkit: ${message}\n` };
}

function money(cents: number): string {
  return (cents / 100).toFixed(2);
}

export async function run(argv: string[], readText: (path: string) => string): Promise<Result> {
  const [command, path, ...options] = argv;
  const flags = new Map<string, string>();
  for (let i = 0; i < options.length; i += 2) flags.set(options[i], options[i + 1]);
  if (!['balances', 'settle'].includes(command) || !path || !flags.get('--home') || [...flags.keys()].some((k) => !['--home', '--rates'].includes(k))) return fail(USAGE);
  // Rates are read from --rates only: fetching them needs network access, which waits on the maintainer.
  if (!flags.get('--rates')) return fail('--rates FILE is needed: tripkit does not fetch rates yet');
  try {
    let texts: [string, string];
    try {
      texts = [readText(path), readText(flags.get('--rates')!)];
    } catch (error) {
      throw new TripError(`cannot read: ${error instanceof Error ? error.message : String(error)}`);
    }
    const owed = balances(parseExpenses(texts[0]), flags.get('--home')!, parseRates(texts[1]));
    const lines = command === 'balances'
      ? [...owed].map(([name, cents]) => `${name} ${cents >= 0 ? '+' : '-'}${money(Math.abs(cents))}\n`)
      : settle(owed).map((t) => `${t.from} pays ${t.to} ${money(t.cents)}\n`);
    return { status: 0, output: lines.join(''), error: '' };
  } catch (error) {
    if (error instanceof TripError || error instanceof SyntaxError) return fail(error.message);
    throw error;
  }
}
