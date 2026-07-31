#!/usr/bin/env node
// Originally from everything-claude-code by Affaan Mustafa (https://github.com/affaan-m/everything-claude-code)
/**
 * PostToolUse Hook: Warn about console.log statements after edits
 *
 * Cross-platform (Windows, macOS, Linux)
 *
 * Runs after Edit tool use. If an edited JS/TS file contains console.log
 * statements, warns with line numbers to help remove debug statements
 * before committing.
 */

const { readFile } = require('./lib/utils');

// Claude Code names the edited file in `tool_input.file_path`. Codex matches
// this hook through its `Edit` alias for `apply_patch`, which instead puts the
// whole patch in `tool_input.command`, so the paths have to be read out of it.
// Markers are verbatim from codex-rs/apply-patch/src/parser.rs. `Delete File`
// is omitted -- there is nothing left to scan.
const PATCH_FILE_MARKERS = ['*** Add File: ', '*** Update File: ', '*** Move to: '];

function editedPaths(toolInput) {
  if (!toolInput) return [];
  if (typeof toolInput.file_path === 'string') return [toolInput.file_path];
  if (typeof toolInput.command !== 'string') return [];

  return toolInput.command.split('\n').reduce((paths, line) => {
    const marker = PATCH_FILE_MARKERS.find(m => line.startsWith(m));
    if (marker) paths.push(line.slice(marker.length).trim());
    return paths;
  }, []);
}

const MAX_STDIN = 1024 * 1024; // 1MB limit
let data = '';
process.stdin.setEncoding('utf8');

process.stdin.on('data', chunk => {
  if (data.length < MAX_STDIN) {
    const remaining = MAX_STDIN - data.length;
    data += chunk.substring(0, remaining);
  }
});

process.stdin.on('end', () => {
  try {
    const input = JSON.parse(data);

    for (const filePath of editedPaths(input.tool_input)) {
      if (!/\.(ts|tsx|js|jsx)$/.test(filePath)) continue;

      const content = readFile(filePath);
      if (!content) continue;

      const matches = [];
      content.split('\n').forEach((line, idx) => {
        if (/console\.log/.test(line)) {
          matches.push((idx + 1) + ': ' + line.trim());
        }
      });

      if (matches.length > 0) {
        console.error('[Hook] WARNING: console.log found in ' + filePath);
        matches.slice(0, 5).forEach(m => console.error(m));
        console.error('[Hook] Remove console.log before committing');
      }
    }
  } catch {
    // Invalid input -- pass through
  }

  process.stdout.write(data);
  process.exit(0);
});
