// The aligned score table printed to the terminal.

function formatTable(rows) {
  const width = Math.max(7, ...rows.map((row) => row.student.length));
  const lines = [`${"Student".padEnd(width)}  Score`];
  for (const row of rows) {
    lines.push(`${row.student.padEnd(width)}  ${row.score}/${row.outOf}`);
  }
  return lines.join("\n");
}

module.exports = { formatTable };
