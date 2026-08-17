'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const {
  buildSkipMatcher,
  prose,
  findRetoldInDiff,
  dedupePairs
} = require('./find-duplicate-comments.js');

test('prose()', async (t) => {
  await t.test('extracts // # * and /* */ openers', () => {
    assert.equal(prose('// this line names a real behavioral constraint here'), 'this line names a real behavioral constraint here');
    assert.equal(prose('  # this line names a real behavioral constraint here'), 'this line names a real behavioral constraint here');
    assert.equal(prose('  * this line names a real behavioral constraint here'), 'this line names a real behavioral constraint here');
    assert.equal(prose('/* this line names a real behavioral constraint */'), 'this line names a real behavioral constraint');
  });

  await t.test('drops a trailing CRLF before matching', () => {
    // Regression: a CRLF-committed blob left a trailing \r that the `(.*)$`
    // patterns rejected, silently hiding the comment (false-clean).
    const withCr = '// this line names a real behavioral constraint here\r';
    assert.equal(prose(withCr), prose('// this line names a real behavioral constraint here'));
    assert.notEqual(prose(withCr), '');
  });

  await t.test('drops short comments below the prose floor', () => {
    assert.equal(prose('// too short'), '');
  });

  await t.test('normalizes case and punctuation so wrapping does not hide a twin', () => {
    const a = prose('// This Line, Wraps! Some Punctuation--here.');
    const b = prose('// this line wraps some punctuation here');
    assert.equal(a, b);
  });

  await t.test('exempts mandated/machine-read markers regardless of length', () => {
    assert.equal(prose('// SPDX-License-Identifier: MIT, a long enough line to pass the floor'), '');
    assert.equal(prose('# noqa: this would otherwise be long enough to pass the floor check'), '');
  });

  await t.test('returns empty for a non-comment line', () => {
    assert.equal(prose('const x = 1;'), '');
  });
});

test('buildSkipMatcher()', async (t) => {
  await t.test('always skips node_modules even with no extra segments', () => {
    const m = buildSkipMatcher([]);
    assert.ok(m.test('node_modules/foo.js'));
    assert.ok(m.test('a/node_modules/b.js'));
  });

  await t.test('matches a whole path segment, never a substring', () => {
    const m = buildSkipMatcher(['dist']);
    assert.ok(m.test('dist/bundle.js'));
    assert.ok(m.test('a/dist/b.js'));
    assert.ok(!m.test('redistribute.js'));
  });

  await t.test('escapes regex metacharacters in a caller-supplied segment', () => {
    // Regression: an unescaped `--skip .*` would compile as a wildcard,
    // match every path, and report a clean tree with nothing actually
    // checked -- the silent false-clean this tool exists to avoid.
    const m = buildSkipMatcher(['.*']);
    assert.ok(m.test('.*/file.js'));
    assert.ok(!m.test('anything/file.js'));
  });
});

test('findRetoldInDiff()', async (t) => {
  await t.test('reports an added line whose prose is indexed elsewhere', () => {
    const diff = [
      '@@ -1,2 +1,3 @@',
      ' unchanged line',
      '+// this line names a real behavioral constraint here',
      ' another unchanged line'
    ].join('\n');
    const index = new Map([['this line names a real behavioral constraint here', ['other/file.js:9']]]);
    const findings = findRetoldInDiff(diff, 'new/file.js', index);
    assert.equal(findings.length, 1);
    assert.equal(findings[0].here, 'new/file.js:2');
    assert.deepEqual(findings[0].elsewhere, ['other/file.js:9']);
  });

  await t.test('does not self-match the site being checked', () => {
    const diff = [
      '@@ -1,1 +1,1 @@',
      '+// this line names a real behavioral constraint here'
    ].join('\n');
    const index = new Map([['this line names a real behavioral constraint here', ['new/file.js:1']]]);
    const findings = findRetoldInDiff(diff, 'new/file.js', index);
    assert.equal(findings.length, 0);
  });

  await t.test('keeps line numbers correct across a "no newline at end of file" marker', () => {
    // Regression: that marker annotates the previous line rather than being
    // one; counting it as a line shifted every later line number by one.
    const diff = [
      '@@ -1,2 +1,3 @@',
      ' unchanged',
      '+first added line, not the one under test at all really',
      '\\ No newline at end of file',
      '+// this line names a real behavioral constraint here'
    ].join('\n');
    const index = new Map([['this line names a real behavioral constraint here', ['other/file.js:9']]]);
    const findings = findRetoldInDiff(diff, 'new/file.js', index);
    assert.equal(findings.length, 1);
    assert.equal(findings[0].here, 'new/file.js:3');
  });

  await t.test('ignores removed lines', () => {
    const diff = [
      '@@ -1,1 +1,0 @@',
      '-// this line names a real behavioral constraint here'
    ].join('\n');
    const index = new Map([['this line names a real behavioral constraint here', ['other/file.js:9']]]);
    const findings = findRetoldInDiff(diff, 'new/file.js', index);
    assert.equal(findings.length, 0);
  });
});

test('dedupePairs()', async (t) => {
  await t.test('collapses a symmetric pair added in the same diff to one entry', () => {
    const findings = [
      { here: 'a.js:1', text: 't', elsewhere: ['b.js:2'] },
      { here: 'b.js:2', text: 't', elsewhere: ['a.js:1'] }
    ];
    assert.equal(dedupePairs(findings).length, 1);
  });

  await t.test('keeps unrelated findings distinct', () => {
    const findings = [
      { here: 'a.js:1', text: 't1', elsewhere: ['b.js:2'] },
      { here: 'c.js:5', text: 't2', elsewhere: ['d.js:6'] }
    ];
    assert.equal(dedupePairs(findings).length, 2);
  });
});
