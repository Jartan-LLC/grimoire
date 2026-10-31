// Version 3 makes the schedule explicit; older files always ran daily.
export const from = 2;
export const to = 3;

/** @param {Record<string, unknown>} config */
export function up(config) {
  return { schedule: "daily", ...config };
}
