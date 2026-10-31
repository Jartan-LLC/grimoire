/** @file Make and cancel bookings. */
import { type Booking, type Kennel, KennelError, addDays } from './model.ts';

function nightsOf(from: string, to: string): string[] {
  const nights: string[] = [];
  for (let night = from; night < to; night = addDays(night, 1)) nights.push(night);
  return nights;
}

export function book(kennel: Kennel, dog: string, from: string, to: string): Booking {
  const found = kennel.dogs.find((d) => d.id === dog);
  if (!found) throw new KennelError(`unknown dog ${dog}`);
  addDays(from, 0);
  addDays(to, 0);
  if (to <= from) throw new KennelError(`${to} is not after ${from}`);
  const sizeOf = new Map(kennel.dogs.map((d) => [d.id, d.size]));
  for (const night of nightsOf(from, to)) {
    const tonight = kennel.bookings.filter((b) => b.from <= night && night < b.to);
    if (tonight.some((b) => b.dog === dog)) throw new KennelError(`${found.name} is already booked on ${night}`);
    if (tonight.filter((b) => sizeOf.get(b.dog) === found.size).length >= kennel.runs[found.size]) {
      throw new KennelError(`no ${found.size} run free on ${night}`);
    }
  }
  const highest = Math.max(0, ...kennel.bookings.map((b) => Number(b.id.slice(1)) || 0));
  const booking = { id: `b${highest + 1}`, dog, from, to };
  kennel.bookings.push(booking);
  return booking;
}

export function cancel(kennel: Kennel, id: string): Booking {
  const index = kennel.bookings.findIndex((b) => b.id === id);
  if (index < 0) throw new KennelError(`no booking ${id}`);
  return kennel.bookings.splice(index, 1)[0];
}
