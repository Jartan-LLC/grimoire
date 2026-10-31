/** Category weights and each student's weighted percentage. */
import { type Score, ScoreError } from './scores.ts';

/** Each category's weight, in percent. */
export type Weights = Record<string, number>;

/** The `category = weight` lines of a weights file; they must add up to 100. */
export function parseWeights(text: string): Weights {
  const weights: Weights = {};
  text.split('\n').forEach((raw, index) => {
    const line = raw.trim();
    if (line === '' || line.startsWith('#')) return;
    const match = /^([\w-]+)\s*=\s*(\d+(?:\.\d+)?)$/.exec(line);
    if (!match) throw new ScoreError(`line ${index + 1}: expected 'category = weight'`);
    weights[match[1]] = Number(match[2]);
  });
  const sum = Object.values(weights).reduce((a, b) => a + b, 0);
  if (Math.abs(sum - 100) > 1e-9) throw new ScoreError(`weights add up to ${sum}, not 100`);
  return weights;
}

/** Each student's percentage, keyed by student in name order. */
export function percentages(scores: Score[], weights: Weights): Map<string, number> {
  const totals = new Map<string, Map<string, { points: number; max: number }>>();
  for (const score of scores) {
    const category = score.item.split(':')[0];
    if (!(category in weights)) throw new ScoreError(`item ${score.item} has no weight for its category`);
    const byCategory = totals.get(score.student) ?? new Map();
    const sum = byCategory.get(category) ?? { points: 0, max: 0 };
    byCategory.set(category, { points: sum.points + score.points, max: sum.max + score.max });
    totals.set(score.student, byCategory);
  }
  const result = new Map<string, number>();
  for (const student of [...totals.keys()].sort()) {
    let percent = 0;
    for (const [category, sum] of totals.get(student)!) percent += (sum.points * weights[category]) / sum.max;
    result.set(student, percent);
  }
  return result;
}
