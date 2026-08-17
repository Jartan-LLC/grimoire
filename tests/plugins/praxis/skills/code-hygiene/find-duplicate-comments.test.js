// Tests for the duplicate-comment finder's parsing and bookkeeping.
//
// Four of the cases below are named `regression:` and each pins a defect the
// tool actually shipped, found by hand against a throwaway repository. Each is
// written to fail against the pre-fix behaviour, so removing the fix reddens the
// suite rather than only deleting a code comment.
//
// Fixtures are throwaway repositories under the OS temp directory, never this
// checkout: the tool runs against whatever repository is being reviewed, and a
// fixture that is this repository lets a rule which suppresses a finding here
// look correct.

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const SOURCE = path.resolve(
  __dirname,
  '../../../../../plugins/praxis/skills/code-hygiene/find-duplicate-comments.js'
);
const {
  parseArgs,
  buildSkipMatcher,
  prose,
  trackedPaths,
  buildCommentIndex,
  findRetoldInDiff,
  dedupePairs
} = require(SOURCE);

// One comment body reused throughout, long enough to clear MIN_PROSE_CHARS, and
// the prose() output it normalizes to.
const COMMENT = 'The retold fact rule needs a whole repo view';
const PROSE = 'the retold fact rule needs a whole repo view';

const GIT_ENV = {
  GIT_AUTHOR_NAME: 'Grimoire Fixture',
  GIT_AUTHOR_EMAIL: 'fixture@example.invalid',
  GIT_COMMITTER_NAME: 'Grimoire Fixture',
  GIT_COMMITTER_EMAIL: 'fixture@example.invalid'
};

function gitIn(cwd, args) {
  const r = spawnSync('git', args, { cwd, encoding: 'utf8', env: { ...process.env, ...GIT_ENV } });
  assert.equal(r.status, 0, `git ${args.join(' ')} failed: ${r.stderr}`);
  return r.stdout;
}

/**
 * A throwaway repository holding `files` as one commit. Config is set rather
 * than inherited: autocrlf on the developer's machine would rewrite the CRLF
 * fixture's bytes, and a signing requirement would fail the commit.
 */
function makeRepo(files) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'grimoire-dupes-'));
  gitIn(dir, ['init', '-q']);
  gitIn(dir, ['config', 'core.autocrlf', 'false']);
  gitIn(dir, ['config', 'commit.gpgsign', 'false']);

  for (const [name, content] of Object.entries(files)) {
    const full = path.join(dir, name);
    fs.mkdirSync(path.dirname(full), { recursive: true });
    fs.writeFileSync(full, content);
  }

  gitIn(dir, ['add', '-A']);
  gitIn(dir, ['commit', '-qm', 'fixture']);
  return dir;
}

