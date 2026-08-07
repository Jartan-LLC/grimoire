#!/usr/bin/env node
// Originally from everything-claude-code by Affaan Mustafa (https://github.com/affaan-m/ECC)

/**
 * PostToolUse Hook: Check for console.log statements in changed files
 *
 * PostToolUse rather than Stop: on Stop, additionalContext continues the
 * conversation so Claude can act on it, keeping the turn alive until the
 * warning stops firing -- which an intentional console.log never would.
 *
 * Findings are rate-limited because this fires per edit rather than per turn.
 * One new to the session surfaces immediately; one already reported repeats
 * only every CONSOLE_LOG_COOLDOWN edits, so a log the user has decided to keep
 * stops nagging without delaying a genuinely new one.
 *
 * Untracked files are covered as well as tracked ones -- `git diff` cannot see
 * a file that was never added, which is exactly where fresh debug logging lives.
 *
 * The exclusions below are the places console.log is usually intentional.
 */

const fs = require('fs');
const {
  isGitRepo,
  getGitModifiedFiles,
  getGitUntrackedFiles,
  grepFile,
  readHookInput,
  writeFile,
  log,
  output,
} = require('./lib/utils');
const {
  sessionId: toSessionId,
  stateFilePath,
  sweepStaleState,
} = require('./lib/session-state');

// Files where console.log is expected and should not trigger warnings
const EXCLUDED_PATTERNS = [
  /\.test\.[jt]sx?$/,
  /\.spec\.[jt]sx?$/,
  /\.config\.[jt]s$/,
  /scripts\//,
  /__tests__\//,
  /__mocks__\//,
];

const SOURCE_PATTERNS = ['\\.tsx?$', '\\.jsx?$'];
const MAX_REPORTED_LINES = 5;
// The payload is injected next to every tool result, so a branch touching many
// files would otherwise grow it without bound.
const MAX_REPORTED_FILES = 10;

const STATE_FILE_PREFIX = 'claude-console-log-';
const DEFAULT_REPEAT_COOLDOWN = 10;

function getRepeatCooldown() {
  const parsed = Number.parseInt(process.env.CONSOLE_LOG_COOLDOWN, 10);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : DEFAULT_REPEAT_COOLDOWN;
}

function changedSourceFiles() {
  const files = [
    ...getGitModifiedFiles(SOURCE_PATTERNS),
    ...getGitUntrackedFiles(SOURCE_PATTERNS),
  ];

  return [...new Set(files)]
    .filter(f => fs.existsSync(f))
    .filter(f => !EXCLUDED_PATTERNS.some(pattern => pattern.test(f)));
}

/**
 * Every console.log in the changed files, one entry per offending line.
 *
 * Keyed on file plus the line's text rather than its number: an edit above a
 * debug statement shifts its line number without changing the statement, and
 * that should not read as a new finding.
 */
function collectFindings() {
  const findings = [];

  for (const file of changedSourceFiles()) {
    // Require the call parenthesis: the bare substring also matches
    // `console.logger.info(...)` and `console.log.bind(...)`, neither of which
    // is a debug statement.
    for (const { lineNumber, content } of grepFile(file, /console\.log\s*\(/)) {
      const text = content.trim();
      findings.push({ file, lineNumber, text, key: `${file}:${text}` });
    }
  }

  return findings;
}

function readState(file) {
  try {
    const parsed = JSON.parse(fs.readFileSync(file, 'utf8'));
    return {
      seen: Array.isArray(parsed.seen) ? parsed.seen : [],
      cooldown: Number.isInteger(parsed.cooldown) ? parsed.cooldown : 0,
    };
  } catch {
    return { seen: [], cooldown: 0 };
  }
}

/**
 * Split findings into what to report now, and the state to carry forward.
 *
 * Findings never reported this session are always returned. Ones already
 * reported come back only when the cooldown has elapsed. Reporting anything
 * restarts the cooldown, so a finding is not announced and then immediately
 * repeated on the next edit. Findings that have disappeared drop out of `seen`,
 * so a statement removed and later reintroduced counts as new again.
 */
function applyCooldown(findings, state, cooldownEdits) {
  const present = new Set(findings.map(f => f.key));
  const seen = new Set(state.seen.filter(key => present.has(key)));

  const fresh = findings.filter(f => !seen.has(f.key));
  const repeats = findings.filter(f => seen.has(f.key));
  const cooledDown = state.cooldown <= 0;

  const report = (repeats.length > 0 && cooledDown) ? findings : fresh;
  const cooldown = report.length > 0
    ? cooldownEdits
    : Math.max(0, state.cooldown - 1);

  return { report, state: { seen: [...present], cooldown } };
}

/** Group findings by file and render them, honouring both display caps. */
function formatWarnings(findings) {
  if (findings.length === 0) return [];

  const byFile = new Map();
  for (const finding of findings) {
    if (!byFile.has(finding.file)) byFile.set(finding.file, []);
    byFile.get(finding.file).push(finding);
  }

  const warnings = [];
  for (const [file, lines] of [...byFile].slice(0, MAX_REPORTED_FILES)) {
    warnings.push(`[Hook] WARNING: console.log found in ${file}`);
    for (const { lineNumber, text } of lines.slice(0, MAX_REPORTED_LINES)) {
      warnings.push(`${lineNumber}: ${text}`);
    }
  }

  if (byFile.size > MAX_REPORTED_FILES) {
    warnings.push(`[Hook] ...and ${byFile.size - MAX_REPORTED_FILES} more file(s) with console.log`);
  }

  warnings.push('[Hook] Remove console.log statements before committing');
  return warnings;
}

function run(sessionId) {
  try {
    if (!isGitRepo()) return [];

    const file = stateFilePath(STATE_FILE_PREFIX, sessionId);
    // Only this hook's own prefix -- every hook sweeps after itself.
    sweepStaleState([STATE_FILE_PREFIX], [file]);

    const { report, state } = applyCooldown(
      collectFindings(),
      readState(file),
      getRepeatCooldown()
    );
    writeFile(file, JSON.stringify(state));

    return formatWarnings(report);
  } catch (err) {
    // An internal failure is a debugging detail, not something to put in front
    // of the model -- log it and report no findings.
    log(`[Hook] check-console-log error: ${err.message}`);
    return [];
  }
}

async function main() {
  const input = await readHookInput();

  const warnings = run(toSessionId(input.session_id));

  // stderr on a zero-exit hook reaches the debug log and nothing else, so
  // findings travel as structured stdout instead: additionalContext is injected
  // next to the tool result. Only one JSON payload is allowed per run, which is
  // why the input is not echoed back alongside it.
  if (warnings.length > 0) {
    output({
      hookSpecificOutput: {
        hookEventName: 'PostToolUse',
        additionalContext: warnings.join('\n')
      }
    });
  }

  process.exit(0);
}

main().catch(err => {
  log(`[Hook] check-console-log error: ${err.message}`);
  process.exit(0);
});

module.exports = { run, applyCooldown };
