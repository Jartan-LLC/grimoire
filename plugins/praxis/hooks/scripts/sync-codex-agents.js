#!/usr/bin/env node
/**
 * SessionStart Hook: install this plugin's Codex agent roles
 *
 * Cross-platform (Windows, macOS, Linux)
 *
 * Codex has no plugin-level agent surface -- a plugin manifest can point at
 * skills, MCP servers, apps and hooks, and nothing else -- so agent roles have
 * to reach the user's Codex config some other way. This copies the generated
 * roles out of the plugin into that config on session start.
 *
 * Codex-only. Codex sets a bare PLUGIN_ROOT for plugin hook processes (as well
 * as CLAUDE_PLUGIN_ROOT, for compatibility); Claude Code sets only the
 * CLAUDE_-prefixed names. The bare one is therefore a reliable discriminator,
 * and reading paths from it means a version bump moves the source directory
 * without stranding a stale copy.
 *
 * Roles land in a `grimoire/<plugin>/` subdirectory rather than loose in
 * agents/: Codex discovers agent roles recursively, so nesting them keeps the
 * namespace ours and cannot clobber a role the user wrote themselves.
 */

const fs = require('fs');
const os = require('os');
const path = require('path');

const NAMESPACE = 'grimoire';

function codexAgentsDir() {
  const home = process.env.CODEX_HOME || path.join(os.homedir(), '.codex');
  return path.join(home, 'agents', NAMESPACE, path.basename(process.env.PLUGIN_ROOT));
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
      const changed = syncRoles(sourceDir, codexAgentsDir());
      if (changed > 0) {
        console.error(`[Hook] Synced ${changed} Codex agent role(s) to ${codexAgentsDir()}`);
      }
    }
  }
} catch (err) {
  console.error(`[Hook] sync-codex-agents skipped: ${err.message}`);
}

process.exit(0);
