#!/usr/bin/env node
// Originally from everything-claude-code by Affaan Mustafa (https://github.com/affaan-m/ECC)

/**
 * Stop Hook: Check for console.log statements in changed files
 *
 * Cross-platform (Windows, macOS, Linux)
 *
 * Runs after each response and checks whether any changed JavaScript/TypeScript
 * file contains console.log statements, reporting the offending line numbers to
 * help developers remove debug statements before committing.
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

    for (const file of changedSourceFiles()) {
      const matches = grepFile(file, /console\.log/);
      if (matches.length === 0) continue;

      warnings.push(`[Hook] WARNING: console.log found in ${file}`);
      for (const { lineNumber, content } of matches.slice(0, MAX_REPORTED_LINES)) {
        warnings.push(`${lineNumber}: ${content.trim()}`);
      }
    }

    if (warnings.length > 0) {
      warnings.push('[Hook] Remove console.log statements before committing');
    }
  } catch (err) {
    warnings.push(`[Hook] check-console-log error: ${err.message}`);
  }

  return warnings;
}

const MAX_STDIN = 1024 * 1024; // 1MB limit
let data = '';
let truncated = false;

process.stdin.setEncoding('utf8');

process.stdin.on('data', chunk => {
  if (data.length < MAX_STDIN) {
    const remaining = MAX_STDIN - data.length;
    data += chunk.substring(0, remaining);
    if (chunk.length > remaining) truncated = true;
  } else {
    truncated = true;
  }
});

/**
 * Echo stdin back, then exit once the pipe has flushed. Truncated stdin is
 * never echoed: a JSON document cut mid-stream is reported by the harness as a
 * Stop hook JSON validation failure, so fail open and stay silent instead.
 */
function passThroughAndExit() {
  if (truncated) {
    log('[Hook] check-console-log: stdin exceeded 1MB; suppressing pass-through (fail-open)');
    process.exit(0);
  }
  if (!data) {
    process.exit(0);
  }
  process.stdout.write(data, () => process.exit(0));
}

process.stdin.on('end', () => {
  for (const warning of run()) {
    log(warning);
  }
  passThroughAndExit();
});

module.exports = { run };
