// SPDX-License-Identifier: ISC
// How full the car park was.
import { toMinutes } from './model.js';

export function occupancy(tickets, time) {
  const at = toMinutes(time);
  return tickets.filter((t) => toMinutes(t.entry) <= at && (t.exit === null || at < toMinutes(t.exit))).length;
}

export function peak(tickets) {
  let best = { time: null, cars: 0 };
  const entries = [...new Set(tickets.map((t) => t.entry))].sort((a, b) => toMinutes(a) - toMinutes(b));
  for (const time of entries) {
    const cars = occupancy(tickets, time);
    if (cars > best.cars) best = { time, cars };
  }
  return best;
}
