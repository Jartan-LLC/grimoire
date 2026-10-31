// Acceptance tests for gradekit, as the README specifies.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { run } from '../src/cli.ts';
import { curve, distribution, letter } from '../src/letters.ts';
import { ScoreError, parseScores } from '../src/scores.ts';
import { parseWeights, percentages } from '../src/weights.ts';

const SCORES = `student,item,points,max
ben,hw:1,5,10
ana,hw:1,9,10

ana,hw:2,8,10
ana,exam:final,85,100
ben,hw:2,7,10
ben,exam:final,60,100
cy,hw:1,10,10
cy,exam:final,95,100
`;

const WEIGHTS = '# homework and the final\nhw = 40\nexam = 60\n';

const FILES: Record<string, string> = { 'scores.csv': SCORES, 'weights.txt': WEIGHTS };

function read(path: string): string {
  if (!(path in FILES)) throw new Error(`ENOENT: ${path}`);
  return FILES[path];
}

function near(actual: number, expected: number): void {
  assert.ok(Math.abs(actual - expected) < 1e-9, `${actual} is not ${expected}`);
}

test('scores keep file order', () => {
  const scores = parseScores(SCORES);
  assert.equal(scores.length, 8);
  assert.deepEqual(scores[0], { student: 'ben', item: 'hw:1', points: 5, max: 10 });
  assert.deepEqual(scores[2], { student: 'ana', item: 'hw:2', points: 8, max: 10 });
});

test('a bad score names its line', () => {
  assert.throws(() => parseScores('student,item,points,max\nana,hw:1,9,10\nana,hw:2,11,10\n'), (e: unknown) => e instanceof ScoreError && /^line 3: /.test(e.message));
  assert.throws(() => parseScores('student,item,points,max\nana,hw:1,nine,10\n'), (e: unknown) => e instanceof ScoreError && /^line 2: /.test(e.message));
});

test('weights must add up to 100', () => {
  assert.deepEqual(parseWeights(WEIGHTS), { hw: 40, exam: 60 });
  assert.throws(() => parseWeights('hw = 40\nexam = 50\n'), (e: unknown) => e instanceof ScoreError && e.message.includes('90'));
});

test('percentages weight each category by points over the maximum', () => {
  const result = percentages(parseScores(SCORES), parseWeights(WEIGHTS));
  assert.deepEqual([...result.keys()], ['ana', 'ben', 'cy']);
  near(result.get('ana')!, 85);
  near(result.get('ben')!, 60);
  near(result.get('cy')!, 97);
});

test('a missing category scores 0 and an unweighted one is an error', () => {
  const scores = parseScores('student,item,points,max\ndee,exam:final,50,100\n');
  near(percentages(scores, { hw: 40, exam: 60 }).get('dee')!, 30);
  const quiz = parseScores('student,item,points,max\ndee,quiz:1,5,10\n');
  assert.throws(() => percentages(quiz, { hw: 40, exam: 60 }), /quiz:1/);
});

test('letters by cutoff', () => {
  assert.equal(letter(97), 'A');
  assert.equal(letter(90), 'A');
  assert.equal(letter(79.2), 'C');
  assert.equal(letter(0), 'F');
  assert.equal(letter(50, [['P', 50], ['F', 0]]), 'P');
});

test('distribution lists every letter in cutoff order', () => {
  assert.deepEqual([...distribution(['B', 'D', 'A', 'B'])], [['A', 1], ['B', 2], ['C', 0], ['D', 1], ['F', 0]]);
});

test('the curve raises everyone by the gap to the target mean, capped at 100', () => {
  const curved = curve(new Map([['ana', 85], ['ben', 60], ['cy', 97]]), 85);
  assert.deepEqual([...curved.keys()], ['ana', 'ben', 'cy']);
  near(curved.get('ana')!, 85 + 13 / 3);
  near(curved.get('ben')!, 60 + 13 / 3);
  assert.equal(curved.get('cy'), 100);
  assert.deepEqual([...curve(new Map([['ana', 85]]), 80)], [['ana', 85]]);
});

test('report', () => {
  assert.deepEqual(run(['report', 'scores.csv', 'weights.txt'], read), { status: 0, output: 'ana 85.0 B\nben 60.0 D\ncy 97.0 A\n', error: '' });
});

test('report with a curve', () => {
  assert.equal(run(['report', 'scores.csv', 'weights.txt', '--curve', '85'], read).output, 'ana 89.3 B\nben 64.3 D\ncy 100.0 A\n');
});

test('dist', () => {
  assert.equal(run(['dist', 'scores.csv', 'weights.txt'], read).output, 'A 1\nB 1\nC 0\nD 1\nF 0\n');
});

test('errors exit 2', () => {
  const missing = run(['report', 'nope.csv', 'weights.txt'], read);
  assert.equal(missing.status, 2);
  assert.ok(missing.error.startsWith('gradekit: '));
  FILES['bad.csv'] = 'student,item,points,max\nana,hw:1,-1,10\n';
  const bad = run(['report', 'bad.csv', 'weights.txt'], read);
  assert.equal(bad.status, 2);
  assert.ok(bad.error.startsWith('gradekit: line 2: '), bad.error);
});
