import { readFileSync } from "node:fs";
import { parseArgs } from "node:util";
import { parseCsv } from "./read.js";

const USAGE = "usage: csvtool cols|count FILE\n";

/** @type {Record<string, (rows: string[][]) => string>} */
const COMMANDS = {
  cols: (rows) => (rows[0] ?? []).map((name) => `${name}\n`).join(""),
  count: (rows) => `${Math.max(rows.length - 1, 0)}\n`,
};

/**
 * Runs csvtool with `argv` (the arguments after the program name); returns the exit status.
 * @param {string[]} argv
 * @param {{ stdout?: { write(s: string): unknown }, stderr?: { write(s: string): unknown } }} [io]
 */
export function run(argv, { stdout = process.stdout, stderr = process.stderr } = {}) {
  let positionals;
  try {
    ({ positionals } = parseArgs({ args: argv, allowPositionals: true, options: {} }));
  } catch (error) {
    stderr.write(`csvtool: ${error.message}\n${USAGE}`);
    return 2;
  }
  const [command, file] = positionals;
  if (!Object.hasOwn(COMMANDS, command ?? "") || !file) {
    stderr.write(USAGE);
    return 2;
  }
  let text;
  try {
    text = readFileSync(file, "utf8");
  } catch (error) {
    stderr.write(`csvtool: cannot read ${file}: ${error.code}\n`);
    return 1;
  }
  stdout.write(COMMANDS[command](parseCsv(text)));
  return 0;
}
