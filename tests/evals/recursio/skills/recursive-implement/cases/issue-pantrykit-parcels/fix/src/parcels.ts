/** The weekly parcel: what a household gets, and packing it from stock. */
import { type Lot, type Pantry, PantryError } from './model.ts';
import { onHand, take } from './stock.ts';

export const TEMPLATE: Record<string, number> = { rice: 1, beans: 2, oats: 1, milk: 2 };

export function parcelFor(size: number, template: Record<string, number> = TEMPLATE): Record<string, number> {
  const people = Math.min(size, 6);
  return Object.fromEntries(Object.entries(template).map(([sku, units]) => [sku, units * people]));
}

export function pack(pantry: Pantry, household: string, today: string, template: Record<string, number> = TEMPLATE): Lot[] {
  const found = pantry.households.find((h) => h.id === household);
  if (!found) throw new PantryError(`unknown household ${household}`);
  const parcel = parcelFor(found.size, template);
  for (const [sku, qty] of Object.entries(parcel)) {
    if (onHand(pantry, sku, today) < qty) throw new PantryError(`not enough ${sku}`);
  }
  return Object.entries(parcel).flatMap(([sku, qty]) => take(pantry, sku, qty, today));
}
