// SPDX-License-Identifier: MIT
// Count words and pick the most frequent.

export function countWords(text) {
  const counts = new Map();
  for (const word of text.toLowerCase().match(/[a-z']+/g) ?? []) {
    counts.set(word, (counts.get(word) ?? 0) + 1);
  }
  return counts;
}

export function top(counts, limit = Infinity) {
  return [...counts.entries()]
    .sort(([a, x], [b, y]) => y - x || (a < b ? -1 : a > b ? 1 : 0))
    .slice(0, limit);
}
