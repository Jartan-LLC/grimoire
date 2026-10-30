// The candidate with the most first preferences; ties go to the alphabetically first.
function plurality(ballots) {
  const counts = new Map();
  for (const [first] of ballots) counts.set(first, (counts.get(first) || 0) + 1);
  return [...counts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))[0][0];
}

module.exports = { plurality };
