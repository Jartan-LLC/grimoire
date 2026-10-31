/** Letter grades, their distribution and the curve. */

/** Letters with the lowest percentage that earns each, highest first. */
export type Cutoffs = [letter: string, min: number][];

/** A 90, B 80, C 70, D 60, F 0. */
export const DEFAULT_CUTOFFS: Cutoffs = [['A', 90], ['B', 80], ['C', 70], ['D', 60], ['F', 0]];

/** The first letter whose minimum the percentage reaches; the percentage is not rounded first. */
export function letter(percent: number, cutoffs: Cutoffs = DEFAULT_CUTOFFS): string {
  const found = cutoffs.find(([, min]) => percent >= min);
  return found ? found[0] : cutoffs[cutoffs.length - 1][0];
}

/** How many of each letter, in cutoff order, zeros included. */
export function distribution(letters: string[], cutoffs: Cutoffs = DEFAULT_CUTOFFS): Map<string, number> {
  const counts = new Map<string, number>(cutoffs.map(([name]) => [name, 0]));
  for (const name of letters) counts.set(name, (counts.get(name) ?? 0) + 1);
  return counts;
}

/** Raise every percentage by the gap between the class mean and `target`, none above 100. */
export function curve(percents: Map<string, number>, target: number): Map<string, number> {
  const values = [...percents.values()];
  const mean = values.reduce((a, b) => a + b, 0) / (values.length || 1);
  if (mean >= target) return new Map(percents);
  return new Map([...percents].map(([student, value]) => [student, Math.min(100, value + target - mean)]));
}
