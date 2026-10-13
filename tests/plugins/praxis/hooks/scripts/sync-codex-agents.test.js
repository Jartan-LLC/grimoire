// The script does its work at require time -- that is how hooks.json invokes
// it -- so every test runs it as a process rather than importing it.

const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const { describe, test } = require('node:test');

const { REPO_ROOT, tempDir, writeFiles } = require('../../../../helpers/fixture');

const SCRIPT = path.join(REPO_ROOT, 'plugins/praxis/hooks/scripts/sync-codex-agents.js');

/** A plugin root holding `roles` ({file name: contents}) in codex/agents, plus a Codex home. */
function setup(t, roles) {
  const dir = tempDir(t);
  const pluginRoot = path.join(dir, 'plugins', 'demo');
  const codexHome = path.join(dir, 'codex-home');
  fs.mkdirSync(path.join(pluginRoot, 'codex', 'agents'), { recursive: true });
  writeFiles(path.join(pluginRoot, 'codex', 'agents'), roles);
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

  test('a PLUGIN_ROOT ending in .. names the real plugin, not the agents directory', t => {
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

  test('exits 0 with nothing on stdout when the sync fails', t => {
    const { dir, pluginRoot } = setup(t, { 'a.toml': 'A' });
    const blocked = path.join(dir, 'codex-home-is-a-file');
    fs.writeFileSync(blocked, '');
    const result = sync({ PLUGIN_ROOT: pluginRoot, CODEX_HOME: blocked, HOME: dir });
    assert.match(result.stderr, /sync-codex-agents skipped/);
  });
});
