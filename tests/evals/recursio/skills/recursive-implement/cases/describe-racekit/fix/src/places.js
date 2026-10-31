// Places overall and within each category.
import { category, compareCategories } from './categories.js';

/**
 * Places in time order.
 * @param {object[]} finishers - finishers, fastest first.
 * @returns {object[]} each finisher with a `place`; the same time shares a place.
 */
export function rank(finishers) {
  return finishers.map((runner, i) => {
    const first = finishers.findIndex((r) => r.seconds === runner.seconds);
    return { ...runner, place: (first === -1 ? i : first) + 1 };
  });
}

/**
 * Places within each category.
 * @param {object[]} finishers - finishers, fastest first.
 * @param {number} year - the race's year.
 * @returns {Map<string, object[]>} each category with finishers, in category order, to its ranked finishers.
 */
export function byCategory(finishers, year) {
  const groups = new Map();
  for (const runner of finishers) {
    const key = category(runner.born, runner.sex, year);
    groups.set(key, [...(groups.get(key) ?? []), runner]);
  }
  return new Map([...groups.keys()].sort(compareCategories).map((key) => [key, rank(groups.get(key))]));
}
