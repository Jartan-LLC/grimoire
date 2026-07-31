#!/usr/bin/env node
// Originally from everything-claude-code by Affaan Mustafa (https://github.com/affaan-m/ECC)

/**
 * PostToolUse Hook: Check for console.log statements in changed files
 *
 * Cross-platform (Windows, macOS, Linux)
 *
 * Runs after an edit and checks whether any changed JavaScript/TypeScript file
 * contains console.log statements, reporting the offending line numbers to help
 * developers remove debug statements before committing.
 *
 * PostToolUse rather than Stop: on Stop, additionalContext is documented to
 * continue the conversation so Claude can act on the feedback, which keeps the
 * turn alive until the warning stops firing. An intentional console.log outside
 * the exclusions below would never stop firing. PostToolUse injects the same
 * warning next to the tool result and ends there.
 *
 * Covers modified tracked files and new untracked ones -- `git diff` alone
 * cannot see a file that was never added, which is exactly where fresh debug
 * logging tends to live.
 *
 * Exclusions: test files, config files, and scripts/ directory (where
 * console.log is often intentional).
 */

const fs = require('fs');
const {
  isGitRepo,
  getGitModifiedFiles,
  getGitUntrackedFiles,
  grepFile,
  log,
  output,
} = require('./lib/utils');

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

function changedSourceFiles() {
  const files = [
    ...getGitModifiedFiles(SOURCE_PATTERNS),
    ...getGitUntrackedFiles(SOURCE_PATTERNS),
  ];

  return [...new Set(files)]
    .filter(f => fs.existsSync(f))
    .filter(f => !EXCLUDED_PATTERNS.some(pattern => pattern.test(f)));
}

function run() {
  const warnings = [];

  try {
    if (!isGitRepo()) return warnings;

    // Require the call parenthesis: the bare substring also matches
    // `console.logger.info(...)` and `console.log.bind(...)`, neither of which
    // is a debug statement.
    const flagged = changedSourceFiles()
      .map(file => ({ file, matches: grepFile(file, /console\.log\s*\(/) }))
      .filter(({ matches }) => matches.length > 0);

    for (const { file, matches } of flagged.slice(0, MAX_REPORTED_FILES)) {
      warnings.push(`[Hook] WARNING: console.log found in ${file}`);
      for (const { lineNumber, content } of matches.slice(0, MAX_REPORTED_LINES)) {
        warnings.push(`${lineNumber}: ${content.trim()}`);
      }
    }

    if (flagged.length > MAX_REPORTED_FILES) {
      warnings.push(`[Hook] ...and ${flagged.length - MAX_REPORTED_FILES} more file(s) with console.log`);
    }

    if (warnings.length > 0) {
      warnings.push('[Hook] Remove console.log statements before committing');
    }
  } catch (err) {
    // An internal failure is a debugging detail, not something to put in front
    // of the model -- log it and report no findings.
    log(`[Hook] check-console-log error: ${err.message}`);
    return [];
  }

  return warnings;
}

// Nothing here reads the hook payload -- the check consults git, not the event
// -- but stdin still has to be drained so the harness is never left writing
// into a full pipe.
process.stdin.resume();
process.stdin.on('data', () => {});

process.stdin.on('end', () => {
  const warnings = run();

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
});

module.exports = { run };
