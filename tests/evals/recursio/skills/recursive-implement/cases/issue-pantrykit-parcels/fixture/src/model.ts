/** The data model: items, lots, households, the pantry's JSON file and date arithmetic. */

export type Kind = 'use-by' | 'best-before';
export type Item = { name: string; kind: Kind };
export type Lot = { id: string; sku: string; qty: number; date: string };
export type Household = { id: string; name: string; size: number };
export type Pantry = { items: Record<string, Item>; lots: Lot[]; households: Household[] };

export class PantryError extends Error {}

export function parsePantry(text: string): Pantry {
  const data = JSON.parse(text) as Pantry;
  return {
    items: { ...data.items },
    lots: data.lots.map((lot) => ({ ...lot })),
    households: data.households.map((household) => ({ ...household })),
  };
}

export function formatPantry(pantry: Pantry): string {
  return `${JSON.stringify(pantry, null, 2)}\n`;
}

const DAY_MS = 24 * 60 * 60 * 1000;

export function checkDate(date: string): string {
  const ms = /^\d{4}-\d{2}-\d{2}$/.test(date) ? Date.parse(`${date}T00:00:00Z`) : Number.NaN;
  if (Number.isNaN(ms) || new Date(ms).toISOString().slice(0, 10) !== date) throw new PantryError(`bad date ${date}`);
  return date;
}

export function addDays(date: string, n: number): string {
  return new Date(Date.parse(`${checkDate(date)}T00:00:00Z`) + n * DAY_MS).toISOString().slice(0, 10);
}
