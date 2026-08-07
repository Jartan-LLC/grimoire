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
 * reliable discriminator. Reading paths from it also means a version bump
 * moves the source directory without stranding a stale copy.
 *
 * hooks.json reads PLUGIN_ROOT inside node rather than shell-interpolating it,
 * so every non-Codex session -- where the variable is unset -- is a clean no-op
 * instead of a `node /hooks/scripts/...` ENOENT. The guard below still stands
 * alone, so the script is safe to invoke directly.
 *
 * Roles nest under `grimoire/<plugin>/` because Codex discovers them
 * recursively; that keeps the namespace ours and cannot clobber a user's own.
 */

const fs = require('fs');
const os = require('os');
const path = require('path');

const NAMESPACE = 'grimoire';

function codexAgentsDir() {
  const home = process.env.CODEX_HOME || path.join(os.homedir(), '.codex');
  // Resolve before taking the basename: a PLUGIN_ROOT ending in `..` would
  // otherwise yield ".." and point the target at the agents directory itself,
  // putting roles this plugin does not own within reach of the sweep below.
  const plugin = path.basename(path.resolve(process.env.PLUGIN_ROOT));
  return path.join(home, 'agents', NAMESPACE, plugin);
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

// Never block a session start: any failure here costs the user some agent
// roles, which is not worth refusing to start over.
try {
  if (process.env.PLUGIN_ROOT) {
    const sourceDir = path.join(process.env.PLUGIN_ROOT, 'codex', 'agents');
    if (fs.existsSync(sourceDir)) {
      const targetDir = codexAgentsDir();
      const changed = syncRoles(sourceDir, targetDir);
      if (changed > 0) {
        console.error(`[Hook] Synced ${changed} Codex agent role(s) to ${targetDir}`);
      }
    }
  }
} catch (err) {
  console.error(`[Hook] sync-codex-agents skipped: ${err.message}`);
}

process.exit(0);
