// Copyright 2026 tripkit contributors. MIT licence.
// Exchange rates and conversion. Rates come from a file: fetching them is left to the maintainer.
import { TripError } from './errors.ts';

export type Rates = { base: string; rates: Record<string, number> };

export function parseRates(text: string): Rates {
  const data = JSON.parse(text) as Partial<Rates>;
  if (typeof data.base !== 'string' || typeof data.rates !== 'object' || data.rates === null) throw new TripError('rates need base and rates');
  return { base: data.base, rates: { ...data.rates } };
}

function rate(currency: string, rates: Rates): number {
  if (currency === rates.base) return 1;
  const found = rates.rates[currency];
  if (found === undefined) throw new TripError(`no rate for ${currency}`);
  return found;
}

export function convert(cents: number, from: string, to: string, rates: Rates): number {
  return Math.round((cents / rate(from, rates)) * rate(to, rates));
}
