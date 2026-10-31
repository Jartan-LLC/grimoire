// SPDX-License-Identifier: ISC
// What a stay costs.
import { ParkError, toMinutes } from './model.js';

const DAY = 24 * 60;

function charge(minutes, rates) {
  if (minutes <= 0) return 0;
  const hours = Math.ceil(minutes / 60);
  return Math.min(rates.dailyCap, rates.firstHour + (hours - 1) * rates.perHour);
}

export function fee(ticket, rates) {
  if (ticket.exit === null || ticket.exit === undefined) throw new ParkError(`${ticket.plate} is still parked`);
  const minutes = toMinutes(ticket.exit) - toMinutes(ticket.entry);
  if (minutes <= rates.graceMinutes) return 0;
  // Each 24 hours from entry is a day for the cap.
  let cents = 0;
  for (let start = 0; start < minutes; start += DAY) {
    const span = Math.min(DAY, minutes - start);
    cents += start === 0 ? charge(span, rates) : Math.min(rates.dailyCap, Math.ceil(span / 60) * rates.perHour);
  }
  return cents;
}

export function total(tickets, rates) {
  return tickets.filter((ticket) => ticket.exit !== null).reduce((sum, ticket) => sum + fee(ticket, rates), 0);
}
