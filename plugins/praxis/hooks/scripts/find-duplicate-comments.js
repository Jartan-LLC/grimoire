#!/usr/bin/env node
/**
 * Duplicate-comment finder -- a reviewer tool, NOT a hook.
 *
 * It lives under hooks/scripts/ only to reuse lib/, which the directory name
 * would otherwise make misleading. Nothing in hooks.json invokes it; a reviewer
 * runs it by hand.
 *
 * The Retold fact rule cannot be applied from one file: judging a comment as a
 * retelling means knowing whether the same fact is told elsewhere, which
 * per-file review structurally cannot see. This supplies that whole-repo view.
 *
 * Scoped to the diff, not the repo -- it reports comment lines ADDED by the
 * change whose prose already appears somewhere tracked, and names both sites so
 * the reviewer can pick which one keeps the telling.
 *
 * Usage:
 *   node find-duplicate-comments.js [base-ref]     (default: origin/main)
 */

const { spawnSync } = require('child_process');

const MIN_PROSE_CHARS = 25;

// Comment openers across the languages this marketplace touches. Deliberately
// loose: a false positive costs a reviewer one glance, a miss costs the rule.
const COMMENT_PATTERNS = [
  /^\s*\/\/+\s?(.*)$/,
  /^\s*#+\s?(.*)$/,
  /^\s*\*\s?(.*)$/,
  /^\s*\/\*+\s?(.*?)(?:\*\/)?\s*$/
];

// Mandated or machine-read text is meant to be identical everywhere, so it is
// never a retelling.
const EXEMPT = /SPDX-License-Identifier|Copyright|Licensed under|eslint-|prettier-|type:\s*ignore|noqa|@ts-|shellcheck\s+disable/i;

// Generated trees are written by a tool; duplication there is the generator's.
const SKIP_PATHS = /(^|\/)(node_modules|\.codex-plugin|codex\/agents|\.agents)(\/|$)/;

function git(args) {
  const r = spawnSync('git', args, { encoding: 'utf8', maxBuffer: 32 * 1024 * 1024 });
  return r.status === 0 ? r.stdout : '';
}

/** Reduce a comment line to comparable prose, or '' when it carries none. */
function prose(line) {
  for (const pattern of COMMENT_PATTERNS) {
    const m = line.match(pattern);
    if (m) {
      const text = (m[1] || '').trim();
      if (!text || EXEMPT.test(text)) return '';
      // Compare on words alone so punctuation and wrapping do not hide a twin.
      const normalized = text.toLowerCase().replace(/[^a-z0-9 ]+/g, ' ').replace(/\s+/g, ' ').trim();
      return normalized.length >= MIN_PROSE_CHARS ? normalized : '';
    }
  }
  return '';
}

function main() {
  const base = process.argv[2] || 'origin/main';

  const changed = git(['diff', '--name-only', `${base}...HEAD`])
    .split('\n')
    .filter(f => f && !SKIP_PATHS.test(f));
  if (changed.length === 0) {
    console.log('No changed files to check.');
    return;
  }

  // Index every comment in the tracked tree, so a retelling is found whether or
  // not the other site was touched by this change.
  const index = new Map();
  for (const file of git(['ls-files']).split('\n')) {
    if (!file || SKIP_PATHS.test(file)) continue;
    const content = git(['show', `HEAD:${file}`]);
    if (!content) continue;
    content.split('\n').forEach((line, i) => {
      const text = prose(line);
      if (!text) return;
      if (!index.has(text)) index.set(text, []);
      index.get(text).push(`${file}:${i + 1}`);
    });
  }

  const findings = [];
  for (const file of changed) {
    const diff = git(['diff', `${base}...HEAD`, '--', file]);
    let lineNo = 0;
    for (const line of diff.split('\n')) {
      const hunk = line.match(/^@@ -\d+(?:,\d+)? \+(\d+)/);
      if (hunk) { lineNo = parseInt(hunk[1], 10); continue; }
      if (line.startsWith('-')) continue;
      if (!line.startsWith('+')) { lineNo++; continue; }

      const text = prose(line.slice(1));
      const here = `${file}:${lineNo}`;
      lineNo++;
      if (!text) continue;

      const elsewhere = (index.get(text) || []).filter(site => site !== here);
      if (elsewhere.length > 0) {
        findings.push({ here, text, elsewhere });
      }
    }
  }

  if (findings.length === 0) {
    console.log('No retold comments found in the diff.');
    return;
  }

  console.log(`${findings.length} added comment line(s) already told elsewhere:\n`);
  for (const f of findings) {
    console.log(`  ${f.here}`);
    console.log(`    "${f.text}"`);
    console.log(`    also at: ${f.elsewhere.slice(0, 5).join(', ')}${f.elsewhere.length > 5 ? ` (+${f.elsewhere.length - 5} more)` : ''}`);
    console.log('');
  }
  console.log('Retold fact: keep the telling where a change would falsify it; the rest point.');
}

main();
