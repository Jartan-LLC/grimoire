// Tests for the shared hook helpers that do real work on their arguments: the
// pattern filter, the two regex-flag guards, and the glob-to-regex conversion.
//
// The thin wrappers over fs and child_process in the same module are deliberately
// untested -- the assertion would be that Node works. CONTRIBUTING.md has the
// full list and why.

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const {
  filterByPatterns,
  findFiles,
  countInFile,
  grepFile
} = require('../../../../../../plugins/praxis/hooks/scripts/lib/utils');

const FILES = ['src/app.ts', 'src/app.tsx', 'src/app.js', 'docs/readme.md'];

function withTempDir(fn) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'grimoire-utils-'));
  try {
    return fn(dir);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

function write(dir, relative, contents = 'x\n', ageMs = 0) {
  const file = path.join(dir, relative);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, contents);
  if (ageMs > 0) {
    const when = (Date.now() - ageMs) / 1000;
    fs.utimesSync(file, when, when);
  }
  return file;
}

const missing = () => path.join(os.tmpdir(), 'grimoire-utils-absent-55123.txt');

test('filterByPatterns leaves the list alone when there are no patterns', () => {
  assert.deepEqual(filterByPatterns(FILES, []), FILES);
});

test('filterByPatterns keeps only what a pattern matches', () => {
  assert.deepEqual(filterByPatterns(FILES, ['\\.tsx?$']), ['src/app.ts', 'src/app.tsx']);
});

test('filterByPatterns unions its patterns', () => {
  assert.deepEqual(filterByPatterns(FILES, ['\\.tsx?$', '\\.jsx?$']), ['src/app.ts', 'src/app.tsx', 'src/app.js']);
});

test('filterByPatterns skips an invalid pattern and applies the rest', () => {
  assert.deepEqual(filterByPatterns(FILES, ['[unclosed', '\\.md$']), ['docs/readme.md']);
});

test('filterByPatterns leaves the list alone when every pattern is unusable', () => {
  // Compiling nothing must not mean matching nothing: an all-invalid list that
  // filtered everything away would report a clean tree to every caller.
  assert.deepEqual(filterByPatterns(FILES, ['[unclosed', '(']), FILES);
  assert.deepEqual(filterByPatterns(FILES, ['', null, undefined, 42]), FILES);
});

test('filterByPatterns matches anywhere in the path, not just the end', () => {
  assert.deepEqual(filterByPatterns(FILES, ['^src/']), ['src/app.ts', 'src/app.tsx', 'src/app.js']);
  assert.deepEqual(filterByPatterns(FILES, ['app']), ['src/app.ts', 'src/app.tsx', 'src/app.js']);
});

test('countInFile counts every match of a string pattern', () => {
  withTempDir(dir => {
    const file = write(dir, 'a.js', 'console.log(1)\nconsole.log(2)\nconsole.log(3)\n');
    assert.equal(countInFile(file, 'console\\.log'), 3);
  });
});

test('countInFile counts every match of a RegExp that lacks the global flag', () => {
  // Without the flag enforced, String.match returns the first match only and the
  // count silently reads 1 however many there are.
  withTempDir(dir => {
    const file = write(dir, 'a.js', 'console.log(1)\nconsole.log(2)\nconsole.log(3)\n');
    assert.equal(countInFile(file, /console\.log/), 3);
  });
});

test('countInFile preserves the other flags on the pattern it is handed', () => {
  withTempDir(dir => {
    const file = write(dir, 'a.js', 'CONSOLE.LOG(1)\nconsole.log(2)\n');
    assert.equal(countInFile(file, /console\.log/i), 2);
    assert.equal(countInFile(file, /console\.log/), 1);
  });
});

test('countInFile is not disturbed by a global RegExp reused across calls', () => {
  withTempDir(dir => {
    const file = write(dir, 'a.js', 'console.log(1)\nconsole.log(2)\n');
    const shared = /console\.log/g;
    assert.equal(countInFile(file, shared), 2);
    assert.equal(countInFile(file, shared), 2);
  });
});

test('countInFile returns zero for a missing file, a bad pattern or a bad type', () => {
  assert.equal(countInFile(missing(), 'x'), 0);
  withTempDir(dir => {
    const file = write(dir, 'a.js', 'x\n');
    assert.equal(countInFile(file, '[unclosed'), 0);
    assert.equal(countInFile(file, 42), 0);
    assert.equal(countInFile(file, null), 0);
  });
});

test('grepFile reports matching lines with 1-based numbers', () => {
  withTempDir(dir => {
    const file = write(dir, 'a.js', 'const x = 1;\nconsole.log(x);\nconst y = 2;\n');
    assert.deepEqual(grepFile(file, /console\.log/), [{ lineNumber: 2, content: 'console.log(x);' }]);
  });
});

