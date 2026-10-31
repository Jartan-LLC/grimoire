/** Parse a course's raw scores. */

/** One row of the scores file. */
export type Score = { student: string; item: string; points: number; max: number };

/** Bad input, in scores or weights. */
export class ScoreError extends Error {}

/** The rows of a scores CSV in file order; blank lines are skipped. */
export function parseScores(text: string): Score[] {
  const scores: Score[] = [];
  text.split('\n').forEach((raw, index) => {
    const line = raw.trim();
    if (index === 0 || line === '') return;
    const fields = line.split(',');
    const where = `line ${index + 1}: `;
    if (fields.length !== 4) throw new ScoreError(`${where}expected 4 fields, got ${fields.length}`);
    const [student, item, pointsText, maxText] = fields.map((f) => f.trim());
    const points = Number(pointsText);
    const max = Number(maxText);
    if (pointsText === '' || Number.isNaN(points)) throw new ScoreError(`${where}points ${pointsText} is not a number`);
    if (maxText === '' || Number.isNaN(max)) throw new ScoreError(`${where}max ${maxText} is not a number`);
    if (max <= 0) throw new ScoreError(`${where}max must be above 0`);
    if (points < 0 || points > max) throw new ScoreError(`${where}points must be between 0 and ${max}`);
    scores.push({ student, item, points, max });
  });
  return scores;
}
