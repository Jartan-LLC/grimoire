/** @file The kennelkit command, kept free of process state so tests can run it. */
import { book, cancel } from './bookings.ts';
import { KennelError, formatKennel, parseKennel } from './model.ts';
import { occupancy } from './occupancy.ts';
import { price } from './pricing.ts';

export type Files = { read(path: string): string; write(path: string, text: string): void };
export type Result = { status: number; output: string; error: string };

const USAGE = 'usage: kennelkit book KENNEL DOG FROM TO | cancel KENNEL ID | occupancy KENNEL FROM TO [--json]';

export function run(argv: string[], files: Files): Result {
  const json = argv.includes('--json');
  const [command, path, ...rest] = argv.filter((a) => a !== '--json');
  const arity: Record<string, number> = { book: 3, cancel: 1, occupancy: 2 };
  if (!(command in arity) || path === undefined || rest.length !== arity[command] || (json && command !== 'occupancy')) {
    return { status: 1, output: '', error: `kennelkit: ${USAGE}\n` };
  }
  try {
    let text: string;
    try {
      text = files.read(path);
    } catch {
      throw new KennelError(`cannot read ${path}`);
    }
    const kennel = parseKennel(text);
    let output: string;
    if (command === 'book') {
      const [dog, from, to] = rest;
      const booking = book(kennel, dog, from, to);
      const found = kennel.dogs.find((d) => d.id === dog)!;
      output = `booked ${booking.id}: ${found.name} ${from} to ${to}, ${(price(booking, found) / 100).toFixed(2)}\n`;
      files.write(path, formatKennel(kennel));
    } else if (command === 'cancel') {
      output = `cancelled ${cancel(kennel, rest[0]).id}\n`;
      files.write(path, formatKennel(kennel));
    } else {
      const nights = occupancy(kennel, rest[0], rest[1]);
      output = json
        ? `${JSON.stringify(nights)}\n`
        : nights.map((n) => `${n.date} small ${n.small}/${kennel.runs.small} large ${n.large}/${kennel.runs.large}\n`).join('');
    }
    return { status: 0, output, error: '' };
  } catch (error) {
    if (error instanceof KennelError || error instanceof SyntaxError) return { status: 1, output: '', error: `kennelkit: ${error.message}\n` };
    throw error;
  }
}
