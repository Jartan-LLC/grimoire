const HEADERS = ["Product", "Units", "Revenue", "Share"];

function cells(row) {
  return [row.product, String(row.units), (row.cents / 100).toFixed(2), `${(row.share * 100).toFixed(1)}%`];
}

function renderTable(rows) {
  const body = rows.map(cells);
  const widths = HEADERS.map((h, i) => Math.max(h.length, ...body.map((r) => r[i].length)));
  const line = (r) => r.map((c, i) => (i === 0 ? c.padEnd(widths[i]) : c.padStart(widths[i]))).join("  ");
  return [line(HEADERS), line(widths.map((w) => "-".repeat(w))), ...body.map(line)].join("\n");
}

module.exports = { renderTable };
