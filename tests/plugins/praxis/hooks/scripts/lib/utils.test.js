const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { describe, test } = require('node:test');

const { REPO_ROOT, tempDir, writeFiles } = require('../../../../../helpers/fixture');
const { knownDefect } = require('../../../../../helpers/known-defect');

const { findFiles, countInFile, grepFile } = require(
  path.join(REPO_ROOT, 'plugins/praxis/hooks/scripts/lib/utils.js'),
);

const DAY_S = 24 * 60 * 60;

/** A temp file holding `contents`. */
function textFile(t, contents) {
  const file = path.join(tempDir(t), 'f.txt');
  fs.writeFileSync(file, contents);
  return file;
}

describe('findFiles', () => {
  const names = (results, dir) => results.map(r => path.relative(dir, r.path)).sort();

  test('* and ? are the only wildcards; every other character is literal', t => {
    const dir = tempDir(t);
    writeFiles(dir, {
      'a.md': '',
      'b.md': '',
      'a.mdx': '',
      amd: '',
      'file1.txt': '',
      'file12.txt': '',
      'aXb': '',
      'a.b': '',
      'notes(1)+[draft].txt': '',
    });
    assert.deepEqual(names(findFiles(dir, '*.md'), dir), ['a.md', 'b.md']);
    assert.deepEqual(names(findFiles(dir, 'file?.txt'), dir), ['file1.txt']);
    assert.deepEqual(names(findFiles(dir, 'a.b'), dir), ['a.b']);
    assert.deepEqual(names(findFiles(dir, 'notes(1)+[draft].txt'), dir), ['notes(1)+[draft].txt']);
  });

  test('descends into subdirectories only when recursive', t => {
    const dir = tempDir(t);
    writeFiles(dir, { 'top.log': '', 'sub/deep/inner.log': '' });
    assert.deepEqual(names(findFiles(dir, '*.log'), dir), ['top.log']);
    assert.deepEqual(names(findFiles(dir, '*.log', { recursive: true }), dir), [
      path.join('sub', 'deep', 'inner.log'),
      'top.log',
    ]);
  });

  test('maxAge drops older files, and results come newest first', t => {
    const dir = tempDir(t);
    writeFiles(dir, { 'new.tmp': '', 'mid.tmp': '', 'old.tmp': '' });
    const now = Date.now() / 1000;
    for (const [name, days] of [['new.tmp', 0.5], ['mid.tmp', 2], ['old.tmp', 10]]) {
      fs.utimesSync(path.join(dir, name), now - days * DAY_S, now - days * DAY_S);
    }
    const order = results => results.map(r => path.basename(r.path));
    assert.deepEqual(order(findFiles(dir, '*.tmp')), ['new.tmp', 'mid.tmp', 'old.tmp']);
    assert.deepEqual(order(findFiles(dir, '*.tmp', { maxAge: 3 })), ['new.tmp', 'mid.tmp']);
  });

  test('returns nothing for a missing directory or an empty pattern', t => {
    assert.deepEqual(findFiles(path.join(tempDir(t), 'absent'), '*'), []);
    assert.deepEqual(findFiles(tempDir(t), ''), []);
  });
});

describe('countInFile', () => {
  test('counts every match whether or not the RegExp carries g', t => {
    const file = textFile(t, 'foo\nFOO foo\nbar foo\n');
    assert.equal(countInFile(file, /foo/), 3);
    assert.equal(countInFile(file, /foo/g), 3);
    assert.equal(countInFile(file, /foo/i), 4);
    assert.equal(countInFile(file, 'fo+'), 3);
  });

  test('gives the same count on repeat calls with one global RegExp', t => {
    const file = textFile(t, 'x x x');
    const pattern = /x/g;
    assert.equal(countInFile(file, pattern), 3);
    assert.equal(countInFile(file, pattern), 3);
  });

  test('returns 0 for an invalid pattern, a non-pattern or a missing file', t => {
    const file = textFile(t, 'a(b');
    assert.equal(countInFile(file, 'a('), 0);
    assert.equal(countInFile(file, 42), 0);
    assert.equal(countInFile(path.join(tempDir(t), 'absent'), 'a'), 0);
  });
});

describe('grepFile', () => {
  const lines = results => results.map(r => r.lineNumber);

  test('reports every matching line with its 1-based number', t => {
    const file = textFile(t, 'console.log(1)\nkeep\nconsole.log(2)\n');
    assert.deepEqual(grepFile(file, 'console\\.log'), [
      { lineNumber: 1, content: 'console.log(1)' },
      { lineNumber: 3, content: 'console.log(2)' },
    ]);
  });

  test('a global RegExp still matches consecutive lines', t => {
    const file = textFile(t, 'hit\nhit\nhit\nmiss\nhit\n');
    assert.deepEqual(lines(grepFile(file, /hit/g)), [1, 2, 3, 5]);
  });

  // grepFile strips g but not y, so a sticky RegExp keeps lastIndex across lines.
  test(
    'a sticky RegExp still matches consecutive lines',
    knownDefect('grimoire#78', /strictly deep-equal/, t => {
      const file = textFile(t, 'hit\nhit\nhit\n');
      assert.deepEqual(lines(grepFile(file, /hit/y)), [1, 2, 3]);
    }),
  );

  test('keeps the other flags', t => {
    const file = textFile(t, 'Hit\nhit\n');
    assert.deepEqual(lines(grepFile(file, /hit/gi)), [1, 2]);
  });

  test('returns nothing for an invalid pattern or a missing file', t => {
    assert.deepEqual(grepFile(textFile(t, 'a(b'), 'a('), []);
    assert.deepEqual(grepFile(path.join(tempDir(t), 'absent'), 'a'), []);
  });
});
