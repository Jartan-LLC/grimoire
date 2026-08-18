// Vendored from everything-claude-code by Affaan Mustafa (https://github.com/affaan-m/ECC)
/**
 * Transcript context-size helpers for the strategic-compact hook.
 *
 * Reads the latest assistant `usage` record from a session transcript (JSONL)
 * and reports the absolute context size of that turn.
 *
 * Nothing here models the context window. The window is not knowable from a
 * hook: transcripts carry a bare model id, and the harness exports no window
 * variable. Reporting absolute tokens leaves no denominator to get wrong -- the
 * user knows which model they are on and can set the threshold accordingly.
 *
 * Only the tail of the transcript is read, keeping the hook fast on very large
 * sessions.
 */

const fs = require('fs');

const DEFAULT_CONTEXT_THRESHOLD_TOKENS = 160000;
const DEFAULT_CONTEXT_INTERVAL_TOKENS = 60000;
const DEFAULT_TRANSCRIPT_TAIL_BYTES = 256 * 1024;
const MAX_TOKEN_SETTING = 10000000;

/**
 * Read the trailing `tailBytes` of a file as UTF-8.
 * Returns null when the file is missing or unreadable.
 */
function readFileTail(filePath, tailBytes) {
  let fd;
  try {
    fd = fs.openSync(filePath, 'r');
  } catch {
    return null;
  }

  try {
    const size = fs.fstatSync(fd).size;
    const start = Math.max(0, size - tailBytes);
    const length = size - start;
    if (length <= 0) {
      return { text: '', truncated: false };
    }

    const buffer = Buffer.alloc(length);
    const bytesRead = fs.readSync(fd, buffer, 0, length, start);
    return {
      text: buffer.toString('utf8', 0, bytesRead),
      truncated: start > 0
    };
  } catch {
    return null;
  } finally {
    try {
      fs.closeSync(fd);
    } catch {
      /* ignore */
    }
  }
}

/**
 * Sum the fields that partition the prompt, so the total is the context size.
 */
function sumPromptTokens(usage) {
  return (
    (Number.isFinite(usage.input_tokens) ? usage.input_tokens : 0) +
    (Number.isFinite(usage.cache_read_input_tokens) ? usage.cache_read_input_tokens : 0) +
    (Number.isFinite(usage.cache_creation_input_tokens) ? usage.cache_creation_input_tokens : 0)
  );
}

/**
 * Extract the context token total from a transcript record's usage block.
 * Returns 0 when the record carries no usable usage data.
 */
function extractUsageTokens(record) {
  const usage = record && record.message && record.message.usage;
  if (!usage || typeof usage !== 'object') {
    return 0;
  }

  // On a multi-iteration turn the top-level fields aggregate ACROSS iterations,
  // so summing them double-counts a context that was never that large -- 2.00x
  // at the worst local case. Each iteration re-sends the prompt, so the largest
  // single iteration is the real context size.
  const iterations = usage.iterations;
  if (Array.isArray(iterations) && iterations.length > 0) {
    const largest = iterations.reduce((max, iteration) => {
      if (!iteration || typeof iteration !== 'object') return max;
      return Math.max(max, sumPromptTokens(iteration));
    }, 0);
    if (largest > 0) {
      return largest;
    }
  }

  const total = sumPromptTokens(usage);
  return total > 0 ? total : 0;
}

/**
 * Scan a session transcript (JSONL) backwards for the most recent record with
 * a non-empty `message.usage` block.
 *
 * @param {string} transcriptPath - Absolute path to the transcript JSONL.
 * @param {object} [options]
 * @param {number} [options.tailBytes] - How many trailing bytes to scan.
 * @returns {{ tokens: number } | null} Latest context size, or null when the
 *   transcript is missing, unreadable, or has no usage records.
 */
function readLatestContextTokens(transcriptPath, options = {}) {
  if (typeof transcriptPath !== 'string' || !transcriptPath) {
    return null;
  }

  const tailBytes = Number.isInteger(options.tailBytes) && options.tailBytes > 0 ? options.tailBytes : DEFAULT_TRANSCRIPT_TAIL_BYTES;

  const tail = readFileTail(transcriptPath, tailBytes);
  if (!tail) {
    return null;
  }

  const lines = tail.text.split('\n');
  // The first line of a truncated tail is almost certainly partial JSON.
  const firstLine = tail.truncated ? 1 : 0;

  for (let i = lines.length - 1; i >= firstLine; i--) {
    const line = lines[i].trim();
    if (!line) continue;

    let record;
    try {
      record = JSON.parse(line);
    } catch {
      continue;
    }

    const tokens = extractUsageTokens(record);
    if (tokens > 0) {
      return { tokens };
    }
  }

  return null;
}

/**
 * Resolve the context-size suggestion threshold (tokens).
 * `COMPACT_CONTEXT_THRESHOLD=0` disables the context signal entirely;
 * other invalid values fall back to the default.
 */
function resolveContextThreshold(env) {
  const raw = env && env.COMPACT_CONTEXT_THRESHOLD;
  if (raw !== undefined && raw !== null && raw !== '') {
    const parsed = Number.parseInt(raw, 10);
    if (parsed === 0) {
      return 0;
    }
    if (Number.isInteger(parsed) && parsed > 0 && parsed <= MAX_TOKEN_SETTING) {
      return parsed;
    }
  }

  return DEFAULT_CONTEXT_THRESHOLD_TOKENS;
}

/**
 * Resolve the re-reminder step (tokens of additional context growth before
 * the suggestion repeats). Invalid values fall back to the default.
 */
function resolveContextInterval(env) {
  const raw = env && env.COMPACT_CONTEXT_INTERVAL;
  const parsed = Number.parseInt(raw, 10);
  return Number.isInteger(parsed) && parsed > 0 && parsed <= MAX_TOKEN_SETTING ? parsed : DEFAULT_CONTEXT_INTERVAL_TOKENS;
}

module.exports = {
  MAX_TOKEN_SETTING,
  readFileTail,
  extractUsageTokens,
  readLatestContextTokens,
  resolveContextThreshold,
  resolveContextInterval
};
