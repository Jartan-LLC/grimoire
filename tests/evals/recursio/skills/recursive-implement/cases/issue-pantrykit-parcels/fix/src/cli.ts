/** The pantrykit command, kept free of process state so tests can run it. */
import { expiring } from './expiry.ts';
import { PantryError, formatPantry, parsePantry } from './model.ts';
import { pack } from './parcels.ts';
import { receive } from './stock.ts';

export type Files = { read(path: string): string; write(path: string, text: string): void };
export type Result = { status: number; output: string; error: string };

const USAGE = 'usage: pantrykit receive PANTRY SKU QTY DATE | pack PANTRY HOUSEHOLD TODAY [--dry-run] | expiring PANTRY TODAY DAYS';

export function run(argv: string[], files: Files): Result {
  const dryRun = argv.includes('--dry-run');
  const [command, path, ...rest] = argv.filter((a) => a !== '--dry-run');
  const arity: Record<string, number> = { receive: 3, pack: 2, expiring: 2 };
  if (!(command in arity) || path === undefined || rest.length !== arity[command] || (dryRun && command !== 'pack')) {
    return { status: 1, output: '', error: `pantrykit: ${USAGE}\n` };
  }
  try {
    let text: string;
    try {
      text = files.read(path);
    } catch {
      throw new PantryError(`cannot read ${path}`);
    }
    const pantry = parsePantry(text);
    let output: string;
    if (command === 'receive') {
      const [sku, qty, date] = rest;
      const lot = receive(pantry, sku, Number(qty), date);
      const item = pantry.items[sku];
      output = `received ${lot.id}: ${item.name} x${lot.qty}, ${item.kind} ${lot.date}\n`;
      files.write(path, formatPantry(pantry));
    } else if (command === 'pack') {
      const [household, today] = rest;
      const portions = pack(pantry, household, today);
      const name = pantry.households.find((h) => h.id === household)!.name;
      output = portions.map((p) => `${pantry.items[p.sku].name} x${p.qty} from ${p.id}\n`).join('') + `packed for ${name}\n`;
      if (!dryRun) files.write(path, formatPantry(pantry));
    } else {
      const days = Number(rest[1]);
      if (!Number.isInteger(days) || days < 0) throw new PantryError(`bad number of days ${rest[1]}`);
      const lots = expiring(pantry, rest[0], days);
      output = lots.length ? lots.map((l) => `${l.date} ${l.id} ${pantry.items[l.sku].name} x${l.qty}\n`).join('') : 'nothing expiring\n';
    }
    return { status: 0, output, error: '' };
  } catch (error) {
    if (error instanceof PantryError || error instanceof SyntaxError) return { status: 1, output: '', error: `pantrykit: ${error.message}\n` };
    throw error;
  }
}
