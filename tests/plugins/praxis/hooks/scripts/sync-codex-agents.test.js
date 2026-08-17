// Process contract for the Codex role installer.
//
// Spawned rather than imported, and not because spawning is tidier: hooks.json
// invokes this script as `require(root + '/hooks/scripts/sync-codex-agents.js')`
// and it does its work at require time, so the `require.main === module` guard
// that would make it importable would turn the hook into a no-op.
//
// Every plugin that ships a copy is covered from here, in one file rather than
// one per plugin: the copies must be byte-identical, which `make verify` asserts
// through generate-codex.py's divergence finder, so a second file would only
// duplicate this one. PLUGIN_ROOT and CODEX_HOME point at temporary directories
// throughout -- the script writes into the user's real Codex config otherwise.

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const PLUGINS = path.resolve(__dirname, '../../../../../plugins');
const RELATIVE = path.join('hooks', 'scripts', 'sync-codex-agents.js');

/** Every plugin shipping this hook, discovered so a new copy is covered too. */
const COPIES = fs
  .readdirSync(PLUGINS, { withFileTypes: true })
  .filter(entry => entry.isDirectory())
  .map(entry => ({ plugin: entry.name, script: path.join(PLUGINS, entry.name, RELATIVE) }))
  .filter(copy => fs.existsSync(copy.script));

test('the hook is shipped by at least one plugin', () => {
  // Discovery that matched nothing would leave every contract below vacuous.
  assert.ok(COPIES.length > 0, `no sync-codex-agents.js found under ${PLUGINS}`);
});

/** Spawn one copy, asserting exit 0 and stdout empty or exactly one JSON object. */
function spawnHook(script, { stdin = '', env = {} } = {}) {
  const r = spawnSync(process.execPath, [script], {
    input: stdin,
    encoding: 'utf8',
    env: { ...process.env, ...env }
  });

  assert.equal(r.status, 0, `exited ${r.status}, signal ${r.signal}; stderr: ${r.stderr}`);
  const out = r.stdout.trim();
  if (out === '') return null;

  const payload = JSON.parse(out);
  assert.equal(typeof payload, 'object');
  assert.notEqual(payload, null);
  return payload;
}

/** A fake plugin root holding `roles`, plus an empty Codex home. */
function withDirs(roles, fn) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'grimoire-codex-'));
  const pluginRoot = path.join(dir, 'someplugin');
  const codexHome = path.join(dir, 'codex-home');
  fs.mkdirSync(codexHome);

  if (roles) {
    const agents = path.join(pluginRoot, 'codex', 'agents');
    fs.mkdirSync(agents, { recursive: true });
    for (const [name, contents] of Object.entries(roles)) {
      fs.writeFileSync(path.join(agents, name), contents);
    }
  } else {
    fs.mkdirSync(pluginRoot);
  }

  try {
    return fn({
      env: { PLUGIN_ROOT: pluginRoot, CODEX_HOME: codexHome },
      codexHome,
      installed: path.join(codexHome, 'agents', 'grimoire', 'someplugin')
    });
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

for (const { plugin, script } of COPIES) {
  test(`${plugin}: contract with PLUGIN_ROOT unset -- a clean no-op`, () => {
    // Claude Code sets only the prefixed name, so this is every non-Codex session.
    const env = { PLUGIN_ROOT: undefined };
    const r = spawnSync(process.execPath, [script], {
      input: '',
      encoding: 'utf8',
      env: Object.fromEntries(Object.entries({ ...process.env, ...env }).filter(([, v]) => v !== undefined))
    });
    assert.equal(r.status, 0, `exited ${r.status}; stderr: ${r.stderr}`);
    assert.equal(r.stdout.trim(), '');
  });

  test(`${plugin}: contract with malformed JSON on stdin`, () => {
    withDirs({ 'reviewer.toml': 'name = "reviewer"\n' }, ({ env }) => {
      assert.equal(spawnHook(script, { stdin: '{"hook_event_name": ', env }), null);
    });
  });

  test(`${plugin}: contract with empty stdin`, () => {
    withDirs({ 'reviewer.toml': 'name = "reviewer"\n' }, ({ env }) => {
      assert.equal(spawnHook(script, { stdin: '', env }), null);
    });
  });

  test(`${plugin}: contract with a payload carrying no transcript_path`, () => {
    withDirs({ 'reviewer.toml': 'name = "reviewer"\n' }, ({ env }) => {
      assert.equal(spawnHook(script, { stdin: JSON.stringify({ hook_event_name: 'SessionStart' }), env }), null);
    });
  });

  test(`${plugin}: contract with no roles to install`, () => {
    withDirs(null, ({ env }) => {
      assert.equal(spawnHook(script, { env }), null);
    });
  });

  test(`${plugin}: installs the roles it ships under its own namespace`, () => {
    withDirs({ 'reviewer.toml': 'name = "reviewer"\n' }, ({ env, installed }) => {
      spawnHook(script, { env });
      assert.equal(fs.readFileSync(path.join(installed, 'reviewer.toml'), 'utf8'), 'name = "reviewer"\n');
    });
  });

  test(`${plugin}: removes a role it no longer ships and leaves other files alone`, () => {
    withDirs({ 'reviewer.toml': 'name = "reviewer"\n' }, ({ env, installed }) => {
      fs.mkdirSync(installed, { recursive: true });
      fs.writeFileSync(path.join(installed, 'dropped.toml'), 'name = "dropped"\n');
      fs.writeFileSync(path.join(installed, 'notes.md'), 'not a role\n');

      spawnHook(script, { env });

      assert.equal(fs.existsSync(path.join(installed, 'dropped.toml')), false);
      assert.equal(fs.existsSync(path.join(installed, 'notes.md')), true);
      assert.equal(fs.existsSync(path.join(installed, 'reviewer.toml')), true);
    });
  });

  test(`${plugin}: leaves an unchanged role's mtime alone`, () => {
    // Writing only on difference keeps mtimes stable across the many sessions
    // that change nothing.
    withDirs({ 'reviewer.toml': 'name = "reviewer"\n' }, ({ env, installed }) => {
      spawnHook(script, { env });
      const target = path.join(installed, 'reviewer.toml');
      const first = fs.statSync(target).mtimeMs;

      spawnHook(script, { env });
      assert.equal(fs.statSync(target).mtimeMs, first);
    });
  });

  test(`${plugin}: installs under the owned namespace even when PLUGIN_ROOT ends in ..`, () => {
    // Resolving before taking the basename is what keeps the sweep inside a
    // directory this plugin owns. Unresolved, the basename is ".." and the
    // target collapses to the shared agents directory, putting roles this
    // plugin does not own within reach of the sweep.
    //
    // Built by concatenation, not path.join: join normalizes the `..` away,
    // which would make this test pass against the bug it exists to catch.
    withDirs({ 'reviewer.toml': 'name = "reviewer"\n' }, ({ env, installed, codexHome }) => {
      const trailing = { ...env, PLUGIN_ROOT: `${env.PLUGIN_ROOT}/codex/..` };
      assert.equal(spawnHook(script, { env: trailing }), null);
      assert.equal(fs.existsSync(path.join(installed, 'reviewer.toml')), true);
      assert.equal(fs.existsSync(path.join(codexHome, 'agents', 'reviewer.toml')), false);
    });
  });
}
