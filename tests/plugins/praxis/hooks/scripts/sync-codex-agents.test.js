// The script does its work at require time -- that is how hooks.json invokes
// it -- so every test runs it as a process rather than importing it.

const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const { describe, test } = require('node:test');

const { REPO_ROOT, tempDir, writeFiles } = require('../../../../helpers/fixture');

const SCRIPT = path.join(REPO_ROOT, 'plugins/praxis/hooks/scripts/sync-codex-agents.js');

/**
 * Install plugin `name` at `version` the way Codex lays out its cache, holding
 * `roles` ({file name: contents}) in codex/agents. Returns its plugin root.
 */
function install(dir, name, version, roles) {
  const pluginRoot = path.join(dir, 'plugins', 'cache', 'grimoire', name, version);
  writeFiles(pluginRoot, { '.codex-plugin/plugin.json': JSON.stringify({ name, version }) });
  fs.mkdirSync(path.join(pluginRoot, 'codex', 'agents'), { recursive: true });
  writeFiles(path.join(pluginRoot, 'codex', 'agents'), roles);
  return pluginRoot;
}

/** Plugin "demo" installed with `roles`, plus a Codex home. */
function setup(t, roles) {
  const dir = tempDir(t);
  const pluginRoot = install(dir, 'demo', '1.0.0', roles);
  const codexHome = path.join(dir, 'codex-home');
  return { dir, pluginRoot, codexHome, target: path.join(codexHome, 'agents', 'grimoire', 'demo') };
}

function sync(env) {
  const result = spawnSync(process.execPath, [SCRIPT], {
    encoding: 'utf8',
    input: '{not json',
    env: { PATH: process.env.PATH, ...env },
  });
  assert.equal(result.status, 0, result.stderr);
  assert.equal(result.stdout, '');
  return result;
}

const listing = dir => fs.readdirSync(dir).sort();

