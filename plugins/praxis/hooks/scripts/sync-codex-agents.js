#!/usr/bin/env node
/**
 * SessionStart Hook: install this plugin's Codex agent roles
 *
 * Codex has no plugin-level agent surface -- a manifest can point at skills,
 * MCP servers, apps and hooks, and nothing else -- so roles have to reach the
 * user's Codex config some other way.
 *
 * Codex-only, keyed on the bare PLUGIN_ROOT: Codex sets it alongside
 * CLAUDE_PLUGIN_ROOT, Claude Code sets only the prefixed name, so it is a
 * reliable discriminator.
 *
 * hooks.json reads PLUGIN_ROOT inside node rather than shell-interpolating it,
 * so every non-Codex session -- where the variable is unset -- is a clean no-op
 * instead of a `node /hooks/scripts/...` ENOENT. The guard below still stands
 * alone, so the script is safe to invoke directly.
 *
 * Roles nest under `grimoire/<plugin>/` because Codex discovers them
 * recursively; that keeps the namespace ours and cannot clobber a user's own.
 * `<plugin>` is the manifest's name, not PLUGIN_ROOT's basename: Codex installs
 * into `<marketplace>/<plugin>/<version>`, and a folder named after the version
 * would leave each old version's roles installed beside the new ones.
 *
 * Earlier releases did name the folder after the version, or `local` for a
 * manifest without one, so the sync also removes every folder in `grimoire/`
 * with such a name. Codex keeps the first role of a name in sorted path order,
 * and a version name starts with a digit, so it sorts before any plugin's and
 * its stale roles would otherwise win over ours. A `local` folder holds roles
 * no plugin owns any more: every plugin installed without a version shared it.
 */

const fs = require('fs');
const os = require('os');
const path = require('path');

const NAMESPACE = 'grimoire';

// Folder names earlier releases installed into (see the header): X.Y.Z with
// any suffix Codex allows in a version folder, or "local".
const LEFTOVER_FOLDER = /^(\d+\.\d+\.\d+([-+][\w.+-]*)?|local)$/;

function readPluginName(pluginRoot) {
  const manifest = path.join(pluginRoot, '.codex-plugin', 'plugin.json');
  const plugin = JSON.parse(fs.readFileSync(manifest, 'utf8')).name;
  // The plugin-name rule Codex installs by. A name it would refuse, such as
  // "..", could point the target outside our namespace, putting roles this
  // plugin does not own within reach of the sweep below.
  if (typeof plugin !== 'string' || !/^[\w-]+(\.[\w-]+)*$/.test(plugin)) {
    throw new Error(`${manifest} has no usable plugin name`);
  }
  return plugin;
}

/**
 * Copy roles whose contents differ from what is already installed, and remove
 * ones this plugin no longer ships. Returns a count of changes; writing only on
 * difference keeps mtimes stable across the many sessions that change nothing.
 */
function syncRoles(sourceDir, targetDir) {
  const roles = fs.readdirSync(sourceDir).filter(f => f.endsWith('.toml'));
  fs.mkdirSync(targetDir, { recursive: true });

  let changed = 0;
  for (const role of roles) {
    const desired = fs.readFileSync(path.join(sourceDir, role), 'utf8');
    const target = path.join(targetDir, role);

    let current = null;
    try {
      current = fs.readFileSync(target, 'utf8');
    } catch {
      // Not installed yet
    }

    if (current !== desired) {
      fs.writeFileSync(target, desired, 'utf8');
      changed++;
    }
  }

  // Roles dropped from the plugin should not linger in the user's config.
  const shipped = new Set(roles);
  for (const stale of fs.readdirSync(targetDir)) {
    if (stale.endsWith('.toml') && !shipped.has(stale)) {
      fs.rmSync(path.join(targetDir, stale), { force: true });
      changed++;
    }
  }

  return changed;
}

/**
 * Remove the folders earlier releases installed roles into, other than
 * `keep`. Returns how many were removed; a folder that cannot be removed is
 * reported and skipped.
 */
function sweepLeftovers(namespaceDir, keep) {
  let swept = 0;
  for (const entry of fs.readdirSync(namespaceDir, { withFileTypes: true })) {
    if (!entry.isDirectory() || entry.name === keep || !LEFTOVER_FOLDER.test(entry.name)) continue;
    const leftover = path.join(namespaceDir, entry.name);
    try {
      fs.rmSync(leftover, { recursive: true });
      swept++;
    } catch (err) {
      console.error(`[Hook] Could not remove old Codex roles in ${leftover}: ${err.message}`);
    }
  }
  return swept;
}

// Never block a session start: any failure here costs the user some agent
// roles, which is not worth refusing to start over.
try {
  const pluginRoot = process.env.PLUGIN_ROOT;
  if (pluginRoot) {
    const sourceDir = path.join(pluginRoot, 'codex', 'agents');
    if (fs.existsSync(sourceDir)) {
      const plugin = readPluginName(pluginRoot);
      const home = process.env.CODEX_HOME || path.join(os.homedir(), '.codex');
      const namespaceDir = path.join(home, 'agents', NAMESPACE);
      const targetDir = path.join(namespaceDir, plugin);
      const changed = syncRoles(sourceDir, targetDir);
      if (changed > 0) {
        console.error(`[Hook] Synced ${changed} Codex agent role(s) to ${targetDir}`);
      }
      const swept = sweepLeftovers(namespaceDir, plugin);
      if (swept > 0) {
        console.error(`[Hook] Removed ${swept} old Codex role folder(s) from ${namespaceDir}`);
      }
    }
  }
} catch (err) {
  console.error(`[Hook] sync-codex-agents skipped: ${err.message}`);
}

process.exit(0);
