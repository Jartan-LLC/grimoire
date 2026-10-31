import * as oneToTwo from "./migrations/1-to-2.js";
import * as twoToThree from "./migrations/2-to-3.js";

/** Every migration, oldest first. Each takes a config at `from` and returns it at `to`. */
const MIGRATIONS = [oneToTwo, twoToThree];

/** The version a fully migrated config has. */
export const LATEST = MIGRATIONS[MIGRATIONS.length - 1].to;

/**
 * Brings `config` up to LATEST. A config with no `version` is version 1. The input is not changed.
 * @param {Record<string, unknown>} config
 * @returns {Record<string, unknown>}
 */
export function migrate(config) {
  const start = config.version ?? 1;
  if (!Number.isInteger(start) || start < 1) {
    throw new Error(`bad config version: ${JSON.stringify(config.version)}`);
  }
  if (start > LATEST) {
    throw new Error(`config version ${start} is newer than this stashd understands (${LATEST})`);
  }
  let current = structuredClone(config);
  for (const step of MIGRATIONS) {
    if (step.from < start) continue;
    current = { ...step.up(current), version: step.to };
  }
  return { ...current, version: LATEST };
}
