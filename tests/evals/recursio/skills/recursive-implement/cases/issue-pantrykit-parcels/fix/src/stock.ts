/** Receiving and taking stock. */
import { type Lot, type Pantry, PantryError, checkDate } from './model.ts';

export function receive(pantry: Pantry, sku: string, qty: number, date: string): Lot {
  if (!(sku in pantry.items)) throw new PantryError(`unknown SKU ${sku}`);
  if (!Number.isInteger(qty) || qty <= 0) throw new PantryError(`bad quantity ${qty}`);
  checkDate(date);
  const top = Math.max(0, ...pantry.lots.map((lot) => Number(lot.id.slice(1)) || 0));
  const lot = { id: `l${top + 1}`, sku, qty, date };
  pantry.lots.push(lot);
  return { ...lot };
}

function usable(pantry: Pantry, sku: string, today: string): Lot[] {
  return pantry.lots
    .filter((lot) => lot.sku === sku && (lot.date >= today || pantry.items[sku].kind === 'best-before'))
    .map((lot, i) => ({ lot, i }))
    .sort((a, b) => (a.lot.date < b.lot.date ? -1 : a.lot.date > b.lot.date ? 1 : a.i - b.i))
    .map(({ lot }) => lot);
}

export function onHand(pantry: Pantry, sku: string, today: string): number {
  return usable(pantry, sku, checkDate(today)).reduce((sum, lot) => sum + lot.qty, 0);
}

export function take(pantry: Pantry, sku: string, qty: number, today: string): Lot[] {
  if (onHand(pantry, sku, today) < qty) throw new PantryError(`not enough ${sku}`);
  const taken: Lot[] = [];
  let left = qty;
  for (const lot of usable(pantry, sku, today)) {
    if (left === 0) break;
    const n = Math.min(left, lot.qty);
    lot.qty -= n;
    left -= n;
    taken.push({ id: lot.id, sku, qty: n, date: lot.date });
  }
  pantry.lots = pantry.lots.filter((lot) => lot.qty > 0);
  return taken;
}
