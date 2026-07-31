#!/usr/bin/env node
// Originally from everything-claude-code by Affaan Mustafa (https://github.com/affaan-m/ECC)
/**
 * Strategic Compact Suggester
 *
 * Cross-platform (Windows, macOS, Linux)
 *
 * Suggests /compact at logical boundaries rather than waiting for auto-compact,
 * which fires mid-task and summarizes away context you still need.
 *
 * - Strategic compacting preserves context through logical phases
 * - Compact after exploration, before execution
 * - Compact after completing a milestone, before starting next
 *
 * Two signals:
 * - Context size (primary): the latest assistant `usage` record from the session
 *   transcript, compared against a window-scaled token threshold
 *   (COMPACT_CONTEXT_THRESHOLD; default 160k on a 200k window, 250k on 1M),
 *   re-reminding after every COMPACT_CONTEXT_INTERVAL tokens of growth
 *   (default 60k).
 * - Tool-call count (secondary): first at COMPACT_THRESHOLD (default 50), then
 *   every 25. A weak proxy for window pressure on its own -- a few large reads
 *   can fill the window in very few calls, and many tiny calls can cross 50
 *   while the window is barely used.
 */

const fs = require('fs');
const {
  writeFile,
  readStdinJson,
  log,
  output
} = require('./lib/utils');
const {
  sessionId: toSessionId,
  stateFilePath,
  sweepStaleState
} = require('./lib/session-state');
const {
  readLatestContextTokens,
  resolveContextWindowTokens,
  resolveContextThreshold,
  resolveContextInterval,
  computeContextBucket,
  formatWindowLabel
} = require('./lib/transcript-context');

const COUNTER_FILE_PREFIX = 'claude-tool-count-';
const CONTEXT_BUCKET_FILE_PREFIX = 'claude-context-bucket-';
const STATE_FILE_PREFIXES = [COUNTER_FILE_PREFIX, CONTEXT_BUCKET_FILE_PREFIX];

/**
 * Increment and persist the per-session tool-call counter.
 * Uses fd-based read+write to reduce (but not eliminate) the race window
 * between concurrent hook invocations.
 */
function incrementToolCallCount(counterFile) {
  let count = 1;

  try {
    const fd = fs.openSync(counterFile, 'a+');
    try {
      const buf = Buffer.alloc(64);
      const bytesRead = fs.readSync(fd, buf, 0, 64, 0);
      if (bytesRead > 0) {
        const parsed = parseInt(buf.toString('utf8', 0, bytesRead).trim(), 10);
        // Clamp to reasonable range -- corrupted files could contain huge values
        // that pass Number.isFinite() (e.g., parseInt('9'.repeat(30)) => 1e+29)
        count = (Number.isFinite(parsed) && parsed > 0 && parsed <= 1000000)
          ? parsed + 1
          : 1;
      }
      fs.ftruncateSync(fd, 0);
      fs.writeSync(fd, String(count), 0);
    } finally {
      fs.closeSync(fd);
    }
  } catch {
    // Fallback: just use writeFile if fd operations fail
    writeFile(counterFile, String(count));
  }

  return count;
}

/**
 * Read the last context bucket this session already fired for (-1 when the
 * suggestion has not fired yet or the state file is unreadable/corrupted).
 */
function readLastContextBucket(bucketFile) {
  try {
    const parsed = parseInt(fs.readFileSync(bucketFile, 'utf8').trim(), 10);
    return Number.isInteger(parsed) && parsed >= 0 && parsed <= 1000000 ? parsed : -1;
  } catch {
    return -1;
  }
}

/**
 * Build the context-size suggestion when the transcript shows the session has
 * crossed into a new context bucket. Returns null when the signal is silent
 * (no transcript, below threshold, disabled, or already fired for the bucket).
 *
 * Never throws -- any transcript or state-file failure silently disables the
 * signal so the hook keeps its always-exit-0 contract.
 */
function buildContextSuggestion(transcriptPath, bucketFile, env) {
  try {
    const usage = readLatestContextTokens(transcriptPath);
    if (!usage) return null;

    const windowTokens = resolveContextWindowTokens(usage.tokens, usage.model);
    const threshold = resolveContextThreshold(env, windowTokens);
    if (threshold <= 0) return null; // COMPACT_CONTEXT_THRESHOLD=0 disables

    const bucket = computeContextBucket(usage.tokens, threshold, resolveContextInterval(env));
    if (bucket < 0 || bucket <= readLastContextBucket(bucketFile)) return null;

    writeFile(bucketFile, String(bucket));

    const approxTokens = `${Math.round(usage.tokens / 1000)}k`;
    const percent = Math.round((usage.tokens / windowTokens) * 100);
    return `[StrategicCompact] Context ~${approxTokens} tokens (${percent}% of ${formatWindowLabel(windowTokens)} window) - consider /compact at the next logical boundary`;
  } catch (err) {
    log(`[StrategicCompact] Context signal skipped: ${err.message}`);
    return null;
  }
}

async function main() {
  // Claude Code passes hook input via stdin JSON. `session_id` is canonical
  // (the legacy env var, then 'default', are fallbacks); `transcript_path`
  // feeds the context-size signal.
  let input = {};
  try {
    input = await readStdinJson({ timeoutMs: 1000 });
  } catch {
    input = {};
  }

  const sessionId = toSessionId(input && input.session_id);
  const transcriptPath = (input && typeof input.transcript_path === 'string') ? input.transcript_path : '';

  const counterFile = stateFilePath(COUNTER_FILE_PREFIX, sessionId);
  const bucketFile = stateFilePath(CONTEXT_BUCKET_FILE_PREFIX, sessionId);

  // Only this hook's own prefixes -- every hook sweeps after itself.
  sweepStaleState(STATE_FILE_PREFIXES, [counterFile, bucketFile]);

  const rawThreshold = parseInt(process.env.COMPACT_THRESHOLD || '50', 10);
  const threshold = Number.isFinite(rawThreshold) && rawThreshold > 0 && rawThreshold <= 10000
    ? rawThreshold
    : 50;

  const count = incrementToolCallCount(counterFile);
  const messages = [];

  const contextSuggestion = buildContextSuggestion(transcriptPath, bucketFile, process.env);
  if (contextSuggestion) {
    messages.push(contextSuggestion);
  }

  if (count === threshold) {
    messages.push(`[StrategicCompact] ${threshold} tool calls reached - consider /compact if transitioning phases`);
  } else if (count > threshold && (count - threshold) % 25 === 0) {
    messages.push(`[StrategicCompact] ${count} tool calls - good checkpoint for /compact if context is stale`);
  }

  // log() writes to stderr, which for a non-blocking PreToolUse hook on exit 0
  // reaches the debug log only -- never the model. Suggestions have to travel as
  // structured stdout JSON instead, via hookSpecificOutput.additionalContext,
  // which Claude Code wraps in a system reminder at the point the hook fired.
  // At most one stdout payload per run, so both signals share it.
  if (messages.length > 0) {
    for (const msg of messages) {
      log(msg);
    }
    output({
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        additionalContext: messages.join('\n')
      }
    });
  }

  process.exit(0);
}

main().catch(err => {
  log(`[StrategicCompact] Error: ${err.message}`);
  process.exit(0);
});
