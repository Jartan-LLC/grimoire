/**
 * Per-session hook state in the OS temp directory.
 *
 * Several hooks need to remember something between invocations within a session
 * -- how many tool calls have gone by, which findings have already been
 * reported. Each writes `<prefix><sessionId>` into the temp dir and is
 * responsible for sweeping its own files; nothing else cleans up after them.
 * The mechanics live here so each hook stays self-contained without copying
 * them.
 */

const fs = require('fs');
const path = require('path');
const { getTempDir, log } = require('./utils');

const DEFAULT_STATE_TTL_DAYS = 14;

/**
 * Reduce a session id to something safe to interpolate into a filename.
 * Falls back to the legacy env var, then a fixed name, so state is still shared
 * within a session when the hook payload omits it.
 */
function sessionId(raw) {
  const candidate = (typeof raw === 'string' && raw)
    ? raw
    : (process.env.CLAUDE_SESSION_ID || 'default');
  return candidate.replace(/[^a-zA-Z0-9_-]/g, '') || 'default';
}

function stateFilePath(prefix, id) {
  return path.join(getTempDir(), `${prefix}${id}`);
}

function stateTtlDays() {
  const parsed = Number.parseInt(process.env.HOOK_STATE_TTL_DAYS, 10);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : DEFAULT_STATE_TTL_DAYS;
}

/**
 * Remove state files older than the TTL, so they do not accumulate one per
 * session forever. Only files matching `prefixes` are considered, and anything
 * in `keep` is preserved -- the caller is about to rewrite those.
 *
 * Never throws: hooks must exit 0, so a filesystem failure is logged and
 * swallowed rather than allowed to escape.
 */
function sweepStaleState(prefixes, keep = [], retentionDays = stateTtlDays()) {
  const tempDir = getTempDir();

  let entries;
  try {
    entries = fs.readdirSync(tempDir, { withFileTypes: true });
  } catch (err) {
    log(`[Hook] Skipping state sweep; readdir failed: ${err.message}`);
    return;
  }

  const cutoffMs = Date.now() - retentionDays * 24 * 60 * 60 * 1000;
  const preserved = new Set(keep.map(file => path.basename(file)));

  for (const entry of entries) {
    if (!entry.isFile()) continue;
    if (!prefixes.some(prefix => entry.name.startsWith(prefix))) continue;
    if (preserved.has(entry.name)) continue;

    const fullPath = path.join(tempDir, entry.name);
    let stats;
    try {
      stats = fs.statSync(fullPath);
    } catch {
      continue;
    }

    // Strict "older than": a file sitting exactly on the cutoff has age ==
    // retentionDays, which is not older than it, so preserve it.
    if (stats.mtimeMs >= cutoffMs) continue;

    try {
      fs.rmSync(fullPath, { force: true });
    } catch (err) {
      log(`[Hook] Warning: failed to prune stale state ${fullPath}: ${err.message}`);
    }
  }
}

module.exports = {
  DEFAULT_STATE_TTL_DAYS,
  sessionId,
  stateFilePath,
  stateTtlDays,
  sweepStaleState,
};
