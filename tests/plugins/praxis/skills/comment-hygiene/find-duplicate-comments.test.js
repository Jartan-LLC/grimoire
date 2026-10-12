const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const path = require('node:path');
const { describe, test } = require('node:test');

const {
  REPO_ROOT,
  commitAll,
  git,
  gitEnv,
  initRepo,
  isolateGit,
  tempDir,
  writeFiles,
} = require('../../../../helpers/fixture');

const SCRIPT = path.join(REPO_ROOT, 'plugins/praxis/skills/comment-hygiene/find-duplicate-comments.js');
const {
  parseArgs,
  buildSkipMatcher,
  prose,
  buildCommentIndex,
  findRetoldInDiff,
  dedupePairs,
} = require(SCRIPT);

isolateGit();

const RETOLD = 'the cache is rebuilt whenever the schema version changes';

function runCli(cwd, ...args) {
  return spawnSync(process.execPath, [SCRIPT, ...args], { cwd, encoding: 'utf8', env: gitEnv() });
}

/** Run `fn` with the process inside `dir`, as the CLI would be. */
function inDir(dir, fn) {
  const previous = process.cwd();
  process.chdir(dir);
  try {
    return fn();
  } finally {
    process.chdir(previous);
  }
}

describe('parseArgs', () => {
  test('defaults the base to origin/main with no skips', () => {
    assert.deepEqual(parseArgs([]), { base: 'origin/main', skips: [] });
  });

  test('takes one base and collects both --skip spellings in order', () => {
    assert.deepEqual(parseArgs(['--skip', 'dist', 'main', '--skip=build']), {
      base: 'main',
      skips: ['dist', 'build'],
    });
  });

  test('keeps a skip value verbatim, metacharacters included', () => {
    assert.deepEqual(parseArgs(['--skip', '.*']).skips, ['.*']);
  });

  for (const [args, message] of [
    [['--skip'], '--skip needs a pattern'],
    [['--frobnicate'], "unknown option '--frobnicate'"],
    [['main', 'extra'], "unexpected argument 'extra'"],
  ]) {
    test(`rejects ${JSON.stringify(args)} with exit 2`, t => {
      const result = runCli(tempDir(t), ...args);
      assert.equal(result.status, 2);
      assert.match(result.stderr, new RegExp(message.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
      assert.equal(result.stdout, '');
    });
  }
});

describe('buildSkipMatcher', () => {
  test('matches a skip as a whole path segment at any depth', () => {
    const skip = buildSkipMatcher(['dist']);
    for (const p of ['dist/a.js', 'src/dist/a.js', 'src/dist']) assert.ok(skip.test(p), p);
    for (const p of ['redistribute.js', 'distro/a.js', 'src/mydist/a.js', 'src/dist.js']) {
      assert.ok(!skip.test(p), p);
    }
  });

  test('always skips node_modules', () => {
    const skip = buildSkipMatcher([]);
    assert.ok(skip.test('web/node_modules/pkg/index.js'));
    assert.ok(!skip.test('web/src/index.js'));
  });

  test('takes metacharacters literally, so --skip .* does not skip every path', () => {
    const skip = buildSkipMatcher(['.*', 'a+b']);
    for (const p of ['src/app.js', 'aab/x.js', 'README.md']) assert.ok(!skip.test(p), p);
    assert.ok(skip.test('.*/x.js'));
    assert.ok(skip.test('lib/a+b/x.js'));
  });
});

describe('prose', () => {
  test('reduces every comment style to the same words', () => {
    const expected = 'the cache is rebuilt whenever the schema version changes';
    for (const line of [
      '// The cache is rebuilt whenever the schema version changes.',
      '    # the cache IS rebuilt -- whenever the schema version changes!',
      ' * The cache is rebuilt, whenever the schema-version changes',
      '/* The cache is rebuilt whenever the schema version changes */',
      '/** The cache is rebuilt whenever the schema version changes. */',
    ]) {
      assert.equal(prose(line), expected, line);
    }
  });

  test('reads a CRLF line the same as an LF one', () => {
    assert.equal(prose(`// ${RETOLD}\r`), RETOLD);
  });

  test('ignores code, short comments and mandated text', () => {
    for (const line of [
      'const cache = rebuild(schemaVersion); // trailing comments are not indexed',
      '// too short to matter',
      '//',
      '# SPDX-License-Identifier: MIT and some more words here',
      '// eslint-disable-next-line no-console because it is needed',
      '# shellcheck disable=SC2016 because the dollar is literal here',
    ]) {
      assert.equal(prose(line), '', line);
    }
  });
});

describe('findRetoldInDiff', () => {
  const index = new Map([[RETOLD, ['other.js:3']]]);

  test('numbers added lines from the hunk header, past context and deletions', () => {
    const diff = [
      'diff --git a/f.js b/f.js',
      '--- a/f.js',
      '+++ b/f.js',
      '@@ -10,4 +20,5 @@ function f() {',
      ' context line',
      `-// ${RETOLD}`,
      '+const added = 1;',
      `+// ${RETOLD}`,
      ' more context',
    ].join('\n');
    assert.deepEqual(findRetoldInDiff(diff, 'f.js', index), [
      { here: 'f.js:22', text: RETOLD, elsewhere: ['other.js:3'] },
    ]);
  });

  test('restarts numbering at each hunk', () => {
    const diff = ['@@ -1 +1 @@', '+x', '@@ -50,2 +60,3 @@', ' y', `+# ${RETOLD}`].join('\n');
    assert.deepEqual(
      findRetoldInDiff(diff, 'f.py', index).map(f => f.here),
      ['f.py:61'],
    );
  });

  test('does not count a "No newline at end of file" marker as a line', () => {
    const diff = [
      '@@ -1,2 +1,3 @@',
      '-old last line',
      '\\ No newline at end of file',
      '+new line',
      `+// ${RETOLD}`,
    ].join('\n');
    assert.deepEqual(
      findRetoldInDiff(diff, 'f.js', index).map(f => f.here),
      ['f.js:2'],
    );
  });

  test('does not report a line as retelling itself', () => {
    const self = new Map([[RETOLD, ['f.js:1']]]);
    assert.deepEqual(findRetoldInDiff(`@@ -0,0 +1 @@\n+// ${RETOLD}`, 'f.js', self), []);
  });

  test('lists every other site, without the line itself', () => {
    const both = new Map([[RETOLD, ['a.js:4', 'f.js:1', 'b.js:9']]]);
    assert.deepEqual(findRetoldInDiff(`@@ -0,0 +1 @@\n+// ${RETOLD}`, 'f.js', both), [
      { here: 'f.js:1', text: RETOLD, elsewhere: ['a.js:4', 'b.js:9'] },
    ]);
  });
});

describe('dedupePairs', () => {
  test('keeps one side of a retelling whose sides were both added', () => {
    const findings = [
      { here: 'a.js:1', text: RETOLD, elsewhere: ['b.js:2'] },
      { here: 'b.js:2', text: RETOLD, elsewhere: ['a.js:1'] },
    ];
    assert.deepEqual(dedupePairs(findings), [findings[0]]);
  });

  test('keeps findings that are not mirror images', () => {
    const findings = [
      { here: 'a.js:1', text: RETOLD, elsewhere: ['b.js:2'] },
      { here: 'a.js:5', text: RETOLD, elsewhere: ['b.js:2'] },
      { here: 'c.js:1', text: 'another comment that is long enough', elsewhere: ['d.js:1'] },
    ];
    assert.deepEqual(dedupePairs(findings), findings);
  });
});

describe('buildCommentIndex', () => {
  test('maps prose to every file:line site at HEAD', t => {
    const dir = initRepo(t, {
      'a.js': `const a = 1;\n// ${RETOLD}\n`,
      'lib/b.py': `# ${RETOLD}\n`,
    });
    const index = inDir(dir, () => buildCommentIndex(['a.js', 'lib/b.py']));
    assert.deepEqual(index.get(RETOLD), ['a.js:2', 'lib/b.py:1']);
  });

  test('keeps blob boundaries after multi-byte content', t => {
    const dir = initRepo(t, {
      'first.md': '# \u00fcber \u2014 na\u00efve \u2014 a comment long enough to index\n',
      'second.js': `x();\n// ${RETOLD}\n`,
    });
    const index = inDir(dir, () => buildCommentIndex(['first.md', 'second.js']));
    assert.deepEqual(index.get(RETOLD), ['second.js:2']);
    assert.deepEqual(index.get('ber na ve a comment long enough to index'), ['first.md:1']);
  });

  test('indexes a CRLF-committed blob', t => {
    const dir = initRepo(t, { 'win.js': `x();\r\n// ${RETOLD}\r\n` });
    const index = inDir(dir, () => buildCommentIndex(['win.js']));
    assert.deepEqual(index.get(RETOLD), ['win.js:2']);
  });

  test('skips a path missing at HEAD and still indexes the rest', t => {
    const dir = initRepo(t, { 'a.js': `// ${RETOLD}\n` });
    const index = inDir(dir, () => buildCommentIndex(['not-committed.js', 'a.js']));
    assert.deepEqual(index.get(RETOLD), ['a.js:1']);
  });
});

describe('command line', () => {
  /** A repository whose `feature` branch adds `added` on top of `base`, both on `main`. */
  function branchRepo(t, base, added) {
    const dir = initRepo(t, base);
    git(dir, 'checkout', '-q', '-b', 'feature');
    writeFiles(dir, added);
    commitAll(dir, 'feature');
    return dir;
  }

  test('reports an added comment already told elsewhere, naming both sites', t => {
    const dir = branchRepo(t, { 'old.js': `x();\n// ${RETOLD}\n` }, { 'new.js': `// ${RETOLD}\n` });
    const result = runCli(dir, 'main');
    assert.equal(result.status, 0, result.stderr);
    assert.match(result.stdout, /1 added comment line\(s\) already told elsewhere/);
    assert.match(result.stdout, /new\.js:1\n/);
    assert.match(result.stdout, /also at: old\.js:2\n/);
  });

  test('--skip .* is a literal segment, not a pattern that hides every finding', t => {
    const dir = branchRepo(t, { 'old.js': `// ${RETOLD}\n` }, { 'new.js': `// ${RETOLD}\n` });
    const result = runCli(dir, 'main', '--skip', '.*');
    assert.equal(result.status, 0, result.stderr);
    assert.match(result.stdout, /also at: old\.js:1\n/);
  });

  test('a skipped tree is neither reported nor indexed', t => {
    const dir = branchRepo(
      t,
      { 'dist/old.js': `// ${RETOLD}\n` },
      { 'new.js': `// ${RETOLD}\n`, 'dist/new.js': `// ${RETOLD}\n` },
    );
    const result = runCli(dir, 'main', '--skip', 'dist');
    assert.equal(result.status, 0, result.stderr);
    assert.match(result.stdout, /No retold comments found in the diff\./);
  });

  test('a submodule gitlink in the tree does not abort the run', t => {
    const dir = initRepo(t, { 'old.js': `// ${RETOLD}\n` });
    // A commit absent from this repository, as a real submodule's usually is.
    const absent = '1234567890abcdef1234567890abcdef12345678';
    git(dir, 'update-index', '--add', '--cacheinfo', `160000,${absent},vendor/sub`);
    // Staged by path from here on: `add -A` would drop the gitlink, which has no checkout.
    git(dir, 'commit', '-q', '-m', 'add submodule');
    git(dir, 'checkout', '-q', '-b', 'feature');
    writeFiles(dir, { 'new.js': `// ${RETOLD}\n` });
    git(dir, 'add', 'new.js');
    git(dir, 'commit', '-q', '-m', 'feature');
    assert.match(git(dir, 'ls-files', '-s'), /^160000 .*\tvendor\/sub$/m);
    const result = runCli(dir, 'main');
    assert.equal(result.status, 0, result.stderr);
    assert.match(result.stdout, /also at: old\.js:1\n/);
  });

  test('a path with spaces and non-ASCII characters is read, not missed', t => {
    const odd = 'docs dir/\u00fcber notes.py';
    const dir = branchRepo(t, { [odd]: `# ${RETOLD}\n` }, { 'new.js': `// ${RETOLD}\n` });
    const result = runCli(dir, 'main');
    assert.equal(result.status, 0, result.stderr);
    assert.ok(result.stdout.includes(`also at: ${odd}:1\n`), result.stdout);
  });

  test('a base ref that does not resolve fails rather than reporting clean', t => {
    const dir = initRepo(t, { 'a.js': 'x();\n' });
    const result = runCli(dir, 'no-such-ref');
    assert.equal(result.status, 2);
    assert.match(result.stderr, /base ref 'no-such-ref' does not resolve/);
    assert.equal(result.stdout, '');
  });
});
