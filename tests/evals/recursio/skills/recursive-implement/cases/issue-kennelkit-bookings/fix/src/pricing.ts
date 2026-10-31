/** @file What a stay costs. */
import { type Booking, type Dog, type Size, addDays, weekday } from './model.ts';

export const PRICES: Record<Size, number> = { small: 3000, large: 4000 };

export function price(booking: Booking, dog: Dog, prices: Record<Size, number> = PRICES): number {
  let cents = 0;
  let nights = 0;
  for (let night = booking.from; night < booking.to; night = addDays(night, 1)) {
    cents += prices[dog.size] + ([5, 6].includes(weekday(night)) ? 500 : 0);
    nights += 1;
  }
  return nights >= 7 ? Math.floor(cents * 0.9) : cents;
}
