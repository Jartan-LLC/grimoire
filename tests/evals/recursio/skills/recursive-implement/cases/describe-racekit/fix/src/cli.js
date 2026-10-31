// The racekit command, kept free of process state so tests can run it.
import { category } from './categories.js';
import { RaceError, formatDuration } from './clock.js';
import { byCategory, rank } from './places.js';
import { finishers, parseResults } from './results.js';

const USAGE = 'usage: racekit results FILE YEAR [--category CAT] | winners FILE YEAR';

/**
 * Runs the racekit command.
 * @param {string[]} argv - the arguments after the command name.
 * @param {(path: string) => string} readText - reads a file.
 * @returns {{status: number, output: string, error: string}} what the command prints and its status.
 */
export function run(argv, readText) {
  const [command, path, yearText, ...rest] = argv;
  const only = rest[0] === '--category' && rest.length === 2 ? rest[1] : null;
  const year = Number(yearText);
  const usable = (command === 'results' && (rest.length === 0 || only)) || (command === 'winners' && rest.length === 0);
  if (!usable || !path || !Number.isInteger(year)) return { status: 2, output: '', error: `racekit: ${USAGE}\n` };
  try {
    let text;
    try {
      text = readText(path);
    } catch {
      throw new RaceError(`cannot read ${path}`);
    }
    const results = parseResults(text);
    const done = finishers(results);
    const line = (r, cat) => `${r.place} ${r.bib} ${r.name} ${formatDuration(r.seconds)} ${cat}\n`;
    let output = '';
    if (command === 'winners') {
      for (const [cat, ranked] of byCategory(done, year)) output += `${cat} ${ranked[0].bib} ${ranked[0].name} ${formatDuration(ranked[0].seconds)}\n`;
    } else if (only) {
      output = (byCategory(done, year).get(only) ?? []).map((r) => line(r, only)).join('');
    } else {
      output = rank(done).map((r) => line(r, category(r.born, r.sex, year))).join('');
      output += results.filter((r) => r.seconds === null).map((r) => `DNF ${r.bib} ${r.name}\n`).join('');
    }
    return { status: 0, output, error: '' };
  } catch (error) {
    if (error instanceof RaceError) return { status: 2, output: '', error: `racekit: ${error.message}\n` };
    throw error;
  }
}
