// Each line after the header is date,project,hours; dates are YYYY-MM-DD.
function readEntries(text) {
  return text
    .trim()
    .split("\n")
    .slice(1)
    .map((line) => {
      const [date, project, hours] = line.split(",");
      return { date, project, hours: Number(hours) };
    });
}

function totals(entries) {
  const sums = {};
  for (const e of entries) sums[e.project] = (sums[e.project] || 0) + e.hours;
  return sums;
}

module.exports = { readEntries, totals };