test('grepFile matches consecutive lines despite a global RegExp', () => {
  // The g flag makes .test() stateful: lastIndex carries between calls, so
  // consecutive matching lines alternate match/miss and half the findings vanish.
  withTempDir(dir => {
    const file = write(dir, 'a.js', 'console.log(1)\nconsole.log(2)\nconsole.log(3)\nconsole.log(4)\n');
    assert.deepEqual(grepFile(file, /console\.log/g).map(m => m.lineNumber), [1, 2, 3, 4]);
  });
});

test('grepFile gives the same answer when a global RegExp is reused', () => {
  withTempDir(dir => {
    const file = write(dir, 'a.js', 'console.log(1)\nconsole.log(2)\n');
    const shared = /console\.log/g;
    assert.deepEqual(grepFile(file, shared), grepFile(file, shared));
  });
});

test('grepFile keeps the flags that are not g', () => {
  withTempDir(dir => {
    const file = write(dir, 'a.js', 'CONSOLE.LOG(1)\nconst x = 2;\n');
    assert.deepEqual(grepFile(file, /console\.log/i).map(m => m.lineNumber), [1]);
    assert.deepEqual(grepFile(file, /console\.log/), []);
  });
});

test('grepFile accepts a string pattern', () => {
  withTempDir(dir => {
    const file = write(dir, 'a.js', 'const x = 1;\nconsole.log(x);\n');
    assert.deepEqual(grepFile(file, 'console\\.log').map(m => m.lineNumber), [2]);
  });
});

test('grepFile returns nothing for a missing file or a bad pattern', () => {
  assert.deepEqual(grepFile(missing(), /x/), []);
  withTempDir(dir => {
    assert.deepEqual(grepFile(write(dir, 'a.js', 'x\n'), '[unclosed'), []);
  });
});

test('findFiles converts the glob wildcards', () => {
  withTempDir(dir => {
    write(dir, 'a.tmp');
    write(dir, 'b.tmp');
    write(dir, 'c.md');
    assert.deepEqual(findFiles(dir, '*.tmp').map(f => path.basename(f.path)).sort(), ['a.tmp', 'b.tmp']);

    write(dir, 'log1.txt');
    write(dir, 'log22.txt');
    assert.deepEqual(findFiles(dir, 'log?.txt').map(f => path.basename(f.path)), ['log1.txt']);
  });
});

test('findFiles escapes the regex specials in a pattern', () => {
  // Unescaped, the dot in `a.txt` is a wildcard and the pattern also matches
  // `axtxt` -- a file the caller never asked for, deleted by a caller that
  // sweeps what this returns.
  withTempDir(dir => {
    write(dir, 'a.txt');
    write(dir, 'axtxt');
    write(dir, 'a+b.txt');
    assert.deepEqual(findFiles(dir, 'a.txt').map(f => path.basename(f.path)), ['a.txt']);
    assert.deepEqual(findFiles(dir, 'a+b.txt').map(f => path.basename(f.path)), ['a+b.txt']);
  });
});

test('findFiles anchors the pattern to the whole name', () => {
  withTempDir(dir => {
    write(dir, 'notes.md');
    write(dir, 'notes.md.bak');
    assert.deepEqual(findFiles(dir, '*.md').map(f => path.basename(f.path)), ['notes.md']);
  });
});

test('findFiles descends only when asked to', () => {
  withTempDir(dir => {
    write(dir, 'top.md');
    write(dir, 'nested/deep.md');
    assert.deepEqual(findFiles(dir, '*.md').map(f => path.basename(f.path)), ['top.md']);
    assert.deepEqual(
      findFiles(dir, '*.md', { recursive: true }).map(f => path.basename(f.path)).sort(),
      ['deep.md', 'top.md']
    );
  });
});

test('findFiles drops anything older than maxAge', () => {
  withTempDir(dir => {
    const day = 24 * 60 * 60 * 1000;
    write(dir, 'fresh.md', 'x\n');
    write(dir, 'stale.md', 'x\n', 10 * day);
    assert.deepEqual(findFiles(dir, '*.md', { maxAge: 5 }).map(f => path.basename(f.path)), ['fresh.md']);
    assert.equal(findFiles(dir, '*.md', { maxAge: 30 }).length, 2);
  });
});

test('findFiles sorts newest first', () => {
  withTempDir(dir => {
    const hour = 60 * 60 * 1000;
    write(dir, 'oldest.md', 'x\n', 3 * hour);
    write(dir, 'newest.md', 'x\n');
    write(dir, 'middle.md', 'x\n', hour);
    assert.deepEqual(
      findFiles(dir, '*.md').map(f => path.basename(f.path)),
      ['newest.md', 'middle.md', 'oldest.md']
    );
  });
});

test('findFiles returns nothing for a missing directory or a bad argument', () => {
  assert.deepEqual(findFiles(path.join(os.tmpdir(), 'grimoire-utils-nodir-8812'), '*.md'), []);
  withTempDir(dir => {
    assert.deepEqual(findFiles(dir, ''), []);
    assert.deepEqual(findFiles(dir, null), []);
    assert.deepEqual(findFiles(null, '*.md'), []);
    assert.deepEqual(findFiles(42, '*.md'), []);
  });
});
