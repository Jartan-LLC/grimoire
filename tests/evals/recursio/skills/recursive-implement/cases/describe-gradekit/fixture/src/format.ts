/** Formatting shared by the command's outputs. */

/** A percentage with one decimal, such as `85.0`. */
export function formatPercent(value: number): string {
  return value.toFixed(1);
}
