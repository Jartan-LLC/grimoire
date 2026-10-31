/** What is about to expire. */
import { type Lot, type Pantry, addDays, checkDate } from './model.ts';

export function expiring(pantry: Pantry, today: string, days: number): Lot[] {
  const last = addDays(checkDate(today), days);
  return pantry.lots
    .map((lot, i) => ({ lot, i }))
    .filter(({ lot }) => lot.date >= today && lot.date <= last)
    .sort((a, b) => (a.lot.date < b.lot.date ? -1 : a.lot.date > b.lot.date ? 1 : a.i - b.i))
    .map(({ lot }) => ({ ...lot }));
}

export function summary(pantry: Pantry, today: string, days: number): { sku: string; name: string; qty: number; date: string }[] {
  const bySku = new Map<string, { sku: string; name: string; qty: number; date: string }>();
  for (const lot of expiring(pantry, today, days)) {
    const entry = bySku.get(lot.sku) ?? { sku: lot.sku, name: pantry.items[lot.sku].name, qty: 0, date: lot.date };
    entry.qty += lot.qty;
    bySku.set(lot.sku, entry);
  }
  return [...bySku.values()].sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : a.sku < b.sku ? -1 : 1));
}
