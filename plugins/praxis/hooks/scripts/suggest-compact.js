#!/usr/bin/env node
// Originally from everything-claude-code by Affaan Mustafa (https://github.com/affaan-m/ECC)
/**
 * Strategic Compact Suggester
 *
 * Suggests /compact at logical boundaries rather than waiting for auto-compact,
 * which fires mid-task and summarizes away context you still need.
 *
 * Two signals:
 * - Context size (primary): the latest assistant `usage` record from the session
 *   transcript, gated by COMPACT_CONTEXT_THRESHOLD and COMPACT_CONTEXT_INTERVAL.
 *   Absolute tokens only -- see lib/transcript-context.js for why there is no
 *   percentage.
 * - Tool-call count (secondary), gated by COMPACT_THRESHOLD. A weak proxy for
 *   window pressure on its own -- a few large reads can fill the window in very
 *   few calls, and many tiny calls can cross the threshold while the window is
 *   barely used.
 *
 * Defaults are declared with the settings themselves, not echoed here.
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
  MAX_TOKEN_SETTING,
  readLatestContextTokens,
  resolveContextThreshold,
  resolveContextInterval
} = require('./lib/transcript-context');

const DEFAULT_TOOL_CALL_THRESHOLD = 50;
const DEFAULT_TOOL_CALL_INTERVAL = 25;
const MAX_TOOL_CALL_SETTING = 10000;

const COUNTER_FILE_PREFIX = 'claude-tool-count-';
const CONTEXT_TOKENS_FILE_PREFIX = 'claude-context-tokens-';
// The file now holds a token count, not a bucket index. Reusing the old prefix
// would let a downgraded hook read ~400000 as a bucket index and go silent for
// the rest of the session; the legacy prefix stays only so stale files sweep.
const LEGACY_CONTEXT_BUCKET_FILE_PREFIX = 'claude-context-bucket-';
const STATE_FILE_PREFIXES = [
  COUNTER_FILE_PREFIX,
  CONTEXT_TOKENS_FILE_PREFIX,
  LEGACY_CONTEXT_BUCKET_FILE_PREFIX
];

/**
 * Resolve a tool-call count setting. Invalid, out-of-range and absent values all
 * fall back to the default; unlike the context threshold, 0 is not a disable
 * switch here, since the count signal has no separate off state.
 */
function resolveToolCallSetting(raw, fallback) {
  const parsed = parseInt(raw, 10);
  return Number.isFinite(parsed) && parsed > 0 && parsed <= MAX_TOOL_CALL_SETTING ? parsed : fallback;
}

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
 * Read the context size this session last fired at. Returns null when the
 * suggestion has not fired yet or the state file is unreadable/corrupted.
 *
 * null rather than -1: with a numeric sentinel, `tokens >= lastFired + interval`
 * silently turns the interval into a floor on the first fire, overriding a
 * configured threshold.
 */
function readLastFiredTokens(tokensFile) {
  try {
    const parsed = parseInt(fs.readFileSync(tokensFile, 'utf8').trim(), 10);
    return Number.isInteger(parsed) && parsed >= 0 && parsed <= MAX_TOKEN_SETTING ? parsed : null;
  } catch {
    return null;
  }
}

/**
 * Build the context-size suggestion when the session has grown enough since the
 * last one. Returns null when the signal is silent (no transcript, below
 * threshold, disabled, or too little growth since the last fire).
 *
 * Never throws -- any transcript or state-file failure silently disables the
 * signal so the hook keeps its always-exit-0 contract.
 */
function buildContextSuggestion(transcriptPath, tokensFile, env) {
  try {
    const usage = readLatestContextTokens(transcriptPath);
    if (!usage) return null;

    const threshold = resolveContextThreshold(env);
    if (threshold <= 0) return null; // COMPACT_CONTEXT_THRESHOLD=0 disables

    let lastFired = readLastFiredTokens(tokensFile);
    // Context shrank, so a compact happened. Without this reset the gate only
    // ever ratchets upward and goes silent for the rest of the session --
    // straight after the action this hook exists to prompt. Clearing the file
    // rather than just the variable matters when the run returns below: growth
    // back past the stale mark would otherwise be gated off the pre-compact
    // peak, which is the same silence in a narrower window.
    if (lastFired !== null && usage.tokens < lastFired) {
      lastFired = null;
      try {
        fs.rmSync(tokensFile, { force: true });
      } catch {
        // Best-effort: the in-memory reset still covers this invocation.
      }
    }

    if (usage.tokens < threshold) return null;
    if (lastFired !== null && usage.tokens < lastFired + resolveContextInterval(env)) return null;

    writeFile(tokensFile, String(usage.tokens));

    const approxTokens = `${Math.round(usage.tokens / 1000)}k`;
    return `[StrategicCompact] Context ~${approxTokens} tokens - consider /compact at the next logical boundary`;
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
  const contextTokensFile = stateFilePath(CONTEXT_TOKENS_FILE_PREFIX, sessionId);

  // Only this hook's own prefixes -- every hook sweeps after itself.
  sweepStaleState(STATE_FILE_PREFIXES, [counterFile, contextTokensFile]);

  const threshold = resolveToolCallSetting(process.env.COMPACT_THRESHOLD, DEFAULT_TOOL_CALL_THRESHOLD);
  const interval = resolveToolCallSetting(process.env.COMPACT_INTERVAL, DEFAULT_TOOL_CALL_INTERVAL);

  const count = incrementToolCallCount(counterFile);
  const messages = [];

  const contextSuggestion = buildContextSuggestion(transcriptPath, contextTokensFile, process.env);
  if (contextSuggestion) {
    messages.push(contextSuggestion);
  }

  if (count === threshold) {
    messages.push(`[StrategicCompact] ${threshold} tool calls reached - consider /compact if transitioning phases`);
  } else if (count > threshold && (count - threshold) % interval === 0) {
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
