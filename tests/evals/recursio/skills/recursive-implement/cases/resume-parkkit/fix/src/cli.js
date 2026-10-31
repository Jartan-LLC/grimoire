// SPDX-License-Identifier: ISC
// The parkkit command, kept free of process state so tests can run it.
import { fee, total } from './fees.js';
import { ParkError, formatCents } from './model.js';
import { occupancy, peak } from './occupancy.js';
import { parseRates } from './rates.js';
import { parseTickets } from './tickets.js';

const USAGE = 'usage: parkkit fees TICKETS RATES | parkkit peak TICKETS | parkkit at TICKETS TIME';

function fail(message) {
  return { status: 2, output: '', error: `parkkit: ${message}\n` };
}

function read(readText, path) {
  try {
    return readText(path);
  } catch {
    throw new ParkError(`cannot read ${path}`);
  }
}

export function run(argv, readText) {
  const [command, ticketsPath, extra, ...rest] = argv;
  const arity = { fees: 1, peak: 0, at: 1 }[command];
  if (arity === undefined || ticketsPath === undefined || rest.length || (arity === 1) !== (extra !== undefined)) return fail(USAGE);
  try {
    const tickets = parseTickets(read(readText, ticketsPath));
    let output;
    if (command === 'fees') {
      const rates = parseRates(read(readText, extra));
      const closed = tickets.filter((t) => t.exit !== null);
      output = closed.map((t) => `${t.plate} ${formatCents(fee(t, rates))}\n`).join('') + `total ${formatCents(total(tickets, rates))}\n`;
    } else if (command === 'peak') {
      const busiest = peak(tickets);
      output = `peak ${busiest.time} ${busiest.cars} cars\n`;
    } else {
      output = `${occupancy(tickets, extra)} cars\n`;
    }
    return { status: 0, output, error: '' };
  } catch (error) {
    if (error instanceof ParkError) return fail(error.message);
    throw error;
  }
}
