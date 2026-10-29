// The plain-text receipt emailed after checkout.

function money(cents) {
  const dollars = (cents / 100).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  return `$${dollars}`;
}

function receiptText(order) {
  const lines = [`Order ${order.id}`, ""];
  let total = 0;
  for (const item of order.items) {
    const cents = item.qty * item.unitCents;
    total += cents;
    lines.push(`${`${item.qty} x ${item.name}`.padEnd(28)}${money(cents).padStart(12)}`);
  }
  lines.push("", `${"Total".padEnd(28)}${money(total).padStart(12)}`);
  return lines.join("\n");
}

module.exports = { receiptText };
