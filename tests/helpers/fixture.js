// Temporary directories and git fixture repositories for the Node tests.

const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const REPO_ROOT = path.resolve(__dirname, '..', '..');

/**
 * The environment a fixture's git runs under. Every inherited GIT_* variable
 * goes: a GIT_DIR or GIT_INDEX_FILE left by a git hook would point the fixture's
 * commands at this checkout. User and system config go too, so a contributor's
 * settings (autocrlf, hooks, signing) cannot change what a fixture holds.
 */
function gitEnv(base = process.env) {
  const env = Object.fromEntries(Object.entries(base).filter(([key]) => !key.startsWith('GIT_')));
  return {
    ...env,
    GIT_CONFIG_NOSYSTEM: '1',
    GIT_CONFIG_GLOBAL: os.devNull,
    GIT_AUTHOR_NAME: 'Fixture',
    GIT_AUTHOR_EMAIL: 'fixture@example.com',
    GIT_COMMITTER_NAME: 'Fixture',
    GIT_COMMITTER_EMAIL: 'fixture@example.com',
  };
}

/** Point this process's own git spawns at gitEnv(), for code under test that inherits it. */
function isolateGit() {
  const isolated = gitEnv();
  for (const key of Object.keys(process.env)) {
    if (!(key in isolated)) delete process.env[key];
  }
  Object.assign(process.env, isolated);
}

/** A fresh temporary directory, removed when test `t` finishes. */
function tempDir(t) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'grimoire-test-'));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  return dir;
}

function git(dir, ...args) {
  const result = spawnSync('git', args, { cwd: dir, encoding: 'utf8', env: gitEnv() });
  assert.equal(result.status, 0, `git ${args.join(' ')} failed: ${result.stderr}`);
  return result.stdout;
}

/** Write `files` ({relative path: contents}) under `dir`, creating parent directories. */
function writeFiles(dir, files) {
  for (const [relative, contents] of Object.entries(files)) {
    const target = path.join(dir, relative);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.writeFileSync(target, contents);
  }
}

/** A new repository on branch `main` in a temporary directory, with `files` committed. */
function initRepo(t, files = {}) {
  const dir = tempDir(t);
  git(dir, 'init', '-q', '-b', 'main');
  writeFiles(dir, files);
  commitAll(dir, 'base');
  return dir;
}

function commitAll(dir, message) {
  git(dir, 'add', '-A');
  git(dir, 'commit', '-q', '--allow-empty', '-m', message);
}

module.exports = { REPO_ROOT, gitEnv, isolateGit, tempDir, git, writeFiles, initRepo, commitAll };
