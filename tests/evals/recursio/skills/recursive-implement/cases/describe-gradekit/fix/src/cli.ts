/** The gradekit command, kept free of process state so tests can run it. */
import { formatPercent } from './format.ts';
import { curve, distribution, letter } from './letters.ts';
import { ScoreError, parseScores } from './scores.ts';
import { parseWeights, percentages } from './weights.ts';

/** What a run of the command printed, and its exit status. */
export type Result = { status: number; output: string; error: string };

const USAGE = 'usage: gradekit report SCORES WEIGHTS [--curve MEAN] | gradekit dist SCORES WEIGHTS';

function fail(message: string): Result {
  return { status: 2, output: '', error: `gradekit: ${message}\n` };
}

/** Run the gradekit command on `argv`, reading files with `readText`. */
export function run(argv: string[], readText: (path: string) => string): Result {
  const [command, scoresPath, weightsPath, ...rest] = argv;
  if (!['report', 'dist'].includes(command) || weightsPath === undefined) return fail(USAGE);
  let target: number | undefined;
  if (rest.length) {
    target = Number(rest[1]);
    if (command !== 'report' || rest[0] !== '--curve' || rest.length !== 2 || Number.isNaN(target)) return fail(USAGE);
  }
  let percents: Map<string, number>;
  try {
    percents = percentages(parseScores(readText(scoresPath)), parseWeights(readText(weightsPath)));
  } catch (error) {
    if (error instanceof ScoreError) return fail(error.message);
    return fail(`cannot read ${error instanceof Error ? error.message : String(error)}`);
  }
  if (target !== undefined) percents = curve(percents, target);
  if (command === 'dist') {
    const counts = distribution([...percents.values()].map((p) => letter(p)));
    return { status: 0, output: [...counts].map(([name, n]) => `${name} ${n}\n`).join(''), error: '' };
  }
  const lines = [...percents].map(([student, p]) => `${student} ${formatPercent(p)} ${letter(p)}\n`);
  return { status: 0, output: lines.join(''), error: '' };
}
