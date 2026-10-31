// Version 2 names the retention period after its unit.
export const from = 1;
export const to = 2;

/** @param {Record<string, unknown>} config */
export function up(config) {
  const { keep, ...rest } = config;
  return keep === undefined ? rest : { ...rest, keepDays: keep };
}
