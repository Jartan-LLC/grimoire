// Copyright 2026 tripkit contributors. MIT licence.
// Who owes whom, and the payments that settle it.
import { type Rates, convert } from './currency.ts';
import type { Expense } from './expenses.ts';

export type Transfer = { from: string; to: string; cents: number };

export function balances(expenses: Expense[], home: string, rates: Rates): Map<string, number> {
  const owed = new Map<string, number>();
  const add = (name: string, cents: number) => owed.set(name, (owed.get(name) ?? 0) + cents);
  for (const expense of expenses) {
    const cents = convert(expense.amount, expense.currency, home, rates);
    add(expense.payer, cents);
    const share = Math.floor(cents / expense.sharedBy.length);
    const odd = cents - share * expense.sharedBy.length;
    expense.sharedBy.forEach((name, i) => add(name, -(share + (i < odd ? 1 : 0))));
  }
  return new Map([...owed].sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0)));
}

export function settle(balances: Map<string, number>): Transfer[] {
  const left = new Map(balances);
  const transfers: Transfer[] = [];
  const pick = (sign: number) => [...left].filter(([, c]) => c * sign > 0).sort(([a, x], [b, y]) => sign * (y - x) || (a < b ? -1 : 1))[0];
  for (;;) {
    const debtor = pick(-1);
    const creditor = pick(1);
    if (!debtor || !creditor) return transfers;
    const cents = Math.min(-debtor[1], creditor[1]);
    transfers.push({ from: debtor[0], to: creditor[0], cents });
    left.set(debtor[0], debtor[1] + cents);
    left.set(creditor[0], creditor[1] - cents);
  }
}