describe('sync-codex-agents', () => {
  test("installs the plugin's .toml roles under agents/grimoire/<plugin>", t => {
    const { pluginRoot, codexHome, target } = setup(t, { 'a.toml': 'name = "a"\n', 'b.toml': 'B', 'notes.md': 'x' });
    sync({ PLUGIN_ROOT: pluginRoot, CODEX_HOME: codexHome, HOME: codexHome });
    assert.deepEqual(listing(target), ['a.toml', 'b.toml']);
    assert.equal(fs.readFileSync(path.join(target, 'a.toml'), 'utf8'), 'name = "a"\n');
  });

  test("a new version replaces the previous version's roles in the same directory", t => {
    const { dir, pluginRoot, codexHome, target } = setup(t, { 'kept.toml': 'old', 'dropped.toml': 'D' });
    sync({ PLUGIN_ROOT: pluginRoot, CODEX_HOME: codexHome, HOME: codexHome });

    const updated = install(dir, 'demo', '2.0.0', { 'kept.toml': 'new' });
    sync({ PLUGIN_ROOT: updated, CODEX_HOME: codexHome, HOME: codexHome });
    assert.deepEqual(listing(path.join(codexHome, 'agents', 'grimoire')), ['demo']);
    assert.deepEqual(listing(target), ['kept.toml']);
    assert.equal(fs.readFileSync(path.join(target, 'kept.toml'), 'utf8'), 'new');
  });

  test('two local installs keep their roles apart', t => {
    const dir = tempDir(t);
    const codexHome = path.join(dir, 'codex-home');
    const env = { CODEX_HOME: codexHome, HOME: codexHome };
    sync({ ...env, PLUGIN_ROOT: install(dir, 'one', 'local', { 'a.toml': 'A' }) });
    sync({ ...env, PLUGIN_ROOT: install(dir, 'two', 'local', { 'b.toml': 'B' }) });
    assert.deepEqual(listing(path.join(codexHome, 'agents', 'grimoire', 'one')), ['a.toml']);
    assert.deepEqual(listing(path.join(codexHome, 'agents', 'grimoire', 'two')), ['b.toml']);
  });

  test('removes the version-named and local folders earlier releases installed into, and nothing else', t => {
    const { pluginRoot, codexHome, target } = setup(t, { 'a.toml': 'A' });
    const grimoire = path.join(codexHome, 'agents', 'grimoire');
    writeFiles(grimoire, {
      '1.11.0/a.toml': 'old',
      '2.0.0-rc.1/a.toml': 'old',
      'local/a.toml': 'old',
      'other/x.toml': 'X',
      'v1.0.0/x.toml': 'X',
      '3.0.0': 'a file, not a folder',
    });
    writeFiles(path.join(codexHome, 'agents'), { '1.0.0/mine.toml': 'M' });

    const result = sync({ PLUGIN_ROOT: pluginRoot, CODEX_HOME: codexHome, HOME: codexHome });
    assert.deepEqual(listing(grimoire), ['3.0.0', 'demo', 'other', 'v1.0.0']);
    assert.deepEqual(listing(target), ['a.toml']);
    assert.ok(fs.existsSync(path.join(codexHome, 'agents', '1.0.0', 'mine.toml')));
    assert.match(result.stderr, /Removed 3 old Codex role folder/);
  });

  test('keeps its own folder when the plugin is named like a leftover', t => {
    const dir = tempDir(t);
    const codexHome = path.join(dir, 'codex-home');
    const pluginRoot = install(dir, 'local', '1.0.0', { 'a.toml': 'A' });
    sync({ PLUGIN_ROOT: pluginRoot, CODEX_HOME: codexHome, HOME: codexHome });
    assert.deepEqual(listing(path.join(codexHome, 'agents', 'grimoire', 'local')), ['a.toml']);
  });

  test('installs its roles and removes the other leftovers when one cannot be removed', t => {
    const { pluginRoot, codexHome, target } = setup(t, { 'a.toml': 'A' });
    const grimoire = path.join(codexHome, 'agents', 'grimoire');
    writeFiles(grimoire, { '1.0.0/locked/a.toml': 'old', '2.0.0/a.toml': 'old' });
    const locked = path.join(grimoire, '1.0.0', 'locked');
    fs.chmodSync(locked, 0o500);
    try {
      const result = sync({ PLUGIN_ROOT: pluginRoot, CODEX_HOME: codexHome, HOME: codexHome });
      assert.match(result.stderr, /Could not remove old Codex roles in .*1\.0\.0/);
      assert.deepEqual(listing(grimoire), ['1.0.0', 'demo']);
      assert.deepEqual(listing(target), ['a.toml']);
    } finally {
      fs.chmodSync(locked, 0o700);
    }
  });

  test('rewrites a changed role and leaves an unchanged one untouched', t => {
    const { pluginRoot, codexHome, target } = setup(t, { 'same.toml': 'S', 'changed.toml': 'new' });
    writeFiles(target, { 'same.toml': 'S', 'changed.toml': 'old' });
    const past = new Date('2020-01-01T00:00:00Z');
    for (const role of ['same.toml', 'changed.toml']) fs.utimesSync(path.join(target, role), past, past);

    sync({ PLUGIN_ROOT: pluginRoot, CODEX_HOME: codexHome, HOME: codexHome });
    assert.equal(fs.readFileSync(path.join(target, 'changed.toml'), 'utf8'), 'new');
    assert.equal(fs.statSync(path.join(target, 'same.toml')).mtimeMs, past.getTime());
  });

  test("removes roles the plugin no longer ships, and nothing it doesn't own", t => {
    const { pluginRoot, codexHome, target } = setup(t, { 'kept.toml': 'K' });
    writeFiles(target, { 'dropped.toml': 'D', 'user-notes.txt': 'U' });
    writeFiles(path.join(codexHome, 'agents'), { 'mine.toml': 'M', 'grimoire/other/x.toml': 'X' });

    sync({ PLUGIN_ROOT: pluginRoot, CODEX_HOME: codexHome, HOME: codexHome });
    assert.deepEqual(listing(target), ['kept.toml', 'user-notes.txt']);
    assert.ok(fs.existsSync(path.join(codexHome, 'agents', 'mine.toml')));
    assert.ok(fs.existsSync(path.join(codexHome, 'agents', 'grimoire', 'other', 'x.toml')));
  });

  test('a PLUGIN_ROOT ending in .. still installs under the manifest name', t => {
    const { pluginRoot, codexHome, target } = setup(t, { 'a.toml': 'A' });
    fs.mkdirSync(path.join(pluginRoot, 'hooks'));
    writeFiles(path.join(codexHome, 'agents'), { 'mine.toml': 'M' });

    // Concatenated, not path.join()ed: join would normalise the .. away.
    sync({ PLUGIN_ROOT: `${pluginRoot}/hooks/..`, CODEX_HOME: codexHome, HOME: codexHome });
    assert.deepEqual(listing(target), ['a.toml']);
    assert.ok(fs.existsSync(path.join(codexHome, 'agents', 'mine.toml')));
  });

  test('does nothing without PLUGIN_ROOT, or when the plugin ships no roles', t => {
    const dir = tempDir(t);
    const codexHome = path.join(dir, 'codex-home');
    sync({ CODEX_HOME: codexHome, HOME: codexHome });
    sync({ PLUGIN_ROOT: path.join(dir, 'no-roles'), CODEX_HOME: codexHome, HOME: codexHome });
    assert.ok(!fs.existsSync(codexHome));
  });

  for (const [label, manifest] of [
    ['a name Codex would refuse', JSON.stringify({ name: '..' })],
    ['no name', JSON.stringify({ version: '1.0.0' })],
    ['invalid JSON', '{not json'],
  ]) {
    test(`installs nothing when the manifest has ${label}`, t => {
      const { pluginRoot, codexHome } = setup(t, { 'a.toml': 'A' });
      writeFiles(codexHome, { 'agents/mine.toml': 'M' });
      writeFiles(pluginRoot, { '.codex-plugin/plugin.json': manifest });
      const result = sync({ PLUGIN_ROOT: pluginRoot, CODEX_HOME: codexHome, HOME: codexHome });
      assert.match(result.stderr, /sync-codex-agents skipped/);
      assert.deepEqual(listing(path.join(codexHome, 'agents')), ['mine.toml']);
    });
  }

  test('installs nothing when the plugin has no Codex manifest', t => {
    const { pluginRoot, codexHome } = setup(t, { 'a.toml': 'A' });
    fs.rmSync(path.join(pluginRoot, '.codex-plugin'), { recursive: true });
    const result = sync({ PLUGIN_ROOT: pluginRoot, CODEX_HOME: codexHome, HOME: codexHome });
    assert.match(result.stderr, /sync-codex-agents skipped/);
    assert.ok(!fs.existsSync(codexHome));
  });

  test('exits 0 with nothing on stdout when the sync fails', t => {
    const { dir, pluginRoot } = setup(t, { 'a.toml': 'A' });
    const blocked = path.join(dir, 'codex-home-is-a-file');
    fs.writeFileSync(blocked, '');
    const result = sync({ PLUGIN_ROOT: pluginRoot, CODEX_HOME: blocked, HOME: dir });
    assert.match(result.stderr, /sync-codex-agents skipped/);
  });
});
