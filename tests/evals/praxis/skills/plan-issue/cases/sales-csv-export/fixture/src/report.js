// One row per product sold in the month: units, revenue in cents, and share of the month's revenue.
function monthlyRows(orders, month) {
  const byProduct = new Map();
  for (const order of orders) {
    if (!order.date.startsWith(month)) continue;
    for (const line of order.lines) {
      const row = byProduct.get(line.product) || { product: line.product, units: 0, cents: 0 };
      row.units += line.qty;
      row.cents += line.qty * line.unitCents;
      byProduct.set(line.product, row);
    }
  }
  const rows = [...byProduct.values()].sort((a, b) => b.cents - a.cents);
  const total = rows.reduce((sum, row) => sum + row.cents, 0);
  return rows.map((row) => ({ ...row, share: total ? row.cents / total : 0 }));
}

module.exports = { monthlyRows };
