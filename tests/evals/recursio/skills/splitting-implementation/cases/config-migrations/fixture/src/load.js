import { readFileSync } from "node:fs";
import { migrate } from "./migrate.js";

/**
 * Reads a stashd.json and migrates it to the current shape.
 * @param {string} path
 */
export function loadConfig(path) {
  return migrate(JSON.parse(readFileSync(path, "utf8")));
}
