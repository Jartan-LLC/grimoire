// Acceptance tests for racekit, as the README specifies.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { ageOn, category, compareCategories } from '../src/categories.js';
import { run } from '../src/cli.js';
import { RaceError } from '../src/clock.js';
import { byCategory, rank } from '../src/places.js';
import { finishers, parseResults } from '../src/results.js';

const YEAR = 2026;

const RESULTS = `bib,name,born,sex,start,finish
12,Ana Ruiz,1990,F,09:00:04,09:41:11
7,Ben Ola,2008,M,09:00:10,09:38:40
31,Cy Park,1975,M,09:00:02,09:44:50

4,Dee Moss,1999,F,09:00:20,09:47:05
19,Eli Shah,1962,M,09:01:00,
22,Fay Lund,1988,F,09:00:30,09:40:55
9,Gus Hale,1996,M,09:00:15,09:36:59
`;

const FILES = { 'results.csv': RESULTS };

function read(path) {
  if (!(path in FILES)) throw new Error(`ENOENT: ${path}`);
  return FILES[path];
}

function bad(row) {
  return `bib,name,born,sex,start,finish\n12,Ana Ruiz,1990,F,09:00:04,09:41:11\n${row}\n`;
}

test('results keep file order', () => {
  const results = parseResults(RESULTS);
  assert.equal(results.length, 7);
  assert.deepEqual(results[0], { bib: 12, name: 'Ana Ruiz', born: 1990, sex: 'F', seconds: 2467 });
  assert.deepEqual(results[4], { bib: 19, name: 'Eli Shah', born: 1962, sex: 'M', seconds: null });
});

test('a bad row names its line', () => {
  for (const row of ['13,Bo,1990,F,09:00:00,08:59:00', '13,Bo,1990,X,09:00:00,09:40:00', '12,Bo,1990,F,09:00:00,09:40:00', '13,Bo,1990,F,09:00:00', '13,Bo,90,F,09:00:00,09:40:00', '1.5,Bo,1990,F,09:00:00,09:40:00']) {
    assert.throws(() => parseResults(bad(row)), (e) => e instanceof RaceError && /^line 3: /.test(e.message), row);
  }
});

test('finishers run fastest first', () => {
  assert.deepEqual(finishers(parseResults(RESULTS)).map((r) => r.bib), [9, 7, 22, 12, 31, 4]);
});

test('ages and categories', () => {
  assert.equal(ageOn(1990, YEAR), 36);
  assert.equal(category(1990, 'F', YEAR), 'FV35');
  assert.equal(category(2008, 'M', YEAR), 'MU20');
  assert.equal(category(2007, 'M', YEAR), 'MU20');
  assert.equal(category(2006, 'M', YEAR), 'MSEN');
  assert.equal(category(1992, 'F', YEAR), 'FSEN');
  assert.equal(category(1991, 'F', YEAR), 'FV35');
  assert.equal(category(1975, 'M', YEAR), 'MV50');
  assert.equal(category(1951, 'M', YEAR), 'MV70');
  assert.throws(() => category(2018, 'F', YEAR), RaceError);
});

test('categories sort by sex, then band', () => {
  assert.deepEqual(['MV50', 'FV40', 'MU20', 'FSEN', 'MSEN', 'FV35', 'FU20'].sort(compareCategories), ['FU20', 'FSEN', 'FV35', 'FV40', 'MU20', 'MSEN', 'MV50']);
});

test('places count from 1 in time order', () => {
  const ranked = rank(finishers(parseResults(RESULTS)));
  assert.deepEqual(ranked.map((r) => [r.place, r.bib]), [[1, 9], [2, 7], [3, 22], [4, 12], [5, 31], [6, 4]]);
  assert.equal(ranked[0].name, 'Gus Hale');
});

test('places within each category', () => {
  const groups = byCategory(finishers(parseResults(RESULTS)), YEAR);
  assert.deepEqual([...groups.keys()], ['FSEN', 'FV35', 'MU20', 'MSEN', 'MV50']);
  assert.deepEqual(groups.get('FV35').map((r) => [r.place, r.bib]), [[1, 22], [2, 12]]);
});

test('results', () => {
  assert.deepEqual(run(['results', 'results.csv', '2026'], read), {
    status: 0,
    output: '1 9 Gus Hale 0:36:44 MSEN\n2 7 Ben Ola 0:38:30 MU20\n3 22 Fay Lund 0:40:25 FV35\n4 12 Ana Ruiz 0:41:07 FV35\n5 31 Cy Park 0:44:48 MV50\n6 4 Dee Moss 0:46:45 FSEN\nDNF 19 Eli Shah\n',
    error: '',
  });
});

test('results for one category', () => {
  assert.equal(run(['results', 'results.csv', '2026', '--category', 'FV35'], read).output, '1 22 Fay Lund 0:40:25 FV35\n2 12 Ana Ruiz 0:41:07 FV35\n');
});

test('winners', () => {
  assert.equal(run(['winners', 'results.csv', '2026'], read).output, 'FSEN 4 Dee Moss 0:46:45\nFV35 22 Fay Lund 0:40:25\nMU20 7 Ben Ola 0:38:30\nMSEN 9 Gus Hale 0:36:44\nMV50 31 Cy Park 0:44:48\n');
});

test('errors exit 2', () => {
  const missing = run(['results', 'nope.csv', '2026'], read);
  assert.equal(missing.status, 2);
  assert.ok(missing.error.startsWith('racekit: '));
  FILES['bad.csv'] = bad('13,Bo,1990,X,09:00:00,09:40:00');
  const broken = run(['winners', 'bad.csv', '2026'], read);
  assert.equal(broken.status, 2);
  assert.ok(broken.error.startsWith('racekit: line 3: '), broken.error);
  assert.equal(run(['podium', 'results.csv', '2026'], read).status, 2);
});
