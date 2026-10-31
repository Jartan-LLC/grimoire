// Copyright 2026 tripkit contributors. MIT licence.
// Parse an expenses file.
import { TripError } from './errors.ts';

export type Expense = { payer: string; amount: number; currency: string; sharedBy: string[]; note: string };

export function parseExpenses(text: string): Expense[] {
  const expenses: Expense[] = [];
  text.split('\n').forEach((raw, index) => {
    const line = raw.trim();
    if (index === 0 || line === '') return;
    const where = `line ${index + 1}: `;
    const fields = line.split(',').map((f) => f.trim());
    if (fields.length !== 5) throw new TripError(`${where}expected payer,amount,currency,shared_by,note`);
    const [payer, amountText, currency, shared, note] = fields;
    if (!/^\d+(\.\d{1,2})?$/.test(amountText) || Number(amountText) <= 0) throw new TripError(`${where}bad amount ${amountText}`);
    if (!/^[A-Z]{3}$/.test(currency)) throw new TripError(`${where}bad currency ${currency}`);
    const sharedBy = shared.split(';').map((s) => s.trim()).filter(Boolean);
    if (sharedBy.length === 0) throw new TripError(`${where}nobody shares this cost`);
    expenses.push({ payer, amount: Math.round(Number(amountText) * 100), currency, sharedBy, note });
  });
  return expenses;
}