/** Run `fn` with the fixture as cwd -- git() in the tool inherits it -- then delete it. */
function inRepo(dir, fn) {
  const before = process.cwd();
  process.chdir(dir);
  try {
    return fn();
  } finally {
    process.chdir(before);
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

test('parseArgs defaults the base ref and collects no skips', () => {
  assert.deepEqual(parseArgs([]), { base: 'origin/main', skips: [] });
});

test('parseArgs takes a positional base ref', () => {
  assert.deepEqual(parseArgs(['HEAD~3']), { base: 'HEAD~3', skips: [] });
});

test('parseArgs collects both --skip spellings, in any position', () => {
  assert.deepEqual(
    parseArgs(['--skip', 'dist', 'upstream/main', '--skip=build']),
    { base: 'upstream/main', skips: ['dist', 'build'] }
  );
});

// die() exits the process, so the rejection paths are exercised as a process.
// Both die inside parseArgs, before the script touches git.
test('parseArgs rejects an unknown option with exit 2', () => {
  const r = spawnSync(process.execPath, [SOURCE, '--nope'], { encoding: 'utf8' });
  assert.equal(r.status, 2);
  assert.match(r.stderr, /unknown option '--nope'/);
});

test('parseArgs rejects a valueless --skip with exit 2', () => {
  const r = spawnSync(process.execPath, [SOURCE, '--skip'], { encoding: 'utf8' });
  assert.equal(r.status, 2);
  assert.match(r.stderr, /--skip needs a pattern/);
});

test('buildSkipMatcher always skips node_modules, at any depth', () => {
  const matcher = buildSkipMatcher([]);
  assert.ok(matcher.test('node_modules/dep/index.js'));
  assert.ok(matcher.test('web/node_modules/dep/index.js'));
  assert.ok(matcher.test('node_modules'));
});

test('buildSkipMatcher matches whole segments only', () => {
  const matcher = buildSkipMatcher(['dist']);
  assert.ok(matcher.test('dist/bundle.js'));
  assert.ok(matcher.test('web/dist/bundle.js'));
  assert.ok(!matcher.test('redistribute.js'));
  assert.ok(!matcher.test('src/distance.js'));
});

test('regression: a --skip value is matched literally, not compiled as a pattern', () => {
  // Taken as a regex, `.*` compiles happily, matches every path, and reports a
  // clean tree -- the silent false-clean the tool exists to avoid producing.
  const matcher = buildSkipMatcher(['.*']);
  assert.ok(!matcher.test('src/index.js'));
  assert.ok(!matcher.test('README.md'));
  // It still skips a directory actually named `.*`.
  assert.ok(matcher.test('src/.*/generated.js'));
});

test('prose reads every comment opener the tool covers', () => {
  assert.equal(prose(`// ${COMMENT}`), PROSE);
  assert.equal(prose(`  # ${COMMENT}`), PROSE);
  assert.equal(prose(` * ${COMMENT}`), PROSE);
  assert.equal(prose(`/* ${COMMENT} */`), PROSE);
});

test('prose returns nothing for a line carrying no comment', () => {
  assert.equal(prose('const answer = 42;'), '');
  assert.equal(prose(''), '');
});

test('prose compares on words alone, so punctuation and case do not hide a twin', () => {
  assert.equal(prose(`// ${COMMENT.toUpperCase()}!!!`), PROSE);
  assert.equal(prose(`//   The  retold, fact "rule" -- needs a whole repo view.`), PROSE);
});

test('prose drops a comment whose prose is shorter than the floor', () => {
  assert.equal(prose('// abcdefghij abcdefghij abc'), 'abcdefghij abcdefghij abc');
  assert.equal(prose('// abcdefghij abcdefghij ab'), '');
});

test('prose exempts mandated and machine-read text', () => {
  assert.equal(prose('// SPDX-License-Identifier: MIT, and enough words to clear the floor'), '');
  assert.equal(prose('# noqa: E501 -- and enough further words to clear the length floor'), '');
  assert.equal(prose('// eslint-disable-next-line no-console, plus words to clear the floor'), '');
});

test('regression: a CRLF line still reads as a comment', () => {
  // A CRLF-committed blob leaves a trailing \r that the `(.*)$` patterns reject,
  // because \r is a line terminator to `.` -- silently hiding every // # and *
  // comment in the file.
  assert.equal(prose(`// ${COMMENT}\r`), PROSE);
  assert.equal(prose(`# ${COMMENT}\r`), PROSE);
  assert.equal(prose(` * ${COMMENT}\r`), PROSE);
});

test('trackedPaths lists tracked files minus the skipped trees', () => {
  const dir = makeRepo({
    'a.js': 'const x = 1;\n',
    'node_modules/dep/index.js': 'const y = 2;\n',
    'dist/bundle.js': 'const z = 3;\n',
    'redistribute.js': 'const w = 4;\n'
  });

  inRepo(dir, () => {
    assert.deepEqual(trackedPaths(buildSkipMatcher(['dist'])).sort(), ['a.js', 'redistribute.js']);
  });
});

test('regression: trackedPaths drops a submodule gitlink', () => {
  // A gitlink is a mode-160000 index entry with no blob behind it.
  // `update-index --cacheinfo` creates one without a submodule checkout.
  const dir = makeRepo({ 'a.js': `// ${COMMENT}\n` });
  gitIn(dir, ['update-index', '--add', '--cacheinfo', `160000,${'0'.repeat(39)}1,vendor/sub`]);
  gitIn(dir, ['commit', '-qm', 'gitlink']);

  inRepo(dir, () => {
    const paths = trackedPaths(buildSkipMatcher([]));
    assert.deepEqual(paths, ['a.js']);

    // Why the entry must never reach the batch: what `cat-file --batch` answers
    // for a gitlink is git-version dependent -- `<sha> submodule`, which carries
    // no size field and ends the whole batch, on the versions that emit it. The
    // filter is the contract; the downstream reply is not ours to pin.
    const index = buildCommentIndex(paths);
    assert.ok(index instanceof Map);
    assert.deepEqual(index.get(PROSE), ['a.js:1']);
  });
});

test('buildCommentIndex maps prose to every site carrying it, 1-based', () => {
  const dir = makeRepo({
    'a.js': `const x = 1;\n// ${COMMENT}\n`,
    'docs/b.md': `# heading\n# ${COMMENT}\n`
  });

  inRepo(dir, () => {
    const index = buildCommentIndex(['a.js', 'docs/b.md']);
    assert.deepEqual(index.get(PROSE), ['a.js:2', 'docs/b.md:2']);
    // `# heading` normalizes below the floor, so it is not indexed at all.
    assert.equal(index.get('heading'), undefined);
  });
});

test('regression: a CRLF-committed blob has its comments indexed', () => {
  const dir = makeRepo({ 'crlf.js': `const x = 1;\r\n// ${COMMENT}\r\n` });

  inRepo(dir, () => {
    assert.deepEqual(buildCommentIndex(['crlf.js']).get(PROSE), ['crlf.js:2']);
  });
});

test('buildCommentIndex skips a file that is missing at HEAD', () => {
  const dir = makeRepo({ 'a.js': `// ${COMMENT}\n` });
  fs.writeFileSync(path.join(dir, 'new.js'), `// ${COMMENT}\n`);

  inRepo(dir, () => {
    // Newly added, so `HEAD:new.js` does not resolve -- normal, and nothing to
    // index either way. It must not take the batch down with it.
    const index = buildCommentIndex(['a.js', 'new.js']);
    assert.deepEqual(index.get(PROSE), ['a.js:1']);
  });
});

test('buildCommentIndex short-circuits an empty file list', () => {
  // No git call at all, so this needs no fixture.
  assert.equal(buildCommentIndex([]).size, 0);
});

test('findRetoldInDiff numbers added lines against the new file', () => {
  const index = new Map([[PROSE, ['other/file.js:7']]]);
  const diff = [
    '@@ -1,2 +1,3 @@',
    ' const first = 1;',
    ' const second = 2;',
    `+// ${COMMENT}`,
    ''
  ].join('\n');

  assert.deepEqual(findRetoldInDiff(diff, 'sample.js', index), [
    { here: 'sample.js:3', text: PROSE, elsewhere: ['other/file.js:7'] }
  ]);
});

test('findRetoldInDiff ignores a removed line and reports nothing told only here', () => {
  const index = new Map([[PROSE, ['sample.js:1']]]);
  const diff = [
    '@@ -1,2 +1,2 @@',
    `-// ${COMMENT}`,
    `+// ${COMMENT}`,
    ''
  ].join('\n');

  // The one recorded site IS this line, so there is nothing told elsewhere.
  assert.deepEqual(findRetoldInDiff(diff, 'sample.js', index), []);
});

test('regression: the no-newline marker does not advance the line counter', () => {
  // `\ No newline at end of file` annotates the previous line rather than being
  // one, so counting it shifts every later line number by one -- a finding that
  // points a reviewer at the wrong line.
  const index = new Map([[PROSE, ['other/file.js:7']]]);
  const diff = [
    '@@ -1,3 +1,3 @@',
    ' const shared = 0;',
    '-const removed = 1;',
    '\\ No newline at end of file',
    '+const added = 1;',
    `+// ${COMMENT}`,
    ''
  ].join('\n');

  const findings = findRetoldInDiff(diff, 'sample.js', index);
  assert.equal(findings.length, 1);
  assert.equal(findings[0].here, 'sample.js:3');
});

test('findRetoldInDiff restarts the counter at each hunk header', () => {
  const index = new Map([[PROSE, ['other/file.js:7']]]);
  const diff = [
    '@@ -1,1 +1,2 @@',
    ' const first = 1;',
    `+// ${COMMENT}`,
    '@@ -40,1 +41,2 @@',
    ' const later = 2;',
    `+// ${COMMENT}`,
    ''
  ].join('\n');

  assert.deepEqual(
    findRetoldInDiff(diff, 'sample.js', index).map(f => f.here),
    ['sample.js:2', 'sample.js:42']
  );
});

test('dedupePairs collapses the mirror image of a pair added on both sides', () => {
  const findings = [
    { here: 'a.js:1', text: PROSE, elsewhere: ['b.js:2'] },
    { here: 'b.js:2', text: PROSE, elsewhere: ['a.js:1'] }
  ];

  assert.deepEqual(dedupePairs(findings), [findings[0]]);
});

test('dedupePairs keeps distinct pairs', () => {
  const findings = [
    { here: 'a.js:1', text: PROSE, elsewhere: ['b.js:2'] },
    { here: 'c.js:3', text: 'a different retelling of some other fact entirely', elsewhere: ['d.js:4'] }
  ];

  assert.deepEqual(dedupePairs(findings), findings);
});
