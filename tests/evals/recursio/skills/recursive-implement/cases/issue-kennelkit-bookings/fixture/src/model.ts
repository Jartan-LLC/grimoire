/** @file The data model: dogs, bookings, the kennel and its JSON file, and date arithmetic. */

export type Size = 'small' | 'large';
export type Dog = { id: string; name: string; size: Size; vaccinatedUntil: string };
export type Booking = { id: string; dog: string; from: string; to: string };
export type Kennel = { runs: Record<Size, number>; dogs: Dog[]; bookings: Booking[] };

export class KennelError extends Error {}

export function parseKennel(text: string): Kennel {
  const data = JSON.parse(text) as Kennel;
  return { runs: { ...data.runs }, dogs: [...data.dogs], bookings: [...data.bookings] };
}

export function formatKennel(kennel: Kennel): string {
  return `${JSON.stringify(kennel, null, 2)}\n`;
}

const DAY_MS = 24 * 60 * 60 * 1000;

function toMs(date: string): number {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) throw new KennelError(`bad date ${date}`);
  const ms = Date.parse(`${date}T00:00:00Z`);
  if (Number.isNaN(ms) || new Date(ms).toISOString().slice(0, 10) !== date) throw new KennelError(`bad date ${date}`);
  return ms;
}

export function addDays(date: string, n: number): string {
  return new Date(toMs(date) + n * DAY_MS).toISOString().slice(0, 10);
}

export function weekday(date: string): number {
  return new Date(toMs(date)).getUTCDay();
}
