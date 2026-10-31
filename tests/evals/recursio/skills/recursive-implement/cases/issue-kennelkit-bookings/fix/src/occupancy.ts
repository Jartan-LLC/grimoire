/** @file How full the runs are. */
import { type Kennel, addDays } from './model.ts';

export type Night = { date: string; small: number; large: number };

export function occupancy(kennel: Kennel, from: string, to: string): Night[] {
  const sizeOf = new Map(kennel.dogs.map((d) => [d.id, d.size]));
  const nights: Night[] = [];
  for (let date = from; date < to; date = addDays(date, 1)) {
    const night = { date, small: 0, large: 0 };
    for (const b of kennel.bookings) {
      const size = sizeOf.get(b.dog);
      if (size && b.from <= date && date < b.to) night[size] += 1;
    }
    nights.push(night);
  }
  return nights;
}

export function busiest(kennel: Kennel, from: string, to: string): Night | null {
  let best: Night | null = null;
  for (const night of occupancy(kennel, from, to)) {
    const taken = night.small + night.large;
    if (taken > 0 && (best === null || taken > best.small + best.large)) best = night;
  }
  return best;
}
